from __future__ import annotations

import json
import logging
import time
import timeit
from functools import partial
from typing import Any

import grpc
import requests
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


def _sign_request(
    callback: grpc.AuthMetadataPluginCallback,
    token: str | None,
    error: Exception | None,
) -> None:
    metadata = (("authorization", f"Bearer {token}"),)
    callback(metadata, error)


class OAuth2MetadataPlugin(grpc.AuthMetadataPlugin):  # type: ignore[misc]
    """AuthMetadataPlugin for OAuth2 Authentication.

    Implements the AuthMetadataPlugin interface for OAuth2 Authentication based on oauthlib and requests_oauthlib.

    https://datatracker.ietf.org/doc/html/rfc6749
    https://oauthlib.readthedocs.io/en/latest/oauth2/oauth2.html
    https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html
    """

    def __init__(
        self,
        oauth2session: OAuth2Session,
        func_retrieve_token: partial[dict[str, Any]],
        leeway: int = 60,
        expire_in: int | None = None,
    ) -> None:
        """AuthMetadataPlugin for OAuth2 Authentication.

        Args:
            oauth2session (OAuth2Session): The OAuth2Session object.
            func_fetch_token (Callable): The function to fetch the token.

            leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
                Defaults to 60.
            expire_in (Optional[int]): The number of seconds the token is valid for.
                Defaults to None.
                Should only be used if the token does not contain an "expires_in" attribute.
        """
        self._oauth: OAuth2Session = oauth2session
        self._func_retrieve_token: partial[dict[str, Any]] = func_retrieve_token

        self._leeway: int = leeway
        self._expires_in: int | None = expire_in
        if self._expires_in is not None:
            # NOTE: "expires_in" is only RECOMMENDED
            # https://datatracker.ietf.org/doc/html/rfc6749#section-5.1
            self._oauth.register_compliance_hook("access_token_response", self._no_expiration)

    def __call__(
        self,
        context: grpc.AuthMetadataContext,
        callback: grpc.AuthMetadataPluginCallback,
    ) -> None:
        start_time = timeit.default_timer()

        try:
            if self.is_token_expired():
                self.retrieve_token()

        except Exception as exception:  # pylint: disable=broad-except
            _sign_request(callback, None, exception)

        else:
            _sign_request(callback, self._oauth.access_token, None)
            logger.debug(
                "Requesting OAuth2 took: %fs",
                timeit.default_timer() - start_time,
            )

            logger.debug(
                "Token will expire in: %is",
                (self._oauth.token.get("expires_at", 0) - time.time()),
            )

    def is_token_expired(self) -> bool:
        """Check if the token is still valid."""
        if not self._oauth.authorized:
            return True

        # NOTE: "expires_at" is not part of the OAuth2 Standard, but very useful
        # https://datatracker.ietf.org/doc/html/rfc6749#appendix-A
        # https://oauthlib.readthedocs.io/en/latest/_modules/oauthlib/oauth2/rfc6749/clients/base.html?highlight=expires_at#
        expires_at = self._oauth.token.get("expires_at", 0)
        if time.time() > (expires_at - self._leeway):
            return True

        return False

    def retrieve_token(self) -> None:
        """Retrieve the access token from the authorization server."""

        try:
            self._func_retrieve_token()

        except oauth2.OAuth2Error as e:
            logger.exception(str(e))
            raise e

    def _no_expiration(self, r: requests.Response) -> requests.Response:
        """
        Sets the expiration time for the token if it is not provided in the response.

        Args:
            r (requests.Response): The response object containing the token.

        Returns:
            requests.Response: The modified response object with the updated token.
        """
        token = r.json()

        if token.get("expires_in") is None:
            logger.warning("Token attribute expires_in not found.")
            token["expires_in"] = self._expires_in

        r._content = json.dumps(token).encode()
        return r


class Oauth2ClientCredentialsMetadataPlugin(OAuth2MetadataPlugin):
    """AuthMetadataPlugin for OAuth2 Client Credentials Authentication based on Oauth2MetadataPlugin.

    https://oauth.net/2/grant-types/client-credentials/
    https://datatracker.ietf.org/doc/html/rfc6749#section-11.2.2
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_server: str,
        scope: str | None = None,
        audience: str | None = None,
        leeway: int = 60,
        expire_in: int | None = None,
    ):
        """AuthMetadataPlugin for OAuth2 Client Credentials Authentication based on Oauth2MetadataPlugin.

        Args:
            client_id (str): The client id.
            client_secret (str): The client secret.
            authorization_server (str): The authorization server issuing access tokens
                to the client after successfully authenticating the client.
            scope (Optional[str]): The scope of the access request. Defaults to None.
            audience (Optional[str]): The audience for authentication. Defaults to None.

            leeway (int): The number of seconds to consider the token as expired before the actual expiration time.
                Defaults to 60.
            expire_in (Optional[int]): The number of seconds the token is valid for.
                Defaults to None.
                Should only be used if the token does not contain an "expires_in" attribute.
        """

        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.authorization_server: str = authorization_server
        self.scope: str | None = scope
        self.audience: str | None = audience
        self.leeway: int = leeway
        self.expire_in: int | None = expire_in

        client = oauth2.BackendApplicationClient(client_id=self.client_id, scope=self.scope)
        oauth2session = OAuth2Session(client=client)

        func = partial(
            oauth2session.fetch_token,
            token_url=self.authorization_server,
            client_secret=self.client_secret,
            audience=self.audience,
        )

        super().__init__(
            oauth2session=oauth2session, func_retrieve_token=func, leeway=self.leeway, expire_in=self.expire_in
        )
