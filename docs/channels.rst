========
Channels
========

In order to instantiate a ZeebeWorker or ZeebeClient you will need to provide an instance of a `grpc.aio.Channel`.

Pyzeebe provides a couple standard ways to achieve this:


Insecure
--------

Create a grpc channel connected to a Zeebe Gateway with tls disabled


.. autoclass:: pyzeebe.create_insecure_channel
    :members:


Example:

.. code-block:: python

    from pyzeebe import create_insecure_channel

    channel = create_insecure_channel(hostname="zeebe", port=443)


Secure
------

Create a grpc channel with a secure connection to a Zeebe Gateway with tls

.. autoclass:: pyzeebe.create_secure_channel
    :members:

Example:

.. code-block:: python

    import grpc
    from pyzeebe import create_secure_channel


    grpc.ssl_channel_credentials(root_certificates="<root_certificate>", private_key="<private_key>")
    channel = create_secure_channel(channel_credentials=credentials)


Camunda Cloud
-------------

Create a grpc channel connected to a Zeebe Gateway running in camunda cloud

.. autoclass:: pyzeebe.create_camunda_cloud_channel
    :members:

Example:

.. code-block:: python

    from pyzeebe import create_camunda_cloud_channel

    
    channel = create_camunda_cloud_channel("client_id", "client_secret", "cluster_id")