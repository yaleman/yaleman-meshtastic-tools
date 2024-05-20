from enum import IntEnum
import json
import time
from typing import Optional

from meshtastic.serial_interface import SerialInterface  # type: ignore
from meshtastic.util import camel_to_snake  # type: ignore
from meshtastic.node import Node  # type: ignore
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
            return PairingModes(value)  # type: ignore
        except Exception:
            if hasattr(PairingModes, str(value)):
                return PairingModes[str(value)]
            else:
                raise ValueError(f"Invalid PairingModes: {value}")


class LoraConfig(BaseModel):
    region: str


class NetworkConfig(BaseModel):
    wifi_ssid: str
    wifi_psk: str
    wifi_enabled: bool


class OwnerConfig(BaseModel):
    short_name: str
    long_name: str

    @field_validator("short_name")
    def _validate_short_name(cls, value: str) -> str:
        if len(value) > 4:
            raise ValueError("Short name must be 4 characters or less")
        return value


class Config(BaseModel):
    owner: Optional[OwnerConfig] = None
    mqtt: Optional[MqttConfig] = None
    bluetooth: Optional[BluetoothConfig] = None
    lora: LoraConfig
    network: Optional[NetworkConfig] = None


def do_network_config(node: Node, config: Config) -> None:
    if config.network is not None:
        need_to_write_network = False
        for key, value in config.network.model_dump().items():
            key = camel_to_snake(key)
            node.localConfig.network.wifi_enabled
            if not hasattr(node.localConfig.network, key):
                logger.debug(f"network has no attribute {key}")
                continue
            oldvalue = getattr(node.localConfig.network, key)
            if oldvalue != value:
                setattr(node.localConfig.network, key, value)
                logger.info(f"updating network/{key} from {oldvalue} to {value}")
                need_to_write_network = True
        if need_to_write_network:
            logger.info("writing newtork config")
            node.writeConfig("network")
            logger.debug("Waiting for reboot...")
            time.sleep(2)
            node.waitForConfig()


def do_lora_config(node: Node, config: Config) -> None:

    if not hasattr(node.localConfig.lora, config.lora.region):
        logger.error("Invalid region from config: {}", config.lora.region)
        return
    logger.info("Current LORA region: {}", node.localConfig.lora.region)
    wanted_region = getattr(node.localConfig.lora, config.lora.region)
    # logger.info("region: {}", wanted_region)
    if node.localConfig.lora.region != wanted_region:
        logger.info("updating lora region to {}", wanted_region)
        node.localConfig.lora.region = wanted_region
        node.writeConfig("lora")
        logger.debug("Waiting for reboot...")
        time.sleep(2)
        node.waitForConfig()


def do_bluetooth_config(node: Node, config: Config) -> None:
    need_to_write_bluetooth = False
    if config.bluetooth is None:
        logger.debug("No bluetooth config")
        return
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
        node.writeConfig("bluetooth")
        logger.debug("Waiting for reboot...")
        time.sleep(2)
        node.waitForConfig()


def do_mqtt_config(node: Node, config: Config, short_name: str) -> None:

    need_to_write_mqtt = False

    if config.mqtt is None:
        logger.debug("No MQTT config")
        return

    if config.mqtt.root is not None:
        if "{id}" in config.mqtt.root:
            config.mqtt.root = config.mqtt.root.replace("{id}", short_name)

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
        time.sleep(2)
        node.waitForConfig()


def do_owner_config(node: Node, config: Config, client: SerialInterface) -> None:

    if config.owner is None:
        logger.debug("No owner config specified!")
        return

    need_to_write_owner = False

    params = {}

    short_name = client.getShortName()

    if "{id}" in config.owner.long_name:
        config.owner.long_name = config.owner.long_name.replace("{id}", short_name)
    if "{id}" in config.owner.short_name:
        config.owner.short_name = config.owner.short_name.replace("{id}", short_name)

    if client.getLongName() != config.owner.long_name:
        params["long_name"] = config.owner.long_name
        need_to_write_owner = True
    if client.getShortName() != config.owner.short_name:
        params["short_name"] = config.owner.short_name
        need_to_write_owner = True

    if need_to_write_owner:
        node.setOwner(**params)

        logger.debug("Waiting for reboot...")
        time.sleep(2)
        node.waitForConfig()


def main() -> None:

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

    device_name = client.getLongName()
    short_name = client.getShortName()
    logger.info("Device long name: {}", device_name)
    # logger.info("Device short name: {}", short_name)
    logger.info("Device info:\n{}", client.myInfo)

    # my_node_num = client.myInfo.my_node_num
    # node = client.getNode(my_node_num)
    # logger.info("printing metadata...\n{}", node.getMetadata())
    node = client.localNode

    logger.debug("Waiting for config...")
    node.waitForConfig()

    do_owner_config(node, config, client)

    do_lora_config(node, config)

    do_mqtt_config(node, config, short_name)

    do_bluetooth_config(node, config)

    do_network_config(node, config)


if __name__ == "__main__":
    main()
