from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
import jsonencoder
import simplejson as json
from tasks import get_track_weather
from zipfile import ZipFile, BadZipfile

from gypsum.positioning.models import Track, Activity
from gypsum.positioning.gpxparser import GPXParser

from geopy import distance

import datetime, re
from django.template.context import RequestContext
from StringIO import StringIO

from avatar.templatetags.avatar_tags import avatar_url

WEATHER_IMAGE_MAP =  {re.compile(r'^Clear$'): 'sun.png',
                      re.compile(r'^Partly Cloudy$'): 'partly_cloudy.png',
                      re.compile(r'^Scattered Clouds$'): 'partly_cloudy.png',
                      re.compile(r'^Mostly Cloudy$'): 'cloudy.png',
                      re.compile(r'^Overcast$'): 'cloudy.png',
                      re.compile(r'^(Light |Heavy |)Rain.*$'): 'rain.png',
                      re.compile(r'^(Light |Heavy |)Snow.*$'): 'snow.png',
                      re.compile(r'^(Light |Heavy |)Thunderstorm.*$'): 'thunderstorm.png',
                      }

def get_weather_image(track):
    if track.weather != None and track.weather.conditions != None:
        for regexp in WEATHER_IMAGE_MAP.keys():
            if regexp.match(track.weather.conditions) != None:
                return WEATHER_IMAGE_MAP[regexp]

    return None

def display_track(request, username, year, month, day, number):
    user = get_object_or_404(User, username__exact = username)
    track = get_track_by_date(user, int(year), int(month), int(day), int(number))
    return render_to_response('display_track.html',
                              {'track': track,
                               'weather_image': get_weather_image(track)},
                              context_instance=RequestContext(request))

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
    positions = track.positions
    last_info_point = positions[0]

    for p in positions:
        if last_pos != None:
            d = d + distance.distance((p.latitude, p.longitude), \
                (last_pos.latitude, last_pos.longitude)).kilometers

        current_kilometer = int(d / marker_spacing) * marker_spacing
        if current_kilometer > last_km_counter:
            info_points[count] = {'distance': current_kilometer, \
                            'total_time': str(p.time - positions[0].time), \
                            'pace': '%s %s' % (track.activity.format_speed(current_kilometer - last_km_counter, (p.time - last_info_point.time).seconds), track.activity.get_speed_format_display())}
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
        positions = track.positions

        if len(positions) > 0:
            date = positions[0].time.strftime('%Y-%m-%d')
            start_time = positions[0].time.strftime('%H:%M')
            end_time = positions[len(positions) - 1].time.strftime('%H:%M')
            markers = create_markers(track)
        else:
            date = 'Unknown'
            start_time = ''
            end_time = ''
            markers = {}

        data = {'name': track.name,
                'distance': track.distance,
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'duration': track.get_duration_string(),
                'pace': track.get_pace_string(),
                'created_time': track.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'elevation_chart_url': track.get_elevation_chart_url(300, 145),
                'pace_chart_url': track.get_pace_chart_url(300, 145),
                'is_open': False,
                'positions': positions,
                'info_points': markers}
        return HttpResponse(jsonencoder.dumps(data), mimetype='application/json')
    else:
        return HttpResponse(status = 404)

def start_page(request):
    users = User.objects.order_by('first_name', 'last_name')
    all_tracks = Track.objects.order_by('date').reverse()
    paginator = Paginator(all_tracks, 5)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    try:
        tracks = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tracks = paginator.page(paginator.num_pages)

    for t in tracks.object_list:
        t.weather_image = get_weather_image(t)

    return render_to_response('index.html', {'users': users, 'tracks': tracks},
                              context_instance=RequestContext(request))

def track_history(request):
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        offset = 0

    tracks = Track.objects.order_by('date').reverse()[offset:offset + 20]
    return HttpResponse(jsonencoder.dumps(map(lambda t: {
            'name': t.name,
            'activity': t.activity.name,
            'activity_icon_url': t.activity.icon_url,
            'distance': t.distance,
            'duration': t.get_duration_string(),
            'pace': t.get_pace_string(),
            'owner': {
                'name': t.owner.get_full_name(),
                'id': t.owner.id,
                'username': t.owner.username,
                'avatar_url': avatar_url(t.owner, 32)
            },
            'date': t.date,
            'number': t.number,
            'details_url': reverse(get_track_data, args=[t.owner.username, str(t.date.year), '%02d' % t.date.month, '%02d' % t.date.day, str(t.number)])
            #'details_url': reverse(get_track_data, kwargs={'username':t.owner.username, 'year':str(t.date.year), 'month':str(t.date.month), 'day': str(t.date.day), 'number': str(t.number)})
        }, tracks)), mimetype='application/json')

def user_timeline(request, username):
    user = User.objects.get(username__exact = username)
    tracks = Track.objects.filter(owner = user).order_by('date').reverse()
    months = []
    current_month = None

    for track in tracks:
        track.weather_image = get_weather_image(track)

        is_new_month = current_month == None \
            or current_month['year'] != track.date.year \
            or current_month['month'] != track.date.month

        if is_new_month:
            activities = {track.activity: {'distance': track.distance,
                                           'tracks': [track]}}

            current_month = {'year': track.date.year,
                             'month': track.date.month,
                             'activities': activities}
            months.append(current_month)
        else:
            if current_month['activities'].has_key(track.activity):
                activity_record = current_month['activities'][track.activity]
            else:
                activity_record = {'distance': 0.0, 'tracks': []}
                current_month['activities'][track.activity] = activity_record

            activity_record['distance'] = activity_record['distance'] + track.distance
            activity_record['tracks'].append(track)

    return render_to_response('user_timeline.html', {'user': user, 'months': months},
                              context_instance=RequestContext(request))

def get_tracks_by_date(owner, year, month, day):
    d = datetime.datetime(year, month, day)
    return Track.objects.filter(owner = owner, date = d).order_by('created_time')

def get_track_by_date(owner, year, month, day, number):
    d = datetime.datetime(year, month, day)
    return get_object_or_404(Track, owner=owner, date=d, number=number)
