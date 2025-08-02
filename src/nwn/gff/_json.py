from typing import Any

from nwn import FileMagic, GenderedLanguage
from nwn.gff import (
    Struct,
    List,
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
)

_TYPE_MAP = {
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
}


def _value_from_json(data: dict) -> Any:
    type_name = data["type"]
    value = data["value"]
    if type_name == "list":
        return List([_struct_from_json(item, 0) for item in value])
    if type_name == "struct":
        return _struct_from_json(value, 0)
    if type_name == "cexolocstring":
        strref = value.get("id", 0xFFFFFFFF)
        entries = {
            GenderedLanguage.from_id(int(k)): v for k, v in value.items() if k != "id"
        }
        return CExoLocString(strref, entries)
    if type_name in _TYPE_MAP:
        gff_type = _TYPE_MAP[type_name]
        return gff_type(value)
    raise ValueError(f"Unknown type: {type_name}")


def _struct_from_json(data: dict, default_struct_id: int) -> Struct:
    struct_id = data.get("__struct_id", default_struct_id)
    fields = {}
    for key, value in data.items():
        if not key.startswith("__"):
            fields[key] = _value_from_json(value)
    return Struct(struct_id, **fields)


def struct_from_json(data: dict) -> tuple[Struct, FileMagic]:
    """
    Parse nwn-style json representation into native python types, same
    as you would get from reading a GFF file with the `read` function.

    The data provided must be a dictionary of the root structure; e.g. reading
    the file as written by the game with the json module.

    Example:
        >>> with open("item.uti.json", "r") as f:
        ...     data = json.load(f)
        ...     print(data["AddCost"])  # "AddCost": {"type": "dword", "value": 1000}
        ...     from nwn.gff import struct_from_json
        ...     xfrm, ty = struct_from_json(data)
        ...     print(xfrm["AddCost"])  # Dword(1000)

    Args:
        data: The json data representing a GFF structure, as emitted by
            the game or neverwinter.nim.

    Returns:
        The parsed GFF structure.

    Raises:
        ValueError: If the json data is malformed or contains unsupported types.
    """
    return (_struct_from_json(data, 0xFFFFFFFF), FileMagic(data["__data_type"]))


def _value_to_json(value: Any) -> dict:
    type_name = value.FIELD_KIND.name.lower()
    if isinstance(value, CExoLocString):
        entries: dict[str, Any] = {str(k.to_id()): v for k, v in value.entries.items()}
        if value.strref and value.strref != 0xFFFFFFFF:
            entries["id"] = value.strref
        return {
            "type": "cexolocstring",
            "value": entries,
        }
    if isinstance(value, (str, int, float)):
        return {"type": type_name, "value": value}
    raise ValueError(f"Unsupported value type: {type(value)} for value: {value}")


def _struct_to_json(struct: Struct, data_type: FileMagic | None = None) -> dict:
    result = {"__struct_id": struct.struct_id}
    if data_type:
        result["__data_type"] = data_type.decode("utf-8")
    for key, value in struct.items():
        if isinstance(value, Struct):
            result[key] = {"type": "struct", "value": _struct_to_json(value)}
        elif isinstance(value, list):
            result[key] = {
                "type": "list",
                "value": [_struct_to_json(item) for item in value],
            }
        elif hasattr(value, "FIELD_KIND"):
            result[key] = _value_to_json(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)} for key: {key}")
    return result


def struct_to_json(struct: Struct, data_type: FileMagic) -> dict:
    """
    Convert a Struct to its nwn-style json representation.

    Args:
        struct: The Struct to convert.
        data_type: File magic type to include in the json.

    Returns:
        A dictionary representing the Struct in json format.

    Raises:
        ValueError: If the Struct contains unsupported types.
    """
    return _struct_to_json(struct, data_type)
