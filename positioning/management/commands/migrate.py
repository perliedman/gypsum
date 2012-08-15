"""
    Migrates from deprecated, relational database to MongoDb.
    This script assumes the legacy database is configured in a
    database called "legacy" in settings, and that MongoDb is
    configured as "default" database.
"""

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User
from positioning import legacy_models, models

from elementtree.SimpleXMLWriter import XMLWriter
from StringIO import StringIO
import datetime

def migrate_users():
    i = 0
    for u in User.objects.using('legacy').all():
        User(
            username = u.username,
            first_name = u.first_name,
            last_name = u.last_name,
            email = u.email,
            password = u.password,
            is_staff = u.is_staff,
            is_active = u.is_active,
            is_superuser = u.is_superuser,
            last_login = u.last_login,
            date_joined = u.date_joined) \
        .save()

        i += 1

    return i


def migrate_activities():
    i = 0
    for activity in legacy_models.Activity.objects.using('legacy').all():
        models.Activity(
            name = activity.name,
            icon_url = activity.icon_url,
            max_speed = activity.max_speed,
            speed_format = activity.speed_format) \
        .save()

        i += 1

    return i

def migrate_tracks():
    i = 0
    for t in legacy_models.LegacyTrack.objects.using('legacy').all():
        positions = legacy_models.Position.objects.using('legacy').filter(track = t).order_by('time')
        positions_new = [models.Position(latitude=p.latitude, longitude=p.longitude, altitude=p.altitude, time=p.time) for p in positions]
        activity_new = models.Activity.objects.get(name=t.activity.name)
        owner_new = User.objects.using('default').get(username = t.owner.username)
        gpx = create_gpx(t, positions)

        new_track = models.Track(
            name = t.name,
            activity = activity_new,
            owner = owner_new,
            date = t.date,
            number = t.number,
            created_time = t.created_time,
            distance = t.distance,
            time = t.time,
            gpx = gpx,
            positions = positions_new,
            hash = gpx.__hash__())

        if t.has_weather:
            new_track.weather = models.Weather(
                temperature = t.temperature,
                precipitation = t.precipitation,
                conditions = t.weather_conditions)

        new_track.save()

        i += 1

    return i

def create_gpx(track, positions):
    f = StringIO()
    w = XMLWriter(f, 'utf-8')

    gpx = w.start('gpx', creator='Gypsum', version='1.1')

    w.start('trk')
    w.start('name')
    w.data(track.__unicode__())
    w.end('name')

    w.start('trkseg')

    for p in positions:
        w.start('trkpt', lat=str(p.latitude), lon=str(p.longitude))

        if p.altitude != None:
            w.start('ele')
            w.data(str(p.altitude))
            w.end('ele')
        w.start('time')
        w.data(datetime.datetime.strftime(p.time, '%Y-%m-%dT%H:%M:%S.%fZ'))
        w.end('time')

        w.end('trkpt')

    w.end('trkseg')

    w.end('trk')

    w.close(gpx)

    return f.getvalue()

class Command(BaseCommand):
    args = ''
    help = 'Migrates from relational to non-relational db model.'

    def handle(self, *args, **options):
        self.stdout.write('Migrating users...\n')
        n = migrate_users()
        self.stdout.write('Migrated %d users.\n' % n)

        self.stdout.write('Migrating activities...\n')
        n = migrate_activities()
        self.stdout.write('Migrated %d activities.\n' % n)

        self.stdout.write('Migrating tracks...\n')
        n = migrate_tracks()
        self.stdout.write('Migrated %d tracks.\n' % n)
