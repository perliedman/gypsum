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
        var bounds = new L.LatLngBounds();
        $.each(positions, function(index, position) {
            var latlng = new L.LatLng(position.latitude, position.longitude);
            bounds.extend(latlng);
            points.push(latlng);
        });

        trackLine = new L.Polyline([], {
            color: '#ff0000',
            opacity: 0.6,
            weight: 6
        });

        map.addLayer(trackLine);
        map.fitBounds(bounds);

        infoPoints = data.info_points;
        isTrackOpen = data.is_open;

        setTimeout(function() { appendPath(map); }, 0);
    };

    function appendPath(map) {
        var path = trackLine.getLatLngs();
        if (path.length < points.length) {
            var infoPoint = infoPoints[path.length];
            if (infoPoint) {
                var marker = new L.Marker(points[path.length], {
                    title: infoPoint.distance + "km"
                });
                marker.bindPopup('<em>' + infoPoint.distance + 'km</em><br/>'
                        + '<em>Total time: ' + infoPoint.total_time + '</em></br/>'
                        + '<em>Speed: ' + infoPoint.pace + '</em><br/>');
                map.addLayer(marker);
            }

            trackLine.spliceLatLngs(path.length, 0, points[path.length]);
            setTimeout(function() { appendPath(map); }, 0);
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
