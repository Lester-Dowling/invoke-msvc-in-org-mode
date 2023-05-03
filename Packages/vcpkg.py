import os
import re
import json
import shutil
import logging
from overrides import overrides
from pathlib import Path
from Packages.IPackage import IPackage
import Packages.DLLs

class Vcpkg(IPackage):
    """
    Vcpkg compiler and linker command line options for cl.exe.  Depends on the VCPKG_ROOT
    environment variable.
    """

    def __init__(self, argv) -> None:
        # Vcpkg root dir:
        self._vcpkg_root = Path(os.environ['VCPKG_ROOT'])
        if not self._vcpkg_root.exists():
            raise Exception(f"No Vcpkg root: {self._vcpkg_root}")

        # Vcpkg lib dir:
        self._vcpkg_lib_dir = self._vcpkg_root / ".." / ".." / "lib"
        if not self._vcpkg_lib_dir.exists():
            raise Exception(f"No Vcpkg lib dir: {self._vcpkg_lib_dir}")

        # Vcpkg lib filename regexes:
        self._arg_regex_str = "-lvcpkg_(.+)"
        self._lib_debug_version_regex_str = ".+-gd-.+"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of Paths to Vcpkg release lib files:
        self._release_libs = list()

        # Compiler options read from json file:
        script_filename = Path(os.path.realpath(__file__))
        user_options_filename = script_filename.with_name( 'invoke-msvc-2022-vcpkg.json')
        with open(user_options_filename) as f:
            user_clo = json.load(f)
        self._defines = user_clo['defines']

        # Vcpkg include dir:
        # "F:/vcpkg/installed/x64-windows/include"
        self._include_dirs = [self._vcpkg_root]

        # Find the requested Vcpkg libs in argv:
        arg_libs = list()  # List of Vcpkg libs found in argv.
        re_arg = re.compile(self._arg_regex_str)
        unused_argv = list()  # argv without Vcpkg options.
        for arg in self._argv:
            m = re_arg.match(arg)
            if m:
                arg_libs.append(m.group(1))
            else:
                unused_argv.append(arg)
        self._argv = unused_argv  # Keep the args not used in this package.

        # Compose the filename regex for the requested Vcpkg libs:
        re_lib_filenames = list()
        for l in arg_libs:
            re_lib_filenames.append(re.compile(f".+{l}-.+\.lib"))

        # Find the Vcpkg release lib files:
        re_debug_version_lib = re.compile(self._lib_debug_version_regex_str)
        self._debug_libs = list()  # List of Paths to Vcpkg debug lib files.
        self._release_libs = list()
        for f in sorted(self._vcpkg_lib_dir.glob('*.lib')):
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
        return self._include_dirs

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
        return Path(self._vcpkg_lib_dir)


    @overrides
    def duplicate_required_dlls(self, target : str) -> list[str]:
        """
        Copy DLLs from their library location to beside the target executable.
        """
        dlls_to_be_copied = DLLs.required_by_target(target)
        uncopied_dlls = []
        for dll in dlls_to_be_copied:
            DEST_PATH = Path(target).parent # Copy DLL beside target executable.
            SRC_PATH = self.lib_dir / dll
            if SRC_PATH.exists():
                shutil.copy2(SRC_PATH, DEST_PATH)
                logging.debug("Copied required DLL: {}".format(str(SRC_PATH)))
            else:
                uncopied_dlls.append(dll)
        return(uncopied_dlls)
