==========
Decorators
==========

A ``pyzeebe`` decorator is a function that receives a :class:`Job` instance and returns a :class:`Job`.

.. code-block:: python

    Callable[[Job], Job]

An example decorator:

.. code-block:: python

    def logging_decorator(job: Job) -> Job:
        logging.info(job)
        return job

If a decorator raises an :class:`Exception` ``pyzeebe`` will just ignore it and continue the task/other decorators.

Task Decorators
---------------

To add a decorator to a :class:`Task`:

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

You can also add a decorator to a :class:`ZeebeTaskRouter`. All tasks registered under the router will then have the decorator.


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

You can also add a decorator to a :class:`ZeebeWorker`. All tasks registered under the worker will then have the decorator.


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

``Worker`` - Decorators registered via the :class:`ZeebeWorker` class.

``Router`` - Decorators registered via the :class:`ZeebeTaskRouter` class and included in the worker with ``include_router``.

``Task`` - Decorators registered to the :class:`Task` class (with the worker/router ``task`` decorator).
