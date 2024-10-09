from functools import partial
from typing import Optional

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.credentials.oauth import Oauth2ClientCredentialsMetadataPlugin
from pyzeebe.types import ChannelArgumentType


def create_oauth2_client_credentials_channel(
    grpc_address: str,
    client_id: str,
    client_secret: str,
    authorization_server: str,
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
        grpc_address (str): Zeebe Gateway Address.

        client_id (str): The client id.
        client_secret (str): The client secret.
        authorization_server (str): The authorization server issuing access tokens
            to the client after successfully authenticating the client.
        scope (Optional[str]): The scope of the access request. Defaults to None.
        audience (Optional[str]): The audience for authentication. Defaults to None.

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
        channel_credentials, call_credentials
    )

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=grpc_address, credentials=composite_credentials, options=get_channel_options(channel_options)
    )

    return channel


def create_camunda_cloud_channel(
    client_id: str,
    client_secret: str,
    cluster_id: str,
    region: str = "bru-2",
    channel_options: Optional[ChannelArgumentType] = None,
) -> grpc.aio.Channel:
    """Create a gRPC channel for connecting to Camunda 8 Cloud (SaaS).

    Args:
        client_id (str): The client id.
        client_secret (str): The client secret.
        cluster_id (str): The ID of the cluster to connect to.
        region (Optional[str]): The region of the cluster. Defaults to "bru-2".

        channel_options (Optional[ChannelArgumentType]): Additional options for the gRPC channel.
            Defaults to None.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

    Returns:
        grpc.aio.Channel: The gRPC channel for connecting to Camunda Cloud.
    """

    grpc_address = f"{cluster_id}.{region}.zeebe.camunda.io:443"
    audience = f"{cluster_id}.{region}.zeebe.camunda.io"
    authorization_server = "https://login.cloud.camunda.io/oauth/token"

    oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        audience=audience,
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
        grpc.ssl_channel_credentials(), call_credentials
    )

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=grpc_address, credentials=composite_credentials, options=get_channel_options(channel_options)
    )

    return channel
