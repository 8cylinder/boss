"""Module for Example engine implementation.

This module defines the Example class, which serves as an implementation of the
Engine base class. It manages dependencies, processes command line arguments,
and performs specific pre- and post-installation tasks based on the Ubuntu version.
"""

from typing import ClassVar

from boss.common import Settings
from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class Example(Engine):
    """Short doc string here for the list command.

    The full doc string is used for the help command.  This should list
    the command line args this module needs.

    Required class variables:
      provides
      requires
      title
    """

    # sel.provides is used for dependency management, each module can
    # provide more than one.  See lamp.py for an example.
    provides: ClassVar = ["example"]

    # Any mods that this mod needs as a prerequisite.  These names are
    # matched to provides.
    requires: ClassVar = ["example2", "example3"]

    # A list of options that this mod requires to be passed in via the args namedtuple.
    required_args: ClassVar[list[str]] = []

    # A human-readable name that is used in help and listing.
    title = "Pretty name"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Example engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

        # List of apt packages to be installed via apt.
        self.apt_pkgs = ["package1", "package2"]

        # dist can be used to different things based on what version of
        # linux being used.
        if ubuntu_version == UbuntuVersion.V18_04:
            self.apt_pkgs = ["package1", "package2", "18.04_package_only"]

    # Run before apt installs the apt_pkgs.
    def pre_install(self) -> None:
        """Pre-installation steps for Example."""
        # bash provides several methods
        self.mod.sed("sed expression", "file")
        self.mod.apt(["list", "of", "packages"])
        self.mod.curl("url", "output-filename", capture=True)
        self.info("title", "message")
        self.mod.restart_apache()
        self.mod.append_to_file("filename", "text to append", backup=False)
        self.mod.run("any valid bash command string", wrap=True, capture=False)
        # capture the result of the command
        result = self.mod.run("any valid bash command string", wrap=True, capture=True)

        # get a value from the Settings class
        variable = Settings.timezone

    # Run after apt installs the apt_pkgs.
    def post_install(self) -> None:
        """Post-installation steps for Example."""
