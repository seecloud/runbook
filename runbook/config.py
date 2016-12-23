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
import sys

import jsonschema


CONF = {
    "reader": None,
    "writer": None
}

DEFAULT_CONF = {
    "reader": {
        "flask": {
            "HOST": "0.0.0.0",
            "PORT": 5000,
            "DEBUG": False
        },
        "backend": {
            "type": "elastic",
            "connection": [{"host": "127.0.0.1", "port": 9200}]
        },
        "regions": [],
    },
    "writer": {
        "flask": {
            "HOST": "0.0.0.0",
            "PORT": 5001,
            "DEBUG": False
        },
        "backend": {
            "type": "elastic",
            "connection": [{"host": "127.0.0.1", "port": 9200}]
        },
        "regions": [],
    }
}


CONF_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "flask": {
            "type": "object",
            "properties": {
                "PORT": {"type": "integer"},
                "HOST": {"type": "string"},
                "DEBUG": {"type": "boolean"}
            },
        },
        "backend": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "connection": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer"}
                        },
                        "required": ["host"]
                    },
                    "minItems": 1
                },
            },
            "required": ["type", "connection"]
        },
        "regions": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string"}
            }
        }
    },
    "additionalProperties": False
}


def get_config(api_type=None):
    """Return cached configuration.

    :returns: application config
    :rtype: dict
    """
    if api_type not in ["reader", "writer"]:
        raise RuntimeError("Unknown api type '{}'".format(api_type))

    global CONF
    if not CONF[api_type]:
        path = os.environ.get(
            "RUNBOOK_{}_CONF".format(api_type.upper()),
            "/etc/runbook/{}-config.json".format(api_type))
        try:
            CONF[api_type] = json.load(open(path))
            logging.info("Config is '%s'" % path)
        except IOError as e:
            logging.warning("Config at '%s': %s" % (path, e))
            CONF[api_type] = DEFAULT_CONF[api_type]
    try:
        jsonschema.validate(CONF[api_type], CONF_SCHEMA)
    except jsonschema.ValidationError as e:
        logging.error(e.message)
        sys.exit(1)
    except jsonschema.SchemaError as e:
        logging.error(e)
        sys.exit(1)
    else:
        return CONF[api_type]
