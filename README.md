# Gypsum

[![Greenkeeper badge](https://badges.greenkeeper.io/perliedman/gypsum.svg)](https://greenkeeper.io/)

Gypsum lets you upload tracks from your GPS (or something) using GPX format, stores them in a database and displays them on a map together with a bunch of statistics.

Multiple users are supported, you can get basic statistics for each user per month, etc.

Gypsum is written in Python with Django.

## Installation

Gypsum is a pretty basic Django app. If you know your way around Django, there shouldn't be any surprises.

In `settings.py`, I have made it possible to break out sensitive stuff like database configuration and passwords (to avoid uploading them to GitHub, like I did). Secrets are put in a file called `secrets.py` in Gypsum's directory. Example of contents for `secrets.py`:

    databases = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'gypsum',
            'USER': 'gypsum',
            'PASSWORD': 'Tr0ub4dor&3',
            'HOST': 'my.db.host'
        }
    }
