#!/bin/bash

if [ "$(basename "$(pwd)")" != "meshtastic_benthos" ]; then
    echo "Run this script from the same dir"
    exit 1
fi

docker run \
    --mount "type=bind,src=$(pwd),target=/conf" \
    --rm ghcr.io/benthosdev/benthos -c /conf/benthos.yaml test /conf/...
