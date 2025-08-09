"""Install miscellaneous applications and setting up system configurations.

This module focuses on setting up useful system tools, emacs as the default
editor, and configuring timezone based on provided settings. It also
incorporates version-specific adjustments for Ubuntu distributions.

Classes:
    First: Provides functionalities for configuring a system with utilities
    and software tools depending on the distribution version.
"""

from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine, Settings


class First(Engine):
    """Install misc apps that are useful.

    - The timezone is set to the value in Settings.timezone.
    - Emacs is configured as the default editor.
    """

    provides: ClassVar = ["first"]
    requires: ClassVar[list[str]] = []
    required_args: ClassVar = []
    title = "First"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the First engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        if self.ubuntu == UbuntuVersion.V14_04:
            self.apt_pkgs = [
                "tree",
                "elinks",
                "virt-what",
                "silversearcher-ag",
                "unzip",
                "htop",
                "source-highlight",
                "whois",
                "curl",
                "figlet",
            ]
            # self.apt_pkgs += ['joe']
            self.apt_pkgs += ["emacs24-nox"]  # adds aprox 100mb
        elif UbuntuVersion.V14_04 < self.ubuntu < UbuntuVersion.V22_04:
            self.apt_pkgs = [
                "tree",
                "elinks",
                "virt-what",
                "silversearcher-ag",
                "unzip",
                "zip",
                "htop",
                "source-highlight",
                "whois",
                "curl",
                "figlet",
                "ntp",
                "locate",
            ]
            # self.apt_pkgs += ['joe']
            self.apt_pkgs += ["emacs-nox"]  # adds aprox 100mb
        elif self.ubuntu == UbuntuVersion.V24_04:
            self.apt_pkgs = [
                "tree",
                "virt-what",
                "ripgrep",
                "unzip",
                "zip",
                "htop",
                "source-highlight",
                "figlet",
                "fail2ban",
                "ssh",
                "trash-cli",
                # "npm",
                # "emacs-nox",  # installs postfix, use command in post_install
            ]
            # self.snap_pkgs: list[tuple[str, Snap]] = [
            #     ("node", Snap.CLASSIC),
            # ]

    def pre_install(self) -> None:
        """Pre-installation steps for First."""
        self.mod.run("sudo apt-get update")
        self.mod.run("sudo apt-get upgrade -y")

    def post_install(self) -> None:
        """Post-installation steps for First."""
        self.set_timezone()

        # install emacs-nox without postfix
        self.mod.run("sudo apt install -y --no-install-recommends emacs-nox")

        # Restart fail2ban
        # `systemctl status fail2ban.service` reports warning: "The unit file,
        # source configuration file or drop-ins of fail2ban.service changed on disk."
        # restarting it seems to fix this.
        if self.is_apt_installed("fail2ban"):
            self.mod.run("sudo systemctl restart fail2ban.service")

    def set_timezone(self) -> None:
        """Set the system timezone based on Settings.timezone."""
        self.mod.run(f"sudo timedatectl set-timezone {Settings.timezone}")

    def install_web_server(self) -> None:
        """Install a web server using tasksel."""
        # Add 'tasksel' to apt_pkgs
        self.mod.run("sudo tasksel install web-server")
