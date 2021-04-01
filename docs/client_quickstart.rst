=================
Client QuickStart
=================

Create a client
---------------

To create a client with default configuration:

.. code-block:: python

    from pyzeebe import ZeebeClient

    client = ZeebeClient()  # Will use ZEEBE_ADDRESS environment variable or localhost:26500


To create a client with custom hostname and port:

.. code-block:: python

    client = ZeebeClient(hostname="zeebe_gateway", port=26500)


To change connection retries:

.. code-block:: python

    worker = ZeebeClient(max_connection_retries=1)  # Will only accept one failure and disconnect upon the second


This means the client will disconnect upon two consecutive failures. Each time the client connects successfully the counter is reset.

.. note::

    The default behavior is 10 retries. If you want infinite retries just set to -1.



To create a client with a secure connection:

.. code-block:: python

    client = ZeebeClient(secure_connection=True)

To create a client with OAuth 2.0 authentication:

.. code-block:: python

    from pyzeebe import ZeebeClient, OAuthCredentials

    credentials = OAuthCredentials(url="oauth_token_url", client_id="client_id", client_secret="client_secret",
                                   audience="audience")
    client = ZeebeClient()

To create a client for a Camunda Cloud instance:

.. code-block:: python

    from pyzeebe import ZeebeClient, CamundaCloudCredentials

    credentials = CamundaCloudCredentials(client_id="client_id", client_secret="client_secret",
                                          cluster_id="cluster_id")
    client = ZeebeClient()


Run a process
--------------

.. code-block:: python

    process_instance_key = client.run_process("bpmn_process_id")


Run a process with result
--------------------------

To run a process and receive the result directly:

.. code-block:: python

    process_instance_key, result = client.run_process_with_result("bpmn_process_id")

    # result will be a dict


Deploy a process
-----------------

.. code-block:: python

    client.deploy_process("process_file.bpmn")


Publish a message
-----------------

.. code-block:: python

    client.publish_message(name="message_name", correlation_key="correlation_key")
