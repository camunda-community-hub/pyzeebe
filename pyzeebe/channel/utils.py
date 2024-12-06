from __future__ import annotations

import os

from pyzeebe.errors import SettingsError

DEFAULT_ZEEBE_ADDRESS = "localhost:26500"


def get_zeebe_address(default: str | None = None) -> str:
    """
    Get the Zeebe Gateway Address.

    Args:
        default (str, optional): Default value to be used if no other value was discovered.

    Returns:
        str: ZEEBE_ADDRESS environment variable or provided default or "localhost:26500"
    """
    return os.getenv("ZEEBE_ADDRESS") or default or DEFAULT_ZEEBE_ADDRESS


def get_camunda_oauth_url(default: str | None = None) -> str:
    """
    Get the Camunda OAuth URL or Zeebe Authorization Server URL.

    Args:
        default (str, optional): Default value to be used if no other value was discovered.

    Returns:
        str: CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL environment variable or provided default

    Raises:
        SettingsError: If neither CAMUNDA_OAUTH_URL nor ZEEBE_AUTHORIZATION_SERVER_URL is provided.
    """
    r = os.getenv("CAMUNDA_OAUTH_URL") or os.getenv("ZEEBE_AUTHORIZATION_SERVER_URL") or default

    if r is None:
        raise SettingsError("No CAMUNDA_OAUTH_URL or ZEEBE_AUTHORIZATION_SERVER_URL provided!")

    return r


def get_camunda_client_id() -> str:
    """
    Get the Camunda Client ID.

    Returns:
        str: CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID environment variable

    Raises:
        SettingsError: If neither CAMUNDA_CLIENT_ID nor ZEEBE_CLIENT_ID is provided.
    """
    r = os.getenv("CAMUNDA_CLIENT_ID") or os.getenv("ZEEBE_CLIENT_ID")

    if r is None:
        raise SettingsError("No CAMUNDA_CLIENT_ID or ZEEBE_CLIENT_ID provided!")

    return r


def get_camunda_client_secret() -> str:
    """
    Get the Camunda Client Secret.

    Returns:
        str: CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET environment variable

    Raises:
        SettingsError: If neither CAMUNDA_CLIENT_SECRET nor ZEEBE_CLIENT_SECRET is provided.
    """
    r = os.getenv("CAMUNDA_CLIENT_SECRET") or os.getenv("ZEEBE_CLIENT_SECRET")

    if r is None:
        raise SettingsError("No CAMUNDA_CLIENT_SECRET or ZEEBE_CLIENT_SECRET provided!")

    return r


def get_camunda_cluster_id() -> str:
    """
    Get the Camunda Cluster ID.

    Returns:
        str: CAMUNDA_CLUSTER_ID environment variable

    Raises:
        SettingsError: If CAMUNDA_CLUSTER_ID is not provided.
    """
    r = os.getenv("CAMUNDA_CLUSTER_ID")

    if r is None:
        raise SettingsError("No CAMUNDA_CLUSTER_ID provided!")

    return r


def get_camunda_cluster_region(default: str | None = None) -> str:
    """
    Get the Camunda Cluster Region.

    Args:
        default (str, optional): Default value to be used if no other value was discovered.

    Returns:
        str: CAMUNDA_CLUSTER_REGION environment variable or provided default

    Raises:
        SettingsError: If CAMUNDA_CLUSTER_REGION is not provided.
    """
    r = os.getenv("CAMUNDA_CLUSTER_REGION") or default

    if r is None:
        raise SettingsError("No CAMUNDA_CLUSTER_REGION provided!")

    return r


def get_camunda_token_audience(default: str | None = None) -> str:
    """
    Get the Camunda Token Audience.

    Args:
        default (str, optional): Default value to be used if no other value was discovered.

    Returns:
        str: CAMUNDA_TOKEN_AUDIENCE or ZEEBE_TOKEN_AUDIENCE environment variable or provided default

    Raises:
        SettingsError: If neither CAMUNDA_TOKEN_AUDIENCE nor ZEEBE_TOKEN_AUDIENCE is provided.
    """
    r = os.getenv("CAMUNDA_TOKEN_AUDIENCE") or os.getenv("ZEEBE_TOKEN_AUDIENCE") or default

    if r is None:
        raise SettingsError("No CAMUNDA_TOKEN_AUDIENCE or ZEEBE_TOKEN_AUDIENCE provided!")

    return r


def get_camunda_address(cluster_id: str | None = None, cluster_region: str | None = None) -> str:
    """
    Get the Camunda Cloud gRPC server address.

    Args:
        cluster_id (str, optional): The Camunda cluster ID provided as parameter.
        cluster_region (str, optional): The Camunda cluster region provided as parameter.

    Returns:
        str: The Camunda Cloud gRPC server address.

    Raises:
        SettingsError: If either cluster_id or cluster_region is not provided.
    """
    if (cluster_id is None) or (cluster_region is None):
        raise SettingsError("The cluster_id and cluster_region must be provided!")

    return f"{cluster_id}.{cluster_region}.zeebe.camunda.io:443"
