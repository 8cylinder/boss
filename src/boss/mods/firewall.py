"""Enable and configure the firewall, with setup for SSH and Apache2.

The module defines a `Firewall` class that extends the base `Engine` class
to handle firewall setup during post-installation steps. This ensures that
necessary ports for SSH and HTTP/HTTPS traffic are allowed and the firewall
is enabled with proper configurations.
"""
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class Firewall(Engine):
    """Enable and configure the firewall.

    Set up for ssh and Apache2 if installed.
    """

    provides: ClassVar = ["firewall"]
    requires: ClassVar = []
    required_args: ClassVar = []
    title = "Firewall"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Firewall engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def post_install(self) -> None:
        """Post-installation steps for the firewall."""
        self.run("sudo ufw allow OpenSSH")

        # if Apache2 in self.args.wanted:
        #     # If Apache2 is installed, allow HTTP and HTTPS traffic.
        #     self.run('sudo ufw allow in "Apache"')

        if self.is_apt_installed("apache2"):
            # If Apache2 is installed, allow HTTP and HTTPS traffic.
            self.run('sudo ufw allow in "Apache"')

        self.run("sudo ufw enable")

        self.run("sudo ufw status")
