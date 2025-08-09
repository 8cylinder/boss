"""Provide a class to handle the Boss CLI commands.

The Engine class which is inherited by all modules in the Boss CLI framework.

And the Bash and Ansible classes which are used by the Engine class implement
the relevant methods for each environment.
"""

import re
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine


class NewUserAsRoot(Engine):
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
    - Set up ssh access using the root user's .ssh directory
    - Disables root login and password authentication via SSH

    Note:
        This class assumes root privileges are available for execution.  Sudo is not
        used in this class.

    """

    provides: ClassVar = ["newuserasroot"]
    requires: ClassVar = []
    required_args: ClassVar = ["new_system_user_and_pass"]
    title = "New user (as root)"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the NewUserAsRoot engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def pre_install(self) -> None:
        """Pre-installation steps for creating a new user."""
        username, password = self.args.new_system_user_and_pass

        self.mod.run(
            f"""if ! id -u {username} &>/dev/null; then
            useradd --shell=/bin/bash --create-home \
              --password $(mkpasswd -m sha-512 {password}) {username};
            fi""",
        )

        # add user to some groups
        for group in ("sudo", "www-data"):
            self.mod.run(
                f"usermod -aG {group} {username}",
            )

        # copy root .ssh to new user's .ssh
        self.mod.run(f"cp -r .ssh /home/{username}/")
        self.mod.run(f"chown -R {username}:{username} /home/{username}/.ssh")

        ssh_conf = "/etc/ssh/sshd_config"

        # disable root login via ssh
        self.mod.sed("s/#*PermitRootLogin.*/PermitRootLogin no/", ssh_conf)

        # disable password login via ssh
        self.mod.sed(
            "s/#*PasswordAuthentication.*/PasswordAuthentication no/",
            ssh_conf,
        )

        # Make sudo last for the user's session length.
        self.mod.run("echo 'Defaults timestamp_timeout=-1' | EDITOR='tee -a' visudo")

        self.info(
            "New user created",
            "Try logging in in another terminal to test user.",
        )
        self.info("ssh", f"ssh {username}@{self.args.servername}")


class Personalize(Engine):
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

    provides: ClassVar = ["personalize"]
    requires: ClassVar = ["first"]
    required_args: ClassVar = []
    title = "Personalize"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Personalize engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def pre_install(self) -> None:
        """Pre-installation steps for personalizing the user's environment."""
        # add user to some groups
        for group in ("sudo", "www-data"):
            self.mod.run(f"sudo usermod -aG {group} $USER")

        self.bash_settings()
        self.emacs_settings()

    def bash_settings(self) -> None:
        """Set up some bash settings for the user."""
        bashrc = "$HOME/.bashrc"
        editor = "emacs"
        bash_settings = rf"""
          # Added by Boss on {self.now}
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
        """  # noqa: E501
        # strip off the leading spaces
        settings = "\n".join(
            [re.sub(r"^\s*", "", i) for i in bash_settings.split("\n")],
        )
        self.mod.append_to_file(bashrc, settings, backup=True, nosudo=True)

    def emacs_settings(self) -> None:
        """Set up some emacs settings for the user."""
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
        settings = self.set_indent(emacs_settings)
        self.mod.write_new_file(dot_emacs, settings, nosudo=True)
        self.mod.write_new_file(root_dot_emacs, settings)
