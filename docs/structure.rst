=========
Structure
=========

The purpose of the ``Structure`` class is primarily to specify the portfolios and timeseries we are interested in. This includes original Belvis portfolios, as well as synthetic ones that are the sum of several original porfolios. It also specifies where relevant prices can be found in Belvis.

It is used by the :doc:`tenant` class, but can also be used stand-alone to load a structure file and investigate, which data is defined and how.

--------------
Initialisation
--------------

We can initialise a ``Structure`` instance by specifying the initialisation parameters. For example:

.. exec_code:: 

   import belvys

   structure = belvys.Structure(
      freq="D",
      tz="Europe/Berlin",
      pflines={
         "current_offtake": "Offtake volume in MW",
         "expected_offtake": ["Offtake volume in MW", "Expected churn in MW"],
         "forward_sourced": [
               "Procurement forward volume in MW",
               "Procurement forward cost in EUR",
         ],
      },
      portfolios={
         "original": ["B2C_household", "B2C_Spot", "B2B_backtoback", "B2B_Spot"]
      },
      prices={
         "fwc_monthly_DE": {"pfid": "Germany", "tsnames": "MPFC (THE)"},
         "fwc_daily_DE": {"pfid": "Germany", "tsnames": ["MPFC (THE)", "M2D profile"]},
      },
   )

See the class documentation, below, for an explanation of the meaning of these parameters. 

Alternatively, the specification can be stored in a ``yaml`` file, and used to initialise the class using the ``belvys.Structure.from_file()`` class method. Here is the corresponding file, which includes some comments for better understanding the format: 

.. literalinclude:: ../belvys/example_structure_basic.yaml
   :language: yaml

-----
Usage
-----

When the instance has been created, several methods tell us which data we expect to be available in Belvis:

* ``.available_pfids()`` returns which portfolios are specified:

   .. exec_code::

      # --- hide: start ---
      import belvys
      structure = belvys.example_structure()
      # --- hide: stop ---
      structure.available_pfids()
      # --- hide: start ---
      print(structure.available_pfids())
      

* ``.available_pflineids()`` returns which portfolio lines are available for a given portfolio. In this case, for the first portfolio: 

   .. exec_code::
      
      # --- hide: start ---
      import belvys
      structure = belvys.example_structure()
      # --- hide: stop ---
      structure.available_pflineids("B2C_household")
      # --- hide: start ---
      print(structure.available_pflineids("B2C_household"))

* ``.available_priceids()`` returns which prices are available. In this case: 

   .. exec_code::
      
      # --- hide: start ---
      import belvys
      structure = belvys.example_structure()
      # --- hide: stop ---
      structure.available_priceids()
      # --- hide: start ---
      print(structure.available_priceids())

---------------
Complex example
---------------

The example shown above is a basic one. Here is a more complex example file, which shows all possibilities to specify a ``Structure``.

.. literalinclude:: ../belvys/example_structure_complex.yaml
   :language: yaml


-------------------
Class Documentation
-------------------

.. autoclass:: belvys.Structure
   :members:
   :inherited-members:
