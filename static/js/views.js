define([
    'backbone',
    'hbt!../templates/track-row',
    'hbt!../templates/track-list-header',
    'hbt!../templates/track-info'],
    function(Backbone, trackRowTemplate, trackListHeaderTemplate, trackInfoTemplate) {

    var TrackRow = Backbone.View.extend({
        tagName: 'tr',

        render: function() {
            this.$el.html(trackRowTemplate(this.model.toJSON()));
            return this;
        },
    });

    return {
        TrackList: Backbone.View.extend({
            tagName: 'table',
            className: 'table table-striped track-list',

            initialize: function() {
                this.model.on('reset', this.render, this);
                this.model.on('add', function(m) {
                    var that = this;

                    var row = new TrackRow({model: m});
                    row.render();
                    this.$el.append(row.el);

                    row.$el.click(function() {
                        that.rowSelected(m)
                    });
                }, this);
            },

            render: function() {
                var that = this;

                that.$el.empty();
                that.$el.append($(trackListHeaderTemplate()));
                this.model.forEach(function(m) {
                    var row = new TrackRow({model: m});
                    row.render();
                    that.$el.append(row.el);

                    row.$el.click(function() {
                        that.rowSelected(m)
                    });
                });
                return this;
            },

            rowSelected: function(rowModel) {
                // Do nothing
            }
        }),

        TrackInformation: Backbone.View.extend({
            render: function() {
                this.$el.html(trackInfoTemplate(this.model.toJSON()));

                return this;
            }
        }),

        TrackMap: Backbone.View.extend({
            initialize: function(options) {
                this.map = options.map;
                this.markers = [];
                this.timer = null;
            },

            render: function() {
                var positions = this.model.get('positions');
                this.points = [];
                var bounds = new L.LatLngBounds();
                var that = this;
                _.each(positions, function(position) {
                    var latlng = new L.LatLng(position.latitude, position.longitude);
                    bounds.extend(latlng);
                    that.points.push(latlng);
                });

                this.trackLine = new L.Polyline([], {
                    color: '#ff0000',
                    opacity: 0.6,
                    weight: 6
                });

                this.map.addLayer(this.trackLine);
                this.map.fitBounds(bounds);

                this.infoPoints = this.model.get('info_points');

                this.timer = setTimeout(function() { that.appendPath(); }, 0);

                return this;
            },

            appendPath: function() {
                var path = this.trackLine.getLatLngs(),
                    that = this;
                if (path.length < this.points.length) {
                    var infoPoint = this.infoPoints[path.length];
                    if (infoPoint) {
                        var marker = new L.Marker(this.points[path.length], {
                            title: infoPoint.distance + "km"
                        });
                        marker.bindPopup('<em>' + infoPoint.distance + 'km</em><br/>'
                                + '<em>Total time: ' + infoPoint.total_time + '</em></br/>'
                                + '<em>Speed: ' + infoPoint.pace + '</em><br/>');
                        this.map.addLayer(marker);
                        this.markers.push(marker);
                    }

                    this.trackLine.spliceLatLngs(path.length, 0, this.points[path.length]);
                    this.timer = setTimeout(function() { that.appendPath(); }, 0);
                }
            },

            clear: function() {
                var that = this;
                clearTimeout(this.timer);
                this.map.removeLayer(this.trackLine);
                _.each(this.markers, function(marker) { that.map.removeLayer(marker); });
            }
        })
    };
});