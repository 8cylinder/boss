"""A module to run bash commands."""

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

from boss.common import Args, Snap
from boss.errors import CommandError
from boss.util import display_cmd, error, notify


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
