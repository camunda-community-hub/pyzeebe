==================
Channels Reference
==================

Channels
--------

.. autofunction:: pyzeebe.create_insecure_channel

.. autofunction:: pyzeebe.create_secure_channel

.. autofunction:: pyzeebe.create_oauth2_client_credentials_channel

.. autofunction:: pyzeebe.create_camunda_cloud_channel


Credentials
-----------

.. autoclass:: pyzeebe.credentials.OAuth2MetadataPlugin
    :members:
    :special-members:
    :private-members:

.. autoclass:: pyzeebe.credentials.Oauth2ClientCredentialsMetadataPlugin
    :members:
    :special-members:
    :private-members:


Utilities (Environment)
-----------------------

.. autofunction:: pyzeebe.channel.utils.get_zeebe_address

.. autofunction:: pyzeebe.channel.utils.get_camunda_oauth_url

.. autofunction:: pyzeebe.channel.utils.get_camunda_client_id

.. autofunction:: pyzeebe.channel.utils.get_camunda_client_secret

.. autofunction:: pyzeebe.channel.utils.get_camunda_cluster_id

.. autofunction:: pyzeebe.channel.utils.get_camunda_cluster_region

.. autofunction:: pyzeebe.channel.utils.get_camunda_token_audience

.. autofunction:: pyzeebe.channel.utils.get_camunda_address
