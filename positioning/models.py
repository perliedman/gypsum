import pymongo
import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class Track(models.Model):
    name = models.CharField(max_length = 64)
    created_time = models.DateTimeField()
    owner = models.ForeignKey(User)

class Position:
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    track = models.ForeignKey(Track)
    
