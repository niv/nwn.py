import struct
from io import BufferedReader, BytesIO

from nwn.nwscript.asm import Opcode, Auxcode, read_extra
from nwn.shared import get_nwn_encoding


def test_parse_extra_constant_integer():
    io = BufferedReader(BytesIO(struct.pack(">i", 42)))
    result = read_extra(io, Opcode.CONSTANT, Auxcode.TYPE_INTEGER)
    assert result == (42,)


def test_parse_extra_constant_float():
    io = BufferedReader(BytesIO(struct.pack(">f", 3.14)))
    result = read_extra(io, Opcode.CONSTANT, Auxcode.TYPE_FLOAT)
    assert abs(result[0] - 3.14) < 1e-6


def test_parse_extra_constant_string():
    test_string = "hello"
    io = BufferedReader(
        BytesIO(
            struct.pack(">H", len(test_string)) + test_string.encode(get_nwn_encoding())
        )
    )
    result = read_extra(io, Opcode.CONSTANT, Auxcode.TYPE_STRING)
    assert result == (test_string,)


def test_parse_extra_jmp():
    io = BufferedReader(BytesIO(struct.pack(">i", 100)))
    result = read_extra(io, Opcode.JMP, Auxcode.NONE)
    assert result == (100,)


def test_parse_extra_store_state():
    io = BufferedReader(BytesIO(struct.pack(">ii", 1, 2)))
    result = read_extra(io, Opcode.STORE_STATE, Auxcode.NONE)
    assert result == (1, 2)


def test_parse_extra_execute_command():
    io = BufferedReader(BytesIO(struct.pack(">HB", 1, 2)))
    result = read_extra(io, Opcode.EXECUTE_COMMAND, Auxcode.NONE)
    assert result == (1, 2)


def test_parse_extra_runstack_copy():
    io = BufferedReader(BytesIO(struct.pack(">iH", 1, 2)))
    result = read_extra(io, Opcode.RUNSTACK_COPY, Auxcode.NONE)
    assert result == (1, 2)


def test_parse_extra_assignment():
    io = BufferedReader(BytesIO(struct.pack(">iH", 1, 2)))
    result = read_extra(io, Opcode.ASSIGNMENT, Auxcode.NONE)
    assert result == (1, 2)


def test_parse_extra_increment():
    io = BufferedReader(BytesIO(struct.pack(">i", 1)))
    result = read_extra(io, Opcode.INCREMENT, Auxcode.NONE)
    assert result == (1,)


def test_parse_extra_de_struct():
    io = BufferedReader(BytesIO(struct.pack(">HHH", 1, 2, 3)))
    result = read_extra(io, Opcode.DE_STRUCT, Auxcode.NONE)
    assert result == (1, 2, 3)
