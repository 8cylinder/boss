# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist


class NewUser(Bash):
    """Create a new user

    Create a new user and add them to the sudo and www-data groups.
    The new user does not require a password for sudo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['newuser']
        self.requires = ['first']

    def pre_install(self):
        username, password = self.args.new_system_user_and_pass

        self.run('if ! id -u {username} &>/dev/null; then sudo useradd --shell=/bin/bash --create-home --password \
                  $(mkpasswd -m sha-512 {password}) {username}; fi'.format(
            password=password, username=username
        ))
        self.run('### or if using these commands interactively, use:')
        self.run('# adduser {username}...'.format(username=username, password=password))
        # add user to some groups
        for group in ('sudo', 'www-data'):
            self.run('sudo usermod -aG {group} {username}'.format(
                group=group,
                username=username
            ))
        # make user not need a password for sudo
        sudo_file = '/etc/sudoers.d/{}-{}'.format(self.scriptname, username)  # filename cannot have a . or ~
        self.run("echo '{} ALL=(ALL) NOPASSWD:ALL' | sudo tee {}".format(username, sudo_file))
