from ..errors import *
from typing import Any
from ..bash import ModBase


class Firewall(ModBase):
    """Enable and configure the firewall.

    Set up for ssh and Apache2 if installed.
    """

    provides = ["firewall"]
    requires: list[str] = []
    required_args: list[str] = []
    title = "Firewall"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

    def post_install(self) -> None:
        self.mod.run("sudo ufw allow OpenSSH")

        # if Apache2 in self.args.wanted:
        #     # If Apache2 is installed, allow HTTP and HTTPS traffic.
        #     self.run('sudo ufw allow in "Apache"')

        if self.is_apt_installed("apache2"):
            # If Apache2 is installed, allow HTTP and HTTPS traffic.
            self.mod.run('sudo ufw allow in "Apache"')

        self.mod.run("sudo ufw enable")

        self.mod.run("sudo ufw status")
