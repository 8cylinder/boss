from typing import Any

from boss.dist import Dist
from boss.engine import Engine, Settings


class First(Engine):
    """Install misc apps that are useful.

    - The timezone is set to the value in Settings.timezone.
    - Emacs is configured as the default editor.
    """

    provides = ["first"]
    requires: list[str] = []
    required_args = []
    title = "First"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.distro == (Dist.UBUNTU, Dist.V14_04):
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
        elif (Dist.UBUNTU, Dist.V14_04) < self.distro < (Dist.UBUNTU, Dist.V22_04):
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
        elif self.distro == (Dist.UBUNTU, Dist.V24_04):
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
        self.mod.run("sudo apt-get update")
        self.mod.run("sudo apt-get upgrade -y")

    def post_install(self) -> None:
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
        self.mod.run(f"sudo timedatectl set-timezone {Settings.timezone}")

    def install_web_server(self) -> None:
        # Add 'tasksel' to apt_pkgs
        self.mod.run("sudo tasksel install web-server")
