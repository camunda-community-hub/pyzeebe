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

   from pyzeebe import ZeebeWorker, create_insecure_channel

   channel = create_insecure_channel()
   worker = ZeebeWorker(channel)

   @worker.task(task_type="my_task")
   async def my_task(x: int):
      return {"y": x + 1}

   await worker.work()

Creating a client

.. code-block:: python

   from pyzeebe import ZeebeClient, create_insecure_channel

   channel = create_insecure_channel()
   client = ZeebeClient(channel)

   await client.run_process("my_process")

   # Run process with variables:
   await client.run_process("my_process", variables={"x": 0})


Dependencies
============

* python 3.9+
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
    Channels <channels>
    Decorators <decorators>
    Exceptions <errors>
    Zeebe Adapter <zeebe_adapter>
