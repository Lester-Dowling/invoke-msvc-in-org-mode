import os
import re
import json
from overrides import overrides
from pathlib import Path
from IPackage import IPackage


class Boost(IPackage):
    """
    Boost compiler and linker command line options for cl.exe.  Depends on the BOOST_ROOT
    environment variable.
    """

    def __init__(self, argv) -> None:
        # Boost root dir:
        self._boost_root = Path(os.environ['BOOST_ROOT'])
        if not self._boost_root.exists():
            raise Exception(f"No Boost root: {self._boost_root}")

        # Boost lib dir:
        self._boost_lib_dir = self._boost_root / ".." / ".." / "lib"
        if not self._boost_lib_dir.exists():
            raise Exception(f"No Boost lib dir: {self._boost_lib_dir}")

        # Boost lib filename regexes:
        self._arg_regex_str = "-lboost_(.+)"
        self._lib_debug_version_regex_str = ".+-gd-.+"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of Paths to Boost release lib files:
        self._release_libs = list()

        # Compiler options read from json file:
        script_filename = Path(os.path.realpath(__file__))
        user_options_filename = script_filename.with_name(
            'invoke-msvc-2022-boost.json')
        with open(user_options_filename) as f:
            user_clo = json.load(f)
        self._defines = user_clo['defines']
        self._include_dirs = [self._boost_root]

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
        return Path(self._boost_lib_dir)
