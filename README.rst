Cloud Runbooks
==============


.. image:: https://coveralls.io/repos/github/seecloud/runbook/badge.svg?branch=master
    :target: https://coveralls.io/github/seecloud/runbook?branch=master

.. image:: https://travis-ci.org/seecloud/runbook.svg?branch=master
    :target: https://travis-ci.org/seecloud/runbook


Stores and allows running Cloud automation Runbooks

How To Use & Run
----------------

Build Docker Image
~~~~~~~~~~~~~~~~~~

.. code-block:: sh

    docker build -t runbook:latest .


Run Docker Container
~~~~~~~~~~~~~~~~~~~~


.. code-block:: sh

    # Update ~/health/etc/config.json file to match your configuration
    vi ~/runbook/etc/writer-config.json
    vi ~/runbook/etc/reader-config.json
    # Run container
    docker run -d --name runbook-app -v ~/etc/runbook:/etc/runbook -p 6000:5000 -p 6001:5001 --env=RUN_RUNBOOK_WRITER_API=1 --env=RUN_RUNBOOK_READER_API=1 runbook


Get App Logs
~~~~~~~~~~~~

.. code-block:: sh

    docker logs runbook-app

