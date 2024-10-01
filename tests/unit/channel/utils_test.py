import os
from uuid import uuid4

from pyzeebe.channel.utils import DEFAULT_ZEEBE_ADDRESS, create_address


class TestCreateAddress:

    def test_returns_passed_address(self):
        address = str(uuid4())

        assert address == create_address(address)

    def test_returns_default_address(self):
        address = create_address()

        assert address == DEFAULT_ZEEBE_ADDRESS

    def test_returns_env_var_if_provided(self):
        zeebe_address = str(uuid4())
        os.environ["ZEEBE_ADDRESS"] = zeebe_address

        address = create_address()

        assert address == zeebe_address
