from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.shortcuts import render_to_response
from django import forms
import jsonencoder

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
        t = Track()
        t.name = track_name
        t.owner = user
        t.created_time = datetime.now()
        t.save()
        
        return HttpResponse("{'track_id': '%s'}" % (t.id,), status = 200)
    else:
        return HttpResponse(status = 401)
        
def report(request):
    try:
        if request.method == 'POST':
            post_data = request.raw_post_data.decode('utf-8')
            data = json.loads(post_data)
            track = Track.objects.get(id=data['track'])
            if (datetime.now() - track.created_time).days > 0:
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
    except Exception, e:
        print e
        raise e
        
def display_track(request, year, month, day, number):
    track = get_track_by_date(int(year), int(month), int(day), int(number))
    if track != None:
        return render_to_response('display_track.html', {'track': track})
    else:
        return HttpResponse(status = 404)
        
def get_track_data(request, year, month, day, number):
    track = get_track_by_date(int(year), int(month), int(day), int(number))
    if track != None:
        positions = Position.objects.filter(track = track)
        last_pos = None
        d = 0.0
        for p in positions:
            if last_pos != None:
                d = d + distance.distance((p.latitude, p.longitude), \
                    (last_pos.latitude, last_pos.longitude)).kilometers
                
            last_pos = p
            
        if len(positions) > 0:
            duration = positions[len(positions) - 1].time - positions[0].time
        else:
            duration = timedelta(0)
            
        data = {'name': track.name,
                'distance': d,
                'duration': str(duration),
                'created_time': track.created_time.strftime('%Y-%M-%d %H:%m:%S'),
                'elevation_chart_url': track.get_elevation_chart_url(300, 145),
                'pace_chart_url': track.get_pace_chart_url(300, 145),
                'positions': positions}
        #return HttpResponse(serializers.serialize("json", data))
        return HttpResponse(jsonencoder.dumps(data), mimetype='application/javascript')
    else:
        return HttpResponse(status = 404)

class UploadTrackForm(forms.Form):
    name = forms.CharField(max_length = 64)
    track_data = forms.FileField()

@login_required
def upload_track(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            time = datetime.datetime.now()
            gpx = GPXParser(form.cleaned_data['track_data'])

            track = Track(name = form.cleaned_data['name'], created_time = time, owner = request.user)
            track.save()
            
            for gpx_track in gpx.tracks.values():
                for pos in gpx_track:
                    pos.track = track
                    pos.save() 

            return HttpResponseRedirect("%04d/%02d/%02d/%d" % (time.year, time.month, time.day, len(get_tracks_by_date(time.year, time.month, time.day)) - 1))
    else:
        form = UploadTrackForm()
        
    return render_to_response('upload_track.html', {'form': form})

def get_tracks_by_date(year, month, day):
    d = datetime.datetime(year, month, day)
    d1 = d + datetime.timedelta(1)
    return Track.objects.filter(created_time__gte = d, created_time__lt = d1)\
        .order_by('created_time')

def get_track_by_date(year, month, day, number):
    tracks = get_tracks_by_date(year, month, day)
    if len(tracks) > number:
        return tracks[number]
    else:
        return None

