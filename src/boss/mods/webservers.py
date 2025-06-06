# run-shell-command :: ../../build.bash
from typing import Any

from ..bash import Bash
from ..errors import *


class Apache2(Bash):
    """Stand-alone Apache

    With a default site at /var/www/html.
    """

    provides = ["apache2"]
    requires: list[str] = []
    title = "Apache2"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ["apache2", "fail2ban"]

    # def post_install(self) -> None:
    #     # add a test html file in the default document root
    #     self.run("sudo mkdir -p /var/www/html")
    #     self.run("sudo chown www-data:www-data /var/www/html")
    #     # self.run("echo '<h1>Apache2 is running</h1>' | sudo tee /var/www/html/index.html")
    #     html_file = '<h1>Apache2 is running</h1>'
    #     self.append_to_file('index.html', html_file)


class Nginx(Bash):
    """Stand-alone Nginx"""

    provides = ["nginx"]
    requires: list[str] = []
    title = "Nginx"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ["nginx"]
