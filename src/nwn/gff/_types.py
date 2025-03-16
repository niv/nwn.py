class Byte(int):
    def __new__(cls, value):
        if not 0 <= value <= 255:
            raise ValueError(f"BYTE value out of bounds: {value}")
        return super().__new__(cls, value)


class Char(int):
    def __new__(cls, value):
        if not -128 <= value <= 127:
            raise ValueError(f"CHAR value out of bounds: {value}")
        return super().__new__(cls, value)


class Word(int):
    def __new__(cls, value):
        if not 0 <= value <= 65535:
            raise ValueError(f"WORD value out of bounds: {value}")
        return super().__new__(cls, value)


class Short(int):
    def __new__(cls, value):
        if not -32768 <= value <= 32767:
            raise ValueError(f"SHORT value out of bounds: {value}")
        return super().__new__(cls, value)


class Dword(int):
    def __new__(cls, value):
        if not 0 <= value <= 4294967295:
            raise ValueError(f"DWORD value out of bounds: {value}")
        return super().__new__(cls, value)


class Int(int):
    def __new__(cls, value):
        if not -2147483648 <= value <= 2147483647:
            raise ValueError(f"INT value out of bounds: {value}")
        return super().__new__(cls, value)


class Dword64(int):
    def __new__(cls, value):
        if not 0 <= value <= 18446744073709551615:
            raise ValueError(f"DWORD64 value out of bounds: {value}")
        return super().__new__(cls, value)


class Int64(int):
    def __new__(cls, value):
        if not -9223372036854775808 <= value <= 9223372036854775807:
            raise ValueError(f"INT64 value out of bounds: {value}")
        return super().__new__(cls, value)


class Float(float):
    pass


class Double(float):
    pass


class CExoString(str):
    pass


class ResRef(str):
    def __new__(cls, value):
        if len(value) > 16:
            raise ValueError(f"ResRef value too long: {value}")
        return super().__new__(cls, value)


class Struct(dict):
    """GFF Structs are just python dicts with .attr access and some metadata."""

    def __init__(self, struct_id, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_struct_id", struct_id)

    @property
    def struct_id(self):
        """The struct ID of the struct."""
        return object.__getattribute__(self, "_struct_id")

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            ) from exc

    def __setattr__(self, name, value):
        self[name] = value


class List(list[Struct]):
    """
    GFF Lists are just python lists of Structs. They carry no metadata.

    This class exists as a convenience for type checking and
    future extensibility.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
