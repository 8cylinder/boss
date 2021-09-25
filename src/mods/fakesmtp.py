# run-shell-command :: ../../build.bash

import urllib.request
import json
from pathlib import Path

from bash import Bash
from dist import Dist
from util import error
# noinspection PyUnresolvedReferences
from util import warn
# noinspection PyUnresolvedReferences
from errors import *

from util import error
from util import warn


class FakeSMTP(Bash):
    """A fake SMTP server for mail testing

    https://www.lullabot.com/articles/installing-mailhog-for-ubuntu-1604
    """
    provides = ['fakesmtp']
    requires = ['php']
    title = 'FakeSMTP (Mailhog)'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.phpini = '/etc/php5/apache2/php.ini'
            self.cliini = '/etc/php5/cli/php.ini'
        elif self.distro == (Dist.UBUNTU, Dist.V16_04):
            self.phpini = '/etc/php/7.0/apache2/php.ini'
            self.cliini = '/etc/php/7.0/cli/php.ini'
        elif self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.phpini = '/etc/php/7.2/apache2/php.ini'
            self.cliini = '/etc/php/7.2/cli/php.ini'
        elif self.distro == (Dist.UBUNTU, Dist.V20_04):
            self.phpini = '/etc/php/7.4/apache2/php.ini'
            self.cliini = '/etc/php/7.4/cli/php.ini'
        else:
            error('FakeSMTP: no php.ini defined for this version of Ubuntu')

    def post_install(self):
        self.install_via_github()
        sedcmd = 's|;sendmail_path =|sendmail_path = /usr/local/bin/mhsendmail|'
        cmds = [
            'chmod +x mailhog mhsendmail',
            'sudo mv mailhog mhsendmail /usr/local/bin',
        ]
        [self.run(i) for i in cmds]
        self.sed(sedcmd, self.phpini)
        self.sed(sedcmd, self.cliini)

        if self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.config_upstart()
        elif self.distro >= (Dist.UBUNTU, Dist.V16_04):
            self.config_systemd()

        if self.distro == (Dist.UBUNTU, Dist.V18_04):
            postfix_config = Path('/etc/postfix/main.cf')
            if postfix_config.exists():
                self.sed('s/^myhostname = .*&/myhostname = localhost/', postfix_config)
                self.sed('s/^relayhost = .*&/relayhostl = [127.0.0.1]:1025/', postfix_config)
            else:
                error(f'No postfix config file: {postfix_config}')

        # test if it works
        cmd = 'php -r "mail(\'boss@example.com\', \'Test from Boss\', \'Test from Boss.\');"'
        self.run(cmd, capture=True)
        # if('error' in result):
        #     error(result)
        self.info('FakeSMTP client', 'http://{}:8025'.format(self.args.servername))
        self.info(' └─ FakeSMTP api', 'curl http://{}:8025/api/v2/messages'.format(self.args.servername))

    def install_via_go(self):
        pass

    def install_via_github(self):
        # download mailhog & mhsendmail.  Get the latest release using
        # GitHub's api.
        data = [{
            'release': 'MailHog_linux_amd64',
            'localname': 'mailhog',
            'url': 'https://api.github.com/repos/mailhog/MailHog/releases/latest',
        }, {
            'release': 'mhsendmail_linux_amd64',
            'localname': 'mhsendmail',
            'url': 'https://api.github.com/repos/mailhog/mhsendmail/releases/latest',
        }]
        # Sometimes github returns 'forbidden' when accessing the api.
        # Rate limiting maybe? I don't know.
        try:
            for prog in data:
                r = urllib.request.urlopen(prog['url']).read()
                content = json.loads(r.decode('utf-8'))
                for asset in content['assets']:
                    if asset['name'] == prog['release']:
                        self.curl(asset['browser_download_url'], prog['localname'])
        except urllib.error.HTTPError as e:
            error('MAILHOG github api: {}'.format(e.msg))

    def config_upstart(self):
        # 14.04 uses upstart
        service = '''
            description "Mailhog"
            start on runlevel [2345]
            stop on runlevel [!2345]
            exec /usr/bin/env /usr/local/bin/mailhog > /dev/null 2>&1 &
        '''
        service_file = '/etc/init/mailhog.conf'
        service = '\n'.join([i[12:] for i in service.split('\n')])
        self.append_to_file(service_file, service, append=False)
        # self.run('echo | sudo tee {service_file} <<EOF{contents}EOF'.format(
        #     service_file=service_file,
        #     contents=service
        # ), wrap=False)

        self.run('sudo ln -s {} /etc/init.d/mailhog'.format(service_file))
        self.run('sudo service mailhog start')

    def config_systemd(self):
        # 16.04 + uses systemd
        service = '''
            [Unit]
            Description=MailHog service

            [Service]
            ExecStart=/usr/local/bin/mailhog \\\\
              -api-bind-addr 0.0.0.0:8025 \\\\
              -ui-bind-addr 0.0.0.0:8025 \\\\
              -smtp-bind-addr 0.0.0.0:1025

            [Install]
            WantedBy=multi-user.target
        '''
        service_file = '/etc/systemd/system/mailhog.service'

        service = '\n'.join([i[12:] for i in service.split('\n')])
        self.run('echo | sudo tee {service_file} <<EOF{contents}EOF'.format(
            service_file=service_file,
            contents=service
        ), wrap=False)
        self.run('sudo systemctl start mailhog')
        self.run('sudo systemctl enable mailhog')
