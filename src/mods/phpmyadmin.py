# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class PhpMyAdmin(Bash):
    """Web database client

    Access at http://<servername>/phpmyadmin
    Use the root username and the password specified via --db_root_pass
    """

    provides = ['phpmyadmin']
    requires = ['apache2', 'php', 'mysql']
    title = 'PhpMyAdmin'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['phpmyadmin']

    def pre_install(self):
        root_pass = self.args.db_root_pass
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/reconfigure-webserver multiselect apache2"')
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/dbconfig-install boolean true"')
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/app-password-confirm password {}"'.format(root_pass))
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/reconfigure-webserver multiselect none"')

        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/mysql/admin-user string root"')
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/mysql/admin-pass password {}"'.format(root_pass))
        self.run('sudo debconf-set-selections <<< "phpmyadmin phpmyadmin/mysql/app-pass password {}"'.format(root_pass))
