"""Generate an Ansible playbook for server configuration."""

import datetime
import os
from pathlib import Path
from typing import Any, ClassVar

from boss.common import Args, Snap


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
        nosudo: bool = False,  # noqa: ARG002
    ) -> None:
        """Create a new file from text using Ansible's copy module."""
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

    # @warn('"append_to_file(...)" is untested in Ansible.')
    def append_to_file(
        self,
        filename: str | Path,
        text: str,
        user: str | None = None,  # noqa: ARG002 - keep for compatibility with Bash
        nosudo: bool = False,  # noqa: ARG002 - keep for compatibility with Bash
        backup: bool = True,
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
        cmd: str,  # noqa: ARG002
        wrap: bool = True,  # noqa: ARG002
        capture: bool = False,  # noqa: ARG002
        comment: str = "",  # noqa: ARG002
    ) -> str:
        """Run a command using Ansible's shell module."""
        return ""

    def curl(
        self,
        url: str,
        output: str,
        capture: bool = False,
    ) -> str | int | bytes | None:
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
