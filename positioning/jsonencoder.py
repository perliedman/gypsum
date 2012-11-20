from django.utils.simplejson import dumps, loads, JSONEncoder
from django.db.models.query import QuerySet
from django.db.models import Model
from django.utils.functional import curry
import datetime
import time

# Well, this isn't as generalized as it could be. But enough
# for this app. Would be interesting with a "real" solution, though.
class GeneralizedJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, object):
            return dict(filter(lambda (x,y): not x.startswith('_'), obj.__dict__.items()))

        return JSONEncoder.default(self, obj)

# partial function, we can now use dumps(my_dict) instead
# of dumps(my_dict, cls=DjangoJSONEncoder)
dumps = curry(dumps, cls=GeneralizedJSONEncoder)
