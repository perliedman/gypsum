define([
  'backbone',
  'jquery',
  './models',
  './views'
  ], function (Backbone, $, models, views) {

  return Backbone.Router.extend({
      initialize: function(options) {
        this.map = options.map;
        this.hasFetchedHistory = false;
        this.history = options.history;
        this.trackMapView = null;
      },

      routes: {
        '': 'home',
        ':user/:year/:month/:day/:number': 'displayTrack',
        'upload': 'upload',
        'add-track': 'addTrack'
      },

      home: function() {
        var that = this;

        // This is a hack to initialize the map view if it
        // hasn't already been initialized.
        try {
          this.map.getCenter();
        } catch (exception) {
          this.map.setView([57.74, 11.93], 10);
        }

        if (!this.hasFetchedHistory) {
          this.history.fetch({
            success: function() {
              that.hasFetchedHistory = true;
            }
          });
        }

        $('#history').show();
      },

      displayTrack: function(user, year, month, day, number) {
        var that = this,
            model = new models.Track({id: user + '/' + year + '/' + month + '/' + day + '/' + number});
        model.fetch({ success: function(model) {
          new views.TrackInformation({
            model: model,
            el: $('#info')
          }).render();

          if (that.trackMapView) {
            that.trackMapView.clear();
          }

          that.trackMapView = new views.TrackMap({
            model: model,
            el: $('#map'),
            map: that.map
          }).render();

          $('#info').show('slide');
          $('#history').hide('slide');
        }});
      },

      upload: function() {
        $('#upload-result').hide();
        $('#upload-track-modal').modal('show');
      },

      addTrack: function() {
        this.clearPanels();
        $('#add-track-control').show();

        var handler = new L.Polyline.Draw(this.map, {});
        handler.enable();
      },

      clearPanels: function() {
        $('#history').hide('slide');
        $('#info').hide('slide');
        if (this.trackMapView) {
          this.trackMapView.clear();
        }
      }
    });
});
