import os
import re
import json
import shutil
import logging
from overrides import overrides
from pathlib import Path
from functools import lru_cache
from Packages.IPackage import IPackage
import Packages.DLLs

class Vcpkg(IPackage):
    """
    Vcpkg compiler and linker command line options for cl.exe.  Depends on the VCPKG_ROOT
    environment variable.
    """

    def __init__(self, argv : list[str] = []):
        # Vcpkg root dir:
        self._root = Path(os.environ['VCPKG_ROOT'])
        if not self._root.exists():
            raise Exception(f"No vcpkg root: {self._root}")

        # Vcpkg installed dir:
        self._installed_dir = self._root / "installed" / "x64-windows"
        if not self._installed_dir.exists():
            raise Exception(f"No vcpkg installed dir: {self._installed_dir}")

        # Vcpkg debug dir:
        self._debug_dir = self._installed_dir / "debug"
        if not self._debug_dir.exists():
            raise Exception(f"No vcpkg debug dir: {self._debug_dir}")

        # Vcpkg lib filenames:
        self._arg_regex_str = "-lvcpkg_(.+)"
        self._arg_include_regex_str = "^-lboost$"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of Paths to Vcpkg release lib files:
        self._release_libs = list()

        # List of DLLs which were not copied:
        self._uncopied_dlls = set()

        # Should include Boost in compilation?
        self._should_use = False

        # Compiler options read from json file:
        self._defines = list()
        script_filename = Path(os.path.realpath(__file__))
        user_options_filename = script_filename.with_name( 'vcpkg.json')
        if user_options_filename.exists():
            with open(user_options_filename) as f:
                user_clo = json.load(f)
            self._defines = user_clo['defines']

        # Find the requested Vcpkg libs in argv:
        requested_libs = list()  # List of Vcpkg libs found in argv.
        re_arg = re.compile(self._arg_regex_str)
        re_arg_include = re.compile(self._arg_include_regex_str)
        unused_argv = list()  # argv without Vcpkg options.
        for arg in self._argv:
            m = re_arg_include.match(arg)
            if m:
                self._should_use = True
            else:
                m = re_arg.match(arg)
                if m:
                    self._should_use = True
                    requested_libs.append(m.group(1))
                else:
                    unused_argv.append(arg)
        self._argv = unused_argv  # Keep the args not used in this package.

        # Find the Vcpkg release lib files:
        self._release_libs = list()
        lib_paths = list(self.lib_dir.glob('*.lib')) # All libs in the lib dir.
        for requested_lib in requested_libs:
            self._release_libs = [str(n) for n in lib_paths if n.stem.startswith(requested_lib)]

        # Find the Vcpkg debug lib files:
        self._debug_libs = list()
        lib_paths = list(self.debug_lib_dir.glob('*.lib')) # All libs in the debug lib dir.
        for requested_lib in requested_libs:
            self._debug_libs = [str(n) for n in lib_paths if n.stem.startswith(requested_lib)]

    @property
    @overrides
    def should_use(self) -> bool:
        return self._should_use or 0 < len(self._release_libs)

    @property
    @overrides
    def compiler_options(self) -> list[str]:
        return []

    @property
    @overrides
    def linker_options(self) -> list[str]:
        return []

    @property
    @overrides
    def defines(self) -> list[str]:
        return self._defines

    @property
    @overrides
    @lru_cache
    def include_dirs(self) -> list[str]:
        d = self._installed_dir / "include"
        if not d.exists():
            raise Exception(f"No vcpkg include dir: {d}")
        return [str(d)]

    @property
    @overrides
    def argv(self) -> list[str]:
        return self._argv

    @property
    @overrides
    def release_libs(self) -> list[str]:
        return self._release_libs

    @property
    def debug_libs(self) -> list[str]:
        return self._debug_libs

    @property
    @overrides
    @lru_cache
    def lib_dir(self) -> Path:
        d = self._installed_dir / "lib"
        if not d.exists():
            raise Exception(f"No vcpkg lib dir: {d}")
        return d

    @property
    @lru_cache
    def debug_lib_dir(self) -> Path:
        d = self._debug_dir / "lib"
        if not d.exists():
            raise Exception(f"No vcpkg debug lib dir: {d}")
        return d

    @property
    @overrides
    @lru_cache
    def dll_dir(self) -> Path:
        d = self._installed_dir / "bin"
        if not d.exists():
            raise Exception(f"No vcpkg dll dir: {d}")
        return d

    @property
    @lru_cache
    def debug_dll_dir(self) -> Path:
        d = self._debug_dir / "bin"
        if not d.exists():
            raise Exception(f"No vcpkg debug dll dir: {d}")
        return d

    @property
    @overrides
    def uncopied_dlls(self) -> set[str]:
        return self._uncopied_dlls
