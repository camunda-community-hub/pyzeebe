from uuid import uuid4

import grpc
import pytest
from mock import Mock, patch

from pyzeebe import create_insecure_channel
from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import (DEFAULT_HOSTNAME, DEFAULT_PORT,
                                   create_address)


class TestCreateInsecureChannel:
    @pytest.fixture(autouse=True)
    def insecure_channel_mock(self, aio_grpc_channel: grpc.aio.Channel):
        with patch("grpc.aio.insecure_channel", return_value=aio_grpc_channel) as mock:
            yield mock

    def test_returns_aio_grpc_channel(self):
        channel = create_insecure_channel()

        assert isinstance(channel, grpc.aio.Channel)

    def test_calls_using_default_grpc_options(self, insecure_channel_mock: Mock):
        create_insecure_channel()

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.kwargs["options"] == get_channel_options()

    def test_uses_default_address(self, insecure_channel_mock: Mock):
        create_insecure_channel()

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.args[0] == create_address()

    def test_overrides_default_port_if_provided(self, insecure_channel_mock: Mock):
        port = 123

        create_insecure_channel(port=port)

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.args[0] == f"{DEFAULT_HOSTNAME}:{port}"

    def test_overrides_default_hostname_if_provided(self, insecure_channel_mock: Mock):
        hostname = str(uuid4())

        create_insecure_channel(hostname=hostname)

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.args[0] == f"{hostname}:{DEFAULT_PORT}"
