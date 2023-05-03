import os
import sys
import subprocess
import logging
from dotenv import load_dotenv
from pathlib import Path
import xml.etree.ElementTree as ET
from Invocation import Invocation


def create_env(env_path):
    """
    Create the environment variables to suit cl.exe from MSVC 2022.
    """
    VSWHERE = Path(os.environ['ProgramFiles(x86)'] +
                   "/Microsoft Visual Studio/Installer/vswhere.exe")
    if not VSWHERE.exists():
        raise Exception("No such file: vswhere.exe")
    p = subprocess.run([VSWHERE, "-prerelease", "-format",
                       "xml", "-nologo"], capture_output=True)
    if p.returncode != 0:
        raise Exception('vswhere failed.')

    m = ET.fromstring(p.stdout)

    for ii in m.iter('instance'):
        VS_YEAR = int(ii.find('catalog').find('productLineVersion').text)
        if VS_YEAR == 2022:
            with open(env_path, 'w') as fenv:
                os.environ['VS_YEAR'] = str(VS_YEAR)
                fenv.write(f"VS_YEAR={os.environ['VS_YEAR']}\n")
                INSTALLATION_PATH = Path(ii.find('installationPath').text)
                if not INSTALLATION_PATH.exists():
                    raise Exception("No such installation path: " + str(INSTALLATION_PATH))
                os.environ['VS_INSTALLATION_PATH'] = str(INSTALLATION_PATH)
                fenv.write(
                    f"VS_INSTALLATION_PATH={os.environ['VS_INSTALLATION_PATH']}\n")
                VS_VC = INSTALLATION_PATH / "VC"
                if not VS_VC.exists():
                    raise Exception("No VC installation folder.")
                os.environ['VS_VC'] = str(VS_VC)
                fenv.write(f"VS_VC={os.environ['VS_VC']}\n")
                VCVARSALL = VS_VC / "Auxiliary" / "Build" / "vcvarsall.bat"
                if not VCVARSALL.exists():
                    raise Exception("No such file: vcvarsall.bat")
                os.environ['VCVARSALL'] = str(VCVARSALL)
                fenv.write(f"VCVARSALL={os.environ['VCVARSALL']}\n")
                VS_COMMONEXTENSIONS = (
                    VS_VC / ".." / "COMMON7" / "IDE" / "COMMONEXTENSIONS").resolve()
                if not VS_COMMONEXTENSIONS.exists():
                    raise Exception("No such dir: COMMONEXTENSIONS")
                os.environ['VS_COMMONEXTENSIONS'] = str(VS_COMMONEXTENSIONS)
                fenv.write(
                    f"VS_COMMONEXTENSIONS={os.environ['VS_COMMONEXTENSIONS']}\n")
                VS_CMAKE = VS_COMMONEXTENSIONS / "MICROSOFT" / \
                    "CMAKE" / "CMake" / "bin" / "cmake.exe"
                if not VS_CMAKE.exists():
                    raise Exception("No CMake installation.")
                os.environ['VS_CMAKE'] = str(VS_CMAKE)
                fenv.write(f"VS_CMAKE={os.environ['VS_CMAKE']}\n")
                VS_MAKE_PROGRAM = VS_COMMONEXTENSIONS / \
                    "MICROSOFT" / "CMAKE" / "Ninja" / "ninja.exe"
                if not VS_MAKE_PROGRAM.exists():
                    raise Exception("No Ninja installation.")
                os.environ['VS_MAKE_PROGRAM'] = str(VS_MAKE_PROGRAM)
                fenv.write(f"VS_MAKE_PROGRAM={os.environ['VS_MAKE_PROGRAM']}\n")
                os.environ['VS_NINJA'] = str(VS_MAKE_PROGRAM)
                fenv.write(f"VS_NINJA={os.environ['VS_NINJA']}\n")
                TOOLS_MSVC = VS_VC / "Tools" / "MSVC"
                if not TOOLS_MSVC.exists():
                    raise Exception("No such installation folder: Tools/MSVC")
                os.environ['VS_TOOLS_MSVC'] = str(TOOLS_MSVC)
                fenv.write(f"VS_TOOLS_MSVC={os.environ['VS_TOOLS_MSVC']}\n")
                VS_TOOLS_VERSIONED = sorted(TOOLS_MSVC.glob('*'))[-1]
                os.environ['VS_TOOLS_VERSIONED'] = str(VS_TOOLS_VERSIONED)
                fenv.write(f"VS_TOOLS_VERSIONED={os.environ['VS_TOOLS_VERSIONED']}\n")
                VS_C_COMPILER = VS_TOOLS_VERSIONED / "bin" / "HostX64" / "x64" / "cl.exe"
                if not VS_C_COMPILER.exists():
                    raise Exception("No C compiler installation.")
                os.environ['VS_C_COMPILER'] = str(VS_C_COMPILER)
                fenv.write(f"VS_C_COMPILER={os.environ['VS_C_COMPILER']}\n")
                VS_CXX_COMPILER = VS_TOOLS_VERSIONED / "bin" / "HostX64" / "x64" / "cl.exe"
                if not VS_CXX_COMPILER.exists():
                    raise Exception("No C++ compiler installation.")
                os.environ['VS_CXX_COMPILER'] = str(VS_CXX_COMPILER)
                fenv.write(f"VS_CXX_COMPILER={os.environ['VS_CXX_COMPILER']}\n")
                p = subprocess.run([
                    "cmd.exe",
                    "/c",
                    "CALL",
                    str(VCVARSALL),
                    "x64",
                    ">nul",
                    "2>&1",
                    "&&",
                    "set"
                ], capture_output=True)
                if p.returncode != 0:
                    raise Exception('cmd failed: ' + str(p))
                m = os.getenv("PATH").split(';')
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


def setup_env():
    """
    Setup the environment variables for MSVC 2022.  Either: (1) read the environment
    variable values from the cache file ~/.env, or (2) create anew the environment
    variables, then cache them in ~/.env.
    """
    env_path = Path.home() / '.env'
    if env_path.exists():
        p = os.environ['PATH']
        load_dotenv(env_path)
        if 'ZPATH' in os.environ.keys():
            os.environ['PATH'] = os.environ['ZPATH'] + ';' + p
        logging.debug(f'Loaded env from {env_path}')
        logging.debug('PATH == {}'.format(os.environ['PATH']))
    else:
        create_env(env_path)
        logging.debug(f'Created env in {env_path}')
        logging.debug('PATH == {}'.format(os.environ['PATH']))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='invoke-msvc-2022.log',
                        format='%(asctime)s\t%(levelname)s\t%(message)s')
    setup_env()
    msvc = Invocation(sys.argv)
    msvc.run()
