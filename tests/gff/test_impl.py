import pytest
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
    Struct,
    List,
)


def test_byte():
    assert Byte(0) == 0
    assert isinstance(Byte(0), int)
    assert Byte(255) == 255
    assert isinstance(Byte(255), int)
    with pytest.raises(ValueError):
        Byte(-1)
    with pytest.raises(ValueError):
        Byte(256)


def test_char():
    assert Char(-128) == -128
    assert isinstance(Char(-128), int)
    assert Char(127) == 127
    assert isinstance(Char(127), int)
    with pytest.raises(ValueError):
        Char(-129)
    with pytest.raises(ValueError):
        Char(128)


def test_word():
    assert Word(0) == 0
    assert isinstance(Word(0), int)
    assert Word(65535) == 65535
    assert isinstance(Word(65535), int)
    with pytest.raises(ValueError):
        Word(-1)
    with pytest.raises(ValueError):
        Word(65536)


def test_short():
    assert Short(-32768) == -32768
    assert isinstance(Short(-32768), int)
    assert Short(32767) == 32767
    assert isinstance(Short(32767), int)
    with pytest.raises(ValueError):
        Short(-32769)
    with pytest.raises(ValueError):
        Short(32768)


def test_dword():
    assert Dword(0) == 0
    assert isinstance(Dword(0), int)
    assert Dword(4294967295) == 4294967295
    assert isinstance(Dword(4294967295), int)
    with pytest.raises(ValueError):
        Dword(-1)
    with pytest.raises(ValueError):
        Dword(4294967296)


def test_int():
    assert Int(-2147483648) == -2147483648
    assert isinstance(Int(-2147483648), int)
    assert Int(2147483647) == 2147483647
    assert isinstance(Int(2147483647), int)
    with pytest.raises(ValueError):
        Int(-2147483649)
    with pytest.raises(ValueError):
        Int(2147483648)


def test_dword64():
    assert Dword64(0) == 0
    assert isinstance(Dword64(0), int)
    assert Dword64(18446744073709551615) == 18446744073709551615
    assert isinstance(Dword64(18446744073709551615), int)
    with pytest.raises(ValueError):
        Dword64(-1)
    with pytest.raises(ValueError):
        Dword64(18446744073709551616)


def test_int64():
    assert Int64(-9223372036854775808) == -9223372036854775808
    assert isinstance(Int64(-9223372036854775808), int)
    assert Int64(9223372036854775807) == 9223372036854775807
    assert isinstance(Int64(9223372036854775807), int)
    with pytest.raises(ValueError):
        Int64(-9223372036854775809)
    with pytest.raises(ValueError):
        Int64(9223372036854775808)


def test_float():
    assert Float(1.23) == 1.23
    assert isinstance(Float(1.23), float)


def test_double():
    assert Double(1.23) == 1.23
    assert isinstance(Double(1.23), float)


def test_cexostring():
    assert CExoString("test") == "test"
    assert isinstance(CExoString("test"), str)


def test_resref():
    assert ResRef("test") == "test"
    assert isinstance(ResRef("test"), str)


def test_struct():
    fields = {"field1": Byte(1), "field2": Char(2)}
    struct = Struct(1, **fields)
    assert struct.struct_id == 1
    assert struct.field1 == Byte(1)
    assert isinstance(struct.field1, int)
    assert struct.field2 == Char(2)
    assert isinstance(struct.field2, int)
    struct.field3 = Word(3)
    assert struct.field3 == Word(3)
    assert isinstance(struct.field3, int)
    assert len(struct) == 3
    assert "field1" in struct
    assert struct["field1"] == Byte(1)
    assert isinstance(struct["field1"], int)
    struct["field4"] = Short(4)
    assert struct["field4"] == Short(4)
    assert isinstance(struct["field4"], int)


def test_list():
    struct1 = Struct(1, field1=Byte(1), field2=Char(2))
    struct2 = Struct(2, field1=Byte(3), field2=Char(4))
    lst = List([struct1, struct2])

    assert isinstance(lst, List)
    assert isinstance(lst, list)

    assert len(lst) == 2
    assert lst[0] == struct1
    assert lst[1] == struct2


def test_list_empty():
    lst = List()
    assert len(lst) == 0
    assert lst == []
