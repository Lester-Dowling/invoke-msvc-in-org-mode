import os
import subprocess
import logging
from pathlib import Path
from Packages.Common import Common
from Packages.Boost import Boost
from Packages.Vcpkg import Vcpkg


def bounded_incr(idx, bound):
    """
    Increment idx but not beyond bound.  Throw exception if out of bounds.
    """
    if idx < bound - 1:
        return idx + 1
    else:
        raise Exception(f'Idx ({idx+1}) is beyond bound ({bound}).')


class Invocation:
    """
    Invoke the MSVC C++ compiler.  Might be possible to write another class for clang:
    Eg: clang++ -std=gnu++2a -O3
    """

    def __init__(self, argv : list[str]):
        self._compiler = "cl.exe"
        self._target = ""
        self._src_path = ""
        self._flags = list()
        self._libs = list()
        self._common = Common(argv)
        self._boost = Boost(self._common.argv)
        self._vcpkg = Vcpkg(self._boost.argv)
        self._argv = self._vcpkg.argv

        # Arg: output target filename prefixed with "-o"
        idx = 0
        idx = bounded_incr(idx, len(self._argv))
        if self._argv[idx] != "-o":
            raise Exception('Command line missing target filename.')
        idx = bounded_incr(idx, len(self._argv))
        self._target = self._argv[idx]
        idx += 1

        # Arg: compiler flags
        while idx < len(self._argv):
            g = self._argv[idx]
            if g.endswith(".cpp"):
                break
            if g.startswith("-"):
                g = g.replace("-", "/")
            self._flags.append(g)
            idx += 1

        # Arg error: missing source code files
        if idx == len(self._argv):
            raise Exception('Command line missing source code filename.')

        # Arg: source code filename
        self._src_path = self._argv[idx]
        idx += 1

        # Arg: libs for linker
        while idx < len(self._argv):
            self._libs.append(self._argv[idx])
            idx += 1

    @property
    def compiler(self):
        return self._compiler

    @property
    def target(self):
        return self._target

    @property
    def src_path(self):
        return self._src_path

    @property
    def flags(self):
        return self._flags

    @property
    def libs(self):
        return self._libs

    def run(self):
        """
        Invoke the compiler and build the target executable.
        """
        logging.debug(f'self.compiler == {self.compiler}')
        logging.debug(f'self.flags == {self.flags}')
        logging.debug(f'self.libs == {self.libs}')

        SRC = Path(self.src_path).resolve()  # The temp C++ file produced by Org mode.
        TARGET = Path(self.target).resolve() # The target executable.
        org_cwd = Path.cwd()                 # The working directory of the org file.
        os.chdir(str(SRC.parent))            # Set cwd to the location of SRC.
        CWD = Path.cwd()                     # The cwd which should now be parent of SRC.
        OBJ = CWD / (SRC.stem + ".obj")      # Obj file to be deleted later.
        logging.debug(f'CWD    == {str(CWD)}')
        logging.debug(f'SRC    == {str(SRC)}')
        logging.debug(f'TARGET == {str(TARGET)}')
        logging.debug(f'OBJ    == {str(OBJ)}')
        if TARGET.exists():
            TARGET.unlink()

        # Compose the command line for cl.exe:
        cl_clo = [self.compiler]
        cl_clo += self._common.compiler_options
        cl_clo += self.flags

        for d in self._common.defines:
            cl_clo.append("/D" + d)

        if self._boost.should_use:
            for d in self._boost.defines:
                cl_clo.append("/D" + d)

        if self._vcpkg.should_use:
            for d in self._vcpkg.defines:
                cl_clo.append("/D" + d)

        cl_clo.append("/I" + str(org_cwd)) # Include files from the current org directory.
        for d in self._common.include_dirs:
            cl_clo.append("/I" + str(Path(d)))

        if self._boost.should_use:
            for d in self._boost.include_dirs:
                cl_clo.append("/I" + str(Path(d)))

        if self._vcpkg.should_use:
            for d in self._vcpkg.include_dirs:
                cl_clo.append("/I" + str(Path(d)))

        cl_clo.append(str(SRC))

        cl_clo.append("/link")
        cl_clo.append("/out:" + str(TARGET))
        cl_clo += self._common.linker_options

        for d in self.libs:
            cl_clo.append(str(d))

        if self._boost.should_use:
            for d in self._boost.release_libs:
                cl_clo.append(str(d))

        if self._vcpkg.should_use:
            for d in self._vcpkg.release_libs:
                cl_clo.append(str(d))

        logging.debug("cl_clo == {}".format(cl_clo))
        # Invoking the compiler with just subprocess.run seems to work well:
        cp = subprocess.run(cl_clo, capture_output=True, text=True)
        if OBJ.exists():
            OBJ.unlink()
        if cp.returncode != 0:
            logging.debug("Compiler output:\n{}\n{}".format(cp.stdout,cp.stderr))
            raise Exception("Compilation failed: \n{}".format(cp.stdout))
        self._boost.duplicate_required_dlls(self.target)
        self._vcpkg.duplicate_required_dlls(self.target)
