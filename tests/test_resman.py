import os

import pytest

from nwn.resdir import LocalDirectory
from nwn.res import ResDict
from nwn import key
from nwn import resman


@pytest.fixture
def temp_resdir(tmp_path):
    valid_files = {
        "test1.txt": b"hello",
        "test2.nss": b"world",
    }
    invalid_files = {
        "invalid file!!!!!!.txt": b"bad",
    }
    for fname, content in valid_files.items():
        with open(os.path.join(tmp_path, fname), "wb") as f:
            f.write(content)
    for fname, content in invalid_files.items():
        with open(os.path.join(tmp_path, fname), "wb") as f:
            f.write(content)
    return tmp_path, valid_files


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


def test_resman_no_user():
    rm = resman.create(include_user=False)
    # No user directory present: no user aliases are added, only the base
    # keyfile will be in the map
    assert len(rm.maps) == 3
    assert isinstance(rm.maps[0], key.Reader)
    assert isinstance(rm.maps[1], key.Reader)
    assert isinstance(rm.maps[2], key.Reader)
    assert len(rm) == 67
    assert rm["nwscript.nss"]


def test_resman_with_user(user_dir):
    user_dir.mkdir()
    (user_dir / "portraits").mkdir()
    (user_dir / "portraits" / "test1.tga").write_bytes(b"test")
    rm = resman.create(include_user=True)
    assert len(rm.maps) > 1
    assert rm["test1.tga"] == b"test"


def test_resman_inmem_writable(user_dir):
    user_dir.mkdir()
    inmem = ResDict()
    rm = resman.create(inmem)
    rm["tempfile.txt"] = b"temporary data"
    assert rm["tempfile.txt"] == b"temporary data"
