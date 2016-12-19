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
import os

import elasticsearch

from runbook import config


LOG = logging.getLogger("storage")

ES_MAPPINGS = {
    "mappings": {
        "runbook": {
            "_all": {"enabled": False},
            "properties": {
                "runbook": {"type": "binary"},
                "description": {"type": "text"},
                "name": {"type": "keyword"},
                "type": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "parameters": {
                    "properties": {
                        "name": {"type": "keyword"},
                        "default": {"type": "keyword"},
                        "type": {"type": "keyword"},
                    }
                },
                "deleted": {"type": "boolean"},
            }
        },
        "run": {
            "_all": {"enabled": False},
            "_parent": {"type": "runbook"},
            "properties": {
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "user": {"type": "string"},
                "output": {"type": "binary"},
                "return_code": {"type": "integer"},
                "status": {"type": "keyword"},
            }
        }
    }
}

ES_CLIENT = None


def get_elasticsearch(api_type):
    """Configures or returns already configured ES client."""
    global ES_CLIENT
    if not ES_CLIENT:
        nodes = config.get_config(api_type)["backend"]["connection"]
        ES_CLIENT = elasticsearch.Elasticsearch(nodes)
    return ES_CLIENT


def ensure_index(index, api_type):
    """Esures index exists in es."""
    es = get_elasticsearch(api_type)

    try:
        if not es.indices.exists(index):
            mapping = json.dumps(ES_MAPPINGS)
            LOG.info("Creating Elasticsearch index: {}".format(index))
            es.indices.create(index, body=mapping)
        else:
            LOG.info("Elasticsearch index: '{}' already exists".format(index))
    except elasticsearch.exceptions.ElasticsearchException:
        LOG.exception("Was unable to get or create index: {}".format(index))
        raise


def configure_regions(api_type="writer"):
    """Ensure there are indices for every region we have configured."""

    for region in config.get_config(api_type)["regions"]:
        ensure_index("ms_{}_{}".format("runbooks", region), api_type)


if __name__ == "__main__":
    api_type = os.environ.get("RUNBOOK_INIT_INDICES_FOR", "writer")
    configure_regions(api_type)
