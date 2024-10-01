========
Channels
========

In order to instantiate a ZeebeWorker or ZeebeClient you will need to provide an instance of a `grpc.aio.Channel`.

Pyzeebe provides a couple standard ways to achieve this:


Insecure
--------

Create a grpc channel connected to a Zeebe Gateway with tls disabled


.. autofunction:: pyzeebe.create_insecure_channel


Example:

.. code-block:: python

    from pyzeebe import create_insecure_channel

    channel = create_insecure_channel(grpc_address="localhost:26500")


Secure
------

Create a grpc channel with a secure connection to a Zeebe Gateway with tls

.. autofunction:: pyzeebe.create_secure_channel

Example:

.. code-block:: python

    import grpc
    from pyzeebe import create_secure_channel


    grpc.ssl_channel_credentials(root_certificates="<root_certificate>", private_key="<private_key>")
    channel = create_secure_channel(grpc_address="host:port", channel_credentials=credentials)


Example with oauth2 (like Camunda Identity):

.. code-block:: python

    import grpc
    from pyzeebe import create_secure_channel
    from pyzeebe import AuthMetadataPlugin, CamundaIdentityCredentials


    credentials = CamundaIdentityCredentials(oauth_url=<...>, client_id=<...>, client_secret=<...>, audience=<...>)
    call_credentials = grpc.metadata_call_credentials(AuthMetadataPlugin(credentials=credentials))
    ssl_credentials = grpc.ssl_channel_credentials(root_certificates="<root_certificate>", private_key="<private_key>")
    channel_credentials = grpc.composite_channel_credentials(ssl_credentials, call_credentials)
    channel = create_secure_channel(grpc_address="host:port", channel_credentials=channel_credentials)


Camunda Cloud
-------------

Create a grpc channel connected to a Zeebe Gateway running in camunda cloud

.. autofunction:: pyzeebe.create_camunda_cloud_channel

Example:

.. code-block:: python

    from pyzeebe import create_camunda_cloud_channel

    
    channel = create_camunda_cloud_channel("client_id", "client_secret", "cluster_id")


Credentials
-----------

.. autoclass:: pyzeebe.AuthMetadataPlugin
   :members:
   :undoc-members:

.. autoclass:: pyzeebe.CredentialsABC
   :members:
   :undoc-members:

.. autoclass:: pyzeebe.CamundaIdentityCredentials
   :members:
   :undoc-members:
