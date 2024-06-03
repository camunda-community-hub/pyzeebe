import datetime
import threading
from typing import Any, Dict, Optional

import requests

from pyzeebe.credentials.base import Credentials
from pyzeebe.credentials.typing import AuthMetadata, CallContext
from pyzeebe.errors import InvalidOAuthCredentialsError


class CamundaIdentityCredentials(Credentials):
    def __init__(
        self,
        *,
        oauth_url: str,
        client_id: str,
        client_secret: str,
        audience: str = "zeebe-api",
        refresh_threshold_seconds: int = 20
    ) -> None:
        self.oauth_url = oauth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience

        self._lock = threading.Lock()
        self._refresh_threshold = datetime.timedelta(seconds=refresh_threshold_seconds)

        self._token: Optional[Dict[str, Any]] = None
        self._expires_in: Optional[datetime.datetime] = None

    def expired(self) -> bool:
        return (
            self._token is None
            or self._expires_in is None
            or (self._expires_in - self._refresh_threshold) < datetime.datetime.now(datetime.timezone.utc)
        )

    def refresh(self) -> None:
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
        with self._lock:
            if self.expired() is True:
                self.refresh()
            return (("authorization", "Bearer {}".format(self._token)),)
