from bash import Bash
from dist import Dist


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
