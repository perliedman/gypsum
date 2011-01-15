from gypsum.positioning.models import Track
from django.contrib.auth.models import User

def enumerate_tracks():
    for u in User.objects.all():
        last_date = None
        n = 0
        for t in Track.objects.filter(owner=u).order_by('date'):
            date = t.date
            if  last_date == None or last_date == date:
                n = n + 1
            else:
                n = 0
                
            t.number = n
            t.save()
            
            last_date = date