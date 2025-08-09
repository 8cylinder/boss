"""Provides a class for managing the configuration of Netdata server monitoring.

This module focuses on the installation and configuration of Netdata, a real-time
performance monitoring tool for servers. It supports running Netdata behind
Apache2 and ensures compatibility with Ubuntu operating systems version 18.04
or greater.

Classes:
    Netdata: Handles the installation and post-installation steps for setting
             up Netdata monitoring on Ubuntu systems.
"""

from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.errors import PlatformError


class Netdata(Engine):
    """Netdata server monitoring."""

    # https://github.com/firehol/netdata
    # https://github.com/firehol/netdata/wiki/Running-behind-apache
    # https://www.digitalocean.com/community/tutorials/how-to-set-up-real-time-performance-monitoring-with-netdata-on-ubuntu-16-04
    # args: username (default:netdata), password (default:<random>)

    provides: ClassVar = ["netdata"]
    requires: ClassVar = ["apache2"]
    required_args: ClassVar = ["netdata_user_pass"]
    title = "Netdata"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Netdata engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

        if self.ubuntu == UbuntuVersion.V18_04:
            self.apt_pkgs = ["netdata"]
        else:
            err_msg = "Netdata only available on Ubuntu 18.04 or greater"
            raise PlatformError(err_msg)

        # manual install:
        # bash <(curl -Ss https://my-netdata.io/kickstart.sh) --non-interactive all

    def post_install(self) -> None:
        """Post-installation steps for Netdata."""
        if self.ubuntu == UbuntuVersion.V18_04:
            self.mod.sed(
                "s/bind socket to IP = .*$/bind socket to IP = *.*.*.*/",
                "/etc/netdata/netdata.conf",
            )
            self.mod.run("sudo systemctl restart netdata")
            self.info("URL", f"http://{self.args.servername}:19999")
