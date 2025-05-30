# run-shell-command :: ../../build.bash

import sys
import click

from ..bash import Bash
from ..errors import *


class Done(Bash):
    provides = ["done"]
    requires = []
    title = "Done"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pre_install(self):
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
                click.echo(
                    click.style(f"  {msg[0]} ", fg=linec, dim=True)
                    + click.style(msg[1] + ": ", fg=keyc)
                    + click.style(msg[2], fg=valuec)
                )
            print()

        sys.stdout.write("\n")
