# meshtastic-tools

## layer-configs.py

Allows you to build a base config and then layer it.

Dump your existing configuration from the device with `meshtastic --export-config`.

### Example

Run for a given node ID with `layer-configs.py <id>`, eg: `layer-configs.py 1234`:

configs/layers-1234.yml

```yaml: configs/layers-1234.yml
---
layers:
    - config-base.yml
    - layer-1234.yml
```

config-base.yml

```yaml config-base.yml
---
config:
  bluetooth:
    enabled: false
    fixedPin: 123456
    mode: RANDOM_PIN
```

config-1234.yml

```yaml config-1234.yml
---
config:
  bluetooth:
    enabled: true
```

results in the file `configs\layered-1234.yml`:

```yaml layered-1234.yml
---
config:
  bluetooth:
    enabled: true
    fixedPin: 123456
    mode: RANDOM_PIN
```
