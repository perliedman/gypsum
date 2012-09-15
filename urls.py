import socialregistration.urls
from django.conf.urls.defaults import *
from django.conf import settings
from gypsum.positioning import views, upload_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^gypsum/', include('gypsum.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^registration/', include(socialregistration.urls)),
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),

    (r'^$', views.start_page),
    (r'^tracks$', views.track_history),
    (r'^(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<number>\d+)/positions$', 'gypsum.positioning.views.get_track_data'),
    (r'^upload$', upload_views.upload_tracks),

    (r'^api/v1/upload$', upload_views.upload_tracks_ajax),
    (r'^api/v1/login$', views.login),
)

if settings.DEBUG:
    doc_root = settings.APP_DIR + '/static'
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': doc_root}),
    )
