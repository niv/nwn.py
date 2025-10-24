import pytest
from nwn.types import FileMagic


def test_string_input():
    fm = FileMagic("ABC")
    assert fm == b"ABC "


def test_bytes_input():
    fm = FileMagic(b"XYZ")
    assert fm == b"XYZ "


def test_exactly_four_chars():
    fm = FileMagic("WXYZ")
    assert fm == b"WXYZ"


def test_padding():
    fm = FileMagic("A")
    assert fm == b"A   "

    fm = FileMagic(b"AB")
    assert fm == b"AB  "


def test_too_long_input():
    with pytest.raises(ValueError, match="Magic must be at most 4 bytes long"):
        FileMagic("ABCDE")

    with pytest.raises(ValueError, match="Magic must be at most 4 bytes long"):
        FileMagic(b"VWXYZ")


def test_invalid_characters():
    with pytest.raises(ValueError, match="Magic must contain only"):
        FileMagic("!")

    with pytest.raises(ValueError, match="Magic must contain only"):
        FileMagic(b"hak ")
