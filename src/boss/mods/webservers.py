from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class Apache2(Engine):
    """Stand-alone Apache.

    With a default site at /var/www/html.
    """

    provides: ClassVar = ["apache2"]
    requires: ClassVar = []
    required_args: ClassVar = []
    title = "Apache2"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Apache2 engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

        self.apt_pkgs = ["apache2", "fail2ban"]

    # def post_install(self) -> None:
    #     # add a test html file in the default document root
    #     self.run("sudo mkdir -p /var/www/html")
    #     self.run("sudo chown www-data:www-data /var/www/html")
    #     # self.run("echo '<h1>Apache2 is running</h1>' | sudo tee /var/www/html/index.html")
    #     html_file = '<h1>Apache2 is running</h1>'
    #     self.append_to_file('index.html', html_file)


class Nginx(Engine):
    """Stand-alone Nginx."""

    provides: ClassVar = ["nginx"]
    requires: ClassVar = []
    required_args: ClassVar = []
    title = "Nginx"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Nginx engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.apt_pkgs = ["nginx"]
