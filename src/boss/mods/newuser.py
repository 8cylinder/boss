# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..errors import *
from typing import Any


class NewUser(Bash):
    """Create a new user

    Create a new user and add them to the sudo and www-data groups.
    Also make the new user's sudo session not expire until logout."""

    provides = ["newuser"]
    requires = ["first"]
    title = "New user"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        username, password = self.args.new_system_user_and_pass

        self.run(
            f"""if ! id -u {username} &>/dev/null; then 
            sudo useradd --shell=/bin/bash --create-home --password $(mkpasswd -m sha-512 {password}) {username}; 
            fi"""
        )
        self.run("### or if using these commands interactively, use:")
        self.run(f"# adduser {username}...")
        # add user to some groups
        for group in ("sudo", "www-data"):
            self.run(
                "sudo usermod -aG {group} {username}".format(
                    group=group, username=username
                )
            )

        # make user not need a password for sudo
        # filename cannot have a . or ~
        sudo_file = "/etc/sudoers.d/{}-{}".format(self.scriptname, username)
        self.run(
            "echo '{} ALL=(ALL) NOPASSWD:ALL' | sudo tee {}".format(username, sudo_file)
        )
