#!/bin/bash

set -e

if [ "$(basename "$(pwd)")" != "meshtastic_benthos" ]; then
    echo "Run this script from the same dir"
    exit 1
fi
docker run --rm -it --mount "type=bind,src=$(pwd),target=/data/" \
    -e "CONF_DIR=/data/" \
    ghcr.io/redpanda-data/connect:4.30.1 \
    -c /data/benthos.yaml test /data/*.yaml
