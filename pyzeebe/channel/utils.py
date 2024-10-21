from __future__ import annotations

import os

DEFAULT_ZEEBE_ADDRESS = "localhost:26500"


def get_zeebe_address(default_value: str | None = None) -> str:
    """
    Args:
        default_value (str, optional): Default value to be used if no other value was discovered.
    Returns: Value from ZEEBE_ADDRESS environment variable
            or provided default_value
            or "localhost:26500"
    """

    return os.getenv("ZEEBE_ADDRESS") or default_value or DEFAULT_ZEEBE_ADDRESS


def get_camunda_oauth_url(default_value: str | None = None) -> str:
    """
    Args:
        default_value (str, optional): Default value to be used if no other value was discovered.
    Returns: The camunda platform authorization server url.
            Default: Value from CAMUNDA_OAUTH_URL
                    or ZEEBE_AUTHORIZATION_SERVER_URL environment variable
                    or provided default_value
    """
    r = os.getenv("CAMUNDA_OAUTH_URL") or os.getenv("ZEEBE_AUTHORIZATION_SERVER_URL") or default_value

    if r is None:
        raise EnvironmentError("No CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL provided!")

    return r


def get_camunda_client_id() -> str:
    """
    Returns: The client id.
            Default: Value from CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable
    """
    r = os.getenv("CAMUNDA_CLIENT_ID") or os.getenv("ZEEBE_CLIENT_ID")

    if r is None:
        raise EnvironmentError("No CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID provided!")

    return r


def get_camunda_client_secret() -> str:
    """
    Returns:
        str: The client secret.
            Default: Value from CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable
    """

    r = os.getenv("CAMUNDA_CLIENT_SECRET") or os.getenv("ZEEBE_CLIENT_SECRET")

    if r is None:
        raise EnvironmentError("No CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET provided!")

    return r


def get_camunda_cluster_id() -> str:
    """
    Returns: The camunda cluster id.
            Default: Value from CAMUNDA_CLUSTER_ID environment variable
    """

    r = os.getenv("CAMUNDA_CLUSTER_ID")

    if r is None:
        raise EnvironmentError("No CAMUNDA_CLUSTER_ID provided!")

    return r


def get_camunda_cluster_region(default_value: str | None = None) -> str:
    """
    Args:
        default_value (str, optional): Default value to be used if no other value was discovered.
    Returns: The camunda cluster region.
            Default: Value from CAMUNDA_CLUSTER_REGION environment variable
    """

    r = os.getenv("CAMUNDA_CLUSTER_REGION") or default_value

    if r is None:
        raise EnvironmentError("No CAMUNDA_CLUSTER_REGION provided!")

    return r


def get_camunda_token_audience(default_value: str | None = None) -> str:
    """
    Args:
        default_value (str, optional): Default value to be used if no other value was discovered.
    Returns: The token audience.
            Default: Value from CAMUNDA_TOKEN_AUDIENCE
                     or ZEEBE_TOKEN_AUDIENCE environment variable
                     or provided default_value
    """
    r = os.getenv("CAMUNDA_TOKEN_AUDIENCE") or os.getenv("ZEEBE_TOKEN_AUDIENCE") or default_value

    if r is None:
        raise EnvironmentError("No CAMUNDA_TOKEN_AUDIENCE or ZEEBE_TOKEN_AUDIENCE provided!")

    return r


def get_camunda_address(cluster_id: str | None = None, cluster_region: str | None = None) -> str:
    """
    Args:
        cluster_id (str, optional): The camunda cluster id provided as parameter.
            Default: Value from CAMUNDA_CLUSTER_ID environment variable or None
        cluster_region (str, optional): The camunda cluster region provided as parameter.
            Default: Value from CAMUNDA_CLUSTER_REGION environment variable.
    Returns:
        str: The Camunda Cloud grpc server address.
    """

    if (cluster_id is None) or (cluster_region is None):
        raise EnvironmentError("The cluster_id and cluster_region must be provided!")

    # if (cluster_id is not None) and (cluster_region is not None):  # and
    return f"{cluster_id}.{cluster_region}.zeebe.camunda.io:443"
