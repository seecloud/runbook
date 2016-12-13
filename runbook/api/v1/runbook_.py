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
    },
    "required": ["name", "description", "runbook", "type"],
    "additionalProperties": False
}


def _convert(hit):
    body = {k: v for k, v in hit["_source"].items()}
    body["_id"] = hit["_id"]
    return body


@bp.route("/<region>/runbooks",
          methods=["GET", "POST"])
@utils.check_regions
def handle_runbooks(region):
    es = storage.get_elasticsearch()
    if flask.request.method == "POST":
        runbook = flask.request.get_json(silent=True)
        try:
            jsonschema.validate(runbook, RUNBOOK_SCHEMA)
        except jsonschema.ValidationError as e:
            # NOTE(kzaitsev): jsonschema exception has really good unicode
            # error representation
            return flask.jsonify(
                {"error": u"{}".format(e)}), 400

        resp = es.index(
            index="ms_runbooks_{}".format(region),
            doc_type="runbook",
            body=runbook,
        )
        if resp['_shards']['successful']:
            # at least 1 means we're good
            return flask.jsonify({"_id": resp["_id"]}), 201
        # should not really be here
        return flask.jsonify({"error": "Was unable to save document"}), 500
    else:
        result = es.search(index="ms_runbooks_region_one", doc_type="runbook")
        hit_list = [_convert(hit) for hit in result['hits']['hits']]
        return flask.jsonify(hit_list)


@bp.route("/<region>/runbooks/<book_id>",
          methods=["GET", "PUT", "DELETE"])
@utils.check_regions
def handle_single_runbook(region, book_id):
    es = storage.get_elasticsearch()

    if flask.request.method == "GET":
        try:
            result = es.get(
                index="ms_runbooks_region_one",
                doc_type="runbook",
                id=book_id
            )
            return flask.jsonify(_convert(result))
        except elasticsearch.NotFoundError:
            flask.abort(404)

    elif flask.request.method == "DELETE":
        try:
            es.delete(
                index="ms_runbooks_region_one",
                doc_type="runbook",
                id=book_id
            )
            return flask.jsonify({}), 204
        except elasticsearch.NotFoundError:
            flask.abort(404)

    elif flask.request.method == "PUT":
        runbook = flask.request.get_json(silent=True)
        try:
            jsonschema.validate(runbook, RUNBOOK_SCHEMA)
        except jsonschema.ValidationError as e:
            # NOTE(kzaitsev): jsonschema exception has really good unicode
            # error representation
            return flask.jsonify(
                {"error": u"{}".format(e)}), 400

        try:
            resp = es.update(
                index="ms_runbooks_{}".format(region),
                doc_type="runbook",
                id=book_id,
                body={"doc": runbook},
            )
        except elasticsearch.NotFoundError:
            flask.abort(404)

        if resp['_shards']['successful'] or resp['result'] == 'noop':
            # noop means nothing to update, also ok
            return flask.jsonify({"_id": resp["_id"]})
        return flask.jsonify({"error": "Was unable to update document"}), 500
    return flask.jsonify({"error": "Unreachable"}), 500


@bp.route("/<region>/runbooks/<book_id>/run",
          methods=["POST"])
@utils.check_regions
def run_runbook(region, book_id):
    return flask.jsonify("fixme!")


@bp.route("/<region>/runbooks/<book_id>/runs")
@utils.check_regions
def runbook_runs(region, book_id):
    return flask.jsonify("fixme!")


@bp.route("/<region>/runbooks/<book_id>/runs/<run_id>")
@utils.check_regions
def single_runbook_run(region, book_id, run_id):
    return flask.jsonify("fixme!")
