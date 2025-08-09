"""Configures the host machine's apt proxy for apt-cacher-ng.

The module facilitates the usage of the apt-cacher-ng service by automatically
creating and applying a configuration file in apt.conf.d. Users must install
and configure apt-cacher-ng on the host machine prior to using this module.
"""

from typing import ClassVar

from boss.engine import Engine


class AptProxy(Engine):
    """Use the host machine's apt proxy.

    apt-cacher-ng needs to be installed and configured on the host:

    1. sudo apt install apt-cacher-ng
    2. echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' \
       | sudo tee /etc/apt/apt.conf.d/00aptproxy

    Installation can be checked by going to http://<HOST IP>:3142/acng-report.html

    Then when using the `aptproxy` module, it will create a config
    file in apt.conf.d to configure apt to use the host's apt cache by
    running the following command:

    `echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' \
     | sudo tee /etc/apt/apt.conf.d/00aptproxy`
    """

    conf_file = "/etc/apt/apt.conf.d/00aptproxy"

    provides: ClassVar[tuple[str, ...]] = ("aptproxy",)
    requires: ClassVar[tuple[str, ...]] = ()
    required_args: ClassVar[tuple[str, ...]] = ("host_ip",)
    title = "Apt Proxy"

    def post_install(self) -> None:
        """Write apt proxy configuration pointing to the host's apt-cacher-ng."""
        host_ip = self.args.host_ip
        proxy_setting = f'\'Acquire::http::Proxy "http://{host_ip}:3142";\''
        cmd = f"echo {proxy_setting} | sudo tee {self.conf_file}"
        self.mod.run(cmd)
