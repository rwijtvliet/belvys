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
    api.access_from_usr_pwd("Myfirst.Lastname", "my_5tr0ngp@ssw0rd")

    # Create Tenant instance to query the data.
    tenant = belvys.Tenant(structure, api)

-----
Usage
-----

The most important methods are ``.portfolio_pfl()``, ``.price_pfl()``, and ``general_pfl()``. All return a ``portfolyo.PfLine`` (see `here <portfolyo.readthedocs.io>`_) instance. Here we see how they are used to get data for the 3-day (left-closed) time period from midnight 2024-09-05 until midnight 2024-09-08.

Portfolio data
--------------

``.portfolio_pfl()`` returns timeseries data in a specific portfolio. The portfolio and the timeseries must specified in the ``Structure`` instance used in the initialisation. 

.. code-block:: python

    # Continuation of previous example.
    offtake = tenant.portfolio_pfl("B2C_household", "current_offtake", "2024-09-05", "2024-09-08")
    offtake

.. code-block:: text

    PfLine object with volume information.
    . Start: 2024-09-05 00:00:00+02:00 (incl)    . Timezone    : Europe/Berlin  
    . End  : 2024-09-08 00:00:00+02:00 (excl)    . Start-of-day: 00:00:00  
    . Freq : <15 * Minutes> (288 datapoints)
                                        w            q
                                       MW          MWh

    2024-09-05 00:00:00 +0200        -67.8         -17
    2024-09-05 00:15:00 +0200        -61.3         -15
    2024-09-05 00:30:00 +0200        -55.5         -14
    2024-09-05 00:45:00 +0200        -50.9         -13
    ..                                  ..          ..
    2024-09-07 23:00:00 +0200       -105.7         -26
    2024-09-07 23:15:00 +0200        -98.9         -25
    2024-09-07 23:30:00 +0200        -91.4         -23
    2024-09-07 23:45:00 +0200        -84.0         -21

Prices
------

``.price_pfl()`` returns timeseries data for a certain price line. The price id must also be specified in the ``Structure`` instance.

.. code-block:: python

    # Continuation of previous example.
    prices = tenant.price_pfl("fwc_monthly_DE", "2024-09-05", "2024-09-08")
    prices

.. code-block:: text

    PfLine object with price information.
    . Start: 2024-09-05 00:00:00+02:00 (incl)    . Timezone    : Europe/Berlin  
    . End  : 2024-09-08 00:00:00+02:00 (excl)    . Start-of-day: 00:00:00  
    . Freq : <15 * Minutes> (288 datapoints)
                                        p
                                  Eur/MWh

    2024-09-05 00:00:00 +0200      209.31
    2024-09-05 00:15:00 +0200      189.06
    2024-09-05 00:30:00 +0200      169.01
    2024-09-05 00:45:00 +0200      147.89
    ..                                 ..
    2024-09-07 23:00:00 +0200      198.68
    2024-09-07 23:15:00 +0200      175.70
    2024-09-07 23:30:00 +0200      152.81
    2024-09-07 23:45:00 +0200      123.77


General
-------

For convenience, the method ``.general_pfl()`` exists. It can be used to fetch data using the timeseries name. This is useful if data is needed from a timeseries that is *not* specified in the ``Structure`` instance.

.. code-block:: python

    # Continuation of previous example.
    churn = tenant.general_pfl("B2C_Household", "Expected churn in MW", "2024-09-05", "2024-09-08")
    churn

.. code-block:: text

    PfLine object with volume information.
    . Start: 2024-09-05 00:00:00+02:00 (incl)    . Timezone    : Europe/Berlin  
    . End  : 2024-09-08 00:00:00+02:00 (excl)    . Start-of-day: 00:00:00  
    . Freq : <15 * Minutes> (288 datapoints)
                                         w           q
                                        MW         MWh
    
    2024-09-05 00:00:00 +0200         -6.8          -2
    2024-09-05 00:15:00 +0200         -6.1          -2
    2024-09-05 00:30:00 +0200         -5.6          -1
    2024-09-05 00:45:00 +0200         -5.1          -1
    ..                                  ..          ..
    2024-09-07 23:00:00 +0200        -10.6          -3
    2024-09-07 23:15:00 +0200         -9.9          -2
    2024-09-07 23:30:00 +0200         -9.1          -2
    2024-09-07 23:45:00 +0200         -8.4          -2


-----
Cache
-----

As mentioned in the :doc:`api` documentation, it can be time-consuming querying the api for timeseries IDs. Even if these are cached, it might be a good idea to explicitly fill the cache beforehand. This can be done using the ``.update_cache()`` menthod. It finds all timeseries in each of the relevant portfolios, and stores their ID in the cache. Any subsequent queries will therefore only use the API to find the *values* of the timeseries - which cannot be cached (because there is many data, which also constantly changes).

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