# Based on jmoirons mod_wsgi / virtualenv script:
# http://jmoiron.net/blog/deploying-django-mod-wsgi-virtualenv/

import sys
import site
import os

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
SITE_PARENT = os.path.join(SITE_ROOT, '..')
# add the app's directory to the PYTHONPATH
sys.path.append(SITE_PARENT)

import gypsum.secrets

vepath = gypsum.secrets.virtualenv

prev_sys_path = list(sys.path)

# add the site-packages of our virtualenv as a site dir
site.addsitedir(vepath)

# reorder sys.path so new directories from the addsitedir show up first
new_sys_path = [p for p in sys.path if p not in prev_sys_path]
for item in new_sys_path:
    sys.path.remove(item)
sys.path[:0] = new_sys_path

# import from down here to pull in possible virtualenv django install
from django.core.handlers.wsgi import WSGIHandler
os.environ['DJANGO_SETTINGS_MODULE'] = 'gypsum.settings'
application = WSGIHandler()
