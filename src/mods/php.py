# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *
from util import error
from util import warn

import os
import datetime


class Php(Bash):
    """PHP with additional packages that CMS's need"""
    provides = ['php']
    requires = ['apache2']
    title = 'PHP'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['php']
        self.requires = ['apache2']

        if self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php5', 'php5-imagick', 'php5-mcrypt', 'php5-curl',
                             'php5-gd', 'php5-mysql', 'libapache2-mod-php5']
        elif self.distro == (Dist.UBUNTU, Dist.V16_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-mcrypt', 'php-curl',
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql']
        elif self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-curl',  # no php-mcrypt on 18.04
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql', 'php-gmp']
        elif self.distro == (Dist.UBUNTU, Dist.V20_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-curl',  # no php-mcrypt on 20.04
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql', 'php-gmp']
        else:
            raise PlatformError(
                'PHP dependencies have not been determined for this platform yet: {}'.format(
                    self.distro))

class Xdebug(Bash):
    provides = ['xdebug']
    requires = ['php']
    title = 'Xdebug'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['php-xdebug']

    def post_install(self):
        settings = '''
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
        '''
        settings = '\n'.join([i[10:] for i in settings.split('\n')])

        if self.distro == (Dist.UBUNTU, Dist.V18_04):
            xdebug_ini = '/etc/php/7.2/mods-available/xdebug.ini'
            self.append_to_file(xdebug_ini, settings)
        elif self.distro == (Dist.UBUNTU, Dist.V20_04):
            xdebug_ini = '/etc/php/7.4/mods-available/xdebug.ini'
            self.append_to_file(xdebug_ini, settings)
        else:
            warn('Xdebug ini edit not implemented yet for this version of Ubuntu.')
        self.info('Xdebug ini edited', xdebug_ini)


class PhpInfo(Bash):
    """Create a phpinfo.php file in /var/www/html

    It is available at https://<servername>/phpinfo.php"""

    provides = ['phpinfo']
    requires = ['php']
    title = 'PHP Info'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loc = '/var/www/html'
        # if self.document_root:
            # self.loc = self.document_root
        self.info_file = '{}/phpinfo.php'.format(self.loc)

    def post_install(self):
        info = '<h1>{}</h1>\n<?php phpinfo();'.format(datetime.datetime.now().isoformat())

        if self.args.dry_run or self.args.generate_script or os.path.exists(self.loc):
            self.append_to_file(self.info_file, info, backup=False)
            # cmd = 'echo \'{info}\' | sudo -u www-data tee {loc}'.format(
            #     info=info,
            #     loc=self.info_file
            # )
            # self.run(cmd)
        else:
            if not self.args.dry_run:
                raise FileNotFoundError('[PhpInfo] Dir does not exist: {}'.format(self.loc))

        site_name = self.args.site_name_and_root[0][0]
        self.info('PHP Info', 'http://{}/phpinfo.php -- {}'.format(site_name, self.info_file))


class Composer(Bash):
    """If the distro is older than 18.04 composer is installed from source
    from github.  Otherwise it is installed from the apt repo.
    """

    provides = ['composer']
    requires = ['php']
    title = 'Composer'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_install(self):
        if self.distro < (Dist.UBUNTU, Dist.V18_04):
            self.source_install()
        else:
            self.apt_install()

        # add www-data to the ubuntu group so when running composer as
        # www-data user, it can create a cache in ubuntu's home dir.
        self.run('sudo usermod -aG $USER www-data')

    def apt_install(self):
        self.apt(['composer'])

    def source_install(self):
        url = 'https://composer.github.io/installer.sig'
        sig_name = os.path.expanduser('~/composer.sig')
        self.curl(url, sig_name)

        expected_sig = None
        if os.path.exists(sig_name):  # could be a dry run
            with open(os.path.expanduser(sig_name)) as f:
                expected_sig = f.read()
            expected_sig = expected_sig.strip()
            self.run('rm {}'.format(sig_name))

        url = 'https://getcomposer.org/installer'
        comp_name = '$HOME/composer_installer'
        self.curl(url, comp_name)

        actual_sig = None
        result = self.run('sha384sum {}'.format(comp_name), capture=True)
        if result:  # could be a dry run
            actual_sig = result.decode('utf-8').split()[0].strip()

        if expected_sig != actual_sig:
            raise SecurityError('Composer\'s signatures do not match.\nExpected: "{}"\n  Actual: "{}"'.format(
                expected_sig, actual_sig
            ))

        [self.run(command) for command in (
            # 'php {} --quiet'.format(comp_name),
            'sudo php {} --quiet --install-dir=/usr/local/bin --filename=composer'.format(comp_name),
            # 'rm {}'.format(comp_name),
            # 'sudo mv composer.phar /usr/local/bin/composer',
            # 'if [[ ! -e $HOME/.composer ]]; then mkdir $HOME/.composer/; fi',
            # 'chmod a+rw $HOME/.composer/',
        )]
        self.run('sudo chown -R $USER: $HOME/.composer')
        self.run('sudo chmod -R uga+rw $HOME/.composer')
