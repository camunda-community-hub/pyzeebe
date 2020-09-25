import grpc
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session

from pyzeebe.credentials.base_credentials import BaseCredentials


class OAuthCredentials(BaseCredentials):
    def __init__(self, url: str, client_id: str, client_secret: str, audience: str):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience

        self.access_token = self.get_access_token(url, client_id, client_secret, audience)
        token_credentials = grpc.access_token_call_credentials(self.access_token)
        ssl_credentials = grpc.ssl_channel_credentials()
        self.grpc_credentials = grpc.composite_channel_credentials(ssl_credentials, token_credentials)

    @staticmethod
    def get_access_token(url: str, client_id: str, client_secret: str, audience: str) -> str:
        client = oauth2.BackendApplicationClient(client_id)
        client.prepare_request_body(include_client_id=True)
        session = OAuth2Session(client=client)

        return session.post(url,
                            data={
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "audience": audience
                            }).json()["access_token"]

    def get_connection_uri(self) -> str:
        return None
