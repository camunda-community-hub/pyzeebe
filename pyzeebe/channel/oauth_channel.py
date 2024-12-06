from __future__ import annotations

from functools import partial

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import (
    get_camunda_address,
    get_camunda_client_id,
    get_camunda_client_secret,
    get_camunda_cluster_id,
    get_camunda_cluster_region,
    get_camunda_oauth_url,
    get_camunda_token_audience,
    get_zeebe_address,
)
from pyzeebe.credentials.oauth import Oauth2ClientCredentialsMetadataPlugin
from pyzeebe.types import ChannelArgumentType, Unset


def create_oauth2_client_credentials_channel(
    grpc_address: str = Unset,
    client_id: str = Unset,
    client_secret: str = Unset,
    authorization_server: str = Unset,
    scope: str | None = Unset,
    audience: str | None = Unset,
    channel_credentials: grpc.ChannelCredentials | None = None,
    channel_options: ChannelArgumentType | None = None,
    leeway: int = 60,
    expire_in: int | None = None,
) -> grpc.aio.Channel:
    """Create a gRPC channel for connecting to Camunda 8 (Self-Managed) with OAuth2ClientCredentials.

    https://oauth.net/2/grant-types/client-credentials/
    https://datatracker.ietf.org/doc/html/rfc6749#section-11.2.2

    Args:
        grpc_address (str, optional): Zeebe Gateway Address.
            Defaults to value from ZEEBE_ADDRESS environment variable
            or "{CAMUNDA_CLUSTER_ID}.{CAMUNDA_CLUSTER_REGION}.zeebe.camunda.io:443"
            or "localhost:26500".
        client_id (str, optional): The client id.
            Defaults to value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable
        client_secret (str, optional): The client secret.
            Defaults to value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable
        authorization_server (str, optional): The authorization server issuing access tokens
            to the client after successfully authenticating the client.
            Defaults to value from CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
        scope (str | None, optional): The scope of the access request.
        audience (str | None, optional): The audience for authentication.
            Defaults to value from CAMUNDA_TOKEN_AUDIENCE or ZEEBE_TOKEN_AUDIENCE environment variable

        channel_credentials (grpc.ChannelCredentials | None): The gRPC channel credentials.
            Defaults to `grpc.ssl_channel_credentials`.
        channel_options (ChannelArgumentType | None): Additional options for the gRPC channel.
            Defaults to None.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

        leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
            Defaults to 60.
        expire_in (int | None): The number of seconds the token is valid for. Defaults to None.
            Should only be used if the token does not contain an "expires_in" attribute.

    Returns:
        grpc.aio.Channel: A gRPC channel connected to the Zeebe Gateway.

    Raises:
        InvalidOAuthCredentialsError: One of the provided camunda credentials is not correct
    """

    if grpc_address is Unset:
        grpc_address = get_zeebe_address()

    if client_id is Unset:
        client_id = get_camunda_client_id()

    if client_secret is Unset:
        client_secret = get_camunda_client_secret()

    if authorization_server is Unset:
        authorization_server = get_camunda_oauth_url()

    if scope is Unset:
        scope = None

    if audience is Unset:
        audience = get_camunda_token_audience()

    oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        scope=scope,
        audience=audience,
        leeway=leeway,
        expire_in=expire_in,
    )

    call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
    composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
        channel_credentials or grpc.ssl_channel_credentials(), call_credentials
    )

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=grpc_address,
        credentials=composite_credentials,
        options=get_channel_options(channel_options),
    )

    return channel


def create_camunda_cloud_channel(
    client_id: str = Unset,
    client_secret: str = Unset,
    cluster_id: str = Unset,
    region: str = Unset,
    authorization_server: str = Unset,
    scope: str | None = Unset,
    audience: str | None = Unset,
    channel_credentials: grpc.ChannelCredentials | None = None,
    channel_options: ChannelArgumentType | None = None,
    leeway: int = 60,
    expire_in: int | None = None,
) -> grpc.aio.Channel:
    """Create a gRPC channel for connecting to Camunda 8 Cloud (SaaS).

    Args:
        client_id (str, optional): The client id.
            Defaults to value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable.
        client_secret (str, optional): The client secret.
            Defaults to value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable.
        cluster_id (str, optional): The ID of the cluster to connect to.
            Defaults to value from CAMUNDA_CLUSTER_ID environment variable.
        region (str, optional): The region of the cluster.
            Defaults to value from CAMUNDA_CLUSTER_REGION environment variable or 'bru-2'.
        authorization_server (str, optional): The authorization server issuing access tokens
            to the client after successfully authenticating the client.
            Defaults to value from CAMUNDA_OAUTH_URL
            or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
            or "https://login.cloud.camunda.io/oauth/token".
        scope (str | None, optional): The scope of the access request.
        audience (str | None, optional): The audience for authentication.
            Defaults to value from CAMUNDA_TOKEN_AUDIENCE
            or ZEEBE_TOKEN_AUDIENCE environment variable
            or "zeebe.camunda.io".

        channel_credentials (grpc.ChannelCredentials | None): The gRPC channel credentials.
            Defaults to `grpc.ssl_channel_credentials`.
        channel_options (ChannelArgumentType | None): Additional options for the gRPC channel.
            Defaults to None.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

        leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
            Defaults to 60.
        expire_in (int | None): The number of seconds the token is valid for. Defaults to None.
            Should only be used if the token does not contain an "expires_in" attribute.

    Returns:
        grpc.aio.Channel: The gRPC channel for connecting to Camunda Cloud.
    """

    if client_id is Unset:
        client_id = get_camunda_client_id()

    if client_secret is Unset:
        client_secret = get_camunda_client_secret()

    if cluster_id is Unset:
        cluster_id = get_camunda_cluster_id()

    if region is Unset:
        region = get_camunda_cluster_region("bru-2")

    if authorization_server is Unset:
        authorization_server = get_camunda_oauth_url("https://login.cloud.camunda.io/oauth/token")

    if scope is Unset:
        scope = None

    if audience is Unset:
        audience = get_camunda_token_audience("zeebe.camunda.io")

    oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        scope=scope,
        audience=audience,
        leeway=leeway,
        expire_in=expire_in,
    )

    # NOTE: Overwrite the _oauth.fetch_token method to include client_id, client_secret in the request body
    func = partial(
        oauth2_client_credentials._oauth.fetch_token,
        include_client_id=True,
        token_url=authorization_server,
        client_secret=client_secret,
        audience=audience,
    )
    oauth2_client_credentials._func_retrieve_token = func

    call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
    composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
        channel_credentials or grpc.ssl_channel_credentials(), call_credentials
    )

    grpc_address = get_camunda_address(cluster_id=cluster_id, cluster_region=region)

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=grpc_address, credentials=composite_credentials, options=get_channel_options(channel_options)
    )

    return channel
