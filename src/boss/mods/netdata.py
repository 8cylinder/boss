# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..dist import Dist
from ..errors import *


class Netdata(Bash):
    """Netdata server monitoring"""

    # https://github.com/firehol/netdata
    # https://github.com/firehol/netdata/wiki/Running-behind-apache
    # https://www.digitalocean.com/community/tutorials/how-to-set-up-real-time-performance-monitoring-with-netdata-on-ubuntu-16-04
    # args: username (default:netdata), password (default:<random>)

    provides = ["netdata"]
    requires = ["apache2"]
    title = "Netdata"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.distro >= (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ["netdata"]
        else:
            raise PlatformError("Netdata only available on Ubuntu 18.04 or greater")

        # manual install: bash <(curl -Ss https://my-netdata.io/kickstart.sh) --non-interactive all

    def post_install(self):
        if self.distro >= (Dist.UBUNTU, Dist.V18_04):
            self.sed(
                "s/bind socket to IP = .*$/bind socket to IP = *.*.*.*/",
                "/etc/netdata/netdata.conf",
            )
            self.run("sudo systemctl restart netdata")
            self.info("URL", "http://{}:19999".format(self.args.servername))
