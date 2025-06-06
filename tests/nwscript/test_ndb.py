import os

import pytest

from nwn.nwscript.ndb import (
    ScalarType,
    StructRef,
    Function,
    Struct,
    Ndb,
    read,
)


def find_ndb_files(directory="./tests/nwscript/corpus"):
    return [
        os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".ndb")
    ]


def test_any_ndb():
    assert find_ndb_files()


@pytest.mark.parametrize("ndb_filename", find_ndb_files())
def test_parse(ndb_filename):
    with open(ndb_filename, "r") as f:
        ndb = read(f)

    assert len(ndb.files) >= 1


def test_struct_by_id():
    ndb = Ndb(
        files=[],
        structs=[Struct("struct1", [])],
        functions=[],
        variables=[],
        lines=[],
    )
    struct_ref = StructRef(id=0)
    struct = ndb.struct_by_id(struct_ref)
    assert struct.label == "struct1"


def test_function_by_name():
    ndb = Ndb(
        files=[],
        structs=[],
        functions=[Function("func1", 0, 1, ScalarType.INT, [])],
        variables=[],
        lines=[],
    )
    func = ndb.function_by_name("func1")
    assert func.label == "func1"

    with pytest.raises(KeyError):
        ndb.function_by_name("nonexistent_func")
