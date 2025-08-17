"""A fake SMTP server and utility for testing email sending capabilities.

This module provides a local SMTP server primarily for development and testing
purposes. It facilitates the installation and configuration of Mailhog and its
dependencies for various Ubuntu versions.

Classes:
    FakeSMTP: Handles installation, configuration, and setup of Mailhog for
    email testing.
"""

import json
import urllib.request
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.out import error


class FakeSMTP(Engine):
    """A fake SMTP server for mail testing.

    Provides a local SMTP server for development and testing purposes.
    See: https://www.lullabot.com/articles/installing-mailhog-for-ubuntu-1604
    """

    provides: ClassVar[list[str]] = ["fakesmtp"]
    requires: ClassVar[list[str]] = ["phpbin"]
    required_args: ClassVar[list[str]] = []
    title: str = "FakeSMTP (Mailhog)"
    phpini: str
    cliini: str

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize FakeSMTP with the correct php.ini paths for the Ubuntu version."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        if ubuntu_version == UbuntuVersion.V14_04:
            self.phpini = "/etc/php5/apache2/php.ini"
            self.cliini = "/etc/php5/cli/php.ini"
        elif ubuntu_version == UbuntuVersion.V16_04:
            self.phpini = "/etc/php/7.0/apache2/php.ini"
            self.cliini = "/etc/php/7.0/cli/php.ini"
        elif ubuntu_version == UbuntuVersion.V18_04:
            self.phpini = "/etc/php/7.2/apache2/php.ini"
            self.cliini = "/etc/php/7.2/cli/php.ini"
        elif ubuntu_version == UbuntuVersion.V20_04:
            self.phpini = "/etc/php/7.4/apache2/php.ini"
            self.cliini = "/etc/php/7.4/cli/php.ini"
        else:
            error("FakeSMTP: no php.ini defined for this version of Ubuntu")

    def post_install(self) -> None:
        """Perform post-installation steps.

        Install binaries, configure PHP, and start the service.
        """
        self.install_via_github()
        sedcmd = "s|;sendmail_path =|sendmail_path = /usr/local/bin/mhsendmail|"
        cmds = [
            "chmod +x mailhog mhsendmail",
            "sudo mv mailhog mhsendmail /usr/local/bin",
        ]
        [self.run(i) for i in cmds]
        self.sed(sedcmd, self.phpini)
        self.sed(sedcmd, self.cliini)

        if self.ubuntu == UbuntuVersion.V14_04:
            self.config_upstart()
        elif self.ubuntu >= UbuntuVersion.V16_04:
            self.config_systemd()

        # if self.ubuntu >= UbuntuVersion.V18_04:
        #    postfix_config = Path('/etc/postfix/main.cf')
        #    if postfix_config.exists():
        #        self.sed('s/^myhostname = .*&/myhostname = localhost/', postfix_config)
        #        self.sed('s/^relayhost = .*&/relayhostl = [127.0.0.1]:1025/', postfix_config)
        #    else:
        #        error(f'No postfix config file: {postfix_config}')

        # test if it works
        cmd = (
            "php -r \"mail('boss@example.com', 'Test from Boss', 'Test from Boss.');\""
        )
        self.run(cmd, capture=True)
        self.info("client", f"http://{self.args.servername}:8025")
        self.info(
            "api",
            f"curl http://{self.args.servername}:8025/api/v2/messages",
        )

    def install_via_go(self) -> None:
        """Stub for installing Mailhog via Go (not implemented)."""

    def install_via_github(self) -> None:
        """Download Mailhog and mhsendmail binaries from GitHub releases."""
        data = [
            {
                "release": "MailHog_linux_amd64",
                "localname": "mailhog",
                "url": "https://api.github.com/repos/mailhog/MailHog/releases/latest",
            },
            {
                "release": "mhsendmail_linux_amd64",
                "localname": "mhsendmail",
                "url": "https://api.github.com/repos/mailhog/mhsendmail/releases/latest",
            },
        ]
        # Sometimes github returns 'forbidden' when accessing the api.
        # Rate limiting maybe? I don't know.
        try:
            for prog in data:
                r = urllib.request.urlopen(prog["url"]).read()
                content = json.loads(r.decode("utf-8"))
                for asset in content["assets"]:
                    if asset["name"] == prog["release"]:
                        self.curl(asset["browser_download_url"], prog["localname"])
        except urllib.error.HTTPError as e:
            error(f"MAILHOG github api: {e.msg}")

    def config_upstart(self) -> None:
        """Configure Mailhog to run as an Upstart service (Ubuntu 14.04)."""
        service = """
            description "Mailhog"
            start on runlevel [2345]
            stop on runlevel [!2345]
            exec /usr/bin/env /usr/local/bin/mailhog > /dev/null 2>&1 &
        """
        service_file = "/etc/init/mailhog.conf"
        service = "\n".join([i[12:] for i in service.split("\n")])
        self.write_new_file(service_file, service)
        self.run(f"sudo ln -s {service_file} /etc/init.d/mailhog")
        self.run("sudo service mailhog start")

    def config_systemd(self) -> None:
        """Configure Mailhog to run as a systemd service (Ubuntu 16.04+)."""
        service = """
            [Unit]
            Description=MailHog service

            [Service]
            ExecStart=/usr/local/bin/mailhog \\\\
              -api-bind-addr 0.0.0.0:8025 \\\\
              -ui-bind-addr 0.0.0.0:8025 \\\\
              -smtp-bind-addr 0.0.0.0:1025

            [Install]
            WantedBy=multi-user.target
        """
        service_file = "/etc/systemd/system/mailhog.service"
        service = "\n".join([i[12:] for i in service.split("\n")])
        self.run(
            f"echo | sudo tee {service_file} <<EOF{service}EOF",
            wrap=False,
        )
        self.run("sudo systemctl start mailhog")
        self.run("sudo systemctl enable mailhog")
