from django.core.serializers import serialize
from django.utils.simplejson import dumps, loads, JSONEncoder
from django.db.models.query import QuerySet
from django.db.models import Model
from django.utils.functional import curry
import datetime

# Well, this isn't as generalized as it could be. But enough
# for this app. Would be interesting with a "real" solution, though.
class GeneralizedJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, object):
            return obj.__dict__

        return JSONEncoder.default(self, obj)

# partial function, we can now use dumps(my_dict) instead
# of dumps(my_dict, cls=DjangoJSONEncoder)
dumps = curry(dumps, cls=GeneralizedJSONEncoder)
