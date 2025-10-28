=====
Tasks
=====

Tasks are the building blocks of processes

Creating a Task
---------------

To create a task you must first create a :py:class:`ZeebeWorker` or :py:class:`ZeebeTaskRouter` instance.

.. code-block:: python

    @worker.task(task_type="my_task")
    async def my_task():
        return {}

This is a task that does nothing. It receives no parameters and also doesn't return any.


.. note::

    While this task indeed returns a python dictionary, it doesn't return anything to Zeebe. To do that we have to fill the dictionary with values.


Async/Sync Tasks
----------------

Tasks can be regular or async functions. If given a regular function, pyzeebe will convert it into an async one by running :py:meth:`asyncio.loop.run_in_executor`

.. note::

    Make sure not to call any blocking function in an async task. This would slow the entire worker down.

    Do:

    .. code-block:: python

        @worker.task(task_type="my_task")
        def my_task():
            time.sleep(10) # Blocking call
            return {}

    Don't:

    .. code-block:: python

        @worker.task(task_type="my_task")
        async def my_task():
            time.sleep(10) # Blocking call
            return {}

Task Exception Handler
----------------------

An exception handler's signature:

.. code-block:: python

    Callable[[Exception, Job, JobController], Awaitable[None]]

In other words: an exception handler is a function that receives an :class:`Exception`,
:py:class:`.Job` instance and :py:class:`.JobController` (a pyzeebe class).

The exception handler is called when the task has failed.

To add an exception handler to a task:

.. code-block:: python

    from pyzeebe import Job, JobController


    async def my_exception_handler(exception: Exception, job: Job, job_controller: JobController) -> None:
        print(exception)
        await job_controller.set_failure_status(job, message=str(exception))


    @worker.task(task_type="my_task", exception_handler=my_exception_handler)
    def my_task():
        raise Exception()

Now every time ``my_task`` is called (and then fails), ``my_exception_handler`` is called.

*What does job_controller.set_failure_status do?*

This tells Zeebe that the job failed. The job will then be retried (if configured in process definition).

.. note::
    The exception handler can also be set via :py:class:`pyzeebe.ZeebeWorker` or :py:class:`pyzeebe.ZeebeTaskRouter`.
    Pyzeebe will try to find the exception handler in the following order:
    ``Worker`` -> ``Router`` -> ``Task``  -> :py:func:`pyzeebe.default_exception_handler`


Task timeout
------------
When creating a task one of the parameters we can specify is ``timeout_ms``.

.. code-block:: python

    @worker.task(task_type="my_task", timeout_ms=20000)
    def my_task(input: str):
        return {"output": f"Hello World, {input}!"}

Here we specify a timeout of 20000 milliseconds (20 seconds).
If the job is not completed within this timeout, Zeebe will reactivate the job and another worker will take over.

The default value is 10000 milliseconds or 10 seconds.

**Be sure to test your task's time and adjust the timeout accordingly.**

Tasks that don't return a dictionary
------------------------------------

Sometimes we want a task to return a singular JSON value (not a dictionary).
To do this we can set the ``single_value`` parameter to ``True``.

.. code-block:: python

    @worker.task(task_type="my_task", single_value=True, variable_name="y")
    def my_task(x: int) -> int:
        return x + 1

This will create a task that receives parameter ``x`` and returns an integer called ``y``.

So the above task is in fact equal to:

.. code-block:: python

    @worker.task(task_type="my_task")
    def my_task(x: int) -> dict:
        return {"y": x + 1}


This can be helpful when we don't want to read return values from a dictionary each time we call the task (in tests for example).

.. note::

    The parameter ``variable_name`` must be supplied if ``single_value`` is true. If not given a :class:`NoVariableNameGiven` will be raised.

Accessing the job object directly
---------------------------------

It is possible to receive the job object as a parameter inside a task function. Simply annotate the parameter with the :py:class:`pyzeebe.Job` type.

Example:

.. code-block:: python

    from pyzeebe import Job


    @worker.task(task_type="my_task")
    async def my_task(job: Job):
        print(job.process_instance_key)
        return {**job.custom_headers}
