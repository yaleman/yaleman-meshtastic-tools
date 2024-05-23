import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import click
from loguru import logger
import yaml


def recursive_update(source: Dict[str, Any], dest: Dict[str, Any]) -> Dict[str, Any]:
    """neatly update things, don't just blat them"""
    for key, value in source.items():
        if isinstance(value, dict) or isinstance(dest.get(key), dict):
            logger.debug("recursing into {}", key)
            dest[key] = recursive_update(value, dest.get(key, {}))
        else:
            logger.debug("setting {} -> {}", key, value)
            dest[key] = value
    return dest


@click.command()
@click.argument("id")
@click.option(
    "--config-dir", "-c", default="configs", help="Directory containing the configs"
)
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.option("--no-write", "-n", is_flag=True, help="Don't write the output to a file")
def main(
    id: str,
    config_dir: str = "configs",
    debug: Optional[bool] = False,
    no_write: Optional[bool] = False,
) -> int:
    """layer the configs and output a yml file"""

    if debug is not None and debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    layer_list_file = Path(os.path.join(config_dir, f"layers-{id}.yml"))

    if not layer_list_file.exists():
        logger.error("Can't find {}", layer_list_file)
        return 1

    layers = yaml.safe_load(layer_list_file.read_text()).get("layers", [])

    if not layers:
        logger.error("No layers found in {}", layer_list_file)
        return 1

    config: Dict[str, Any] = {}

    for layer in layers:
        layer_file = Path(os.path.join(config_dir, f"{layer}"))
        if not layer_file.exists():
            logger.error("Can't find  layer file {}", layer_file)
            return 1
        logger.info("Loading {}", layer_file)
        layer_file_content = yaml.safe_load(layer_file.read_text())
        config = recursive_update(layer_file_content, config)

    print(yaml.dump(config))
    if no_write is not None and no_write:
        return 0
    yaml_file = Path(os.path.join(config_dir, f"layered-{id}.yml"))
    logger.info("Writing to {}", yaml_file)
    yaml_file.write_text(yaml.dump(config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
