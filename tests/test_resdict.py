import pytest

from nwn.res import ResDict


def test_resdict_set_and_get():
    d = ResDict()
    d["foo.txt"] = b"abc"
    assert d["foo.txt"] == b"abc"
    assert d["FOO.TXT"] == b"abc"
    with pytest.raises(ValueError):
        d["bad file!!!!!!!!!!!!!!!.txt"] = b"oops"
