from django.contrib.auth import authenticate
from django.http import HttpRequest, HttpResponse
from django.core import serializers
import simplejson as json
from gypsum.positioning.models import Position, Track
from datetime import datetime

def begin_track(request):
    username = request.REQUEST['user']
    password = request.REQUEST['pw']
    track_name = request.REQUEST['track']

    user = authenticate(username = username, password = password)
    if user is not None and user.is_active:
        t = Track()
        t.name = track_name
        t.owner_id = username
        t.created_time = datetime.now()
        t.save()
        
        return HttpResponse("{'track_id': '%s'}" % (t.id,), status = 200)
    else:
        return HttpResponse(status = 401)
        
def report(request):
    print "Entering request"
    try:
        if request.method == 'POST':
            post_data = request.raw_post_data.decode('utf-8')
            data = json.loads(post_data)
            track = Track.get(pymongo.objectid.ObjectId(data['track']))
            if (datetime.now() - track.created_time).days > 0:
                return HttpResponse('Track is older than one day and closed for reporting.', status = 400)
            
            for pos_doc in data['positions']:
                pos_doc['time'] = datetime.fromtimestamp(pos_doc['time'] / 1000)
                Position(pos_doc).save()
                print "saved"

            return HttpResponse(status = 200)
        else:
            return HttpResponse("Only POST allowed.", status = 400)
    except Exception, e:
        print e
        raise e
        

