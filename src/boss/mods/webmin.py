# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..dist import Dist
from ..errors import *


class Webmin(Bash):
    provides = ['webmin']
    requires = ['apache2', 'php', 'cert']
    title = 'Webmin console'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['webmin']

    def pre_install(self):
        # add webmin to sources.list, get PGP key
        cmds = [
            'sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak',
            'echo "deb http://download.webmin.com/download/repository sarge contrib" | sudo tee -a /etc/apt/sources.list',
            # 'wget http://www.webmin.com/jcameron-key.asc',
            # 'sudo apt-key add jcameron-key.asc',
        ]
        self.curl('http://www.webmin.com/jcameron-key.asc', 'jcameron-key.asc')
        self.run('sudo apt-key add jcameron-key.asc')
        for cmd in cmds:
            global APTUPDATED
            APTUPDATED = False
            self.run(cmd)

        self.info('Webmin', 'http://{}:10000 (user & password for any user that can sudo)'.format(self.args.servername))
