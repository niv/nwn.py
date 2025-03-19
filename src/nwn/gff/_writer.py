import struct
from typing import BinaryIO

from nwn.shared import get_nwn_encoding
from nwn.gff._types import (
    Byte,
    Char,
    Word,
    Short,
    Dword,
    Int,
    Dword64,
    Int64,
    Float,
    Double,
    CExoString,
    ResRef,
    CExoLocString,
    VOID,
    Struct,
    List,
)
from nwn.gff._impl import FieldEntry, StructEntry


def write(file: BinaryIO, root: Struct, file_type: str) -> None:
    """
    Write a GFF data structure to a binary stream.

    The structure must only use supported GFF types, as GFF is a strongly
    typed format and deviation from these will make the game fail to read
    them (e.g. storing a byte as a int will make the game not see it).

    Example:
        >>> root = gff.Struct(0, Byte=gff.Byte(255), SomeStruct=gff.Struct(SomeKey=gff.CExoString("5")))
        ... out = BytesIO()
        ... gff.write(out, root, "TEST")

    Args:
        file: The binary stream to write to.
        root: The root structure of the GFF file.
        file_type: The file type identifier (4 characters).
    """

    labels = []
    fields = []
    structs = []
    list_indices = []
    field_indices = []
    field_data = bytearray()

    label_to_index = {}

    labels = []
    fields = []
    structs = []
    list_indices = []
    field_indices = []
    field_data = bytearray()

    label_to_index = {}

    def _add_label(label: str) -> int:
        label = label.encode("ascii")[0:16]
        label = label.ljust(16, b"\x00")
        if label in label_to_index:
            return label_to_index[label]
        index = len(labels)
        label_to_index[label] = index
        labels.append(label)
        return index

    def _process_field(name: str, value) -> int:
        data_or_offset = len(field_data)

        if isinstance(value, (Byte, Char, Word, Short, Dword, Int)):
            data_or_offset = int(value)

        elif isinstance(value, Dword64):
            field_data.extend(struct.pack("<Q", int(value)))

        elif isinstance(value, Int64):
            field_data.extend(struct.pack("<q", int(value)))

        elif isinstance(value, Float):
            data_or_offset = struct.unpack("<I", struct.pack("<f", float(value)))[0]

        elif isinstance(value, Double):
            field_data.extend(struct.pack("<d", float(value)))

        elif isinstance(value, CExoString):
            encoded = value.encode(get_nwn_encoding())
            field_data.extend(struct.pack("<I", len(encoded)))
            field_data.extend(encoded)

        elif isinstance(value, ResRef):
            encoded = value.encode(get_nwn_encoding())
            if len(encoded) > 16:
                raise ValueError("Resref too long")
            field_data.extend(struct.pack("<B", len(encoded)))
            field_data.extend(encoded)

        elif isinstance(value, CExoLocString):
            field_data.extend(struct.pack("<I", 0))
            field_data.extend(struct.pack("<I", value.strref))
            field_data.extend(struct.pack("<I", len(value.entries)))
            for fid, text in value.entries.items():
                encoded = text.encode(get_nwn_encoding())
                field_data.extend(struct.pack("<I", fid))
                field_data.extend(struct.pack("<I", len(encoded)))
                field_data.extend(encoded)

        elif isinstance(value, VOID):
            field_data.extend(struct.pack("<I", len(value)))
            field_data.extend(value)

        elif isinstance(value, List):
            data_or_offset = _process_list(value)

        elif isinstance(value, Struct):
            data_or_offset = _process_struct(value)

        else:
            raise ValueError(f"Field type {type(value)} cannot be serialized to GFF")

        fields.append(
            FieldEntry(
                type=value.__class__.FIELD_KIND,
                label_index=_add_label(name),
                data_or_offset=data_or_offset,
            )
        )

        return len(fields) - 1

    def _process_struct(struct_obj: Struct) -> int:
        structs.append(None)
        struct_id = len(structs) - 1

        struct_field_indices = []
        for name, value in struct_obj.items():
            field_index = _process_field(name, value)
            struct_field_indices.append(field_index)

        if len(struct_field_indices) == 1:
            structs[struct_id] = StructEntry(
                id=struct_obj.struct_id,
                data_or_offset=struct_field_indices[0],
                field_count=1,
            )
        else:
            offset = len(field_indices)
            field_indices.extend(struct_field_indices)
            structs[struct_id] = StructEntry(
                id=struct_obj.struct_id,
                data_or_offset=offset * 4,
                field_count=len(struct_field_indices),
            )

        return struct_id

    def _process_list(list_obj: List) -> int:
        offset = len(list_indices)
        list_indices.append(len(list_obj))
        for struct_obj in list_obj:
            struct_index = _process_struct(struct_obj)
            list_indices.append(struct_index)
        return offset

    _ = _process_struct(root)

    header_size = 56
    struct_offset = header_size
    field_offset = struct_offset + len(structs) * 12
    label_offset = field_offset + len(fields) * 12
    field_data_offset = label_offset + len(labels) * 16
    field_indices_offset = field_data_offset + len(field_data)
    list_indices_offset = field_indices_offset + len(field_indices) * 4

    file.write(file_type.encode("ascii"))
    file.write(b"V3.2")

    file.write(
        struct.pack(
            "<12i",
            struct_offset,
            len(structs),
            field_offset,
            len(fields),
            label_offset,
            len(labels),
            field_data_offset,
            len(field_data),
            field_indices_offset,
            len(field_indices) * 4,
            list_indices_offset,
            len(list_indices) * 4,
        )
    )

    for struct_entry in structs:
        file.write(
            struct.pack(
                "<III",
                struct_entry.id,
                struct_entry.data_or_offset,
                struct_entry.field_count,
            )
        )

    for field_entry in fields:
        file.write(
            struct.pack(
                "<III",
                int(field_entry.type),
                field_entry.label_index,
                field_entry.data_or_offset,
            )
        )

    for label in labels:
        file.write(label)

    file.write(field_data)

    for index in field_indices:
        file.write(struct.pack("<I", index))

    for index in list_indices:
        file.write(struct.pack("<I", index))
