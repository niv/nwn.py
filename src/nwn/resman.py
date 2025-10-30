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

from collections import ChainMap

from nwn.environ import (
    get_install_directory,
    get_install_language_directory,
    get_user_directory,
    resolve_alias,
    Alias,
)
from nwn.res import Container
from nwn.resdir import LocalDirectory
from nwn.key import Reader as Key


class ResMan(ChainMap[str, bytes]):
    """
    A resource manager that chains multiple resource mappings together.

    This is currently a type alias for ChainMap[str, bytes] to indicate its
    intended use, but may be extended in the future; so make sure to use
    this type for foward compatibility.
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
        A ResMan containing all provided resource maps, plus the base game
        resource keys.

    Raises:
        FileNotFoundError: If any of the required directories cannot be found.
    """
    try:
        user = get_user_directory() if include_user else None
    except FileNotFoundError:
        user = None

    dataroot = get_install_directory() / "data"
    langdataroot = get_install_language_directory() / "data"

    retailkey = dataroot / "nwn_retail.key"
    # Not all installs have a retail.key (eg the headless server package)
    if not retailkey.is_file():
        retailkey = None

    langkey = langdataroot / "nwn_base_loc.key"
    # Not all language overrides have a keyfile
    if not langkey.is_file():
        langkey = None

    def loc_dir(alias: Alias) -> LocalDirectory | None:
        if not user:
            return None
        return LocalDirectory(resolve_alias(alias))

    stack = [
        *maps,
        # TEMPCLIENT: not used for our python impl
        loc_dir(Alias.PORTRAITS),
        loc_dir(Alias.PORTRAITSINSTALL),
        # DMVAULT: not enabled by default
        # LOCALVAULT: not enabled by default
        # SERVERVAULT: not enabled by default
        # DMVAULTINSTALL: not enabled by default
        # LCVAULTINSTALL: not enabled by default
        loc_dir(Alias.DEVELOPMENT),
        loc_dir(Alias.OVERRIDE),
        loc_dir(Alias.OVERRIDELOCINSTALL),
        # OVERRIDEINSTALL: not used since patch 37
        loc_dir(Alias.AMBIENT),
        loc_dir(Alias.AMBIENTINSTALL),
        loc_dir(Alias.MUSIC),
        loc_dir(Alias.MUSICINSTALL),
        Key(langkey) if langkey else None,
        Key(dataroot / "nwn_retail.key") if retailkey else None,
        Key(dataroot / "nwn_base.key"),
    ]
    return ResMan(*[s for s in stack if s is not None])
