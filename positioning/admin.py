from gypsum.positioning.models import Track, Activity
from django.contrib import admin
from datetime import timedelta

def format_time(track):
    return str(timedelta(seconds = track.time))

class TrackAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'owner', 'activity', 'distance', format_time)

admin.site.register(Track, TrackAdmin)
admin.site.register(Activity)

