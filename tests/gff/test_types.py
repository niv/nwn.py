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
    CExoLocString,
    VOID,
    Struct,
    List,
)
from nwn import Language


def test_byte():
    assert Byte(0) == 0
    assert Byte(128) == 128
    assert Byte(255) == 255

    with pytest.raises(ValueError):
        Byte(-1)
    with pytest.raises(ValueError):
        Byte(256)


def test_char():
    assert Char(-128) == -128
    assert Char(0) == 0
    assert Char(127) == 127

    with pytest.raises(ValueError):
        Char(-129)
    with pytest.raises(ValueError):
        Char(128)


def test_word():
    assert Word(0) == 0
    assert Word(32768) == 32768
    assert Word(65535) == 65535

    with pytest.raises(ValueError):
        Word(-1)
    with pytest.raises(ValueError):
        Word(65536)


def test_short():
    assert Short(-32768) == -32768
    assert Short(0) == 0
    assert Short(32767) == 32767

    with pytest.raises(ValueError):
        Short(-32769)
    with pytest.raises(ValueError):
        Short(32768)


def test_dword():
    assert Dword(0) == 0
    assert Dword(2147483647) == 2147483647
    assert Dword(4294967295) == 4294967295

    with pytest.raises(ValueError):
        Dword(-1)
    with pytest.raises(ValueError):
        Dword(4294967296)


def test_int():
    assert Int(-2147483648) == -2147483648
    assert Int(0) == 0
    assert Int(2147483647) == 2147483647

    with pytest.raises(ValueError):
        Int(-2147483649)
    with pytest.raises(ValueError):
        Int(2147483648)


def test_dword64():
    assert Dword64(0) == 0
    assert Dword64(9223372036854775807) == 9223372036854775807
    assert Dword64(18446744073709551615) == 18446744073709551615

    with pytest.raises(ValueError):
        Dword64(-1)
    with pytest.raises(ValueError):
        Dword64(18446744073709551616)


def test_int64():
    assert Int64(-9223372036854775808) == -9223372036854775808
    assert Int64(0) == 0
    assert Int64(9223372036854775807) == 9223372036854775807

    with pytest.raises(ValueError):
        Int64(-9223372036854775809)
    with pytest.raises(ValueError):
        Int64(9223372036854775808)


def test_float():
    assert Float(3.14) == 3.14
    assert isinstance(Float(3.14), float)
    assert Float(3.14).FIELD_KIND is not None


def test_double():
    assert Double(3.14159265359) == 3.14159265359
    assert isinstance(Double(3.14159265359), float)
    assert Double(3.14159265359).FIELD_KIND is not None


def test_cexostring():
    test_str = "Test string"
    assert CExoString(test_str) == test_str
    assert isinstance(CExoString(test_str), str)
    assert CExoString(test_str).FIELD_KIND is not None


def test_resref():
    assert ResRef("validname") == "validname"
    assert ResRef("16charslongname") == "16charslongname"

    with pytest.raises(ValueError):
        ResRef("this_resref_is_too_long")


def test_cexolocstring():
    locstring = CExoLocString(
        strref=Dword(1234),
        entries={Language.ENGLISH: "Hello", Language.FRENCH: "Bonjour"},
    )
    assert locstring.strref == 1234
    assert locstring.entries[Language.ENGLISH] == "Hello"
    assert locstring.entries[Language.FRENCH] == "Bonjour"


def test_void():
    test_bytes = b"test bytes"
    assert VOID(test_bytes) == test_bytes
    assert isinstance(VOID(test_bytes), bytes)


def test_struct():
    struct = Struct(123, name="Test", value=5)
    assert struct.struct_id == 123
    assert struct["name"] == "Test"
    assert struct.name == "Test"

    struct.age = 30
    assert struct["age"] == 30

    with pytest.raises(AttributeError):
        _ = struct.nonexistent


def test_list():
    gff_list = List()
    assert len(gff_list) == 0

    struct1 = Struct(1, name="item1")
    struct2 = Struct(2, name="item2")
    gff_list = List([struct1, struct2])

    assert len(gff_list) == 2
    assert gff_list[0].name == "item1"
    assert gff_list[1].name == "item2"
