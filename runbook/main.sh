#!/bin/bash

RUNBOOK_INIT_INDICES_FOR="${RUNBOOK_INIT_INDICES_FOR:-"writer"}"

if [ ! -z "$RUN_RUNBOOK_WRITER_API" ]; then
    runbook-init-storage
    gunicorn -w 4 -b 0.0.0.0:5001 runbook.main_writer:app &
fi

if [ ! -z "$RUN_RUNBOOK_READER_API" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 runbook.main_reader:app &
fi

wait -n
