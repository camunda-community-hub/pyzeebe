import json
import logging
import time
import timeit
from typing import Optional

import grpc
from grpc._auth import _sign_request

from oauthlib import oauth2
from requests_oauthlib import OAuth2Session


logger = logging.getLogger(__name__)


class OAuth2ClientCredentials(grpc.AuthMetadataPlugin):
    """Metadata wrapper for OAuth2ClientCredentials for Authentication.

    https://oauth.net/2/grant-types/client-credentials/
    https://datatracker.ietf.org/doc/html/rfc6749#section-11.2.2
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_server: str,
        scope: Optional[str] = None,
        audience: Optional[str] = None,
        expire_in: Optional[int] = 0,
    ) -> None:
        """Metadata wrapper for OAuth2ClientCredentials for Authentication.

        Args:
            client_id (str): The client identifier issued to the client during
            the registration process.
            client_secret (str): The client secret.
            authorization_server (str): The server issuing access tokens
            to the client after successfully authenticating the resource owner
            and obtaining authorization.
            scope (Optional[str]): The Access Token Scope.
            audience (Optional[str]): The audience for the token.

            expire_in (Optional[int]): Only used if the token does not contain an "expires_in" attribute. The number of seconds the token is valid for.
        """
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._authorization_server: str = authorization_server
        self._scope: Optional[str] = scope
        self._audience: Optional[str] = audience

        self._expires_in: Optional[int] = expire_in

        client = oauth2.BackendApplicationClient(client_id=self._client_id, scope=self._scope)
        client.prepare_request_body(include_client_id=True)
        self._oauth = OAuth2Session(client=client)

        # NOTE: "expires_in" is only RECOMMENDED
        # https://datatracker.ietf.org/doc/html/rfc6749#section-5.1
        self._oauth.register_compliance_hook("access_token_response", self._no_expiration)

    def __call__(
        self,
        context: grpc.AuthMetadataContext,
        callback: grpc.AuthMetadataPluginCallback,
    ):
        start_time = timeit.default_timer()  # TODO: remove

        try:
            if self._oauth.authorized is False:
                self._get_access_token()

            # NOTE: "expires_at" is not part of the OAuth2 Standard, but very useful
            # https://datatracker.ietf.org/doc/html/rfc6749#appendix-A
            # https://oauthlib.readthedocs.io/en/latest/_modules/oauthlib/oauth2/rfc6749/clients/base.html?highlight=expires_at#
            elif self._oauth.token.get("expires_at", 0) - 10 <= time.time():  # FIXME: 10 seconds before expiration
                self._get_access_token()

        except Exception as exception:  # pylint: disable=broad-except
            _sign_request(callback, None, exception)

        else:
            _sign_request(callback, self._oauth.access_token, None)
            logger.debug(
                "Requesting OAuth2ClientCredentials took: %fs",
                timeit.default_timer() - start_time,
            )  # TODO: remove

            logger.debug(
                "Token will expire in: %is",
                (self._oauth.token.get("expires_at", 0) - time.time()),
            )

    def _get_access_token(self) -> None:
        """Get the access token from the authorization server."""

        try:
            self._oauth.fetch_token(
                token_url=self._authorization_server,
                client_secret=self._client_secret,
                audience=self._audience,
            )

        except oauth2.OAuth2Error as e:
            logger.error(str(e))
            raise e

    def _no_expiration(self, r):
        token = json.loads(r.text)

        if token.get("expires_in") is None:
            logger.warning("Token attribute expires_in not found.")
            token["expires_in"] = self._expires_in

        r._content = json.dumps(token).encode()
        return r
