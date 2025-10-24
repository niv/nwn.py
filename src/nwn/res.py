"""
Types and classes for ResMan (resource management) functionality.
"""

RESTYPE_MAP = {
    0: "res",
    1: "bmp",
    2: "mve",
    3: "tga",
    4: "wav",
    5: "wfx",
    6: "plt",
    7: "ini",
    8: "bmu",
    9: "mpg",
    10: "txt",
    2000: "plh",
    2001: "tex",
    2002: "mdl",
    2003: "thg",
    2005: "fnt",
    2007: "lua",
    2008: "slt",
    2009: "nss",
    2010: "ncs",
    2011: "mod",
    2012: "are",
    2013: "set",
    2014: "ifo",
    2015: "bic",
    2016: "wok",
    2017: "2da",
    2018: "tlk",
    2022: "txi",
    2023: "git",
    2024: "bti",
    2025: "uti",
    2026: "btc",
    2027: "utc",
    2029: "dlg",
    2030: "itp",
    2031: "btt",
    2032: "utt",
    2033: "dds",
    2034: "bts",
    2035: "uts",
    2036: "ltr",
    2037: "gff",
    2038: "fac",
    2039: "bte",
    2040: "ute",
    2041: "btd",
    2042: "utd",
    2043: "btp",
    2044: "utp",
    2045: "dft",
    2046: "gic",
    2047: "gui",
    2048: "css",
    2049: "ccs",
    2050: "btm",
    2051: "utm",
    2052: "dwk",
    2053: "pwk",
    2054: "btg",
    2055: "utg",
    2056: "jrl",
    2057: "sav",
    2058: "utw",
    2059: "4pc",
    2060: "ssf",
    2061: "hak",
    2062: "nwm",
    2063: "bik",
    2064: "ndb",
    2065: "ptm",
    2066: "ptt",
    2067: "bak",
    2068: "dat",
    2069: "shd",
    2070: "xbc",
    2071: "wbm",
    2072: "mtr",
    2073: "ktx",
    2074: "ttf",
    2075: "sql",
    2076: "tml",
    2077: "sq3",
    2078: "lod",
    2079: "gif",
    2080: "png",
    2081: "jpg",
    2082: "caf",
    2083: "jui",
    9996: "ids",
    9997: "erf",
    9998: "bif",
    9999: "key",
    0xFFFF: "___",
}


def restype_to_extension(restype: int) -> str:
    """
    Convert a resource type to its corresponding file extension.

    Args:
        restype: The resource type to convert.

    Returns:
        The corresponding file extension for the given resource type.

    Raises:
        ValueError: If the given resource type is unknown.
    """
    try:
        return RESTYPE_MAP[restype]
    except KeyError as e:
        raise ValueError(f"Unknown restype: {restype}") from e


def extension_to_restype(extension: str) -> int:
    """
    Convert a file extension to its corresponding resource type identifier.

    Args:
        extension: The file extension to convert.

    Returns:
        The resource type identifier corresponding to the given extension.

    Raises:
        ValueError: If the extension is not recognized.
    """

    try:
        return {v: k for k, v in RESTYPE_MAP.items()}[extension.lower()]
    except KeyError as e:
        raise ValueError(f"Unknown extension: {extension}") from e


def is_valid_resref(f: str) -> bool:
    """
    Check if a given filename is a valid NWN resref.

    Args:
        f: The filename to check.

    Returns:
        True if the filename is a valid resref, False otherwise.
    """
    if "/" in f or "\\" in f or f.count(".") != 1:
        return False
    name, ext = f.rsplit(".", 1)
    if len(name) > 16 or not name:
        return False
    try:
        extension_to_restype(ext)
        return True
    except ValueError:
        return False
