import sys
import logging
from pathlib import Path
import Packages.MSVC2022 as MSVC2022
from Invocation import Invocation


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='invoke-msvc-2022.log',
                        format='%(asctime)s\t%(levelname)s\t%(message)s')
    MSVC2022.setup_env()
    logging.debug(f'CWD    == {str(Path.cwd())}')
    logging.debug("sys.arv == {}".format(sys.argv))
    compiler = Invocation(sys.argv)
    compiler.run()
