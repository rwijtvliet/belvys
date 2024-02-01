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

.. image:: https://readthedocs.org/projects/belvys/badge/?version=latest
    :target: https://belvys.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Belvys is a package to fetch data through the REST API of energy portfolio management software "Belvis".

Installation
------------

.. code-block:: bash

   pip install belvys
   
Or add it to ``pyproject.toml``.


Documentation
-------------

Documentation is hosted on readthedocs:

https://belvys.readthedocs.io/


The package defines 3 classes: ``Tenant``, which is the main class, and ``Structure`` and ``Api``, which it depends on. 

* The ``Tenant`` class uses a structure specification (an instance of the ``Structure`` class) and an interface (an instance of the ``Api`` class) to retrieve timeseries (more specifically ``portfolyo.PfLine`` instances) from Belvis.

* The purpose of the ``Structure`` class is primarily to specify the portfolios and timeseries we are interested in. This includes original Belvis portfolios, as well as synthetic ones that are the sum of several original porfolios. It also specifies where relevant prices can be found in Belvis.

* The ``Api`` class is used to query the belvis Api and retrieve data, including the authentication part.


Repository
----------

The git repository is hosted on github:

http://www.github.com/rwijtvliet/belvys


Developing
----------

This project uses ``black`` to format code and ``flake8`` for linting. We also support ``pre-commit`` to ensure these have been run. To configure your local environment please install these development dependencies and set up the commit hooks.

.. code-block:: bash

   poetry install --with dev,test
   pre-commit install

Development is done on feature branches, which are merged back into ``master`` via pull request.

Before creating a pull request:

* Merge the current state of ``master`` into the feature branch;

* Increase the version number (by running ``poetry version major|minor|patch``) of the feature branch.

   
Publishing
----------

To publish the current state of ``master``, run the ``create_tag.sh`` script. It will create a tag from the version number and push it to github. (The version number must be unequal to a previous tag, which is automatically true if the development is only done in feature branches, and every feature branch increases the version number.) On github, a release can be drafted from the tag.

   
Disclaimer
----------

This package interacts with the Belvis software which is delevoped by Kisters. This package is not written by, maintained by, or associated with Kisters in any way.
