from django.conf.urls.defaults import *
from gypsum.positioning import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^gypsum/', include('gypsum.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    
    (r'^report/positions$', views.report),
    (r'^report/newtrack$', views.begin_track),
    (r'^(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<number>\d+)/$', views.display_track),
    (r'^(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<number>\d+)/positions$', views.get_track_data),
    (r'^upload$', views.upload_tracks),
)
