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

from ._shared import (
    Language,
    GenderedLanguage,
    Gender,
    get_nwn_encoding,
    restype_to_extension,
    extension_to_restype,
    is_valid_resref,
    FileMagic,
)

__all__ = [
    "Language",
    "GenderedLanguage",
    "Gender",
    "get_nwn_encoding",
    "restype_to_extension",
    "extension_to_restype",
    "is_valid_resref",
    "FileMagic",
]
