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

import elasticsearch
import flask
import jsonschema

from runbook.api import utils
from runbook import storage

API_TYPE = "writer"
bp = flask.Blueprint("runbooks", __name__)


def get_blueprints():
    return [["/region", bp]]


RUNBOOK_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "type": {"type": "string"},
        "runbook": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 0,
        },
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "default": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["name"],
            },
            "minItems": 0,
        },
    },
    "required": ["name", "description", "runbook", "type"],
    "additionalProperties": False
}


def _convert(hit):
    body = {k: v for k, v in hit["_source"].items()}
    body["_id"] = hit["_id"]
    return body


@bp.route("/<region>/runbooks", methods=["POST"])
@utils.check_regions(API_TYPE)
def handle_runbooks(region):
    es = storage.get_elasticsearch(API_TYPE)
    index_name = "ms_runbooks_{}".format(region)

    runbook = flask.request.get_json(silent=True)
    try:
        jsonschema.validate(runbook, RUNBOOK_SCHEMA)
    except jsonschema.ValidationError as e:
        # NOTE(kzaitsev): jsonschema exception has really good unicode
        # error representation
        return flask.jsonify(
            {"error": u"{}".format(e)}), 400

    resp = es.index(
        index=index_name,
        doc_type="runbook",
        body=runbook,
    )
    if resp['_shards']['successful']:
        # at least 1 means we're good
        return flask.jsonify({"id": resp["_id"]}), 201
    # should not really be here
    return flask.jsonify({"error": "Was unable to save the document"}), 500


@bp.route("/<region>/runbooks/<book_id>", methods=["PUT", "DELETE"])
@utils.check_regions(API_TYPE)
def handle_single_runbook(region, book_id):
    es = storage.get_elasticsearch(API_TYPE)
    index_name = "ms_runbooks_{}".format(region)

    if flask.request.method == "DELETE":
        runbook = {"deleted": True}
        success_code = 204
    else:  # PUT
        runbook = flask.request.get_json(silent=True)
        try:
            jsonschema.validate(runbook, RUNBOOK_SCHEMA)
        except jsonschema.ValidationError as e:
            return flask.jsonify(
                {"error": u"{}".format(e)}), 400
        success_code = 200

    try:
        resp = es.update(
            index=index_name,
            doc_type="runbook",
            id=book_id,
            body={"doc": runbook},
        )
    except elasticsearch.NotFoundError:
        flask.abort(404)

    if resp['_shards']['successful'] or resp['result'] == 'noop':
        # noop means nothing to update, also ok
        return flask.jsonify({"_id": resp["_id"]}), success_code
    return flask.jsonify({"error": "Was unable to update the document"}), 500
