import os
import tempfile
import shutil
from collections import ChainMap

import pytest

from nwn.res import ResDict
from nwn.resdir import LocalDirectory


@pytest.fixture
def temp_resdir():
    temp_dir = tempfile.mkdtemp()
    try:
        valid_files = {
            "test1.txt": b"hello",
            "test2.nss": b"world",
        }
        invalid_files = {
            "invalid file!!!!!!.txt": b"bad",
        }
        for fname, content in valid_files.items():
            with open(os.path.join(temp_dir, fname), "wb") as f:
                f.write(content)
        for fname, content in invalid_files.items():
            with open(os.path.join(temp_dir, fname), "wb") as f:
                f.write(content)
        yield temp_dir, valid_files
    finally:
        shutil.rmtree(temp_dir)


def test_resdir_read(temp_resdir):
    path, valid_files = temp_resdir
    resdir = LocalDirectory(path)
    for fname, content in valid_files.items():
        assert resdir[fname] == content
    assert set(resdir) == {k.lower() for k in valid_files}
    assert len(resdir) == len(valid_files)


def test_resdir_readonly(temp_resdir):
    path, valid_files = temp_resdir
    resdir = LocalDirectory(path)
    with pytest.raises(TypeError):
        resdir["newfile.txt"] = b"data"


def test_resdir_set_and_del(temp_resdir):
    path, valid_files = temp_resdir
    resdir = LocalDirectory(path, writable=True)
    new_file = "another.bic"
    new_content = b"foobar"
    resdir[new_file] = new_content
    assert resdir[new_file] == new_content
    assert new_file.lower() in resdir
    del resdir[new_file]
    assert new_file.lower() not in resdir


def test_resdir_invalid_set(temp_resdir):
    path, _ = temp_resdir
    resdir = LocalDirectory(path, writable=True)
    with pytest.raises(ValueError):
        resdir["bad file!!!!!!!!!!!!.txt"] = b"oops"


def test_resdir_missing_get(temp_resdir):
    path, _ = temp_resdir
    resdir = LocalDirectory(path)
    with pytest.raises(KeyError):
        _ = resdir["doesnotexist.txt"]


def test_resdir_iter_and_len(temp_resdir):
    path, valid_files = temp_resdir
    resdir = LocalDirectory(path)
    files = list(resdir)
    assert set(files) == {k.lower() for k in valid_files}
    assert len(resdir) == len(valid_files)


def test_case_insensitivity(temp_resdir):
    path, valid_files = temp_resdir
    resdir = LocalDirectory(path)
    for fname, content in valid_files.items():
        assert resdir[fname.upper()] == content
        assert resdir[fname.lower()] == content


def test_chainmap_resource_stack(temp_resdir):
    path, valid_files = temp_resdir
    resman = ChainMap(
        ResDict(),
        LocalDirectory(path),
    )

    assert resman["test1.txt"] == valid_files["test1.txt"]
    resman["testing.txt"] = b"data"
    assert resman["testing.txt"] == b"data"
    del resman["testing.txt"]
    with pytest.raises(KeyError):
        del resman["test1.txt"]
