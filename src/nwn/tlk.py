"""
Read and write TLK (Talk Table) files.

All strings are transparently converted to and from the NWN encoding.
"""

import struct

from typing import NamedTuple, BinaryIO
from nwn._shared import Language, get_nwn_encoding


class TlkEntry(NamedTuple):
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
) -> tuple[list, Language]:
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
        list: An object containing the language and entries from the TLK file.
        Language: The language the TLK file is configured as.

    Raises:
        ValueError: If the file does not contain valid TLK data.
    """

    magic = file.read(4)
    if magic != b"TLK ":
        raise ValueError("Invalid TLK magic")
    version = file.read(4)
    if version != b"V3.0":
        raise ValueError("Invalid TLK version")
    language = struct.unpack("<I", file.read(4))[0]
    language = Language(language)
    entry_count = struct.unpack("<I", file.read(4))[0]
    entries_offset = struct.unpack("<I", file.read(4))[0]

    if entry_count > max_entries:
        raise ValueError(f"Too many entries in TLK file: {entry_count} > {max_entries}")

    entries = []
    for i in range(entry_count):
        file.seek(20 + 40 * i)

        (
            _,  # flags (text_present=0x1, sound_present=0x2,length_present=0x4)
            sound_resref,
            _,  # volume variance: unused as per spec
            _,  # pitch variance: unused as per spec
            offset_to_string,
            string_sz,
            sound_length,
        ) = struct.unpack("<I16sIIIIf", file.read(40))

        sound_resref = sound_resref.decode("ascii").strip("\x00\xc0")

        file.seek(entries_offset + offset_to_string)
        text = file.read(string_sz).decode(get_nwn_encoding())

        if include_sound_data:
            entries.append(TlkEntry(text, sound_resref, sound_length))
        else:
            entries.append(text)

    return (entries, language)


def write(file: BinaryIO, entries: list, language: Language):
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
            entry = TlkEntry(entry)

        if entry.text:
            flags |= 0x1
            text_len = len(entry.text.encode(get_nwn_encoding()))
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
        str_data += entry.text.encode(get_nwn_encoding())

    file.write(str_data)
