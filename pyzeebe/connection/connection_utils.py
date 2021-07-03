import os
from typing import Optional

from pyzeebe import OAuthCredentials
from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.errors.connection_errors import EnvironmentConfigError

DEFAULT_ZEEBE_HOST = "localhost"
DEFAULT_ZEEBE_PORT = 26500


class Options:
    def __init__(self, hostname: str, port: int, credentials: BaseCredentials, secure_connection: bool) -> None:
        self.hostname = hostname
        self.port = port
        self.credentials = credentials
        self.secure_connection = secure_connection


def merge_options(hostname: Optional[str] = None, port: Optional[int] = None,
                  credentials: Optional[BaseCredentials] = None, secure_connection: Optional[bool] = None) -> Options:
    # if the user provides either, we'll ignore ZEEBE_ADDRESS
    if not hostname or not port:
        zeebe_address_env = os.getenv("ZEEBE_ADDRESS")
        if zeebe_address_env:
            hostname, port_ = zeebe_address_env.rsplit(":", 1)
            if port_ and str(port_).isdigit():
                port = int(port)
    hostname = hostname or DEFAULT_ZEEBE_HOST
    port = port or DEFAULT_ZEEBE_PORT
    credentials = credentials or _get_oauth2_credentials(hostname, port)
    secure_connection = secure_connection if secure_connection is not None else bool(credentials)
    return Options(hostname, port, credentials, secure_connection)


def _check_missing_oauth2_env_key(err: KeyError):
    """ Raise exception if user specifies one of these, and missing others """
    oauth_environ_keys = [
        "ZEEBE_AUTHORIZATION_SERVER_URL",
        "ZEEBE_CLIENT_SECRET",
        "ZEEBE_CLIENT_ID",
    ]
    if any(key in os.environ for key in oauth_environ_keys):
        raise EnvironmentConfigError(
            f"Some keys for OAuth2 specified, but missing {err.args[0]}"
        ) from err


def _get_oauth2_credentials(hostname, port) -> Optional[OAuthCredentials]:
    """
    When setting up a Camunda Cloud cluster, the would get a file containing the following:

        export ZEEBE_ADDRESS='<cluster id>.zeebe.camunda.io:443'
        export ZEEBE_CLIENT_ID='<client id>'
        export ZEEBE_CLIENT_SECRET='<client secret>'
        export ZEEBE_AUTHORIZATION_SERVER_URL='https://login.cloud.camunda.io/oauth/token'
    """
    try:
        auth_server_url = os.environ["ZEEBE_AUTHORIZATION_SERVER_URL"]
        client_secret = os.environ["ZEEBE_CLIENT_SECRET"]
        client_id = os.environ["ZEEBE_CLIENT_ID"]
        audience = os.getenv("ZEEBE_TOKEN_AUDIENCE", f"{hostname}:{port}")
    except KeyError as err:
        _check_missing_oauth2_env_key(err)
        return None
    return OAuthCredentials(
        url=auth_server_url,
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
    )
