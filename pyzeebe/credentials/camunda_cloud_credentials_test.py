from unittest.mock import patch
from uuid import uuid4

from pyzeebe.credentials.camunda_cloud_credentials import CamundaCloudCredentials


def test_get_access_token():
    with patch('requests_oauthlib.OAuth2Session.post') as post_mock:
        client_id = str(uuid4())
        client_secret = str(uuid4())
        cluster_id = str(uuid4())
        CamundaCloudCredentials.get_access_token(client_id, client_secret, cluster_id)
        post_mock.assert_called_with('https://login.cloud.camunda.io/oauth/token',
                                     data={
                                         'client_id': client_id,
                                         'client_secret': client_secret,
                                         'audience': f'{cluster_id}.zeebe.camunda.io'
                                     })
