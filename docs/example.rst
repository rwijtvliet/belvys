============
Example data
============

The package provides a few examples of ``Api`` and ``Structure`` configurations. Most are shown on their respective pages in this documentation, but it is also possible to directly get the class instances or the corresponding configuration files with the following functions.

---------
Structure
---------

A basic and a more complex example of a structure file can be downloaded here: 

* basic structure configuration (:download:`download yaml📄<../belvys/example_structure_basic.yaml>`)
* complex structure configuration (:download:`download yaml📄<../belvys/example_structure_complex.yaml>`)

To use and play around with these configurations in code, use the ``belvys.example_structure()`` function. It takes a single argument ``"basic"`` or ``"complex"``, and returns a ``Structure`` instance. With ``belvys.example_structure_to_file()`` this configuration can be saved as a ``yaml`` file. 

---
Api
---

Likewise, a basic and a more complex example of an api file can be downloaded here: 

* basic api configuration (:download:`download yaml📄<../belvys/example_api_basic.yaml>`)
* complex api configuration (:download:`download yaml📄<../belvys/example_api_complex.yaml>`)

Similar functions exists: ``belvys.example_api()`` returns an ``Api`` instance, and with ``belvys.example_api_to_file()`` it can be saved as a file. These functions take the same arguments as those mentioned above - though the difference between "basic" and "complex" is much smaller here.
