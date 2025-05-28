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

        for title, msg in self.info_messages:
            if self.args.generate_script:
                sys.stdout.write("echo '{:20} {}'\n".format(title + ":", msg))
            else:
                click.echo(
                    "{:30} {}".format(
                        click.style(title, fg="white"), click.style(msg, fg="blue")
                    )
                )
            sys.stdout.flush()

        sys.stdout.write("\n")
