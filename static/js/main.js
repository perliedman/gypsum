require([
  'jquery',
  './map',
  './track',
  './models',
  './views',
  'handlebars',
  'backbone'
  ], function($, Map, track, models, views, Handlebars, Backbone) {

  Handlebars.registerHelper('numberFormat', function(number, maxDecimals) {
    var f = 1;
    for (var i = 0; i < maxDecimals; i++) {
      f *= 10;
    }

    return parseInt(number * f) / f;
  });

  var map = Map.create('map'),
      trackMapView = null,
      hasFetchedHistory = false;

  var Router = Backbone.Router.extend({
    routes: {
      '': 'home',
      ':user/:year/:month/:day/:number': 'displayTrack'
    },

    home: function() {
      if (!hasFetchedHistory) {
        history.fetch({
          success: function() {
            hasFetchedHistory = true;
          }
        });
      }

      $('#history').show();
    },

    displayTrack: function(user, year, month, day, number) {
      var model = new models.Track({id: user + '/' + year + '/' + month + '/' + day + '/' + number});
      model.fetch({ success: function(model) {
        new views.TrackInformation({
          model: model,
          el: $('#info')
        }).render();

        if (trackMapView) {
          trackMapView.clear();
        }

        trackMapView = new views.TrackMap({
          model: model,
          el: $('#map'),
          map: map
        }).render();

        $('#info').show();
        $('#history').hide();
      }});
    }
  }),
    router = new Router(),
    history = setupHistory();

  Backbone.history.start();

  function setupHistory() {
    var History = models.TrackCollection.extend({
        url: '/tracks',
      }),
      offset = 0,
      history = new History(),
      historyView = new views.TrackList({
        map: map,
        model: history,
      });

    historyView.rowSelected = function(rowModel) {
      router.navigate(rowModel.get('owner').username + '/' + rowModel.get('date').replace(/-/g, '/') + '/' + rowModel.get('number'),
        {trigger: true});
    };

    $('#history-table-wrapper').append(historyView.el);

    history.on('beginFetch', function() { $('#history-throbber').show();});
    history.on('endFetch', function(rowsFetched) {
      $('#history-throbber').hide();
      if (rowsFetched === null || rowsFetched > 0) {
        offset += rowsFetched;
        $('#history-refresh').show();
      } else {
        $('#history-refresh').hide();
      }
    });

    $('#history-refresh-button').click(function() {
      history.fetch({
        add: true,
        offset: offset
      })
    });

    return history;
  }
});
