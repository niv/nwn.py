import hashlib

import pytest

from nwn.key import Reader


@pytest.fixture
def reader():
    return Reader("tests/key/data/test.key")


def test_simple_read(reader):
    nws = reader.read_file("nwscript.nss")
    assert hashlib.sha1(nws).hexdigest() == "8a4d7d70d664416999b2d4a454793b8a135ab71d"
    assert reader.filenames() == [
        "inc_common.shd",
        "nwscript.nss",
        "fswater.shd",
        "ruleset.2da",
    ]


def test_invalid_file(reader):
    with pytest.raises(FileNotFoundError):
        reader.read_file("does_not_exist.txt")
