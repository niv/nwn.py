from io import BufferedReader, BytesIO
from typing import TextIO, BinaryIO
from nwn.nwscript import ndb


class Script:
    """
    Wrapper around NCS/NDB with utility helpers.

    Args:
        ncs_file: The compiled NCS file.
        ndb_file: The NDB debug information.
    """

    def __init__(self, ncs_file: BinaryIO, ndb_file: TextIO):
        self._ncs = ncs_file
        self._ndb = ndb_file

        # We currently cannot easily disasm the NCS file in one go,
        # as the actual bytecode contains relative offset instructions
        # and instructions are of variable length.
        self._ncs_file = BufferedReader(BytesIO(ncs_file.read()[8 + 1 + 4 :]))
        self._ndb_data = ndb.read(ndb_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @classmethod
    def from_compiled(cls, script_name: str):
        """
        Create a Script instance from a filename, relative to cwd.

        Args:
            script_name: The script without file extension.
        """

        return Script(
            open(script_name + ".ncs", "rb"),
            open(script_name + ".ndb", "r"),
        )

    @property
    def ncs(self) -> BufferedReader:
        return self._ncs_file

    @property
    def ndb(self) -> ndb.Ndb:
        return self._ndb_data

    def close(self):
        self._ncs.close()
        self._ndb.close()
