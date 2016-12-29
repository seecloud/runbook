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
import datetime
import importlib
import logging
import sys
import time

import elasticsearch.exceptions
import eventlet
import schedule

from runbook import config
from runbook import storage

eventlet.monkey_patch()

API_TYPE = "runner"
CONF = config.get_config(API_TYPE)
POOL = eventlet.GreenPool()

LOG = logging.getLogger("runner")
LOG.setLevel(logging.INFO)

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
    "version": True,
    "query": {
        "bool": {
            "filter": [
                INNER_QUERY_WITH_PARENT,
                {"term": {"status": "scheduled"}},
            ]
        }
    }
}


def handle_hit(hit, index_name, driver):
    es = storage.get_elasticsearch(API_TYPE)
    try:
        es.update(
            index=index_name,
            doc_type="run",
            id=hit["_id"],
            routing=hit["_routing"],
            version=hit["_version"],
            body={"doc": {"status": "started"}}
        )
        LOG.info("Handling run '{}'".format(hit['_id']))
    except elasticsearch.exceptions.ConflictError:
        LOG.warning("Ignoring run '{}' with id '{}'"
                    "It's already being handled by other thread".format(
                        hit["_source"], hit["_id"]))
        return False

    parameters = hit.get("parameters", {})
    try:
        runbook = hit['inner_hits']['parent']['hits']['hits'][0]["_source"]
    except (IndexError, KeyError):
        LOG.exception("Couldn't find runbook to run for {}".format(hit))
        return False

    run_result = {}
    try:
        run_result = driver.run(runbook, parameters)
    except Exception:
        LOG.exception("Got exception, when running '{}', marking "
                      "run as 'failed'".format(hit["_source"]))

    LOG.info("Finished run '{}': '{}'".format(hit['_id'], run_result))

    end_status = "finished" if run_result.get("return_code") == 0 else "failed"
    # end_status = "scheduled"  # FIXME

    now = datetime.datetime.now()
    try:
        es.update(
            index=index_name,
            doc_type="run",
            id=hit["_id"],
            routing=hit["_routing"],
            body={"doc": {
                "status": end_status,
                "output": run_result.get("output"),
                "return_code": run_result.get("return_code"),
                "updated_at": now,
            }}
        )
        LOG.info("Updated run '{}' status".format(hit['_id']))
    except elasticsearch.exceptions.TransportError:
        LOG.exception("Got exception, when finilazing run "
                      "'{}'".format(hit["_source"]))
        return False
    return True


def job():
    driver_name = CONF.get("driver", "shell")
    try:
        driver_module = importlib.import_module(
            "runbook.drivers." + driver_name)
    except ImportError:
        LOG.critical("No driver named '{}'".format(driver_name))
        return

    driver = driver_module.Driver

    es = storage.get_elasticsearch(API_TYPE)
    for region in CONF["regions"]:
        index_name = "ms_runbooks_{}".format(region)

        query = copy.deepcopy(RUNS_QUERY)

        result = es.search(index=index_name,
                           doc_type="run",
                           body=query)
        for hit in result['hits']['hits']:
            POOL.spawn_n(handle_hit, hit, index_name, driver)


def main():

    run_every_seconds = CONF.get("run_every_seconds", 30)
    schedule.every(run_every_seconds).seconds.do(job)

    job()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        LOG.error("Got KeyboardInterrupt, exiting.")
