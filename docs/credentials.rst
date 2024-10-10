===========
Credentials
===========

Oauth2 Client Credentials Plugin
--------------------------------

.. autoclass:: pyzeebe.credentials.Oauth2ClientCredentialsMetadataPlugin
    :members:
    :special-members:
    :private-members:

Example:

.. code-block:: python

   oauth2_client_credentials = Oauth2ClientCredentialsMetadataPlugin(
      client_id=ZEEBE_CLIENT_ID,
      client_secret=ZEEBE_CLIENT_SECRET,
      authorization_server=ZEEBE_AUTHORIZATION_SERVER_URL,
      scope="profile email",
      audience="zeebe-api",
   )
   call_credentials: grpc.CallCredentials = grpc.metadata_call_credentials(oauth2_client_credentials)
   channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials(
      certificate_chain=None, private_key=None, root_certificates=None
   )
   composite_credentials: grpc.ChannelCredentials = grpc.composite_channel_credentials(
      channel_credentials, call_credentials
   )
   options: ChannelArgumentType = (("grpc.so_reuseport", 0),)
   channel: grpc.aio.Channel = grpc.aio.secure_channel(
      target=ZEEBE_ADDRESS, credentials=composite_credentials, options=options
   )
   client = ZeebeClient(channel)

Oauth2 Plugin
-------------
.. autoclass:: pyzeebe.credentials.OAuth2MetadataPlugin
    :members:
    :special-members:
    :private-members:

Internal (Deprecated)
---------------------

.. autoclass:: pyzeebe.AuthMetadataPlugin
   :members:
   :undoc-members:

.. autoclass:: pyzeebe.CredentialsABC
   :members:
   :undoc-members:

.. autoclass:: pyzeebe.CamundaIdentityCredentials
   :members:
   :undoc-members:
