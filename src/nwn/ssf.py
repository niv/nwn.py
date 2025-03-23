"""
Read and write soundset files.

Note that the index in the SSF always has a special meaning (soundset.2da),
and cannot be reordered.
"""

import struct
from typing import BinaryIO, NamedTuple


class Entry(NamedTuple):
    """
    A single entry in a SSF file including the resref and strref.
    """

    resref: str = ""
    strref: int = 0xFFFFFFFF


def read(file: BinaryIO, max_entries=0xFF) -> list[Entry]:
    """
    Read a SSF file and return a list of entries.

    Args:
        file: A binary file object containing the SSF file.
        max_entries: The maximum number of entries to read.

    Returns:
        list: A list of tuples containing the resref and strref of each entry.

    Raises:
        ValueError: If the file does not contain valid SSF data.
    """

    magic = file.read(8)
    if magic != b"SSF V1.0":
        raise ValueError("Not a valid SSF file")

    entry_count = struct.unpack("<I", file.read(4))[0]
    if entry_count > max_entries:
        raise ValueError(f"Too many entries in SSF file: {entry_count} > {max_entries}")

    table_offset = struct.unpack("<I", file.read(4))[0]
    if table_offset != 40:
        raise ValueError("Invalid table offset")

    padding = file.read(24)
    if padding != b"\x00" * 24:
        raise ValueError("Invalid padding")

    entry_offsets = [struct.unpack("<I", file.read(4))[0] for _ in range(entry_count)]
    entries = []
    for offset in entry_offsets:
        file.seek(offset)
        resref = file.read(16).decode("ascii").strip("\x00")
        strref = struct.unpack("<I", file.read(4))[0]
        entries.append(Entry(resref, strref))

    return entries


def write(file: BinaryIO, entries: list[Entry]):
    """
    Writes a list of entries to a binary file in the SSF V1.0 format.

    Args:
        file: The binary file to write to.
        entries: A list of Entry objects to be written to the file.
    """

    file.write(b"SSF V1.0")
    file.write(struct.pack("<I", len(entries)))
    file.write(struct.pack("<I", 40))
    file.write(b"\x00" * 24)

    entry_offsets = []
    for idx in range(len(entries)):
        offset = len(entries) * 4 + 40 + idx * 20
        entry_offsets.append(offset)
        file.write(struct.pack("<I", offset))

    for entry in entries:
        file.write(entry.resref.ljust(16, "\x00").encode("ascii"))
        file.write(struct.pack("<I", entry.strref))
