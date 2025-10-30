import pathlib
import tomllib

import pytest


@pytest.fixture(autouse=True)
def install_dir(tmp_path, monkeypatch):
    # The test directory ships with a fake install dir that has some
    # dummy data in it, in the same layout as the real game install.
    insdir = pathlib.Path(__file__).parent / "install_dir"
    monkeypatch.setenv("NWN_ROOT", str(insdir))


@pytest.fixture(autouse=True)
def user_dir(tmp_path, monkeypatch) -> pathlib.Path:
    # The default user dir is empty and does not exist yet.
    # You can request it with "nwn_user_dir" and create/write to it
    usrdir = tmp_path / "user"
    monkeypatch.setenv("NWN_HOME", str(usrdir))
    return usrdir
