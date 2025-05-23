# run-shell-command :: ../../build.bash

from ..bash import Bash
from ..dist import Dist
from ..errors import *


class First(Bash):
    """Misc apps that are useful

    The timezone is set to "America/Los_Angeles" and Emacs is configured
    as the default editor.
    """

    provides = ["first"]
    requires = []
    title = "First"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.distro > (Dist.UBUNTU, Dist.V14_04):
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
        elif self.distro == (Dist.UBUNTU, Dist.V14_04):
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

    def pre_install(self):
        pass

    def post_install(self):
        # set timezone
        tz = "America/Los_Angeles"
        self.run("sudo timedatectl set-timezone {}".format(tz))

        self.bash_settings()

    def bash_settings(self):
        bashrc = "$HOME/.bashrc"
        editor = "emacs"
        settings = """
          PS1='\n${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\n\$ '

          alias ls='LC_ALL=C ls --almost-all --classify --human-readable --color=auto --group-directories-first'
          alias time='/usr/bin/time --format="Time elapsed: %E"'
          alias pss='ps -Af | grep -i $1'
          alias grep='grep --color=auto'
          alias tree='tree --dirsfirst'
          alias gs='git status'
          alias gl='git log --name-only'
          alias gls='git log --pretty=format:"%ad  %s" --date=short'

          export HISTSIZE=-1
          export HISTFILESIZE=-1
          export HISTTIMEFORMAT="%F %T "
          shopt -s histappend

          export EDITOR=emacs
          export VISUAL=emacs
          export SUDO_EDITOR=emacs
        """

        settings = "\n".join([i[10:] for i in settings.split("\n")])
        self.append_to_file(bashrc, settings, backup=True)
