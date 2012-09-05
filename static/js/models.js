define(['backbone'], function(Backbone) {
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
            }
        })
    };
});