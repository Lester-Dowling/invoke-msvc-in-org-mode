import os
import json
from overrides import overrides
from pathlib import Path
from Packages.IPackage import IPackage


class Common(IPackage):
    """
    Common compiler and linker command line options for cl.exe.
    """

    def __init__(self, argv) -> None:
        # Make a copy of argv:
        self._argv = argv[:]

        # lib files:
        self._debug_libs = list()
        self._release_libs = list()

        # Replace linker flags for cl.exe command line:
        self._linker_options = list()
        unused_argv = list()  # argv without Boost options.
        for arg in self._argv:
            if arg.startswith("-L"):
                self._linker_options.append(arg.replace("-L", "/LIBPATH:"))
            else:
                unused_argv.append(arg)
        self._argv = unused_argv  # Keep the args not used in this package.

        # Compiler options read from json file:
        script_filename = Path(os.path.realpath(__file__))
        user_options_filename = script_filename.with_name('common.json')
        with open(user_options_filename) as user_options_file:
            user_options = json.load(user_options_file)
        self._defines = user_options['defines']
        self._include_dirs = user_options['include_dirs']
        self._release_libs = user_options['libs']
        self._linker_options += user_options['linker_options']
        self._compiler_options = list()
        for co in user_options['compiler_options']:
            self._compiler_options.append("/" + co)

    @property
    @overrides
    def should_use(self) -> bool:
        return True

    @property
    @overrides
    def compiler_options(self) -> list[str]:
        return self._compiler_options

    @property
    @overrides
    def linker_options(self) -> list[str]:
        return self._linker_options

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
        return None

    @overrides
    def duplicate_required_dlls(self, target : str) -> list[str]:
        return []
