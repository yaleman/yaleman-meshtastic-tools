import pytest
from configure import LoraConfig


def test_mode() -> None:
    with pytest.raises(ValueError):
        LoraConfig(region="US915", modem_preset="FOO")
        LoraConfig(region="EXAMPLE", modem_preset="LONG_FAST")

    LoraConfig(region="ANZ", modem_preset="LONG_FAST")
