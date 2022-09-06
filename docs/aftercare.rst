=========
Aftercare
=========

As part of the :doc:`tenant` class, we can specify an "aftercare" function.

----------
Motivation
----------

The ``Api.series()`` method returns a ``pandas`` Series (`documentation <https://pandas.pydata.org/docs/reference/api/pandas.Series.html>`_), which is close to how the data is returned by the Belvis Rest Api. In particular, the timestamps in the index are not altered in any way - they are simply put in a pandas ``DatetimeIndex``, without any timezone conversions or other changes.

The ``Tenant.portfolio_pfl()`` and ``Tenant.price_pfl()`` methods, however, return a ``portfolyo`` PfLine (`documentation <https://portfolyo.readthedocs.io/en/latest/core/pfline.html>`_), and the series above are not always in the correct format to use as input for this class. With the help of the aftercare function, the series can be changed before being used as input.

---------------------
Necessary adjustments
---------------------

Here are several characteristics of the timeseries returned by ``Api.series()`` that are a reason for making adjustments to it. (See `the documentation <https://portfolyo.readthedocs.io/en/latest/specialized_topics/dataprep.html>`_ for the form in which ``portfolyo`` expects its data.)

We present the adjustments as functions that all have the same signature. They take a pandas Series as their single input argument, and also return a pandas Series. Further below we will see, how we combine these adjustments into a single aftercare function. 

Timezone
--------

1. The timestamps are localized to the UTC timezone (e.g. ``2022-01-01 15:00:00+00:00`` - note the ``+00:00``), even if the data applies to another timezone. E.g., if the data is actually in the 'Europe/Berlin' timezone, the correct corresponding timestamp is ``2022-01-01 16:00:00+01:00`` - with a UTC-offset of ``+01:00``. For timestamps in the summer, the UTC-offset must be ``+02:00`` due to daylight-savings time. The necessary adjustment here is to apply the ``.tz_convert()`` method to the series; in this example ``.tz_convert('Europe/Berlin')``. The adjustment function could look like this:

    .. code-block:: python

        def convert_to_berlin(s: pandas.Series) -> pandas.Series:
            return s.tz_convert('Europe/Berlin')


2. Additionally, some series with daily values ignore daylight-savings time. In other words, all values are exactly 24h apart, and the 23h-day at the start of the daylight-savings period, and 25h-day at the end are not present. Here a more complex adjustment is needed:

    .. code-block:: python

        def cet_to_berlin(s: pandas.Series) -> pandas.Series:
            return s.tz_convert("+01:00").tz_localize(None).tz_localize('Europe/Berlin')

Frequency
---------

3. Even though the timestamps are regular (e.g., one value every hour), the index of the series does not have its ``.freq`` attribute set. We can only fix this after taking care of the timezone issues (because only then are daily values actually at midnight in the correct timezone, instead of at e.g. 23:00 in UTC). Here, we can use the ``pandas.infer_freq()`` or ``portfolyo.set_frequency()`` function to adjust the series:

    .. code-block:: python

        from portfolyo.tools import frames

        def infer_frequency(s: pandas.Series) -> pandas.Series:
            return frames.set_frequency(s)  

Right-bound
-----------

4. The timestamps are right-bound if the timeseries have a below-daily (i.e., quarterhourly or hourly) frequency, and left-bound otherwise. In other words, a timestamp that denotes midnight (e.g. ``2022-01-01 00:00:00+01:00``) applies to day that *starts* at that moment if we have daily values (in this case, the first day of 2022), but it applies to the hour that *ends* at that moment if we have hourly values (in this case, the last hour of 2021). Apart from being extremely confusing, we cannot use right-bound timestamps when creating PfLine objects, so we need to adjust any series with right-bound timestamps to have left-bound timestamps instead. For example like so:

    .. code-block:: python

        from portfolyo.tools import frames

        def makeleft(s: pandas.Series) -> pandas.Series:
            td = s.index[1] - s.index[0]
            if td <= dt.timedelta(hours=2):
                s.index = portfolyo.right_to_left(s.index)
            return s

Custom issues
-------------

5. In gas markets, a 'day' is often not midnight-to-midnight, but e.g. from 06:00 to 06:00 the next day. Therefore, when the Belvis server gives us hourly values, which we want to aggregate to daily values we must actually query the data, from 06:00 on the first day we're interested in, till 06:00 of the day after the final day we're interested in. Then, we cannot simply resample (as this assumes midnight-to-midnight), but rather we must aggregate the values "manually" with our own function. The necessary adjustments here are currently not addressed in the ``belvys`` package, which introduces (usually minor) errors.

-------------------------------------------
Combining adjustments in aftercare function
-------------------------------------------

The aftercare function is a function that accepts 4 arguments: a pandas Series, the timeseries id, the portfolio id, and the timeseries name:

.. code-block:: python
    
    Aftercare = Callable[[pandas.Series, int, str, str], pandas.Series]

The ``.aftercare`` attribute of the ``Tenant`` class is such an aftercare function. Whenever a timeseries is fetched from the Belvis REST API, this function is called on the output of the ``Api.series()`` method. The output should be timeseries from which a portfolio line (``portfolyo.PfLine``) can be initialized.

The final three arguments (``tsid``, ``pfid``, ``tsname``) are passed as well, and may be used in the function definition to apply certain adjustments only to a specific timeseries, as we'll see in the example below.

``Tenant.aftercare`` is set to a default when the object is created (see below), but can simply be overwritten by setting it (i.e., ``tenant.aftercare = ...``).

Create and apply
----------------

Let's look at the aftercare function for the issues above. We have created 4 adjustment functions (``convert_to_berlin``, ``cet_to_berlin``, ``infer_frequency``, ``makeleft``). Let's say in our situation, only the timeseries with ID ``tsid == 23346575`` has the second issue. In that case, we can create the following aftercare function:

.. code-block:: python

   def aftercare_custom(s: pandas.Series, tsid: int, pfid: str, tsname: str) -> pandas.Series:
        if tsid == 23346575:
            s = cet_to_berlin(s)
        else:
            s = convert_to_berlin(s)
        s = infer_frequency(s)
        s = makeleft(s)
        return s

    tenant.aftercare = aftercare_custom

--------
Defaults
--------

By default, ``.aftercare`` attribute is a function close to the example shown above. It combines three adjustments:
  
* One to convert the timezone, similar to ``convert_to_berlin``, above. The target, however, is not "Europe/Berlin" by default, but rather the ``tz`` parameter of the ``Structure`` instance (so: ``tenant.structure.tz``).

* One to infer and set the frequency. This is the function ``infer_frequency`` shown above.

* One to make right-bound timestamps left-bound. It is the function ``makeleft`` shown above.

---------------
Ajustment store
---------------

Unless the default is exactly what is needed, the user must define the aftercare function, in the same fashion as ``aftercare_custom`` shown above. To make this easier, several common adjustment functions are available in the ``belvys.adjustment`` module. This module contains two types of functions:

* Adjustment functions (such as ``convert_to_berlin``, ``infer_frequency`` and ``makeleft``) that can be used directly. These are functions that have as input and output a single pandas Series.

* Adjustemnt function *factories*. These *return* an adjustment function, based on some configuration parameters. Their names start with ``fact_``. For example, ``fact_convert_to_tz("Europe/Berlin")`` returns the ``convert_to_berlin`` function above. (It is the more general case that allows the user to specify the timezone.) And ``fact_frequency(None)`` returns the ``infer_frequency`` function. 

Just for clarity, the ``aftercare_custom()`` function, above, is recreated here using factory functions whenever possible:

.. code-block:: python

    import belvys

    # (...) creating Tenant instance (...)

    adj1 = belvys.adjustment.fact_fixed_to_correct('+01:00', tenant.structure.tz)
    adj2 = belvys.adjustment.fact_convert_to_tz(tenant.structure.tz)

    def aftercare_custom(s: pandas.Series, tsid: int, pfid: str, tsname: str) -> pandas.Series:
        if tsid == 23346575:
            s = adj1(s)
        else:
            s = adj2(s)
        s = belvys.adjustment.infer_frequency(s)
        s = belvys.adjustment.makeleft(s)
        return s

    tenant.aftercare = aftercare_custom