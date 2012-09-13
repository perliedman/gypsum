require([
  'jquery',
  './map',
  './track',
  './models',
  './views',
  'handlebars',
  'backbone',
  './router',
  './jam/bootstrap/js/bootstrap-tab'
  ], function($, Map, track, models, views, Handlebars, Backbone, Router) {

  var map = Map.create('map'),
      history = setupHistory(),
      router = new Router({map: map, history: history});

  Backbone.history.start();

  Handlebars.registerHelper('numberFormat', function(number, maxDecimals) {
    var f = 1;
    for (var i = 0; i < maxDecimals; i++) {
      f *= 10;
    }

    return parseInt(number * f) / f;
  });

  function setupLogin() {
    $('#login-button').click(function() {
      var username = $('#login-control input[type=text]'),
          password = $('#login-control input[type=password]');
      alert(username + ' ' + password);
    })
  }

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
        $('#history-refresh').show('slide');
      } else {
        $('#history-refresh').hide('slide');
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
