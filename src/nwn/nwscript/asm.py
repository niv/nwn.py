"""
This module provides functionality for disassembling NCS (Neverwinter Nights Script) files.

While the language bytecode is principally game-agnostic, the supported opcodes
describe the default NWN:EE instruction set.
"""

import struct

from enum import Enum
from typing import NamedTuple
import json

from nwn.shared import get_nwn_encoding

_NCS_HEADER = b"NCS V1.0"


class Opcode(Enum):
    ASSIGNMENT = 0x01
    RUNSTACK_ADD = 0x02
    RUNSTACK_COPY = 0x03
    CONSTANT = 0x04
    EXECUTE_COMMAND = 0x05
    LOGICAL_AND = 0x06
    LOGICAL_OR = 0x07
    INCLUSIVE_OR = 0x08
    EXCLUSIVE_OR = 0x09
    BOOLEAN_AND = 0x0A
    EQUAL = 0x0B
    NOT_EQUAL = 0x0C
    GEQ = 0x0D
    GT = 0x0E
    LT = 0x0F
    LEQ = 0x10
    SHIFT_LEFT = 0x11
    SHIFT_RIGHT = 0x12
    USHIFT_RIGHT = 0x13
    ADD = 0x14
    SUB = 0x15
    MUL = 0x16
    DIV = 0x17
    MODULUS = 0x18
    NEGATION = 0x19
    ONES_COMPLEMENT = 0x1A
    MODIFY_STACK_POINTER = 0x1B
    STORE_IP = 0x1C
    JMP = 0x1D
    JSR = 0x1E
    JZ = 0x1F
    RET = 0x20
    DE_STRUCT = 0x21
    BOOLEAN_NOT = 0x22
    DECREMENT = 0x23
    INCREMENT = 0x24
    JNZ = 0x25
    ASSIGNMENT_BASE = 0x26
    RUNSTACK_COPY_BASE = 0x27
    DECREMENT_BASE = 0x28
    INCREMENT_BASE = 0x29
    SAVE_BASE_POINTER = 0x2A
    RESTORE_BASE_POINTER = 0x2B
    STORE_STATE = 0x2C
    NO_OPERATION = 0x2D


class Auxcode(Enum):
    NONE = 0x00
    TYPE_VOID = 0x01
    TYPE_COMMAND = 0x02
    TYPE_INTEGER = 0x03
    TYPE_FLOAT = 0x04
    TYPE_STRING = 0x05
    TYPE_OBJECT = 0x06
    TYPE_ENGST0 = 0x10
    TYPE_ENGST1 = 0x11
    TYPE_ENGST2 = 0x12
    TYPE_ENGST3 = 0x13
    TYPE_ENGST4 = 0x14
    TYPE_ENGST5 = 0x15
    TYPE_ENGST6 = 0x16
    TYPE_ENGST7 = 0x17
    TYPE_ENGST8 = 0x18
    TYPE_ENGST9 = 0x19
    TYPETYPE_INTEGER_INTEGER = 0x20
    TYPETYPE_FLOAT_FLOAT = 0x21
    TYPETYPE_OBJECT_OBJECT = 0x22
    TYPETYPE_STRING_STRING = 0x23
    TYPETYPE_STRUCT_STRUCT = 0x24
    TYPETYPE_INTEGER_FLOAT = 0x25
    TYPETYPE_FLOAT_INTEGER = 0x26
    TYPETYPE_ENGST0_ENGST0 = 0x30
    TYPETYPE_ENGST1_ENGST1 = 0x31
    TYPETYPE_ENGST2_ENGST2 = 0x32
    TYPETYPE_ENGST3_ENGST3 = 0x33
    TYPETYPE_ENGST4_ENGST4 = 0x34
    TYPETYPE_ENGST5_ENGST5 = 0x35
    TYPETYPE_ENGST6_ENGST6 = 0x36
    TYPETYPE_ENGST7_ENGST7 = 0x37
    TYPETYPE_ENGST8_ENGST8 = 0x38
    TYPETYPE_ENGST9_ENGST9 = 0x39
    TYPETYPE_VECTOR_VECTOR = 0x3A
    TYPETYPE_VECTOR_FLOAT = 0x3B
    TYPETYPE_FLOAT_VECTOR = 0x3C
    EVAL_INPLACE = 0x70
    EVAL_POSTPLACE = 0x71


class Instr(NamedTuple):
    op: Opcode
    aux: Auxcode
    extra: tuple
    extra_len: int

    def __str__(self):
        return f"{self.op.name}.{self.aux.name}{self.extra}"


def read_extra(file, op: Opcode, aux: Auxcode) -> tuple:
    """
    Parses additional data based on the opcode and auxiliary code.

    Note: This will re-parse embedded extra data every time it's called:
    For example, JSON payloads will be evaluated.

    Args:
        file (BinaryIO): A binary stream from which to read the data.
        op: The opcode of the instruction.
        aux: The auxiliary code providing additional context for the operation.

    Returns:
        tuple: A tuple containing the parsed data, or empty.

    Raises:
        struct.error: If the data cannot be read from the stream.
        ValueError: Various error conditions.
    """

    if op == Opcode.CONSTANT:
        if aux == Auxcode.TYPE_INTEGER:
            return struct.unpack(">i", file.read(4))
        if aux == Auxcode.TYPE_FLOAT:
            return struct.unpack(">f", file.read(4))
        if aux == Auxcode.TYPE_OBJECT:
            return struct.unpack(">i", file.read(4))
        if aux == Auxcode.TYPE_STRING:
            slen = struct.unpack(">H", file.read(2))[0]
            return (file.read(slen).decode(get_nwn_encoding()),)
        if aux == Auxcode.TYPE_ENGST2:
            return struct.unpack(">i", file.read(4))
        if aux == Auxcode.TYPE_ENGST7:
            # TODO: this is wasteful, doing it every time we parse an instr
            slen = struct.unpack(">H", file.read(2))[0]
            js = file.read(slen)
            return (json.loads(js),)
        return ()
    if op in [Opcode.JZ, Opcode.JMP, Opcode.JSR, Opcode.JNZ]:
        return struct.unpack(">i", file.read(4))
    if op == Opcode.STORE_STATE:
        return struct.unpack(">ii", file.read(8))
    if op == Opcode.MODIFY_STACK_POINTER:
        return struct.unpack(">i", file.read(4))
    if op == Opcode.EXECUTE_COMMAND:
        return struct.unpack(">HB", file.read(3))
    if op in [Opcode.RUNSTACK_COPY, Opcode.RUNSTACK_COPY_BASE]:
        return struct.unpack(">iH", file.read(6))
    if op in [Opcode.ASSIGNMENT, Opcode.ASSIGNMENT_BASE]:
        return struct.unpack(">iH", file.read(6))
    if op in [
        Opcode.INCREMENT,
        Opcode.DECREMENT,
        Opcode.INCREMENT_BASE,
        Opcode.DECREMENT_BASE,
    ]:
        return struct.unpack(">i", file.read(4))
    if op == Opcode.DE_STRUCT:
        return struct.unpack(">HHH", file.read(6))
    return ()


def read_instr(file) -> Instr:
    """
    Reads an instruction from the given input stream.

    Args:
        file: A binary stream from which the instruction is read.

    Returns:
        Instr: The instruction read from the input stream.

    Raises:
        struct.error: If the data cannot be read from the stream.
        ValueError: If the opcode or auxiliary code is invalid.
    """

    op, aux = struct.unpack(">BB", file.read(2))
    op, aux = Opcode(op), Auxcode(aux)
    io_start = file.tell()
    ex = read_extra(file, op, aux)
    exl = file.tell() - io_start
    return Instr(op, aux, ex, exl)


def disasm(file):
    """
    Disassembles bytecode from a file-ish.

    Skips any encountered NCS header as a convenience.

    Args:
        file: A file-ish containing the bytecode to disassemble.

    Yields:
        Instr: The next instruction read from the bytecode stream.
    """

    # Skip header as a convenience
    if file.peek(8)[0:8] == _NCS_HEADER:
        file.seek(file.tell() + 8 + 1 + 4)

    while file.peek(1):
        yield read_instr(file)


_OPCODE_TO_CANONICAL = {
    Opcode.ASSIGNMENT: "CPDOWNSP",
    Opcode.RUNSTACK_ADD: "RSADD",
    Opcode.RUNSTACK_COPY: "CPTOPSP",
    Opcode.CONSTANT: "CONST",
    Opcode.EXECUTE_COMMAND: "ACTION",
    Opcode.LOGICAL_AND: "LOGAND",
    Opcode.LOGICAL_OR: "LOGOR",
    Opcode.INCLUSIVE_OR: "INCOR",
    Opcode.EXCLUSIVE_OR: "EXCOR",
    Opcode.BOOLEAN_AND: "BOOLAND",
    Opcode.EQUAL: "EQUAL",
    Opcode.NOT_EQUAL: "NEQUAL",
    Opcode.GEQ: "GEQ",
    Opcode.GT: "GT",
    Opcode.LT: "LT",
    Opcode.LEQ: "LEQ",
    Opcode.SHIFT_LEFT: "SHLEFT",
    Opcode.SHIFT_RIGHT: "SHRIGHT",
    Opcode.USHIFT_RIGHT: "USHRIGHT",
    Opcode.ADD: "ADD",
    Opcode.SUB: "SUB",
    Opcode.MUL: "MUL",
    Opcode.DIV: "DIV",
    Opcode.MODULUS: "MOD",
    Opcode.NEGATION: "NEG",
    Opcode.ONES_COMPLEMENT: "COMP",
    Opcode.MODIFY_STACK_POINTER: "MOVSP",
    Opcode.STORE_IP: "STOREIP",
    Opcode.JMP: "JMP",
    Opcode.JSR: "JSR",
    Opcode.JZ: "JZ",
    Opcode.RET: "RET",
    Opcode.DE_STRUCT: "DESTRUCT",
    Opcode.BOOLEAN_NOT: "NOT",
    Opcode.DECREMENT: "DECSP",
    Opcode.INCREMENT: "INCSP",
    Opcode.JNZ: "JNZ",
    Opcode.ASSIGNMENT_BASE: "CPDOWNBP",
    Opcode.RUNSTACK_COPY_BASE: "CPTOPBP",
    Opcode.DECREMENT_BASE: "DECBP",
    Opcode.INCREMENT_BASE: "INCBP",
    Opcode.SAVE_BASE_POINTER: "SAVEBP",
    Opcode.RESTORE_BASE_POINTER: "RESTOREBP",
    Opcode.STORE_STATE: "STORESTATE",
    Opcode.NO_OPERATION: "NOP",
}

_AUXCODE_TO_CANONICAL = {
    Auxcode.TYPE_INTEGER: "I",
    Auxcode.TYPE_FLOAT: "F",
    Auxcode.TYPE_STRING: "S",
    Auxcode.TYPE_OBJECT: "O",
    Auxcode.TYPE_ENGST0: "E0",
    Auxcode.TYPE_ENGST1: "E1",
    Auxcode.TYPE_ENGST2: "E2",
    Auxcode.TYPE_ENGST3: "E3",
    Auxcode.TYPE_ENGST4: "E4",
    Auxcode.TYPE_ENGST5: "E5",
    Auxcode.TYPE_ENGST6: "E6",
    Auxcode.TYPE_ENGST7: "E7",
    Auxcode.TYPE_ENGST8: "E8",
    Auxcode.TYPE_ENGST9: "E9",
    Auxcode.TYPETYPE_INTEGER_INTEGER: "II",
    Auxcode.TYPETYPE_FLOAT_FLOAT: "FF",
    Auxcode.TYPETYPE_OBJECT_OBJECT: "OO",
    Auxcode.TYPETYPE_STRING_STRING: "SS",
    Auxcode.TYPETYPE_STRUCT_STRUCT: "TT",
    Auxcode.TYPETYPE_INTEGER_FLOAT: "IF",
    Auxcode.TYPETYPE_FLOAT_INTEGER: "FI",
    Auxcode.TYPETYPE_ENGST0_ENGST0: "E0E0",
    Auxcode.TYPETYPE_ENGST1_ENGST1: "E1E1",
    Auxcode.TYPETYPE_ENGST2_ENGST2: "E2E2",
    Auxcode.TYPETYPE_ENGST3_ENGST3: "E3E3",
    Auxcode.TYPETYPE_ENGST4_ENGST4: "E4E4",
    Auxcode.TYPETYPE_ENGST5_ENGST5: "E5E5",
    Auxcode.TYPETYPE_ENGST6_ENGST6: "E6E6",
    Auxcode.TYPETYPE_ENGST7_ENGST7: "E7E7",
    Auxcode.TYPETYPE_ENGST8_ENGST8: "E8E8",
    Auxcode.TYPETYPE_ENGST9_ENGST9: "E9E9",
    Auxcode.TYPETYPE_VECTOR_VECTOR: "VV",
    Auxcode.TYPETYPE_VECTOR_FLOAT: "VF",
    Auxcode.TYPETYPE_FLOAT_VECTOR: "FV",
}
