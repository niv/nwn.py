"""
Class and library to deal with NWN resources directories.
"""

import os

from nwn.res import Container, is_valid_resref


class LocalDirectory(Container):
    """
    A resource directory that reads files from a filesystem directory.

    Data is indexed once on initialization; you need to explicitly call
    reindex() to refresh the file list if you change the contents of the
    directory outside of the LocalDirectory instance.

    Missing/non-existent directories are allowed for reading.

    If you initialize with writable=True, the directory will be created if it
    does not exist.

    This class implements a read-write mapping interface but if you intend
    to modify the directory contents, you must initialize it with writable=True.

    Args:
        path: The filesystem path to the resource directory.
    """

    def reindex(self):
        self._files = (
            {
                f.lower(): os.path.join(self._path, f)
                for f in os.listdir(self._path)
                if is_valid_resref(f)
            }
            if os.path.isdir(self._path)
            else {}
        )

    def __init__(self, path: str, writable: bool = False):
        self._path = path
        self.reindex()
        self._writable = writable
        if self._writable:
            os.makedirs(self._path, exist_ok=True)

    def __getitem__(self, key: str) -> bytes:
        file_path = self._files[key.lower()]
        with open(file_path, "rb") as f:
            return f.read()

    def __iter__(self):
        return iter(self._files)

    def __len__(self) -> int:
        return len(self._files)

    def __setitem__(self, key: str, value: bytes):
        if not self._writable:
            raise TypeError("ResDir is read-only")
        if not is_valid_resref(key):
            raise ValueError(f"Invalid resref: {key}")
        file_path = os.path.join(self._path, key)
        with open(file_path, "wb") as f:
            f.write(value)
        self._files[key.lower()] = file_path

    def __delitem__(self, key: str):
        if not self._writable:
            raise TypeError("ResDir is read-only")
        file_path = self._files.pop(key.lower())
        os.remove(file_path)
