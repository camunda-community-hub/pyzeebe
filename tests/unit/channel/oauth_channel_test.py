import pytest
from unittest import mock
from pyzeebe.channel.oauth_channel import create_oauth2_client_credentials_channel
import grpc
from oauthlib import oauth2
from pyzeebe.credentials.oauth import OAuth2ClientCredentials


@pytest.fixture
def mock_oauth2_credentials():
    with mock.patch("pyzeebe.credentials.oauth.OAuth2ClientCredentials") as mock_credentials:
        yield mock_credentials


@pytest.fixture
def mock_grpc_methods():
    with mock.patch("grpc.metadata_call_credentials") as mock_metadata, mock.patch(
        "grpc.ssl_channel_credentials"
    ) as mock_ssl, mock.patch("grpc.aio.secure_channel") as mock_secure_channel:
        mock_secure_channel.return_value = mock.MagicMock(spec=grpc.aio.Channel)
        yield mock_metadata, mock_ssl, mock_secure_channel


@mock.patch("pyzeebe.credentials.oauth.OAuth2ClientCredentials")
@mock.patch("grpc.metadata_call_credentials")
@mock.patch("grpc.ssl_channel_credentials")
@mock.patch("grpc.composite_channel_credentials")
@mock.patch("grpc.aio.secure_channel")
def test_create_oauth2_client_credentials_channel_valid(
    mock_secure_channel,
    mock_composite_credentials,
    mock_ssl_credentials,
    mock_metadata_credentials,
    mock_oauth2_credentials,
):
    # Mock the return value of ssl_channel_credentials and metadata_call_credentials to be ChannelCredentials
    mock_ssl_credentials.return_value = grpc.ssl_channel_credentials()
    mock_metadata_credentials.return_value = grpc.metadata_call_credentials(lambda context: context)

    # Mock the composite_channel_credentials to accept any arguments and return a ChannelCredentials instance
    mock_composite_credentials.return_value = grpc.ChannelCredentials(None)

    # Mock the secure_channel to return a MagicMock, simulating grpc.aio.Channel
    mock_secure_channel.return_value = mock.MagicMock(spec=grpc.aio.Channel)

    # Call the function under test
    target = "zeebe-gateway:26500"
    client_id = "client_id"
    client_secret = "client_secret"
    authorization_server = "https://authorization.server"
    channel = create_oauth2_client_credentials_channel(target, client_id, client_secret, authorization_server)

    assert isinstance(channel, grpc.aio.Channel)


# def test_create_oauth2_client_credentials_channel_missing_credentials():
#     with pytest.raises(
#         oauth2.OAuth2Error
#     ):  # Assuming Exception is replaced with a specific exception for invalid credentials
#         create_oauth2_client_credentials_channel("", "", "", "")


def test_create_oauth2_client_credentials_channel_invalid_channel_options(mock_oauth2_credentials, mock_grpc_methods):
    target = "zeebe-gateway:26500"
    client_id = "client_id"
    client_secret = "client_secret"
    authorization_server = "https://authorization.server"
    channel_options = "invalid_options"  # This should be a dict, using a string to simulate invalid input
    with pytest.raises(
        Exception
    ):  # Assuming Exception is replaced with a specific exception for invalid channel options
        create_oauth2_client_credentials_channel(
            target, client_id, client_secret, authorization_server, channel_options=channel_options
        )
