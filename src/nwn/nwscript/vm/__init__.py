"""
A VM that can run NWScript bytecode with bidirectional Python linkage.

This module is very, very preliminary. Expect the types to move and change.

Example:
    >>> from nwn.nwscript.vm import VM, Script
    ... from nwn.nwscript import langspec
    ...
    ... class Impl:
    ...     def Random(self, nMax) -> int:
    ...         return nMax + 1
    ...
    ... script = Script.from_compiled("test")  # requires test.{ncs,nss}
    ... with open("nwscript.nss", "r") as nws:
    ...     spec = langspec.read(nws)
    ... vm = VM(script=script, spec=spec, impl=Impl())
    ... proxy = vm.proxy()
    ...
    ... assert vm.some_func(5) == 42
    ... assert vm.some_func2() == {"a": 42, "b": 3.14, "c": "Hellorld"}

Contents of ``test.nss``; compile with ndb (-g):

    .. code-block:: c

        struct Testing { int a; float b; string c; };

        int some_func() { return Random(41); }

        struct Testing some_func2() {
            struct Testing t;
            t.a = 42;
            t.b = 3.14;
            t.c = "Hellorld";
            return t;
        }

        void main() {}

"""

from ._stack import Stack
from ._script import Script
from ._vm import VM

__all__ = [
    "Stack",
    "Script",
    "VM",
]
