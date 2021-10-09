from typing import Dict, Optional

import grpc
from oauthlib import oauth2
from requests import HTTPError
from requests_oauthlib import OAuth2Session

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.errors import (InvalidCamundaCloudCredentialsError,
                            InvalidOAuthCredentialsError)


def create_camunda_cloud_channel(
    client_id: str,
    client_secret: str,
    cluster_id: str,
    region: str = "bru-2",
    channel_options: Optional[Dict] = None,
) -> grpc.aio.Channel:
    """
    Create channel connected to a Camunda Cloud cluster

    Args:
        client_id (str): The client id provided by Camunda Cloud
        client_secret (str): The client secret provided by Camunda Cloud
        cluster_id (str): The zeebe cluster id to connect to
        region (str): The cluster's region. Defaults to bru-2
        channel_options (Optional[Dict], optional): GRPC channel options. See https://grpc.github.io/grpc/python/glossary.html

    Returns:
        grpc.aio.Channel: A GRPC Channel connected to the Zeebe gateway.

    Raises:
        InvalidCamundaCloudCredentialsError: One of the provided camunda credentials is not correct
    """
    channel_credentials = _create_camunda_cloud_credentials(
        client_id, client_secret, cluster_id, region
    )

    return grpc.aio.secure_channel(
        f"{cluster_id}.{region}.zeebe.camunda.io:443",
        channel_credentials,
        options=get_channel_options(channel_options),
    )


def _create_camunda_cloud_credentials(
    client_id: str, client_secret: str, cluster_id: str, region: str
) -> grpc.ChannelCredentials:
    try:
        access_token = _get_access_token(
            "https://login.cloud.camunda.io/oauth/token",
            client_id,
            client_secret,
            f"{cluster_id}.{region}.zeebe.camunda.io",
        )
        return _create_oauth_credentials(access_token)
    except InvalidOAuthCredentialsError as oauth_error:
        raise InvalidCamundaCloudCredentialsError(
            client_id, cluster_id
        ) from oauth_error


def _get_access_token(
    url: str, client_id: str, client_secret: str, audience: str
) -> str:
    try:
        client = oauth2.BackendApplicationClient(client_id)
        client.prepare_request_body(include_client_id=True)
        with OAuth2Session(client=client) as session:
            response = session.post(
                url,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": audience,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]
    except HTTPError as http_error:
        raise InvalidOAuthCredentialsError(
            url=url, client_id=client_id, audience=audience
        ) from http_error


def _create_oauth_credentials(access_token: str) -> grpc.ChannelCredentials:
    token_credentials = grpc.access_token_call_credentials(access_token)
    ssl_credentials = grpc.ssl_channel_credentials()
    return grpc.composite_channel_credentials(ssl_credentials, token_credentials)
