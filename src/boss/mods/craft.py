# run-shell-command :: ../../build.bash

import os

from ..bash import Bash
from ..dist import Dist
from ..errors import PlatformError
from ..util import error
# noinspection PyUnresolvedReferences
from ..util import warn


class Craft3(Bash):
    """https://craftcms.com"""

    provides = ['craft3']
    requires = ['apache2', 'php', 'mysql', 'composer']
    title = 'Craft 3'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['craft3']
        self.requires = ['apache2', 'php', 'mysql', 'composer']
        if self.distro == (Dist.UBUNTU, Dist.V16_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-mcrypt',
                             'php-curl', 'php-xml', 'php-zip', 'php-soap']
        elif self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ['php7.2-mbstring', 'php-imagick', 'php7.2-curl',
                             'php-xml', 'php7.2-zip', 'php-soap', 'php7.2-gmp',
                             'php-gmp']  # php7.2-gmp or php7.2-bcmath
        elif self.distro == (Dist.UBUNTU, Dist.V20_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-curl',
                             'php-xml', 'php-zip', 'php-soap', 'php-gmp']
        elif self.distro == (Dist.UBUNTU, Dist.V24_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-curl',
                             'php-xml', 'php-zip', 'php-soap', 'php-gmp']
        else:
            raise PlatformError("Craft3 dependencies have not been determined yet for this platform: {}".format(self.distro))

    def post_install(self):
        if not self.args.craft_credentials:
            return

        # if site_name_and_root used, use the first one for craft
        self.craft_dir = '/var/www/craft'
        if self.args.site_name_and_root:
            html_dir = os.path.join('/var/www/', self.args.site_name_and_root[0][1])
            self.html_dir = html_dir
        else:
            self.html_dir = '/var/www/html'

        # setup the dirs
        craft_dir = self.craft_dir
        html_dir = self.html_dir
        for d in (craft_dir, html_dir):
            if not os.path.exists(d):
                self.run('sudo mkdir {}'.format(d))
            self.run('sudo chown www-data: {}'.format(d))
            self.run('sudo chmod ug+rw {}'.format(d))

        # make sure craft dir is empty
        if not self.args.dry_run:
            if os.path.exists(craft_dir) and os.listdir(craft_dir):
                error('Craft dir is not empty. ({})'.format(craft_dir), self.args.dry_run)

        # Install craft3 via composer
        craft_db_user = 'root'
        craft_db_pass = self.args.db_root_pass
        craft_db_name = self.args.db_name

        # install from composer
        self.run('sudo -u www-data composer create-project --no-ansi --remove-vcs --no-interaction craftcms/craft {}'.format(craft_dir))

        # setup the db
        self.run(f'''sudo -u www-data php {craft_dir}/craft setup/db --interactive 0 \
            --driver mysql \
            --database {craft_db_name} \
            --user {craft_db_user} \
            --password {craft_db_pass} \
            --port 3306 \
            --server localhost''')
        # run the install
        username, email, password = self.args.craft_credentials
        self.run('''sudo -u www-data php {craft_dir}/craft install/craft --interactive=0 \
            --email={email} \
            --username={username} \
            --password={password} \
            --siteName={sitename} \
            --siteUrl={siteurl}'''.format(
                craft_dir=craft_dir,
                email=email,
                username=username,
                password=password,
                sitename=self.args.servername,
                siteurl="'@web'"
            ))
        # copy web files to the html dir, adjust permissions, enable rewrite and restart server
        [self.run(command) for command in (
            'sudo chown www-data: {}'.format(html_dir),
            'sudo -u www-data cp -r "{}/web/." "{}"'.format(craft_dir, html_dir),
            'sudo chmod 774 {}/cpresources/'.format(html_dir),
            'sudo chmod -R g+rw {}'.format(craft_dir),
            'sudo chmod -R g+rw {}'.format(html_dir),
            'sudo a2enmod rewrite',
        )]
        self.restart_apache()

        sed_exp = 's|dirname(__DIR__)|\'{}\'|'.format(craft_dir)
        index = os.path.join(html_dir, 'index.php')
        self.sed(sed_exp, index)
        self.run('sudo chown www-data:www-data {}'.format(index))

        self.info('Craft admin', 'https://{}/admin'.format(self.args.servername))
