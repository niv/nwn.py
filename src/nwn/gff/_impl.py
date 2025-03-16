from enum import IntEnum
from typing import NamedTuple


class FieldKind(IntEnum):
    BYTE = 0
    CHAR = 1
    WORD = 2
    SHORT = 3
    DWORD = 4
    INT = 5
    DWORD64 = 6
    INT64 = 7
    FLOAT = 8
    DOUBLE = 9
    CEXOSTRING = 10
    RESREF = 11
    CEXOLOCSTRING = 12
    VOID = 13
    STRUCT = 14
    LIST = 15


class Header(NamedTuple):
    file_type: str
    file_version: str
    struct_offset: int
    struct_count: int
    field_offset: int
    field_count: int
    label_offset: int
    label_count: int
    field_data_offset: int
    field_data_size: int
    field_indices_offset: int
    field_indices_size: int
    list_indices_offset: int
    list_indices_size: int


class StructEntry(NamedTuple):
    id: int
    data_or_offset: int
    field_count: int


class FieldEntry(NamedTuple):
    type: FieldKind
    label_index: int
    data_or_offset: int
