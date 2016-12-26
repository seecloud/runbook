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

import flask

from runbook.api import utils
from runbook import storage

API_TYPE = "reader"
bp = flask.Blueprint("runs", __name__)


def get_blueprints():
    return [["", bp]]


INNER_QUERY_WITH_PARENT = {
    "has_parent": {
        "inner_hits": {
            "name": "parent",
            "size": 1,
        },
        "type": "runbook",
        "query": {
            "match_all": {}
        }
    }
}

RUNS_QUERY = {
    "query": {
        "bool": {
            "should": INNER_QUERY_WITH_PARENT,
        }
    }
}


@bp.route("/region/<region>/runbook_runs", methods=["GET"])
@bp.route("/runbook_runs", methods=["GET"])
@utils.check_regions(API_TYPE)
def handle_runs(region=None):
    es = storage.get_elasticsearch(API_TYPE)

    if region is None:
        region = "*"
    index_name = "ms_runbooks_{}".format(region)

    query = copy.deepcopy(RUNS_QUERY)

    runbook_id = flask.request.args.get('runbook_id', '')
    if runbook_id:
        query["query"]["bool"]["should"]["has_parent"]["query"] = {
            "ids": {
                "values": runbook_id,
                "type": "runbook",
            }
        }

    result = es.search(index=index_name,
                       doc_type="run",
                       body=query)
    hit_list = [utils.convert_run(hit) for hit in result['hits']['hits']]
    return flask.jsonify(hit_list)


@bp.route("/region/<region>/runbook_runs/<run_id>", methods=["GET"])
@utils.check_regions(API_TYPE)
def handle_single_run(region, run_id):
    es = storage.get_elasticsearch(API_TYPE)
    index_name = "ms_runbooks_{}".format(region)

    query = copy.deepcopy(RUNS_QUERY)
    query["query"]["bool"]["must"] = {"ids": {"values": [run_id]}}
    result = es.search(index=index_name,
                       doc_type="run",
                       body=query)

    hit_list = [utils.convert_run(hit) for hit in result['hits']['hits']]
    if not hit_list:
        flask.abort(404)

    return flask.jsonify(hit_list[0])
