from __future__ import annotations

import datetime
import threading
from typing import Any

import requests

from pyzeebe.credentials.base import CredentialsABC
from pyzeebe.credentials.typing import AuthMetadata, CallContext
from pyzeebe.errors import InvalidOAuthCredentialsError


class CamundaIdentityCredentials(CredentialsABC):
    """Credentials client for Camunda Platform.

    Args:
        oauth_url (str): The Keycloak auth endpoint url.
        client_id (str): The client id provided by Camunda Platform
        client_secret (str): The client secret provided by Camunda Platform
        audience (str): Audience for Zeebe. Default: zeebe-api
        refresh_threshold_seconds (int): Will try to refresh token if it expires in this number of seconds or less. Default: 20
    """

    def __init__(
        self,
        *,
        oauth_url: str,
        client_id: str,
        client_secret: str,
        audience: str = "zeebe-api",
        refresh_threshold_seconds: int = 20,
    ) -> None:
        self.oauth_url = oauth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience

        self._lock = threading.Lock()
        self._refresh_threshold = datetime.timedelta(seconds=refresh_threshold_seconds)

        self._token: dict[str, Any] | None = None
        self._expires_in: datetime.datetime | None = None

    def _expired(self) -> bool:
        return (
            self._token is None
            or self._expires_in is None
            or (self._expires_in - self._refresh_threshold) < datetime.datetime.now(datetime.timezone.utc)
        )

    def _refresh(self) -> None:
        try:
            response = requests.post(
                self.oauth_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": self.audience,
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._expires_in = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                seconds=int(data["expires_in"])
            )
        except requests.HTTPError as http_error:
            raise InvalidOAuthCredentialsError(
                url=self.oauth_url, client_id=self.client_id, audience=self.audience
            ) from http_error

    def get_auth_metadata(self, context: CallContext) -> AuthMetadata:
        """
        Args:
            context (grpc.AuthMetadataContext): Provides information to call credentials metadata plugins.

        Returns:
            Tuple[Tuple[str, Union[str, bytes]], ...]: The `metadata` used to construct the :py:class:`grpc.CallCredentials`.

        Raises:
            InvalidOAuthCredentialsError: One of the provided camunda credentials is not correct
        """
        with self._lock:
            if self._expired() is True:
                self._refresh()
            return (("authorization", f"Bearer {self._token}"),)
