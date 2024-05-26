#!/bin/bash

set -e

if [ "$(basename "$(pwd)")" != "meshtastic_benthos" ]; then
    echo "Run this script from the same dir"
    exit 1
fi

benthos -c "$(pwd)/benthos.yaml" test "$(pwd)/..."