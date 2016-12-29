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
import logging
import os
import subprocess
import tempfile

from runbook.drivers import base


class Driver(base.Driver):

    @classmethod
    def initialise(cls):
        pass

    @classmethod
    def run(cls, runbook, parameters):
        logging.info("Running runbook '{}' with parameters '{}'".format(
            runbook, parameters))
        f = tempfile.NamedTemporaryFile()
        f.write(runbook["runbook"])
        f.flush()

        returncode = 0
        interpreter = cls.interpreters.get(runbook.get("type"))
        if not interpreter:
            return {
                "return_code": -1,
                "output": "Don't know how to run '{}' type runbook".format(
                    runbook.get("type")),
            }

        env = copy.deepcopy(os.environ)
        env.update(parameters)
        try:
            output = subprocess.check_output(
                [interpreter, f.name],
                stderr=subprocess.STDOUT,
                env=env)
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode

        return {
            "return_code": returncode,
            "output": output,
        }
