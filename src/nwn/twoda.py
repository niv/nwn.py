"""
This module provides functionality to read and write 2DA files.
"""

from typing import TextIO

_MAGIC = "2DA V2.0"

CELL = str | None
r"""A type alias for a cell value, which can be a string or None (\*\*\*\*)."""


def _escape_cell(cell: CELL):
    if cell is None:
        return "****"
    if " " in cell:
        return f'"{cell}"'
    return cell


def _split_twoda_style(line: str) -> list[CELL]:
    in_quotes = False
    current = []
    result = []
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char.isspace() and not in_quotes:
            if current:
                result.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        result.append("".join(current))
    return result


class DictReader:
    def __init__(self, columns, f):
        self._columns = columns
        self._f = f

    @property
    def columns(self):
        return self._columns

    def __iter__(self):
        return self

    def __next__(self):
        ln = self._f.readline()
        if not ln:
            raise StopIteration
        ln = _split_twoda_style(ln.strip())
        # First cell is the row number, which canonically gets discarded
        ln.pop(0)
        ln = [None if x == "****" else x for x in ln]
        # Fill in None values for missing columns
        ln = ln + [None] * (len(self._columns) - len(ln))
        return dict(zip(self._columns, ln))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._f.close()


def read(file: TextIO):
    """
    Reads a 2DA file and returns a DictReader object.

    Example:
        >>> with open("file.2da", "r") as f:
        ...     for row in twoda.read(f):
        ...         print(row)

    Args:
        file: The 2DA file to read.

    Returns:
        DictReader: An object that allows reading the 2DA file as a dictionary.

    Raises:
        ValueError: Parse/format errors.
    """

    def fetch():
        ln = file.readline()
        if ln is None:
            raise ValueError("Unexpected EOF")
        return ln.strip()

    head = fetch()
    if head != _MAGIC:
        raise ValueError("Not a 2DA file")

    if fetch() != "":
        raise ValueError("Expected empty line after magic")

    columns = fetch().split()

    if not columns:
        raise ValueError("No columns found")

    return DictReader(columns=columns, f=file)


class DictWriter:
    def __init__(self, columns, f):
        self._columns = columns
        self._f = f
        self._idx = 0
        f.write(_MAGIC + "\n\n")
        f.write(" " + " ".join(columns) + "\n")

    def add_row(self, row: dict[str, CELL]):
        self._f.write(
            str(self._idx)
            + " "
            + " ".join(_escape_cell(row.get(h)) for h in self._columns)
            + "\n"
        )
        self._idx += 1


def write(file: TextIO, columns: list[str]) -> DictWriter:
    """
    Writes data to a file using the specified columns.

    Example:
        >>> with open("file.2da", "w") as f:
        ...     writer = twoda.write(f, ["col1", "col2"])
        ...     writer.add_row({"col1": "foo", "col2": "bar"})
        ...     writer.add_row({"col1": "baz", "col2": "qux"})

    Args:
        file: The file object where the data will be written.
        columns: A list of column names to be used in the output file.

    Returns:
        DictWriter: An instance of DictWriter initialized with the given columns and file.
    """

    return DictWriter(columns=columns, f=file)
