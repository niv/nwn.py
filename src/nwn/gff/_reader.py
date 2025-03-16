import struct
from typing import BinaryIO


from nwn.shared import get_nwn_encoding, CExoLocString
from nwn.gff._types import (
    Byte,
    Char,
    Word,
    Short,
    Dword,
    Int,
    Float,
    CExoString,
    ResRef,
    Struct,
    List,
)
from nwn.gff._impl import FieldKind, Header, FieldEntry, StructEntry


def read(file: BinaryIO):
    """
    Read a GFF data from a binary stream.

    Args:
        file: The binary stream to read from.

    Returns:
        (Struct, str): The root structure of the GFF file and the file type.
    """

    root_offset = file.tell()
    labels = []
    fields = []
    structs = []
    list_indices = []
    field_indices = []
    resolved_structs = {}
    struct_parents = {}

    header = Header(
        file.read(4).decode("ascii"),
        file.read(4).decode("ascii"),
        *struct.unpack("<12i", file.read(48)),
    )
    if header.file_version != "V3.2":
        raise ValueError(f"Unsupported GFF version: {header.file_version}")

    file.seek(root_offset + header.label_offset)
    for _ in range(header.label_count):
        labels.append(file.read(16).split(b"\x00")[0].decode("ascii"))

    file.seek(root_offset + header.field_offset)
    for _ in range(header.field_count):
        data = struct.unpack("<III", file.read(12))
        fields.append(FieldEntry(FieldKind(data[0]), data[1], data[2]))

    file.seek(root_offset + header.field_indices_offset)
    for _ in range(header.field_indices_size // 4):
        field_indices.append(struct.unpack("<I", file.read(4))[0])

    file.seek(root_offset + header.list_indices_offset)
    for _ in range(header.list_indices_size // 4):
        list_indices.append(struct.unpack("<I", file.read(4))[0])

    file.seek(root_offset + header.struct_offset)
    for _ in range(header.struct_count):
        data = struct.unpack("<III", file.read(12))
        structs.append(StructEntry(data[0], data[1], data[2]))

    def _read_field_value(field):
        simple_types = {
            FieldKind.BYTE: ("B", Byte),
            FieldKind.CHAR: ("b", Char),
            FieldKind.WORD: ("H", Word),
            FieldKind.SHORT: ("h", Short),
            FieldKind.DWORD: ("I", Dword),
            FieldKind.INT: ("i", Int),
            FieldKind.FLOAT: ("f", Float),
        }

        if field.type in simple_types:
            us, cls = simple_types[field.type]
            data = struct.pack("<I", field.data_or_offset)[: struct.calcsize(us)]
            up = struct.unpack("<" + us, data)
            return cls(up[0])

        file.seek(root_offset + header.field_data_offset + field.data_or_offset)

        if field.type == FieldKind.CEXOSTRING:
            sz = struct.unpack("<I", file.read(4))[0]
            if sz > 0xFFFF:
                raise ValueError("String too long")
            return CExoString(file.read(sz).decode(get_nwn_encoding()))

        if field.type == FieldKind.RESREF:
            sz = struct.unpack("<b", file.read(1))[0]
            if sz > 16:
                raise ValueError("Resref too long")
            return ResRef(file.read(sz).decode(get_nwn_encoding()))

        if field.type == FieldKind.CEXOLOCSTRING:
            _ = struct.unpack("<I", file.read(4))[0]
            strref = struct.unpack("<I", file.read(4))[0]
            count = struct.unpack("<I", file.read(4))[0]
            entries = {}
            for _ in range(count):
                fid = struct.unpack("<I", file.read(4))[0]
                sz = struct.unpack("<I", file.read(4))[0]
                entries[fid] = file.read(sz).decode(get_nwn_encoding())
            return CExoLocString(strref, entries)

        if field.type == FieldKind.LIST:
            offset = field.data_or_offset // 4
            size = list_indices[offset]
            start = offset + 1
            end = start + size

            return List(*[_read_struct(field, lid) for lid in list_indices[start:end]])

        if field.type == FieldKind.STRUCT:
            return _read_struct(field, field.data_or_offset)

        raise NotImplementedError(f"Field type {field.type} not implemented")

    def _read_struct(parent, struct_idx) -> Struct:
        if struct_idx in resolved_structs:
            if struct_parents[struct_idx] != parent:
                raise ValueError("Struct already resolved with different parent")
            return resolved_structs[struct_idx]

        struct_entry = structs[struct_idx]

        if struct_entry.field_count == 1:
            field_array_indices = [struct_entry.data_or_offset]
        else:
            start = struct_entry.data_or_offset // 4
            end = start + struct_entry.field_count
            if end < start:
                raise ValueError("Field index array out of bounds")

            field_array_indices = field_indices[start:end]

        resolved_structs[struct_idx] = Struct(
            struct_entry.id,
            **{
                labels[fld.label_index]: _read_field_value(fld)
                for fld in map(lambda x: fields[x], field_array_indices)
            },
        )

        struct_parents[struct_idx] = parent
        return resolved_structs[struct_idx]

    root = _read_struct(None, 0)
    return root, header.file_type
