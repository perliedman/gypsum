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

  setupLogin();

  Backbone.history.start();

  Handlebars.registerHelper('numberFormat', function(number, maxDecimals) {
    var f = 1;
    for (var i = 0; i < maxDecimals; i++) {
      f *= 10;
    }

    return parseInt(number * f) / f;
  });

  function setupLogin() {
    var login;

    $('#login-button').click(function() {
      var username = $('#login-control input[type=text]').val(),
          password = $('#login-control input[type=password]').val();
      login = new models.Login({username: username, password: password});
      login.save({}, {
        success: function(model) {
          if (model.get('success')) {
            login = model;
            new views.Login({model: login, el: $('#logged-in-control')}).render();
            $('#login-control').hide();
            $('#logged-in-control').show();
          } else {
            alert(model.get('code'));
          }
        },
        error: function() { alert('Login failed. :(');}
      });
    });

    $('#logout-button').click(function() {
      if (login) {
        login.destroy();
        $('#login-control').show();
        $('#logged-in-control').hide();
      }
    });
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
