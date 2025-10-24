"""Shared types useful across the whole library."""

from dataclasses import dataclass
from enum import IntEnum


class Language(IntEnum):
    """Maps engine language IDs."""

    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5


class Gender(IntEnum):
    """Maps engine gender IDs."""

    MALE = 0
    FEMALE = 1


@dataclass(frozen=True)
class GenderedLanguage:
    """
    A combination of Language and Gender.

    This type is needed for various file formats, where the Language and Gender
    types are combined into a single integer.
    """

    lang: Language
    gender: Gender

    def __str__(self):
        return f"{self.lang.name} {self.gender.name}"

    @classmethod
    def from_id(cls, combined_id: int):
        """
        Create a new GenderedLanguage instance from a combined ID.

        Args:
            combined_id: The combined ID, which is 2 times the Language ID plus the Gender.

        Returns:
            A new GenderedLanguage instance.
        """
        lang = Language(combined_id // 2)
        gender = Gender(combined_id % 2)
        return GenderedLanguage(lang, gender)

    def to_id(self) -> int:
        """
        Convert the Language instance to a combined ID.

        Returns:
            The combined ID, which is 2 times the Language ID plus the Gender.
        """
        return self.lang * 2 + self.gender


class FileMagic(bytes):
    """
    A file magic identifies a file type: For NWN, it is the first four characters
    on certain file types.

    Args:
        value: Exactly 4 characters or bytes.

    Raises:
        ValueError: If the input is not exactly 4 bytes long.
    """

    def __new__(cls, value: str | bytes | memoryview):
        if isinstance(value, str):
            value = value.encode("ascii")
        if isinstance(value, memoryview):
            value = value.tobytes()
        if len(value) > 4:
            raise ValueError("Magic must be at most 4 bytes long")
        value = value.ljust(4, b" ")
        if not all(c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " for c in value):
            raise ValueError(
                "Magic must contain only ASCII uppercase letters, digits, or spaces"
            )
        return super().__new__(cls, value)
