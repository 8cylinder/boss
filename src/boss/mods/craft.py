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
        if not self.args.craft_credentials:
            self.info(
                "Install",
                "Craft credentials (--craft-credentials) not provided, not installing Craft.",
            )
            return

        # if site_name_and_root used, use the first one for craft
        if not self.args.site_name_and_root:
            self.info(
                "Install",
                "Site name and root (--site-name-and-root) not provided, not installing Craft.",
            )
            return
        html_dir = os.path.join("/var/www/", self.args.site_name_and_root[0][1])

        self.configure_dirs(html_dir)

        craft_db_user, craft_db_pass = self.args.new_db_user_and_pass

        # Install craft3 via composer
        self.run(
            f"sudo rm -If {html_dir}/index.html {html_dir}/*.local.crt {html_dir}/*.local.key"
        )
        # install from composer
        # cmd = f"sudo -u www-data composer create-project --no-ansi --remove-vcs --no-interaction --no-cache craftcms/craft {html_dir}"

        cmd = f"sg www-data 'composer create-project --no-ansi --remove-vcs --no-interaction craftcms/craft {html_dir}/'"
        self.run(cmd)

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
        # run the install
        username, email, password = self.args.craft_credentials
        self.run(f"""sg www-data 'php {html_dir}/craft install/craft --interactive=0 \
            --email={email} \
            --username={username} \
            --password={password} \
            --siteName={self.args.servername} \
            --siteUrl={"@web"}
            '
        """)
        # copy web files to the html dir, adjust permissions, enable rewrite and restart server
        [
            self.run(command)
            for command in (
                # "sudo chown www-data: {}".format(html_dir),
                # 'sudo -u www-data cp -r "{}/web/." "{}"'.format(html_dir, html_dir),
                # "sudo chmod 774 {}/cpresources/".format(html_dir),
                # "sudo chmod -R g+rw {}".format(html_dir),
                # "sudo chmod -R g+rw {}".format(html_dir),
                "sudo a2enmod rewrite",
            )
        ]
        self.restart_apache()

        # sed_exp = f"s|dirname(__DIR__)|'{html_dir}'|"
        # index = os.path.join(html_dir, "index.php")
        # self.sed(sed_exp, index)
        # self.run("sudo chown www-data:www-data {}".format(index))

        self.info("Craft admin", f"https://{self.args.servername}/admin")

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
