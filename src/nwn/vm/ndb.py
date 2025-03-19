"""
This module provides a parser for the NDB format used by the Neverwinter Nights
scripting engine. The NDB format is used to store debugging information for
compiled scripts, such as variable and function names, line numbers, and
structure definitions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import TextIO


class ScalarType(Enum):
    FLOAT = "f"
    INT = "i"
    VOID = "v"
    OBJECT = "o"
    STRING = "s"
    EFFECT = "e"


@dataclass(frozen=True)
class StructRef:
    id: int


@dataclass(frozen=True)
class Function:
    label: str
    b_start: int  # NB: includes NCS header
    b_end: int
    ret_type: ScalarType | StructRef
    args: list[ScalarType | StructRef]


@dataclass(frozen=True)
class Struct:
    label: str
    fields: list


@dataclass(frozen=True)
class Variable:
    label: str
    type: int
    b_start: int
    b_end: int
    stack_loc: int


@dataclass(frozen=True)
class Line:
    file_num: int
    line_num: int
    b_start: int
    b_end: int


@dataclass(frozen=True)
class Ndb:
    files: list
    structs: list
    functions: list
    variables: list
    lines: list

    def struct_by_id(self, struct_ref: StructRef) -> Struct:
        return self.structs[struct_ref.id]

    def function_by_name(self, name: str) -> Function:
        for f in self.functions:
            if f.label == name:
                return f
        raise KeyError(f"Function {name} not found")


def _parse_type(s):
    if s[0] == "t":
        return StructRef(int(s[1:]))
    return ScalarType(s[0])


def read(file: TextIO) -> Ndb:
    """
    Reads the given file object containing NDB data and returns an Ndb object.

    Args:
        file: A text mode file containing the NDB data to be parsed.

    Returns:
        Ndb: The parsed Ndb object.

    Raises:
        ValueError: If parsing fails.
    """

    files, structs, functions, variables, lines = [], [], [], [], []
    if file.readline().strip() != "NDB V1.0":
        raise ValueError("Invalid NDB file version.")

    counters = list(map(int, file.readline().strip().split(" ")))
    if len(counters) != 5:
        raise ValueError("Invalid NDB file header: Not enough counters.")

    while ln := file.readline().strip():
        if not ln or ln[0] == "#":
            continue

        s = ln.split(" ")

        if not s[0]:
            raise ValueError(f"Invalid line: {ln}")

        if s[0][0] in ["N", "n"]:
            if int(s[0][1:]) != len(files):
                raise ValueError(f"Expected file {len(files)}, got {s[0][1:]}")
            files.append(s[1])

        elif s[0] == "s":
            if len(s) != 3:
                raise ValueError(f"Invalid struct line: {ln}")
            structs.append(Struct(s[2], []))

        elif s[0] == "sf":
            if len(s) != 3 or not structs:
                raise ValueError(f"Invalid struct field line: {ln}")
            structs[-1].fields.append((s[2], _parse_type(s[1])))

        elif s[0] == "f":
            if len(s) != 6:
                raise ValueError(f"Invalid function line: {ln}")
            functions.append(
                Function(s[5], int(s[1], 16), int(s[2], 16), _parse_type(s[4]), [])
            )

        elif s[0] == "fp":
            if len(s) != 2 or not functions:
                raise ValueError(f"Invalid function parameter line: {ln}")
            functions[-1].args.append(_parse_type(s[1]))

        elif s[0] == "v":
            if len(s) != 6:
                raise ValueError(f"Invalid variable line: {ln}")
            variables.append(
                Variable(
                    s[5], _parse_type(s[4]), int(s[1], 16), int(s[2], 16), int(s[3], 16)
                )
            )

        elif s[0][0] == "l":
            lines.append(Line(int(s[0][1:]), int(s[1]), int(s[2], 16), int(s[3], 16)))

        else:
            raise ValueError(f"Unparsed line: {ln}")

    if len(files) != counters[0]:
        raise ValueError(f"Expected {counters[0]} files, got {len(files)}")
    if len(structs) != counters[1]:
        raise ValueError(f"Expected {counters[1]} structs, got {len(structs)}")
    if len(functions) != counters[2]:
        raise ValueError(f"Expected {counters[2]} functions, got {len(functions)}")
    if len(variables) != counters[3]:
        raise ValueError(f"Expected {counters[3]} variables, got {len(variables)}")
    if len(lines) != counters[4]:
        raise ValueError(f"Expected {counters[4]} lines, got {len(lines)}")

    return Ndb(
        files,
        structs,
        functions,
        variables,
        lines,
    )
