# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class Mysql(Bash):
    """Mysql db and password configuration

    Requires root's password and new db to create.  Optionally, a new
    user can be created.

    root's password: --db-root-password=PASSWORD
    New db: --db-name=DBNAME
    Optional new user and password: --new-db-user-and-pass=USER,PASSWORD
    """

    provides = ['mysql']
    requires = []
    title = 'MySQL'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['mysql-server']

    def configure_root_password(self):
        root_pass = self.args.db_root_pass
        self.run('''sudo debconf-set-selections <<< \
            "mysql-server mysql-server/root_password password {}"'''.format(root_pass))
        self.run('''sudo debconf-set-selections <<< \
            "mysql-server mysql-server/root_password_again password {}"'''.format(root_pass))

    def setup_user(self, db_user, db_pass, root_pass):
        # only for MySQL 5.7.8 and up?
        sql = '''
        DROP USER IF EXISTS '{db_user}'@'localhost';
          CREATE USER '{db_user}'@'localhost'
            IDENTIFIED BY '{db_pass}';
          GRANT ALL PRIVILEGES ON * . * TO '{db_user}'@'localhost';
          FLUSH PRIVILEGES;
        '''.format(
            db_user=db_user,
            db_pass=db_pass
        )
        self.run('mysql -uroot -p{root_pass} <<EOF\n{sql}\nEOF'.format(
            root_pass=root_pass,
            sql=sql), wrap=False)

    def create_schema(self, db_name, root_pass):
        sql = ' '.join('''
          DROP DATABASE IF EXISTS {db_name};
          CREATE DATABASE IF NOT EXISTS {db_name};
        '''.format(
            db_name=db_name,
        ).split())
        self.run('mysql -uroot -p{root_pass} <<EOF\n{sql}\nEOF'.format(
            root_pass=root_pass,
            sql=sql
        ), wrap=False)

    def import_sql(self, root_pass, sql_file):
        self.run('mysql -uroot -p{root_pass} < {sql_file}'.format(
            root_pass=root_pass,
            sql_file=sql_file
        ))

    def pre_install(self):
        self.configure_root_password()

    def post_install(self):
        if self.args.new_db_user_and_pass:
            db_user, db_pass = self.args.new_db_user_and_pass
            self.setup_user(db_user, db_pass, self.args.db_root_pass)
        if self.args.db_name:
            self.create_schema(self.args.db_name, self.args.db_root_pass)
        if self.args.sql_file:
            self.import_sql(self.args.db_root_pass, self.args.sql_file)


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
