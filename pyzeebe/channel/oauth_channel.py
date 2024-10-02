from functools import partial
from typing import Optional

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import (
    get_camunda_client_id,
    get_camunda_client_secret,
    get_camunda_cloud_cluster_id,
    get_camunda_cloud_cluster_region,
    get_camunda_cloud_hostname,
    get_camunda_credentials_scopes,
    get_camunda_oauth_url,
    get_camunda_token_audience,
    get_zeebe_address,
)
from pyzeebe.credentials.oauth import Oauth2ClientCredentialsMetadataPlugin
from pyzeebe.types import ChannelArgumentType


def create_oauth2_client_credentials_channel(
    grpc_address: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    authorization_server: Optional[str] = None,
    scope: Optional[str] = None,
    audience: Optional[str] = None,
    channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials(),
    channel_options: Optional[ChannelArgumentType] = None,
    leeway: int = 60,
    expire_in: Optional[int] = None,
) -> grpc.aio.Channel:
    """Create a gRPC channel for connecting to Camunda 8 (Self-Managed) with OAuth2ClientCredentials.

    https://oauth.net/2/grant-types/client-credentials/
    https://datatracker.ietf.org/doc/html/rfc6749#section-11.2.2

    Args:
        grpc_address (Optional[str]): Zeebe Gateway Address.
            Defaults to value from ZEEBE_ADDRESS environment variable
                    or "{CAMUNDA_CLUSTER_ID}.{CAMUNDA_CLUSTER_REGION}.zeebe.camunda.io:443"
                    or "localhost:26500".
        client_id (Optional[str]): The client id.
            Defaults to value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable
        client_secret (Optional[str]): The client secret.
            Defaults to value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable
        authorization_server (Optional[str]): The authorization server issuing access tokens
            to the client after successfully authenticating the client.
            Defaults to value from CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
        scope (Optional[str]): The scope of the access request.
            Defaults to value from CAMUNDA_CREDENTIALS_SCOPES environment variable.
        audience (Optional[str]): The audience for authentication.
            Defaults to value from CAMUNDA_TOKEN_AUDIENCE or ZEEBE_TOKEN_AUDIENCE environment variable

        channel_credentials (grpc.ChannelCredentials): The gRPC channel credentials.
            Defaults to grpc.ssl_channel_credentials().
        channel_options (Optional[ChannelArgumentType]): Additional options for the gRPC channel.
            Defaults to None.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

        leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
            Defaults to 60.
        expire_in (Optional[int]): The number of seconds the token is valid for. Defaults to None.
            Should only be used if the token does not contain an "expires_in" attribute.

    Returns:
        grpc.aio.Channel: A gRPC channel connected to the Zeebe Gateway.

    Raises:
        InvalidOAuthCredentialsError: One of the provided camunda credentials is not correct
    """

    authorization_server = get_camunda_oauth_url(authorization_server)

    if not authorization_server:
        raise ValueError("ZEEBE_AUTHORIZATION_SERVER_URL is not configured")

    oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
        client_id=get_camunda_client_id(client_id),
        client_secret=get_camunda_client_secret(client_secret),
        authorization_server=authorization_server or "",
        scope=get_camunda_credentials_scopes(scope),
        audience=get_camunda_token_audience(audience),
        leeway=leeway,
        expire_in=expire_in,
    )

    call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
    composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
        channel_credentials, call_credentials
    )

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=get_zeebe_address(grpc_address),
        credentials=composite_credentials,
        options=get_channel_options(channel_options),
    )

    return channel


def create_camunda_cloud_channel(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    cluster_id: Optional[str] = None,
    region: Optional[str] = None,
    scope: Optional[str] = None,
    authorization_server: Optional[str] = None,
    audience: Optional[str] = None,
    channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials(),
    channel_options: Optional[ChannelArgumentType] = None,
    leeway: int = 60,
    expire_in: Optional[int] = None,
) -> grpc.aio.Channel:
    """Create a gRPC channel for connecting to Camunda 8 Cloud (SaaS).

    Args:
        client_id (Optional[str]): The client id.
            Defaults to value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable.
        client_secret (Optional[str]): The client secret.
            Defaults to value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable.
        cluster_id (Optional[str]): The ID of the cluster to connect to.
            Defaults to value from CAMUNDA_CLUSTER_ID environment variable.
        region (Optional[str]): The region of the cluster.
            Defaults to value from CAMUNDA_CLUSTER_REGION environment variable or 'bru-2'.
        scope (Optional[str]): The scope of the access request.
            Defaults to value from CAMUNDA_CREDENTIALS_SCOPES environment variable or 'Zeebe'.
        authorization_server (Optional[str]): The authorization server issuing access tokens
            to the client after successfully authenticating the client.
            Defaults to value from CAMUNDA_OAUTH_URL
                or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
                or "https://login.cloud.camunda.io/oauth/token".
        audience (Optional[str]): The audience for authentication.
            Defaults to value from CAMUNDA_TOKEN_AUDIENCE
                or ZEEBE_TOKEN_AUDIENCE environment variable
                or "{cluster_id}.{region}.zeebe.camunda.io"
                or "zeebe.camunda.io".

        channel_credentials (grpc.ChannelCredentials): The gRPC channel credentials.
            Defaults to grpc.ssl_channel_credentials().
        channel_options (Optional[ChannelArgumentType]): Additional options for the gRPC channel.
            Defaults to None.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

        leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
            Defaults to 60.
        expire_in (Optional[int]): The number of seconds the token is valid for. Defaults to None.
            Should only be used if the token does not contain an "expires_in" attribute.

    Returns:
        grpc.aio.Channel: The gRPC channel for connecting to Camunda Cloud.
    """

    cluster_id = get_camunda_cloud_cluster_id(cluster_id)
    region = get_camunda_cloud_cluster_region(region)

    oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
        client_id=get_camunda_client_id(client_id),
        client_secret=get_camunda_client_secret(client_secret),
        authorization_server=get_camunda_oauth_url(authorization_server)
        or "https://login.cloud.camunda.io/oauth/token",
        scope=get_camunda_credentials_scopes(scope) or "Zeebe",
        audience=get_camunda_token_audience(audience) or "zeebe.camunda.io",
        leeway=leeway,
        expire_in=expire_in,
    )

    # NOTE: Overwrite the _oauth.fetch_token method to include client_id in the request body
    oauth2_client_credentials._func_retrieve_token = partial(
        oauth2_client_credentials._func_retrieve_token,
        include_client_id=True,
    )

    call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
    # channel_credentials: grpc.ChannelCredentials = channel_credentials or grpc.ssl_channel_credentials()
    composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
        channel_credentials, call_credentials
    )

    grpc_hostname = get_camunda_cloud_hostname(cluster_id, region)
    if grpc_hostname:
        grpc_address = f"{grpc_hostname}:443"
    else:
        grpc_address = get_zeebe_address(None)

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=grpc_address, credentials=composite_credentials, options=get_channel_options(channel_options)
    )

    return channel
