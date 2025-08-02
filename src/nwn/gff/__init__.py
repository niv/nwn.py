"""
Transform GFF (Generic File Format) files from/to native python types.

Python representation is (Struct) and (List) objects, which can be nested.
They behave just like native python dictionaries and lists, but with some
additional methods and properties to make life easier.

Since GFF has strong typing beyond what python offers natively, the module
provides a number of custom types to represent the various field types that
can be found in a GFF file.

All field types are subclasses of the native python types, and are used to
enforce the GFF type system.

This module also provides helpers to transform NWN-style JSON data to/from
the native python type schema (eg. this data is returned by the game template
functions, and is also the serialisation format used by neverwinter.nim).
"""

from nwn.gff._reader import read
from nwn.gff._writer import write
from nwn.gff._types import (
    Byte,
    Char,
    Word,
    Short,
    Dword,
    Int,
    Dword64,
    Int64,
    Float,
    Double,
    CExoString,
    ResRef,
    CExoLocString,
    VOID,
    Struct,
    List,
)
from nwn.gff._json import struct_to_json, struct_from_json


__all__ = [
    "read",
    "write",
    "Byte",
    "Char",
    "Word",
    "Short",
    "Dword",
    "Int",
    "Dword64",
    "Int64",
    "Float",
    "Double",
    "CExoString",
    "ResRef",
    "CExoLocString",
    "VOID",
    "List",
    "Struct",
    "struct_to_json",
    "struct_from_json",
]
