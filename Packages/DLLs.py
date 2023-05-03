import subprocess
import logging
import re
import shutil
from pathlib import Path

def _remove_system(dll_list : list[str]) -> list[str]:
    """
    Remove standard system-supplied DLLs from the given DLL list.
    """
    # Standard system-supplied DLLs:
    system_dlls = [
        'MSVCP140.dll', 'KERNEL32.dll', 'VCRUNTIME140.dll',
        'VCRUNTIME140_1.dll', 'api-ms-win-crt-runtime-l1-1-0.dll',
        'api-ms-win-crt-heap-l1-1-0.dll', 'api-ms-win-crt-environment-l1-1-0.dll',
        'api-ms-win-crt-math-l1-1-0.dll', 'api-ms-win-crt-stdio-l1-1-0.dll',
        'api-ms-win-crt-locale-l1-1-0.dll' ]
    dlls_without_system = []
    for dll in dll_list:
        if not dll in system_dlls:
            dlls_without_system.append(dll)
    return(dlls_without_system)



def required_by_target(target : str) -> list[str]:
    """
    Find out which DLLs are required by the given target executable.
    """
    TARGET = Path(target) # The just built target executable.
    dumpbin_exe = shutil.which('dumpbin')
    if dumpbin_exe is None:
        raise Exception('No such executable: dumpbin')
    logging.debug("dumpbin == {}".format(dumpbin_exe))
    dumpbin_clo = [dumpbin_exe, "/IMPORTS", str(TARGET)]
    cp = subprocess.run(dumpbin_clo, capture_output=True, text=True)
    dll_list = re.findall(r'[^ \t]+\.dll', cp.stdout) # Assumes DLL filename has no spaces.
    dlls_to_be_copied = _remove_system(dll_list)
    return(dlls_to_be_copied)
