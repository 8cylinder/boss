from ..bash import Bash, Snap, Settings
from ..dist import Dist
from ..errors import *


class First(Bash):
    """Install misc apps that are useful.

    - The timezone is set to the value in Settings.timezone
    - Emacs is configured as the default editor.
    """

    provides = ["first"]
    requires = []
    title = "First"

    def __init__(self, *args, **kwargs):
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
            ]
            self.snap_pkgs: list[tuple[str, Snap]] = [
                ("emacs", Snap.CLASSIC),
                ("node", Snap.CLASSIC),
            ]

    def post_install(self):
        # Don't use this, install the parts individually.
        # self.install_web_server()

        self.set_timezone()

    def set_timezone(self):
        self.run("sudo timedatectl set-timezone {}".format(Settings.timezone))

    def install_web_server(self):
        # Add 'tasksel' to apt_pkgs
        self.run("sudo tasksel install web-server")
