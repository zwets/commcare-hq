from __future__ import absolute_import
from __future__ import unicode_literals

import json
from collections import defaultdict, namedtuple

from corehq.apps.app_manager.dbaccessors import get_current_app
from corehq.apps.export.dbaccessors import get_latest_case_export_schema, get_latest_form_export_schema
from corehq.apps.export.models import CaseExportDataSchema, ExportInstance, ExportItem, FormExportDataSchema
from corehq.apps.reports.analytics.esaccessors import get_case_types_for_domain_es
from corehq.util.datadog.gauges import datadog_counter
from corehq.util.datadog.utils import bucket_value


FieldMetadata = namedtuple('FieldMetadata', ['name', 'odata_type'])


def get_case_type_to_properties(domain):
    case_type_to_properties = defaultdict(list)
    case_types = get_case_types_for_domain_es(domain)
    for case_type in case_types:
        if not case_type:
            # TODO - understand why a case can have a blank case type and handle appropriately
            continue
        case_export_schema = (
            get_latest_case_export_schema(domain, case_type)
            or CaseExportDataSchema.generate_schema_from_builds(domain, None, case_type)
        )
        for export_group_schema in case_export_schema.group_schemas[0].items:
            case_type_to_properties[case_type].append(export_group_schema.label)
    return dict(case_type_to_properties)


def get_xmlns_to_properties(domain, app_id):
    return {
        xmlns: get_properties_by_xmlns(domain, app_id, xmlns)
        for xmlns in get_xmlns_by_app(domain, app_id)
    }


def get_xmlns_by_app(domain, app_id):
    app = get_current_app(domain, app_id)
    return [form.xmlns.split('/')[-1] for form in app.get_forms()]


def get_properties_by_xmlns(domain, app_id, xmlns):
    complete_xmlns = 'http://openrosa.org/formdesigner/' + xmlns
    form_export_schema = get_latest_form_export_schema(
        domain, app_id, complete_xmlns
    ) or FormExportDataSchema.generate_schema_from_builds(domain, app_id, complete_xmlns)

    if not form_export_schema.group_schemas:
        return set()
    else:
        export_items = [
            item for item in form_export_schema.group_schemas[0].items
            if isinstance(item, ExportItem)
        ]
        return set([get_odata_property_from_export_item(item) for item in export_items]) - {''}


def get_odata_property_from_export_item(export_item):
    return format_odata_property_for_power_bi(export_item.label)


def format_odata_property_for_power_bi(odata_property):
    return odata_property.replace('#', '').replace('@', '').replace('.', '_').strip()


def get_case_odata_fields_from_config(case_export_config):
    # todo: this should eventually be handled by the data dictionary but we don't do a good
    # job of mapping that in exports today so we don't have datatype information handy.
    SPECIAL_TYPES = {
        'closed': 'Edm.Boolean',
        'modified_on': 'Edm.DateTimeOffset',
        'date_modified': 'Edm.DateTimeOffset',
        'server_modified_on': 'Edm.DateTimeOffset',
        'opened_on': 'Edm.DateTimeOffset',
    }

    def _get_primary_path(export_column):
        if export_column and export_column.item and export_column.item.path:
            return export_column.item.path[0].name
        return None

    return [FieldMetadata(column.label, SPECIAL_TYPES.get(_get_primary_path(column), 'Edm.String'))
            for column in case_export_config.tables[0].selected_columns]


def get_form_odata_fields_from_config(form_export_config):
    table = form_export_config.tables[0]
    return [column.label for column in table.selected_columns]


def record_feed_access_in_datadog(request, config_id, duration, response):
    config = ExportInstance.get(config_id)
    username = request.couch_user.username
    json_response = json.loads(response.content.decode('utf-8'))
    rows = json_response['value']
    row_count = len(rows)
    try:
        column_count = len(rows[0])
    except IndexError:
        column_count = 0
    datadog_counter('commcare.odata_feed.test_v3', tags=[
        'domain:{}'.format(request.domain),
        'feed_id:{}'.format(config_id),
        'feed_type:{}'.format(config.type),
        'username:{}'.format(username),
        'row_count:{}'.format(row_count),
        'column_count:{}'.format(column_count),
        'size:{}'.format(len(response.content)),
        'duration:{}'.format(duration),
        'duration_bucket:{}'.format(bucket_value(duration, (1, 5, 20, 60, 120, 300, 600), 's')),
    ])
