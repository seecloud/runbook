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

import json

import elasticsearch
import mock

from tests.unit.api.v1 import base


class WriterRunbookTestCase(base.APITestCase):
    api_type = "writer"

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
        self.assertEqual(resp_json["id"], "123")

        es_index.assert_called_with(index="ms_runbooks_region_one",
                                    doc_type="runbook",
                                    body=self.correct_runbook)

    @mock.patch.object(elasticsearch.Elasticsearch, "update")
    def test_del_single_runbook(self, es_update):
        es_update.return_value = {
            "_shards": {"successful": 1},
            "_id": "123",
        }
        resp = self.client.delete("/api/v1/region/region_one/runbooks/123",
                                  content_type="application/json")
        self.assertEqual(204, resp.status_code)
        es_update.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123",
                                     body={'doc': {'deleted': True}})

    @mock.patch.object(elasticsearch.Elasticsearch, "update")
    def test_del_single_runbook_bad_id(self, es_update):
        es_update.side_effect = elasticsearch.NotFoundError
        resp = self.client.delete("/api/v1/region/region_one/runbooks/123",
                                  content_type="application/json")
        self.assertEqual(404, resp.status_code)
        es_update.assert_called_with(index="ms_runbooks_region_one",
                                     doc_type="runbook",
                                     id="123",
                                     body={'doc': {'deleted': True}})

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
