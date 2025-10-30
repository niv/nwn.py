"""
Functionality related to game and user/system environment,
such as locating installation directories and detecting
language and codepage.
"""

import os
import tomllib
import configparser
import locale
import platform
from functools import cache
from typing import Any

from .types import Language, CodePage


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
        return dict(config["Alias"])
    except KeyError:
        return {}


@cache
def resolve_alias(alias: str) -> str:
    """
    Get the path for a given NWN alias from nwn.ini, or return the
    default value if not found.

    Currently only works for user directory aliases, not install or locinstall.

    Args:
        alias: The alias to look up.

    Returns:
        The resolved path for the alias, or the default value.

    Raises:
        FileNotFoundError: If the user directory cannot be found. This function
            requires a user directory set up already.
    """
    aliases = _get_aliases()
    return aliases.get(alias.upper(), os.path.join(get_user_directory(), alias.lower()))


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
def get_user_directory() -> str:
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
            return candidate

    raise FileNotFoundError("Could not locate NWN user directory; try setting NWN_HOME")


@cache
def get_install_directory() -> str:
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
            return candidate

    raise FileNotFoundError("Could not locate NWN; try setting NWN_ROOT")


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
