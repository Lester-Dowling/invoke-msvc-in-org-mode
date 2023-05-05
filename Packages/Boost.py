import os
import re
import json
import shutil
import logging
from overrides import overrides
from pathlib import Path
from Packages.IPackage import IPackage
import Packages.DLLs

class Boost(IPackage):
    """
    Boost compiler and linker command line options for cl.exe.  Depends on the BOOST_ROOT
    environment variable.
    """

    def __init__(self, argv) -> None:
        # Boost root dir:
        self._root = Path(os.environ['BOOST_ROOT'])
        if not self._root.exists():
            raise Exception(f"No Boost root: {self._root}")

        # Vcpkg include dir:
        self._include_dir = self._root
        if not self._include_dir.exists():
            raise Exception(f"No Boost include dir: {self._include_dir}")

        # Boost lib dir:
        self._boost_lib_dir = self._root / ".." / ".." / "lib"
        if not self._boost_lib_dir.exists():
            raise Exception(f"No Boost lib dir: {self._boost_lib_dir}")

        # Boost lib filename regexes:
        self._arg_regex_str = "-lboost_(.+)"
        self._lib_debug_version_regex_str = ".+-gd-.+"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of Paths to Boost release lib files:
        self._release_libs = list()

        # List of DLLs which were not copied:
        self._uncopied_dlls = set()

        # Compiler options read from json file:
        script_filename = Path(os.path.realpath(__file__))
        user_options_filename = script_filename.with_name('boost.json')
        if user_options_filename.exists():
            with open(user_options_filename) as f:
                user_clo = json.load(f)
                self._defines = user_clo['defines']

        # Find the requested Boost libs in argv:
        arg_libs = list()  # List of Boost libs found in argv.
        re_arg = re.compile(self._arg_regex_str)
        unused_argv = list()  # argv without Boost options.
        for arg in self._argv:
            m = re_arg.match(arg)
            if m:
                arg_libs.append(m.group(1))
            else:
                unused_argv.append(arg)
        self._argv = unused_argv  # Keep the args not used in this package.

        # Compose the filename regex for the requested Boost libs:
        re_lib_filenames = list()
        for l in arg_libs:
            re_lib_filenames.append(re.compile(f".+{l}-.+\.lib"))

        # Find the Boost release lib files:
        re_debug_version_lib = re.compile(self._lib_debug_version_regex_str)
        self._debug_libs = list()  # List of Paths to Boost debug lib files.
        self._release_libs = list()
        for f in sorted(self._boost_lib_dir.glob('*.lib')):
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
        return 0 < len(self._release_libs)

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
    def include_dirs(self) -> list[str]:
        return [self._include_dir]

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
    def lib_dir(self) -> Path:
        return Path(self._boost_lib_dir)

    @overrides
    def locate_required_dlls(self, target : str) -> set[str]:
        """
        Locate the canonical path to each required DLL.
        """
        required_dlls = Packages.DLLs.required_by_target(target)
        self._uncopied_dlls = set()
        located_dlls = set()
        for dll in required_dlls:
            DLL_PATH = self.lib_dir / dll
            if DLL_PATH.exists():
                located_dlls.add(dll)
            else:
                self._uncopied_dlls.add(dll)
        return(located_dlls)


    @overrides
    def duplicate_required_dlls(self, target : str):
        """
        Copy DLLs from their library location to beside the target executable.
        """
        dlls_to_be_copied = self.locate_required_dlls(target)
        DEST_PATH = Path(target).parent # Copy DLL beside target executable.
        for dll_path in dlls_to_be_copied:
            shutil.copy2(dll_path, DEST_PATH)
            logging.debug("Copied required DLL: {}".format(str(dll_path)))
