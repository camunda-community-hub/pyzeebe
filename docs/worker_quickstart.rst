=================
Worker Quickstart
=================

Create and start a worker
-------------------------

.. code-block:: python

    import asyncio

    from pyzeebe import ZeebeWorker, create_insecure_channel

    channel = create_insecure_channel()
    worker = ZeebeWorker(channel)


    @worker.task(task_type="my_task")
    async def my_task(x: int):
        return {"y": x + 1}

    asyncio.run(worker.work())


Worker connection options
-------------------------

To change connection retries:

.. code-block:: python

    worker = ZeebeWorker(grpc_channel, max_connection_retries=1)  # Will only accept one failure and disconnect upon the second

This means the worker will disconnect upon two consecutive failures. Each time the worker connects successfully the counter is reset.

.. note::

    The default behavior is 10 retries. If you want infinite retries just set to -1.


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
