from django.contrib.auth import authenticate
from django.http import HttpRequest, HttpResponse
from django.core import serializers
from django.shortcuts import render_to_response
import simplejson as json
from gypsum.positioning.models import Position, Track
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
    track = get_track_by_date(year, month, day, number)
    if track != None:
        return render_to_response('display_track.html', {'track': track})
    else:
        return HttpResponse(status = 404)
        
def get_track_positions(request, year, month, day, number):
    track = get_track_by_date(int(year), int(month), int(day), int(number))
    if track != None:
        return HttpResponse(json.dumps(track.positions()))
    else:
        return HttpResponse(status = 404)

def get_track_by_date(year, month, day, number):
    d = datetime.datetime(year, month, day)
    d1 = d + datetime.timedelta(1)
    tracks = Track.objects.filter(created_time__gte = d, created_time__lt = d1)\
        .order_by('created_time')
    if len(tracks) > number:
        return tracks[number]
    else:
        return None
