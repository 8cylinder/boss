from bash import Bash
from dist import Dist


class Php(Bash):
    """Base PHP, nothing else."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['php']
        self.requires = ['apache2']
        if self.distro > (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php']
        elif self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php5']


class Xdebug(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['xdebug']
        self.requires = ['php']
        self.apt_pkgs = ['php-xdebug']    # good enough?


class PhpInfo(Bash):
    """Create a phpinfo.php file in /var/www/html

    It is available at https://<servername>/phpinfo.php"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['phpinfo']
        self.requires = ['php']
        self.loc = '/var/www/html'
        self.info_file = '{}/phpinfo.php'.format(self.loc)

    def post_install(self):
        info = '<h1>{}</h1>\n<?php phpinfo();'.format(datetime.datetime.now().isoformat())
        if os.path.exists(self.loc):
            cmd = 'echo \'{info}\' | sudo -u www-data tee {loc}'.format(
                info=info,
                loc=self.info_file
            )
            self.run(cmd)
        else:
            error('[PhpInfo] Dir does not exist: {}'.format(self.loc), self.args.dry_run)

        # self.info('Php info', 'https://{}/phpinfo.php'.format(self.args.servername))

    def post_uninstall(self):
        cmd = 'if test -e {infofile}; then rm {infofile}; fi'.format(
            infofile=self.info_file
        )
        self.run(cmd)


class Composer(Bash):
    """If the distro is older than 18.04 composer is installed from source
    from github.  Otherwise it is installed from the apt repo.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['composer']
        self.requires = ['php']

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

    def post_uninstall(self):
        self.run('sudo rm /usr/local/bin/composer')
        self.run('if [[ -e $HOME/.composer ]]; then rm -rf $HOME/.composer/; fi')
        self.run('if [[ -e $HOME/composer.sig]]; then rm $HOME/composer.sig; fi')
