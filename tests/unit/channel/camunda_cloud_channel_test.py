from uuid import uuid4

import grpc
import pytest
import responses
from mock import Mock, patch
from requests import HTTPError

from pyzeebe import create_camunda_cloud_channel
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
def region() -> str:
    return str(uuid4())


@pytest.fixture
def url() -> str:
    return "https://login.cloud.camunda.io/oauth/token"


@pytest.fixture
def access_token() -> str:
    return str(uuid4())


@pytest.fixture
def mock_access_token_response(
    mocked_responses: responses.RequestsMock, url: str, access_token: str
):
    mocked_responses.add(
        responses.POST, url, json={"access_token": access_token}, status=200
    )


class TestCamundaCloudChannel:
    @pytest.fixture(autouse=True)
    def secure_channel_mock(self, aio_grpc_channel: grpc.aio.Channel) -> Mock:
        with patch("grpc.aio.secure_channel", return_value=aio_grpc_channel) as mock:
            yield mock

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_returns_grpc_channel(
        self,
        mocked_responses: responses.RequestsMock,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        channel = create_camunda_cloud_channel(client_id, client_secret, cluster_id)

        assert isinstance(channel, grpc.aio.Channel)

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_gets_access_token_from_camunda_cloud(
        self,
        mocked_responses: responses.RequestsMock,
        client_id: str,
        client_secret: str,
        cluster_id: str,
    ):
        create_camunda_cloud_channel(client_id, client_secret, cluster_id)

        assert len(mocked_responses.calls) == 1

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_gets_access_token_using_correct_parameters(
        self,
        mocked_responses: responses.RequestsMock,
        client_id: str,
        client_secret: str,
        cluster_id: str,
        region: str,
    ):
        expected_request_body = f"client_id={client_id}&client_secret={client_secret}&audience={cluster_id}.{region}.zeebe.camunda.io"

        create_camunda_cloud_channel(client_id, client_secret, cluster_id, region)

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
        mocked_responses.add(
            responses.POST, url, status=400
        )  # Camunda cloud returns 400 when invalid credentials are provided

        with pytest.raises(InvalidCamundaCloudCredentialsError):
            create_camunda_cloud_channel(client_id, client_secret, cluster_id)

    @pytest.mark.usefixtures("mock_access_token_response")
    def test_creates_channel_using_grpc_credentials(
        self,
        client_id: str,
        client_secret: str,
        cluster_id: str,
        secure_channel_mock: Mock,
    ):
        create_camunda_cloud_channel(client_id, client_secret, cluster_id)

        secure_channel_call = secure_channel_mock.mock_calls[0]
        arguments = [arg for arg in secure_channel_call.args]
        assert any(
            isinstance(arg, grpc.ChannelCredentials) for arg in arguments
        ), "None of the arguments to grpc.aio.create_secure_channel were of type grpc.ChannelCredentials"
