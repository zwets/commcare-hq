hqDefine("app_manager/js/forms/form_view", function () {
    var initialPageData = hqImport("hqwebapp/js/initial_page_data"),
        appManagerUtils = hqImport('app_manager/js/app_manager');
    appManagerUtils.setPrependedPageTitle("\u2699 ", true);
    appManagerUtils.setAppendedPageTitle(gettext("Form Settings"));
    appManagerUtils.updatePageTitle(initialPageData.get("form_name"));

    function formFilterMatches(filter, substringMatches) {
        if (typeof(filter) !== 'string') {
            return false;
        }

        var result = false;
        $.each(substringMatches, function (index, sub) {
            result = result || filter.indexOf(sub) !== -1;
        });

        return result;
    }

    function formFilterModel() {
        var self = {};
        var patterns = initialPageData.get('form_filter_patterns');

        self.formFilter = ko.observable(initialPageData.get('form_filter'));

        self.caseReferenceNotAllowed = ko.computed(function () {
            var moduleUsesCase = initialPageData.get('all_other_forms_require_a_case') && initialPageData.get('form_requires') === 'case';
            if (!moduleUsesCase || (initialPageData.get('put_in_root') && !initialPageData.get('root_requires_same_case'))) {
                // We want to determine here if the filter expression references
                // any case but the user case.
                var filter = self.formFilter();
                if (typeof(filter) !== 'string') {
                    return true;
                }

                $.each(patterns.usercase_substring, function (index, sub) {
                    filter = filter.replace(sub, '');
                });

                if (formFilterMatches(filter, patterns.case_substring)) {
                    return true;
                }
            }
            return false;
        });

        self.isUsercaseInUse = ko.observable(initialPageData.get('is_usercase_in_use'));
        self.usercaseReferenceNotAllowed = ko.computed(function () {
            return !self.isUsercaseInUse() && formFilterMatches(
                self.formFilter(), patterns.usercase_substring
            );
        });

        self.enableUsercaseInProgress = ko.observable(false);
        self.enableUsercaseError = ko.observable();
        self.enableUsercase = function () {
            self.enableUsercaseInProgress(true);
            const url = initialPageData.reverse("enable_usercase");
            $.ajax(url, {
                method: "POST",
                success: function () {
                    self.isUsercaseInUse(true);
                },
                error: function () {
                    self.enableUsercaseInProgress(false);
                    self.enableUsercaseError(gettext("Could not enable user properties, please try again later."));
                },
            });
        };

        self.allowed = ko.computed(function () {
            return !self.formFilter() || !self.caseReferenceNotAllowed() && !self.usercaseReferenceNotAllowed();
        });

        return self;
    }

    $(function () {
        // Form name
        $(document).on("inline-edit-save", function (e, data) {
            if (_.has(data.update, '.variable-form_name')) {
                var appManager = hqImport('app_manager/js/app_manager');
                appManager.updatePageTitle(data.update['.variable-form_name']);
                appManager.updateDOM(data.update);
            }
        });

        // Validation for build
        var setupValidation = hqImport('app_manager/js/app_manager').setupValidation;
        setupValidation(initialPageData.reverse("validate_form_for_build"));

        // Analytics for renaming form
        $(".appmanager-edit-title").on('click', '.btn-primary', function () {
            hqImport('analytix/js/kissmetrix').track.event("Renamed form from form settings page");
        });

        // Settings > Logic
        var $formFilter = $('#form-filter');
        if ($formFilter.length && initialPageData.get('allow_form_filtering')) {
            $('#form-filter').koApplyBindings(formFilterModel());
        }

        var FormWorkflow = hqImport('app_manager/js/forms/form_workflow').FormWorkflow,
            labels = initialPageData.get('form_workflows');
        var options = {
            labels: labels,
            workflow: initialPageData.get('post_form_workflow'),
            workflow_fallback: initialPageData.get('post_form_workflow_fallback'),
        };

        if (_.has(labels, FormWorkflow.Values.FORM)) {
            options.forms = initialPageData.get('linkable_forms');
            options.formLinks = initialPageData.get('form_links');
            options.formDatumsUrl = initialPageData.reverse('get_form_datums');
        }

        $('#form-workflow').koApplyBindings(new FormWorkflow(options));

        // Settings > Advanced
        $('#auto-gps-capture').koApplyBindings({
            auto_gps_capture: ko.observable(initialPageData.get('auto_gps_capture')),
        });

        if (initialPageData.get('is_training_module')) {
            $('#release-notes-setting').koApplyBindings({
                is_release_notes_form: ko.observable(initialPageData.get('is_release_notes_form')),
                enable_release_notes: ko.observable(initialPageData.get('enable_release_notes')),
                is_allowed_to_be_release_notes_form: ko.observable(initialPageData.get('is_allowed_to_be_release_notes_form')),
                toggle_enable: function () {
                    var allowed = this.is_release_notes_form();
                    if (!allowed) {
                        this.enable_release_notes(false);
                    }
                    return true;
                },
            });
        }

        var $shadowParent = $('#shadow-parent');
        if ($shadowParent.length) {
            $shadowParent.koApplyBindings({
                shadow_parent: ko.observable(initialPageData.get('shadow_parent_form_id')),
            });
        }

        if (hqImport('hqwebapp/js/toggles').toggleEnabled('CUSTOM_INSTANCES')) {
            var customInstances = hqImport('app_manager/js/forms/custom_instances').wrap({
                customInstances: initialPageData.get('custom_instances'),
            });
            $('#custom-instances').koApplyBindings(customInstances);
        }

        // Case Management > Data dictionary descriptions for case properties
        $('.property-description').popover();

        // Advanced > XForm > Upload
        $("#xform_file_input").change(function () {
            if ($(this).val()) {
                $("#xform_file_submit").show();
            } else {
                $("#xform_file_submit").hide();
            }
        }).trigger('change');
    });
});
