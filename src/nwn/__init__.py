"""
nwn
===

A python package with various modules for accessing Neverwinter Nights: Enhanced Edition
data formats and functionality.

Stability
---------

This package is currently in ALPHA state. API stability is not guaranteed.

Installation
------------

The package is available on PyPI and can be installed with pip:

.. code-block:: bash

    pip install nwn

License
-------

This package is licensed under the MIT license.
"""

# Deprecation import shim, will be removed at some point; these are just left
# here to avoid breaking existing code that imports from nwn.*
from .environ import get_codepage as get_nwn_encoding
from .types import FileMagic, Gender, GenderedLanguage, Language
from .res import restype_to_extension, extension_to_restype, is_valid_resref
