import re
import sys
from typing import Any

import click

from boss.engine import Engine


class Last(Engine):
    """Show a summary of the installation process."""

    provides = ["done"]
    requires: list[str] = []
    required_args: list[str] = []
    title = "Done"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        # https://github.com/pwaller/pyfiglet/blob/master/doc/figfont.txt
        script_mode = False
        if self.args.generate_script:
            sys.stdout.write("set +x\n")
            script_mode = True
        if servername := self.args.servername:
            self.mod.run(f"figlet -w89 {servername}")

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
                msg_value = re.sub(r"\.$", "", msg_value)  # remove trailing period
                click.echo(
                    click.style(f"  {tree_line} ", fg=linec, dim=True)
                    + click.style(msg_title + ": ", fg=keyc)
                    + click.style(msg_value, fg=valuec),
                    err=script_mode,
                )
            print()

        sys.stdout.write("\n")
