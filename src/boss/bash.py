import os
import sys
import re
from .dist import Dist
import datetime
import subprocess
from typing import NamedTuple, Any
from dataclasses import dataclass
from .errors import CommandError, DependencyError
from .util import display_cmd, error, notify
from enum import Enum, auto
from pathlib import Path


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


class ModBase:
    """Base class for modules that can switch between Bash and Ansible implementations.

    Example usage:
    ```python
    from boss.mods import ModBase, ModType
    from boss.mods.bash import Bash
    from boss.mods.ansible import Ansible
    ModBase.set_mod_type(ModType.BASH)  # or ModType.ANSIBLE
    class MyModule(ModBase):
        provides = ["my_module"]
        requires = ["some_dependency"]
        required_args = ["arg1", "arg2"]
        title = "My Module"
    ```
    """

    _mod_type: ModType = ModType.BASH

    @classmethod
    def set_mod_type(cls, mod_type: ModType) -> None:
        """Set the module type to either bash or ansible."""
        cls._mod_type = mod_type

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Dynamically set the parent class based on _mod_type."""
        super().__init_subclass__(**kwargs)

        # # Import here to avoid circular imports
        # from .bash import Bash
        # from .ansible import Ansible

        # Map mod types to their implementation classes
        implementations = {
            ModType.BASH: Bash,
            ModType.ANSIBLE: Ansible,
        }

        # Get current bases except ModBase
        current_bases = tuple(b for b in cls.__bases__ if b is not ModBase)

        # Set new bases with the correct implementation
        cls.__bases__ = (implementations[cls._mod_type],) + current_bases


class Ansible:
    """Ansible implementation with the same API as Bash class."""

    APTUPDATED = False
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
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

    def ensure_arg_requirements(self) -> None:
        pass

    def sed(self, sed_exp: str, config_file: str) -> None:
        pass

    def write_new_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
    ) -> None:
        pass

    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
        append: bool = True,
    ) -> None:
        pass

    def apt(self, progs: list[str]) -> None:
        pass

    def install(self) -> None:
        pass

    def is_apt_installed(self, package_name: str) -> bool:
        return True

    def pre_install(self) -> None:
        pass

    def post_install(self) -> None:
        pass

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
