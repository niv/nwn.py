"""
A NWN-like resman implementation.

Allows stacking resources origins with ChainMap semantics with similar lookup
behaviour to the NWN engine.

The provided default implementation will correctly look up user-configured
aliases. If you do not want this behaviour, you can create your own
ResMan/ChainMap by combining your own resource containers; or you can override
the env var NWN_ROOT/NWN_HOME to point to a custom installation/user directory.

Example:

    >>> from nwn.erf import Reader as ErfReader
    ... from nwn.res import ResDict
    ... from nwn.resdir import ResDir
    ... from nwn.resman import create as create_resman
    ...
    ... module_erf = ErfReader("mymodule.erf")
    ... inmem = ResDict()
    ... rm = create_resman(inmem, ResDir("local_dir"), module_erf)
    ...
    ... ifo = rm["module.ifo"]         # from mymodule.erf
    ... nss = rm["nwscript.nss"]       # from retail keyfile
    ... rm["temp.txt"] = b"SomeData"   # writes to inmem dict

"""

import os
from collections import ChainMap

from nwn.environ import (
    get_install_directory,
    get_user_directory,
    get_language,
    resolve_alias,
)
from nwn.res import Container
from nwn.resdir import LocalDirectory
from nwn.key import Reader as Key


class ResMan(ChainMap[str, bytes]):
    """
    A resource manager that chains multiple resource mappings together.

    This is currently a type alias for ChainMap[str, bytes] to indicate its
    intended use.
    """


def create(*maps: Container, include_user: bool = True) -> ResMan:
    """
    Create a default resman instance containing all base and user game data,
    in addition to any additional resource maps provided. Uses the environment
    to locate NWN installation and user directories.

    Hint: If you want to create a resman that can also store data, prefix
    your maps chain with a ResDict() instance (for in-memory storage or
    a ResDir(..., writable=True) instance pointing to a writable directory).

    Args:
        maps: Additional resource maps to include in the resman, in order of
            precedence (first has highest precedence).
        include_user: Whether to include the user directory aliases.

    Returns:
        A ChainMap containing all provided resource maps, plus the base game
        resource keys.

    Raises:
        FileNotFoundError: If any of the required directories cannot be found.
    """
    install = get_install_directory()
    try:
        user = get_user_directory() if include_user else None
    except FileNotFoundError:
        user = None
    language = get_language()
    dataroot = os.path.join(install, "data")
    langdataroot = os.path.join(install, "lang", language.code, "data")

    langkey = os.path.join(langdataroot, "nwn_base_loc.key")
    if not os.path.isfile(langkey):
        langkey = None

    def make_root_resdir(path: str) -> LocalDirectory:
        return LocalDirectory(os.path.join(dataroot, path))

    def make_lang_resdir(path: str) -> LocalDirectory:
        return LocalDirectory(os.path.join(langdataroot, path))

    def make_user_aliasdir(alias: str) -> LocalDirectory | None:
        return LocalDirectory(resolve_alias(alias)) if user else None

    stack = [
        *maps,
        # TEMPCLIENT: not used for our python impl
        make_user_aliasdir("PORTRAITS"),
        make_root_resdir("prt"),
        # DMVAULT: not enabled by default
        # LOCALVAULT: not enabled by default
        # SERVERVAULT: not enabled by default
        # DMVAULTINSTALL: not enabled by default
        # LCVAULTINSTALL: not enabled by default
        make_user_aliasdir("DEVELOPMENT"),
        make_user_aliasdir("OVERRIDE"),
        make_lang_resdir("ovr"),
        # OVERRIDEINSTALL: not used since patch 37
        make_user_aliasdir("AMBIENT"),
        make_root_resdir("amb"),
        make_user_aliasdir("MUSIC"),
        make_root_resdir("mus"),
        Key(langkey) if langkey else None,
        Key(os.path.join(dataroot, "nwn_retail.key")),
        Key(os.path.join(dataroot, "nwn_base.key")),
    ]
    return ResMan(*[s for s in stack if s])
