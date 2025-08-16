"""Manage the installation and configuration of Craft CMS.

This module provides a class `Craft` that sets up Craft CMS by managing
dependencies, directories, composer setups, and configurations for Apache
and the Craft application itself.

Classes:
- Craft: Main class for handling the Craft CMS installation process.
"""

import os
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.errors import DependencyError, PlatformError


class Craft(Engine):
    """Install Craft CMS."""

    provides: ClassVar[list[str]] = ["craft"]
    requires: ClassVar[list[str]] = [
        "apache2",
        "phpbin",
        "mysql",
        "composer",
        "virtualhost",
    ]
    required_args: ClassVar[list[str]] = [
        "db_name",
        "craft_credentials",
        "site_name_and_root",
        "new_db_user_and_pass",
    ]
    title = "Craft CMS"

    def __init__(
        self,
        *,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the Craft engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)
        if ubuntu_version == UbuntuVersion.V16_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-mcrypt",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-soap",
            ]
        elif ubuntu_version == UbuntuVersion.V18_04:
            self.apt_pkgs = [
                "php7.2-mbstring",
                "php-imagick",
                "php7.2-curl",
                "php-xml",
                "php7.2-zip",
                "php-soap",
                "php7.2-gmp",
                "php-gmp",
            ]  # php7.2-gmp or php7.2-bcmath
        elif ubuntu_version == UbuntuVersion.V20_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-soap",
                "php-gmp",
            ]
        elif ubuntu_version == UbuntuVersion.V24_04:
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-soap",
                "php-gmp",
                "php-bcmath",
                "php-intl",
            ]
        else:
            error_msg = (
                "Craft dependencies have not been determined yet "
                f"for this platform: {ubuntu_version}"
            )
            raise PlatformError(error_msg)

    def post_install(self) -> None:
        """Install Craft CMS."""
        if not self.args.craft_credentials or not self.args.site_name_and_root:
            self.info(
                "Install",
                "Craft credentials (--craft-credentials) not provided, "
                "not installing Craft.",
            )
            return

        html_dir = os.path.join("/var/www/", self.args.site_name_and_root[0][1])  # noqa: PTH118

        # set up the dirs
        self.configure_dirs(html_dir)

        # Install craft3 via composer
        self.composer_install_craft(html_dir)

        # configure craft
        craft_db_user, craft_db_pass = self.args.new_db_user_and_pass
        self.configure_craft(craft_db_pass, craft_db_user, html_dir)

        # edit the apache conf to point the DocumentRoot to the /web directory
        site_name = self.args.site_name_and_root[0][0]
        self.edit_conf(site_name, html_dir)

        self.run("sudo a2enmod rewrite")
        self.restart_apache()

        self.info("Craft admin", f"https://{self.args.servername}/admin")

    def edit_conf(self, site_name: str, site_dir: str) -> None:
        """Edit the Apache configuration file for the Craft site."""
        conf_file = f"/etc/apache2/sites-available/{site_name}.conf"
        sed_exp = [
            f"s|DocumentRoot {site_dir}|DocumentRoot {site_dir}/web|g",
            f's|Directory "{site_dir}/web"|Directory "{site_dir}/web"|g',
        ]
        for exp in sed_exp:
            self.sed(exp, conf_file)

    def configure_craft(
        self,
        craft_db_pass: str,
        craft_db_user: str,
        html_dir: str,
    ) -> None:
        """Configure Craft using the craft cli command.

        Use `sg` to run the command as the www-data user.
        """
        # setup the db
        self.run(f"""sg www-data 'php {html_dir}/craft setup/db --interactive 0 \
            --driver mysql \
            --server localhost \
            --port 3306 \
            --user {craft_db_user} \
            --database {self.args.db_name} \
            --password {craft_db_pass} \
            '
        """)
        # run the craft install
        username, email, password = self.args.craft_credentials
        self.run(f"""sg www-data 'php {html_dir}/craft install/craft \
            --interactive=0 \
            --email={email} \
            --username={username} \
            --password={password} \
            --siteName={self.args.servername} \
            --siteUrl={"@web"}
            '
        """)

    def composer_install_craft(self, html_dir: str) -> None:
        """Install Craft CMS using Composer."""
        # remove existing files
        # self.run(
        #     f"sudo rm -If {html_dir}/index.html {html_dir}/*.local.crt {html_dir}/*.local.key"
        # )
        self.run("ls *")
        self.run(f"sudo rm -Irf {html_dir}/*")
        cmd = (
            f"sg www-data 'composer create-project --no-ansi "
            f"--remove-vcs --no-interaction craftcms/craft {html_dir}/'"
        )
        self.run(cmd)

    def configure_dirs(self, html_dir: str) -> None:
        """Configure the directories for Craft."""
        if not (os.path.exists(html_dir) or self.args.dry_run):  # noqa: PTH110
            error_msg = (
                f'Site root "{html_dir}" does not exist, include "virtualhost" '
                "in your command line arguments to create it."
            )
            raise DependencyError(error_msg)
        self.run(f"sudo chown www-data: {html_dir}")
        self.run(f"sudo chmod ug+rw {html_dir}")
