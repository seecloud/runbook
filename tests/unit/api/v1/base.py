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

import mock
import testtools


TEST_CONFIG = {
    "flask": {
        "PORT": 5000,
        "HOST": "0.0.0.0",
        "DEBUG": True
    },
    "backend": {
        "type": "elastic",
        "connection": [{"host": "127.0.0.1", "port": 9200}]
    },
    "regions": [
        "region_one",
        "region_two"
    ],
}


class APITestCase(testtools.TestCase):

    def setUp(self):
        super(APITestCase, self).setUp()
        self.addCleanup(mock.patch.stopall)

        # NOTE(kzaitsev): mock all get_config for a ll the tests
        self.patcher = mock.patch('runbook.config.get_config')
        self.get_config = self.patcher.start()
        self.get_config.return_value = TEST_CONFIG

        # NOTE(kzaitsev): importing this module calls get_config, so I'm
        # importing it after I've mocked get_config itself
        import runbook.main
        self.client = runbook.main.app.test_client()
        self.app = runbook.main.app

    def test_not_found(self):
        resp = self.client.get('/404')
        self.assertEqual({"error": "Not Found"},
                         json.loads(resp.data.decode()))
        self.assertEqual(404, resp.status_code)
