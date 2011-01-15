from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django import forms
import jsonencoder
import simplejson as json
from zipfile import ZipFile, BadZipfile

from gypsum.positioning.models import Position, Track, Activity
from gypsum.positioning.gpxparser import GPXParser

from geopy import distance

import datetime
from django.template.context import RequestContext

def begin_track(request):
    username = request.REQUEST['user']
    password = request.REQUEST['pw']
    track_name = request.REQUEST['track']

    user = authenticate(username = username, password = password)
    if user is not None and user.is_active:
        t = Track(name = track_name, owner = user, created_time = datetime.datetime.now(), is_open = True)
        t.save()
        
        return HttpResponse("{'track_id': '%s'}" % (t.id,), status = 200)
    else:
        return HttpResponse(status = 401)
        
def report(request):
    if request.method == 'POST':
        post_data = request.raw_post_data.decode('utf-8')
        data = json.loads(post_data)
        track = Track.objects.get(id=data['track'])
        if (datetime.datetime.now() - track.created_time).days > 0:
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
        
def display_track(request, username, year, month, day, number):
    user = User.objects.get(username__exact = username)
    if user == None:
        print 'No user called "%s".' % username
        return HttpResponse(status = 404)
        
    track = get_track_by_date(user, int(year), int(month), int(day), int(number))
    if track != None:
        return render_to_response('display_track.html', {'track': track},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponse(status = 404)

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
    positions = track.positions()
    last_info_point = positions[0]
    
    for p in positions:
        if last_pos != None:
            d = d + distance.distance((p.latitude, p.longitude), \
                (last_pos.latitude, last_pos.longitude)).kilometers

        current_kilometer = int(d / marker_spacing)
        if current_kilometer > last_km_counter:
            info_points[count] = {'distance': current_kilometer * marker_spacing, \
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
        positions = track.positions()

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
                'is_open': track.is_open,
                'positions': positions,
                'info_points': markers}
        return HttpResponse(jsonencoder.dumps(data), mimetype='application/javascript')
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
    
    return render_to_response('start_page.html', {'users': users, 'tracks': tracks},
                              context_instance=RequestContext(request))

def user_timeline(request, username):
    user = User.objects.get(username__exact = username)
    tracks = Track.objects.filter(owner = user).order_by('date').reverse()
    months = []
    current_month = None
    last_date = None
    day_track_count = 0
    for track in tracks:
        if track.date == last_date:
            day_track_count = day_track_count + 1
        else:
            day_track_count = 0
            last_date = track.date

        track.url = '%s/%d/' % (track.date.strftime('%Y/%m/%d'), day_track_count)
    
        if current_month == None or current_month['year'] != track.date.year or current_month['month'] != track.date.month:
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

class UploadTrackForm(forms.Form):
    track_data = forms.FileField(label = 'File to upload', 
        help_text = 'The file to upload. The file must be a GPX file, or a ZIP file containing GPX files.')
    only_newer = forms.BooleanField(label = 'Store only newer', initial = True)

def parse_gpx_tracks(user, gpx_file):
    gpx = GPXParser(gpx_file)

    track_models = []
    
    for track_name in gpx.tracks:
        gpx_track = gpx.tracks[track_name]
        if len(gpx_track) > 0:
            if not track_name.isdigit() and len(track_name) > 0:
                given_name = track_name
            else:
                given_name = None
        
            t = gpx_track[0].time
            duration = gpx_track[len(gpx_track) - 1].time - t

            track = Track(name = given_name, 
                date = datetime.date(t.year, t.month, t.day), 
                created_time = datetime.datetime.now(), 
                owner = user, 
                distance = 0,
                time = duration.seconds,    # TODO: this will break for tracks longer than a day!
                is_open = False)
            positions = []
            last_pos = None
            
            for pos in gpx_track:
                positions.append(pos)
                
                if last_pos != None:
                    track.distance = track.distance + distance.distance((pos.latitude, pos.longitude), \
                        (last_pos.latitude, last_pos.longitude)).kilometers
                        
                last_pos = pos
                
            avg_speed_kmh = track.distance / (duration.seconds / 3600.0) # TODO: this will break for tracks longer than a day!
            for activity in Activity.objects.order_by('max_speed').reverse():
                if avg_speed_kmh <= activity.max_speed:
                    track.activity = activity
                                    
            track_models.append((track, positions))
            
    return track_models

def save_track_file(file, user, only_after):
    tracks_positions = parse_gpx_tracks(user, file)
    tracks = []
    for (t, positions) in tracks_positions:
        # The track's hash isn't calculated automatically, so hash it explicitly
        t.hash = Track._hash(t, positions)
        if (only_after == None or t.date > only_after) and len(Track.objects.filter(owner = user, hash = t.hash)) == 0:
            days_tracks = get_tracks_by_date(user, track.date.year, track.date.month, track.date.day)
            t.number = len(days_tracks)
            t.save()
            d = 0.0
            last_pos = None
            for p in positions:
                p.track = t
                p.save()
                         
            tracks.append(t)

    return (tracks, len(tracks_positions))

@login_required
def upload_tracks(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            tracks = None
            uploaded_file = form.cleaned_data['track_data']

            only_after = None            
            if form.cleaned_data['only_newer']:
                tracks = Track.objects.filter(owner = request.user).order_by('date').reverse()
                if len(tracks) > 0:
                    only_after = tracks[0].date
            
            total_read_tracks = 0
            try:
                zip = ZipFile(uploaded_file)
                tracks = []
                for name in zip.namelist():
                    f = zip.open(name)
                    try:
                        (saved_tracks, number_read_tracks) = save_track_file(f, request.user, only_after)
                        tracks.extend(saved_tracks)
                        total_read_tracks = total_read_tracks + number_read_tracks
                    finally:
                        f.close()
            except BadZipfile:
                uploaded_file.seek(0)
                (tracks, total_read_tracks) = save_track_file(uploaded_file, request.user, only_after)
                      
            if len(tracks) > 0:
                return HttpResponseRedirect(reverse(user_timeline, 
                                            kwargs = {'username': tracks[len(tracks) - 1].owner.username}))
    else:
        form = UploadTrackForm()
        
    return render_to_response('upload_track.html', {'form': form}, context_instance=RequestContext(request))

def get_tracks_by_date(owner, year, month, day):
    d = datetime.datetime(year, month, day)
    return Track.objects.filter(owner = owner, date = d).order_by('created_time')

def get_track_by_date(owner, year, month, day, number):
    return Track.objects.get(owner=owner, date=d, number=number)
