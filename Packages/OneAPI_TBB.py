import os
import re
import json
import logging
import subprocess
from dotenv import load_dotenv
from overrides import overrides
from pathlib import Path
from Packages.IPackage import IPackage

def _create_env(env_path):
    """
    Create the environment variables to suit Intel's oneAPI.
    Depends on the TBB_ROOT environment variable.
    """
    TBB_ROOT = Path(os.environ['TBB_ROOT'])
    if not TBB_ROOT.exists():
        raise Exception("No such directory: TBB Root")

    with open(env_path, 'w') as fenv:
        TBBVARS = TBB_ROOT / "env" /  "vars.bat"
        if not TBBVARS.exists():
            raise Exception("No such file: env/vars.bat")
        os.environ['TBBVARS'] = str(TBBVARS)
        fenv.write(f"TBBVARS={os.environ['TBBVARS']}\n")
        p = subprocess.run([
            "cmd.exe",
            "/c",
            "CALL",
            str(TBBVARS),
            "intel64",
            "vs2022",
            ">nul",
            "2>&1",
            "&&",
            "set"
        ], capture_output=True)
        if p.returncode != 0:
            raise Exception('cmd failed: ' + str(p))
        m = str(os.getenv("PATH")).split(';')
        z = list()
        e = p.stdout.replace(b'\r\n', b'\n').decode('latin1')

        for l in e.split('\n'):
            s = l.split('=')
            if len(s) == 2:
                n, v = s
                if not os.getenv(n):
                    os.environ[n] = v
                    fenv.write(f"{n}={v}\n")
                    if n == 'PATH':
                        for d in v.split(';'):
                            d = d.replace('\\\\', '\\')
                            if not d in m:
                                m.append(d)
                                z.append(d)
        os.environ['PATH'] = ';'.join(z) + ';' + os.environ['PATH']
        fenv.write(f"ZPATH={';'.join(z)}\n")


def _setup_env():
    """
    Setup the environment variables for Intel's TBB.  Either: (1) read the
    environment variable values from the cache file ~/.env, or (2) create anew the
    environment variables, then cache them in env_path.
    """
    env_path = Path.home() / '.env-oneapi-tbb'
    if env_path.exists():
        p = os.environ['PATH']
        load_dotenv(env_path)
        if 'ZPATH' in os.environ.keys():
            os.environ['PATH'] = os.environ['ZPATH'] + ';' + p
        logging.debug(f'Loaded env from {env_path}')
        logging.debug('PATH == {}'.format(os.environ['PATH']))
    else:
        _create_env(env_path)
        logging.debug(f'Created env in {env_path}')
        logging.debug('PATH == {}'.format(os.environ['PATH']))


class TBB(IPackage):
    """
    Compiler and linker command line options for TBB under oneAPI.
    Depends on the TBB_ROOT environment variable.
    """

    def __init__(self, argv : list[str] = []):
        _setup_env()
        self._root = Path(os.environ['TBB_ROOT'])
        if not self._root.exists():
            raise Exception(f"No oneAPI TBB root: {self._root}")

        # TBB lib flag:
        self._arg_regex_str = "-loneapi_tbb"

        # Make a copy of argv:
        self._argv = argv[:]

        # List of DLLs which were not copied:
        self._uncopied_dlls = set()

        # Should use TBB in compilation?
        self._should_use = False

        # Compiler options read from json file:
        self._defines = list()
        this_script_filename = Path(os.path.realpath(__file__))
        user_options_filename = this_script_filename.with_name( 'OneAPI_TBB.json')
        if user_options_filename.exists():
            with open(user_options_filename) as f:
                user_clo = json.load(f)
            self._defines = user_clo['defines']

        # Find the TBB lib flag in argv:
        requested_libs = list()  # List of TBB libs found in argv.
        re_arg = re.compile(self._arg_regex_str)
        remainder_argv = list()  # argv without TBB options.
        for arg in self._argv:
            m = re_arg.match(arg)
            if m:
                self._should_use = True
                requested_libs.append("tbb")
            else:
                remainder_argv.append(arg)
        self._argv = remainder_argv  # Keep the args not used in this package.

        # Find the TBB release lib files:
        self._release_libs = list()
        lib_glob = list(self.lib_dir.glob('*.lib')) # All libs in the lib dir.
        for requested_lib in requested_libs:
            found_libs = [str(n) for n in lib_glob if n.stem.startswith(requested_lib)]
            self._release_libs.extend(found_libs)

        # Find the TBB debug lib files:
        self._debug_libs = list()
        lib_glob = list(self.debug_lib_dir.glob('*_debug.lib')) # All debug libs in the lib dir.
        for requested_lib in requested_libs:
            found_libs = [str(n) for n in lib_glob if n.stem.startswith(requested_lib)]
            self._debug_libs.extend(found_libs)

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
    def include_dirs(self) -> list[str]:
        d = self._root / "include"
        if not d.exists():
            raise Exception(f"No TBB include dir: {d}")
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
    def lib_dir(self) -> Path:
        d = self._root / "lib" / "intel64" / "vc14"
        if not d.exists():
            raise Exception(f"No TBB lib dir: {d}")
        return d

    @property
    def debug_lib_dir(self) -> Path:
        return self.lib_dir

    @property
    @overrides
    def dll_dir(self) -> Path:
        d = self._root / "redist" / "intel64" / "vc14"
        if not d.exists():
            raise Exception(f"No TBB dll dir: {d}")
        return d

    @property
    def debug_dll_dir(self) -> Path:
        return self.dll_dir

    @property
    @overrides
    def uncopied_dlls(self) -> set[str]:
        return self._uncopied_dlls
