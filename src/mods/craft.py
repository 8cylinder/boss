# run-shell-command :: ../../build.bash

import os

from bash import Bash
from dist import Dist
from errors import *


class Craft2(Bash):
    provides = ['craft2']
    requires = ['apache2', 'php', 'mysql']
    title = 'Craft 2'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php5', 'php5-imagick', 'php5-mcrypt', 'php5-curl',
                             'php5-gd', 'php5-mysql' , 'libapache2-mod-php5']
        elif self.distro == (Dist.UBUNTU, Dist.V16_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-mcrypt', 'php-curl',
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql']
        elif self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-curl', # no php-mcrypt on 18.04
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql']
        else:
            raise PlatformError(
                'Craft2 dependencies have not been determined for this platform: {}'.format(
                self.distro))

    def post_install(self):
        if self.distro >= (Dist.UBUNTU, Dist.V18_04):
            self.install_mcrypt()
            self.disable_groupby()

    def install_mcrypt(self):
        """Manualy compile and install mcrypt since it has be depreciated and not available on 18.04

        https://askubuntu.com/a/1037418"""

        # Install prerequisites
        self.apt(['php-dev', 'libmcrypt-dev', 'gcc', 'make autoconf', 'libc-dev', 'pkg-config'])

        # Compile mcrypt extension
        self.run('yes '' | sudo pecl install mcrypt-1.0.1')
        # Just press enter when it asks about libmcrypt prefix
        # `yes ''` causes pecl to accept the default

        # Enable extension for apache
        self.run('echo "extension=mcrypt.so" | sudo tee -a /etc/php/7.2/apache2/conf.d/mcrypt.ini')

        # Restart apache
        self.run('sudo service apache2 restart')

    def disable_groupby(self):
        '''
        mycnf_dir='/etc/mysql/conf.d/'
        mycnf_file='disable_only_full_group_by.cnf'
        if [[ -d "$mycnf_dir" ]]; then
            cat <<-EOF > ~/$mycnf_file
        [mysqld]
        sql_mode="STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"
        EOF
            sudo mv ~/$mycnf_file $mycnf_dir || error "cannot create ${mycnf_dir}${mycnf_file}"
            echo "Created ${mycnf_dir}${mycnf_file}"
        fi
        sudo service mysql restart
        '''

        mycnf_dir = '/etc/mysql/conf.d/'
        mycnf_file = 'disable_only_full_group_by.cnf'
        if self.args.dry_run or self.args.generate_script or os.path.exists(mycnf_dir):
            setting = '''
              [mysqld]
              sql_mode="STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"
            '''
            setting = '\n'.join(i[14:] for i in setting.split('\n'))
            self.run('echo | sudo tee {file} <<EOF\n{contents}\nEOF'.format(
                file=mycnf_file,
                contents=setting,
            ))
        else:
            raise FileNotFoundError('In disable_groupby(), {} not found'.format(mycnf_dir))


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
        elif self.distro >= (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ['php7.2-mbstring', 'php-imagick', 'php7.2-curl',
                             'php-xml', 'php7.2-zip', 'php-soap']
        else:
            raise PlatformError("Craft3 requires PHP7, it is not available on this platform: {}".format(self.distro))

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
            if os.listdir(craft_dir):
                error('Craft dir is not empty. ({})'.format(craft_dir), self.args.dry_run)

        # Install craft3 via composer
        craft_db_user = 'root'
        craft_db_pass = self.args.db_root_pass
        craft_db_name = self.args.db_name

        # install from composer
        self.run('sudo -u www-data composer create-project --no-ansi --remove-vcs --no-interaction craftcms/craft {}'.format(craft_dir))

        # setup the db
        self.run('''sudo -u www-data php {craft_dir}/craft setup/db --interactive 0 \
            --driver mysql \
            --database {db_name} \
            --user {db_user} \
            --password {db_pass} \
            --port 3306 \
            --server localhost'''.format(
                craft_dir=craft_dir,
                db_name=craft_db_name,
                db_user=craft_db_user,
                db_pass=craft_db_pass
            ))
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
            'sudo service apache2 restart',
        )]

        sed_exp = 's|dirname(__DIR__)|\'{}\'|'.format(craft_dir)
        index = os.path.join(html_dir, 'index.php')
        self.sed(sed_exp, index)
        self.run('sudo chown www-data:www-data {}'.format(index))

        # self.info('Craft admin', 'https://{}/admin'.format(self.args.servername))
