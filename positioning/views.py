from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django import forms
import jsonencoder
import simplejson as json
from zipfile import ZipFile

from gypsum.positioning.models import Position, Track
from gypsum.positioning.gpxparser import GPXParser

from geopy import distance

import datetime

def begin_track(request):
    username = request.REQUEST['user']
    password = request.REQUEST['pw']
    track_name = request.REQUEST['track']

    user = authenticate(username = username, password = password)
    if user is not None and user.is_active:
        t = Track(name = track_name, owner = user, created_time = datetime.datetime.now(), is_open = True)
        t.save()
        
        return HttpResponse("{'track_id': '%s'}" % (t.id,), status = 200)
    else:
        return HttpResponse(status = 401)
        
def report(request):
    if request.method == 'POST':
        post_data = request.raw_post_data.decode('utf-8')
        data = json.loads(post_data)
        track = Track.objects.get(id=data['track'])
        if (datetime.datetime.now() - track.created_time).days > 0:
            return HttpResponse('Track is older than one day and closed for reporting.', status = 400)
        
        for pos_doc in data['positions']:
            p = Position(latitude = pos_doc['lat'], \
                         longitude = pos_doc['lat'], \
                         altitude = pos_doc['lat'], \
                         time = datetime.datetime.fromtimestamp(pos_doc['time'] / 1000), \
                         track = track)
            p.save()	

        return HttpResponse(status = 200)
    else:
        return HttpResponse("Only POST allowed.", status = 400)
        
def display_track(request, username, year, month, day, number):
    user = User.objects.get(username__exact = username)
    if user == None:
        print 'No user called "%s".' % username
        return HttpResponse(status = 404)
        
    track = get_track_by_date(user, int(year), int(month), int(day), int(number))
    if track != None:
        return render_to_response('display_track.html', {'track': track})
    else:
        return HttpResponse(status = 404)
        
def get_track_data(request, username, year, month, day, number):
    user = User.objects.get(username__exact = username)
    if user == None:
        print 'No user called "%s".' % username
        return HttpResponse(status = 404)
        
    track = get_track_by_date(user, int(year), int(month), int(day), int(number))
    if track != None:
        positions = Position.objects.filter(track = track)

        if len(positions) > 0:
            duration = positions[len(positions) - 1].time - positions[0].time
            date = positions[0].time.strftime('%Y-%m-%d')
            start_time = positions[0].time.strftime('%H:%M')
            end_time = positions[len(positions) - 1].time.strftime('%H:%M')
            last_info_point = positions[0]
        else:
            duration = datetime.timedelta(0)
            date = 'Unknown'
            start_time = ''
            end_time = ''

        last_pos = None
        d = 0.0
        last_km_counter = -1
        count = 0
        info_points = {}
        
        for p in positions:
            if last_pos != None:
                d = d + distance.distance((p.latitude, p.longitude), \
                    (last_pos.latitude, last_pos.longitude)).kilometers

            current_kilometer = int(d)
            if current_kilometer > last_km_counter:
                info_points[count] = {'distance': current_kilometer, \
                                'total_time': str(p.time - positions[0].time), \
                                'last_km': str(p.time - last_info_point.time)}
                last_info_point = p
                last_km_counter = current_kilometer

            last_pos = p
            count = count + 1
                        
        data = {'name': track.name,
                'distance': d,
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'duration': str(duration),
                'created_time': track.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'elevation_chart_url': track.get_elevation_chart_url(300, 145),
                'pace_chart_url': track.get_pace_chart_url(300, 145),
                'is_open': track.is_open,
                'positions': positions,
                'info_points': info_points}
        return HttpResponse(jsonencoder.dumps(data), mimetype='application/javascript')
    else:
        return HttpResponse(status = 404)

class UploadTrackForm(forms.Form):
    name = forms.CharField(max_length = 64)
    track_data = forms.FileField()

def add_gpx_track(name, user, gpx_file):
    gpx = GPXParser(gpx_file)
    
    if len(gpx.tracks.values()) > 0:
        gpx_track = gpx.tracks.values()[0]
        if len(gpx_track) > 0:
            track = Track(name = name, date = gpx_track[0].time, created_time = datetime.datetime.now(), owner = user, is_open = False)
            positions = []
            
            for gpx_track in gpx.tracks.values():
                for pos in gpx_track:
                    positions.append(pos)
                                    
            return (track, positions)
        else:
            return (None, None)
    else:
        return (None, None)

@login_required
def upload_track(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            (track, positions) = add_gpx_track(form.cleaned_data['name'], request.user, form.cleaned_data['track_data'])
            if track != None:
                track.save()
                for p in positions:
                    p.track = track
                    p.save() 
            
                time = track.date
                return HttpResponseRedirect(reverse(display_track, kwargs = {
                            'username': track.owner.username, 
                            'year': time.year, 
                            'month': time.month, 
                            'day': time.day, 
                            'number': len(get_tracks_by_date(request.user, time.year, time.month, time.day)) - 1}))
    else:
        form = UploadTrackForm()
        
    return render_to_response('upload_track.html', {'form': form})

@login_required
def upload_tracks(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            zip = ZipFile(form.cleaned_data['track_data'])
            
            for name in zip.namelist():
                print 'Opening', name
                f = zip.open(name)
                try:
                    (t, positions) = add_gpx_track(name, request.user, f)
                    if t != None and len(Track.objects.filter(hash = t.hash)) == 0:
                        track = t
                        track.save()
                        for p in positions:
                            p.track = track
                            p.save() 
                        print 'Saved track', track.name
                    else:
                        print 'File is not GPX or does not have content:', name
                finally:
                    f.close()
                    
            print 'Done'
            
            time = track.date
            return HttpResponseRedirect(reverse('gypsum.positioning.views.display_track', args = [request.user.username, time.year, time.month, time.day, len(get_tracks_by_date(request.user, time.year, time.month, time.day)) - 1]))
    else:
        form = UploadTrackForm()
        
    return render_to_response('upload_track.html', {'form': form})

def get_tracks_by_date(owner, year, month, day):
    d = datetime.datetime(year, month, day)
    return Track.objects.filter(owner = owner, date = d).order_by('created_time')

def get_track_by_date(owner, year, month, day, number):
    tracks = get_tracks_by_date(owner, year, month, day)
    if len(tracks) > number:
        return tracks[number]
    else:
        return None

