from __future__ import annotations

import os

DEFAULT_ZEEBE_ADDRESS = "localhost:26500"


def get_zeebe_address(grpc_address: str | None = None) -> str:
    """
    Args:
        grpc_address (str, optional): zeebe grpc server address.

    Returns:
        str: The zeebe grpc server address.
            Default: Value from ZEEBE_ADDRESS environment variable
                    or "{CAMUNDA_CLUSTER_ID}.{CAMUNDA_CLUSTER_REGION}.zeebe.camunda.io"
                    or "localhost:26500"
    """

    if grpc_address:
        return grpc_address

    camunda_cloud_address = None
    camunda_cloud_hostname = get_camunda_cloud_hostname(None, None)

    if camunda_cloud_hostname:
        camunda_cloud_address = f"{camunda_cloud_hostname}:443"

    return os.getenv("ZEEBE_ADDRESS", camunda_cloud_address or DEFAULT_ZEEBE_ADDRESS)


def get_camunda_oauth_url(oauth_url: str | None) -> str | None:
    """
    Args:
        oauth_url (str, optional): The camunda platform authorization server url provided as parameter.

    Returns:
        str: The camunda platform authorization server url.
            Default: Value from CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
    """
    return oauth_url or os.getenv("CAMUNDA_OAUTH_URL", os.getenv("ZEEBE_AUTHORIZATION_SERVER_URL"))


def get_camunda_client_id(client_id: str | None) -> str:
    """
    Args:
        client_id (str, optional): The client id provided as parameter.

    Returns:
        str: The client id.
            Default: Value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable
    """
    ret = client_id or os.getenv("CAMUNDA_CLIENT_ID", os.getenv("ZEEBE_CLIENT_ID"))

    if not ret:
        raise ValueError(
            "parameter client_id or one of the environment variables CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID must be provided!"
        )

    return ret


def get_camunda_client_secret(client_secret: str | None) -> str:
    """
    Args:
        client_secret (str, optional): The client secret provided as parameter.

    Returns:
        str: The client secret.
            Default: Value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable
    """
    ret = client_secret or os.getenv("CAMUNDA_CLIENT_SECRET") or os.getenv("ZEEBE_CLIENT_SECRET")

    if not ret:
        raise ValueError(
            "parameter client_secret or one of the environment variables CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET must be provided!"
        )

    return ret


def get_camunda_cluster_id(cluster_id: str | None) -> str | None:
    """
    Args:
        cluster_id (str, optional): The camunda cluster id provided as parameter.

    Returns:
        str: The camunda cluster id.
            Default: Value from CAMUNDA_CLUSTER_ID environment variable
    """

    return cluster_id or os.getenv("CAMUNDA_CLUSTER_ID")


def get_camunda_cluster_region(cluster_region: str | None) -> str:
    """
    Args:
        cluster_region (str, optional): The camunda cluster region provided as parameter.

    Returns:
        str: The camunda cluster region.
            Default: Value from CAMUNDA_CLUSTER_REGION environment variable or 'bru-2'
    """

    return cluster_region or os.getenv("CAMUNDA_CLUSTER_REGION") or "bru-2"


def get_camunda_token_audience(token_audience: str | None) -> str | None:
    """
    Args:
        token_audience (str, optional): The token audience provided as parameter.

    Returns:
        str: The token audience.
            Default: Value from CAMUNDA_TOKEN_AUDIENCE
                     or ZEEBE_TOKEN_AUDIENCE environment variable
                     or camunda cloud token audience if camunda cluster_id is available
    """

    return (
        token_audience
        or os.getenv("CAMUNDA_TOKEN_AUDIENCE")
        or os.getenv("ZEEBE_TOKEN_AUDIENCE")
        or get_camunda_cloud_hostname(None, None)
    )


def get_camunda_cloud_hostname(cluster_id: str | None, cluster_region: str | None) -> str | None:
    """
    Args:
        cluster_id (str, optional): The camunda cluster id provided as parameter.
        cluster_region (str, optional): The camunda cluster region provided as parameter.

    Returns:
        str: The token audience for camunda cloud or none if cluster_id or cluster_region is not provided.
    """

    cluster_id = get_camunda_cluster_id(cluster_id)
    cluster_region = get_camunda_cluster_region(cluster_region)

    if (not cluster_id) or (not cluster_region):
        return None

    return f"{cluster_id}.{cluster_region}.zeebe.camunda.io"
