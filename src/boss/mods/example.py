from typing import Any

from boss.engine import Engine

from ..dist import Dist
from ..engine import Settings


class Example(Engine):
    """Short doc string here for the list command

    The full doc string is used for the help command.  This should list
    the command line args this module needs.

    Required class variables:
      provides
      requires
      title
    """

    # sel.provides is used for dependency management, each module can
    # provide more than one.  See lamp.py for an example.
    provides = ["example"]

    # Any mods that this mod needs as a prerequisite.  These names are
    # matched to provides.
    requires = ["example2", "example3"]

    # A list of options that this mod requires to be passed in via the args namedtuple.
    required_args: list[str] = []

    # A human readable name that is used in help and listing.
    title = "Pretty name"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        # List of apt packages to be installed via apt.
        self.apt_pkgs = ["package1", "package2"]

        # dist can be used to different things based on what version of
        # linux being used.
        if self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ["package1", "package2", "18.04_package_only"]

    # Run before apt installs the apt_pkgs.
    def pre_install(self) -> None:
        # bash provides several methods
        self.mod.sed("sed expression", "file")
        self.mod.apt(["list", "of", "packages"])
        self.mod.curl("url", "output-filename", capture=True)
        self.info("title", "message")
        self.mod.restart_apache()
        self.mod.append_to_file("filename", "text to append", append=True, backup=False)
        self.mod.run("any valid bash command string", wrap=True, capture=False)
        # capture the result of the command
        result = self.mod.run("any valid bash command string", wrap=True, capture=True)

        # get a value from the Settings class
        variable = Settings.timezone

    # Run after apt installs the apt_pkgs.
    def post_install(self) -> None:
        pass
