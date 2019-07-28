# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist


class PhpMyAdmin(Bash):
    """Web database client

    Access at http://<servername>/phpmyadmin
    Use the root username and the password specified via --db_root_pass
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['phpmyadmin']
        self.requires = ['apache2', 'php', 'mysql']
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

    def post_install(self):
        # self.info('PhpMyadmin', 'https://{}/phpmyadmin'.format(self.args.servername))
        pass
