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
from zipfile import ZipFile, BadZipfile

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

def calculate_marker_spacing(track):
    marker_spacing = 1
    d = track.distance
    count = 0
    while (int(d / marker_spacing) > 25):
        if count % 2 == 0:
            marker_spacing = marker_spacing * 5
        else:
            marker_spacing = marker_spacing * 2
            
        count = count + 1
        
    return marker_spacing 
        
def create_markers(track):
    marker_spacing = calculate_marker_spacing(track)

    last_pos = None
    d = 0.0
    last_km_counter = -1
    count = 0
    info_points = {}
    positions = track.positions()
    last_info_point = positions[0]
    
    for p in positions:
        if last_pos != None:
            d = d + distance.distance((p.latitude, p.longitude), \
                (last_pos.latitude, last_pos.longitude)).kilometers

        current_kilometer = int(d / marker_spacing)
        if current_kilometer > last_km_counter:
            info_points[count] = {'distance': current_kilometer * marker_spacing, \
                            'total_time': str(p.time - positions[0].time), \
                            'last_km': str(p.time - last_info_point.time)}
            last_info_point = p
            last_km_counter = current_kilometer

        last_pos = p
        count = count + 1
        
    return info_points
        
def get_track_data(request, username, year, month, day, number):
    user = User.objects.get(username__exact = username)
    if user == None:
        print 'No user called "%s".' % username
        return HttpResponse(status = 404)
        
    track = get_track_by_date(user, int(year), int(month), int(day), int(number))
    if track != None:
        positions = track.positions()

        if len(positions) > 0:
            duration = positions[len(positions) - 1].time - positions[0].time
            date = positions[0].time.strftime('%Y-%m-%d')
            start_time = positions[0].time.strftime('%H:%M')
            end_time = positions[len(positions) - 1].time.strftime('%H:%M')
            markers = create_markers(track)
        else:
            duration = datetime.timedelta(0)
            date = 'Unknown'
            start_time = ''
            end_time = ''
            markers = {}
                        
        data = {'name': track.name,
                'distance': track.distance,
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'duration': str(duration),
                'created_time': track.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'elevation_chart_url': track.get_elevation_chart_url(300, 145),
                'pace_chart_url': track.get_pace_chart_url(300, 145),
                'is_open': track.is_open,
                'positions': positions,
                'info_points': markers}
        return HttpResponse(jsonencoder.dumps(data), mimetype='application/javascript')
    else:
        return HttpResponse(status = 404)

class UploadTrackForm(forms.Form):
    track_data = forms.FileField()

def parse_gpx_tracks(user, gpx_file):
    gpx = GPXParser(gpx_file)

    track_models = []
    
    for track_name in gpx.tracks:
        gpx_track = gpx.tracks[track_name]
        if len(gpx_track) > 0:
            t = gpx_track[0].time
            track = Track(name = track_name, 
                date = datetime.date(t.year, t.month, t.day), 
                created_time = datetime.datetime.now(), 
                owner = user, 
                distance = 0, 
                is_open = False)
            positions = []
            last_pos = None
            
            for pos in gpx_track:
                positions.append(pos)
                
                if last_pos != None:
                    track.distance = track.distance + distance.distance((pos.latitude, pos.longitude), \
                        (last_pos.latitude, last_pos.longitude)).kilometers
                        
                last_pos = pos
                                    
            track_models.append((track, positions))
            
    return track_models

def save_track_file(file, user):
    tracks_positions = parse_gpx_tracks(user, file)
    tracks = []
    for (t, positions) in tracks_positions:
        # The track's hash isn't calculated automatically, so hash it explicitly
        t.hash = Track._hash(t, positions)
        if len(Track.objects.filter(hash = t.hash)) == 0:
            t.save()
            d = 0.0
            last_pos = None
            for p in positions:
                p.track = t
                p.save()
                         
            tracks.append(t)

    return tracks

@login_required
def upload_tracks(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            tracks = None
            uploaded_file = form.cleaned_data['track_data']
            try:
                zip = ZipFile(uploaded_file)
                
                for name in zip.namelist():
                    f = zip.open(name)
                    try:
                        tracks = save_track_file(f, request.user)
                    finally:
                        f.close()
            except BadZipfile:
                uploaded_file.seek(0)
                tracks = save_track_file(uploaded_file, request.user)
                      
            if len(tracks) > 0:
                track = tracks[len(tracks) - 1]
                time = track.date
                return HttpResponseRedirect(reverse(display_track, kwargs = {
                            'username': track.owner.username, 
                            'year': time.year, 
                            'month': '%02d' % time.month, 
                            'day': '%02d' % time.day, 
                            'number': len(get_tracks_by_date(request.user, time.year, time.month, time.day)) - 1}))
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

