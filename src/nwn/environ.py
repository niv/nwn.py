"""
Functionality related to game and user/system environment,
such as locating installation directories and detecting
language and codepage.

Note that most functions here rely on caching to avoid repeated
filesystem access; if you modify environment variables or
configuration files during runtime, you may need to clear
the relevant function caches using functools.cache_clear(). This
will typically only be necessary during testing, is not considered
part of the public API, and will likely change in a future version.
"""

import os
import tomllib
import configparser
import locale
import platform
from pathlib import Path
from typing import Any
from enum import StrEnum

# I'm not overly fond of this. The internal cache system is currently necessary
# for performance, but it might be replaced in the future with more explicit
# control over caching. Caveat empor if you decide to use it in your code.
from functools import cache

from .types import Language, CodePage


class Alias(StrEnum):
    HD0 = "_hd0"  # NWN_HOME
    MODULES = "modules"
    SAVES = "saves"
    OVERRIDE = "override"
    DEVELOPMENT = "development"
    HAK = "hak"
    SCREENSHOTS = "screenshots"
    CURRENTGAME = "currentgame"
    LOGS = "logs"
    TEMP = "temp"
    TEMPCLIENT = "tempclient"
    PATCH = "patch"
    LOCALVAULT = "localvault"
    DMVAULT = "dmvault"
    SERVERVAULT = "servervault"
    OLDSERVERVAULT = "oldservervault"
    DATABASE = "database"
    PORTRAITS = "portraits"
    AMBIENT = "ambient"
    MOVIES = "movies"
    MUSIC = "music"
    TLK = "tlk"
    NWSYNC = "nwsync"
    CACHE = "cache"
    MODELCOMPILER = "modelcompiler"
    CRASHREPORT = "crashreport"

    HD0INSTALL = "_hd0install"  # NWN_ROOT
    PORTRAITSINSTALL = "data/prt"
    MOVIESINSTALL = "data/mov"
    MUSICINSTALL = "data/mus"
    AMBIENTINSTALL = "data/amb"
    PATCHINSTALL = "data/pat"
    PREMIUMINSTALL = "data/prem"
    MODULESINSTALL = "data/mod"
    NWMINSTALL = "data/nwm"
    LCVAULTINSTALL = "data/lcv"
    DMVAULTINSTALL = "data/dmv"
    HAKINSTALL = "data/hk"
    TLKINSTALL = "data/tlk"

    HD0LOCINSTALL = "_hd0locinstall"  # NWN_ROOT / lang
    MOVIESLOCINSTALL = "data/mov"
    TLKLOCINSTALL = "data/tlk"
    OVERRIDELOCINSTALL = "data/ovr"

    @classmethod
    def by_name(cls, name: str) -> "Alias":
        """
        Get the Alias enum from a string name.

        Args:
            name: The alias name (e.g. "MODULES").

        Returns:
            The corresponding Alias enum.

        Raises:
            ValueError: If the name is unknown.
        """
        for alias in cls:
            if alias.value.upper() == name.upper():
                return alias
        raise ValueError(f"{name} is not a valid Alias")


@cache
def _get_settings_tml() -> dict:
    try:
        user = get_user_directory()
        settings_path = os.path.join(user, "settings.tml")
        with open(settings_path, "rb") as settings:
            return tomllib.load(settings)
    except FileNotFoundError:
        pass
    return {}


@cache
def _get_aliases() -> dict:
    try:
        user = get_user_directory()
        ini_path = os.path.join(user, "nwn.ini")
        config = configparser.ConfigParser()
        config.read(ini_path)
        return {k.upper(): v for k, v in config["Alias"].items()}
    except KeyError:
        return {}


@cache
def resolve_alias(alias: str | Alias) -> Path:
    """
    Get the path for a given NWN alias from nwn.ini, or return the
    default value if not found.

    Args:
        alias: The alias to look up.

    Returns:
        The resolved path for the alias, or the default value.

    Raises:
        FileNotFoundError: If the user directory cannot be found. This function
            requires a user directory set up already.
    """

    if isinstance(alias, str):
        alias = Alias.by_name(alias)

    if alias == Alias.HD0:
        return get_user_directory()
    if alias == Alias.HD0INSTALL:
        return get_install_directory()
    if alias == Alias.HD0LOCINSTALL:
        return get_install_language_directory()

    value = alias.value.lower()

    if alias.name.endswith("LOCINSTALL"):
        return get_install_language_directory() / "data" / value

    if alias.name.endswith("INSTALL"):
        return get_install_directory() / "data" / value

    return get_user_directory() / _get_aliases().get(alias.name.upper(), value)


@cache
def get_setting(key: str) -> Any:
    """
    Get a setting from the user's settings.tml file.

    Args:
        key: The setting key to look up, in dot notation (e.g. "game.language.override").

    Returns:
        The setting value, or None if not found.

    Raises:
        FileNotFoundError: If the user directory cannot be found. This function
            requires a user directory set up already.
    """
    settings = _get_settings_tml()
    parts = key.split(".")
    current = settings
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


@cache
def get_user_directory() -> Path:
    """
    Find the current user NWN directory.

    The search can be overridden by setting the NWN_HOME or NWN_USER_DIRECTORY
    environment variables.

    Returns:
        The path to the NWN user directory.

    Raises:
        FileNotFoundError: If the directory cannot be found.
    """

    candidates = [
        os.environ.get("NWN_HOME"),
        os.environ.get("NWN_USER_DIRECTORY"),
    ]

    # We never expose system dirs to pytest, just to avoid it clobbering
    # user data and to make tests reproducible.
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        if platform.system() in ("Windows", "Darwin"):
            candidates.append(os.path.expanduser("~/Documents/Neverwinter Nights"))
        else:
            candidates.append(os.path.expanduser("~/.local/share/Neverwinter Nights"))

    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return Path(candidate)

    raise FileNotFoundError("Could not locate NWN user directory; try setting NWN_HOME")


@cache
def get_install_directory() -> Path:
    """
    Find the first matching NWN installation directory.
    Currently only supports searching for Steam installs.

    The search can be overridden by setting the NWN_ROOT environment variable.

    Returns:
        The path to the NWN root directory.

    Raises:
        FileNotFoundError: If the directory cannot be found.
    """

    candidates = [
        os.environ.get("NWN_ROOT"),
    ]

    # We never expose system dirs to pytest, just to avoid it clobbering
    # user data and to make tests reproducible.
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        suffix = "/Steam/steamapps/common/Neverwinter Nights/"
        if platform.system() == "Windows":
            candidates.append("c:/program files (x86)/" + suffix)
        elif platform.system() == "Darwin":
            candidates.append(
                os.path.expanduser("~/Library/Application Support/" + suffix)
            )
        else:
            candidates.append(os.path.expanduser("~/.local/share/" + suffix))

    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return Path(candidate)

    raise FileNotFoundError("Could not locate NWN; try setting NWN_ROOT")


def get_install_language_directory() -> Path:
    """
    Get the path to the language data directory inside the NWN installation.

    Returns:
        The path to the language data directory.

    Raises:
        FileNotFoundError: If the installation directory cannot be found.
    """
    install = get_install_directory()
    language = get_language()
    return install / "lang" / language.code


@cache
def get_codepage() -> CodePage:
    """
    Detect the codepage used by the NWN installation based on the user
    language.

    The codepage can be overridden by setting the NWN_CODEPAGE environment variable.

    Returns:
        The codepage specified in settings.tml, or defaults based on language.
    """
    try:
        cp = os.environ.get("NWN_CODEPAGE", get_setting("game.language.codepage"))
    except FileNotFoundError:
        cp = None
    try:
        if not cp:
            cp = CodePage.from_language(get_language())
        return CodePage(cp)
    except ValueError:
        return CodePage.CP1252


@cache
def get_language() -> Language:
    """
    Detect the language of the NWN installation based on system locale
    or configuration inside game settings.

    Returns:
        The detected Language enum value, or english by default.
    """

    lang = os.environ.get("NWN_LANGUAGE")

    if not lang:
        try:
            lang = get_setting("game.language.override")
        except FileNotFoundError:
            lang = None

    if not lang:
        if loc := locale.getlocale()[0]:
            lang = loc.split("_")[0]

    try:
        return Language.from_code(lang or "en")
    except ValueError:
        return Language.ENGLISH
