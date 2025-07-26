import os
import glob
from io import BytesIO

import pytest

from nwn import gff, Language, Gender, GenderedLanguage, FileMagic


def gff_corpus_files():
    files = glob.glob("tests/gff/corpus/*")
    return [f for f in files if os.path.isfile(f)]


def test_corpus_files():
    assert gff_corpus_files(), "No test files found in tests/gff/corpus directory"


def test_read():
    with open("tests/gff/corpus/x3_it_rubygem.uti", "rb") as f:
        root, file_type = gff.read(f)

    assert file_type == b"UTI "
    assert root.Tag == "X3_IT_RUBYGEM"

    assert root.PaletteID == 54
    assert isinstance(root.PaletteID, gff.Byte)


def test_cexolocstr():
    with open("tests/gff/corpus/x3_it_rubygem.uti", "rb") as f:
        root, _ = gff.read(f)

    assert isinstance(root.Description, gff.CExoLocString)
    assert isinstance(root.Description.strref, gff.Dword)
    assert isinstance(list(root.Description.entries.keys())[0], GenderedLanguage)
    lng = GenderedLanguage(Language.ENGLISH, Gender.FEMALE)
    assert root.Description.entries[lng] == "Bonjour."


@pytest.mark.parametrize("file_name", gff_corpus_files())
def test_rewrite(file_name):
    with open(file_name, "rb") as f:
        root, file_type = gff.read(f)

    out = BytesIO()
    # breakpoint()
    gff.write(out, root, file_type)
    assert out.tell()
    out.seek(0)

    test_root, test_ft = gff.read(out)

    assert test_root == root
    assert test_ft == file_type


def test_all_types():
    l1 = GenderedLanguage(Language.ENGLISH, Gender.MALE)
    l2 = GenderedLanguage(Language.FRENCH, Gender.FEMALE)
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
            strref=gff.Dword(123456), entries={l1: "Entry 0", l2: "Entry 1"}
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
    gff.write(out, root, FileMagic("TEST"))
    assert out.tell()
    out.seek(0)

    test_root, test_ft = gff.read(out)

    assert test_ft == FileMagic("TEST")
    assert test_root == root

    assert isinstance(test_root.Byte, gff.Byte)
    assert isinstance(test_root.Char, gff.Char)
    assert isinstance(test_root.Word, gff.Word)
    assert isinstance(test_root.Short, gff.Short)
    assert isinstance(test_root.Dword, gff.Dword)
    assert isinstance(test_root.Int, gff.Int)
    assert isinstance(test_root.Dword64, gff.Dword64)
    assert isinstance(test_root.Int64, gff.Int64)
    assert isinstance(test_root.Float, gff.Float)
    assert isinstance(test_root.Double, gff.Double)
    assert isinstance(test_root.CExoString, gff.CExoString)
    assert isinstance(test_root.ResRef, gff.ResRef)
    assert isinstance(test_root.CExoLocString, gff.CExoLocString)
    assert isinstance(test_root.Void, gff.VOID)
    assert isinstance(test_root.Struct, gff.Struct)
    assert isinstance(test_root.List, gff.List)

    assert isinstance(test_root.Struct.NestedByte, gff.Byte)
    assert isinstance(test_root.List[0], gff.Struct)
    assert isinstance(test_root.List[0].ListByte, gff.Byte)
    assert isinstance(test_root.List[1], gff.Struct)
    assert isinstance(test_root.List[1].ListByte, gff.Byte)


def test_dict_fail():
    root = gff.Struct(0, Nested={})
    with pytest.raises(ValueError):
        gff.write(BytesIO(), root, FileMagic("TEST"))


def test_list_fail():
    root = gff.Struct(0, Nested=[])
    with pytest.raises(ValueError):
        gff.write(BytesIO(), root, FileMagic("TEST"))
