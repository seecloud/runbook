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

import logging
import os
import shutil
import tempfile
import uuid

import docker

from runbook.drivers import base

LOG = logging.getLogger("runner.docker")


RUNNER_DOCKERFILE = """
FROM ubuntu:14.04
RUN apt-get update
RUN apt-get install python -y
"""

RUN_DOCKERFILE = """
FROM runbook_runner
COPY . /runbook
WORKDIR /runbook
ENTRYPOINT ["{interpreter}"]
CMD ["runbook"]
"""


class Driver(base.Driver):

    @classmethod
    def initialise(cls):
        dcli = docker.from_env()
        dirname = tempfile.mkdtemp()
        with open(os.path.join(dirname, 'Dockerfile'), "w") as f:
            f.write(RUNNER_DOCKERFILE)
        dcli.images.build(path=dirname, tag="runbook_runner")
        LOG.info("Built 'runbook_runner' image")

        shutil.rmtree(dirname)

    @classmethod
    def run(cls, runbook, parameters):
        dcli = docker.from_env()
        LOG.info("Running runbook '{}' with parameters '{}'".format(
            runbook, parameters))

        interpreter = cls.interpreters.get(runbook.get("type"))
        if not interpreter:
            return {
                "return_code": -1,
                "output": "Don't know how to run '{}' type runbook".format(
                    runbook.get("type")),
            }

        dirname = tempfile.mkdtemp()

        with open(os.path.join(dirname, 'runbook'), "w") as f:
            f.write(runbook["runbook"])

        with open(os.path.join(dirname, 'Dockerfile'), "w") as f:
            f.write(RUN_DOCKERFILE.format(
                interpreter=interpreter))

        run_name = "run-{}".format(uuid.uuid4().hex)

        dcli.images.build(path=dirname, tag=run_name)
        LOG.info("Built 'runbook_runner' image")

        returncode = 0
        try:
            container = dcli.containers.run(
                run_name,
                name=run_name,
                stderr=True,
                detach=True,
            )
        except Exception:
            LOG.exception("Could not start container for {}".format(run_name))
        returncode = container.wait()
        output = container.logs()

        # cleanup
        try:
            container.remove()
            LOG.info("Removed container {}".format(run_name))
        except Exception:
            LOG.exception("Could not remove container {}".format(run_name))

        try:
            dcli.images.remove(run_name)
            LOG.info("Removed image {}".format(run_name))
        except Exception:
            LOG.exception("Could not remove image {}".format(run_name))
        shutil.rmtree(dirname, ignore_errors=True)

        return {
            "return_code": returncode,
            "output": output,
        }
