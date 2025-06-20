# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..errors import *


class Webmin(Bash):
    """Webmin console"""

    provides = ["webmin"]
    requires = ["apache2", "phpbin", "cert"]
    title = "Webmin console"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ["webmin"]

    def pre_install(self):
        # add webmin to sources.list, get PGP key
        cmds = [
            "sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak",
            'echo "deb http://download.webmin.com/download/repository sarge contrib" | sudo tee -a /etc/apt/sources.list',
            # 'wget http://www.webmin.com/jcameron-key.asc',
            # 'sudo apt-key add jcameron-key.asc',
        ]
        self.curl("http://www.webmin.com/jcameron-key.asc", "jcameron-key.asc")
        self.run("sudo apt-key add jcameron-key.asc")
        for cmd in cmds:
            global APTUPDATED
            APTUPDATED = False
            self.run(cmd)

        self.info(
            "URL",
            f"http://{self.args.servername}:10000 (user & password for any user that can sudo)",
        )
