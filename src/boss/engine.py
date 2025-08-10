import datetime
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from functools import wraps
from pathlib import Path
from typing import Any, ClassVar, NamedTuple, ParamSpec, TypeVar

import click

from boss.dist import UbuntuVersion
from boss.errors import CommandError, DependencyError
from boss.util import display_cmd, error, notify

# Type variable for the return type of the decorated function
R = TypeVar("R")
# Parameter specification for capturing all possible argument types
P = ParamSpec("P")


def warn(warning_message: str) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Require user confirmation before executing the decorated function."""

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            # Ask user for confirmation
            if (
                click.prompt(
                    warning_message,
                    type=click.Choice(["y", "N"], case_sensitive=False),
                    default="n",
                    show_default=False,
                ).lower()
                == "y"
            ):
                return func(*args, **kwargs)

            click.echo("Boss halted.")
            sys.exit(1)

        return wrapper

    return decorator


class Args(NamedTuple):
    """A class representing configuration arguments for a specific operation.

    This class is used to store and manage various configurations and
    parameters required for a given task such as script generation,
    database operations, and module handling. It provides a structured
    way to group arguments and ensure proper data types.
    """

    bash: bool
    servername: str
    modules: tuple[str, ...]
    dry_run: bool
    required: bool
    dependencies: bool
    generate_script: bool
    dist_version: float | None
    new_user_and_pass: tuple[str, str]  # ...?
    sql_file: str | None
    db_name: str | None
    db_root_pass: str
    new_db_user_and_pass: tuple[str, str]
    new_system_user_and_pass: tuple[str, str]
    site_name_and_root: list[tuple[str, str, str]]
    craft_credentials: tuple[str, str, str]
    host_ip: str | None
    netdata_user_pass: tuple[str, str]
    wanted: list[str] = []


class Snap(Enum):
    """An enumeration to represent different types of Snap."""

    CLASSIC = auto()
    DEFAULT = auto()


class ModType(Enum):
    """An enumeration to represent different module types.

    This class provides enumeration members to differentiate between
    module types, such as `BASH` and `ANSIBLE`, which can be used to
    categorize or manage modules in a system.
    """

    BASH = auto()
    ANSIBLE = auto()


@dataclass
class Settings:
    """Represents application settings configuration.

    This class is used to manage and provide settings for the application. It allows
    definition of default configurations such as the timezone.
    """

    timezone: str = "America/Los_Angeles"


class Ansible:
    """Ansible implementation with the same API as Bash class."""

    APTUPDATED = False
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str
    requires: list[str]
    required_args: list[str]

    apt_task: ClassVar[dict[str, Any]] = {
        "name": "Install apt packages",
        "ansible.builtin.apt": {
            "state": "present",
            "pkg": [],
        },
    }
    playbook: ClassVar[list[dict[str, Any]]] = [
        {
            "name": "Configure server",
            "hosts": "webservers",  # from inventory
            "become": "yes",
            "tasks": [],
        },
    ]

    def __init__(self, args: Args, dry_run: bool = False) -> None:
        """Initialize the Ansible module with the given arguments."""
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

    def sed(self, sed_exp: str, config_file: str) -> None:
        """Replace a string in a file using Ansible's replace module."""
        # ansible.builtin.lineinfile or ansible.builtin.replace
        task: dict[str, Any] = {
            "name": f"Replace string in {config_file}",
            "ansible.builtin.replace": {
                "path": str(config_file),
                "regexp": sed_exp,
                "replace": "",
                "backup": True,
            },
        }
        self.playbook[0]["tasks"].append(task)

    def write_new_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
    ) -> None:
        """Create a new file with the specified content using Ansible's copy module."""
        task: dict[str, Any] = {
            "name": f"Create file {filename}",
            "ansible.builtin.copy": {
                "dest": str(filename),
                "content": text,
                "owner": user if user else "root",
                "mode": "0644",
                "force": True,
            },
        }
        self.playbook[0]["tasks"].append(task)

    @warn('"append_to_file(...)" is untested in Ansible. Proceed?')
    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        # user: str | None = None,
        nosudo: bool = False,  # noqa: ARG002 - keep for compatibility with Bash
        backup: bool = True,
        # append: bool = True,
    ) -> None:
        """Append text to a file using Ansible's blockinfile module."""
        task: dict[str, Any] = {
            "name": f"Append to file {filename}",
            "ansible.builtin.blockinfile": {
                "path": str(filename),
                "block": text,
                "create": False,
                "backup": backup,
            },
        }
        self.playbook[0]["tasks"].append(task)

    def apt(self, progs: list[str]) -> None:
        """Add packages to the Ansible apt task."""
        self.apt_task["ansible.builtin.apt"]["pkg"].extend(progs)

    def install(self) -> None:
        """Match the bash.install() method.

        It doesn't do anything in Ansible, since that is
        handled by the playbook.
        """

    def pre_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def post_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def run(
        self,
        cmd: str,
        wrap: bool = True,
        capture: bool = False,
        comment: str = "",
    ) -> str | None:
        """Run a command using Ansible's shell module."""

    def curl(self, url: str, output: str, capture: bool = False) -> str | None:
        """Download a file using Ansible's get_url module."""

    def restart_apache(self) -> None:
        """Restart Apache using Ansible's service module."""

    def _apt(self, packages_list: list[str]) -> None:
        """Add packages to the Ansible apt task."""

    def _snap(self, packages: list[tuple[str, Snap]]) -> None:
        pass

    def info(self, title: str, msg: str) -> None:
        """Add information messages to be displayed later."""
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]

    def set_indent(self, text: str, amount: int = 0) -> str:
        """Remove leading whitespace from each line in the text.

        Uses the first line's indentation level to determine how much to remove.
        """
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


class Bash:
    """A class to run bash commands and manage system operations."""

    APTUPDATED = False
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str
    requires: list[str]
    required_args: list[str]

    def __init__(self, args: Args, dry_run: bool = False) -> None:
        """Initialize the Bash module with the given arguments."""
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        # self.distro = Dist()
        # self.ubuntu = Ubuntu()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

    def sed(self, sed_exp: str, config_file: str) -> None:
        """Replace a string in a file using sed."""
        new_ext = f".original-{self.now}"
        sed_cmd = f'sudo sed --in-place="{new_ext}" "{sed_exp}" "{config_file}"'
        self.run(sed_cmd)

    def write_new_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
    ) -> None:
        """Create a new file with the specified content."""
        sudo = "" if nosudo else "sudo"
        alt_user = f"-u {user}" if user else ""
        cmd = f"""echo | {sudo} {alt_user} tee "{filename}" <<'EOF'\n{text}\nEOF"""
        self.run(cmd, wrap=False)

    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
    ) -> None:
        """Append text to a file, optionally backing it up first."""
        sudo = "" if nosudo else "sudo"

        if backup:
            copy_cmd = f'{sudo} cp "{filename}" "{filename}.original-{self.now}"'
            self.run(copy_cmd)

        www_user = ""
        if user == self.WWW_USER:
            www_user = f"-u {self.WWW_USER}"

        add_cmd = (
            f'echo | {sudo} {www_user} tee --append "{filename}" <<EOF\n{text}\nEOF'
        )

        # remove leading spaces from add_cmd using regex
        add_cmd = re.sub(r"^\s+", "", add_cmd, flags=re.MULTILINE)
        self.run(add_cmd, wrap=False)

    def apt(self, progs: list[str]) -> None:
        """Install packages using apt."""
        self._apt(progs)

    def install(self) -> None:
        """Install both apt and snap packages."""
        self._apt(self.apt_pkgs)
        self._snap(self.snap_pkgs)

    def run(
        self,
        cmd: str,
        wrap: bool = True,
        capture: bool = False,
        comment: str = "",
    ) -> str:
        """Run an arbitrary command in the shell."""
        if wrap:
            pretty_cmd = " ".join(cmd.split())
            display_cmd(
                pretty_cmd,
                wrap=True,
                script=self.args.generate_script,
                comment=comment,
            )
        else:
            display_cmd(
                cmd,
                wrap=False,
                script=self.args.generate_script,
                comment=comment,
            )

        result: str | bytes | int | None
        if self.args.dry_run or self.args.generate_script:
            return ""

        if capture:
            result = subprocess.check_output(
                cmd,
                shell=True,
                executable="/bin/bash",
            ).decode()
            sys.stdout.flush()
        else:
            result = subprocess.check_call(cmd, shell=True, executable="/bin/bash")
            if result > 0:
                raise CommandError(cmd)
        return str(result)

    def curl(
        self,
        url: str,
        output: str,
        capture: bool = False,
    ) -> str | int | bytes | None:
        """Download a file using curl."""
        cmd = f"curl -sSL {url} --output {output}"
        return self.run(cmd, capture=capture)

    def restart_apache(self) -> None:
        """Restart Apache using the appropriate command.

        Details about whether to use service or systemctl
        https://askubuntu.com/a/903405
        """
        self.run("sudo service apache2 restart")

    def _apt(self, packages_list: list[str]) -> None:
        if not packages_list:
            return
        dry = "--dry-run" if self.dry_run else ""
        packages = " ".join(packages_list)
        if not Bash.APTUPDATED:
            self.run("sudo apt-get --quiet update")
            # self.run('sudo apt-get --quiet --yes upgrade')   # not really necessary
            Bash.APTUPDATED = True
        self.run(
            f"export DEBIAN_FRONTEND=noninteractive; sudo apt-get {dry} "
            "--yes --quiet install {packages}",
        )

    def _snap(self, packages: list[tuple[str, Snap]]) -> None:
        try:
            for package, snap_mode in packages:
                mode = "--classic" if snap_mode == Snap.CLASSIC else ""
                self.run(f"sudo snap install {mode} {package}")
        except ValueError as e:
            notify(f"Snaps: {packages}")
            error(f"Snap package not defined correctly: {e}")

    def info(self, title: str, msg: str) -> None:
        """Add information messages to be displayed later."""
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]

    def set_indent(self, text: str, amount: int = 0) -> str:
        """Remove leading whitespace from each line in the text.

        Uses the first line's indentation level to determine how much to remove.
        """
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
        result = self.mod.run(cmd, capture=True)
        return result == "installed"

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

    def install(self) -> None:
        """Install both apt and snap packages."""
        self.mod.apt_pkgs = self.apt_pkgs
        self.mod.snap_pkgs = self.snap_pkgs
        self.mod.install()

    def pre_install(self) -> None:
        """Pre-installation tasks."""
        return

    def post_install(self) -> None:
        """Post-installation tasks."""
        return
