import base64
import json
import os
import sys
from typing import Any, Optional

import click
import paho.mqtt.client as mqtt
from meshtastic import mqtt_pb2, portnums_pb2, mesh_pb2, protocols, BROADCAST_NUM  # type: ignore
from google.protobuf.json_format import MessageToDict  # type: ignore

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

ROOT_TOPIC = "msh"
DEFAULT_KEY = "1PG7OiApB1nwvP+rz05pAQ=="
NODE_NAMES: dict[str, str] = {}


# with thanks to pdxlocs
def try_decode(mp: Any) -> None:
    """ decode a packet """
    key_bytes = base64.b64decode(DEFAULT_KEY.encode("ascii"))

    nonce = getattr(mp, "id").to_bytes(8, "little") + getattr(mp, "from").to_bytes(
        8, "little"
    )
    cipher = Cipher(
        algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
    )
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()

    data = mesh_pb2.Data()
    data.ParseFromString(decrypted_bytes)
    mp.decoded.CopyFrom(data)


def on_connect(client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Optional[dict[str,Any]]=None) -> None:
    """ handle connect events """
    if reason_code == 0:
        print("Connected!")
        client.subscribe("meshtastic/2/c/#")
        client.subscribe("msh/2/c/#")
        client.subscribe("meshtastic/2/e/#")
        client.subscribe("msh/2/e/#")
    else:
        print(f"{userdata} {flags} {reason_code} {properties}")


def on_disconnect(_client: Any, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any=None) -> None:
    """ handle disconnect events """
    print(f"disconnected with reason code {str(reason_code)}")


def parse_message(message_input: bytes, msg: Optional[Any]) -> Optional[str]:
    """ parse a message from the MQTT broker """
    se = mqtt_pb2.ServiceEnvelope()
    try:
        se.ParseFromString(message_input)
        mp = se.packet
    except Exception as e:
        print(f"ERROR: parsing service envelope: {str(e)}")
        if msg is not None:
            print(f"{msg.info} {msg.payload}")
        return None

    from_id = getattr(mp, "from")
    if from_id in NODE_NAMES:
        from_id = f"{from_id:08x}[{NODE_NAMES.get(getattr(mp,'from'))}]"
    else:
        from_id = f"{from_id:08x}"
    to_id = mp.to
    if to_id == BROADCAST_NUM:
        to_id = "all"
    else:
        to_id = f"{to_id:08x}"

    pn = portnums_pb2.PortNum.Name(mp.decoded.portnum)

    # prefix = f"{mp.channel} [{from_id}->{to_id}] {pn}:"
    if mp.HasField("encrypted") and not mp.HasField("decoded"):
        try:
            try_decode(mp)

            pn = portnums_pb2.PortNum.Name(
                mp.decoded.portnum
            )  # type: ignore[no-member]
            # prefix = f"{mp.channel} [{from_id}->{to_id}] {pn}:"
        except Exception as e:
            print(f"message could not be decrypted {e}", file=sys.stderr)
            return None
    message = {
        "channel": mp.channel,
        "from_id": from_id,
        "to_id": to_id,
        "portnum": pn,
    }
    handler = protocols.get(mp.decoded.portnum)
    if handler is None:
        print(f"{message} no handler came from protocols", file=sys.stderr)
        return None

    if handler.protobufFactory is None:
        message["payload"] = mp.decoded.payload
    else:
        pb = handler.protobufFactory()
        pb.ParseFromString(mp.decoded.payload)
        for key, value in MessageToDict(pb).items():
            message[key] = value
        if mp.decoded.portnum == portnums_pb2.PortNum.NODEINFO_APP:
            # print(f"node {getattr(mp,'from'):x} has short_name {pb.short_name}")
            NODE_NAMES[getattr(mp, "from")] = pb.short_name
            message["from_id"] = (
                f"{getattr(mp,'from'):x}[{NODE_NAMES.get(getattr(mp,'from'))}]"
            )
    print(json.dumps(message))
    return None


def on_message(_client: Any, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
    """ handle incoming messages """
    parse_message(msg.payload, msg)


def connect(client: Any, username: str, pw: str, broker: str, port: int) -> None:
    """ connect to the MQTT broker """
    try:
        client.username_pw_set(username, pw)
        client.connect(broker, port, 60)
    except Exception as e:
        print(f"failed connect: {str(e)}")


@click.command()
@click.option("--hostname", default=os.getenv("MQTT_HOSTNAME"))
@click.option("--port", default=int(os.getenv("MQTT_PORT", 1883)), type=int)
@click.option("--decode")
def main(
    hostname: Optional[str] = None, port: int = 1883, decode: Optional[str] = None
) -> None:
    if decode is not None:
        parse_message(
            base64.b64decode(decode.encode("utf-8")),
            None,
        )
    else:
        if hostname is None:
            print("hostname is required")
            return
        try:
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2, # type: ignore[attr-defined]
                client_id="",
                clean_session=True,
                userdata=None,
            )
        except Exception as _:
            client = mqtt.Client(client_id="", clean_session=True, userdata=None)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        print(f"Connecting to {hostname}:{port}...", file=sys.stderr)
        client.connect(hostname, port=port)
        client.loop_forever()


if __name__ == "__main__":

    main()
