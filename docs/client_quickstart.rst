=================
Client QuickStart
=================

Create a client
---------------

To create a client with default configuration:

.. code-block:: python

    from pyzeebe import ZeebeClient, create_insecure_channel

    channel = create_insecure_channel()  # Will use ZEEBE_ADDRESS environment variable or localhost:26500
    client = ZeebeClient(channel)


To change connection retries:

.. code-block:: python

    client = ZeebeClient(grpc_channel, max_connection_retries=1)  # Will only accept one failure and disconnect upon the second


This means the client will disconnect upon two consecutive failures. Each time the client connects successfully the counter is reset.

.. note::

    The default behavior is 10 retries. If you want infinite retries just set to -1.



Run a Zeebe process instance
----------------------------

.. code-block:: python

    process_instance_key = await client.run_process("bpmn_process_id")


Run a process with result
--------------------------

To run a process and receive the result directly:

.. code-block:: python

    process_instance_key, result = await client.run_process_with_result("bpmn_process_id")

    # result will be a dict


Deploy a process
-----------------

.. code-block:: python

    await client.deploy_resource("process_file.bpmn")


Publish a message
-----------------

.. code-block:: python

    await client.publish_message(name="message_name", correlation_key="correlation_key")
