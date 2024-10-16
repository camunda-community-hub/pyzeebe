=================
Worker Quickstart
=================

Create and start a worker
-------------------------

Run using event loop

.. code-block:: python

    import asyncio

    from pyzeebe import ZeebeWorker, create_insecure_channel

    channel = create_insecure_channel()
    worker = ZeebeWorker(channel)


    @worker.task(task_type="my_task")
    async def my_task(x: int):
        return {"y": x + 1}

    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.work())

.. warning::

    Calling ``worker.work`` directly using ``asyncio.run`` will not work. When you create an async grpc channel a new event loop will automatically be created, which causes problems when running the worker (see: https://github.com/camunda-community-hub/pyzeebe/issues/198).

    An easy workaround:

    .. code-block:: python

        async def main():
            channel = create_insecure_channel()
            worker = ZeebeWorker(channel)
            await worker.work()

        asyncio.run(main())

    This does make it somewhat harder to add tasks to a worker. The recommended way to deal with this is using a :ref:`Task Router`.


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

Stopping a worker
-----------------

To stop a running worker:

.. code-block:: python

    # Trigger this on some event (SIGTERM for example)
    async def shutdown():
        await worker.stop()
