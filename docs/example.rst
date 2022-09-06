============
Example data
============

The package provides a few examples of ``Api`` and ``Structure`` configurations. Most are shown on their respective pages in this documentation, but it is also possible to directly get the class instances or the corresponding configuration files with the following functions.

---------
Structure
---------

``belvys.example_structure()`` returns a ``Structure`` instance. The function takes a single argument that is used to return either a "basic" or a "complex" example. With ``belvys.example_structure_to_file()`` this configuration can be saved as a ``yaml`` file.

---
Api
---

Likewise, ``belvys.example_api()`` returns an ``Api`` instance, and with ``belvys.example_api_to_file()`` it can be saved as a file. These functions take the same arguments as those mentioned above - though the difference between "basic" and "complex" is much smaller here.