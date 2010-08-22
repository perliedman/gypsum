from gypsum.positioning.models import Track, Activity
from django.contrib import admin
from datetime import timedelta

def format_time(track):
    return str(timedelta(seconds = track.time))
format_time.short_description = 'Time'

def format_distance(track):
    return '%.1f' % track.distance
format_distance.short_description = 'Distance'

class TrackAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'owner', 'activity', format_distance, format_time)
    list_editable = ('owner', 'activity')

admin.site.register(Track, TrackAdmin)
admin.site.register(Activity)

