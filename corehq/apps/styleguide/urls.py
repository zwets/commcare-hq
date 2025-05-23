from django.urls import include, re_path as url

from corehq.apps.styleguide.examples.bootstrap5.example_urls import urlpatterns as example_urlpatterns
from corehq.apps.styleguide.examples.bootstrap5.htmx_alpine_form_views import (
    HtmxAlpineFormDemoView,
    FilterDemoFormView,
)
from corehq.apps.styleguide.examples.bootstrap5.htmx_hq_hx_action import TodoListDemoView
from corehq.apps.styleguide.views import (
    AtomsStyleGuideView,
    MainStyleGuideView,
    MoleculesStyleGuideView,
    OrganismsStyleGuideView,
    PagesStyleGuideView,
)
from corehq.apps.styleguide.views.docs import default

from corehq.apps.styleguide.views import bootstrap5
from corehq.apps.styleguide.views import bootstrap5_data

doc_urlpatterns = [
    url(r'^$', default, name='sg_examples_default'),
    url(r'^simple_crispy/',
        include('corehq.apps.styleguide.examples.simple_crispy_form.urls')),
]

advanced_demo_urlpatterns = [
    url(r'^htmx_todo/$', TodoListDemoView.as_view(), name=TodoListDemoView.urlname),
    url(r'^htmx_alpine_form/$', HtmxAlpineFormDemoView.as_view(), name=HtmxAlpineFormDemoView.urlname),
    url(r'^htmx_alpine_form/form/$', FilterDemoFormView.as_view(), name=FilterDemoFormView.urlname),
]

urlpatterns = [
    url(r'^$', MainStyleGuideView.as_view(), name=MainStyleGuideView.urlname),
    url(r'^atoms/$', AtomsStyleGuideView.as_view(),
        name=AtomsStyleGuideView.urlname),
    url(r'^molecules/$', MoleculesStyleGuideView.as_view(),
        name=MoleculesStyleGuideView.urlname),
    url(r'^organisms/$', OrganismsStyleGuideView.as_view(),
        name=OrganismsStyleGuideView.urlname),
    url(r'^pages/$', PagesStyleGuideView.as_view(),
        name=PagesStyleGuideView.urlname),
    url(r'^docs/', include(doc_urlpatterns)),
    url(r'^demo/', include(advanced_demo_urlpatterns)),
    url(r'^b5/$', bootstrap5.styleguide_home, name="styleguide_home_b5"),
    url(r'^b5/data/select2_ajax_demo$', bootstrap5_data.select2_ajax_demo,
        name="styleguide_data_select2_ajax_demo"),
    url(r'^b5/data/remote_modal_demo$', bootstrap5_data.remote_modal_demo,
        name="styleguide_data_remote_modal"),
    url(r'^b5/data/inline_edit_demo$', bootstrap5_data.inline_edit_demo,
        name="styleguide_inline_edit_demo"),
    url(r'^b5/data/submit_feedback_demo$', bootstrap5_data.submit_feedback_demo,
        name="styleguide_submit_feedback_demo"),
    url(r'^b5/data/validate_ko_demo$', bootstrap5_data.validate_ko_demo,
        name="styleguide_validate_ko_demo"),
    url(r'^b5/data/datatables_data$', bootstrap5_data.datatables_data,
        name="styleguide_datatables_data"),
    url(r'^b5/data/paginated_table_data$', bootstrap5_data.paginated_table_data,
        name="styleguide_paginated_table_data"),
    url(r'^b5/data/a_hanging_view$', bootstrap5_data.a_hanging_view,
        name="styleguide_a_hanging_view"),
    url(r'^b5/example/', include(example_urlpatterns)),
    url(r'^b5/guidelines/$', bootstrap5.styleguide_code_guidelines,
        name="styleguide_code_guidelines_b5"),
    url(r'^b5/migration/$', bootstrap5.styleguide_migration_guide,
        name="styleguide_migration_guide_b5"),
    url(r'^b5/javascript/$', bootstrap5.styleguide_javascript_guide,
        name="styleguide_javascript_guide_b5"),
    url(r'^b5/htmx_alpine/$', bootstrap5.styleguide_htmx_and_alpine,
        name="styleguide_htmx_and_alpine_b5"),
    url(r'^b5/atoms/accessibility/$', bootstrap5.styleguide_atoms_accessibility,
        name="styleguide_atoms_accessibility_b5"),
    url(r'^b5/atoms/typography/$', bootstrap5.styleguide_atoms_typography,
        name="styleguide_atoms_typography_b5"),
    url(r'^b5/atoms/colors/$', bootstrap5.styleguide_atoms_colors,
        name="styleguide_atoms_colors_b5"),
    url(r'^b5/atoms/icons/$', bootstrap5.styleguide_atoms_icons,
        name="styleguide_atoms_icons_b5"),
    url(r'^b5/molecules/buttons/$', bootstrap5.styleguide_molecules_buttons,
        name="styleguide_molecules_buttons_b5"),
    url(r'^b5/molecules/selections/$', bootstrap5.styleguide_molecules_selections,
        name="styleguide_molecules_selections_b5"),
    url(r'^b5/molecules/checkboxes/$', bootstrap5.styleguide_molecules_checkboxes,
        name="styleguide_molecules_checkboxes_b5"),
    url(r'^b5/molecules/modals/$', bootstrap5.styleguide_molecules_modals,
        name="styleguide_molecules_modals_b5"),
    url(r'^b5/molecules/pagination/$', bootstrap5.styleguide_molecules_pagination,
        name="styleguide_molecules_pagination_b5"),
    url(r'^b5/molecules/searching/$', bootstrap5.styleguide_molecules_searching,
        name="styleguide_molecules_searching_b5"),
    url(r'^b5/molecules/inline_editing/$', bootstrap5.styleguide_molecules_inline_editing,
        name="styleguide_molecules_inline_editing_b5"),
    url(r'^b5/molecules/help/$', bootstrap5.styleguide_molecules_help,
        name="styleguide_molecules_help_b5"),
    url(r'^b5/molecules/feedback/$', bootstrap5.styleguide_molecules_feedback,
        name="styleguide_molecules_feedback_b5"),
    url(r'^b5/molecules/dates-times/$', bootstrap5.styleguide_molecules_dates_times,
        name="styleguide_molecules_dates_times_b5"),
    url(r'^b5/organisms/forms/$', bootstrap5.styleguide_organisms_forms,
        name="styleguide_organisms_forms_b5"),
    url(r'^b5/organisms/tables/$', bootstrap5.styleguide_organisms_tables,
        name="styleguide_organisms_tables_b5"),
    url(r'^b5/pages/navigation/$', bootstrap5.styleguide_pages_navigation,
        name="styleguide_pages_navigation_b5"),
    url(r'^b5/pages/views/$', bootstrap5.styleguide_pages_views,
        name="styleguide_pages_views_b5"),
]
