import pymongo
import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from pygooglechart import SimpleLineChart, Axis
from geopy import distance
from filter import ema

class Track(models.Model):
    name = models.CharField(max_length = 64)
    created_time = models.DateTimeField()
    owner = models.ForeignKey(User)
    is_open = models.BooleanField()
    
    def positions(self):
        return Position.objects.filter(track = self)
    
    def get_pace_chart_url(self, width, height):
        pace = []
        int_dist = []
        s = 0
        last_p = None
        for p in self.positions():
            if last_p != None:
                ds = distance.distance((p.latitude, p.longitude), \
                    (last_p.latitude, last_p.longitude)).kilometers
                s = s + int(ds * 1000)
                dt = (p.time - last_p.time).seconds
                pace.append(dt / ds)
                int_dist.append(s)
                
            last_p = p

        int_pace = [int(p) for p in ema(pace, 20)]
        
        min_pace = int(min(int_pace) * 0.95)
        max_pace = int(max(int_pace) / 0.95)
        mid_pace = (max_pace + min_pace) / 2
        
        min_pace_str = '%02d:%02d' % (min_pace / 60, min_pace % 60)
        mid_pace_str = '%02d:%02d' % (mid_pace / 60, mid_pace % 60)
        max_pace_str = '%02d:%02d' % (max_pace / 60, max_pace % 60)
        
        chart = SimpleLineChart(width, height, y_range = (min_pace, max_pace))
        chart.add_data(int_pace)
        chart.set_axis_labels(Axis.LEFT, [min_pace_str, mid_pace_str, max_pace_str])
        
        return chart.get_url()
    
    def get_elevation_chart_url(self, width, height):
        int_elevations = [int(elevation) for elevation in ema([p.altitude for p in self.positions()], 20)]
        max_elev = int(max(int_elevations) / 0.95)
        min_elev = int(min(int_elevations) * 0.95)
        
        chart = SimpleLineChart(width, height, y_range = (min_elev, max_elev))
        chart.add_data(int_elevations)
        chart.set_axis_range(Axis.LEFT, min_elev, max_elev)
        
        return chart.get_url()

class Position(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    time = models.DateTimeField()
    track = models.ForeignKey(Track)
    
