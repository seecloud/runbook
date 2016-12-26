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


import functools

import flask
import six

from runbook import config


def check_regions(api_type):
    def check_decorator(func):
        regions = set(config.get_config(api_type)["regions"])

        @functools.wraps(func)
        def checker(region=None, *args, **kwargs):

            if region is not None and region not in regions:
                return flask.jsonify(
                    {"error": "Region {} Not Found".format(region)}), 404
            return func(region, *args, **kwargs)

        return checker
    return check_decorator


def convert_run(hit):
    body = {k: v for k, v in hit["_source"].items()}

    if "_index" in hit:
        body["region_id"] = hit["_index"][len("ms_runbooks_"):]

    runbook = None
    if 'inner_hits' in hit:
        inner_hit = hit['inner_hits']['parent']['hits']['hits']
        if inner_hit:
            runbook = convert_runbook(inner_hit[0])

    body["runbook"] = runbook

    body["id"] = hit["_id"]
    return body


def convert_runbook(hit):
    body = {k: v for k, v in hit["_source"].items()}
    body.setdefault("tags", [])

    # convert any single tag to list of tags
    if isinstance(body["tags"], six.string_types):
        body["tags"] = [body["tags"]]

    if "_index" in hit:
        body["region_id"] = hit["_index"][len("ms_runbooks_"):]

    latest_run = None
    if 'inner_hits' in hit:
        inner_hit = hit['inner_hits']['latest']['hits']['hits']
        if inner_hit:
            latest_run = convert_run(inner_hit[0])

    body["latest_run"] = latest_run

    body["id"] = hit["_id"]
    return body
