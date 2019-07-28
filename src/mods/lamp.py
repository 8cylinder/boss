# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist

from mods.webservers import Apache2
from mods.webservers import Nginx
from mods.databases import Mysql
from mods.php import Php


class Lamp(Apache2, Mysql):
    """The whole shebang

    This runs `apt-get install lamp-server^`

    Installed packages.  Use `apt show lamp-server^ | grep Package:` for
    details.

    perl, apache2, apache2-bin, apache2-utils, apache2-data, ssl-cert,
    php7.0-cli, php7.0-common, php7.0-json, php7.0-opcache,
    mysql-common, perl-modules-5.22, tcpd, mysql-client-5.7,
    mysql-client-core-5.7, mysql-server, mysql-server-5.7,
    mysql-server-core-5.7, rename, php-common, php-mysql,
    php7.0-mysql, php7.0-readline"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['apache2', 'php', 'mysql', 'lamp']
        self.apt_pkgs = ['lamp-server^']

    def pre_install(self):
        for cls in Lamp.__bases__:
            cls.pre_install(self)

    def post_install(self):
        for cls in Lamp.__bases__:
            cls.post_install(self)

        self.run('sudo service apache2 restart')
