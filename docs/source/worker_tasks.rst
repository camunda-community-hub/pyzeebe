=====
Tasks
=====

Tasks are the building blocks of workflows

Most basic Task
---------------

To create a task you must first create a :class:`ZeebeWorker` instance.

.. code-block:: python

    @worker.task(task_type="my_task")
    def my_task():
        return {}

This is a task that does nothing. It receives no parameters and also doesn't return any.





Task Exception Handler
----------------------

An exception handler's signature:

.. code-block:: python

    Callable[[Exception, Job], None]

In other words: an exception handler is a function that receives an :class:`Exception` and :class:`Job` instance (a pyzeebe class).

The exception handler is called when the task has failed.

To add an exception handler to a task:

.. code-block:: python

    from pyzeebe import Job


    def my_exception_handler(exception: Exception, job: Job) -> None:
        print(exception)
        job.set_failure_status(message=str(exception))


    @worker.task(task_type="my_task", exception_handler=my_exception_handler)
    def my_task():
        raise Exception()

Now every time ``my_task`` is called (and then fails), ``my_exception_handler`` is called.

*What does job.set_failure_status do?*

This tells Zeebe that the job failed. The job will then be retried (if configured in workflow definition).

Task timeout
------------
When creating a task one of the parameters we can specify is ``timeout``.

.. code-block:: python

    @worker.task(task_type="my_task", timeout=20000)
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


