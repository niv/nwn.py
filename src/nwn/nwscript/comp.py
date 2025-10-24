"""
Bindings for the official nwn script compiler.

The compiler depends on a native library. This package ships with precompiled
binaries for MacOS, Windows and Linux both on X64 and ARM64 architectures.

This module or the underlying library is currently NOT threadsafe.

Example:
    >>> from nwn.nwscript.comp import Compiler
    ...
    ... def resolver(filename: str) -> bytes | None:
    ...     # Load the file from disk, or return None if not found.
    ...     # You can also service from memory, or anywhere else.
    ...     with open(filename, "rb") as f:
    ...         return f.read()
    ... comp = Compiler(resolver)
    >>> ncs, ndb = comp.compile("myscript.nss")
    >>> print(ncs)  # The compiled bytecode
    >>> print(ndb)  # The debug information

"""

import os
import platform
import ctypes as ct
from ctypes.util import find_library
from typing import Callable
from enum import IntEnum

from nwn.res import restype_to_extension
from nwn.environ import get_codepage


_CB_WRITE = ct.CFUNCTYPE(
    ct.c_int32,
    ct.c_char_p,
    ct.c_uint16,
    ct.c_void_p,
    ct.c_size_t,
    ct.c_bool,
)

_CB_LOAD = ct.CFUNCTYPE(
    ct.c_char_p,
    ct.c_char_p,
    ct.c_uint16,
)


class Optimization(IntEnum):
    DEAD_FUNCTIONS = 0x00000001
    MELD_INSTRUCTIONS = 0x00000002
    DEAD_BRANCHES = 0x00000004


class _NativeCompileResult(ct.Structure):
    _fields_ = [
        ("code", ct.c_int32),
        ("str", ct.c_char_p),
    ]


class CompilationError(Exception):
    """Exception raised for errors in the compilation process."""

    def __init__(self, code: int, message: str):
        assert code != 0
        super().__init__()
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.message} ({self.code})"


class Compiler:
    """A class to compile NWScript using the NWScript compiler."""

    _instance: ct.CDLL | None = None

    def __init__(
        self,
        resolver: Callable[[str], str | bytes | None],
        src_rt=2009,  # nss
        bin_rt=2010,  # ncs
        dbg_rt=2064,  # ndb
        langspec=b"nwscript",
        debug_info=True,
        max_include_depth=16,
        encoding=None,
        optimizations: set[Optimization] | int | None = None,
    ):
        """
        Create a new compiler instance.

        This will load the compiler library, and immediately request the langspec
        file (e.g. nwscript.nss).

        Re-use the compiler instance for increased performance.

        Args:
            resolver: A callable that resolves the filename to a str, or None.
                The filename will always have the source restype extension appended.
                (e.g. "myscript.nss", not "myscript").
            src_rt: The resource type for the source file.
            bin_rt: The resource type for the binary file.
            dbg_rt: The resource type for the debug file.
            langspec: The language specification.
            debug_info: Whether to write debug information.
                Generating NDB is usually cheap and useful for debugging, so
                the recommendation is to generate and store this info alongside
                the NCS file.
            max_include_depth: The maximum include depth.
            encoding: The encoding to use for filenames (defaults to the configured
                nwn encoding).
            optimizations: A set of optimizations to apply. The default is
                to use whatever the linked library defaults to.

        Raises:
            FileNotFoundError: If the library cannot not be found, either bundled
                or in the system library path.
            OSError: If the library could not be loaded.
        """

        self._resolver = resolver
        self._ncs = None
        self._ndb = None
        self._comp = None
        self._src_rt = src_rt
        self._bin_rt = bin_rt
        self._dbg_rt = dbg_rt
        self._src_ext = restype_to_extension(src_rt)
        self._bin_ext = restype_to_extension(bin_rt)
        self._dbg_ext = restype_to_extension(dbg_rt)
        self._encoding = encoding or get_codepage()

        self._lib = Compiler._load_library()

        def cb_write(*args):
            return self._write_file(*args)

        def cb_load(*args):
            return self._load_file(*args)

        self._cb_write = _CB_WRITE(cb_write)
        self._cb_load = _CB_LOAD(cb_load)
        self._comp = self._lib.scriptCompApiNewCompiler(
            src_rt,
            bin_rt,
            dbg_rt,
            self._cb_write,
            self._cb_load,
        )

        # NB: This will trigger the first request, for "nwscript.nss".
        self._lib.scriptCompApiInitCompiler(
            self._comp,
            langspec,
            debug_info,
            max_include_depth,
            None,
            b"scriptout",
        )

        if optimizations is not None:
            if isinstance(optimizations, int):
                opt = optimizations
            elif isinstance(optimizations, set):
                opt = sum(o.value for o in optimizations)
            else:
                raise TypeError(f"Invalid optimizations type: {type(optimizations)}")

            self._lib.scriptCompApiSetOptimizationFlags(self._comp, opt)

    @classmethod
    def _load_library(cls) -> ct.CDLL:
        if cls._instance:
            return cls._instance

        sys = platform.system().lower()
        if sys == "darwin":
            sys = "macos"
        arch = platform.machine().lower()
        if arch == "arm64":
            arch = "aarch64"
        if arch == "amd64":
            arch = "x86_64"
        ext = "so" if sys == "linux" else "dll" if sys == "windows" else "dylib"

        root_fn = "nwnscriptcomp"
        lib_path = os.path.join(
            os.path.dirname(__file__),
            "lib",
            f"{sys}_{arch}",
            f"lib{root_fn}.{ext}",
        )

        if not lib_path or not os.path.exists(lib_path):
            lib_path = find_library(root_fn)

        if not lib_path or not os.path.exists(lib_path):
            raise FileNotFoundError(
                "Could not find libscriptcomp (no builtin, no system)"
            )

        cls._instance = ct.cdll.LoadLibrary(lib_path)

        if not cls._instance or not cls._instance._name:
            raise OSError("Could not load libscriptcomp (failed to instance)")

        lib = cls._instance

        abiver = lib.scriptCompApiGetABIVersion()
        if abiver != 1:
            raise ImportError(f"ABI version mismatch: {abiver} != 1")

        fn_newcomp = lib.scriptCompApiNewCompiler
        fn_newcomp.argtypes = [
            ct.c_int,  # src
            ct.c_int,  # bin
            ct.c_int,  # dbg
            _CB_WRITE,
            _CB_LOAD,
        ]
        fn_newcomp.restype = ct.c_void_p

        fn_initcomp = lib.scriptCompApiInitCompiler
        fn_initcomp.argtypes = [
            ct.c_void_p,  # compiler
            ct.c_char_p,  # lang
            ct.c_bool,  # writeDebug
            ct.c_int,  # maxIncludeDepth
            ct.c_char_p,  # graphvizOut
            ct.c_char_p,  # outputAlias
        ]

        fn_compile = lib.scriptCompApiCompileFile
        fn_compile.argtypes = [
            ct.c_void_p,  # compiler
            ct.c_char_p,  # filename
        ]
        fn_compile.restype = _NativeCompileResult

        fn_deliver_file = lib.scriptCompApiDeliverFile
        fn_deliver_file.argtypes = [
            ct.c_void_p,  # compiler
            ct.c_void_p,  # data
            ct.c_size_t,  # size
        ]

        fn_destroycomp = lib.scriptCompApiDestroyCompiler
        fn_destroycomp.argtypes = [
            ct.c_void_p,  # compiler
        ]

        fn_setopt = lib.scriptCompApiSetOptimizationFlags
        fn_setopt.argtypes = [
            ct.c_void_p,  # compiler
            ct.c_int,  # flags
        ]

        return lib

    def __del__(self):
        if self._comp:
            self._lib.scriptCompApiDestroyCompiler(self._comp)

    def _write_file(self, _fn, res_type: int, data: bytes, size: int, is_binary: bool):
        dat = bytes(ct.cast(data, ct.POINTER(ct.c_char * size)).contents)
        if is_binary:
            assert not self._ncs, f"compiler called twice for binary data: {self._ncs=}"
            assert res_type == self._bin_rt, f"unexpected restype: {res_type=}"
            self._ncs = dat
        else:
            assert not self._ndb, f"compiler called twice for debug data: {self._ndb=}"
            assert res_type == self._dbg_rt, f"unexpected restype: {res_type=}"
            self._ndb = dat.decode(self._encoding)
        return 0

    def _load_file(self, script_name: bytes, res_type: int):
        assert res_type == self._src_rt, f"unexpected restype: {res_type=}"
        filename = f"{script_name.decode(self._encoding)}.{self._src_ext}"
        if data := self._resolver(filename):
            data = data.encode(self._encoding) if isinstance(data, str) else data
            self._lib.scriptCompApiDeliverFile(self._comp, data, len(data))
            return True

        return False

    def compile(self, script_name: str) -> tuple[bytes, str]:
        """
        Compile the given script filename.

        This will invoke multiple callbacks to load the script and
        any includes. The script will be compiled to bytecode and
        debug information.

        Args:
            script_name: The script to compile. It will be requested
                from the resolver. The source restype extension is
                optionally stripped; other extensions will raise
                a ValueError.

        Returns:
            A tuple of (bytecode, debug data).
            The bytecode is a bytes object, and the debug data is
            a string; or None if no debug data was requested.

        Raises:
            CompilationError: If the compilation fails.
            ValueError: If the script name is invalid.
        """

        root, ext = os.path.splitext(script_name)

        if ext == "." + self._src_ext:
            script_name = root
        elif ext:
            raise ValueError(
                f"Invalid script name: {script_name}. Expected extension: {self._src_ext}"
            )

        r = self._lib.scriptCompApiCompileFile(
            self._comp, script_name.encode(self._encoding)
        )
        if r.code != 0:
            raise CompilationError(r.code, r.str.decode(self._encoding).strip())
        assert self._ncs
        ncs, ndb = self._ncs, self._ndb
        self._ncs = None
        self._ndb = None
        return (ncs, ndb)
