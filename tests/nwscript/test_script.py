import os
import pytest
from nwn.nwscript.vm._script import Script


def find_script_files(directory="./tests/nwscript/corpus"):
    ncs_files = [f for f in os.listdir(directory) if f.endswith(".ncs")]
    ndb_files = [f for f in os.listdir(directory) if f.endswith(".ndb")]
    return [
        (os.path.join(directory, ncs), os.path.join(directory, ndb))
        for ncs, ndb in zip(ncs_files, ndb_files)
    ]


def test_find_script_files():
    assert find_script_files()


@pytest.mark.parametrize("ncs_file, ndb_file", find_script_files())
def test_script_initialization(ncs_file, ndb_file):
    with open(ncs_file, "rb") as ncs, open(ndb_file, "r") as ndb:
        script = Script(ncs, ndb)
        assert script.ncs is not None
        assert script.ndb is not None


@pytest.mark.parametrize("ncs_file, ndb_file", find_script_files())
def test_script_from_name(ncs_file, ndb_file):
    script_name = os.path.splitext(os.path.basename(ncs_file))[0]
    script = Script.from_compiled(os.path.join("./tests/nwscript/corpus", script_name))
    assert script.ncs is not None
    assert script.ndb is not None
