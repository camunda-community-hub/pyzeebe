import json
import re
import time
from typing import Any
from unittest import TestCase, mock, removeResult
from unittest.mock import MagicMock, Mock, PropertyMock, patch
from urllib import request
from uuid import uuid4

import pytest
import pytest_asyncio
from oauthlib import oauth2
from oauthlib.oauth2 import OAuth2Error
from requests import Response
from requests_oauthlib import OAuth2Session

from pyzeebe.credentials.oauth import OAuth2ClientCredentials


@pytest.fixture
def access_token():
    return str(uuid4())


@pytest.fixture
def token(access_token) -> dict:
    return dict(
        {
            "access_token": access_token,
            "expires_in": 3600,
            "refresh_expires_in": 0,
            "token_type": "Bearer",
            "not-before-policy": 0,
            "scope": ["test_scope"],
        }
    )


class TestOauth2ClientCredentials:

    @pytest.fixture(autouse=True)
    def oauth_client_credentials(self):

        return OAuth2ClientCredentials(
            client_id="test_id",
            client_secret="test_secret",
            authorization_server="https://auth.server",
            scope="test_scope",
            audience="test_audience",
        )

    def test_initialization(self, oauth_client_credentials: OAuth2ClientCredentials):
        assert oauth_client_credentials._client_id == "test_id"
        assert oauth_client_credentials._client_secret == "test_secret"
        assert oauth_client_credentials._authorization_server == "https://auth.server"
        assert oauth_client_credentials._scope == "test_scope"
        assert oauth_client_credentials._audience == "test_audience"

    # Test OAuth2Session Initialization
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session")
    def test_oauth2_session_initialization(self, mock_oauth2_session):
        isinstance(mock_oauth2_session, oauth2.BackendApplicationClient)

    @pytest.fixture()
    def mock_response(self, token):
        response = mock.Mock(spec=Response)
        type(response).text = PropertyMock(return_value=json.dumps(token))
        response.status_code = 200

        response.request = MagicMock()
        response.headers = MagicMock()
        return response

    @pytest.mark.parametrize("authorized", [False, True])
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.authorized", new_callable=PropertyMock)
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.request")
    def test_authorized(
        self,
        mock_request,
        mock_authorized,
        oauth_client_credentials: OAuth2ClientCredentials,
        mock_response,
        token,
        authorized,
    ):

        mock_authorized.return_value = authorized

        mock_request.return_value = mock_response
        oauth_client_credentials._oauth.request = mock_request

        mock_context = MagicMock()
        mock_callback = MagicMock()
        oauth_client_credentials.__call__(mock_context, mock_callback)

        mock_request.assert_called_once()
        assert oauth_client_credentials._oauth.authorized is authorized

        t = oauth_client_credentials._oauth.token
        del t["expires_at"]  # NOTE: We don't care about the expiration time
        assert t == token

    # Test Fetching Token
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.fetch_token")
    def test_fetch_token(self, mock_fetch_token, oauth_client_credentials: OAuth2ClientCredentials, token):

        # Call method to fetch  token and assert the returned token matches mock_token
        # Verify correct parameters were passed to fetch_token
        mock_context = MagicMock()
        mock_callback = MagicMock()
        oauth_client_credentials.__call__(mock_context, mock_callback)

        mock_fetch_token.assert_called_once_with(
            token_url=oauth_client_credentials._authorization_server,
            client_secret=oauth_client_credentials._client_secret,
            audience=oauth_client_credentials._audience,
        )


class TestOauth2ClientCredentialsExpireIn:

    # NOTE: Following tests in scenario where "expires_in" is not available in the OAuth2ClientCredentials Token
    @pytest.fixture(autouse=True, scope="class")
    def oauth_client_credentials_expire_in(self):
        # This fixture now returns an instance of OAuth2ClientCredentials
        return OAuth2ClientCredentials(
            client_id="test_id",
            client_secret="test_secret",
            authorization_server="https://auth.server",
            scope="test_scope",
            audience="test_audience",
            expire_in=3600,
        )

    def test_initialization_expire_in(self, oauth_client_credentials_expire_in: OAuth2ClientCredentials):
        assert oauth_client_credentials_expire_in._client_id == "test_id"
        assert oauth_client_credentials_expire_in._client_secret == "test_secret"
        assert oauth_client_credentials_expire_in._authorization_server == "https://auth.server"
        assert oauth_client_credentials_expire_in._scope == "test_scope"
        assert oauth_client_credentials_expire_in._audience == "test_audience"
        assert oauth_client_credentials_expire_in._expires_in == 3600

    @mock.patch("pyzeebe.credentials.oauth.json.loads")
    @mock.patch("pyzeebe.credentials.oauth.json.dumps")
    def test_no_expiration(self, mock_dumps, mock_loads, oauth_client_credentials_expire_in: OAuth2ClientCredentials):
        mock_response = mock.MagicMock()
        mock_response.text = "{}"
        mock_loads.return_value = {}
        oauth_client_credentials_expire_in._no_expiration(mock_response)
        mock_dumps.assert_called_once_with({"expires_in": 3600})

    @pytest.fixture
    def token_without_expire_in(self, token) -> dict:
        t = token
        del t["expires_in"]
        return t

    @pytest.fixture
    def token_without_expire_in_string(self, token_without_expire_in) -> str:
        return json.dumps(token_without_expire_in)

    @mock.patch("pyzeebe.credentials.oauth.json.loads")
    @mock.patch("pyzeebe.credentials.oauth.json.dumps")
    def test_no_expiration_with_token(
        self,
        mock_dumps,
        mock_loads,
        token,
        token_without_expire_in,
        token_without_expire_in_string,
        oauth_client_credentials_expire_in: OAuth2ClientCredentials,
    ):
        mock_response = mock.MagicMock()
        mock_response.text = token_without_expire_in_string
        mock_loads.return_value = token_without_expire_in
        oauth_client_credentials_expire_in._no_expiration(mock_response)
        mock_dumps.assert_called_once_with(token)
