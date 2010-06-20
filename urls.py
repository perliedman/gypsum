from django.conf.urls.defaults import *
import gypsum.positioning.views

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
    
    (r'^report/positions$', 'gypsum.positioning.views.report'),
    (r'^report/newtrack$', 'gypsum.positioning.views.begin_track'),
    (r'^tracks/(\d{4})/(\d{2})/(\d{2})/(\d+)/$', 'gypsum.positioning.views.display_track'),
    (r'^tracks/(\d{4})/(\d{2})/(\d{2})/(\d+)/positions$', 'gypsum.positioning.views.get_track_data'),
    (r'^tracks/upload$', 'gypsum.positioning.views.upload_track'),
)
