import pytest
from nwn.nwscript._types import Object


def test_object_ranges():
    with pytest.raises(ValueError):
        _ = Object(-1)
    with pytest.raises(ValueError):
        _ = Object(0x80000000)


def test_object_validity():
    assert Object(0)
    assert not Object.INVALID


def test_object_repr():
    assert repr(Object(1234)) == "Object(0x4D2)"
    assert repr(Object.INVALID) == "Object.INVALID"


def test_object_equality_valid():
    assert Object(1234) != Object(1235)
    assert Object(1234) == Object(1234)


def test_object_equality_none():
    assert Object.INVALID == None  # noqa: E711
    assert None == Object.INVALID  # noqa: E711


def test_object_equality_invalid():
    assert Object.INVALID == Object.INVALID
    assert Object.INVALID.id == 0x7F000000
    assert Object.INVALID != Object(1234)


def test_object_compare_wrong_type():
    with pytest.raises(TypeError):
        Object(1234) == "1234"
    with pytest.raises(TypeError):
        Object(1234) == 1234


def test_object_self():
    assert repr(Object.SELF) == "Object.SELF"
