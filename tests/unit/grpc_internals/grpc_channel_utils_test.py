from random import randint
from uuid import uuid4

from mock import MagicMock, patch

from pyzeebe.grpc_internals.grpc_channel_utils import (create_channel,
                                                       create_connection_uri)


class TestCreateChannel:
    def test_creates_insecure_channel_on_default(self):
        with patch("grpc.aio.insecure_channel") as channel_mock:
            create_channel(str(uuid4()))

            channel_mock.assert_called_once()

    def test_creates_secure_channel_when_given_credentials(self):
        with patch("grpc.aio.secure_channel") as channel_mock:
            create_channel(str(uuid4()), credentials=MagicMock())

            channel_mock.assert_called_once()

    def test_creates_secure_channel_when_secure_connection_is_enabled(self):
        with patch("grpc.aio.secure_channel") as channel_mock:
            create_channel(str(uuid4()), secure_connection=True)

            channel_mock.assert_called_once()

    def test_creates_secure_channel_with_default_options(self):
        with patch("grpc.aio.insecure_channel") as channel_mock:
            create_channel(str(uuid4()), options=None)

            expected_options = (
                ("grpc.keepalive_time_ms", 45000),
            )
            assert channel_mock.call_args[1]["options"] == expected_options

    def test_creates_insecure_channel_with_options(self):
        with patch("grpc.aio.insecure_channel") as channel_mock:
            additional_options = {
                "grpc.keepalive_timeout_ms": 120000,
                "grpc.http2.min_time_between_pings_ms": 60000,
            }
            create_channel(str(uuid4()), options=additional_options)

            expected_options = (
                ("grpc.keepalive_time_ms", 45000),
                ("grpc.keepalive_timeout_ms", 120000),
                ("grpc.http2.min_time_between_pings_ms", 60000),
            )
            assert channel_mock.call_args[1]["options"] == expected_options

class TestCreateConnectionUri:
    def test_uses_credentials_first(self):
        credentials = MagicMock(return_value=str(uuid4()))

        connection_uri = create_connection_uri(
            credentials=credentials, hostname="localhost", port=123
        )

        assert connection_uri == credentials.get_connection_uri()

    def test_uses_hostname_and_port_when_given(self):
        hostname = str(uuid4())
        port = randint(0, 10000)

        connection_uri = create_connection_uri(hostname, port)

        assert connection_uri == f"{hostname}:{port}"

    def test_default_port_value_is_26500(self):
        hostname = str(uuid4())

        connection_uri = create_connection_uri(hostname)

        assert connection_uri == f"{hostname}:26500"

    def test_default_hostname_is_localhost(self):
        port = randint(0, 10000)

        connection_uri = create_connection_uri(port=port)

        assert connection_uri == f"localhost:{port}"

    def test_default_values_are_taken_from_env_variables(self):
        address = f"{str(uuid4())}:{randint(0, 10000)}"
        with patch("os.getenv", return_value=address):
            connection_uri = create_connection_uri()

            assert connection_uri == address
