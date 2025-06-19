import os

from ..bash import Bash
from ..dist import Dist
from ..errors import PlatformError, DependencyError

# noinspection PyUnresolvedReferences
from typing import Any


class Craft(Bash):
    """https://craftcms.com"""

    provides = ["craft"]
    requires = ["apache2", "phpbin", "mysql", "composer", "virtualhost"]
    title = "Craft CMS"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # self.provides = ["craft"]
        # self.requires = ["apache2", "phpbin", "mysql", "composer"]
        if self.distro == (Dist.UBUNTU, Dist.V16_04):
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-mcrypt",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-soap",
            ]
        elif self.distro == (Dist.UBUNTU, Dist.V18_04):
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
        elif self.distro == (Dist.UBUNTU, Dist.V20_04):
            self.apt_pkgs = [
                "php-mbstring",
                "php-imagick",
                "php-curl",
                "php-xml",
                "php-zip",
                "php-soap",
                "php-gmp",
            ]
        elif self.distro == (Dist.UBUNTU, Dist.V24_04):
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
            raise PlatformError(
                "Craft dependencies have not been determined yet for this platform: {}".format(
                    self.distro
                )
            )

    def post_install(self) -> None:
        if not self.args.craft_credentials or not self.args.site_name_and_root:
            self.info(
                "Install",
                "Craft credentials (--craft-credentials) not provided, not installing Craft.",
            )
            return

        html_dir = os.path.join("/var/www/", self.args.site_name_and_root[0][1])

        # setup the dirs
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
        conf_file = f"/etc/apache2/sites-available/{site_name}.conf"
        sed_exp = [
            f"s|DocumentRoot {site_dir}|DocumentRoot {site_dir}/web|g",
            f's|Directory "{site_dir}/web"|Directory "{site_dir}/web"|g',
        ]
        for exp in sed_exp:
            self.sed(exp, conf_file)

    def configure_craft(
        self, craft_db_pass: str, craft_db_user: str, html_dir: str
    ) -> None:
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
        self.run(f"""sg www-data 'php {html_dir}/craft install/craft --interactive=0 \
            --email={email} \
            --username={username} \
            --password={password} \
            --siteName={self.args.servername} \
            --siteUrl={"@web"}
            '
        """)

    def composer_install_craft(self, html_dir: str) -> None:
        # remove existing files
        # self.run(
        #     f"sudo rm -If {html_dir}/index.html {html_dir}/*.local.crt {html_dir}/*.local.key"
        # )
        self.run("ls *")
        self.run(f"sudo rm -Irf {html_dir}/*")
        cmd = f"sg www-data 'composer create-project --no-ansi --remove-vcs --no-interaction craftcms/craft {html_dir}/'"
        self.run(cmd)

    def configure_dirs(self, html_dir: str) -> None:
        # setup the dirs
        # craft_dir = self.craft_dir
        if not os.path.exists(html_dir) and not self.args.dry_run:
            raise DependencyError(
                f'Site root "{html_dir}" does not exist, include "virtualhost" '
                + "in your command line arguments to create it."
            )
        self.run("sudo chown www-data: {}".format(html_dir))
        self.run("sudo chmod ug+rw {}".format(html_dir))
