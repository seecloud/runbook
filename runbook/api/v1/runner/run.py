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

import datetime

import elasticsearch
import flask
import jsonschema

from runbook.api import utils
from runbook import storage

API_TYPE = "runner"
bp = flask.Blueprint("runbooks", __name__)


def get_blueprints():
    return [["/region", bp]]

RUN_SETTINGS_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "parameters": {
            "type": "object",
        },
        "user": {"type": "string"},
    },
    "required": ["user"],
    "additionalProperties": False
}


@bp.route("/<region>/runbooks/<book_id>/run", methods=["POST"])
@utils.check_regions(API_TYPE)
def handle_single_runbook(region, book_id):
    es = storage.get_elasticsearch(API_TYPE)
    index_name = "ms_runbooks_{}".format(region)

    try:
        resp = es.get(index=index_name, doc_type="runbook", id=book_id)
    except elasticsearch.NotFoundError:
        flask.abort(404)

    if resp["_source"].get("deleted"):
        return flask.jsonify(
            {"error": "Can't run deleted runbook"}), 400

    run_settings = flask.request.get_json(silent=True)

    try:
        jsonschema.validate(run_settings, RUN_SETTINGS_SCHEMA)
    except jsonschema.ValidationError as e:
        return flask.jsonify(
            {"error": u"{}".format(e)}), 400

    run_parameters = {}
    if resp["_source"].get("parameters"):
        run_parameters = run_settings.get("parameters", {})
        for param in resp["_source"]["parameters"]:
            run_parameters.setdefault(param["name"], param.get("default"))

    run = {
        "created_at": datetime.datetime.now(),
        "updated_at": None,
        "user": run_settings["user"],
        "status": "scheduled",
        "output": None,
        "return_code": None,
        "parameters": run_parameters,
    }

    resp = es.index(
        index=index_name,
        doc_type="run",
        body=run,
        parent=book_id,
    )

    return flask.jsonify({"id": resp["_id"]}), 202
