from typing import Optional

import grpc
from grpc.aio._typing import ChannelArgumentType

from pyzeebe.credentials.oauth import OAuth2ClientCredentials


def create_oauth2_client_credentials_channel(
    target: str,
    client_id: str,
    client_secret: str,
    authorization_server: str,
    scope: Optional[str] = None,
    audience: Optional[str] = None,
    expire_in: Optional[int] = 0,
    channel_options: Optional[ChannelArgumentType] = None,
) -> grpc.aio.Channel:
    """
    Create channel connected to a Camunda Cloud cluster

    Args:
        target (str): The target address of the Zeebe Gateway.

        client_id (str): The client id provided by Camunda Cloud
        client_secret (str): The client secret provided by Camunda Cloud
        authorization_server (str): The server issuing access tokens
        to the client after successfully authenticating the resource owner
        and obtaining authorization.
        scope (Optional[str]): The Access Token Scope.
        audience (Optional[str]): The audience for the token.

        expire_in (Optional[int]): Only used if the token does not contain an "expires_in" attribute. The number of seconds the token is valid for.

        channel_options (Optional[Dict], optional): GRPC channel options. See https://grpc.github.io/grpc/python/glossary.html

    Returns:
        grpc.aio.Channel: A GRPC Channel connected to the Zeebe Gateway.

    Raises:
        InvalidOAuthCredentialsError: One of the provided camunda credentials is not correct
    """

    oauth2_client_credentials = OAuth2ClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        scope=scope,
        audience=audience,
        expire_in=expire_in,
    )

    call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
    channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials()

    composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
        channel_credentials, call_credentials
    )

    channel: grpc.aio.Channel = grpc.aio.secure_channel(
        target=target, credentials=composite_credentials, options=channel_options
    )

    return channel
