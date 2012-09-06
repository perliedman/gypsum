define([
    'backbone',
    'hbt!../templates/track-row',
    'hbt!../templates/track-list-header',
    'hbt!../templates/track-info',
    'hbt!../templates/marker-template'],
    function(Backbone, trackRowTemplate, trackListHeaderTemplate, trackInfoTemplate, markerTemplate) {

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
            renderTime: 5 * 1000, // milliseconds

            lineStyles: [
                {
                    color: '#000000',
                    opacity: 0.2,
                    weight: 9
                },
                {
                    color: '#ffffff',
                    opacity: 1,
                    weight: 6
                },
                {
                    color: '#ff4000',
                    opacity: 1,
                    weight: 3
                }
            ],

            initialize: function(options) {
                this.map = options.map;
                this.markers = new L.FeatureGroup();
                this.map.addLayer(this.markers);
                this.trackLines = new L.FeatureGroup();
                this.map.addLayer(this.trackLines);
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

                this.positionIndex = 0;

                _.each(this.lineStyles, function(style) {
                    var line = new L.Polyline([], style);
                    that.trackLines.addLayer(line);
                });

                this.map.fitBounds(bounds);

                this.infoPoints = this.model.get('info_points');

                this.renderStart = Date.now();
                this.timer = setTimeout(function() { that.appendPath(); }, 0);

                return this;
            },

            appendPath: function() {
                var that = this;
                if (this.positionIndex < this.points.length) {
                    var expectedNumberPositions = Math.min(Math.ceil(this.points.length * (Date.now() - this.renderStart) / this.renderTime), this.points.length),
                        positionsToAdd = expectedNumberPositions - this.positionIndex;
                        spliceArgs = [this.positionIndex, 0];

                    for (var i = this.positionIndex; i < this.positionIndex + positionsToAdd; i++) {
                        var infoPoint = this.infoPoints[i];
                        if (infoPoint) {
                            var title = infoPoint.distance + " km",
                                marker = new L.Marker(this.points[i], {
                                    title: title,
                                    icon: new L.Icon.Label.Default({ labelText: title})
                                });
                            marker.bindPopup(markerTemplate(infoPoint));
                            this.markers.addLayer(marker);
                        }
                        spliceArgs.push(this.points[i]);
                    }

                    this.trackLines.eachLayer(function(line) {
                        L.Polyline.prototype.spliceLatLngs.apply(line, spliceArgs);
                    });

                    this.positionIndex += positionsToAdd;

                    this.timer = setTimeout(function() { that.appendPath(); }, 0);
                }
            },

            clear: function() {
                clearTimeout(this.timer);
                this.map.removeLayer(this.markers);
                this.map.removeLayer(this.trackLines);
            }
        })
    };
});