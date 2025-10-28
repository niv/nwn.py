"""
Read and write TLK (Talk Table) files (for translation and base game string references).

All strings are transparently converted to and from the NWN encoding.
"""

import struct
from io import BytesIO
from typing import NamedTuple, BinaryIO

from nwn.types import Language
from nwn.environ import get_codepage


class Entry(NamedTuple):
    """
    A single entry in a TLK file including the text, sound resref, and sound length.
    Only used when reading TLK files with sound data.
    """

    text: str
    sound_resref: str = ""
    sound_length: float = 0.0

    def __str__(self):
        return self.text


def read(
    file: BinaryIO, include_sound_data=False, max_entries=0x7FFFF
) -> tuple[list[str | Entry], Language]:
    """
    Reads a TLK file fully into memory and returns a list of entries.

    Args:
        file: A binary file object containing the TLK file.
        include_sound_data: If True, entries are returned as TlkEntry objects.
            Otherwise, the resulting dict will contain only the text.
        max_entries: The maximum number of entries to read from the TLK file.
            This is a sanity check to avoid allocating excess memory when
            reading untrusted or corrupted data.

    Returns:
        The list of entries and the language of the TLK file.
            The list contains either strings or Entry objects, depending on
            the value of include_sound_data.

    Raises:
        ValueError: If the file does not contain valid TLK data.
    """

    (
        magic,
        version,
        language,
        entry_count,
        entries_offset,
    ) = struct.unpack("<4s4sIII", file.read(20))

    if magic != b"TLK ":
        raise ValueError("Invalid TLK magic")
    if version != b"V3.0":
        raise ValueError("Invalid TLK version")
    language = Language(language)

    if entry_count > max_entries:
        raise ValueError(f"Too many entries in TLK file: {entry_count} > {max_entries}")

    file.seek(20)
    entry_data = file.read(entry_count * 40)
    entries = [
        (
            sound_resref.decode("ascii").strip("\x00\xc0"),
            offset_to_string,
            string_sz,
            sound_length,
        )
        for (
            _,  # flags (text_present=0x1,sound_present=0x2,length_present=0x4)
            sound_resref,
            _,  # volume_variance unused as per spec
            _,  # pitch_variance unused as per spec
            offset_to_string,
            string_sz,
            sound_length,
        ) in struct.iter_unpack("<I16sIIIIf", entry_data)
    ]

    # We might be reading from a file-like object in the middle of some other stream,
    # so make sure not to read beyond the boundary of the last string.
    end_offset = max(offset + size for (_, offset, size, _) in entries)
    file.seek(entries_offset)
    string_data = file.read(end_offset).decode(get_codepage())

    return [
        (
            Entry(string_data[offset : offset + size], sound_resref, sound_length)
            if include_sound_data
            else string_data[offset : offset + size]
        )
        for (sound_resref, offset, size, sound_length) in entries
    ], language


def write(file: BinaryIO, entries: list[Entry], language: Language):
    """
    Writes a Tlk object to a binary file.

    Args:
        file: A binary file object to write the TLK data to.
        entries: A list containing the entries to write, in order.
            Entries can be either strings or TlkEntry objects.
        language: The language of the TLK file to write.

    Raises:
        ValueError: If the TLK object contains invalid data.
    """

    file.write(
        struct.pack(
            "<4s4sIII",
            b"TLK ",
            b"V3.0",
            language.value,
            len(entries),
            20 + len(entries) * 40,
        )
    )

    str_data = bytearray()

    string_offset = 0
    for idx, entry in enumerate(entries):
        flags = 0
        text_len = 0

        if isinstance(entry, str):
            entry = Entry(entry)

        if entry.text:
            flags |= 0x1
            text_len = len(entry.text.encode(get_codepage()))
        if entry.sound_resref:
            flags |= 0x2
        if entry.sound_length:
            flags |= 0x4

        if len(entry.sound_resref) > 16:
            raise ValueError(f"Sound resref at {idx} is too long")

        file.write(
            struct.pack(
                "<I16sIIIIf",
                flags,
                entry.sound_resref.ljust(16, "\x00").encode("ascii"),
                0,  # volume variance: unused as per spec
                0,  # pitch variance: unused as per spec
                string_offset,
                text_len,
                entry.sound_length,
            )
        )
        string_offset += text_len
        str_data += entry.text.encode(get_codepage())

    file.write(str_data)
