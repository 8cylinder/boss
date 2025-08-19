"""The Engine class that all mods inherit from.

It provides shared functionality for both Bash and Ansible modules,
and orchestrates which one to use based on the provided arguments.
"""

import datetime
import os
from collections.abc import Sequence
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar, ParamSpec, TypeVar

from boss.ansible import Ansible
from boss.bash import Bash
from boss.common import Args, Snap
from boss.dist import UbuntuVersion
from boss.errors import DependencyError

# Type variable for the return type of the decorated function
R = TypeVar("R")
# Parameter specification for capturing all possible argument types
P = ParamSpec("P")


class ModType(Enum):
    """An enumeration to represent different module types.

    This class provides enumeration members to differentiate between
    module types, such as `BASH` and `ANSIBLE`, which can be used to
    categorize or manage modules in a system.
    """

    BASH = auto()
    ANSIBLE = auto()


class Engine:
    """Base class containing shared functionality between Bash and Ansible."""

    APTUPDATED = False
    info_messages: ClassVar[dict[str, list[tuple[str, str, str]]]] = {}
    WWW_USER = "www-data"
    title: str
    provides: ClassVar[Sequence[str]]
    requires: ClassVar[Sequence[str]]
    required_args: ClassVar[Sequence[str]]
    mod: Bash | Ansible

    def __init__(
        self,
        *,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Engine with the given arguments."""
        # self.ok_code = 0
        # self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        # self.provides: list[str] = []
        # self.distro = Dist()
        self.ubuntu = ubuntu_version
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

        if args.bash:
            self.mod = Bash(dry_run=dry_run, args=args)
        else:
            self.mod = Ansible(dry_run=dry_run, args=args)

    def ensure_arg_requirements(self) -> None:
        """Ensure that all required arguments are provided."""
        if not self.args:
            return
        missing_args = []

        for arg in self.required_args:
            if not getattr(self.args, arg, None):
                missing_args.append(arg)
        if missing_args:
            # make the missing args look like command line args
            missing_args = [f"--{i.replace('_', '-')}" for i in missing_args]
            missing = ", ".join(missing_args)
            this = self.__class__.__name__
            error_msg = f"Missing arguments for {this}: {missing}. "
            raise DependencyError(error_msg)

    def is_apt_installed(self, package_name: str) -> bool:
        """Check if a package is installed using apt."""
        cmd = f"dpkg-query -Wf'${{db:Status-Status}}' {package_name} 2>/dev/null"
        result = self.run(cmd, capture=True)
        return str(result) == "installed"

    def info(self, title: str, msg: str) -> None:
        """Add information messages to be displayed later."""
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]

    def set_indent(self, text: str, amount: int = 0) -> str:
        """Remove leading whitespace from each line in the text."""
        lines = text.splitlines()
        if not lines:
            return ""
        new_indent = " " * amount
        indent_level = len(lines[1]) - len(lines[1].lstrip())
        # unindent each line by the indent level
        lines = [i[indent_level:] for i in lines]
        # add the new indent level to each line
        lines = [f"{new_indent}{i}" for i in lines]
        return "\n".join(lines)

    def pre_install(self) -> None:
        """Pre-installation tasks."""
        return

    def post_install(self) -> None:
        """Post-installation tasks."""
        return

    # ----------------------------------
    # Methods mapped to Bash and Ansible
    # ----------------------------------

    def sed(self, sed_exp: str, config_file: str) -> None:
        """Replace a string in a file using sed."""
        self.mod.sed(sed_exp, config_file)

    def write_new_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
    ) -> None:
        """Create a new file with the specified content."""
        self.mod.write_new_file(filename, text, user=user, nosudo=nosudo)

    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
    ) -> None:
        """Append text to a file, optionally backing it up first."""
        self.mod.append_to_file(
            filename,
            text,
            user=user,
            nosudo=nosudo,
            backup=backup,
        )

    def apt(self, progs: list[str]) -> None:
        """Install packages using apt."""
        self.mod.apt(progs)

    def install(self) -> None:
        """Install both apt and snap packages."""
        self.mod.install()

    def run(
        self,
        cmd: str,
        wrap: bool = True,
        capture: bool = False,
        comment: str = "",
    ) -> str:
        """Map run method to composed method."""
        return self.mod.run(cmd, wrap=wrap, capture=capture, comment=comment)

    def curl(
        self,
        url: str,
        output: str,
        capture: bool = False,
    ) -> str | int | bytes | None:
        """Map curl method to composed method."""
        return self.mod.curl(url, output, capture=capture)

    def restart_apache(self) -> None:
        """Map restart_apache method to composed method."""
        self.mod.restart_apache()
