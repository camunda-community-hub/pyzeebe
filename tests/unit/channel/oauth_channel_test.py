from unittest import mock

import grpc
import pytest

from pyzeebe.channel.oauth_channel import (
    create_camunda_cloud_channel,
    create_oauth2_client_credentials_channel,
)


@pytest.fixture
def mock_oauth2metadataplugin():
    with mock.patch("pyzeebe.credentials.oauth.OAuth2MetadataPlugin") as mock_credentials:
        yield mock_credentials


def test_create_oauth2_client_credentials_channel(
    mock_oauth2metadataplugin,
):

    grpc_address = "zeebe-gateway:26500"
    client_id = "client_id"
    client_secret = "client_secret"
    authorization_server = "https://authorization.server"
    channel = create_oauth2_client_credentials_channel(grpc_address, client_id, client_secret, authorization_server)

    assert isinstance(channel, grpc.aio.Channel)


def test_create_camunda_cloud_channel(
    mock_oauth2metadataplugin,
):
    client_id = "client_id"
    client_secret = "client_secret"
    cluster_id = "cluster_id"
    region = "bru-2"
    scope = "Zeebe"
    authorization_server = "https://login.cloud.camunda.io/oauth/token"
    audience = "zeebe.camunda.io"

    channel = create_camunda_cloud_channel(
        client_id, client_secret, cluster_id, region, scope, authorization_server, audience
    )

    assert isinstance(channel, grpc.aio.Channel)
