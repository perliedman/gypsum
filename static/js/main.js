require([
  'jquery',
  './map',
  './track'
  ], function($, Map, track) {
  var map;
  var trackLine;
  var points;
  var infoPoints;
  var isTrackOpen;
  var currInfoWindow = null;

  $(document).ready(function() {
    $("#trackInfo").tabs();

    var map = Map.create('map');

    track.updateTrackData(map);
  });
});
