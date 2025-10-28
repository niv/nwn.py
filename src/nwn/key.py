"""
Read keyfiles, which store base game resources in the installation directory.
"""

import os
import struct
from datetime import datetime, timedelta, date
from typing import NamedTuple, BinaryIO, Mapping

from .res import restype_to_extension


class _VariableResource(NamedTuple):
    id: int
    io_offset: int
    io_size: int
    res_type: int


class Reader(Mapping[str, bytes]):
    """
    Open a keyfile for reading.

    Example:
        >>> with Reader("nwn_base.key") as rd:
        ...     data = rd.read_file("doortype.2da")
        ...     print(data)

    Args:
        filename: The name of the keyfile to open.
        bif_directory: The directory to search for BIF files in. If not provided,
            the directory containing the keyfile is used.

    Raises:
        ValueError: If the keyfile is not valid.
        FileNotFoundError: If the keyfile or a BIF file is not found.
    """

    class _BIFF(NamedTuple):
        filename: str
        file: BinaryIO
        variable_resources: dict[int, _VariableResource]

    class Entry(NamedTuple):
        resref: str
        size: int
        bif: str

    def __init__(self, filename: str, bif_directory=None):
        bif_directory = bif_directory or os.path.dirname(filename) + "/.."
        self._bif_files = {}
        file = self._file = open(filename, "rb")

        magic = file.read(4)
        if magic != b"KEY ":
            raise ValueError("Not a keyfile")
        version = file.read(4)
        if version != b"V1  ":
            raise ValueError("Unsupported keyfile version")

        (
            bif_count,
            key_count,
            offset_to_file_table,
            offset_to_key_table,
            self._build_year,
            self._build_day,
        ) = struct.unpack("<IIIIII", file.read(24))

        file.seek(offset_to_file_table)
        file_table = list(struct.iter_unpack("<IIHH", file.read(12 * bif_count)))

        filename_table = []
        for entry in file_table:
            file.seek(entry[1])
            filename = file.read(entry[2]).decode("ASCII").replace("\\", "/")
            filename_table.append(filename)

        def read_bif(bif_filename):
            # pylint: disable=consider-using-with
            bif_file = open(os.path.join(bif_directory, bif_filename), "rb")
            magic = bif_file.read(4)
            if magic != b"BIFF":
                raise ValueError("Not a BIF file")
            version = bif_file.read(4)
            if version != b"V1  ":
                raise ValueError("Unsupported BIF version")
            var_res_count, fixed_res_count, variable_table_offset = struct.unpack(
                "<III", bif_file.read(12)
            )
            if fixed_res_count != 0:
                raise ValueError("Fixed resources not supported")
            variable_resources = {}
            bif_file.seek(variable_table_offset)
            resource_data = bif_file.read(var_res_count * 16)
            for full_id, offset, file_size, res_type in struct.iter_unpack(
                "<IIII", resource_data
            ):
                variable_resources[full_id & 0xFFFFF] = _VariableResource(
                    id=full_id,
                    io_offset=offset,
                    io_size=file_size,
                    res_type=res_type,
                )
            return self._BIFF(
                os.path.normpath(bif_filename),
                bif_file,
                variable_resources,
            )

        file.seek(offset_to_key_table)
        self._resref_id_lookup = {}
        key_table_data = file.read(key_count * 22)
        for (
            resref_bytes,
            res_type,
            res_id,
        ) in struct.iter_unpack("<16sHI", key_table_data):
            resref = resref_bytes.rstrip(b"\x00").decode("ASCII")
            bif_idx = res_id >> 20
            if bif_idx < 0 or bif_idx >= len(file_table):
                raise ValueError("Invalid BIF index")
            resext = restype_to_extension(res_type)
            self._resref_id_lookup[f"{resref}.{resext}"] = res_id

        self._bif_files = [read_bif(fn) for fn in filename_table]

        self._entries = {
            fn: self.Entry(
                resref=fn,
                size=self._bif_files[res_id >> 20]
                .variable_resources[res_id & 0xFFFFF]
                .io_size,
                bif=self._bif_files[res_id >> 20].filename,
            )
            for fn, res_id in self._resref_id_lookup.items()
            if res_id >> 20 < len(self._bif_files)
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """
        Closes the main file and all associated BIF files. You should call
        this method when you are done with the keyfile. It is also called
        automatically when the object is deleted (eg. via context manager).
        """

        if self._file:
            self._file.close()
            self._file = None
            for bif_file in self._bif_files:
                bif_file.file.close()
            self._bif_files = []

    @property
    def build_date(self) -> date:
        """
        The build date when this keyfile was created.
        """

        return datetime(1900 + self._build_year, 1, 1).date() + timedelta(
            days=self._build_day - 1
        )

    @property
    def filenames(self) -> list[str]:
        """
        Returns all filenames in the keyfile.
        """

        return list(self._resref_id_lookup.keys())

    @property
    def filemap(self) -> dict[str, Entry]:
        """
        Returns a mapping of filenames to Entry objects.
        """

        return self._entries

    def read_file(self, filename: str) -> bytes:
        """
        Reads the content of a file from the resource archive.

        Args:
            filename: The name of the file to read, including extension.

        Returns:
            The content of the file.

        Raises:
            ValueError: If the internal state is invalid.
            KeyError: If the file is not found in the archive.
        """

        res_id = self._resref_id_lookup.get(filename)
        if res_id is None:
            raise KeyError(f"File {filename} not found in keyfile")
        bif_idx = res_id >> 20
        res_idx = res_id & 0xFFFFF
        bif = self._bif_files[bif_idx]
        resource = bif.variable_resources[res_idx]
        bif.file.seek(resource.io_offset)
        return bif.file.read(resource.io_size)

    def __getitem__(self, key: str) -> bytes:
        return self.read_file(key)

    def __iter__(self):
        return iter(self.filenames)

    def __len__(self) -> int:
        return len(self._entries)
