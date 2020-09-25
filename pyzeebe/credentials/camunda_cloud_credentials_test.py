from unittest.mock import patch
from uuid import uuid4

from pyzeebe.credentials.camunda_cloud_credentials import CamundaCloudCredentials


def test_init():
    client_id = str(uuid4())
    client_secret = str(uuid4())
    cluster_id = str(uuid4())

    with patch("pyzeebe.credentials.oauth_credentials.OAuthCredentials.__init__") as init:
        CamundaCloudCredentials(client_id, client_secret, cluster_id)
        init.assert_called_with(url=f"https://login.cloud.camunda.io/oauth/token", client_id=client_id,
                                client_secret=client_secret, audience=f"{cluster_id}.zeebe.camunda.io")
