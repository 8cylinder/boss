# run-shell-command :: ../../build.bash

import os
from bash import Bash
from dist import Dist
from errors import *


class Bashrc(Bash):
    """A custom bashrc from GitHub and symlink boss to ~/bin/

    1. Downloads a bashrc from GitHub and creates a bin dir in the $HOME dir.
    2. Backups the orginal .bashrc
    3. Symlinks the ~/bin/bashrc to ~/.bashrc
    4. Symlink /project/boss to ~/bin/boss"""

    provides = ['bashrc']
    requires = []
    title = 'Custom .bashrc'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['emacs-nox']

    def install_bashrc(self):
        self.run('if [[ ! -d $HOME/bin ]]; then mkdir $HOME/bin; fi')
        gh_files = {
            'bashrc': 'https://raw.githubusercontent.com/8cylinder/bin/master/bashrc',
            'bashrc_prompt.py': 'https://raw.githubusercontent.com/8cylinder/bin/master/bashrc_prompt.py',
            'bashrc_prompt.themes': 'https://raw.githubusercontent.com/8cylinder/bin/master/bashrc_prompt.themes',
        }
        for ghname, ghurl in gh_files.items():
            self.curl(ghurl, '$HOME/bin/' + ghname)

        # if .bashrc is not a link, back it up
        self.run('if [[ ! -L $HOME/.bashrc ]]; then mv $HOME/.bashrc $HOME/.bashrc.original; fi')
        # if .bashrc does not exist, make a link to bin/bashrc
        self.run('if [[ ! -e $HOME/.bashrc ]]; then ln -s $HOME/bin/bashrc $HOME/.bashrc; fi')
        # self.run('echo -e "\n\nalias emacs=\'jmacs\'\n" >> $HOME/bin/bashrc')
        self.run('chmod +x $HOME/bin/bashrc_prompt.py')

    def link_boss(self):
        source = __file__
        name = os.path.basename(source)
        dest = os.path.expanduser(os.path.join('$HOME/bin', name))
        self.run('if [[ ! -h {} ]]; then ln -s {} {}; fi'.format(dest, source, dest))

    def post_install(self):
        self.install_bashrc()
        self.link_boss()

    def uninstall(self):
        self.run('if [[ -d $HOME/bin ]]; then sudo rm -rf $HOME/bin; fi')
        # if .bashrc.original exists, restore it
        self.run('if [[ -e $HOME/.bashrc.original ]]; then mv .bashrc.original .bashrc; fi')
