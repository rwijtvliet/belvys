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
   api = belvys.Api("belvisserver01:8040", "pfm_gas")

We can also initialise from a configuration file, with the ``belvys.Api.from_file()`` class method. For the example above, the contents of the corresponing ``yaml``-file is

.. literalinclude:: ../belvys/example_api_basic.yaml
   :language: yaml

--------------
Authentication
--------------

Before we can get any data from the belvis server, we need to authenicate with by providing username and password:

.. code-block:: python

   # Continuation of previous example.
   api.access_from_usr_pwd('Myfirst.Lastname', 'my_5tr0ngp@ssw0rd')

.. warning:: Never store your username and password in a python file - e.g. use environment variables instead, and access those from the built-in ``os.environ`` dictionary.

-----
Usage
-----
 
The following methods can be used to get timeseries data, *if* the timeseries ID (``tsid``) is known. 

Metadata
--------

``.metadata()`` returns a dictionary *describing* the timeseries, see the example below. The most relevant metadata are highlighted. With the ``instanceToken``, the portfolio ID is meant. 

  .. code-block:: python
     
     # Continuation of previous example.
     api.metadata(23840744)

  .. code-block:: text
     :emphasize-lines: 1, 4, 6, 14

     {'id': '23840744',
      'dataExchangeNumber': None,
      'instanceName': 'Household customers',
      'instanceToken': 'B2C_household',
      'instanceType': 'book',
      'measurementUnit': 'MW',
      'meteringCodeOnExport': None,
      'obisCode': None,
      'obisCodeOnMsconsExport': None,
      'parameterName': 'General',
      'specificationName': 'Buch.Wirkl.Saldo',
      'specificationNumber': 5163,
      'timeRange': '2016-01-01T06:00:00.000Z--2026-01-01T05:00:00.000Z',
      'timeSeriesName': 'Procurement forward volume in MW',
      'timeStampOfLastSaving': '2022-09-02T11:57:41.000Z',
      'virtualMeteringCode': None}

Series
------

This is the main method of this class; ``.series()`` returns actual timeseries data. It includes a physical (`pint <https://pint.readthedocs.io>`_) unit if one is found in the metadata, see below. 

  .. code-block:: python

     # Continuation of previous example.
     import pandas as pd
     api.series(23840744, pd.Timestamp('2022-09-30'), pd.Timestamp('2022-10-02'))

  .. code-block:: text

      ts
      2022-09-29 23:00:00+00:00    17.802
      2022-09-30 00:00:00+00:00    17.802
      2022-09-30 01:00:00+00:00    17.802
      2022-09-30 02:00:00+00:00    17.802
      ...                          ...
      2022-10-01 02:00:00+00:00    17.802
      2022-10-01 03:00:00+00:00    17.802
      2022-10-01 04:00:00+00:00    17.802
      2022-10-01 05:00:00+00:00    36.935
      2022-10-01 06:00:00+00:00    36.935
      2022-10-01 07:00:00+00:00    36.935
      ...                          ...
      2022-10-01 18:00:00+00:00    36.935
      2022-10-01 19:00:00+00:00    36.935
      2022-10-01 20:00:00+00:00    36.935
      2022-10-01 21:00:00+00:00    36.935
      2022-10-01 22:00:00+00:00    36.935
      Freq: H, Length: 48, dtype: pint[MW]

A few things to note here about the data as it is returned by the Belvis API:

* Timestamps are localized to the UTC timezone. A conversion to the correct (in this case "Europe/Berlin") timezone is necessary.

* Timestamps are right-bound. In the example above, the first timestamp is ``2022-09-29 23:00:00+00:00``, which is the same as ``2022-09-30 01:00:00+02:00`` in the Europe/Berlin timezone. The first hour of 2022-09-30 is thus denoted with the 01:00 o'clock timestamp, which is when that hour *ends*, not when it starts.

* A peculiarity of the gas market can also be seen: daily values do not apply from midnight to midnight, but rather from 06:00 to 06:00. The values change with the timestamp ``2022-10-01 05:00:00+00:00``, which is ``2022-10-01 07:00:00+02:00`` in the Europe/Berlin timezone, which in Belvis denotes the hour starting at 06:00 (see previous point). 

More series
-----------

For convenience, the method ``.series_from_tsname()`` combines looking up the timeseries id with fetching the data. It is a thin wrapper around ``.series()``.

--------------
Timeseries IDs
--------------

For most methods above, the timeseries ID is needed. This is a number uniquely identifying a timeseries (including the portfolio that contains it) in the Belvis database.

In order to find the ``tsid``, several methods are available, depending on how much information is known about the timeseries.

* ``all_ts()``: if only the portfolio is known, this method can be used. It returns a dictionary with the names and IDs of *all* the timeseries in it.

* ``find_tsids()``: if the portfolio and part of the timeseries name is know, this method can be used. It returns the same kind of dictionary as ``all_ts()``.

* ``find_tsid()``: if the portfolio and the exact timeseries name are known, this method is used. It returns the corresponding integer ID number.

Cache
-----

To avoid repeating the (potentially time-costly) task of finding the timeseries ID, the class keeps a cache. When a file is provided during the initialisation, it is used to persistently store the cache every time it is updated. (When initialising with ``.from_file()``, this file is automatically used for this purpose.)


-------------------
Class Documentation
-------------------

.. autoclass:: belvys.Api
   :members:
   :inherited-members: