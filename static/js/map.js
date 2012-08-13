define(function() {
  return {
    create: function(id) {
      var url = "http://a.tiles.mapbox.com/v3/liedman.map-5qqfez0n.jsonp";
      var map = new L.Map(id);
      wax.tilejson(url, function(tilejson) {
        map.addLayer(new wax.leaf.connector(tilejson));
      });

      return map;
    }
  };
});