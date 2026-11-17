#!/bin/bash
# Render everything waiting in scripts/queue/. Used by the scheduler.
cd "$(dirname "$0")/pipeline" || exit 1
exec /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 run_batch.py "$@"
