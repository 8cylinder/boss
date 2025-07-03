import os
import sys
import re
from .dist import Dist
import datetime
import subprocess
from typing import NamedTuple, Any, TypeVar, Callable, ParamSpec, cast  # noqa F401
from dataclasses import dataclass
from .errors import CommandError, DependencyError
from .util import display_cmd, error, notify
from enum import Enum, auto
from pathlib import Path
import click
from functools import wraps


# Type variable for the return type of the decorated function
R = TypeVar("R")
# Parameter specification for capturing all possible argument types
P = ParamSpec("P")


def warn(warning_message: str) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """A decorator that prompts the user for confirmation before executing the function."""

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
            else:
                click.echo("Boss halted.")
                sys.exit(1)
                # return None

        return wrapper

    return decorator


class Args(NamedTuple):
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
    CLASSIC = auto()
    DEFAULT = auto()


class ModType(Enum):
    BASH = auto()
    ANSIBLE = auto()


@dataclass
class Settings:
    timezone: str = "America/Los_Angeles"


# class ModBase:
#     """Base class for modules that can switch between Bash and Ansible implementations.
#
#     Example usage:
#     ```python
#     from boss.mods import ModBase, ModType
#     from boss.mods.bash import Bash
#     from boss.mods.ansible import Ansible
#     ModBase.set_mod_type(ModType.BASH)  # or ModType.ANSIBLE
#     class MyModule(ModBase):
#         provides = ["my_module"]
#         requires = ["some_dependency"]
#         required_args = ["arg1", "arg2"]
#         title = "My Module"
#     ```
#     """
#
#     # _mod_type: ModType
#     # _mod_type: ModType = ModType.BASH
#     _mod_type: ModType = ModType.ANSIBLE
#
#     @classmethod
#     def set_mod_type(cls, mod_type: ModType) -> None:
#         """Set the module type to either bash or ansible."""
#         cls._mod_type = mod_type
#
#     def __init_subclass__(cls, **kwargs: Any) -> None:
#         """Dynamically set the parent class based on _mod_type."""
#         super().__init_subclass__(**kwargs)
#
#         # # Import here to avoid circular imports
#         # from .bash import Bash
#         # from .ansible import Ansible
#
#         # Map mod types to their implementation classes
#         implementations = {
#             ModType.BASH: Bash,
#             ModType.ANSIBLE: Ansible,
#         }
#
#         # Get current bases except ModBase
#         current_bases = tuple(b for b in cls.__bases__ if b is not ModBase)
#
#         # Set new bases with the correct implementation
#         cls.__bases__ = (implementations[cls._mod_type],) + current_bases
#         # cls.__bases__ = (implementations[cls._mod_type], ModBase)
#
#     def doit(self) -> None:
#         print("x" * 80)


class ModBase:
    """Base class containing shared functionality between Bash and Ansible implementations."""

    APTUPDATED = False
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str
    requires: list[str]
    required_args: list[str]

    # def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
    def __init__(self, args: Args, dry_run: bool = False) -> None:
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        self.distro = Dist()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

        self.mod = Bash(dry_run=dry_run, args=args)

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
            raise DependencyError(f"Missing arguments for {this}: {missing}. ")

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

    # def install(self) -> None:
    #     """Main installation method that handles both apt and snap packages."""
    #     self._apt(self.apt_pkgs)
    #     self._snap(self.snap_pkgs)

    def pre_install(self) -> None:
        """Hook for pre-installation tasks."""
        return

    def post_install(self) -> None:
        """Hook for post-installation tasks."""
        return

    ## Abstract methods that must be implemented by child classes
    # def _apt(self, packages_list: list[str]) -> None:
    #     """Install packages using apt."""
    #     raise NotImplementedError
    #
    # def _snap(self, packages: list[tuple[str, Any]]) -> None:
    #     """Install packages using snap."""
    #     raise NotImplementedError
    #
    # def run(
    #     self, cmd: str, wrap: bool = True, capture: bool = False, comment: str = ""
    # ) -> str | None:
    #     """Execute a command."""
    #     raise NotImplementedError
    #
    # def write_new_file(
    #     self,
    #     filename: str | Path,
    #     text: str,
    #     user: str | None = None,
    #     nosudo: bool = False,
    # ) -> None:
    #     """Create a new file with given content."""
    #     raise NotImplementedError
    #
    # def append_to_file(
    #     self,
    #     filename: str | Path,
    #     text: str,
    #     user: str | None = None,
    #     nosudo: bool = False,
    #     backup: bool = True,
    #     append: bool = True,
    # ) -> None:
    #     """Append content to an existing file."""
    #     raise NotImplementedError
    #
    # def sed(self, sed_exp: str, config_file: str) -> None:
    #     """Perform sed operations on a file."""
    #     raise NotImplementedError
    #
    # def curl(
    #     self, url: str, output: str, capture: bool = False
    # ) -> str | int | bytes | None:
    #     """Download a file using curl."""
    #     raise NotImplementedError
    #
    # def restart_apache(self) -> None:
    #     """Restart the Apache service."""
    #     raise NotImplementedError


class Ansible:
    """Ansible implementation with the same API as Bash class."""

    APTUPDATED = False
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str
    requires: list[str]
    required_args: list[str]

    apt_task: dict[str, Any] = {
        "name": "Install apt packages",
        "ansible.builtin.apt": {
            "state": "present",
            "pkg": [],
        },
    }
    playbook: list[dict[str, Any]] = [
        {
            "name": "Configure server",
            "hosts": "webservers",  # from inventory
            "become": "yes",
            "tasks": [],
        },
    ]

    def __init__(self, args: Args, dry_run: bool = False) -> None:
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        self.distro = Dist()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

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
            raise DependencyError(f"Missing arguments for {this}: {missing}. ")

    def sed(self, sed_exp: str, config_file: str) -> None:
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
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
        append: bool = True,
    ) -> None:
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
        self.apt_task["tasks"].append(*progs)

    def install(self) -> None:
        """This is here to match bash.install().

        It doesn't do anything in Ansible, since that is
        handled by the playbook."""
        pass

    def is_apt_installed(self, package_name: str) -> bool:
        """Check if a package is installed using apt."""
        cmd = f"dpkg-query -Wf'${{db:Status-Status}}' {package_name} 2>/dev/null"
        result = self.run(cmd, capture=True)
        if result == "installed":
            return True
        else:
            return False

    def pre_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def post_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def run(
        self, cmd: str, wrap: bool = True, capture: bool = False, comment: str = ""
    ) -> str | None:
        pass

    def curl(self, url: str, output: str, capture: bool = False) -> str | None:
        pass

    def restart_apache(self) -> None:
        pass

    def _apt(self, packages_list: list[str]) -> None:
        pass

    def _snap(self, packages: list[tuple[str, Snap]]) -> None:
        pass

    def info(self, title: str, msg: str) -> None:
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]

    def set_indent(self, text: str, amount: int = 0) -> str:
        """Remove leading whitespace from each line in the text.

        Uses the first line's indentation level to determine how much to remove."""
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
    APTUPDATED = False
    # info_messages: list[list[str]] = []
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str
    requires: list[str]
    required_args: list[str]

    def __init__(self, args: Args, dry_run: bool = False) -> None:
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        self.distro = Dist()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

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
            raise DependencyError(f"Missing arguments for {this}: {missing}. ")

    def sed(self, sed_exp: str, config_file: str) -> None:
        new_ext = ".original-{}".format(self.now)
        sed_cmd = f'sudo sed --in-place="{new_ext}" "{sed_exp}" "{config_file}"'
        self.run(sed_cmd)

    def write_new_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
    ) -> None:
        sudo = "" if nosudo else "sudo"
        alt_user = f"-u {user}" if user else ""
        cmd = f'''echo | {sudo} {alt_user} tee "{filename}" <<'EOF'\n{text}\nEOF'''
        self.run(cmd, wrap=False)

    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
        append: bool = True,
    ) -> None:
        sudo = "" if nosudo else "sudo"

        if backup:
            copy_cmd = f'{sudo} cp "{filename}" "{filename}.original-{self.now}"'
            self.run(copy_cmd)

        www_user = ""
        if user == self.WWW_USER:
            www_user = "-u {}".format(self.WWW_USER)

        append_flag = ""
        if append is True:
            append_flag = "-a"

        add_cmd = f'echo | {sudo} {www_user} tee {append_flag} "{filename}" <<EOF\n{text}\nEOF'

        # remove leading spaces from add_cmd using regex
        add_cmd = re.sub(r"^\s+", "", add_cmd, flags=re.MULTILINE)
        self.run(add_cmd, wrap=False)

    def apt(self, progs: list[str]) -> None:
        self._apt(progs)

    def install(self) -> None:
        self._apt(self.apt_pkgs)
        self._snap(self.snap_pkgs)

    def is_apt_installed(self, package_name: str) -> bool:
        """Check if a package is installed using apt."""
        cmd = f"dpkg-query -Wf'${{db:Status-Status}}' {package_name} 2>/dev/null"
        result = self.run(cmd, capture=True)
        if result == "installed":
            return True
        else:
            return False

    def pre_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def post_install(self) -> None:
        """Stub to ensure that all modules have this method."""
        return

    def run(
        self, cmd: str, wrap: bool = True, capture: bool = False, comment: str = ""
    ) -> str | None:
        if wrap:
            pretty_cmd = " ".join(cmd.split())
            display_cmd(
                pretty_cmd, wrap=True, script=self.args.generate_script, comment=comment
            )
        else:
            display_cmd(
                cmd, wrap=False, script=self.args.generate_script, comment=comment
            )

        result: str | bytes | int | None
        if self.args.dry_run or self.args.generate_script:
            return None

        if capture:
            result = subprocess.check_output(
                cmd, shell=True, executable="/bin/bash"
            ).decode()
            sys.stdout.flush()
        else:
            result = subprocess.check_call(cmd, shell=True, executable="/bin/bash")
            if result > 0:
                raise CommandError(cmd)
        return str(result)

    def curl(
        self, url: str, output: str, capture: bool = False
    ) -> str | int | bytes | None:
        cmd = "curl -sSL {url} --output {output}".format(url=url, output=output)
        result = self.run(cmd, capture=capture)
        return result

    def restart_apache(self) -> None:
        """Restart Apache using the appropriate command

        Details about whether to use service or systemctl
        https://askubuntu.com/a/903405"""

        if self.distro == Dist.UBUNTU:
            self.run("sudo service apache2 restart")
        else:
            error("restart_apache has unknown platform")

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
            "export DEBIAN_FRONTEND=noninteractive; sudo apt-get {dry} --yes --quiet install {packages}".format(
                dry=dry, packages=packages
            )
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
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]

    def set_indent(self, text: str, amount: int = 0) -> str:
        """Remove leading whitespace from each line in the text.

        Uses the first line's indentation level to determine how much to remove."""
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
