import sys, string
from xml.dom import minidom, Node
import datetime
from gypsum.positioning.models import Position
from elementtree.SimpleXMLWriter import XMLWriter
from StringIO import StringIO

class GPXParser:
  def __init__(self, filename):
    self.tracks = {}
    try:
      doc = minidom.parse(filename)
      doc.normalize()
    except:
      return # handle this properly later
    gpx = doc.documentElement
    for node in gpx.getElementsByTagName('trk'):
      self.parseTrack(node)

  def parseTrack(self, trk):
    name = trk.getElementsByTagName('name')[0].firstChild.data
    if not name in self.tracks:
      self.tracks[name] = []
    for trkseg in trk.getElementsByTagName('trkseg'):
      for trkpt in trkseg.getElementsByTagName('trkpt'):
        lat = float(trkpt.getAttribute('lat'))
        lon = float(trkpt.getAttribute('lon'))
        ele = float(trkpt.getElementsByTagName('ele')[0].firstChild.data)
        rfc3339 = trkpt.getElementsByTagName('time')[0].firstChild.data
        try:
            t = datetime.datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            t = datetime.datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%SZ')
        self.tracks[name].append(Position(latitude = lat, longitude = lon, altitude = ele, time = t))


def create_gpx(track, positions):
    f = StringIO()
    w = XMLWriter(f, 'utf-8')

    gpx = w.start('gpx', creator='Gypsum', version='1.1')

    w.start('trk')
    w.start('name')
    w.data(track.__unicode__())
    w.end('name')

    w.start('trkseg')

    for p in positions:
        w.start('trkpt', lat=str(p.latitude), lon=str(p.longitude))

        if p.altitude != None:
            w.start('ele')
            w.data(str(p.altitude))
            w.end('ele')
        w.start('time')
        w.data(datetime.datetime.strftime(p.time, '%Y-%m-%dT%H:%M:%S.%fZ'))
        w.end('time')

        w.end('trkpt')

    w.end('trkseg')

    w.end('trk')

    w.close(gpx)

    return f.getvalue()
