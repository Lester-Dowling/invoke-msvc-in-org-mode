from abc import ABCMeta
from abc import abstractmethod
from overrides import EnforceOverrides


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
