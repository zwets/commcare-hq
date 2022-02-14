import json
import math
from contextlib import contextmanager
from copy import deepcopy

import uuid
from django.test import SimpleTestCase, override_settings
from nose.tools import nottest
from unittest.mock import patch

from corehq.util.es.elasticsearch import Elasticsearch, TransportError

from .utils import (
    TestDoc,
    TestDocumentAdapter,
    docs_from_result,
    docs_to_dict,
    es_test,
)
from ..client import (
    ElasticClientAdapter,
    ElasticManageAdapter,
    get_client,
    _elastic_hosts,
    _client_default,
    _client_for_export,
)
from ..exceptions import ESShardFailure, TaskError, TaskMissing


@override_settings(ELASTICSEARCH_HOSTS=["localhost"],
                   ELASTICSEARCH_PORT=9200)
@es_test
class TestClient(SimpleTestCase):

    def test_elastic_host(self):
        expected = [{"host": "localhost", "port": 9200}]
        self.assertEqual(expected, _elastic_hosts())

    @override_settings(ELASTICSEARCH_HOSTS=["localhost", "otherhost:9292"])
    def test_elastic_hosts(self):
        expected = [
            {"host": "localhost", "port": 9200},
            {"host": "otherhost", "port": 9292},
        ]
        self.assertEqual(expected, _elastic_hosts())

    @override_settings(ELASTICSEARCH_HOSTS=[],
                       ELASTICSEARCH_HOST="otherhost:9292")
    def test_elastic_hosts_fall_back_to_host(self):
        expected = [{"host": "otherhost", "port": 9292}]
        self.assertEqual(expected, _elastic_hosts())

    @override_settings(ELASTICSEARCH_PORT=9292)
    def test_elastic_hosts_alt_default_port(self):
        expected = [{"host": "localhost", "port": 9292}]
        self.assertEqual(expected, _elastic_hosts())

    @override_settings(ELASTICSEARCH_HOSTS=["otherhost:9292"])
    def test_elastic_hosts_alt_host_spec(self):
        expected = [{"host": "otherhost", "port": 9292}]
        self.assertEqual(expected, _elastic_hosts())

    def test_get_client(self):
        self.assertIsInstance(get_client(), Elasticsearch)

    def test_get_client_for_export(self):
        export_client = get_client(for_export=True)
        self.assertIsInstance(export_client, Elasticsearch)
        # depends on memoized client
        self.assertIsNot(export_client, get_client())


class BaseAdapterTest(SimpleTestCase):

    def setUp(self):
        super().setUp()
        self.adapter = self.adapter_class()


@es_test
class TestElasticClientAdapter(BaseAdapterTest):

    adapter_class = ElasticClientAdapter

    def test_info(self):
        self.assertEqual(sorted(self.adapter.info()),
                         ["cluster_name", "cluster_uuid", "name", "tagline", "version"])

    def test_ping(self):
        self.assertTrue(self.adapter.ping())

    @override_settings(ELASTICSEARCH_HOSTS=["localhost:65536"])  # bad port
    def test_ping_fail(self):

        def clear_cached_clients():
            for func in [_client_default, _client_for_export]:
                func.reset_cache()

        clear_cached_clients()  # discard cached client so we get a new one
        failed_adapter = ElasticClientAdapter()
        self.assertFalse(failed_adapter.ping())
        clear_cached_clients()  # discard again so later tests get a real client


class BaseAdapterTestWithIndex(BaseAdapterTest):

    index = None  # set by subclass

    def setUp(self):
        super().setUp()
        # clear in case it's still hanging around from other tests
        self._purge_test_index()

    def tearDown(self):
        self._purge_test_index()
        super().tearDown()

    @nottest
    def _purge_test_index(self):
        try:
            ElasticManageAdapter().index_delete(self.index)
        except TransportError:
            # TransportError(404, 'index_not_found_exception', 'no such index')
            pass


@es_test
class TestElasticManageAdapter(BaseAdapterTestWithIndex):

    adapter_class = ElasticManageAdapter
    index = "test_manage-adapter"

    def test_index_exists(self):
        self.assertFalse(self.adapter.index_exists(self.index))
        self.adapter.index_create(self.index)
        try:
            self.adapter.indices_refresh([self.index])
            self.assertTrue(self.adapter.index_exists(self.index))
        finally:
            self.adapter.index_delete(self.index)

    def test_cluster_health(self):
        self.assertIn("status", self.adapter.cluster_health())

    def test_cluster_health_of_index(self):
        self.adapter.index_create(self.index)
        self.assertIn("status", self.adapter.cluster_health(self.index))

    def test_cluster_routing_enable(self):
        self._clear_cluster_routing(verify=True)
        self.adapter.cluster_routing_enable(True)
        settings = self.adapter._es.cluster.get_settings(flat_settings=True)
        self.assertEqual(
            settings["transient"]["cluster.routing.allocation.enable"],
            "all",
        )
        self._clear_cluster_routing()

    def test_cluster_routing_disable(self):
        self._clear_cluster_routing(verify=True)
        self.adapter.cluster_routing_enable(False)
        settings = self.adapter._es.cluster.get_settings(flat_settings=True)
        self.assertEqual(
            settings["transient"]["cluster.routing.allocation.enable"],
            "none",
        )
        self._clear_cluster_routing()

    def _clear_cluster_routing(self, verify=False):
        try:
            self.adapter._cluster_put_settings({"cluster.routing.allocation.enable": None})
        except TransportError:
            # TransportError(400, 'action_request_validation_exception', 'Validation Failed: 1: no settings to update;')  # noqa: E501
            pass
        if verify:
            settings = self.adapter._es.cluster.get_settings()
            self.assertIsNone(settings["transient"].get("cluster.routing.allocation.enable"))

    def test_get_node_info(self):
        info = self.adapter._es.nodes.info()
        node_id = list(info["nodes"])[0]
        node_name = info["nodes"][node_id]["name"]
        self.assertEqual(self.adapter.get_node_info(node_id, "name"), node_name)

    def test_get_task(self):
        with self._mock_single_task_response() as (task_id, patched):
            task = self.adapter.get_task(task_id)
            patched.assert_called_once_with(task_id=task_id, detailed=True)
            self.assertIn("running_time_in_nanos", task)

    @contextmanager
    def _mock_single_task_response(self):
        """A context manager that fetches a real list of all tasks from
        Elasticsearch and returns the tuple ``(task_id, patched)`` where:
        - ``task_id`` is the ID of a task present in the mock's ``return_value``
        - ``patched`` is the mock object returned by patching
          ``self.adapter._es.tasks.list`` and setting its ``return_value`` to
          the real list of tasks, pruned down to contain details for only
          ``task_id`` (to simulate the response returned for a single task by
          its ID)

        This function depends on the fact that at any given time, an
        Elasticsearch cluster will _always_ return at least one task (which is
        observed to be true in at least Elasticsearch 2.4).
        """
        response = self.adapter._es.tasks.list()
        parsed = self.adapter._parse_task_result(response, _return_one=False)
        task_id = list(parsed)[0]  # get the first task_id
        # prune the response of all tasks but one
        for node_name, info in response["nodes"].items():
            for t_id in list(info["tasks"]):
                if t_id != task_id:
                    info["tasks"].pop(t_id)
        with patch.object(self.adapter._es.tasks, "list", return_value=response) as patched:
            yield task_id, patched

    def test_get_task_missing(self):
        node_name = list(self.adapter._es.nodes.info()["nodes"])[0]
        hopefully_missing_task_id = f"{node_name}:0"
        with self.assertRaises(TaskMissing):
            self.adapter.get_task(hopefully_missing_task_id)

    def test_get_task_error(self):
        with self.assertRaises(TaskError):
            self.adapter.get_task("_:0")  # (hopefully) bad task (node) ID

    def test__parse_task_result_empty_valid_failure_and_cause(self):
        cause = {"type": "resource_not_found_exception"}
        result = {"nodes": {}, "node_failures": [{
            "type": "failed_node_exception",
            "caused_by": cause,
        }]}
        with self.assertRaises(TaskMissing) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(test.exception.tasks_result, cause)

    def test__parse_task_result_empty_unknown_reason(self):
        result = {"nodes": {}}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(result, test.exception.tasks_result)

    def test__parse_task_result_empty_unknown_fail_type(self):
        result = {"nodes": {}, "node_failures": [{"type": "bogus"}]}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(result, test.exception.tasks_result)

    def test__parse_task_result_empty_unknown_caused_by_type(self):
        result = {"nodes": {}, "node_failures": [{
            "type": "failed_node_exception",
            "caused_by": {"type": "bogus"},
        }]}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(result, test.exception.tasks_result)

    def test__parse_task_result_empty_missing_caused_by(self):
        result = {"nodes": {}, "node_failures": [{
            "type": "failed_node_exception"
        }]}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(result, test.exception.tasks_result)

    def test__parse_task_result_empty_multi_failures(self):
        result = {"nodes": {}, "node_failures": ["one", "two"]}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(test.exception.tasks_result, result)

    def test__parse_task_result_single_task_valid(self):
        details = "we're interested in this bit"
        result = {"nodes": {"node_0": {"tasks": {"node_0:1": details}}}}
        self.assertEqual(details, self.adapter._parse_task_result(result))

    def test__parse_task_result_multi_tasks_expected(self):
        result = {"nodes": {
            "node_0": {"tasks": {"node_0:1": {}, "node_0:2": {}}},
            "node_1": {"tasks": {"node_1:1": {}, "node_1:2": {}}},
        }}
        expected = {
            "node_0:1": {},
            "node_0:2": {},
            "node_1:1": {},
            "node_1:2": {},
        }
        self.assertEqual(
            expected,
            self.adapter._parse_task_result(result, _return_one=False),
        )

    def test__parse_task_result_multi_tasks_not_expected(self):
        result = {"nodes": {
            "node_0": {"tasks": {"node_0:1": {}, "node_0:2": {}}},
            "node_1": {"tasks": {"node_1:1": {}, "node_1:2": {}}},
        }}
        with self.assertRaises(TaskError) as test:
            self.adapter._parse_task_result(result)
        self.assertEqual(test.exception.tasks_result, result)

    def test_index_create(self):
        self.assertFalse(self.adapter.index_exists(self.index))
        self.adapter.index_create(self.index)
        self.assertTrue(self.adapter.index_exists(self.index))

    def test_index_delete(self):
        self.adapter.index_create(self.index)
        self.assertTrue(self.adapter.index_exists(self.index))
        self.adapter.index_delete(self.index)
        self.assertFalse(self.adapter.index_exists(self.index))

    def test_indices_refresh(self):
        doc_adapter = TestDocumentAdapter()
        doc_adapter.index = self.index  # use our index so it gets cleaned up
        self.adapter.index_create(self.index)
        doc_adapter.upsert(TestDoc("1", "test"))

        def get_search_hits():
            return doc_adapter.search({})["hits"]["hits"]

        self.assertEqual([], get_search_hits())
        self.adapter.indices_refresh([doc_adapter.index])
        docs = [h["_source"] for h in get_search_hits()]
        self.assertEqual([{"_id": "1", "entropy": 3, "value": "test"}], docs)

    def test_index_flush(self):
        with patch.object(self.adapter._es.indices, "flush") as patched:
            self.adapter.index_flush(self.index)
            patched.assert_called_once_with(self.index, expand_wildcards="none")

    def test_index_close(self):
        doc_adapter = TestDocumentAdapter()
        doc_adapter.index = self.index  # use our index so it gets cleaned up
        self.adapter.index_create(self.index)
        doc_adapter.upsert(TestDoc("1", "test"))  # does not raise
        self.adapter.index_close(self.index)
        with self.assertRaises(TransportError) as test:
            doc_adapter.upsert(TestDoc("2", "test"))
        self.assertEqual(test.exception.status_code, 403)
        self.assertEqual(test.exception.error, "index_closed_exception")

    def test_index_put_alias(self):
        alias = "test_alias"
        aliases = self.adapter.get_aliases()
        self.assertNotIn(alias, aliases)
        self.adapter.index_create(self.index)
        self.adapter.index_put_alias(self.index, alias)
        self._assert_alias_on_single_index(alias, self.index)

    def test_index_put_alias_flips_existing(self):
        alias = "test_alias"
        flip_to_index = f"{self.index}_alt"
        self.adapter.index_create(self.index)
        self.adapter.index_create(flip_to_index)
        try:
            self.adapter.index_put_alias(self.index, alias)
            self._assert_alias_on_single_index(alias, self.index)
            self.adapter.index_put_alias(flip_to_index, alias)
            self._assert_alias_on_single_index(alias, flip_to_index)
        finally:
            self.adapter.index_delete(flip_to_index)

    def _assert_alias_on_single_index(self, alias, index):
        aliases = self.adapter.get_aliases()
        self.assertIn(alias, aliases)
        self.assertEqual(aliases[alias], {index})

    def test_index_set_replicas(self):
        self.adapter.index_create(self.index)

        def get_replicas(index):
            info = self.adapter._es.indices.get_settings(
                self.index,
                "index.number_of_replicas",
                flat_settings=True,
            )
            return int(info[index]["settings"]["index.number_of_replicas"])

        self.assertEqual(get_replicas(self.index), 1)  # initial value is 1
        self.adapter.index_set_replicas(self.index, 0)
        self.assertEqual(get_replicas(self.index), 0)

    def test_index_put_mapping(self):
        type_ = "test_doc"
        mapping = {
            "properties": {
                "value": {"type": "string"}
            }
        }
        self.adapter.index_create(self.index)

        def get_mapping(index, type_):
            info = self.adapter._es.indices.get_mapping(index, type_)
            if info:
                return info[index]["mappings"][type_]
            return info

        self.assertEqual(get_mapping(self.index, type_), {})
        self.adapter.index_put_mapping(self.index, type_, mapping)
        self.assertEqual(get_mapping(self.index, type_), mapping)

    def test__validate_single_index(self):
        self.adapter._validate_single_index(self.index)  # does not raise

    def test__validate_single_index_fails_empty(self):
        with self.assertRaises(ValueError):
            self.adapter._validate_single_index("")

    def test__validate_single_index_fails_None(self):
        with self.assertRaises(ValueError):
            self.adapter._validate_single_index(None)

    def test__validate_single_index_fails__all(self):
        with self.assertRaises(ValueError):
            self.adapter._validate_single_index("_all")

    def test__validate_single_index_fails_multi_syntax(self):
        with self.assertRaises(ValueError):
            self.adapter._validate_single_index("index1,index2")

    def test__validate_single_index_fails_wildcard(self):
        with self.assertRaises(ValueError):
            self.adapter._validate_single_index("case*")


@nottest
class TestDocumentAdapterWithExtras(TestDocumentAdapter):
    """A special document adapter (has extra methods) specifically for reducing
    boilerplate on adapter tests where periodic management actions are needed."""

    def index_exists(self):
        return ElasticManageAdapter().index_exists(self.index)

    def create_index(self, settings=None):
        ElasticManageAdapter().index_create(self.index, settings)

    def delete_index(self):
        ElasticManageAdapter().index_delete(self.index)

    def refresh_index(self):
        ElasticManageAdapter().indices_refresh([self.index])


@es_test
class TestElasticDocumentAdapter(BaseAdapterTestWithIndex):

    adapter_class = TestDocumentAdapterWithExtras
    index = TestDocumentAdapterWithExtras.index  # for _purge_test_index

    def setUp(self):
        super().setUp()
        # simply fail all the tests rather than spewing many huge tracebacks
        self.assertFalse(self.adapter.index_exists(),
                         f"index exists: {self.adapter.index}")
        self.adapter.create_index({"mappings": {self.adapter.type: self.adapter.mapping}})

    def test_transform(self):
        doc = TestDoc("1", "test")
        transformed = (doc.id, {"value": doc.value, "entropy": doc.entropy})
        self.assertEqual(transformed, self.adapter.transform(doc))

    def test_transform_full(self):
        doc = TestDoc("1", "test")
        transformed_full = {"_id": doc.id, "value": doc.value, "entropy": doc.entropy}
        self.assertEqual(transformed_full, self.adapter.transform_full(doc))

    def test_transform_full_id_null(self):
        doc = TestDoc(None, "test")
        transformed_full = {"value": doc.value, "entropy": doc.entropy}
        self.assertEqual(transformed_full, self.adapter.transform_full(doc))

    def test_exists(self):
        doc = self._index_new_doc()
        self.assertTrue(self.adapter.exists(doc["_id"]))

    def test_fetch(self):
        doc = self._index_new_doc()
        self.assertEqual(doc, self.adapter.fetch(doc["_id"]))

    def test_fetch_limit_fields(self):
        doc = self._index_new_doc()
        doc.pop("entropy")
        self.assertEqual(doc, self.adapter.fetch(doc["_id"], ["value"]))

    def test_count(self):
        docs = self._index_many_new_docs(2)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))
        query = {"query": {"term": {"value": docs[0]["value"]}}}
        self.assertEqual(1, self.adapter.count(query))

    def test__prepare_count_query(self):
        query = {k: "remove" for k in ["size", "sort", "from", "to", "_source"]}
        query["key"] = "keep"
        self.assertEqual({"key": "keep"}, self.adapter._prepare_count_query(query))

    def test_fetch_many(self):
        query_docs = self._index_many_new_docs(2)
        query_ids = [doc["_id"] for doc in query_docs]
        no_fetch = self._index_new_doc()
        fetched = docs_to_dict(self.adapter.fetch_many(query_ids))
        self.assertNotIn(no_fetch["_id"], fetched)
        self.assertEqual(docs_to_dict(query_docs), fetched)

    # TODO: activate this test -- legacy Elastic code does not check for shard
    # failures on '.fetch_many()' calls.
    #def test_fetch_many_raises_on_shards_failure(self):
    #    doc = self._index_new_doc()
    #    doc_ids = [doc["_id"]]
    #    self.assertEqual([doc], self.adapter.fetch_many(doc_ids))
    #    exc_args, wrapper = self._make_shards_fail({"failed": 1, "test": "val"},
    #                                               self.adapter._mget)
    #    with patch.object(self.adapter, "_mget", wrapper):
    #        with self.assertRaises(ESShardFailure) as test:
    #            self.adapter.fetch_many(doc_ids)
    #        self.assertEqual(test.exception.args, exc_args)

    def test_iter_fetch(self):
        query_docs = self._index_many_new_docs(4)
        no_fetch = query_docs.pop()
        query_ids = [doc["_id"] for doc in query_docs]
        fetched = self.adapter.iter_fetch(query_ids, chunk_size=1)
        self.assertEqual(docs_to_dict(query_docs), docs_to_dict(fetched))
        self.assertNotIn(no_fetch["_id"], fetched)

    def test_iter_fetch_chunks_requests(self):
        indexed = self._index_many_new_docs(7)
        query_ids = [doc["_id"] for doc in indexed]
        chunk_size = 2
        chunk_calls = math.ceil(len(indexed) / chunk_size)
        with patch.object(self.adapter, "fetch_many", side_effect=self.adapter.fetch_many) as patched:
            list(self.adapter.iter_fetch(query_ids, chunk_size=chunk_size))
            self.assertEqual(patched.call_count, chunk_calls)

    def test_iter_fetch_yields_same_as_fetch_many(self):
        query_docs = self._index_many_new_docs(3)
        no_fetch = query_docs.pop()
        query_ids = [doc["_id"] for doc in query_docs]
        fetched = docs_to_dict(self.adapter.fetch_many(query_ids))
        chunked = docs_to_dict(self.adapter.iter_fetch(query_ids))
        self.assertNotIn(no_fetch["_id"], fetched)
        self.assertEqual(docs_to_dict(query_docs), fetched)
        self.assertEqual(fetched, chunked)

    def test__mget(self):
        one, two = self._index_many_new_docs(2)
        one_id = one.pop("_id")
        result = self.adapter._mget({"ids": [one_id]})
        result_docs_dict = {d["_id"]: d["_source"] for d in result["docs"]}
        self.assertEqual({one_id: one}, result_docs_dict)
        self.assertNotIn(two["_id"], result_docs_dict)

    def test_search(self):
        docs = self._index_many_new_docs(2)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))

    def test_search_limited_results(self):
        docs = self._index_many_new_docs(2)
        no_fetch = docs.pop()
        query = {"query": {"term": {"value": docs[0]["value"]}}}
        expected = docs_to_dict(docs)
        self.assertEqual(expected, self._search_hits_dict(query))
        self.assertNotIn(no_fetch["_id"], expected)

    def test_search_raises_on_shards_failure(self):
        doc = self._index_new_doc()
        self.assertEqual(docs_to_dict([doc]), self._search_hits_dict({}))  # does not raise
        exc_args, wrapper = self._make_shards_fail({"failed": 1, "test": "val"},
                                                   self.adapter._search)
        with patch.object(self.adapter, "_search", wrapper):
            with self.assertRaises(ESShardFailure) as test:
                self.adapter.search({})
            self.assertEqual(test.exception.args, exc_args)

    def test__search(self):
        docs = self._index_many_new_docs(2)
        result = self.adapter._search({})
        self.assertEqual(set(result), {"took", "timed_out", "_shards", "hits"})
        self.assertEqual(set(result["hits"]), {"total", "max_score", "hits"})
        self.assertIsInstance(result["hits"]["total"], int)
        by_id = docs_to_dict(docs)
        for hit in result["hits"]["hits"]:
            hit.pop("_score")
            doc_id = hit["_id"]
            self.assertEqual(hit, {
                "_index": self.adapter.index,
                "_type": self.adapter.type,
                "_id": doc_id,
                "_source": by_id[doc_id],
            })

    def test_scroll(self):
        docs = self._index_many_new_docs(2)
        self.assertEqual(docs_to_dict(docs),
                         self._scroll_hits_dict({}, size=1))

    def test_scroll_yields_same_as_search(self):
        docs = self._index_many_new_docs(3)
        no_fetch = docs.pop()
        query = {"query": {"bool": {"must_not": {"term": {"value": no_fetch["value"]}}}}}
        searched = self._search_hits_dict(query)
        scrolled = self._scroll_hits_dict(query, size=1)
        self.assertNotIn(no_fetch["_id"], searched)
        self.assertEqual(docs_to_dict(docs), searched)
        self.assertEqual(searched, scrolled)

    def test_scroll_raises_on_shards_failure(self):
        docs = self._index_many_new_docs(3)
        self.assertEqual(docs_to_dict(docs), self._scroll_hits_dict({}, size=1))  # should not raise
        exc_args, wrapper = self._make_shards_fail({"failed": 1, "test": "val"},
                                                   self.adapter._es.scroll)
        with patch.object(self.adapter._es, "scroll", side_effect=wrapper) as patched:
            with self.assertRaises(ESShardFailure) as test:
                list(self.adapter.scroll({}, size=1))
            self.assertEqual(test.exception.args, exc_args)
            patched.assert_called_once()

    def test_scroll_cancels_after_exhaustion(self):
        docs = self._index_many_new_docs(3)
        with patch.object(self.adapter._es, "clear_scroll") as patched:
            self.assertEqual(docs_to_dict(docs),
                             self._scroll_hits_dict({}, size=1))
            patched.assert_called_once()

    def test_scroll_cancels_after_failure(self):
        class Bang(Exception):
            pass

        def crash(*args, **kw):
            raise Bang()

        self._index_many_new_docs(2)
        with patch.object(self.adapter._es, "scroll", side_effect=crash) as patched_scl, \
             patch.object(self.adapter._es, "clear_scroll") as patched_clr:
            with self.assertRaises(Bang):
                list(self.adapter.scroll({}, size=1))
            patched_scl.assert_called_once()
            patched_clr.assert_called_once()

    def test__scroll(self):
        docs = self._index_many_new_docs(5)
        top_level = {"_scroll_id", "took", "timed_out", "_shards", "hits"}
        is_first = True
        for result in self.adapter._scroll({}, size=2):
            self.assertEqual(set(result), top_level)
            if is_first:
                top_level.add("terminated_early")
                is_first = False
            self.assertEqual(set(result["hits"]), {"total", "max_score", "hits"})
            self.assertIsInstance(result["hits"]["total"], int)
            by_id = docs_to_dict(docs)
            for hit in result["hits"]["hits"]:
                hit.pop("_score")
                hit.pop("sort")
                doc_id = hit["_id"]
                self.assertEqual(hit, {
                    "_index": self.adapter.index,
                    "_type": self.adapter.type,
                    "_id": doc_id,
                    "_source": by_id[doc_id],
                })

    def test_scroll_no_searchtype_scan(self):
        """Tests that search_type='scan' is not added to the search parameters"""
        self._validate_scroll_search_params({}, {"sort": "_doc"})

    def test_scroll_query_extended(self):
        """Tests that sort=_doc is added to an non-empty query"""
        self._validate_scroll_search_params({"_id": "abc"},
                                            {"_id": "abc", "sort": "_doc"})

    def test_scroll_query_sort_safe(self):
        """Tests that a provided ``sort`` query will not be overwritten"""
        self._validate_scroll_search_params({"sort": "_id"}, {"sort": "_id"})

    def _validate_scroll_search_params(self, scroll_query, search_query):
        """Call adapter.scroll() and test that the resulting API search
        parameters match what we expect.

        Notably:
        - Search call does not include ``search_type='scan'``.
        - Calling ``scroll(query=scroll_query)`` results in an API call
          where ``body == search_query``.
        """
        scroll_kw = {
            "scroll": "1m",
            "size": 10,
        }
        with patch.object(self.adapter._es, "search", return_value={}) as search:
            list(self.adapter.scroll(scroll_query, **scroll_kw))
            search.assert_called_once_with(self.adapter.index,
                                           self.adapter.type, search_query,
                                           **scroll_kw)

    def test_scroll_ambiguous_size_raises(self):
        query = {"size": 1}
        with self.assertRaises(ValueError):
            list(self.adapter.scroll(query, size=1))

    def test_scroll_query_size_as_keyword(self):
        docs = self._index_many_new_docs(3)
        self._test_scroll_backend_calls({}, len(docs), size=1)

    def test_scroll_query_size_in_query(self):
        docs = self._index_many_new_docs(3)
        self._test_scroll_backend_calls({"size": 1}, len(docs))

    @patch("corehq.apps.es.client.SCROLL_SIZE", 1)
    def test_scroll_size_default(self):
        docs = self._index_many_new_docs(3)
        self._test_scroll_backend_calls({}, len(docs))

    def _test_scroll_backend_calls(self, query, call_count, **scroll_kw):
        _search = self.adapter._es.search
        _scroll = self.adapter._es.scroll
        with patch.object(self.adapter._es, "search", side_effect=_search) as search, \
             patch.object(self.adapter._es, "scroll", side_effect=_scroll) as scroll:
            list(self.adapter.scroll(query, **scroll_kw))
            # NOTE: scroll.call_count == call_count because the final
            # `client.scroll()`` call returns zero hits (ending the generator).
            # Call sequence (for 3 matched docs with size=1):
            # - len(client.search(...)["hits"]["hits"]) == 1
            # - len(client.scroll(...)["hits"]["hits"]) == 1
            # - len(client.scroll(...)["hits"]["hits"]) == 1
            # - len(client.scroll(...)["hits"]["hits"]) == 0
            search.assert_called_once()
            self.assertEqual(scroll.call_count, call_count)

    def test_scroll_returns_over_2x_size_docs(self):
        """Test that all results are returned for scroll queries."""
        scroll_size = 3  # fetch N docs per "scroll"
        total_docs = (scroll_size * 2) + 1
        docs = self._index_many_new_docs(total_docs)
        self.assertEqual(len(docs), total_docs)
        self.assertEqual(docs_to_dict(docs),
                         self._scroll_hits_dict({}, size=scroll_size))

    def test_upsert(self):
        doc = self._make_doc()
        self.assertEqual({}, self._search_hits_dict({}))
        self.adapter.upsert(doc, refresh=True)
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))

    def test_upsert_fails_with_invalid_id(self):
        doc = self._make_doc()
        doc.id = None
        with self.assertRaises(ValueError):
            self.adapter.upsert(doc, refresh=True)
        self.assertEqual({}, self._search_hits_dict({}))

    def test_upsert_succeeds_if_exists(self):
        doc = self._make_doc()
        self.adapter.upsert(doc, refresh=True)
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))
        self.adapter.upsert(doc, refresh=True)  # does not raise

    def test_upsert_with_change_succeeds_if_exists(self):
        doc = self._make_doc()
        doc_id = doc.id
        self.adapter.upsert(doc, refresh=True)
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))
        doc.value = self._make_doc().value  # modify the doc
        self.assertEqual(doc.id, doc_id)  # confirm it has the same ID
        self.adapter.upsert(doc, refresh=True)  # does not raise
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))

    def test_update(self):
        doc = self._make_doc()
        self.adapter.upsert(doc, refresh=True)
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))
        doc.value = self._make_doc().value  # modify the doc
        self.adapter.update(doc, refresh=True)
        self.assertEqual([self.adapter.transform_full(doc)],
                         docs_from_result(self.adapter.search({})))

    def test_update_fails_if_missing(self):
        self.assertEqual([], docs_from_result(self.adapter.search({})))
        doc = self._make_doc()
        with self.assertRaises(TransportError) as test:
            self.adapter.update(doc)
        self.assertEqual(test.exception.status_code, 404)
        self.assertEqual(test.exception.error, "document_missing_exception")

    def test_delete(self):
        doc = self._index_new_doc()
        self.assertEqual([doc], docs_from_result(self.adapter.search({})))
        self.adapter.delete(doc["_id"], refresh=True)
        self.assertEqual([], docs_from_result(self.adapter.search({})))

    def test_delete_fails_if_missing(self):
        missing_id = self._make_doc().id
        self.assertEqual([], docs_from_result(self.adapter.search({})))
        with self.assertRaises(TransportError) as test:
            self.adapter.delete(missing_id)
        self.assertEqual(test.exception.status_code, 404)
        error_info = test.exception.info
        error_info.pop("_version")
        error_info.pop("_shards")
        self.assertEqual(error_info, {
            "found": False,
            "_index": self.adapter.index,
            "_type": self.adapter.type,
            "_id": missing_id,
        })

    def test_bulk_index(self):
        docs = []
        serialized = []
        for x in range(3):
            doc = self._make_doc()
            docs.append(doc)
            serialized.append(self.adapter.transform_full(doc))
        self.assertEqual({}, self._search_hits_dict({}))
        self.adapter.bulk_index(docs, refresh=True)
        self.assertEqual(docs_to_dict(serialized), self._search_hits_dict({}))

    def test_bulk_index_fails_with_invalid_id(self):
        docs = [self._make_doc() for x in range(2)]
        docs[0].id = None
        with self.assertRaises(ValueError):
            self.adapter.bulk_index(docs, refresh=True)
        self.assertEqual({}, self._search_hits_dict({}))

    def test_bulk_delete(self):
        docs = self._index_many_new_docs(3)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))
        self.adapter.bulk_delete([d["_id"] for d in docs], refresh=True)
        self.assertEqual({}, self._search_hits_dict({}))

    def test_bulk(self):
        docs = self._index_many_new_docs(2)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))
        action_template = {
            "_op_type": "delete",
            "_index": self.adapter.index,
            "_type": self.adapter.type,
        }
        actions = [{"_id": doc["_id"], **action_template} for doc in docs]
        self.adapter.bulk(actions, refresh=True)
        self.assertEqual({}, self._search_hits_dict({}))

    def test_bulk_with_id_in_source(self):
        action_template = {
            "_op_type": "index",
            "_index": self.adapter.index,
            "_type": self.adapter.type,
        }
        docs = []
        actions = []
        for x in range(3):
            doc = self.adapter.transform_full(self._make_doc())
            docs.append(doc)
            actions.append({"_id": doc["_id"], "_source": doc, **action_template})
        self.assertEqual({}, self._search_hits_dict({}))
        self.adapter.bulk(actions, refresh=True)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))

    def test__bulk(self):
        docs = self._index_many_new_docs(2)
        self.assertEqual(docs_to_dict(docs), self._search_hits_dict({}))
        action_template = {
            "_op_type": "delete",
            "_index": self.adapter.index,
            "_type": self.adapter.type,
        }
        actions = [{"_id": doc["_id"], **action_template} for doc in docs]
        self.adapter._bulk(actions, refresh=True)
        self.assertEqual({}, self._search_hits_dict({}))

    def test__iter_id_stripped_actions(self):
        actions = [{"_source": {"_id": 1, "test": True}}]
        self.assertEqual([{"_source": {"test": True}}],
                         list(self.adapter._iter_id_stripped_actions(actions)))

    def test__verify_doc_id(self):
        self.adapter._verify_doc_id("abc")  # should not raise

    def test__verify_doc_id_fails_empty_string(self):
        with self.assertRaises(ValueError):
            self.adapter._verify_doc_id("")

    def test__verify_doc_id_fails_non_strings(self):
        for invalid in [None, True, False, 123, 1.23]:
            with self.assertRaises(ValueError):
                self.adapter._verify_doc_id(invalid)

    def test__iter_id_stripped_actions_does_not_mutate_actions(self):
        actions = [{"_source": {"_id": 1}}]
        expected = deepcopy(actions)
        list(self.adapter._iter_id_stripped_actions(actions))
        self.assertEqual(expected, actions)

    def test__fix_hit(self):
        doc_id = "abc"
        hit = {"_id": doc_id, "_source": {"test": True}}
        expected = deepcopy(hit)
        expected["_source"]["_id"] = doc_id
        self.adapter._fix_hit(hit)
        self.assertEqual(expected, hit)

    def test__fix_hits_in_results(self):
        ids = ["abc", "def"]
        result = {"hits": {"hits": [
            {"_id": ids[0], "_source": {"test": True}},
            {"_id": ids[1], "_source": {"test": True}},
        ]}}
        expected = deepcopy(result)
        expected["hits"]["hits"][0]["_source"]["_id"] = ids[0]
        expected["hits"]["hits"][1]["_source"]["_id"] = ids[1]
        self.adapter._fix_hits_in_results(result)
        self.assertEqual(expected, result)

    def test__report_and_fail_on_shard_failures(self):
        result = self.adapter._search({})
        self.adapter._report_and_fail_on_shard_failures(result)  # does not raise
        shard_result = {"failed": 5, "test": True}
        shard_exc_args = (f"_shards: {json.dumps(shard_result)}",)
        result["_shards"] = shard_result
        with self.assertRaises(ESShardFailure) as test:
            self.adapter._report_and_fail_on_shard_failures(result)
        self.assertEqual(test.exception.args, shard_exc_args)

    def _index_many_new_docs(self, count, refresh=True):
        docs = []
        for x in range(count):
            docs.append(self._index_new_doc(refresh=False))
        if refresh:
            self.adapter.refresh_index()
        return docs

    def _index_new_doc(self, refresh=True):
        doc = self._make_doc()
        self.adapter.upsert(doc, refresh=refresh)
        return self.adapter.transform_full(doc)

    def _make_doc(self, value=None):
        if value is None:
            if not hasattr(self, "_doc_value_history"):
                self._doc_value_history = 0
            value = f"test doc {self._doc_value_history:04}"
            self._doc_value_history += 1
        return TestDoc(uuid.uuid4().hex, value)

    def _search_hits_dict(self, query):
        """Convenience method for getting a ``dict`` of search results.

        :param query: ``dict`` search query (default: ``{}``)
        :returns: ``{<doc_id>: <doc_sans_id>, ...}`` dict
        """
        return docs_to_dict(docs_from_result(self.adapter.search(query)))

    def _scroll_hits_dict(self, query, **kw):
        def do_scroll():
            for doc in self.adapter.scroll(query, **kw):
                yield doc["_source"]
        return docs_to_dict(do_scroll())

    @staticmethod
    def _make_shards_fail(shards_obj, result_getter):
        def wrapper(*args, **kw):
            result = result_getter(*args, **kw)
            result["_shards"] = shards_obj
            return result
        exc_args = (f"_shards: {json.dumps(shards_obj)}",)
        return exc_args, wrapper
