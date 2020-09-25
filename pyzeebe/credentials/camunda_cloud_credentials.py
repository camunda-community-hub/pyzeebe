import grpc
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session

from pyzeebe.credentials.base_credentials import BaseCredentials


class CamundaCloudCredentials(BaseCredentials):
    def __init__(self, client_id: str, client_secret: str, cluster_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.cluster_id = cluster_id

        self.access_token = self.get_access_token(client_id, client_secret, cluster_id)
        token_credentials = grpc.access_token_call_credentials(self.access_token)
        ssl_credentials = grpc.ssl_channel_credentials()
        self.grpc_credentials = grpc.composite_channel_credentials(ssl_credentials, token_credentials)

    @staticmethod
    def get_access_token(client_id: str, client_secret: str, cluster_id: str) -> str:
        client = oauth2.BackendApplicationClient(client_id)
        client.prepare_request_body(include_client_id=True)
        session = OAuth2Session(client=client)

        return session.post('https://login.cloud.camunda.io/oauth/token',
                            data={
                                'client_id': client_id,
                                'client_secret': client_secret,
                                'audience': f'{cluster_id}.zeebe.camunda.io'
                            }).json()['access_token']

    def get_connection_uri(self) -> str:
        return f'{self.cluster_id}.zeebe.camunda.io:443'
