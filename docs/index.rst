Welcome to pyzeebe's documentation!
===================================
Python client for Zeebe workflow engine

Current version is |version|.


Library installation
====================

.. code-block:: bash

   $ pip install pyzeebe

Getting Started
===============

Creating a worker

.. code-block:: python

   from pyzeebe import ZeebeWorker

   worker = ZeebeWorker()

   @worker.task(task_type="my_task")
   def my_task(x: int):
      return {"y": x + 1}

   worker.work()

Creating a client

.. code-block:: python

   from pyzeebe import ZeebeClient

   client = ZeebeClient()

   client.run_workflow("my_workflow")

   # Run workflow with variables:
   client.run_workflow("my_workflow", variables={"x": 0})


Dependencies
============

* python 3.5+
* zeebe-grpc
* grpcio
* protobuf
* oauthlib
* requests-oauthlib


Table Of Contents
=================
.. toctree::
   :maxdepth: 2

    Client <client>
    Worker <worker>
    Decorators <decorators>
    Exceptions <exceptions>
