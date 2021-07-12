from uuid import uuid4

import grpc
import pytest
import responses
from mock import Mock, patch
from requests import HTTPError

from pyzeebe import create_camunda_cloud_channel
from pyzeebe.channel.camunda_cloud_channel import (
    create_camunda_cloud_credentials, create_oauth_credentials,
    get_access_token)
from pyzeebe.errors import (InvalidCamundaCloudCredentialsError,
                            InvalidOAuthCredentialsError)


@pytest.fixture
def mocked_responses() -> responses.RequestsMock:
    with responses.RequestsMock() as response_mock:
        yield response_mock


@pytest.fixture
def client_id() -> str:
    return str(uuid4())


@pytest.fixture
def client_secret() -> str:
    return str(uuid4())


@pytest.fixture
def cluster_id() -> str:
    return str(uuid4())


@pytest.fixture
def url() -> str:
    return "https://login.cloud.camunda.io/oauth/token"


class TestCamundaCloudChannel:
    def test_returns_grpc_channel(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        mocked_responses.add(
            responses.POST, url, json={"access_token": str(uuid4())}, status=200
        )

        channel = create_camunda_cloud_channel(client_id, client_secret, cluster_id)

        assert isinstance(channel, grpc.aio.Channel)


class TestGetAccessToken:
    @pytest.fixture
    def post_request_mock(self):
        with patch("requests_oauthlib.OAuth2Session.post") as post_request_mock:
            yield post_request_mock

    def test_returns_expected_access_token(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        cluster_id,
    ):
        expected_access_token = str(uuid4())
        mocked_responses.add(
            responses.POST,
            url,
            json={"access_token": expected_access_token},
            status=200,
        )

        access_token = get_access_token(url, client_id, client_secret, cluster_id)

        assert access_token == expected_access_token

    def test_gets_token_using_correct_format(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        expected_request_body = (
            f"client_id={client_id}&client_secret={client_secret}&audience={cluster_id}"
        )
        mocked_responses.add(
            responses.POST, url, json={"access_token": str(uuid4())}, status=200
        )

        get_access_token(
            url,
            client_id,
            client_secret,
            cluster_id,
        )

        request = mocked_responses.calls[0].request
        assert request.body == expected_request_body

    def test_raises_on_invalid_credentials(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        mocked_responses.add(responses.POST, url, status=400)

        with pytest.raises(InvalidOAuthCredentialsError):
            get_access_token(url, client_id, client_secret, cluster_id)


class TestCreateCamundaCloudCredentials:
    def test_raises_on_invalid_credentials(
        self,
        mocked_responses: responses.RequestsMock,
        url: str,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        mocked_responses.add(responses.POST, url, status=400)

        with pytest.raises(InvalidCamundaCloudCredentialsError):
            create_camunda_cloud_credentials(client_id, client_secret, cluster_id)


class TestCreateOAuthCredentials:
    def test_returns_grpc_credentials(self):
        access_token = str(uuid4())

        credentials = create_oauth_credentials(access_token)

        assert isinstance(credentials, grpc.ChannelCredentials)
