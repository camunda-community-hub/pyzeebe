from unittest.mock import Mock, patch

import grpc
import pytest

from pyzeebe import create_insecure_channel
from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import get_zeebe_address


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
        assert insecure_channel_call.kwargs["target"] == get_zeebe_address()
