# run-shell-command :: ../../build.bash

from ..bash import Bash
from typing import Any


class AptProxy(Bash):
    """Use the host machine's apt proxy.

    apt-cacher-ng needs to be installed and configured on the host:
    1. sudo apt install apt-cacher-ng
    2. echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' | sudo tee /etc/apt/apt.conf.d/00aptproxy

    Installation can be checked by going to http://<HOST IP>:3142/acng-report.html

    Then when using the `aptproxy` module, it will create a config
    file in apt.conf.d to configure apt to use the host's apt cache by
    running the following command:
    `echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' | sudo tee /etc/apt/apt.conf.d/00aptproxy`"""

    conf_file = "/etc/apt/apt.conf.d/00aptproxy"

    provides = ["aptproxy"]
    requires: list[str] = []
    title = "Apt Proxy"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def post_install(self) -> None:
        host_ip = self.args.host_ip
        proxy_setting = f"""'Acquire::http::Proxy "http://{host_ip}:3142";'"""
        cmd = f"echo {proxy_setting} | sudo tee {self.conf_file}"
        self.run(cmd)
