from pathlib import Path
from abc import ABCMeta
from abc import abstractmethod
from overrides import EnforceOverrides
import shutil
import logging
import Packages.DLLs
from pathlib import Path


class IPackage(EnforceOverrides, metaclass=ABCMeta):
    """
    Interface to a package of the compilation process.  The details of each package are
    listed on the command line to the compiler.
    """

    @property
    @abstractmethod
    def should_use(self) -> bool:
        """
        Should the details of this package be passed to the compiler?
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def compiler_options(self) -> list[str]:
        """
        A list of options to pass to the compiler.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def linker_options(self) -> list[str]:
        """
        A list of options to pass to the linker.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def defines(self) -> list[str]:
        """
        A list of macro defines to pass to the compiler.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def include_dirs(self) -> list[str]:
        """
        A list of include directories to pass to the compiler.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def argv(self) -> list[str]:
        """
        A list of the original command line args which remain after processing.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def release_libs(self) -> list[str]:
        """
        A list of lib pathnames to pass to the linker for a release build.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def lib_dir(self) -> Path:
        """
        The lib directory for all the lib files of the package.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def dll_dir(self) -> Path:
        """
        The DLL directory for all the DLL files of the package.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def uncopied_dlls(self) -> set[str]:
        """
        The set of DLLs which were not copied.
        """
        raise NotImplementedError()


    def locate_required_dlls(self, target : str) -> set[str]:
        """
        Locate the canonical path to each required DLL.
        """
        self._uncopied_dlls = set()
        located_dlls = set()
        for dll in Packages.DLLs.required_by_target(target):
            dll_path = self.dll_dir / dll
            if dll_path.exists():
                located_dlls.add(dll_path)
                recursed_required_dlls = self.locate_required_dlls(str(dll_path))
                located_dlls |= recursed_required_dlls
            else:
                self._uncopied_dlls.add(dll)
        return(located_dlls)


    def duplicate_required_dlls(self, target : str):
        """
        Copy DLLs from their library location to beside the target executable.
        """
        dlls_to_be_copied = self.locate_required_dlls(target)
        dest_path = Path(target).parent # Copy DLL beside target executable.
        logging.debug("Dest path of DLLs: {}".format(str(dest_path)))
        for dll_path in dlls_to_be_copied:
            shutil.copy2(dll_path, dest_path)
            logging.debug("Copied required DLL: {}".format(str(dll_path)))
