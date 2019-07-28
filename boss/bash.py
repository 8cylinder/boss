# run-shell-command :: ../build.bash

import os
from dist import Dist
from enum import Enum

from util import display_cmd
from util import title
from util import warn
from util import notify


class Bash:
    APTUPDATED = False

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
            action = args.subparser_name
            self.log(action, self.__class__.__name__)

    def log(self, action, name):
        log_name = '~/boss-installed-modules'
        mod = '{}\n'.format(name)
        try:
            with open(os.path.expanduser(log_name), 'r') as f:
                installed_mods = f.readlines()
        except FileNotFoundError:
            installed_mods = []

        installed_mods = set(installed_mods)
        if action == 'install':
            installed_mods.add(mod)
        elif action == 'uninstall':
            try:
                installed_mods.remove(mod)
            except KeyError:
                pass

        with open(os.path.expanduser(log_name), 'w') as f:
            f.writelines(installed_mods)

    def sed(self, sed_exp, config_file):
        now = datetime.datetime.now().strftime('%y-%m-%d-%X')
        new_ext = '.original-{}'.format(now)
        sed_cmd = 'sudo sed --in-place="{}" "{}" "{}"'.format(new_ext, sed_exp, config_file)
        self.run(sed_cmd)

    def apt(self, progs):
        self._apt(progs)

    def install(self):
        self._apt(self.apt_pkgs)
        return True

    def pre_install(self):
        return True

    def post_install(self):
        return True

    def check_requirments(self, installed):
        missing = []
        for required in self.requires:
            if required.lower() not in installed:
                missing.append(required)
        if missing:
            raise DependencyError('Module {} requires: {}.'.format(
                self.__class__.__name__, ', '.join(missing)))

    def run(self, cmd, wrap=True, capture=False):
        if wrap:
            pretty_cmd = ' '.join(cmd.split())
            display_cmd(pretty_cmd, wrap=True, script=self.args.generate_script)
        else:
            display_cmd(cmd, wrap=False, script=self.args.generate_script)

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
            action=action, dry=dry, packages=packages))
        return True

    def info(self, title, msg):
        info.append([title, msg])
