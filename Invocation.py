import sys
import subprocess
import logging
import re
import shutil
from pathlib import Path
from Boost import Boost
from Common import Common


def bounded_incr(idx, bound):
    if idx < bound - 1:
        return idx + 1
    else:
        raise Exception(f'Idx ({idx+1}) is beyond bound ({bound}).')


class Invocation:
    def __init__(self, argv) -> None:
        self._compiler = "cl.exe"
        self._target = ""
        self._src_path = ""
        self._flags = list()
        self._libs = list()
        self._common = Common(argv)
        self._boost = Boost(self._common.argv)
        self._argv = self._boost.argv
        # Standard system-supplied DLLs which should not be copied beside the executable.
        self._system_dlls = [
            'MSVCP140.dll', 'KERNEL32.dll', 'VCRUNTIME140.dll',
            'VCRUNTIME140_1.dll', 'api-ms-win-crt-runtime-l1-1-0.dll',
            'api-ms-win-crt-heap-l1-1-0.dll', 'api-ms-win-crt-environment-l1-1-0.dll',
            'api-ms-win-crt-math-l1-1-0.dll', 'api-ms-win-crt-stdio-l1-1-0.dll',
            'api-ms-win-crt-locale-l1-1-0.dll'
            ]

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

        CWD = Path.cwd()
        SRC = Path(self.src_path)  # The temp C++ file produced by Org mode.
        TARGET = Path(self.target) # The target executable.
        OBJ = CWD / (SRC.stem + ".obj") # Obj file to be deleted later.
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

        for d in self._common.include_dirs:
            cl_clo.append("/I" + str(Path(d)))

        for d in self._boost.include_dirs:
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

        logging.debug("cl_clo == {}".format(cl_clo))
        # Invoking the compiler with just subprocess.run seems to work well:
        cp = subprocess.run(cl_clo, capture_output=True, text=True)
        # c = subprocess.Popen(cl_clo, stdout=sys.stderr, stderr=sys.stderr)
        # c.communicate()
        if OBJ.exists():
            OBJ.unlink()
        if cp.returncode != 0:
            logging.debug("Compiler output:\n{}\n{}".format(cp.stdout,cp.stderr))
            raise Exception("Compilation failed: \n{}".format(cp.stdout))
        self.duplicate_required_dlls()


    def duplicate_required_dlls(self):
        """
        Copy DLLs from their library location to beside the target executable.
        """
        TARGET = Path(self.target) # The just built target executable.
        dumpbin_exe = shutil.which('dumpbin')
        if dumpbin_exe is None:
            raise Exception('No such executable: dumpbin')
        logging.debug("dumpbin == {}".format(dumpbin_exe))
        dumpbin_clo = [dumpbin_exe, "/IMPORTS", str(TARGET)]
        cp = subprocess.run(dumpbin_clo, capture_output=True, text=True)
        dll_list = re.findall(r'[^ \t]+\.dll', cp.stdout)
        dlls_to_be_copied = []
        for dll in dll_list:
            if not dll in self._system_dlls:
                dlls_to_be_copied.append(dll)
        for dll in dlls_to_be_copied:
            DEST_PATH = TARGET.parent # Copy DLL beside target executable.
            SRC_PATH = self._boost.lib_dir / dll
            if SRC_PATH.exists():
                shutil.copy2(SRC_PATH, DEST_PATH)
                logging.debug("Copied required DLL: {}".format(str(SRC_PATH)))
            else:
                raise Exception("No such DLL: {}".format(str(SRC_PATH)))
