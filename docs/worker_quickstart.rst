=================
Worker Quickstart
=================

Create and start a worker
-------------------------

.. code-block:: python

    import asyncio

    from pyzeebe import ZeebeWorker


    worker = ZeebeWorker()


    @worker.task(task_type="my_task")
    async def my_task(x: int):
        return {"y": x + 1}

    asyncio.run(worker.work())


Worker connection options
-------------------------

To create a worker with default configuration:

.. code-block:: python

    from pyzeebe import ZeebeWorker

    worker = ZeebeWorker()  # Will use ZEEBE_ADDRESS environment variable or localhost:26500


To create a worker with custom hostname and port:

.. code-block:: python

    worker = ZeebeWorker(hostname="zeebe_gateway", port=26500)

To change connection retries:

.. code-block:: python

    worker = ZeebeWorker(max_connection_retries=1)  # Will only accept one failure and disconnect upon the second

This means the worker will disconnect upon two consecutive failures. Each time the worker connects successfully the counter is reset.

.. note::

    The default behavior is 10 retries. If you want infinite retries just set to -1.

To create a worker with a secure connection:

.. code-block:: python

    worker = ZeebeWorker(secure_connection=True)

To create a worker with OAuth 2.0 authentication:

.. code-block:: python

    from pyzeebe import ZeebeWorker, OAuthCredentials

    credentials = OAuthCredentials(url="oauth_token_url", client_id="client_id", client_secret="client_secret",
                                   audience="audience")
    worker = ZeebeWorker()

To create a worker for a Camunda Cloud instance:

.. code-block:: python

    from pyzeebe import ZeebeWorker, CamundaCloudCredentials

    credentials = CamundaCloudCredentials(client_id="client_id", client_secret="client_secret",
                                          cluster_id="cluster_id")
    worker = ZeebeWorker()


Add a task
----------


To add a task to the worker:

.. code-block:: python

    @worker.task(task_type="my_task")
    async def my_task(x: int):
        return {"y": x + 1}

    # Or using a non-async function:

    @worker.task(task_type="my_task")
    def second_task(x: int):
        return {"y": x + 1}
