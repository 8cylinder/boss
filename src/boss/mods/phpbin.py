import datetime
import os
from pathlib import Path
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.errors import PlatformError, SecurityError
from boss.util import error


class PhpBin(Engine):
    """PHP with additional packages that CMS's need."""

    provides: ClassVar = ["phpbin"]
    requires: ClassVar = ["apache2"]
    required_args: ClassVar = []
    title = "PHP bin"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the PHP bin engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

        if ubuntu_version == UbuntuVersion.V14_04:
            self.apt_pkgs = [
                "php5",
                "php5-imagick",
                "php5-mcrypt",
                "php5-curl",
                "php5-gd",
                "php5-mysql",
                "libapache2-mod-php5",
            ]
        elif ubuntu_version == UbuntuVersion.V16_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-mcrypt",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-gd",
                "php-mysql",
            ]
        elif ubuntu_version == UbuntuVersion.V18_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-curl",  # no php-mcrypt on 18.04
                "php-xml",
                "php-zip",
                "php-gd",
                "php-mysql",
                "php-gmp",
            ]
        elif ubuntu_version == UbuntuVersion.V20_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-curl",  # no php-mcrypt on 20.04
                "php-xml",
                "php-zip",
                "php-gd",
                "php-mysql",
                "php-gmp",
            ]
        elif ubuntu_version == UbuntuVersion.V24_04:
            self.apt_pkgs = [
                "php",
                "libapache2-mod-php",
                "php-mbstring",
                "php-imagick",
                "php-curl",
                "php-mcrypt",
                "php-xml",
                "php-zip",
                "php-gd",
                "php-mysql",
                "php-gmp",
            ]
        else:
            err_msg = (
                "PHP dependencies have not been determined for "
                "this platform yet: {ubuntu_version}",
            )
            raise PlatformError(err_msg)


class Xdebug(Engine):
    """A standard Xdebug installation for PHP."""

    provides: ClassVar = ["xdebug"]
    requires: ClassVar = ["phpbin"]
    required_args: ClassVar = []
    title = "Xdebug"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Xdebug engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.apt_pkgs = ["php-xdebug"]

    def post_install(self) -> None:
        """Post-installation steps for Xdebug."""
        settings = """
          ### added by Boss ###
          xdebug.remote_autostart = 1
          xdebug.remote_enable = 1
          xdebug.remote_connect_back = 1
          xdebug.remote_port = 9000
          xdebug.max_nesting_level = 512

          # https://www.jetbrains.com/help/phpstorm/configuring-xdebug.html#configuring-xdebug-vagrant
          # https://nystudio107.com/blog/using-phpstorm-with-vagrant-homestead#are-we-there-yet
          # This is usually 10.0.2.2 for vagrant
          # use this command to get the host's ip:
          # `netstat -rn | grep "^0.0.0.0" | tr -s " " | cut -d " " -f2`
          xdebug.remote_host = '10.0.2.2'
        """
        settings = "\n".join([i[10:] for i in settings.split("\n")])

        xdebug_ini = ""
        if self.ubuntu == UbuntuVersion.V18_04:
            xdebug_ini = "/etc/php/7.2/mods-available/xdebug.ini"
            self.mod.append_to_file(xdebug_ini, settings)
        elif self.ubuntu == UbuntuVersion.V20_04:
            xdebug_ini = "/etc/php/7.4/mods-available/xdebug.ini"
            self.mod.append_to_file(xdebug_ini, settings)
        elif self.ubuntu == UbuntuVersion.V24_04:
            xdebug_ini = "/etc/php/8.3/mods-available/xdebug.ini"
            self.mod.append_to_file(xdebug_ini, settings)
        else:
            error("Xdebug ini edit not implemented yet for this version of Ubuntu.")
        self.info("Xdebug INI", xdebug_ini)


class PhpInfo(Engine):
    """Create a phpinfo.php file in /var/www/html.

    It is available at https://<servername>/phpinfo.php
    """

    provides: ClassVar = ["phpinfo"]
    requires: ClassVar = ["phpbin"]
    required_args: ClassVar = ["site_name_and_root"]
    title = "PHP Info"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the PhpInfo engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        self.loc = "/var/www/html"
        self.info_file = f"{self.loc}/phpinfo.php"

    def post_install(self) -> None:
        """Post-installation steps for PHP Info."""
        info = f"<h1>{datetime.datetime.now().isoformat()}</h1>\n<?php phpinfo();"
        loc_path = Path(self.loc)
        if self.args.dry_run or self.args.generate_script or loc_path.exists():
            self.mod.write_new_file(self.info_file, info)
            # cmd = 'echo \'{info}\' | sudo -u www-data tee {loc}'.format(
            #     info=info,
            #     loc=self.info_file
            # )
            # self.run(cmd)
        elif not self.args.dry_run:
            msg = f"[PhpInfo] Dir does not exist: {self.loc}"
            raise FileNotFoundError(msg)
        site_name = self.args.site_name_and_root[0][0]
        self.info("Info URL", f"http://{site_name}/phpinfo.php")
        self.info("Info file", self.info_file)


class Composer(Engine):
    """Setup Composer, the PHP package manager.

    If the Ubuntu version is older than 18.04 composer is installed from source
    from github. Otherwise it is installed from the apt repo.
    """

    provides: ClassVar = ["composer"]
    requires: ClassVar = ["phpbin"]
    required_args: ClassVar = []
    title = "Composer"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Composer engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def post_install(self) -> None:
        """Post-installation steps for Composer."""
        if self.ubuntu < UbuntuVersion.V18_04:
            self.source_install()
        else:
            self.apt_install()

        # add www-data to the ubuntu group so when running composer as
        # www-data user, it can create a cache in ubuntu's home dir.
        self.mod.run("sudo usermod -aG $USER www-data")

    def apt_install(self) -> None:
        """Install Composer from apt."""
        self.mod.apt(["composer"])

    def source_install(self) -> None:
        """Install Composer from source."""
        url = "https://composer.github.io/installer.sig"
        sig_name = os.path.expanduser("~/composer.sig")
        self.mod.curl(url, sig_name)
        expected_sig = None
        sig_path = Path(sig_name)
        if sig_path.exists():
            with sig_path.open() as f:
                expected_sig = f.read()
            expected_sig = expected_sig.strip()
            self.mod.run(f"rm {sig_name}")
        url = "https://getcomposer.org/installer"
        comp_name = "$HOME/composer_installer"
        self.mod.curl(url, comp_name)
        actual_sig = None
        result = self.mod.run(f"sha384sum {comp_name}", capture=True)
        if result:  # could be a dry run
            actual_sig = result.decode("utf-8").split()[0].strip()
        if expected_sig != actual_sig:
            msg = (
                f"Composer's signatures do not match.\nExpected: "
                f'"{expected_sig}"\n  Actual: "{actual_sig}"'
            )
            raise SecurityError(msg)

        for command in (
            # 'php {} --quiet'.format(comp_name),
            f"sudo php {comp_name} --quiet --install-dir=/usr/local/bin --filename=composer",
            # 'rm {}'.format(comp_name),
            # 'sudo mv composer.phar /usr/local/bin/composer',
            # 'if [[ ! -e $HOME/.composer ]]; then mkdir $HOME/.composer/; fi',
            # 'chmod a+rw $HOME/.composer/',
        ):
            self.mod.run(command)

        self.mod.run("sudo chown -R $USER: $HOME/.composer")
        self.mod.run("sudo chmod -R uga+rw $HOME/.composer")
