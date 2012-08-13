import datetime
from django.conf import settings
from django.db import models
from djangotoolbox.fields import ListField
from django.contrib.auth.models import User
from pygooglechart import SimpleLineChart, Axis
from geopy import distance
from filter import ema
from djangotoolbox.fields import EmbeddedModelField
from gypsum.positioning.gpxparser import GPXParser
from StringIO import StringIO
import pymongo

class Activity(models.Model):
    name = models.CharField(max_length = 32)
    icon_url = models.CharField(max_length = 255)
    max_speed = models.FloatField()
    speed_format = models.CharField(choices = (('km_h', 'km/h'),('min_km', 'minutes/km')), max_length = 6)

    def __unicode__(self):
        return self.name

    def format_speed(self, distance_km, time_seconds):
        try:
            if self.speed_format == 'km_h':
                return "%.0f" % (distance_km / (time_seconds / 3600.0))
            elif self.speed_format == 'min_km':
                seconds_per_km = time_seconds / distance_km
                return "%d:%02d" % (int(seconds_per_km) / 60, int(seconds_per_km) % 60)
            else:
                raise Exception('Unknown speed format "%s".' % self.speed_format)
        except ZeroDivisionError:
            return '-'

class Weather(models.Model):
    temperature = models.FloatField(null = True, blank = True)
    precipitation = models.CharField(null = True, max_length = 32, blank = True)
    conditions = models.CharField(null = True, max_length = 32, blank = True)

class Track(models.Model):
    class MongoMeta:
        index_together = ['owner', ('date', pymongo.DESCENDING)]

    name = models.CharField(max_length = 64, null = True, blank = True)
    activity = models.ForeignKey(Activity, null = True)
    date = models.DateField(db_index=True)
    number = models.IntegerField(db_index=True)
    created_time = models.DateTimeField()
    owner = models.ForeignKey(User)
    distance = models.FloatField()
    time = models.IntegerField()
    weather = EmbeddedModelField('Weather', null=True, default=None, db_index=True)
    gpx = models.TextField(null = False, default = '')
    geojson = models.TextField(null = False, default = '')
    hash = models.IntegerField()

    def __unicode__(self):
        return "%s's %s on %s, %.1f km, %s" % \
            (self.owner.get_full_name(), str(self.activity),
             self.date.strftime('%Y-%m-%d'), self.distance,
             str(datetime.timedelta(seconds = self.time)))

    @models.permalink
    def get_absolute_url(self):
        return ('gypsum.positioning.views.display_track', (),
                {'username': self.owner.username,
                 'year': self.date.year,
                 'month': '%02d' % self.date.month,
                 'day': '%02d' % self.date.day,
                 'number': self.number})

    def save(self, *args, **kwargs):
        super(Track, self).save(*args, **kwargs)

    def positions(self):
        if not hasattr(self, '_positions'):
            gpx = GPXParser(StringIO(self.gpx))
            self._positions = []
            for track_name in gpx.tracks:
                for p in gpx.tracks[track_name]:
                    self._positions.append(p)
        return self._positions

    def center_coordinate(self):
        bbox = self.get_bounding_box()
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    def get_bounding_box(self):
        positions = self.positions()
        if len(positions) == 0:
            raise Exception("Center coordinate can't be calculated for track without positions.")

        limits = [90, 180, -90, -180]
        for p in positions:
            limits[0] = min(limits[0], p.latitude)
            limits[1] = min(limits[1], p.longitude)
            limits[2] = max(limits[2], p.latitude)
            limits[3] = max(limits[3], p.longitude)

        return limits

    def get_title(self):
        if self.name != None and len(self.name) > 0:
            return self.name
        else:
            return "%s's %s - %s" % (self.owner.get_full_name(), self.activity.name, self.date.strftime('%Y-%m-%d'))

    def get_pace_string(self):
        return '%s %s' % \
            (self.activity.format_speed(self.distance, self.time),
             self.activity.get_speed_format_display())

    def get_duration_string(self):
        return str(datetime.timedelta(seconds = self.time))

    def __hash__(self):
        return Track._hash(self, self.positions())

    @classmethod
    def _hash(clss, track, positions):
        h = hash(track.name) \
            * 37 + hash(track.date)

        for p in positions[::50]:
            h = h + 37 * hash(p.latitude) \
                + 37 * hash(p.longitude) \
                + 37 * hash(p.time)

        return int(h & (2**31 - 1))

    def get_pace_chart_url(self, width, height):
        if len(self.positions()) == 0:
            return ''

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
                if ds > 0:
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
        if len(self.positions()) == 0:
            return ''

        int_elevations = [int(elevation) for elevation in ema([p.altitude for p in self.positions()], 20)]

        max_elev = int(max(int_elevations) / 0.95)
        min_elev = int(min(int_elevations) * 0.95)

        chart = SimpleLineChart(width, height, y_range = (min_elev, max_elev))
        chart.add_data(int_elevations)
        chart.set_axis_range(Axis.LEFT, min_elev, max_elev)

        return chart.get_url()
