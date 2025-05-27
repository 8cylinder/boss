import re
from ..bash import Bash
from ..errors import *
from typing import Any


class NewUserAsRoot(Bash):
    """Create a new user assuming the current user is root."""

    provides = ["newuserasroot"]
    requires = []
    title = "New user (as root)"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        username, password = self.args.new_system_user_and_pass

        self.run(
            f"""if ! id -u {username} &>/dev/null; then 
            useradd --shell=/bin/bash --create-home --password $(mkpasswd -m sha-512 {password}) {username}; 
            fi"""
        )
        self.run("### or if using these commands interactively, use:")
        self.run(f"# adduser {username}...")

        # add user to some groups
        for group in ("sudo", "www-data"):
            self.run(
                "usermod -aG {group} {username}".format(
                    group=group, username=username
                )
            )
            
        # modify ssh.conf to allow passwords

        # Option A is only for local dev machines, option B should be used instead.
        #
        # A)
        # Make user not need a password for sudo.
        # filename cannot have a . or ~
        # sudo_file = "/etc/sudoers.d/{}-{}".format(self.scriptname, username)
        # self.run(
        #    "echo '{} ALL=(ALL) NOPASSWD:ALL' | sudo tee {}".format(username, sudo_file)
        # )
        #
        # B)
        # Make sudo last for the user's session length.
        self.run("echo 'Defaults timestamp_timeout=-1' | EDITOR='tee -a' visudo")

        self.info('New user created', 'Try logging in in another terminal to test user.')


class Personalize(Bash):
    """Personalize the user's environment."""

    provides = ["personalize"]
    requires = ["first"]
    title = "Personalize"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        self.bash_settings()
        self.emacs_settings()

    def bash_settings(self)->None:
        bashrc = "$HOME/.bashrc"
        editor = "emacs"
        bash_settings = rf"""
          #PS1='\n${{debian_chroot:+($debian_chroot)}}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\n\$ '
          PS1='\n\[\e[38;5;214m\]\u@\H\[\e[0m\] \[\e[38;5;131m\]\A\[\e[0m\] \[\e[38;5;39m\]\w\n\[\e[0m\]\$ '
          alias ls='LC_ALL=C ls --almost-all --classify --human-readable --color=auto --group-directories-first'
          alias time='/usr/bin/time --format="Time elapsed: %E"'
          alias pss='ps -Af | grep -i $1'
          alias grep='grep --color=auto'
          alias tree='tree --dirsfirst'
          #alias gs='git status'
          #alias gl='git log --name-only'
          #alias gls='git log --pretty=format:"%ad  %s" --date=short'

          export HISTSIZE=-1
          export HISTFILESIZE=-1
          export HISTTIMEFORMAT="%F %T "
          shopt -s histappend

          export EDITOR={editor}
          export VISUAL={editor}
          export SUDO_EDITOR={editor}
        """
        # strip off the leading spaces
        settings = "\n".join(
            [re.sub(r"^\s*", "", i) for i in bash_settings.split("\n")]
        )
        self.append_to_file(bashrc, settings, backup=True)

    def emacs_settings(self)->None:
        dot_emacs = "~/.emacs"
        emacs_settings = """
          ;;; -*- lexical-binding: t -*-
          (custom-set-variables
           ;; custom-set-variables was added by Custom.
           ;; If you edit it by hand, you could mess it up, so be careful.
           ;; Your init file should contain only one such instance.
           ;; If there is more than one, they won't work right.
           '(custom-enabled-themes '(modus-vivendi))
           '(menu-bar-mode nil))
          (custom-set-faces
           ;; custom-set-faces was added by Custom.
           ;; If you edit it by hand, you could mess it up, so be careful.
           ;; Your init file should contain only one such instance.
           ;; If there is more than one, they won't work right.
           )        
        """
        # strip off the leading spaces
        settings = "\n".join(
            [re.sub(r"^\s*", "", i) for i in emacs_settings.split("\n")]
        )
        self.append_to_file(dot_emacs, settings, backup=True, append=False)
