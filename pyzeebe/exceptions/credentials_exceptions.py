from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class InvalidOAuthCredentials(PyZeebeException):
    def __init__(self, url: str, client_id: str, audience: str):
        super().__init__(
            f"Invalid OAuth credentials supplied for {url} with audience {audience} and client id {client_id}")


class InvalidCamundaCloudCredentials(PyZeebeException):
    def __init__(self, client_id: str, cluster_id: str):
        super().__init__(f"Invalid credentials supplied for cluster {cluster_id} with client {client_id}")
