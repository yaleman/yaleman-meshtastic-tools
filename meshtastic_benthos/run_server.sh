#!/bin/bash

echo "Running a dev server on http://localhost:4195"

docker run -p 4195:4195 --rm ghcr.io/benthosdev/benthos blobl server --no-open --host 0.0.0.0
