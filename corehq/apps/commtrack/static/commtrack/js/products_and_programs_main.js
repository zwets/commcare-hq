"use strict";
hqDefine('commtrack/js/products_and_programs_main', [
    'jquery',
    'knockout',
    'underscore',
    'hqwebapp/js/initial_page_data',
    'es6!hqwebapp/js/bootstrap5_loader',
    'commtrack/js/base_list_view_model',
    'hqwebapp/js/bootstrap5/widgets',   // "Additional Information" on product page uses a .hqwebapp-select2
    'commcarehq',
], function (
    $,
    ko,
    _,
    initialPageData,
    bootstrap,
    models
) {
    var commtrackProductsProgramsViewModel = function (o) {
        var self = models.BaseListViewModel(o);

        self.currentlySearching = ko.observable(false);

        self.colspan = ko.computed(function () {
            return 7;
        });

        self.init = function () {
            $(function () {
                self.change_page(self.current_page);
            });
        };

        self.change_page = function (page) {
            page = ko.utils.unwrapObservable(page);

            if (page) {
                self.currentlySearching(true);
                $.ajax({
                    url: formatURL(page),
                    dataType: 'json',
                    error: function () {
                        self.initialLoad(true);
                        $('.hide-until-load').removeClass("d-none");
                        $('#user-list-notification').text(gettext('Sorry, there was an problem contacting the server ' +
                            'to fetch the data. Please, try again in a little bit.'));
                        self.currentlySearching(false);
                    },
                    success: reloadList,
                });
            }

            return false;
        };

        self.unsuccessfulArchiveAction = function (button) {
            return function (data) {
                if (data.product_id) {
                    var alertContainer = $('#alert_' + data.product_id),
                        message = data.message || _.template(gettext("Could not <%= action %> product. Please try again later."))({action: $(button).text().toLowerCase()});
                    alertContainer.text(message);
                    alertContainer.removeClass("d-none");
                    var $modal = $(button).closest(".modal"),
                        modal = bootstrap.Modal.getOrCreateInstance($modal);
                    $modal.one('hidden.bs.modal', function () {
                        alertContainer.addClass("d-none");
                    });
                }
                $(button).enableButton();
            };
        };

        var reloadList = function (data) {
            self.currentlySearching(false);
            if (data.success) {
                if (!self.initialLoad()) {
                    self.initialLoad(true);
                    $('.hide-until-load').removeClass("d-none");
                }
                self.current_page(parseInt(data.current_page));
                self.dataList(data.data_list);
                self.archiveActionItems([]);
            }
        };
        var formatURL = function (page) {
            if (!page) {
                return "#";
            }
            return self.listURL + '?page=' + page +
                "&limit=" + self.pageLimit() +
                "&show_inactive=" + self.showInactive;
        };

        return self;
    };

    ko.bindingHandlers.isPrevNextDisabled = {
        update: function (element, valueAccessor) {
            var value = valueAccessor()();
            if (value === undefined) {
                $(element).parent().addClass('disabled');
            } else {
                $(element).parent().removeClass('disabled');
            }
        },
    };

    ko.bindingHandlers.isPaginationActive = {
        update: function (element, valueAccessor, allBindingsAccessor) {
            var currentPage = parseInt(valueAccessor()()),
                currentItem = parseInt(allBindingsAccessor()['text']);
            if (currentPage === currentItem) {
                $(element).parent().addClass('active');
            } else {
                $(element).parent().removeClass('active');
            }
        },
    };

    $(function () {
        var options = initialPageData.get('program_product_options');
        _.each($('.ko-program-product-list'), function (list) {
            var viewModel = commtrackProductsProgramsViewModel(options);
            $(list).koApplyBindings(viewModel);
            viewModel.init();
        });
    });
});
