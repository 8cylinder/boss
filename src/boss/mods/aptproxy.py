# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..dist import Dist
from ..errors import *


class AptProxy(Bash):
    """Use the host machine's apt proxy

    apt-cacher-ng needs to be installed and configured on the host:
    1. sudo apt install apt-cacher-ng
    2. echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' | sudo tee /etc/apt/apt.conf.d/00aptproxy

    Installation can be checked by going to http://<HOST IP>:3142/acng-report.html

    Then when using the `aptproxy` module, it will create a config
    file in apt.conf.d to configure apt to use the host's apt cache by
    running the following command:
    `echo 'Acquire::http::Proxy "http://<HOST IP>:3142";' | sudo tee /etc/apt/apt.conf.d/00aptproxy`"""

    conf_file = '/etc/apt/apt.conf.d/00aptproxy'

    provides = ['aptproxy']
    requires = []
    title = 'Apt Proxy'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_install(self):
        host_ip = self.args.host_ip
        proxy_setting = '\'Acquire::http::Proxy "http://{}:3142";\''.format(host_ip)
        cmd = 'echo {setting} | sudo tee {ip}'.format(
            setting=proxy_setting,
            ip=self.conf_file
        )
        self.run(cmd)
