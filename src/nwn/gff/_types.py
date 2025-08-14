from dataclasses import dataclass

from nwn import GenderedLanguage
from nwn.gff._impl import FieldKind


class Byte(int):
    FIELD_KIND = FieldKind.BYTE
    SIMPLE_DATA_FORMAT = "B"
    LABEL = "byte"

    def __new__(cls, value):
        if not 0 <= value <= 255:
            raise ValueError(f"BYTE value out of bounds: {value}")
        return super().__new__(cls, value)


class Char(int):
    FIELD_KIND = FieldKind.CHAR
    SIMPLE_DATA_FORMAT = "b"
    LABEL = "char"

    def __new__(cls, value):
        if not -128 <= value <= 127:
            raise ValueError(f"CHAR value out of bounds: {value}")
        return super().__new__(cls, value)


class Word(int):
    FIELD_KIND = FieldKind.WORD
    SIMPLE_DATA_FORMAT = "H"
    LABEL = "word"

    def __new__(cls, value):
        if not 0 <= value <= 65535:
            raise ValueError(f"WORD value out of bounds: {value}")
        return super().__new__(cls, value)


class Short(int):
    FIELD_KIND = FieldKind.SHORT
    SIMPLE_DATA_FORMAT = "h"
    LABEL = "short"

    def __new__(cls, value):
        if not -32768 <= value <= 32767:
            raise ValueError(f"SHORT value out of bounds: {value}")
        return super().__new__(cls, value)


class Dword(int):
    FIELD_KIND = FieldKind.DWORD
    SIMPLE_DATA_FORMAT = "I"
    LABEL = "dword"

    def __new__(cls, value):
        if not 0 <= value <= 4294967295:
            raise ValueError(f"DWORD value out of bounds: {value}")
        return super().__new__(cls, value)


class Int(int):
    FIELD_KIND = FieldKind.INT
    SIMPLE_DATA_FORMAT = "i"
    LABEL = "int"

    def __new__(cls, value):
        if not -2147483648 <= value <= 2147483647:
            raise ValueError(f"INT value out of bounds: {value}")
        return super().__new__(cls, value)


class Dword64(int):
    FIELD_KIND = FieldKind.DWORD64
    LABEL = "dword64"

    def __new__(cls, value):
        if not 0 <= value <= 18446744073709551615:
            raise ValueError(f"DWORD64 value out of bounds: {value}")
        return super().__new__(cls, value)


class Int64(int):
    FIELD_KIND = FieldKind.INT64
    LABEL = "int64"

    def __new__(cls, value):
        if not -9223372036854775808 <= value <= 9223372036854775807:
            raise ValueError(f"INT64 value out of bounds: {value}")
        return super().__new__(cls, value)


class Float(float):
    FIELD_KIND = FieldKind.FLOAT
    SIMPLE_DATA_FORMAT = "f"
    LABEL = "float"


class Double(float):
    FIELD_KIND = FieldKind.DOUBLE
    LABEL = "double"


class CExoString(str):
    FIELD_KIND = FieldKind.CEXOSTRING
    LABEL = "cexostring"


class ResRef(str):
    FIELD_KIND = FieldKind.RESREF
    LABEL = "resref"

    def __new__(cls, value):
        if len(value) > 16:
            raise ValueError(f"ResRef value too long: {value}")
        return super().__new__(cls, value)


@dataclass
class CExoLocString:
    """Represents a localized string in the NWN engine."""

    FIELD_KIND = FieldKind.CEXOLOCSTRING
    LABEL = "cexolocstring"

    strref: Dword
    entries: dict[GenderedLanguage, str]

    def __str__(self):
        english = GenderedLanguage.from_id(0)
        if self.strref == 0xFFFFFFFF and self.entries.keys() == {english}:
            return self.entries[english]
        s = {str(lid.to_id()): text for lid, text in self.entries.items()}
        if self.strref != 0xFFFFFFFF:
            s["id"] = str(self.strref)
        return str(s)


class VOID(bytes):
    FIELD_KIND = FieldKind.VOID
    LABEL = "void"

    def __new__(cls, value):
        return super().__new__(cls, value)


class Struct(dict):
    """GFF Structs are just python dicts with .attr access and some metadata."""

    FIELD_KIND = FieldKind.STRUCT
    LABEL = "struct"

    def __init__(self, struct_id, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_struct_id", struct_id)

    @property
    def struct_id(self):
        """The struct ID of the struct."""
        return object.__getattribute__(self, "_struct_id")

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            ) from exc

    def __setattr__(self, name, value):
        self[name] = value


class List(list[Struct]):
    """
    GFF Lists are just python lists of Structs. They carry no metadata.

    This class exists as a convenience for type checking and
    future extensibility.
    """

    FIELD_KIND = FieldKind.LIST
    LABEL = "list"

    def __init__(self, value=None):
        if value is None:
            value = []
        super().__init__(value)


SIMPLE_TYPES = {
    FieldKind.BYTE: Byte,
    FieldKind.CHAR: Char,
    FieldKind.WORD: Word,
    FieldKind.SHORT: Short,
    FieldKind.DWORD: Dword,
    FieldKind.INT: Int,
    FieldKind.FLOAT: Float,
}

LABEL_MAP = {
    "byte": Byte,
    "char": Char,
    "word": Word,
    "short": Short,
    "dword": Dword,
    "int": Int,
    "dword64": Dword64,
    "int64": Int64,
    "float": Float,
    "double": Double,
    "cexostring": CExoString,
    "resref": ResRef,
    "cexolocstring": CExoLocString,
    "void": VOID,
    "struct": Struct,
    "list": List,
}


def type_label_to_type(label: str):
    """
    Convert a GFF type label to the corresponding type class.

    Args:
        label: The GFF label to convert.

    Returns:
        The corresponding type class.

    Raises:
        ValueError: If the label is not recognized.
    """

    if label in LABEL_MAP:
        return LABEL_MAP[label]
    raise ValueError(f"Unknown GFF type label: {label}")
