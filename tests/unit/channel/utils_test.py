import os
from uuid import uuid4

from pyzeebe.channel.utils import DEFAULT_ADDRESS, create_address


class TestCreateAddress:
    def test_returns_default_address(self):
        address = create_address()

        assert address == DEFAULT_ADDRESS

    def test_default_port_is_26500(self):
        address = create_address(hostname=str(uuid4()))

        assert address.split(":")[1] == "26500"

    def test_default_hostname_is_localhost(self):
        address = create_address(port=12)

        assert address.split(":")[0] == "localhost"

    def test_returns_env_var_if_provided(self):
        zeebe_address = str(uuid4())
        os.environ["ZEEBE_ADDRESS"] = zeebe_address

        address = create_address()

        assert address == zeebe_address
