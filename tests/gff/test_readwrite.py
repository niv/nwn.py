from io import BytesIO

import pytest

import nwn.gff as gff


def test_read():
    with open("tests/gff/x3_it_rubygem.uti", "rb") as f:
        root, file_type = gff.read(f)
        assert file_type == "UTI "
        assert root.Tag == "X3_IT_RUBYGEM"

        assert root.PaletteID == 54
        assert isinstance(root.PaletteID, gff.Byte)


def test_rewrite():
    with open("tests/gff/x3_it_rubygem.uti", "rb") as f:
        root, file_type = gff.read(f)

    out = BytesIO()
    gff.write(out, root, file_type)
    assert out.tell()
    out.seek(0)

    test_root, test_ft = gff.read(out)

    assert test_root == root
    assert test_ft == file_type


def test_all_types():
    root = gff.Struct(
        0,
        Byte=gff.Byte(255),
        Char=gff.Char(127),
        Word=gff.Word(65535),
        Short=gff.Short(32767),
        Dword=gff.Dword(4294967295),
        Int=gff.Int(2147483647),
        Dword64=gff.Dword64(18446744073709551615),
        Int64=gff.Int64(9223372036854775807),
        Float=gff.Float(3.0),
        Double=gff.Double(6.0),
        CExoString=gff.CExoString("Test String"),
        ResRef=gff.ResRef("ResRefTest"),
        CExoLocString=gff.CExoLocString(
            strref=123456, entries={0: "Entry 0", 1: "Entry 1"}
        ),
        Void=gff.VOID(b"1234"),
        Struct=gff.Struct(0, NestedByte=gff.Byte(1)),
        List=gff.List(
            [
                gff.Struct(2, ListByte=gff.Byte(2)),
                gff.Struct(3, ListByte=gff.Byte(3)),
            ]
        ),
    )

    out = BytesIO()
    gff.write(out, root, "TEST")
    assert out.tell()
    out.seek(0)

    test_root, test_ft = gff.read(out)

    assert test_ft == "TEST"
    assert test_root == root


def test_dict_fail():
    root = gff.Struct(0, Nested={})
    with pytest.raises(ValueError):
        gff.write(BytesIO(), root, "TEST")


def test_list_fail():
    root = gff.Struct(0, Nested=[])
    with pytest.raises(ValueError):
        gff.write(BytesIO(), root, "TEST")
