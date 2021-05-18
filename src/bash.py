# run-shell-command :: ../build.bash

import os
import sys
from dist import Dist
import datetime
import subprocess

from errors import *
from util import display_cmd
from util import title
from util import warn
from util import notify
from util import error


class Bash:
    APTUPDATED = False
    info_messages = []
    WWW_USER = 'www-data'

    def __init__(self, dry_run=False, args=None):
        self.ok_code = 0
        self.requires = []
        self.apt_pkgs = []
        self.provides = []
        self.distro = Dist()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)

        if args and not dry_run:
            # action = args.subparser_name
            self.log(self.__class__.__name__)
        self.now = datetime.datetime.now().strftime('%y-%m-%d-%X')

    def log(self, name):
        log_name = '~/boss-installed-modules'
        mod = '{}\n'.format(name)
        try:
            with open(os.path.expanduser(log_name), 'r') as f:
                installed_mods = f.readlines()
        except FileNotFoundError:
            installed_mods = []

        installed_mods = set(installed_mods)
        installed_mods.add(mod)

        with open(os.path.expanduser(log_name), 'w') as f:
            f.writelines(installed_mods)

    def sed(self, sed_exp, config_file):
        new_ext = '.original-{}'.format(self.now)
        sed_cmd = 'sudo sed --in-place="{}" "{}" "{}"'.format(new_ext, sed_exp, config_file)
        self.run(sed_cmd)

    def append_to_file(self, filename, text, user=None, backup=True, append=True):
        if backup:
            new_ext = '.original-{}'.format(self.now)
            copy_cmd = 'sudo cp "{file}" "{file}{now}"'.format(
                file=filename, now=new_ext)
            self.run(copy_cmd)

        www_user = ''
        if user == self.WWW_USER:
            www_user = '-u {}'.format(self.WWW_USER)

        append_flag = ''
        if append is True:
            append_flag = '-a'

        add_cmd = 'echo | sudo {user} tee {append} "{file}" <<EOF\n{text}\nEOF'.format(
            text=text, file=filename, user=www_user, append=append_flag)
        self.run(add_cmd, wrap=False)

    def apt(self, progs):
        self._apt(progs)

    def install(self):
        self._apt(self.apt_pkgs)
        return True

    def pre_install(self):
        return True

    def post_install(self):
        return True

    def run(self, cmd, wrap=True, capture=False, comment=False):
        if wrap:
            pretty_cmd = ' '.join(cmd.split())
            display_cmd(pretty_cmd, wrap=True, script=self.args.generate_script, comment=comment)
        else:
            display_cmd(cmd, wrap=False, script=self.args.generate_script, comment=comment)

        if self.args.dry_run or self.args.generate_script:
            return
        if capture:
            # result = subprocess.run(cmd, shell=True, check=True, executable='/bin/bash', stdout=subprocess.PIPE)
            result = subprocess.check_output(cmd, shell=True, executable='/bin/bash')
            sys.stdout.flush()
        else:
            # result = subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
            result = subprocess.check_call(cmd, shell=True, executable='/bin/bash')
        return result

    def curl(self, url, output, capture=False):
        cmd = 'curl -sSL {url} --output {output}'.format(
            url=url, output=output)
        result = self.run(cmd, capture=capture)
        return result

    def restart_apache(self):
        """Restart Apache using the apropriate command

        Details about wether to use service or systemctl
        https://askubuntu.com/a/903405"""

        if self.distro == Dist.UBUNTU:
            self.run('sudo service apache2 restart')
        else:
            error('restart_apache has unknown platform')

    def _apt(self, packages):
        dry = '--dry-run' if self.dry_run else ''
        packages = ' '.join(packages)
        if not packages:
            return False
        if not Bash.APTUPDATED:
            self.run('sudo apt-get --quiet update')
            #self.run('sudo apt-get --quiet --yes upgrade')   # not really necessary
            Bash.APTUPDATED = True
        self.run('export DEBIAN_FRONTEND=noninteractive; sudo apt-get {dry} --yes --quiet install {packages}'.format(
            dry=dry, packages=packages))
        return True

    def info(self, title, msg):
        self.info_messages.append([title, msg])
