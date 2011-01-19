# coding=utf-8
import math
import urllib2
from xml.dom import minidom
from datetime import datetime

def parse_float_or_none(s):
    try:
        return float(s)
    except ValueError:
        return None

class WeatherNotAvailableError(Exception):
    def __init__(self, message):
        self.message = message

class Weather:
    def __init__(self, time, wunderground_csv_line):
        cols = wunderground_csv_line.split(',')
        self.time = time
        self.temperature = parse_float_or_none(cols[1])
        self.dew_point = parse_float_or_none(cols[2])
        self.humidity = parse_float_or_none(cols[3])
        self.pressure_hpa = parse_float_or_none(cols[4])
        self.visibility_km = parse_float_or_none(cols[5])
        self.wind_dir = cols[6]
        self.wind_speed_kmh = parse_float_or_none(cols[7])
        self.gust_speed_kmh = parse_float_or_none(cols[8])
        self.precipitation_cm = parse_float_or_none(cols[9])
        self.events = cols[10]
        self.conditions = cols[11]
        self.wind_dir_degrees = cols[12]
        
        if self.temperature == -9999:
            self.temperature = None
        
    def __str__(self):
        return "Weather @ %s: %s, %.1f°C, wind %.0f km/h from %s. %s" % \
            (self.time.strftime('%Y-%m-%d %H:%M'),
             self.conditions, self.temperature, self.wind_speed_kmh, self.wind_dir, self.events)

DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi
EARTH_RADIUS = 6372795.0

def distance(lat1, lon1, lat2, lon2):
    lat1 = lat1 * DEG_TO_RAD
    lon1 = lon1 * DEG_TO_RAD
    lat2 = lat2 * DEG_TO_RAD
    lon2 = lon2 * DEG_TO_RAD
    dlat = lat2 - lat1;
    dlon = lon2 - lon1;
    sdlat = math.sin(dlat / 2.0);
    sdlon = math.sin(dlon / 2.0);

    a = sdlat * sdlat + \
        math.cos(lat1) * math.cos(lat2) * sdlon * sdlon;
    return 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)) * EARTH_RADIUS;

def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def get_weather_from_location(latitude, longitude, time):
    closest_station = get_closest_airport(latitude, longitude)
    return get_weather_from_station(closest_station, time)

def get_weather_from_station(station, time):
    w = get_best_weather_from_station(station, time)
    return Weather(w[1], w[2])
    
def get_best_weather_from_station(station, time):
    url = 'http://www.wunderground.com/history/airport/%s/%d/%d/%d/DailyHistory.html?format=1' % (station, time.year, time.month, time.day)
    f = urllib2.urlopen(url)
    datepart_str = time.strftime('%Y-%m-%d')
    best_match = (86400, None, None)
    
    try:
        lines = f.readlines()
        for line in lines[2:len(lines) - 1]:
            cols = line.split(',')
            if len(cols) != 13:
                raise WeatherNotAvailableError('No weather available for station "%s" at %s' % (station, datepart_str))
            
            observation_time = datetime.strptime('%s %s' % (datepart_str, cols[0]), '%Y-%m-%d %I:%M %p')
            diff = math.fabs(total_seconds(time - observation_time))
            if diff < best_match[0]:
                best_match = (diff, observation_time, line)
                
        return best_match
    finally:
        f.close()

def get_closest_airport(latitude, longitude):
    airports = get_airports(latitude, longitude)
    if len(airports) > 0:
        return airports[0][0]
    else:
        raise Exception("No airport found near %.3f, %.3f" % (latitude, longitude))

def get_airports(latitude, longitude):
    f = urllib2.urlopen('http://api.wunderground.com/auto/wui/geo/GeoLookupXML/index.xml?query=%f,%f' % (latitude, longitude))
    try:
        dom = minidom.parse(f)
        stations = []
        for airport in dom.getElementsByTagName('airport')[0].getElementsByTagName('station'):
            icao = getText(airport.getElementsByTagName('icao')[0].childNodes)
            if icao.isalnum():
                lat = float(getText(airport.getElementsByTagName('lat')[0].childNodes))
                lon = float(getText(airport.getElementsByTagName('lon')[0].childNodes))
                stations.append((icao, distance(latitude, longitude, lat, lon)))
            
        stations.sort(cmp=lambda x,y: cmp(x[1], y[1]))
        return stations
    finally:
        f.close()