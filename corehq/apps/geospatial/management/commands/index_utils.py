from dimagi.utils.chunked import chunked

from corehq.apps.es import case_search_adapter
from corehq.apps.geospatial.es import case_query_for_missing_geopoint_val
from corehq.form_processor.models import CommCareCase
from corehq.util.log import with_progress_bar
from corehq.apps.geospatial.const import DEFAULT_CHUNK_SIZE, DEFAULT_QUERY_LIMIT


def process_batch(
    domain,
    geo_case_property,
    total_count,
    with_progress=False,
    offset=0,
):
    should_sort = bool(total_count > DEFAULT_QUERY_LIMIT)
    query = case_query_for_missing_geopoint_val(
        domain, geo_case_property, case_type, size=DEFAULT_QUERY_LIMIT, offset=offset, should_sort=should_sort
    )
    case_ids = query.get_ids()
    _index_case_ids(domain, case_ids, with_progress)


def _index_case_ids(domain, case_ids, with_progress):
    if with_progress:
        ids = with_progress_bar(case_ids)
    else:
        ids = case_ids
    for case_id_chunk in chunked(ids, DEFAULT_CHUNK_SIZE):
        case_chunk = CommCareCase.objects.get_cases(list(case_id_chunk), domain)
        case_search_adapter.bulk_index(case_chunk)
