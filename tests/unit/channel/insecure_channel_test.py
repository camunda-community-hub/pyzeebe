import os
import sys
from unittest.mock import Mock, patch

import grpc
import pytest

from pyzeebe import create_insecure_channel
from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import get_zeebe_address


@pytest.mark.anyio
class TestCreateInsecureChannel:
    @pytest.fixture(autouse=True)
    async def insecure_channel_mock(self, anyio_backend, aio_grpc_channel: grpc.aio.Channel):
        with patch("grpc.aio.insecure_channel", return_value=aio_grpc_channel) as mock:
            yield mock

    async def test_returns_aio_grpc_channel(self):
        channel = create_insecure_channel()

        assert isinstance(channel, grpc.aio.Channel)

    async def test_calls_using_default_grpc_options(self, insecure_channel_mock: Mock):
        create_insecure_channel()

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.kwargs["options"] == get_channel_options()

    async def test_uses_default_address(self, insecure_channel_mock: Mock):
        create_insecure_channel()

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.kwargs["target"] == get_zeebe_address()

    @patch.dict(
        os.environ,
        {"ZEEBE_ADDRESS": "ZEEBE_ADDRESS"},
    )
    @pytest.mark.xfail(sys.version_info < (3, 10), reason="https://github.com/python/cpython/issues/98086")
    async def test_uses_zeebe_address_environment_variable(self, insecure_channel_mock: Mock):
        create_insecure_channel()

        insecure_channel_call = insecure_channel_mock.mock_calls[0]
        assert insecure_channel_call.kwargs["target"] == "ZEEBE_ADDRESS"
