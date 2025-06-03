import re
from ..bash import Bash
from ..errors import *
from typing import Any


class NewUserAsRoot(Bash):
    """Create a new user assuming the current user is root.

    This class provides functionality to create a new system user with appropriate
    shell access and group permissions. It handles user creation, password setup,
    and additional system configurations.

    The class performs the following operations:
    - Creates a new user with /bin/bash as the default shell
    - Creates the user's home directory
    - Configures the user's password using SHA-512 encryption
    - Adds the user to 'sudo' and 'www-data' groups
    - Configures sudo to maintain authentication for the user's session duration

    Note:
        This class assumes root privileges are available for execution.  Sudo is not
        used in this class.
    """

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
                "usermod -aG {group} {username}".format(group=group, username=username)
            )

        # modify ssh.conf to allow passwords

        # Option A is only for local dev machines, option B should be used instead.
        #
        # A)
        # Make user not need a password for sudo.
        # filename cannot have a . or ~
        # sudo_file = "/etc/sudoers.d/{}-{}".format(self.scriptname, username)
        # self.run(
        #    "echo '{} ALL=(ALL) NOPASSWD:ALL' | tee {}".format(username, sudo_file)
        # )
        #
        # B)
        # Make sudo last for the user's session length.
        self.run("echo 'Defaults timestamp_timeout=-1' | EDITOR='tee -a' visudo")

        self.info(
            "New user created", "Try logging in in another terminal to test user."
        )


class Personalize(Bash):
    """Personalize the user's environment with custom configurations.

    This class handles the customization of a user's shell and editor environment by
    configuring bash and emacs settings. It sets up various shell aliases, prompt
    customization, history settings, and editor preferences.

    The class performs the following configurations:
    - Customizes the bash prompt (PS1) with color-coded user, host, and path info
    - Sets up useful shell aliases for common commands like ls, grep, and tree
    - Configures bash history settings for better command history tracking
    - Sets default editor preferences for regular, visual, and sudo operations
    - Configures emacs with custom theme (modus-vivendi) and interface settings
    """

    provides = ["personalize"]
    requires = ["first"]
    title = "Personalize"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

    def pre_install(self) -> None:
        # add user to some groups
        for group in ("sudo", "www-data"):
            self.run(f"sudo usermod -aG {group} $USER")

        self.bash_settings()
        self.emacs_settings()

    def bash_settings(self) -> None:
        bashrc = "$HOME/.bashrc"
        editor = "emacs"
        bash_settings = rf"""
          #PS1='\n${{debian_chroot:+($debian_chroot)}}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\n\$ '
          PS1='\n\[\e[38;5;214m\]\u@\H\[\e[0m\] \[\e[38;5;131m\]\A\[\e[0m\] \[\e[38;5;39m\]\w\n\[\e[0m\]\$ '
          
          LESS_PIPE="/usr/share/source-highlight/src-hilite-lesspipe.sh"
          export LESSOPEN="| $LESS_PIPE %s"
          export LESS=' -R -F --HILITE-UNREAD --chop-long-lines --ignore-case --tabs=4 --window=-5 '
          
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
        self.append_to_file(bashrc, settings, backup=True, nosudo=True)

    def emacs_settings(self) -> None:
        dot_emacs = "$HOME/.emacs"
        root_dot_emacs = "/root/.emacs"
        emacs_settings = """
          ;;; -*- lexical-binding: t -*-
          (custom-set-variables
           '(backup-directory-alist '(("." . "~/.emacs-backup")))
           '(custom-enabled-themes '(modus-vivendi))
           '(menu-bar-mode nil))
          (custom-set-faces)
        """
        # strip off the leading spaces
        settings = "\n".join(
            [re.sub(r"^\s*", "", i) for i in emacs_settings.split("\n")]
        )
        self.write_new_file(dot_emacs, settings)
        self.write_new_file(root_dot_emacs, settings)
