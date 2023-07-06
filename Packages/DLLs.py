import os
import re
import json
import subprocess
import logging
import shutil
from pathlib import Path
from functools import lru_cache


@lru_cache
def _system_dlls() -> set[str]:
    # List of standard system DLLs read from json file:
    script_path = Path(os.path.realpath(__file__))
    system_dll_path = script_path.with_name('system-dlls.json')
    if system_dll_path.exists():
        with open(system_dll_path) as f:
            system_dll = json.load(f)
            return(system_dll['list'])
    else:
        return(set())



def _remove_system_dlls(dll_list : list[str]) -> set[str]:
    """
    Remove standard system-supplied DLLs from the given DLL list.
    """
    dlls_without_system = set()
    for dll in dll_list:
        if not dll.startswith("api-ms-win-crt-"):
            if not dll in _system_dlls():
                dlls_without_system.add(dll)
    return(dlls_without_system)



def required_by_target(target : str) -> set[str]:
    """
    Find out which DLLs are required by the given target executable.
    """
    TARGET = Path(target).resolve() # The target executable.
    dumpbin_exe = shutil.which('dumpbin')
    if dumpbin_exe is None:
        raise Exception('No such executable: dumpbin')
    logging.debug("dumpbin == {}".format(dumpbin_exe))
    dumpbin_clo = [dumpbin_exe, "/IMPORTS", str(TARGET)]
    cp = subprocess.run(dumpbin_clo, capture_output=True, text=True)
    dll_list = re.findall(r'[^ \t]+\.dll', cp.stdout) # Assumes DLL filename has no spaces.
    logging.debug("dll_list == {}".format(dll_list))
    dlls_to_be_copied = _remove_system_dlls(dll_list)
    logging.debug("dlls_to_be_copied == {}".format(dlls_to_be_copied))
    if TARGET.name in dlls_to_be_copied:
        dlls_to_be_copied.remove(TARGET.name)
    if str(TARGET) in dlls_to_be_copied:
        dlls_to_be_copied.remove(str(TARGET))
    return(dlls_to_be_copied)
