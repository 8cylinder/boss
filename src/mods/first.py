# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class First(Bash):
    """Misc apps that are useful

    The timezone is set to America/Los_Angeles and Emacs is configured
    as the defalt editor.
    """
    provides = ['first']
    requires = []
    title = 'First'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.distro > (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = [
                'tree', 'elinks', 'virt-what', 'silversearcher-ag', 'unzip',
                'htop', 'source-highlight', 'whois', 'curl', 'figlet', 'ntp',
            ]
            # self.apt_pkgs += ['joe']
            self.apt_pkgs += ['emacs-nox'] # adds aprox 100mb
        elif self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = [
                'tree', 'elinks', 'virt-what', 'silversearcher-ag', 'unzip',
                'htop', 'source-highlight', 'whois', 'curl', 'figlet'
            ]
            # self.apt_pkgs += ['joe']
            self.apt_pkgs += ['emacs24-nox'] # adds aprox 100mb

    def pre_install(self):
        pass

    def post_install(self):
        # set timezone
        tz = 'America/Los_Angeles'
        self.run('sudo timedatectl set-timezone {}'.format(tz))

        # configure the editor
        # editor = 'jmacs'
        editor = 'emacs'
        cmds = [
            "echo export EDITOR='{}' >> $HOME/.bashrc".format(editor),
            "echo export VISUAL='{}' >> $HOME/.bashrc".format(editor),
            "echo export SUDO_EDITOR='{}' >> $HOME/.bashrc".format(editor),
        ]
        if editor == 'jmacs':
            cmds += ["echo alias emacs='jmacs' >> $HOME/.bashrc"]
        for cmd in cmds:
            self.run(cmd)
