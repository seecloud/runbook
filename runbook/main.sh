#!/bin/bash

# ensure indices for runbooks exist
runbook-init-storage

if [ ! -z "$RUN_RUNBOOK_API" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 runbook.main:app &
fi

wait -n
