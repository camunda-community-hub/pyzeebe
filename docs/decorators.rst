==========
Decorators
==========

A ``pyzeebe`` decorator is an async/sync function that receives a :py:class:`Job` instance and returns a :py:class:`Job`.

.. code-block:: python

    Union[
        Callable[[Job], Job],
        Callable[[Job], Awaitable[Job]]
    ]

An example decorator:

.. code-block:: python

    def logging_decorator(job: Job) -> Job:
        logging.info(job)
        return job

    # Or:

    async def logging_decorator(job: Job) -> Job:
        await async_logger.info(job)
        return job

If a decorator raises an :class:`Exception` ``pyzeebe`` will just ignore it and continue the task/other decorators.

Task Decorators
---------------

To add a decorator to a :py:class:`Task`:

.. code-block:: python

    from pyzeebe import Job


    def my_decorator(job: Job) -> Job:
        print(job)
        return job


    @worker.task(task_type="my_task", before=[my_decorator], after=[my_decorator])
    def my_task():
        return {}

Now before and after a job is performed ``my_decorator`` will be called.

TaskRouter Decorators
---------------------

You can also add a decorator to a :py:class:`ZeebeTaskRouter`. All tasks registered under the router will then have the decorator.


.. code-block:: python

    from pyzeebe import ZeebeTaskRouter, Job

    router = ZeebeTaskRouter()

    def my_decorator(job: Job) -> Job:
        print(job)
        return job


    router.before(my_decorator)
    router.after(my_decorator)

Now all tasks registered to the router will have ``my_decorator``.

Worker Decorators
-----------------

You can also add a decorator to a :py:class:`ZeebeWorker`. All tasks registered under the worker will then have the decorator.


.. code-block:: python

    from pyzeebe import ZeebeWorker, Job

    worker = ZeebeWorker()

    def my_decorator(job: Job) -> Job:
        print(job)
        return job


    worker.before(my_decorator)
    worker.after(my_decorator)

Now all tasks registered to the worker will have ``my_decorator``.


Decorator order
---------------

``Worker`` -> ``Router`` -> ``Task``  -> Actual task function -> ``Task`` -> ``Router`` -> ``Worker``

``Worker`` - Decorators registered via the :py:class:`ZeebeWorker` class.

``Router`` - Decorators registered via the :py:class:`ZeebeTaskRouter` class and included in the worker with ``include_router``.

``Task`` - Decorators registered to the :py:class:`Task` class (with the worker/router ``task`` decorator).
