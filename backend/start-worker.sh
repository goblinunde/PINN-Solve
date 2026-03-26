#!/bin/bash

set -e

cd "$(dirname "$0")"
source .venv/bin/activate
python -m celery -A tasks.celery_app worker --pool solo --loglevel INFO
