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
import logging

import elasticsearch

from runbook import config


LOG = logging.getLogger("storage")
LOG.setLevel(config.get_config().get("logging", {}).get("level", "INFO"))

ES_MAPPINGS = {
    "mappings": {
        "runbook": {
            "_all": {"enabled": False},
            "properties": {
                "runbook": {"type": "binary"},
                "description": {"type": "text"},
                "name": {"type": "keyword"},
                "type": {"type": "keyword"},
            }
        },
        "run": {
            "_all": {"enabled": False},
            "properties": {
                "date": {"type": "date"},
                "user": {"type": "string"},
                "output": {"type": "binary"},
                "return_code": {"type": "integer"},
            }
        }
    }
}

ES_CLIENT = None


def get_elasticsearch():
    """Configures or returns already configured ES client."""
    global ES_CLIENT
    if not ES_CLIENT:
        nodes = config.get_config()["backend"]["connection"]
        ES_CLIENT = elasticsearch.Elasticsearch(nodes)
    return ES_CLIENT


def ensure_index(index):
    """Esures index exists in es."""
    es = get_elasticsearch()

    try:
        if not es.indices.exists(index):
            mapping = json.dumps(ES_MAPPINGS)
            LOG.info("Creating Elasticsearch index: {}".format(index))
            es.indices.create(index, body=mapping)
    except elasticsearch.exceptions.ElasticsearchException:
        LOG.exception("Was unable to get or create index: {}".format(index))
        raise


def configure_regions():
    """Ensure there are indices for every region we have configured."""

    for region in config.get_config()["regions"]:
        ensure_index("ms_{}_{}".format("runbooks", region))


if __name__ == "__main__":
    configure_regions()
