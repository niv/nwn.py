"""
Binary File Format Version 3
============================

These tables describe the binary file format for the NWSync manifest file itself.

For individual files, see :mod:`nwn.compressedbuf`.

Manifest
--------

===================  ============================================
Field Type           Description
===================  ============================================
uint32               version (always 3)
uint32               count of ManifestEntries
uint32               count of ManifestMappings
ManifestEntry[]      count entries
ManifestMapping[]    count additional mappings
===================  ============================================

ManifestEntry (sorted)
----------------------

===================  ============================================
Field Type           Description
===================  ============================================
byte[20]             SHA1 (as raw bytes) of resref
uint32               size (bytes)
char[16]             resref (WITHOUT extension, pad with 0-bytes)
uint16               restype
===================  ============================================

ManifestMapping (sorted)
------------------------

===================  ============================================
Field Type           Description
===================  ============================================
uint32               Index into ManifestEntry array
char[16]             resref (WITHOUT extension, pad with 0-bytes)
uint16               restype
===================  ============================================
"""

from typing import NamedTuple, BinaryIO

from ._shared import FileMagic, restype_to_extension, extension_to_restype

NWSYNC_MANIFEST_VERSION = 3
"""The only supported version of the NWSync manifest file format."""

NWSYNC_MANIFEST_MAGIC = FileMagic("NSYM")
"""The file magic for NWSync manifest files."""


class ManifestEntry(NamedTuple):
    sha1: bytes
    """The SHA1 hash of the file, as 20 bytes."""
    size: int
    """The size of the file in bytes."""
    resref: str
    """The full filename, with resolved extension."""

    @property
    def repository_path(self):
        """The relative repository path for the file."""
        sha_hex = self.sha1.hex()
        return f"{sha_hex[0:2]}/{sha_hex[2:4]}/{sha_hex}"


class Manifest(NamedTuple):
    entries: list[ManifestEntry]

    @property
    def version(self):
        """Currently, the only supported version is 3."""
        return NWSYNC_MANIFEST_VERSION


def read(file: BinaryIO) -> Manifest:
    """
    Reads and parses a manifest file from a binary stream.

    Args:
        file: A binary stream representing the manifest file.

    Returns:
        Manifest: An object representing the parsed manifest.

    Raises:
        ValueError: If the file does not contain a valid manifest.
    """

    magic = FileMagic(file.read(4))
    if magic != NWSYNC_MANIFEST_MAGIC:
        raise ValueError("Invalid manifest magic")

    version = int.from_bytes(file.read(4), "little")
    if version != NWSYNC_MANIFEST_VERSION:
        raise ValueError("Unsupported manifest version")

    entry_count = int.from_bytes(file.read(4), "little")
    mapping_count = int.from_bytes(file.read(4), "little")

    if entry_count == 0:
        raise ValueError("Manifest has no entries")

    entries = []
    for _ in range(entry_count):
        sha1 = file.read(20)
        size = int.from_bytes(file.read(4), "little")
        resref = file.read(16).decode("ascii").rstrip("\0")
        restype = int.from_bytes(file.read(2), "little")
        filename = f"{resref}.{restype_to_extension(restype)}"
        entry = ManifestEntry(sha1, size, filename)
        entries.append(entry)

    for _ in range(mapping_count):
        index = int.from_bytes(file.read(4), "little")
        resref = file.read(16).decode("ascii").rstrip("\0")
        restype = int.from_bytes(file.read(2), "little")
        filename = f"{resref}.{restype_to_extension(restype)}"
        entry = ManifestEntry(entries[index].sha1, entries[index].size, filename)
        entries.append(entry)

    return Manifest(entries=entries)


def write(file: BinaryIO, manifest: Manifest):
    """
    Writes a manifest to a binary stream.

    Args:
        file: A binary stream to write the manifest to.
        manifest: The manifest to write to the stream.

    Raises:
        ValueError: If the manifest is invalid.
    """

    file.write(NWSYNC_MANIFEST_MAGIC)
    file.write(manifest.version.to_bytes(4, "little"))

    unique_entries = []
    mappings = []
    seen_sha1 = {}

    for entry in manifest.entries:
        if entry.sha1 not in seen_sha1:
            seen_sha1[entry.sha1] = len(unique_entries)
            unique_entries.append(entry)
        else:
            mappings.append((seen_sha1[entry.sha1], entry))

    file.write(len(unique_entries).to_bytes(4, "little"))
    file.write(len(mappings).to_bytes(4, "little"))

    def write_filename(entry):
        resref = entry.resref.split(".")[0]
        if len(resref) > 16:
            raise ValueError(f"Resref too long: {resref}")
        resext = entry.resref.split(".")[-1]
        restype = extension_to_restype(resext)
        file.write(resref.encode("ascii").ljust(16, b"\0"))
        file.write((restype).to_bytes(2, "little"))

    for entry in unique_entries:
        file.write(entry.sha1)
        file.write(entry.size.to_bytes(4, "little"))
        write_filename(entry)

    for index, entry in mappings:
        file.write(index.to_bytes(4, "little"))
        write_filename(entry)
