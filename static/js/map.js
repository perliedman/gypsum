define(function() {
  return {
    create: function(id) {
      var latlng = new google.maps.LatLng(57.8, 11.9);
      var myOptions = {
        zoom: 8,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      var map = new google.maps.Map(document.getElementById(id), myOptions);

      return map;
    }
  };
});