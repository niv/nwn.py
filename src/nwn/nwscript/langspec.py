"""
A simplified parser for nwscript.nss.
"""

import re
from typing import TextIO, NamedTuple, Any, Optional

from ._types import Vector, Object, Location, VMType


class Constant(NamedTuple):
    """
    A constant definition from the language spec (e.g. ``const int TRUE = 1;``).
    """

    ty: VMType
    name: str
    value: Any


class FunctionArg(NamedTuple):
    ty: VMType
    name: str
    default: Optional[Any]


class Function(NamedTuple):
    id: int
    return_type: VMType
    name: str
    args: list[FunctionArg]
    doc: str = ""


class LanguageSpec(NamedTuple):
    constants: list[Constant]
    functions: list[Function]


_VM_TYPE_RX = "(?:" + ("|".join([f.value for f in VMType])) + ")"

_CONST_RX = re.compile("(" + _VM_TYPE_RX + ")" + r"\s+([A-Z0-9_]+)\s*=\s*([^;]+);")

_FUNC_RX = re.compile(r"\b(" + _VM_TYPE_RX + r")\s+(\w+)\s*\((.*?)\)\s*;")

_FUNC_ARG_RX = re.compile(
    r"\s*("
    + _VM_TYPE_RX
    + r")\s+(\w+)(?:\s*=\s*("
    + re.escape(r"[0.0,0.0,0.0]")
    + r"|[\w\"-]+))?"
)


def read(file: TextIO) -> LanguageSpec:
    """
    Reads a language specification from a given file.

    Args:
        file: A file-like object containing the language specification; usually nwscript.nss.

    Returns:
        LanguageSpec: An object containing constants and functions parsed from the file.

    Raises:
        ValueError: If the parsing fails.

    """

    consts = []
    funcs = []

    curdoc = []

    func_idx = 0
    for line in file:
        if line.startswith("//"):
            curdoc.append(line.removeprefix("//").strip())
            continue

        if m := _CONST_RX.match(line):
            ty = VMType(m.group(1))
            va = m.group(3)
            if ty == VMType.FLOAT:
                va = va.strip("f")
            if ty == VMType.INT and va == "TRUE":
                va = 1
            if ty == VMType.INT and va == "FALSE":
                va = 0
            va = ty.python_type()(va)
            consts.append(Constant(ty, m.group(2), va))
            curdoc = []

        if m := _FUNC_RX.match(line):
            args = []
            mm = _FUNC_ARG_RX.findall(m.group(3))
            if len(m.group(3)) != 0 and not mm:
                raise ValueError(f"Failed to parse {m.group(3)}")

            for mmm in mm:
                default = None
                if mmm[2] == "":
                    pass
                elif mmm[2] == "TRUE":
                    default = True
                elif mmm[2] == "FALSE":
                    default = False
                elif mmm[2] == "OBJECT_SELF":
                    default = Object.SELF
                elif mmm[2] == "OBJECT_INVALID":
                    default = Object.INVALID
                elif re.match(r"^-?\d+$", mmm[2]):
                    default = int(mmm[2])
                elif re.match(r"^-?\d+\.\d+f?$", mmm[2]):
                    default = float(mmm[2])
                elif mmm[2] == "[0.0,0.0,0.0]":
                    default = Vector(0, 0, 0)
                elif re.match(r'^"([^"]*)"$', mmm[2]):
                    default = mmm[2][1:-1]
                elif mmm[2] == "LOCATION_INVALID":
                    default = Location.INVALID
                elif re.match(r"^[A-Z][A-Z_]+[A-Z]$", mmm[2]):
                    # At this point, all constants must have been defined
                    c = next((c for c in consts if c.name == mmm[2]), None)
                    if c is None:
                        raise ValueError(
                            f"Unknown constant {mmm[2]} referenced in {m.group(2)}"
                        )
                    default = c.value
                else:
                    raise NotImplementedError(f"Unknown default value {mmm[2]}")
                args.append(FunctionArg(VMType(mmm[0]), mmm[1], default))

            funcs.append(
                Function(func_idx, VMType(m.group(1)), m.group(2), args, curdoc)
            )
            curdoc = []
            func_idx += 1

    return LanguageSpec(consts, funcs)
