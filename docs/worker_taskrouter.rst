===========
Task Router
===========

The :py:class:`ZeebeTaskRouter` class is responsible for routing tasks to a :py:class:`ZeebeWorker` instance.
This helps with organization of large projects, where you can't import the worker in each file.

Create a Router
---------------

.. code-block:: python

    from pyzeebe import ZeebeTaskRouter

    router = ZeebeTaskRouter()

Create a task with a Router
---------------------------

Creating a task with a router is the exact same process as wiht a :py:class:`.ZeebeWorker` instance.

.. code-block:: python

    @router.task(task_type="my_task")
    async def my_task(x: int):
        return {"y": x + 1}


.. note::

    The :py:meth:`.ZeebeTaskRouter.task` decorator has all the capabities of the :py:class:`.ZeebeWorker` class.

Merge Router tasks to a worker
------------------------------

To add the router tasks to the worker we use the :py:func:`include_router` method on the worker.

.. code-block:: python

    from my_task import router

    worker.include_router(router)


Or to add multiple routers at once:

.. code-block:: python

    worker.include_router(router1, router2, router3, ...)



That's it!
