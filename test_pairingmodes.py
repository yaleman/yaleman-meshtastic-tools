import pytest
from configure import BluetoothConfig


def test_pairingmodes() -> None:
    BluetoothConfig(mode="RANDOM_PIN")  # type: ignore

    BluetoothConfig(mode=1)  # type: ignore

    with pytest.raises(ValueError):
        BluetoothConfig(mode="INVALID")  # type: ignore
