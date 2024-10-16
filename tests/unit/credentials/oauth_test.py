import json
import time
from functools import partial
from typing import Callable
from unittest import mock
from unittest.mock import MagicMock, PropertyMock
from uuid import uuid4

import pytest
from oauthlib import oauth2
from oauthlib.oauth2 import OAuth2Error
from requests import Response
from requests_oauthlib import OAuth2Session

from pyzeebe.credentials.oauth import (
    Oauth2ClientCredentialsMetadataPlugin,
    OAuth2MetadataPlugin,
)
from pyzeebe.errors.credentials_errors import InvalidOAuthCredentialsError


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
            "scope": ["test_scope_a", "test_scope_b"],
        }
    )


@pytest.fixture
def client_id():
    return "test_id"


@pytest.fixture
def client_secret():
    return "test_secret"


@pytest.fixture
def token_url():
    return "https://auth.server"


@pytest.fixture
def scope():
    return "test_scope_a test_scope_b"


@pytest.fixture
def audience():
    return "test_audience"


@pytest.fixture
def oauth2_client(client_id, scope):
    return oauth2.BackendApplicationClient(client_id=client_id, scope=scope)


@pytest.fixture()
def oauth2session(oauth2_client):
    return OAuth2Session(client=oauth2_client)


@pytest.fixture()
def func(oauth2session, token_url, client_secret, audience):
    return partial(
        oauth2session.fetch_token,
        token_url=token_url,
        client_secret=client_secret,
        audience=audience,
    )


class TestOAuth2MetadataPlugin:

    @pytest.fixture(autouse=True)
    def oauth2mp(self, oauth2session, func):
        return OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=func,
        )

    # Test OAuth2Session Initialization
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session")
    def test_oauth2_session_initialization(self, mock_oauth2_session):
        isinstance(mock_oauth2_session, oauth2.BackendApplicationClient)

    def test_initialization(self, oauth2mp: OAuth2MetadataPlugin):
        assert isinstance(oauth2mp._oauth, OAuth2Session)
        assert isinstance(oauth2mp._func_retrieve_token, partial)
        assert isinstance(oauth2mp._func_retrieve_token, Callable)

        assert oauth2mp._oauth.client_id == "test_id"
        assert oauth2mp._oauth.scope == "test_scope_a test_scope_b"
        assert oauth2mp._leeway == 60

        assert oauth2mp._func_retrieve_token.keywords["token_url"] == "https://auth.server"
        assert oauth2mp._func_retrieve_token.keywords["client_secret"] == "test_secret"
        assert oauth2mp._func_retrieve_token.keywords["audience"] == "test_audience"

    @pytest.mark.parametrize(
        "authorized, token, is_expired",
        [
            (True, {"expires_at": time.time() + 300}, False),
            (True, {"expires_at": time.time()}, True),
            (False, {"expires_at": time.time() + 300}, True),
            (False, {"expires_at": time.time()}, True),
        ],
    )
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.authorized", new_callable=PropertyMock)
    def test_is_token_expired(self, mock_authorized, authorized, token, is_expired, oauth2mp):
        mock_authorized.return_value = authorized

        oauth2mp._oauth.token = token
        assert oauth2mp.is_token_expired() is is_expired

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
        oauth2mp: OAuth2MetadataPlugin,
        mock_response,
        token,
        authorized,
    ):

        mock_authorized.return_value = authorized

        mock_request.return_value = mock_response
        oauth2mp._oauth.request = mock_request

        mock_context = MagicMock()
        mock_callback = MagicMock()
        oauth2mp.__call__(mock_context, mock_callback)

        mock_request.assert_called_once()
        assert oauth2mp._oauth.authorized is authorized

        t = oauth2mp._oauth.token
        del t["expires_at"]  # NOTE: We don't care about the expiration time
        assert t == token

    @pytest.fixture()
    def oauth2mp_mock_func(self, oauth2session, mock_func):

        return OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=mock_func,
        )

    # Test Fetching Token
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.fetch_token")
    def test_fetch_token(self, mock_fetch_token, oauth2session: OAuth2Session):

        func = partial(
            mock_fetch_token,
            token_url="https://auth.server",
            client_secret="test_secret",
            audience="test_audience",
        )

        oauth2mp = OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=func,
        )

        mock_context = MagicMock()
        mock_callback = MagicMock()
        oauth2mp.__call__(mock_context, mock_callback)

        mock_fetch_token.assert_called_once_with(
            token_url="https://auth.server",
            client_secret="test_secret",
            audience="test_audience",
        )

    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.fetch_token", side_effect=OAuth2Error("Error fetching token"))
    def test_authorized_error(
        self,
        mock_fetch_token,
        oauth2session: OAuth2Session,
    ):

        func = partial(
            mock_fetch_token,
            token_url="https://auth.server",
            client_secret="test_secret",
            audience="test_audience",
        )

        oauth2mp = OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=func,
        )

        mock_context = MagicMock()
        mock_callback = MagicMock()

        oauth2mp.__call__(mock_context, mock_callback)

        with pytest.raises(InvalidOAuthCredentialsError, match="Error fetching token"):
            oauth2mp.retrieve_token()


class TestOAuth2MetadataPluginExpireIn:

    # NOTE: Following tests in scenario where "expires_in" is not available in the OAuth2ClientCredentials Token
    @pytest.fixture(autouse=True)
    def oauth2mp_expire_in(self, oauth2session, func):

        return OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=func,
            expire_in=3600,
        )

    def test_initialization(self, oauth2mp_expire_in: OAuth2MetadataPlugin):

        assert isinstance(oauth2mp_expire_in._oauth, OAuth2Session)
        assert isinstance(oauth2mp_expire_in._func_retrieve_token, partial)
        assert isinstance(oauth2mp_expire_in._func_retrieve_token, Callable)

        assert oauth2mp_expire_in._oauth.client_id == "test_id"
        assert oauth2mp_expire_in._oauth.scope == "test_scope_a test_scope_b"
        assert oauth2mp_expire_in._expires_in == 3600

        assert oauth2mp_expire_in._func_retrieve_token.keywords["token_url"] == "https://auth.server"
        assert oauth2mp_expire_in._func_retrieve_token.keywords["client_secret"] == "test_secret"
        assert oauth2mp_expire_in._func_retrieve_token.keywords["audience"] == "test_audience"

    @mock.patch("pyzeebe.credentials.oauth.json.dumps")
    def test_no_expiration(self, mock_dumps, oauth2mp_expire_in: OAuth2MetadataPlugin):
        mock_response = mock.MagicMock(Response)
        mock_response.json.return_value = {}
        oauth2mp_expire_in._no_expiration(mock_response)
        mock_dumps.assert_called_once_with({"expires_in": 3600})

    @pytest.fixture
    def token_without_expire_in(self, token) -> dict:
        t = token
        del t["expires_in"]
        return t

    @mock.patch("pyzeebe.credentials.oauth.json.dumps")
    def test_no_expiration_with_token(
        self,
        mock_dumps,
        token,
        token_without_expire_in,
        oauth2mp_expire_in: OAuth2MetadataPlugin,
    ):
        mock_response = mock.MagicMock(Response)
        mock_response.json.return_value = token_without_expire_in
        oauth2mp_expire_in._no_expiration(mock_response)
        mock_dumps.assert_called_once_with(token)


class TestOAuth2MetadataPluginLeeway:

    # NOTE: Following tests in scenario where "leeway" needs to be considered
    @pytest.fixture(autouse=True)
    def oauth2mp_leeway(self, oauth2session, func):

        return OAuth2MetadataPlugin(
            oauth2session=oauth2session,
            func_retrieve_token=func,
            leeway=30,
        )

    def test_initialization(self, oauth2mp_leeway: OAuth2MetadataPlugin):

        assert isinstance(oauth2mp_leeway._oauth, OAuth2Session)
        assert isinstance(oauth2mp_leeway._func_retrieve_token, partial)
        assert isinstance(oauth2mp_leeway._func_retrieve_token, Callable)

        assert oauth2mp_leeway._oauth.client_id == "test_id"
        assert oauth2mp_leeway._oauth.scope == "test_scope_a test_scope_b"
        assert oauth2mp_leeway._leeway == 30

        assert oauth2mp_leeway._func_retrieve_token.keywords["token_url"] == "https://auth.server"
        assert oauth2mp_leeway._func_retrieve_token.keywords["client_secret"] == "test_secret"
        assert oauth2mp_leeway._func_retrieve_token.keywords["audience"] == "test_audience"

    @pytest.mark.parametrize(
        "authorized, token, is_expired",
        [
            (True, {"expires_at": time.time() + 300}, False),
            (True, {"expires_at": time.time() + 30}, True),  # NOTE: leeway is 30
            (True, {"expires_at": time.time()}, True),
            (False, {"expires_at": time.time() + 300}, True),
            (False, {"expires_at": time.time() + 30}, True),  # NOTE: leeway is 30
            (False, {"expires_at": time.time()}, True),
        ],
    )
    @mock.patch("pyzeebe.credentials.oauth.OAuth2Session.authorized", new_callable=PropertyMock)
    def test_is_token_expired(self, mock_authorized, authorized, token, is_expired, oauth2mp_leeway):
        mock_authorized.return_value = authorized

        oauth2mp_leeway._oauth.token = token
        assert oauth2mp_leeway.is_token_expired() is is_expired


class TestOauth2ClientCredentialsMetadataPlugin:

    @pytest.fixture(autouse=True)
    def oauth2ccmp(self, client_id, client_secret, token_url, scope, audience):

        return Oauth2ClientCredentialsMetadataPlugin(
            client_id=client_id,
            client_secret=client_secret,
            authorization_server=token_url,
            scope=scope,
            audience=audience,
        )

    def test_initialization(self, oauth2ccmp: Oauth2ClientCredentialsMetadataPlugin):
        assert isinstance(oauth2ccmp._oauth, OAuth2Session)
        assert isinstance(oauth2ccmp._func_retrieve_token, partial)
        assert isinstance(oauth2ccmp._func_retrieve_token, Callable)

        assert oauth2ccmp._oauth.client_id == "test_id"
        assert oauth2ccmp._oauth.scope == "test_scope_a test_scope_b"

        assert oauth2ccmp._func_retrieve_token.keywords["token_url"] == "https://auth.server"
        assert oauth2ccmp._func_retrieve_token.keywords["client_secret"] == "test_secret"
        assert oauth2ccmp._func_retrieve_token.keywords["audience"] == "test_audience"
