# Meshtastic-Benthos

This is some config to use [Benthos](https://www.benthos.dev/) to take what's going into MQTT from meshtastic nodes and make it usable, eg ingestion into Splunk :D

## Configuration

The config requires two env vars:

- MQTT_SERVER - just the hostname
- CONF_DIR - because when I run it in a container, I mount the files in `/conf/` but... local testing needs different paths.
