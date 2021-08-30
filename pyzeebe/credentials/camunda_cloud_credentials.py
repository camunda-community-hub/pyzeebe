from pyzeebe.credentials.oauth_credentials import OAuthCredentials
from pyzeebe.exceptions import InvalidOAuthCredentials, InvalidCamundaCloudCredentials


class CamundaCloudCredentials(OAuthCredentials):
    def __init__(self, client_id: str, client_secret: str, cluster_id: str, region: str="bru-2"):
        try:
            super().__init__(url="https://login.cloud.camunda.io/oauth/token", client_id=client_id,
                             client_secret=client_secret, audience=f"{cluster_id}.{region}.zeebe.camunda.io")
        except InvalidOAuthCredentials:
            raise InvalidCamundaCloudCredentials(client_id=client_id, cluster_id=cluster_id)

    def get_connection_uri(self) -> str:
        return f"{self.audience}:443"
