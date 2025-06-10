import pytest
from configure import BluetoothConfig


def test_pairingmodes() -> None:
    """ test bluetooth config """
    BluetoothConfig(mode="RANDOM_PIN")

    BluetoothConfig(mode=1)

    with pytest.raises(ValueError):
        BluetoothConfig(mode="INVALID")
