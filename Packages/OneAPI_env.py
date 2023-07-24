import os
import re
import json
import logging
import subprocess
from dotenv import load_dotenv
from overrides import overrides
from Packages.IPackage import IPackage
from pathlib import Path


def _create_env(env_path):
    """
    Create the environment variables to suit Intel's oneAPI.
    Depends on the ONEAPI_ROOT environment variable.
    """
    ONEAPI_ROOT = Path(os.environ['ONEAPI_ROOT'])
    if not ONEAPI_ROOT.exists():
        raise Exception("No such directory: oneAPI Root")

    with open(env_path, 'w') as fenv:
        SETVARS = ONEAPI_ROOT / "setvars.bat"
        if not SETVARS.exists():
            raise Exception("No such file: setvars.bat")
        os.environ['SETVARS'] = str(SETVARS)
        fenv.write(f"SETVARS={os.environ['SETVARS']}\n")
        p = subprocess.run([
            "cmd.exe",
            "/c",
            "CALL",
            str(SETVARS),
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
    Setup the environment variables for Intel's oneAPI.  Either: (1) read the
    environment variable values from the cache file ~/.env, or (2) create anew the
    environment variables, then cache them in ~/.env.
    """
    env_path = Path.home() / '.env-oneapi'
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
