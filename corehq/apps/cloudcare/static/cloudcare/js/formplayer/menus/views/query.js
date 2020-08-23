/*global _, FormplayerFrontend, Marionette */

hqDefine("cloudcare/js/formplayer/menus/views/query", function () {
    var QueryView = Marionette.View.extend({
        tagName: "tr",
        className: "formplayer-request",
        template: _.template($("#query-view-item-template").html() || ""),

        templateContext: function () {
            var imageUri = this.options.model.get('imageUri');
            var audioUri = this.options.model.get('audioUri');
            var appId = this.model.collection.appId;
            return {
                imageUrl: imageUri ? FormplayerFrontend.getChannel().request('resourceMap', imageUri, appId) : "",
                audioUrl: audioUri ? FormplayerFrontend.getChannel().request('resourceMap', audioUri, appId) : "",
            };
        },
    });

    var QueryTableView = Marionette.CollectionView.extend({
        childView: QueryView,
        tagName: "tbody",
    });

    var QueryListView = Marionette.View.extend({
        tagName: "div",
        template: _.template($("#query-view-list-template").html() || ""),

        regions: {
            body: {
                el: 'table',
            },
        },
        onRender: function () {
            this.getRegion('body').show(new QueryTableView({
                collection: this.collection,
            }));
        },

        initialize: function (options) {
            this.parentModel = options.collection.models;
        },

        templateContext: function () {
            return {
                title: this.options.title,
            };
        },

        ui: {
            submitButton: '#query-submit-button',
        },

        events: {
            'click @ui.submitButton': 'submitAction',
        },

        submitAction: function (e) {
            e.preventDefault();
            var payload = {};
            var fields = $(".query-field");
            var model = this.parentModel;
            fields.each(function (index) {
                if (this.value !== '') {
                    payload[model[index].get('id')] = this.value;
                }
            });
            FormplayerFrontend.trigger("menu:query", payload);
        },
    });

    return function (data) {
        return new QueryListView(data);
    };
});
