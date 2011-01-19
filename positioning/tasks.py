from celery.decorators import task
from gypsum.positioning.models import Track
from django.contrib.auth.models import User
from gypsum.positioning import weather 
from datetime import timedelta

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

@task
def get_track_weather():
    for t in Track.objects.filter(has_weather=None)[0:10]:
        try:
            c = t.center_coordinate()
            w = weather.get_weather_from_location(c[0], c[1], t.positions()[0].time + timedelta(seconds=t.time / 2))
            t.temperature = w.temperature
            t.weather_conditions = w.conditions
            t.precipitation = w.precipitation_cm
            t.has_weather = True
        except weather.WeatherNotAvailableError:
            t.has_weather = False
            
        t.save()
