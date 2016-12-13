# Copyright 2016: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import json

import elasticsearch
import mock

from tests.unit.api.v1 import base


class RunbookTestCase(base.APITestCase):
    correct_runbook = {
        "name": "test",
        "description": "test",
        "type": "bash",
        "runbook": "echo",
    }

    incorrect_runbook = {
        "name": "test",
        "description": "test",
        "type": "bash",
    }

    def test_get_no_region(self):
        resp = self.client.get("/api/v1/region/region_zero/runbooks")
        self.assertEqual(404, resp.status_code)

        resp = self.client.post("/api/v1/region/region_zero/runbooks")
        self.assertEqual(404, resp.status_code)

    def test_post_new_runbook_bad_input(self):
        resp = self.client.post("/api/v1/region/region_one/runbooks")
        self.assertEqual(400, resp.status_code)

        resp = self.client.post("/api/v1/region/region_one/runbooks",
                                data=json.dumps(self.incorrect_runbook),
                                content_type="application/json")
        self.assertEqual(400, resp.status_code)

        resp = self.client.post("/api/v1/region/region_one/runbooks",
                                data=json.dumps(self.correct_runbook),
                                )
        self.assertEqual(400, resp.status_code)

    @mock.patch.object(elasticsearch.Elasticsearch, "index")
    def test_post_new_runbook(self, es_index):
        es_index.return_value = {
            "_shards": {"successful": 1},
            "_id": "123",
        }
        resp = self.client.post("/api/v1/region/region_one/runbooks",
                                data=json.dumps(self.correct_runbook),
                                content_type="application/json")
        self.assertEqual(201, resp.status_code)
        resp_json = json.loads(resp.data.decode())
        self.assertEqual(resp_json["_id"], "123")

        es_index.assert_called_with(index="ms_runbooks_region_one",
                                    doc_type="runbook",
                                    body=self.correct_runbook)

    @mock.patch.object(elasticsearch.Elasticsearch, "search")
    def test_get_runbooks(self, es_search):
        es_search.return_value = {
            "hits": {"hits": [
                {
                    "_id": "121",
                    "_source": self.correct_runbook,
                },
                {
                    "_id": "122",
                    "_source": self.correct_runbook,
                },
                {
                    "_id": "123",
                    "_source": self.correct_runbook,
                },
            ]},
        }
        resp = self.client.get("/api/v1/region/region_one/runbooks",
                               content_type="application/json")
        self.assertEqual(200, resp.status_code)
        resp_json = json.loads(resp.data.decode())
        expected = []
        for book_id in ["121", "122", "123"]:
            data = copy.copy(self.correct_runbook)
            data["_id"] = book_id
            expected.append(data)
        self.assertEqual(expected, resp_json)

        es_search.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook")

    @mock.patch.object(elasticsearch.Elasticsearch, "get")
    def test_get_single_runbook_bad_id(self, es_get):
        es_get.side_effect = elasticsearch.NotFoundError
        resp = self.client.get("/api/v1/region/region_one/runbooks/123",
                               content_type="application/json")
        self.assertEqual(404, resp.status_code)

        es_get.assert_called_with(index="ms_runbooks_region_one",
                                  doc_type="runbook",
                                  id="123")

    @mock.patch.object(elasticsearch.Elasticsearch, "get")
    def test_get_single_runbook(self, es_get):
        es_get.return_value = {
            "_source": self.correct_runbook,
            "_id": "123",
        }
        resp = self.client.get("/api/v1/region/region_one/runbooks/123",
                               content_type="application/json")
        self.assertEqual(200, resp.status_code)

        resp_json = json.loads(resp.data.decode())
        expected = copy.copy(self.correct_runbook)
        expected["_id"] = "123"
        self.assertEqual(expected, resp_json)

        es_get.assert_called_with(index="ms_runbooks_region_one",
                                  doc_type="runbook",
                                  id="123")

    @mock.patch.object(elasticsearch.Elasticsearch, "get")
    def test_get_single_runbook_reg_two(self, es_get):
        es_get.return_value = {
            "_source": self.correct_runbook,
            "_id": "123",
        }
        resp = self.client.get("/api/v1/region/region_two/runbooks/123",
                               content_type="application/json")
        self.assertEqual(200, resp.status_code)

        resp_json = json.loads(resp.data.decode())
        expected = copy.copy(self.correct_runbook)
        expected["_id"] = "123"
        self.assertEqual(expected, resp_json)

        es_get.assert_called_with(index="ms_runbooks_region_two",
                                  doc_type="runbook",
                                  id="123")

    @mock.patch.object(elasticsearch.Elasticsearch, "delete")
    def test_del_single_runbook(self, es_delete):
        es_delete.side_effect = None
        resp = self.client.delete("/api/v1/region/region_one/runbooks/123",
                                  content_type="application/json")
        self.assertEqual(204, resp.status_code)
        es_delete.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123")

    @mock.patch.object(elasticsearch.Elasticsearch, "delete")
    def test_del_single_runbook_bad_id(self, es_delete):
        es_delete.side_effect = elasticsearch.NotFoundError
        resp = self.client.delete("/api/v1/region/region_one/runbooks/123",
                                  content_type="application/json")
        self.assertEqual(404, resp.status_code)
        es_delete.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123")

    @mock.patch.object(elasticsearch.Elasticsearch, "update")
    def test_put_single_runbook_bad_id(self, es_update):
        es_update.side_effect = elasticsearch.NotFoundError
        resp = self.client.put("/api/v1/region/region_one/runbooks/123",
                               data=json.dumps(self.correct_runbook),
                               content_type="application/json")
        self.assertEqual(404, resp.status_code)
        expected_body = {"doc": self.correct_runbook}
        es_update.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123",
                                     body=expected_body)

    @mock.patch.object(elasticsearch.Elasticsearch, "update")
    def test_put_single_runbook(self, es_update):
        es_update.return_value = {
            "_shards": {"successful": 1},
            "_id": "123",
        }
        resp = self.client.put("/api/v1/region/region_one/runbooks/123",
                               data=json.dumps(self.correct_runbook),
                               content_type="application/json")
        self.assertEqual(200, resp.status_code)
        resp_json = json.loads(resp.data.decode())
        self.assertEqual({"_id": "123"}, resp_json)

        expected_body = {"doc": self.correct_runbook}
        es_update.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123",
                                     body=expected_body)
