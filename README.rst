======
Belvys
======

.. image:: https://img.shields.io/pypi/v/belvys
   :target: https://pypi.org/project/belvys
   :alt: PyPI

Package to fetch data from Kisters Belvis API. 

------------
Installation
------------

.. code-block:: bash

   pip install belvys


----------
Disclaimer
----------

This package is not written by, maintained by, or associated with Kisters in any way.


-------------
Documentation
-------------

It has 3 classes: ``Tenant``, which is the main class, and ``Structure`` and ``Api``, which it depends on. 


Class ``Tenant``
----------------

This class uses a structure specification (see ``Structure``) and an interface (see ``Api``) to retrieve timeseries (more specifically ``portfolyo.PfLine`` instances) from Belvis.

It can be created from a ``Structure`` and ``Api`` instance, which can be accessed from the ``.structure`` and ``.api`` properties.


Class ``Structure``
-------------------

The purpose of this class is primarily to specify the portfolios and timeseries we are interested in. This includes original Belvis portfolios, as well as synthetic ones that are the sum of several original porfolios. It also specifies where relevant prices can be found in Belvis.

It is used by the ``Tenant`` class, but can also be used stand-alone to load a structure file and investigate, which data is defined and how.

The most convenient way to create a ``Structure`` instance is from a yaml file, with the ``Structure.from_file()`` class method. 

An example structure is returned by the ``belvys.example_structure()`` function; the corresponding file can stored to the file system with ``belvys.example_structure_to_file()``.


Class ``Api``
-------------

This class is used to query the belvis Api and retrieve data, including the authentication part. It is used by the ``Tenant`` class for this purpose, but can also be used stand-alone to investigate the timeseries available in a Belvis instance. 

For example, we can create an instance with ``api = belvys.Api('belvisserver:port', 'gas')``, then provide access with ``api.access_from_usr_pwd('Myfirst.Lastname', 'my!p@ssw0rd')`` and finally query it, e.g. to find the timeseries in a certain portfolio (``api.find_tsids``), or, with the unique timeseries id, get information (``api.metadata``) or values (``api.series``).
