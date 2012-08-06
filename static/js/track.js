define(['jquery'], function($) {
    function displayTrackData(data, map) {
    if (data['name'] != null && data['name'].length > 0) {
        $("#trackName").text(data['name']);
        $("#trackNameRow").show();
    } else {
        $("#trackNameRow").hide();
    }
    $("#trackDate").text(data['date']);
    $("#trackDistance").text((Math.round(data['distance'] * 100) / 100).toFixed(2) + " km");
    $("#trackDuration").text(data['duration']);
    $("#trackTime").text(data['start_time'] + " - " + data['end_time'] + ' (UTC)');
    $("#trackPace").text(data['pace']);
    $("#trackCreationTime").text(data['created_time']);
    $("#paceChart").attr("src", data['pace_chart_url']);
    $("#elevationChart").attr("src", data['elevation_chart_url']);

    var positions = data['positions'];
    points = [];
    var bounds = new google.maps.LatLngBounds();
    $.each(positions, function(index, position) {
        var latlng = new google.maps.LatLng(position.fields.latitude, position.fields.longitude);
        bounds.extend(latlng);
        points.push(latlng);
    });

    trackLine = new google.maps.Polyline({
        path: [],
        strokeColor: '#ff0000',
        strokeOpacity: 0.6,
        strokeWeight: 6
    });

    trackLine.setMap(map);
    map.fitBounds(bounds);

    infoPoints = data.info_points;
    isTrackOpen = data.is_open;

    setTimeout(function() { appendPath(map); }, 0);
  };

  function appendPath(map) {
    var path = trackLine.getPath();
    if (path.length < points.length) {
        var infoPoint = infoPoints[path.length];
        if (infoPoint) {
            var marker = new google.maps.Marker({
                position: points[path.length],
                map: map,
                title: infoPoint.distance + "km"
            });
            var infoWindow = new google.maps.InfoWindow({
                content: '<em>' + infoPoint.distance + 'km</em><br/>'
                    + '<em>Total time: ' + infoPoint.total_time + '</em></br/>'
                    + '<em>Speed: ' + infoPoint.pace + '</em><br/>'
            });
            google.maps.event.addListener(marker, 'click', function() {
                if (currInfoWindow != null) {
                    currInfoWindow.close();
                }

                infoWindow.open(map, marker);
                currInfoWindow = infoWindow;
            });
        }

        path.insertAt(path.length, points[path.length]);
        setTimeout(appendPath, 0);
    } else if (isTrackOpen) {
        setTimeout(updateTrackData, 30);
    }
  };

  return {
    updateTrackData: function(map) {
      $.getJSON('positions', function(data) { displayTrackData(data, map); });
    }
  };
});
