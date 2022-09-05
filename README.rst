Belvys
======

.. image:: https://img.shields.io/pypi/v/belvys
   :target: https://pypi.org/project/belvys
   :alt: PyPI

.. image:: https://github.com/rwijtvliet/belvys/workflows/CI/badge.svg
   :target: https://github.com/rwijtvliet/belvys/actions?query=workflow%3ACI
   :alt: GitHub Actions - CI

.. image:: https://github.com/rwijtvliet/belvys/workflows/pre-commit/badge.svg
   :target: https://github.com/rwijtvliet/belvys/actions?query=workflow%3Apre-commit
   :alt: GitHub Actions - pre-commit

Package to fetch data from Kisters Belvis API. 

------------
Installation
------------

.. code-block:: bash

   pip install belvys


-------------
Documentation
-------------

Documentation is hosted on readthedocs:

https://belvys.readthedocs.io/

----------
Repository
----------

The git repository is hosted on github:

http://www.github.com/rwijtvliet/belvys


----------
Developing
----------

This project uses ``black`` to format code and ``flake8`` for linting. We also support ``pre-commit`` to ensure
these have been run. To configure your local environment please install these development dependencies and set up
the commit hooks.

.. code-block:: bash

   $ pip install -r requirements-dev.txt
   $ pre-commit install


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
