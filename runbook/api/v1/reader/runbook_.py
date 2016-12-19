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
bp = flask.Blueprint("runbooks", __name__)


def get_blueprints():
    return [["", bp]]


INNER_QUERY_NO_RUNS = {
    "bool": {
        "must_not": [
            {
                "has_child": {
                    "type": "run",
                    "query": {
                        "match_all": {}
                    }
                }
            }
        ]
    }
}

INNER_QUERY_WITH_RUNS = {
    "has_child": {
        "inner_hits": {
            "name": "latest",
            "size": 1,
            "sort": [{"created_at": {"order": "desc"}}]
        },
        "type": "run",
        "query": {
            "match_all": {}
        }
    }
}

RUNBOOK_QUERY = {
    "query": {
        "bool": {
            "should": [
                INNER_QUERY_NO_RUNS,
                INNER_QUERY_WITH_RUNS
            ],
        }
    }
}


@bp.route("/runbooks", methods=["GET"])
@bp.route("/region/<region>/runbooks", methods=["GET"])
@utils.check_regions(API_TYPE)
def handle_runbooks(region=None):
    es = storage.get_elasticsearch(API_TYPE)

    if region is None:
        region = "*"
    index_name = "ms_runbooks_{}".format(region)

    tags = flask.request.args.get('tags', '').split(',')

    query = copy.deepcopy(RUNBOOK_QUERY)

    # exclude deleted runbooks
    query["query"]["bool"]["must_not"] = {"term": {"deleted": True}}

    # filter by tags, combining multiple 'term' queries effectively AND's
    # supplied tags
    tag_terms = []
    for tag in tags:
        if tag:
            tag_terms.append({"term": {"tags": tag}})
    if tag_terms:
        query["query"]["bool"]["must"] = tag_terms

    result = es.search(index=index_name,
                       doc_type="runbook",
                       body=query)
    hit_list = [utils.convert_runbook(hit) for hit in result['hits']['hits']]
    return flask.jsonify(hit_list)


@bp.route("/region/<region>/runbooks/<book_id>", methods=["GET"])
@utils.check_regions(API_TYPE)
def handle_single_runbook(region, book_id):
    es = storage.get_elasticsearch(API_TYPE)
    index_name = "ms_runbooks_{}".format(region)

    query = copy.deepcopy(RUNBOOK_QUERY)
    query["query"]["bool"]["must"] = {"ids": {"values": [book_id]}}
    result = es.search(index=index_name,
                       doc_type="runbook",
                       body=query)

    hit_list = [utils.convert_runbook(hit) for hit in result['hits']['hits']]
    if not hit_list:
        flask.abort(404)

    return flask.jsonify(hit_list[0])
