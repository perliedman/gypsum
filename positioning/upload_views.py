from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django import forms
from tasks import get_track_weather
from zipfile import ZipFile, BadZipfile
from gypsum.positioning.models import Track, Activity
from gypsum.positioning.gpxparser import GPXParser

from geopy import distance

import datetime, re
from django.template.context import RequestContext
from django.contrib import messages
from StringIO import StringIO
from gypsum.positioning.gpxparser import create_gpx
from gypsum.positioning.views import get_tracks_by_date, user_timeline

class UploadTrackForm(forms.Form):
    track_data = forms.FileField(label = 'File to upload',
        help_text = 'The file to upload. The file must be a GPX file, or a ZIP file containing GPX files.')
    only_newer = forms.BooleanField(label = 'Store only newer', initial = False, required=False)

def guess_activity(speed_kmh):
    result = None

    for activity in Activity.objects.order_by('max_speed').reverse():
        if speed_kmh <= activity.max_speed:
            result = activity

    return result

def sum_distance(positions):
    d = reduce(lambda acc, pos: (acc[0] + distance.distance((acc[1].latitude, acc[1].longitude), (pos.latitude, pos.longitude)).kilometers, pos), positions[1:len(positions)], (0, positions[0]))
    return d[0]

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
                time = duration.seconds,    # TODO: this will break for tracks longer than a day!
                positions = [p for p in gpx_track],
                distance = sum_distance(gpx_track))

            track.gpx = create_gpx(track, track.positions)
            track.hash = hash(track)

            avg_speed_kmh = track.distance / (duration.seconds / 3600.0) # TODO: this will break for tracks longer than a day!
            track.activity = guess_activity(avg_speed_kmh)

            track_models.append(track)

    return track_models

def save_track_file(file, user, only_after):
    def track_action(t):
        if only_after != None and t.date < only_after:
            return 'too_early'
        elif len(Track.objects.filter(owner = user, hash = t.hash)) > 0:
            return 'exists'
        else:
            return 'save'

    tracks = [(t, track_action(t)) for t in parse_gpx_tracks(user, file)]

    tracks_to_save = [t for (t, action) in tracks if action == 'save']
    for t in tracks_to_save:
        days_tracks = get_tracks_by_date(user, t.date.year, t.date.month, t.date.day)
        t.number = len(days_tracks)
        t.save()

    return tracks

def upload_tracks_from_stream(user, uploaded_file, only_newer):
    only_after = None
    if only_newer:
        tracks = Track.objects.filter(owner=user).order_by('date').reverse()
        if len(tracks) > 0:
            only_after = tracks[0].date

    all_tracks = []
    try:
        zip = ZipFile(uploaded_file)
        tracks = []
        for name in zip.namelist():
            f = zip.open(name)
            try:
                tracks.extend(save_track_file(f, user, only_after))
            finally:
                f.close()
    except BadZipfile:
        uploaded_file.seek(0)
        tracks = save_track_file(uploaded_file, user, only_after)

    if any(filter(lambda t: t[1] == 'save', tracks)):
        try:
            get_track_weather.delay()
        except:
            # TODO: log, show message, etc.
            pass

    return tracks

# --- VIEWS ---

def upload_tracks_ws(request):
    username = request.REQUEST['username']
    password = request.REQUEST['password']

    user = authenticate(username = username, password = password)
    if user is not None and user.is_active:
        only_newer = bool(request.REQUEST['only_newer'])
        stream = StringIO(request.REQUEST['data'])
        try:
            tracks = upload_tracks_from_stream(user, stream, only_newer)
            return HttpResponse(jsonencoder.dumps({'number_found_tracks': len(tracks),
                                                   'number_saved_tracks': len(filter(lambda t: t[1] == 'save', tracks))}),
                                                   mimetype='application/json')
        finally:
            stream.close()
    else:
        return HttpResponse(status=403)

@login_required
def upload_tracks(request):
    if request.method == 'POST':
        form = UploadTrackForm(request.POST, request.FILES)
        if form.is_valid():
            tracks = upload_tracks_from_stream(request.user, form.cleaned_data['track_data'], form.cleaned_data['only_newer'])

            redirect = False
            for track, action in tracks:
                if action == 'save':
                    messages.add_message(request, messages.INFO, "Saved track %s (%s - %.1f km)" % (track.name, str(track.activity), track.distance))
                    redirect = True
                elif action == 'too_early':
                    messages.add_message(request, messages.INFO, "Ignored track %s - it is not new (%s - %.1f km)" % (track.name, str(track.activity), track.distance))
                elif action == 'exists':
                    messages.add_message(request, messages.INFO, "Ignored track %s - already exists (%s - %.1f km; hash %d)" % (track.name, str(track.activity), track.distance, track.hash))

            if redirect:
                return HttpResponseRedirect(reverse(user_timeline,
                                            kwargs = {'username': request.user}))
    else:
        form = UploadTrackForm()

    return render_to_response('upload_track.html', {'form': form}, context_instance=RequestContext(request))
