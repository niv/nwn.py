"""Shared types and helpers useful across the whole library."""

from enum import IntEnum, StrEnum
from dataclasses import dataclass
from typing import NamedTuple


class Language(IntEnum):
    """Maps engine language IDs."""

    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5

    @property
    def code(self) -> str:
        """Get the two-letter language code."""
        return {
            Language.ENGLISH: "en",
            Language.FRENCH: "fr",
            Language.GERMAN: "de",
            Language.ITALIAN: "it",
            Language.SPANISH: "es",
            Language.POLISH: "pl",
        }[self]

    @classmethod
    def from_code(cls, code: str) -> "Language":
        """
        Get the Language enum from a two-letter code.

        Args:
            code: The two-letter language code (eg. "de").

        Returns:
            The corresponding Language enum.

        Raises:
            ValueError: If the code is unknown.
        """
        for lang in cls:
            if lang.code == code.lower():
                return lang
        raise ValueError(f"Unknown language code: {code}")


class CodePage(StrEnum):
    """Maps engine code page names."""

    CP1250 = "cp1250"
    CP1251 = "cp1251"
    CP1252 = "cp1252"

    @classmethod
    def from_language(cls, lang: Language) -> "CodePage":
        """
        Get the default codepage for a given language.

        Args:
            lang: The Language enum.

        Returns:
            The corresponding CodePage enum.

        Raises:
            ValueError: If the language is unknown.
        """
        match lang:
            case (
                Language.ENGLISH
                | Language.FRENCH
                | Language.GERMAN
                | Language.ITALIAN
                | Language.SPANISH
            ):
                return cls.CP1252
            case Language.POLISH:
                return cls.CP1250
        raise ValueError(f"Unknown language: {lang}")


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


class Platform(IntEnum):
    """
    Game platform IDs, as used in various file formats and network messages.
    """

    INVALID = 0
    WINDOWS_X86 = 1
    WINDOWS_X64 = 2

    LINUX_X86 = 10
    LINUX_X64 = 11
    LINUX_ARM32 = 12
    LINUX_ARM64 = 13

    MAC_X86 = 20
    MAC_X64 = 21
    MAC_ARM64 = 22

    IOS = 30

    ANDROID_ARM32 = 40
    ANDROID_ARM64 = 41
    ANDROID_X64 = 42

    NINTENDO_SWITCH = 50

    MICROSOFT_XBOXONE = 60

    SONY_PS4 = 70


class Vector(NamedTuple):
    """
    A 3D vector in the game world.

    Vectors are always immutable, just like in the game engine.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
