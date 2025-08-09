"""Database engines for Boss."""

from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.errors import PlatformError
from boss.util import error


class Mysql(Engine):
    """Mysql db and password configuration.

    Requires root's password and new db to create.  Optionally, a new
    user can be created.

    - root's password: --db-root-password=PASSWORD
    - New db: --db-name=DBNAME
    - Optional new user and password: --new-db-user-and-pass=USER,PASSWORD
    """

    provides: ClassVar = ["mysql"]
    requires: ClassVar[list[str]] = []
    required_args: ClassVar = ["db_name", "db_root_pass"]
    title = "MySQL"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the MySQL engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.apt_pkgs = ["mysql-server"]

    def configure_root_password(self) -> None:
        """Configure the MySQL root password."""
        root_pass = self.args.db_root_pass
        self.mod.run(
            f'''sudo debconf-set-selections <<< \
            "mysql-server mysql-server/root_password password {root_pass}"''',
        )
        self.mod.run(
            f'''sudo debconf-set-selections <<< \
            "mysql-server mysql-server/root_password_again password {root_pass}"''',
        )

    def setup_user(self, db_user: str, db_pass: str, root_pass: str) -> None:
        """Set up a new MySQL user with privileges."""
        # only for MySQL 5.7.8 and up?
        sql = f"""
        DROP USER IF EXISTS '{db_user}'@'localhost';
          CREATE USER '{db_user}'@'localhost'
            IDENTIFIED BY '{db_pass}';
          GRANT ALL PRIVILEGES ON * . * TO '{db_user}'@'localhost';
          FLUSH PRIVILEGES;
        """
        self.mod.run(
            f"mysql -uroot -p{root_pass} <<EOF\n{sql}\nEOF",
            wrap=False,
        )

    def create_schema(self, db_name: str, root_pass: str) -> None:
        """Create a new MySQL database schema."""
        sql = " ".join(
            f"""
          DROP DATABASE IF EXISTS {db_name};
          CREATE DATABASE IF NOT EXISTS {db_name};
        """.split(),
        )
        self.mod.run(
            f"mysql -uroot -p{root_pass} <<EOF\n{sql}\nEOF",
            wrap=False,
        )

    def import_sql(self, root_pass: str, sql_file: str) -> None:
        """Import an SQL file into the MySQL database."""
        self.mod.run(
            f"mysql -uroot -p{root_pass} < {sql_file}",
        )

    def config_for_low_memory(self) -> None:
        """Configure MySQL for low memory usage."""
        setting_file = "/etc/mysql/my.cnf"
        setting = self.set_indent("""
            [mysqld]
            performance_schema = off
        """)
        self.mod.append_to_file(setting_file, setting)

    def test_mysql_connectivity(self) -> None:
        """Test MySQL connectivity.

        Tests MySQL connectivity, including root user login, additional user
        login, and database existence if configured. This method verifies
        that the MySQL server is functional and accessible using the provided
        credentials and database name.

        Raises:
            PlatformError: If root login fails, additional user login fails, or the
                specified database does not exist or is not accessible.

        """
        # Test root connection
        try:
            self.mod.run(f"mysql -uroot -p{self.args.db_root_pass} -e 'SELECT 1;'")
            self.info("Root test", "User 'root' login successful.")
        except Exception as e:
            err_msg = f"Root login failed: {e}"
            raise PlatformError(err_msg) from e

        # Test configured user if provided
        if self.args.new_db_user_and_pass:
            db_user, db_pass = self.args.new_db_user_and_pass
            try:
                self.mod.run(f"mysql -u{db_user} -p{db_pass} -e 'SELECT 1;'")
                self.info("User test", f"User '{db_user}' login successful.")
            except Exception as e:
                err_msg = f'User "{db_user}" login failed, {e}'
                raise PlatformError(err_msg) from e

        # Test database existence if configured
        if self.args.db_name:
            try:
                self.mod.run(
                    f"mysqlshow -uroot -p{self.args.db_root_pass} {self.args.db_name};",
                )
                self.info("Database test", f"Database '{self.args.db_name}' exists")
            except Exception as e:
                err_msg = (
                    f'Database "{self.args.db_name}" does not '
                    "exist or is not accessible."
                )
                raise PlatformError(err_msg) from e

    def pre_install(self) -> None:
        """Pre-installation steps for MySQL."""
        self.configure_root_password()

    def post_install(self) -> None:
        """Post-installation steps for MySQL."""
        if self.args.new_db_user_and_pass:
            db_user, db_pass = self.args.new_db_user_and_pass
            self.setup_user(db_user, db_pass, self.args.db_root_pass)
        if self.args.db_name:
            self.create_schema(self.args.db_name, self.args.db_root_pass)
        if self.args.sql_file:
            self.import_sql(self.args.db_root_pass, self.args.sql_file)

        self.config_for_low_memory()

        # Test the MySQL setup
        self.test_mysql_connectivity()


class PhpMyAdmin(Engine):
    """Web database client.

    Access at http://<servername>/phpmyadmin

    Use the root username and the password specified via --db_root_pass
    """

    provides: ClassVar = ["phpmyadmin"]
    requires: ClassVar = ["apache2", "phpbin", "mysql"]
    required_args: ClassVar = []
    title = "PhpMyAdmin"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the PhpMyAdmin engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.apt_pkgs = ["phpmyadmin"]

    def pre_install(self) -> None:
        """Pre-installation steps for PhpMyAdmin."""
        root_pass = self.args.db_root_pass
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            'phpmyadmin/reconfigure-webserver multiselect apache2"',
        )
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            'phpmyadmin/dbconfig-install boolean true"',
        )
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            f'phpmyadmin/app-password-confirm password {root_pass}"',
        )
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            'phpmyadmin/reconfigure-webserver multiselect none"',
        )

        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            'phpmyadmin/mysql/admin-user string root"',
        )
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            f'phpmyadmin/mysql/admin-pass password {root_pass}"',
        )
        self.mod.run(
            'sudo debconf-set-selections <<< "phpmyadmin '
            f'phpmyadmin/mysql/app-pass password {root_pass}"',
        )

        site_name = self.args.site_name_and_root[0][0]
        self.info("URL", f"http://{site_name}/phpmyadmin")


class Adminer(Engine):
    """Web database client, an alternative to PhpMyAdmin."""

    provides: ClassVar = ["adminer"]
    requires: ClassVar = ["apache2", "phpbin", "mysql"]
    required_args: ClassVar = []
    title = "Adminer"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Adminer engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

        if self.ubuntu >= UbuntuVersion.V18_04:
            self.apt_pkgs = ["adminer"]
        else:
            error(f"{self.title} not tested on this platform")

        site_name = self.args.servername
        self.info("URL", f"http://{site_name}/adminer.php")

    def post_install(self) -> None:
        """Post-installation steps for Adminer.

        For 18.04, an extra compile step needs to be
        done.  20.04 and later don't need this.
        """
        if self.ubuntu == UbuntuVersion.V18_04:
            self.mod.run("cd /usr/share/adminer/ && sudo php compile.php")
            filename: str = self.mod.run(
                "cd /usr/share/adminer/ && ls adminer-*.*.*.php",
                capture=True,
            )
            filename = filename.decode("ascii")
            self.mod.append_to_file(
                "/etc/apache2/conf-available/adminer.conf",
                f"Alias /adminer.php /usr/share/adminer/{filename}",
                backup=False,
            )
            self.mod.run("sudo a2enconf adminer")
            self.mod.restart_apache()
