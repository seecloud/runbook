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


import flask
from flask_helpers import routing

from runbook.api.v1 import runbook as runbook_api
from runbook import config


app = flask.Flask(__name__, static_folder=None)
app.config.update(config.get_config()["flask"])


@app.route("/api/")
def versions():
    return flask.jsonify({"versions": ["1.0"]})


@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({"error": "Not Found"}), 404


for bp in [runbook_api]:
    for url_prefix, blueprint in bp.get_blueprints():
        app.register_blueprint(blueprint, url_prefix="/api/v1%s" % url_prefix)


app = routing.add_routing_map(app, html_uri=None, json_uri="/")


def main():
    app.run()


if __name__ == "__main__":
    main()
