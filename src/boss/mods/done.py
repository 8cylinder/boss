# run-shell-command :: ../../build.bash

import sys
import click

from ..bash import Bash
from ..errors import *
from typing import Any


class Done(Bash):
    """Show a summary of the installation process."""

    provides = ["done"]
    requires: list[str] = []
    title = "Done"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        # https://github.com/pwaller/pyfiglet/blob/master/doc/figfont.txt
        if self.args.generate_script:
            sys.stdout.write("set +x\n")
        self.run("figlet -w89 {}".format(self.args.servername))

        # titlec = linec = (255, 148, 0)
        titlec = linec = keyc = (0, 145, 255)
        valuec = "green"

        end_tree = "└─"
        for title, info in self.info_messages.items():
            click.secho(title, fg=titlec, bold=True)
            info[-1] = (end_tree, info[-1][1], info[-1][2])
            for msg in info:
                tree_line = msg[0]
                msg_title = msg[1]
                msg_value = msg[2]
                msg_value = msg_value if msg_value.endswith(".") else msg_value + "."
                click.echo(
                    click.style(f"  {tree_line} ", fg=linec, dim=True)
                    + click.style(msg_title + ": ", fg=keyc)
                    + click.style(msg_value, fg=valuec)
                )
            print()

        sys.stdout.write("\n")
