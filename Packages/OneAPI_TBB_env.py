import os
import logging
import subprocess
from dotenv import load_dotenv
from pathlib import Path


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


def setup_env():
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
