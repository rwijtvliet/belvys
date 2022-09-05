===
Api
===

The ``Api`` class is used to authenicate with the belvis Api and retrieve timeseries data. It is used by the :doc:`tenant` class for this purpose, but can also be used stand-alone to investigate the timeseries available in a Belvis instance. 

--------------
Initialisation
--------------

We must specify the server (and port) and the Belvis tenant that will give us the data. For example:

.. exec_code:: 

   import belvys
   api = belvys.Api("belvisserver01:8080", "gas")

We can also initialise from a configuration file, with the ``belvys.Api.from_file()`` class method. For the example above, the contents of the corresponing ``yaml``-file is

.. literalinclude:: ../belvys/example_api_basic.yaml
   :language: yaml

--------------
Authentication
--------------

Before we can get any data from the belvis server, we need to authenicate with by providing username and password:

.. code-block:: python

   # Continuation of previous example.
   api.access_from_usr_pwd('Myfirst.Lastname', 'my!p@ssw0rd')

.. warning:: Never store your username and password in a python file - e.g. use environment variables instead, and access those from the built-in ``os.environ`` dictionary.

-----
Usage
-----

The following methods can be used to get timeseries data, IF the timeseries ID (``tsid``) is known. 

* ``.metadata()``: data *describing* the timeseries.

  .. code-block:: python
     
     # Continuation of previous example.
     api.metadata(120729)

  .. code-block:: python

     # Example data TODO

* ``.series()``: actual timeseries data. Includes a physical (`pint <https://pint.readthedocs.io>`_) unit if one is found in the metadata. This is the main method of this class.

  .. code-block:: python

     # Continuation of previous example.
     import pandas as pd
     api.series(120729, pd.Timestamp('2022-11-11'), pd.Timestamp('2022-11-13'))

  .. code-block:: python

     # Expample data TODO

--------------
Timeseries IDs
--------------

For the methods above, the timeseries ID is needed. This is a number uniquely identifying a timeseries (including the portfolio that contains it) in the Belvis database.

In order to find the ``tsid``, several methods are available, depending on how much information is known about the timeseries.

* ``all_ts()``: if only the portfolio is known, this method can be used. It returns a dictionary with the name and ID of *all* the timeseries in it.

* ``find_tsids()``: if the portfolio and part of the timeseries name is know, this method can be used. It returns the same kind of dictionary.

* ``find_tsid()``: if the portfolio and the exact timeseries name are known, this method is used. It returns the corresponding integer ID number.

Cache
-----

To avoid repeating the (potentially time-intensive) task of finding the timeseries ID, the class keeps a cache. When a file is provided during the initialisation, it is used to persistently store the cache every time it is updated. (When initialising with ``.from_file()``, this file is automatically used for this purpose.)


-------------------
Class Documentation
-------------------

.. autoclass:: belvys.Api
   :members:
   :inherited-members: