import pymongo
from django.conf import settings

_connection = pymongo.Connection(settings.MONGO_HOST)
_db = _connection[settings.MONGO_DB]

class Position:
    def __init__(self, doc):
        self.latitude = doc['lat']
        self.longitude = doc['lon']
        self.altitude = doc['alt']
        self.time = doc['time']
        
    def save(self):
        _db.positions.insert({
            'lat': self.latitude,
            'lon': self.longitude,
            'alt': self.altitude,
            'time': self.time})
            
