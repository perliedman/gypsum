from django.http import HttpRequest, HttpResponse
from django.core import serializers
import simplejson as json
from gypsum.positioning.models import Position
from datetime import datetime

def report(request):
    print "Entering request"
    try:
        if request.method == 'POST':
            post_data = request.raw_post_data.decode('utf-8')
            print "JSON:", post_data
            data = json.loads(post_data)
            print "Parsed JSON:", data
            user = data['auth']
            for pos_doc in data['positions']:
                pos_doc['time'] = datetime.fromtimestamp(pos_doc['time'] / 1000)
                Position(pos_doc).save()
                print "saved"

            print "Done"            
            return HttpResponse('', status = 200)
        else:
            return HttpResponse("Only POST allowed.", status = 400)
    except Exception, e:
        print e
        raise e
        
