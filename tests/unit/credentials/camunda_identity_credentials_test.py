from unittest.mock import Mock
from uuid import uuid4

import pytest
import responses

from pyzeebe import CamundaIdentityCredentials
from pyzeebe.errors import InvalidOAuthCredentialsError


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as response_mock:
        yield response_mock


@pytest.fixture
def client_id() -> str:
    return str(uuid4())


@pytest.fixture
def client_secret() -> str:
    return str(uuid4())


@pytest.fixture
def url() -> str:
    return "https://login.cloud.camunda.io/oauth/token"


@pytest.fixture
def access_token() -> str:
    return str(uuid4())


@pytest.fixture
def mock_access_token_response(mocked_responses: responses.RequestsMock, url: str, access_token: str):
    mocked_responses.add(responses.POST, url, json={"access_token": access_token, "expires_in": 30}, status=200)


class TestCamundaIdentityCredentials:
    @pytest.mark.usefixtures("mock_access_token_response")
    def test_gets_access_token(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        access_token: str,
    ):
        credentials = CamundaIdentityCredentials(oauth_url=url, client_id=client_id, client_secret=client_secret)

        assert credentials.get_auth_metadata(Mock()) == (("authorization", f"Bearer {access_token}"),)

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_gets_access_token_using_correct_parameters(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
    ):
        expected_request_body = (
            f"client_id={client_id}&client_secret={client_secret}&audience=zeebe-api&grant_type=client_credentials"
        )

        credentials = CamundaIdentityCredentials(oauth_url=url, client_id=client_id, client_secret=client_secret)
        credentials.get_auth_metadata(Mock())

        request = mocked_responses.calls[0].request
        assert request.url == url
        assert request.body == expected_request_body

    def test_raises_on_invalid_credentials(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
    ):
        mocked_responses.add(responses.POST, url, status=400)
        credentials = CamundaIdentityCredentials(oauth_url=url, client_id=client_id, client_secret=client_secret)

        with pytest.raises(InvalidOAuthCredentialsError):
            credentials.get_auth_metadata(Mock())

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_gets_access_token_use_cache(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        access_token: str,
    ):
        credentials = CamundaIdentityCredentials(oauth_url=url, client_id=client_id, client_secret=client_secret)

        assert credentials.get_auth_metadata(Mock()) == (("authorization", f"Bearer {access_token}"),)
        assert credentials.get_auth_metadata(Mock()) == (("authorization", f"Bearer {access_token}"),)
        assert mocked_responses.assert_call_count(url, 1)

    def test_gets_access_token_refresh_threshold(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
    ):
        mocked_responses.add(responses.POST, url, json={"access_token": "test1", "expires_in": 9}, status=200)
        mocked_responses.add(responses.POST, url, json={"access_token": "test2", "expires_in": 9}, status=200)
        credentials = CamundaIdentityCredentials(
            oauth_url=url, client_id=client_id, client_secret=client_secret, refresh_threshold_seconds=10
        )

        assert credentials.get_auth_metadata(Mock()) == (("authorization", "Bearer test1"),)
        assert credentials.get_auth_metadata(Mock()) == (("authorization", "Bearer test2"),)
        assert mocked_responses.assert_call_count(url, 2)
