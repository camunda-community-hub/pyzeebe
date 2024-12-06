======================
Channels Configuration
======================

This document describes the environment variables and configurations used for establishing different gRPC channel connections to Camunda (Zeebe) instances, either with or without authentication.

Environment Variables
---------------------

The following environment variables are used to configure channels. The variables are grouped according to their relevance and usage context in each type of channel.

These variables are only considered if a corresponding argument was not passed (Unset) during initialization of a channel.

Common Variables
----------------

This variables is used across all types of channels:

**ZEEBE_ADDRESS**
  :Description:
    The default address of the Zeebe Gateway.

  :Usage:
    Used in both secure and insecure channel configurations.
    :func:`pyzeebe.create_insecure_channel`
    :func:`pyzeebe.create_secure_channel`

  :Default:
    ``"localhost:26500"``

Common OAuth2 Variables
-----------------------

These variables are specifically for connecting to generic OAuth2 or Camunda Cloud instances.

**CAMUNDA_CLIENT_ID** / **ZEEBE_CLIENT_ID**
  :Description:
    The client ID required for OAuth2 client credential authentication.

  :Usage:
    Required for OAuth2 and Camunda Cloud channels.
    :func:`pyzeebe.create_oauth2_client_credentials_channel`
    :func:`pyzeebe.create_camunda_cloud_channel`

**CAMUNDA_CLIENT_SECRET** / **ZEEBE_CLIENT_SECRET**
  :Description:
    The client secret for the OAuth2 client.

  :Usage:
    Required for OAuth2 and Camunda Cloud channels.
    :func:`pyzeebe.create_oauth2_client_credentials_channel`
    :func:`pyzeebe.create_camunda_cloud_channel`

OAuth2 Variables (Self-Managed)
-------------------------------

These variables are primarily used for OAuth2 authentication in self-managed Camunda 8 instances.

**CAMUNDA_OAUTH_URL** / **ZEEBE_AUTHORIZATION_SERVER_URL**
  :Description:
    Specifies the URL of the authorization server issuing access tokens to the client.

  :Usage:
    Required if channel initialization argument was not specified.
    :func:`pyzeebe.create_oauth2_client_credentials_channel`

**CAMUNDA_TOKEN_AUDIENCE** / **ZEEBE_TOKEN_AUDIENCE**
  :Description:
    Specifies the audience for the OAuth2 token.

  :Usage:
    Used when creating OAuth2 or Camunda Cloud channels.
    :func:`pyzeebe.create_oauth2_client_credentials_channel`

  :Default:
    ``None`` if not provided.

Camunda Cloud Variables (SaaS)
------------------------------

These variables are specifically for connecting to Camunda Cloud instances.

**CAMUNDA_OAUTH_URL** / **ZEEBE_AUTHORIZATION_SERVER_URL**
  :Description:
    Specifies the URL of the authorization server issuing access tokens to the client.

  :Usage:
    Used in the OAuth2 and Camunda Cloud channel configurations.
    :func:`pyzeebe.create_camunda_cloud_channel`

  :Default:
    ``"https://login.cloud.camunda.io/oauth/token"`` if not specified.

**CAMUNDA_CLUSTER_ID**
  :Description:
    The unique identifier for the Camunda Cloud cluster to connect to.

  :Usage:
    Required if channel initialization argument was not specified.
    :func:`pyzeebe.create_camunda_cloud_channel`

**CAMUNDA_CLUSTER_REGION**
  :Description:
    The region where the Camunda Cloud cluster is hosted.

  :Usage:
    Required for Camunda Cloud channels.
    :func:`pyzeebe.create_camunda_cloud_channel`

  :Default:
    ``"bru-2"`` if not provided.

**CAMUNDA_TOKEN_AUDIENCE** / **ZEEBE_TOKEN_AUDIENCE**
  :Description:
    Specifies the audience for the OAuth2 token.

  :Usage:
    Used when creating OAuth2 or Camunda Cloud channels.
    :func:`pyzeebe.create_camunda_cloud_channel`

  :Default:
    ``"zeebe.camunda.io"`` if not provided.
