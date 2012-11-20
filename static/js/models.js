define(['backbone', 'underscore', 'moment'], function(Backbone, _, moment) {
    var TrackSummary = Backbone.Model.extend({

    });

    return {
        TrackSummary: TrackSummary,

        TrackCollection: Backbone.Collection.extend({
            model: TrackSummary,

            fetch: function(options) {
                options = options || {};

                var success = options.success,
                    error = options.error,
                    offset = options.offset,
                    that = this;

                if (offset) {
                    options.url = options.url || this.url;
                    options.url += "?offset=" + offset;
                }

                options.success = function(collection, response) {
                    that.trigger('endFetch', response.length);
                    if (success) {
                        success(collection, response);
                    }
                };
                options.error = function(collection, response) {
                    that.trigger('endFetch', null);
                    if (error) {
                        error(collection, response);
                    }
                };

                this.trigger('beginFetch');

                Backbone.Collection.prototype.fetch.call(this, options);
            }
        }),

        Track: Backbone.Model.extend({
            url: function() {
                return this.id + "/positions";
            },

            parse: function(response) {
                _.forEach(response.positions, function(p) {
                    p.date = moment(p.time);
                });

                return response;
            },

            getInfo: function() {
                var d = this.toJSON();
                d.position_density = d.positions.length / d.duration;
                d.position_period = d.duration / d.positions.length;
                d.data_gaps = _.reduce(d.positions, function(acc, p) {
                    if (acc.last_pos) {
                        var dt = p.date.diff(acc.last_pos.date),
                            ll1 = new L.LatLng(p.latitude, p.longitude),
                            ll2 = new L.LatLng(acc.last_pos.latitude, acc.last_pos.longitude),
                            d = ll1.distanceTo(ll2);

                        if (d > 100 && dt > 10 * 1000) {
                            acc.gaps.push({
                                start_time: p.date,
                                end_time: acc.last_pos.date,
                                duration: dt / 1000,
                                distance: ll1.distanceTo(ll2)
                            });
                        }
                    }

                    acc.last_pos = p;
                    return acc;
                }, {gaps: []}).gaps;

                return d;
            }
        }),

        Login: Backbone.Model.extend({
            url: function() {
                return 'api/v1/login'
            }
        })
    };
});