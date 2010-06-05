import pymongo
from django.conf import settings

_connection = pymongo.Connection(settings.MONGO_HOST)
_db = _connection[settings.MONGO_DB]

class Track:
    def __init__(self):
        self.name = None
        self.owner_id = None    
        self.created_time = None
        
    def positions(self):    
        return [Position(p) for p in \
            _db.positions.find({'track': self.id}).sort('time', pymongo.ASCENDING)]            

    def save(self):
        self.id = _db.tracks.insert({
            'name': self.name,
            'owner_id': self.owner_id,
            'created_time': self.created_time})

    @classmethod
    def create(cls, doc):
        t = Track()
        t.id = doc['_id']
        t.name = doc['name']
        t.owner_id = doc['owner_id']
        t.created_time = doc['created_time']
        
        return t

    @classmethod
    def get(cls, id):
        doc = _db.tracks.find_one({'_id': id})
    
        if doc != None:
            return cls.create(doc)
        else:
            raise Exception('No track with id %s.' % (str(id)))

class Position:
    def __init__(self, doc):
        self.latitude = doc['lat']
        self.longitude = doc['lon']
        self.altitude = doc['alt']
        self.time = doc['time']
        self.track = doc['track']
        
    def save(self):
        _db.positions.insert({
            'lat': self.latitude,
            'lon': self.longitude,
            'alt': self.altitude,
            'time': self.time,
            'track': self.track})

