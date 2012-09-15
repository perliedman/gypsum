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
        'upload': 'upload'
      },

      home: function() {
        var that = this;

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

      clearPanels: function() {
        $('#history').hide('slide');
        $('#info').hide('slide');
        if (this.trackMapView) {
          this.trackMapView.clear();
        }
      }
    });
});
