from typing import Optional

from meshtastic.serial_interface import SerialInterface
from meshtastic.util import camel_to_snake
from loguru import logger
from pydantic import BaseModel


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


class Config(BaseModel):
    mqtt: Optional[MqttConfig] = None


def main():

    config = Config.model_validate_json(
        open("config.json", "r", encoding="utf-8").read()
    )
    client = SerialInterface(None)

    try:
        client.getShortName()
    except Exception:
        logger.error("Failed to get shortname, probably not connected!")
        return

    logger.info("Device name: {}", client.getLongName())
    logger.info("Device info:")
    logger.info(client.myInfo)

    my_node_num = client.myInfo.my_node_num
    node = client.getNode(my_node_num)
    print(node.getMetadata())

    need_to_write_mqtt = False
    for key, value in config["mqtt"].items():
        key = camel_to_snake(key)
        if not hasattr(node.moduleConfig.mqtt, key):
            print(f"mqtt has no attribute {key}")
            continue
        oldvalue = getattr(node.moduleConfig.mqtt, key)
        if oldvalue != value:
            setattr(node.moduleConfig.mqtt, key, value)
            print(f"updating mqtt {key} from {oldvalue} to {value}")
            need_to_write_mqtt = True
    if need_to_write_mqtt:
        print("writing mqtt config")
        node.writeConfig("mqtt")


if __name__ == "__main__":
    main()
