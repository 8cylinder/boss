"""Install the Webmin engine for managing the Webmin console.

Webmin is a web-based interface for system administration for Unix-like systems.
"""

from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class Webmin(Engine):
    """Webmin console."""

    provides: ClassVar = ["webmin"]
    requires: ClassVar = ["apache2", "phpbin"]
    required_args: ClassVar = []
    title = "Webmin console"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Webmin engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.apt_pkgs = ["webmin"]

    def pre_install(self) -> None:
        """Pre-installation steps for Webmin."""
        # add webmin to sources.list, get PGP key
        self.mod.curl("http://www.webmin.com/jcameron-key.asc", "jcameron-key.asc")
        self.mod.run("sudo apt-key add jcameron-key.asc")
        cmds = [
            "sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak",
            'echo "deb http://download.webmin.com/download/repository sarge contrib" | sudo tee -a /etc/apt/sources.list',  # noqa: E501
            # 'wget http://www.webmin.com/jcameron-key.asc',
            # 'sudo apt-key add jcameron-key.asc',
            "sudo apt-get update",
        ]
        for cmd in cmds:
            self.mod.run(cmd)

        self.info(
            "URL",
            (
                f"http://{self.args.servername}:10000 "
                "(user & password for any user that can sudo)"
            ),
        )
