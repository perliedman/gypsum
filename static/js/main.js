require([
  'jquery',
  './map',
  './models',
  './views',
  'handlebars',
  'backbone',
  './router',
  'hbt!../templates/upload-result',
  './jam/bootstrap/js/bootstrap-tab',
  './jam/bootstrap/js/bootstrap-modal',
  './jam/bootstrap/js/bootstrap-transition',
  './jam/bootstrap/js/bootstrap-collapse'
  ], function($, Map, models, views, Handlebars, Backbone, Router, uploadResult) {

  var map = Map.create('map'),
      history = setupHistory(),
      router = new Router({map: map, history: history}),
      login;

  setupLogin(window.currentLogin);
  setupUpload();

  Backbone.history.start();

  Handlebars.registerHelper('numberFormat', function(number, maxDecimals) {
    var f = 1;
    for (var i = 0; i < maxDecimals; i++) {
      f *= 10;
    }

    return parseInt(number * f) / f;
  });

  function setupLogin(currentLogin) {
    if (currentLogin) {
      setLogin(new models.Login(currentLogin));
    }

    $('#login-button').click(function() {
      var username = $('#login-control input[type=text]').val(),
          password = $('#login-control input[type=password]').val();

      new models.Login({username: username, password: password}).save({}, {
        success: function(model) {
          if (model.get('success')) {
            setLogin(model);
          } else {
            alert(model.get('code'));
          }
        },
        error: function() { alert('Login failed. :(');}
      });
    });

    $('#logout-button').click(function() {
      setLoggedOut();
    });
  }

  function setLogin(model) {
    login = model;
    new views.Login({model: login, el: $('#logged-in-control')}).render();
    $('#login-control').hide();
    $('#logged-in-control').show();
    $('#logged-in-menu').show();
  }

  function setLoggedOut() {
      if (login) {
        login.destroy();
      }

      $('#login-control').show();
      $('#logged-in-control').hide();
      $('#logged-in-menu').hide();

      login = null;
  }

  function setupUpload() {
    $('#upload-track-button').click(function() {
      var formData = new FormData($('#upload-track-form')[0]);
      $.ajax({
        url: 'api/v1/upload',
        type: 'POST',
        xhr: function() {
          var _xhr = $.ajaxSettings.xhr();
          if (_xhr.upload) {
            _xhr.upload.addEventListener('progress', uploadProgress, false);
          }

          return _xhr;
        },
        beforeSend: function() {
          $('progress').show();
        },
        success: function(data) {
          $('progress').hide();

          var groups = _.reduce(data.tracks, function(memo, trackData) {
            if (!memo[trackData.action]) {
              memo[trackData.action] = [];
            }

            memo[trackData.action].push(trackData.track);
            return memo;
          }, {});

          $('#upload-result').html(uploadResult({groups: groups, numberTracks: data.tracks.length})).show('slide');
        },
        error: function() {
          $('progress').hide();
          alert('Error! :(');
        },
        data: formData,
        cache: false,
        contentType: false,
        processData: false
      });
    });
  }

  function uploadProgress(e) {
    if (e.lengthComputable) {
      if (e.loaded < e.total) {
        $('progress').attr({value: e.loaded, max: e.total});
      } else {
        $('progress').attr({value: null, max: null});
      }
    }
  }

  function setupHistory() {
    var History = models.TrackCollection.extend({
        url: 'tracks',
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
