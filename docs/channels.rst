========
Channels
========

In order to instantiate a ZeebeWorker or ZeebeClient you will need to provide an instance of a `grpc.aio.Channel`.
This Channel can be configured with the parameters `channel_credentials` and `channel_options`.

.. seealso::

    `Python Channel Options <https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments>`_
      Documentation of the available Python `grpc.aio.Channel` `options` (channel_arguments).


.. note::

    By default, channel_options is defined so that the grpc.keepalive_time_ms option is always set to 45_000 (45 seconds).
    Reference Camunda Docs `keep alive intervals <https://docs.camunda.io/docs/self-managed/zeebe-deployment/operations/setting-up-a-cluster/#keep-alive-intervals>`_.

    You can override the default `channel_options` by passing
    e.g. `channel_options = (("grpc.keepalive_time_ms", 60_000),)` - for a keepalive time of 60 seconds.


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


Oauth2 Client Credentials Channel
---------------------------------

.. autofunction:: pyzeebe.channel.oauth_channel.create_oauth2_client_credentials_channel

.. warning::
    Some arguments are Optional and are highly dependent on your Authentication Server configuration,
    `scope` is usually required and is often optional `audience` .

Example:

.. code-block:: python

    import grpc
    from pyzeebe.channel.oauth_channel import create_oauth2_client_credentials_channel

    channel: grpc.aio.Channel = create_oauth2_client_credentials_channel(
        grpc_address=ZEEBE_ADDRESS,
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        authorization_server=ZEEBE_AUTHORIZATION_SERVER_URL,
        scope="profile email",
        audience="zeebe-api", # NOTE: Can be omitted in some cases.
    )

Example with custom `channel_options`:

.. code-block:: python

    import grpc
    from pyzeebe.channel.oauth_channel import create_oauth2_client_credentials_channel
    from pyzeebe.types import ChannelArgumentType

    channel_options: ChannelArgumentType  = (("grpc.so_reuseport", 0),)

    channel: grpc.aio.Channel = create_oauth2_client_credentials_channel(
        grpc_address=ZEEBE_ADDRESS,
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        authorization_server=ZEEBE_AUTHORIZATION_SERVER_URL,
        scope="profile email",
        audience="zeebe-api",
        channel_options=channel_options,
    )

Example with custom `channel_credentials`:

Useful for self-signed certificates with `grpc.ssl_channel_credentials`.

.. code-block:: python

    import grpc
    from pyzeebe.channel.oauth_channel import create_oauth2_client_credentials_channel
    from pyzeebe.types import ChannelArgumentType

    channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials(
        certificate_chain=None, private_key=None, root_certificates=None
    )
    channel_options: ChannelArgumentType  = (("grpc.so_reuseport", 0),)

    channel: grpc.aio.Channel = create_oauth2_client_credentials_channel(
        grpc_address=ZEEBE_ADDRESS,
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        authorization_server=ZEEBE_AUTHORIZATION_SERVER_URL,
        scope="profile email",
        audience="zeebe-api",
        channel_credentials=channel_credentials,
        channel_options=channel_options,
    )

Camunda Cloud (Oauth2 Client Credentials Channel)
-------------------------------------------------

.. autofunction:: pyzeebe.channel.oauth_channel.create_camunda_cloud_channel

.. note::
    This is a convenience function for creating a channel with the correct parameters for Camunda Cloud.
    It is equivalent to calling `create_oauth2_client_credentials_channel` with the correct parameters.

Example:

.. code-block:: python

    from pyzeebe.channel.oauth_channel import create_camunda_cloud_channel

    channel: grpc.aio.Channel = create_camunda_cloud_channel(
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
    )

Camunda Cloud (Deprecated)
--------------------------

Create a grpc channel connected to a Zeebe Gateway running in camunda cloud

.. autofunction:: pyzeebe.channel.camunda_cloud_channel.create_camunda_cloud_channel

Example:

.. code-block:: python

    from pyzeebe.channel.camunda_cloud_channel import create_camunda_cloud_channel


    channel = create_camunda_cloud_channel("client_id", "client_secret", "cluster_id")
