#!/bin/bash

echo "Running a dev server on http://localhost:4195"

docker run -p 4195:4195 --rm \
    ghcr.io/redpanda-data/connect:4.30.1 \
    blobl server --no-open --host 0.0.0.0
