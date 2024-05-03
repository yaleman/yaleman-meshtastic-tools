from enum import IntEnum
import json
from typing import Optional

from meshtastic.serial_interface import SerialInterface
from meshtastic.util import camel_to_snake
from loguru import logger
from pydantic import BaseModel, field_validator


class MqttConfig(BaseModel):
    address: str
    username: str
    password: str
    encryptionEnabled: bool = False
    root: str
    enabled: bool = False
    jsonEnabled: bool = False
    tlsEnabled: bool = False
    proxyToClientEnabled: bool = False
    mapReportingEnabled: bool = False


class PairingModes(IntEnum):
    RANDOM_PIN = 0
    FIXED_PIN = 1
    NO_PIN = 2


class BluetoothConfig(BaseModel):
    enabled: bool = False
    fixedPin: int = 12355
    mode: PairingModes = PairingModes.RANDOM_PIN

    @field_validator("mode", mode="before")
    def from_str_mode(cls, value: str | int) -> PairingModes:
        try:
            return PairingModes(value)
        except Exception:
            return PairingModes[value.upper()]


class Config(BaseModel):
    mqtt: Optional[MqttConfig] = None
    bluetooth: Optional[BluetoothConfig] = None


def main():

    config = Config.model_validate_json(
        open("config.json", "r", encoding="utf-8").read()
    )
    client = SerialInterface(None)

    # logger.debug(config.model_dump_json(indent=4))

    try:
        client.getShortName()
    except Exception:
        logger.error("Failed to get shortname, probably not connected!")
        return

    logger.info("Device name: {}", client.getLongName())
    logger.info("Device info:\n{}", client.myInfo)

    # my_node_num = client.myInfo.my_node_num
    # node = client.getNode(my_node_num)
    node = client.localNode
    # logger.info("printing metadata...\n{}", node.getMetadata())

    logger.debug("Waiting for config...")
    node.waitForConfig()

    need_to_write_mqtt = False
    for key, value in config.mqtt.model_dump().items():
        key = camel_to_snake(key)
        if not hasattr(node.moduleConfig.mqtt, key):
            logger.debug(f"mqtt has no attribute {key}")
            continue
        oldvalue = getattr(node.moduleConfig.mqtt, key)
        if oldvalue != value:
            setattr(node.moduleConfig.mqtt, key, value)
            logger.info(f"updating mqtt {key} from {oldvalue} to {value}")
            need_to_write_mqtt = True
    if need_to_write_mqtt:
        logger.info("writing mqtt config")
        logger.debug(json.dumps(node.moduleConfig.mqtt, default=str, indent=4))
        node.writeConfig("mqtt")

        logger.debug("Waiting for reboot...")
        node.waitForConfig()

    need_to_write_bluetooth = False
    for key, value in config.bluetooth.model_dump().items():
        key = camel_to_snake(key)
        if not hasattr(node.localConfig.bluetooth, key):
            logger.debug(f"bluetooth has no attribute {key}")
            continue
        oldvalue = getattr(node.localConfig.bluetooth, key)
        if oldvalue != value:
            setattr(node.localConfig.bluetooth, key, value)
            logger.info(f"updating bluetooth {key} from {oldvalue} to {value}")
            need_to_write_bluetooth = True
    if need_to_write_bluetooth:
        logger.info("writing bluetooth config")
        # node.writeConfig("bluetooth")
        logger.debug("Waiting for reboot...")
        node.waitForConfig()


if __name__ == "__main__":
    main()
