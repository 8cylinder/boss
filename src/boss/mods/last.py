import re
import sys
from typing import Any, ClassVar

import click
import yaml

from boss import out
from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class Last(Engine):
    """Show a summary of the installation process."""

    provides: ClassVar = ["done"]
    requires: ClassVar = []
    required_args: ClassVar = []
    title = "Done"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Last engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def pre_install(self) -> None:
        """Pre-installation steps for the Last engine."""
        if not self.args.bash:
            self.output_playbook(self.playbook)

        elif self.args.generate_script:
            sys.stdout.write("set +x\n")

        # https://github.com/pwaller/pyfiglet/blob/master/doc/figfont.txt
        if servername := self.args.servername:
            self.run(f"figlet -w89 {servername}")

        # titlec = linec = (255, 148, 0)
        titlec = linec = keyc = (0, 145, 255)
        valuec = "green"

        end_tree = "└─"
        for title, info in self.info_messages.items():
            out.print_fd(click.style(title, fg=titlec, bold=True), fd=out.FD.INFO)
            info[-1] = (end_tree, info[-1][1], info[-1][2])
            for msg in info:
                tree_line = msg[0]
                msg_title = msg[1]
                msg_value = msg[2]
                msg_value = re.sub(r"\.$", "", msg_value)  # remove trailing period
                out.print_fd(
                    click.style(f"  {tree_line} ", fg=linec, dim=True)
                    + click.style(msg_title + ": ", fg=keyc)
                    + click.style(msg_value, fg=valuec),
                    fd=out.FD.INFO,
                )
            click.echo()

        sys.stdout.write("\n")

    def output_playbook(self, playbook: list[dict[str, Any]]) -> None:
        """Output the Ansible playbook."""
        yaml_content = yaml.dump(playbook, default_flow_style=False)
        out.print_fd(yaml_content)
