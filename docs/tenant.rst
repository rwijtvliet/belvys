======
Tenant
======

The ``Tenant`` class uses a structure specification (an instance of the :doc:`structure` class) and an interface (an instance of the :doc:`api` class) to retrieve timeseries (more specifically ``portfolyo.PfLine`` instances) from Belvis.

It also allows for some custom bespoke handling of the data which may be necessary due to the specifics of the Belvis implementation.

--------------
Initialisation
--------------

A tenant can be initialised using a ``Structure`` and an ``Api`` instance. Continuing the examples provided on their documentation pages:

.. code-block:: python

    import belvys

    # Define the structure of the belvis tenant and the timeseries we're interested in.
    structure = belvys.Structure.from_file('structureconf.yaml')

    # Define where and how to access the rest api.
    api = belvys.Api.from_file("apispec.yaml")
    api.access_from_usr_pwd("First.Lastname", "my_5tr0ngp@ssw0rd")

    # Create Tenant instance to query the data.
    tenant = belvys.Tenant(structure, api)

-----
Usage
-----

The most important methods are ``.portfolio_pfl()`` and ``.price_pfl()``. Both return a ``portfolyo.PfLine`` (see `here <portfolyo.readthedocs.io>`_) instance. Here we see how they are used to get data for the 3-day (left-closed) time period from midnight 2022-09-05 until midnight 2022-09-08:

.. code-block:: python

    # Continuation of previous example.
    import pandas as pd
    ts_left = pd.Timestamp('2022-09-05')
    ts_right = pd.Timestamp('2022-09-08')
    

Portfolio data
--------------

``.portfolio_pfl()`` returns timeseries data in a specific portfolio. The portfolio and the timeseries must specified in the ``Structure`` instance used in the initialisation. 

.. code-block:: python

    # Continuation of previous example.
    offtake = tenant.portfolio_pfl("B2C_household", "current_offtake", ts_left, ts_right)
    offtake

.. code-block:: text

    PfLine object with volume information.
    . Timestamps: first: 2022-09-05 00:00:00+02:00     timezone: Europe/Berlin
                   last: 2022-09-07 23:45:00+02:00         freq: <15 * Minutes> (288 datapoints)
                                         w           q
                                        MW         MWh

    2022-09-05 00:00:00 +0200        -99.4         -25
    2022-09-05 00:15:00 +0200        -98.4         -25
    2022-09-05 00:30:00 +0200        -97.3         -24
    2022-09-05 00:45:00 +0200        -95.9         -24
    2022-09-05 01:00:00 +0200        -95.3         -24
    ..                                  ..          ..
    2022-09-07 23:00:00 +0200       -112.4         -28
    2022-09-07 23:15:00 +0200       -109.8         -27
    2022-09-07 23:30:00 +0200       -107.3         -27
    2022-09-07 23:45:00 +0200       -105.7         -26

Prices
------

``.price_pfl()`` returns timeseries data for a certain price line. The price id must also be specified in the ``Structure`` instance.

.. code-block:: python

    # Continuation of previous example.
    prices = tenant.price_pfl("fwc_monthly_DE", ts_left, ts_right)
    prices

.. code-block:: text

    PfLine object with price information.
    . Timestamps: first: 2022-09-05 00:00:00+02:00     timezone: Europe/Berlin
                   last: 2022-09-07 23:45:00+02:00         freq: <15 * Minutes> (288 datapoints)
                                        p
                                  Eur/MWh

    2022-09-05 00:00:00 +0200      274.89
    2022-09-05 00:15:00 +0200      250.00
    2022-09-05 00:30:00 +0200      257.86
    2022-09-05 00:45:00 +0200      215.83
    2022-09-05 01:00:00 +0200      249.90
    ..                                 ..
    2022-09-07 23:00:00 +0200      499.12
    2022-09-07 23:15:00 +0200      433.34
    2022-09-07 23:30:00 +0200      377.55
    2022-09-07 23:45:00 +0200      295.72



-----
Cache
-----

As mentioned in the :doc:`api` documentation, it can be time-consuming querying the api for timeseries IDs. Even if these are cached, it might be a good idea to explicitly fill the cache beforehand. This can be done using the ``.update_cache()`` menthod. It finds all timeseries in each of the relevant portfolios, and stores their ID in the cache. Any subsequent queries will therefore only use the API to find the *values* of the timeseries - which cannot be cached, as they constantly change.

Here too: if a file is specified when initialising the ``Api`` instance, or if the instance is initialised from a file (``Api.from_file()``), the cache is stored there and can be reused when the program ends.

---------
Aftercare
---------

Unfortunately, not always is the ``pandas`` Series that is returned by the ``Api.series()`` method perfect; it may need small changes before it can be turned into a ``portfolyo`` PfLine. This is where the "aftercare" functions come into play. For more information, see this seperate page: :doc:`aftercare`.


-------------------
Class Documentation
-------------------

.. autoclass:: belvys.Tenant
   :members:
   :inherited-members: