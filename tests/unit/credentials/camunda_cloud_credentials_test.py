from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from pyzeebe.credentials.camunda_cloud_credentials import CamundaCloudCredentials
from pyzeebe.exceptions import InvalidOAuthCredentials, InvalidCamundaCloudCredentials


def test_init():
    client_id = str(uuid4())
    client_secret = str(uuid4())
    cluster_id = str(uuid4())

    with patch("pyzeebe.credentials.oauth_credentials.OAuthCredentials.__init__") as init:
        CamundaCloudCredentials(client_id, client_secret, cluster_id)
        init.assert_called_with(url=f"https://login.cloud.camunda.io/oauth/token", client_id=client_id,
                                client_secret=client_secret, audience=f"{cluster_id}.bru-2.zeebe.camunda.io")


def test_invalid_credentials():
    CamundaCloudCredentials.get_access_token = MagicMock(
        side_effect=InvalidOAuthCredentials(str(uuid4()), str(uuid4()), str(uuid4())))

    with pytest.raises(InvalidCamundaCloudCredentials):
        CamundaCloudCredentials(str(uuid4()), str(uuid4()), str(uuid4()))
