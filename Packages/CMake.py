import os
import re
import json
from overrides import overrides
from pathlib import Path
from functools import lru_cache
from Packages.IPackage import IPackage

class CMake(IPackage):
    """
    Write a short CMakeLists file to compile and link command line options for cl.exe.  Depends on the BOOST_ROOT
    environment variable.
    """

    def __init__(self, argv : list[str] = []):
        # Boost root dir:
        self._root = Path(os.environ['BOOST_ROOT']).resolve()
        if not self._root.exists():
            raise Exception(f"No Boost root: {self._root}")

        # Boost lib filename regexes:
        self._arg_regex_str = "-lboost_(.+)"
        self._arg_include_regex_str = "^-lboost$"
        self._lib_debug_version_regex_str = ".+-gd-.+"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of DLLs which were not copied:
        self._uncopied_dlls = set()

        # Should include Boost in compilation?
        self._should_use = False

        # Compiler options read from json file:
        script_filename = Path(os.path.realpath(__file__)).resolve()
        user_options_filename = script_filename.with_name('boost.json')
        if user_options_filename.exists():
            with open(user_options_filename) as f:
                user_clo = json.load(f)
                self._defines = user_clo['defines']

        # Find the requested Boost libs in argv:
        requested_libs = list()  # List of Boost libs found in argv.
        re_arg = re.compile(self._arg_regex_str)
        re_arg_include = re.compile(self._arg_include_regex_str)
        unused_argv = list()  # argv without Boost options.
        for arg in self._argv:
            m = re_arg_include.match(arg)
            if m:
                self._should_use = True
            else:
                m = re_arg.match(arg)
                if m:
                    requested_libs.append(m.group(1))
                else:
                    unused_argv.append(arg)
        self._argv = unused_argv  # Keep the args not used in this package.

        # Compose the filename regex for the requested Boost libs:
        re_lib_filenames = list()
        for l in requested_libs:
            re_lib_filenames.append(re.compile(f".+{l}-.+\\.lib"))

        # Find the Boost release lib files:
        re_debug_version_lib = re.compile(self._lib_debug_version_regex_str)
        self._debug_libs = list()  # List of Paths to Boost debug lib files.
        self._release_libs = list()
        for f in sorted(self.lib_dir.glob('*.lib')):
            fstr = str(f)
            for re_lib_filename in re_lib_filenames:
                if re_lib_filename.match(fstr):
                    if re_debug_version_lib.match(fstr):
                        self._debug_libs.append(fstr)
                    else:
                        self._release_libs.append(fstr)

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
        d = self._root
        if not d.exists():
            raise Exception(f"No Boost include dir: {d}")
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
    @overrides
    @lru_cache
    def lib_dir(self) -> Path:
        d = self._root / ".." / ".." / "lib"
        d = d.resolve()
        if not d.exists():
            raise Exception(f"No Boost lib dir: {d}")
        return d

    @property
    @overrides
    @lru_cache
    def dll_dir(self) -> Path:
        return self.lib_dir

    @property
    @overrides
    def uncopied_dlls(self) -> set[str]:
        return self._uncopied_dlls
