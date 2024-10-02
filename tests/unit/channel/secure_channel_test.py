from unittest.mock import Mock, patch

import grpc
import pytest

from pyzeebe import create_secure_channel
from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import get_zeebe_address


class TestCreateSecureChannel:
    @pytest.fixture(autouse=True)
    def secure_channel_mock(self, aio_grpc_channel: grpc.aio.Channel):
        with patch("grpc.aio.secure_channel", return_value=aio_grpc_channel) as mock:
            yield mock

    def test_returns_grpc_channel(self):
        channel = create_secure_channel()

        assert isinstance(channel, grpc.aio.Channel)

    def test_uses_ssl_credentials_if_no_channel_credentials_provided(self):
        with patch("grpc.ssl_channel_credentials") as ssl_mock:
            create_secure_channel()

        ssl_mock.assert_called_once()

    def test_calls_using_default_grpc_options(self, secure_channel_mock: Mock):
        create_secure_channel()

        secure_channel_call = secure_channel_mock.mock_calls[0]
        assert secure_channel_call.kwargs["options"] == get_channel_options()

    def test_uses_default_address(self, secure_channel_mock: Mock):
        create_secure_channel()

        secure_channel_call = secure_channel_mock.mock_calls[0]
        assert secure_channel_call.kwargs["target"] == get_zeebe_address()
