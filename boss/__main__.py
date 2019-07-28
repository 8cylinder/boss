# run-shell-command :: ../build.bash

import os
import sys
import string
import random
# from enum import Enum
import subprocess
import argparse
import textwrap
from pprint import pprint as pp
import datetime
import urllib.request
import json
from collections import namedtuple
import deps.click as click
# import IPython

from util import display_cmd
from util import title
from util import warn
from util import error
from util import notify
from util import password_gen

from dist import Dist
from bash import Bash

from mods.aptproxy import AptProxy
from mods.bashrc import Bashrc
from mods.cert import Cert
from mods.craft import Craft2
from mods.craft import Craft3
from mods.django import Django
from mods.django import Wagtail
from mods.databases import Mysql
from mods.done import Done
from mods.fakesmtp import FakeSMTP
from mods.first import First
from mods.lamp import Lamp
from mods.netdata import Netdata
from mods.newuser import NewUser
from mods.php import Php
from mods.php import Xdebug
from mods.php import PhpInfo
from mods.php import Composer
from mods.phpmyadmin import PhpMyAdmin
from mods.virtualhost import VirtualHost
from mods.webmin import Webmin
from mods.webservers import Apache2
from mods.webservers import Nginx
from mods.wordpress import Wordpress
from mods.wordpress import WpCli


class DependencyError(Exception): pass
class PlatformError(Exception): pass
class SecurityError(Exception): pass

info = []


# --------------------------------- UI ---------------------------------

def init(args):
    # list of all modules and the order they should be executed in.
    mods = [
        AptProxy,
        First,  # this is a required module
        NewUser,
        Cert,
        Lamp,
        Apache2,
        Nginx,
        Php,
        PhpInfo,
        Mysql,
        Composer,
        Xdebug,
        PhpMyAdmin,
        Craft2,
        Craft3,
        FakeSMTP,
        VirtualHost,
        WpCli,
        Netdata,
        Webmin,
        Bashrc,
        Done,
    ]
    if args.subparser_name == 'install':
        install_uninstall(args, mods)
    elif args.subparser_name == 'uninstall':
        install_uninstall(args, mods)
    elif args.subparser_name == 'list':
        list_modules(args, mods)
    elif args.subparser_name == 'help':
        found = False
        w = textwrap.TextWrapper(initial_indent='', subsequent_indent='  ', break_on_hyphens=False)
        for mod in mods:
            # if args.module.lower() in mapping[0].lower() or args.module == 'all':
            if args.module.lower() in mod.__class__.__name__.lower() or args.module == 'all':
                app = mod()
                print()
                title(app.__class__.__name__, show_date=False)
                if app.__doc__:
                    lines = app.__doc__.split('\n')
                    lines = [i.strip() for i in lines]
                    print('\n'.join(lines))
                else:
                    print('(No documentation)')
                if app.apt_pkgs:
                    print()
                    # print('Installed apt packages:', end=' ')
                    installed = w.wrap('Installed packages: {}'.format(', '.join(app.apt_pkgs)))
                    print('\n'.join(installed))
                if app.requires:
                    print()
                    print('Requires: {}'.format(', '.join(app.requires)))

                found = True
        if not found:
            error('Unknown module: {}.  Try `boss list`'.format(args.module))


def list_modules(args, mods):
    installed_file = os.path.expanduser('~/boss-installed-modules')
    installed = []
    if os.path.exists(installed_file):
        with open(installed_file) as f:
            installed = f.readlines()
        installed = [i.lower().strip() for i in installed]

    for mod in mods:
        name = mod.__name__
        module = mod
        # state = '[X] ' if name in installed else '[-] '
        state = ' ✓ ' if name in installed else '   '
        state = click.style(state, fg='green')
        description = module.__doc__ if module.__doc__ else ''
        description = description.split('\n')[0]
        click.echo(
            state +
            click.style(name.ljust(13), bold=True) +
            description
        )
        sys.stdout.flush()


def install_uninstall(args, mods):
    modules = args.modules

    required = ['first', 'done']
    # extract the requested modules and the required from mods list
    if args.subparser_name == 'install':
        if args.no_required:
            apps = [i for i in mods if i in modules]
        else:
            apps = [i for i in mods if i in modules or i in required]
    else:
        apps = [i for i in mods if i in modules]

    # check if the user is asking for non-existent modules
    mapping_keys = [i.__name__.lower() for i in mods]
    invalid_modules = [i for i in modules if i not in mapping_keys]
    if invalid_modules:
        error('module(s) "{invalid}" does not exist.\nValid modules are:\n{valid}'.format(
            valid=', '.join(mapping_keys),
            invalid=', '.join(invalid_modules)
        ))

    # check if the requested modules have their dependencies met
    if args.subparser_name == 'install' and not args.no_dependencies:
        install_reqs = []
        print(apps)
        for mapping in apps:
            try:
                app = mapping()
            except subprocess.CalledProcessError as e:
                error(e)
            except DependencyError as e:
                error(e)
            except PlatformError as e:
                # print(e)
                error(e)
            except SecurityError as e:
                error(e)

            install_reqs += app.provides
            provided = set(install_reqs)
            required = set(app.requires)
            # print(provided, required)
            if len(required - provided):
                error('Requirements not met for {}: {}.'.format(
                    app.__class__.__name__, ', '.join(app.requires)))

    if args.generate_script:
        sys.stdout.write('#!/usr/bin/env bash\n\n')
        sys.stdout.write('# {}\n\n'.format(' '.join(sys.argv)))
        sys.stdout.write('PS4=\'+ ${LINENO}: \'\n')
        sys.stdout.write('set -x\n')

    user = None
    installed = []
    for mapping in apps:
        App = mapping[1]
        module_name = App.__name__
        title(module_name, script=args.generate_script)
        # module_title = '{} '.format(module_name)
        # title(module_title.ljust(CONSOLE_WIDTH, '-'))
        app = App(dry_run=args.dry_run, args=args)

        # if mapping == 'newuser':
        #     # set the user after 'newuser' has run so the rest of the modules
        #     # will use the new user.
        #     user, _ = self.args.new_system_user_and_pass

        try:
            if args.subparser_name == 'install':
                if not args.no_dependencies:
                    app.check_requirments(installed)
                app.pre_install()
                app.install()
                app.post_install()
                installed += app.provides
                app.log('install', module_name)
            elif args.subparser_name == 'uninstall':
                app.uninstall()
                app.post_uninstall()
                app.log('uninstall', module_name)
        except subprocess.CalledProcessError as e:
            error(e)
        except DependencyError as e:
            error(e)
        except PlatformError as e:
            error(e)
        except SecurityError as e:
            error(e)


if __name__ == '__main__':
    # https://stackoverflow.com/questions/44247099/click-command-line-interfaces-make-options-required-if-other-optional-option-is
    # https://docs.python.org/3/library/zipapp.html

    # custom types for argparse
    def userpass(s):
        try:
            username, password = [i.strip() for i in s.split(',', 1) if i.strip()]
        except ValueError:
            msg = '''must be a username and password seperated by a comma
            (the password can have a comma in it, but not the username).'''
            raise argparse.ArgumentTypeError(msg)
        return username.strip(), password.strip()

    def userpassemail(s):
        try:
            username, email, password = [i.strip() for i in s.split(',', 2) if i.strip()]
        except ValueError:
            msg = '''must be a username, email and password seperated by a comma
            (the password can have a comma in it, but not the username or email).'''
            raise argparse.ArgumentTypeError(msg)
        return username.strip(), email.strip(), password.strip()

    def newsite(s):
        sites = s.split(':')
        cleaned_sites = []
        for site in sites:
            try:
                sitename, documentroot = [i.strip() for i in site.split(',', 1) if i.strip()]
            except ValueError:
                msg = 'must be a sitename and document root seperated by a comma.'
                raise argparse.ArgumentTypeError(msg)
            # if '/' in documentroot:
            #     raise argparse.ArgumentTypeError('DOCUMENTROOT cannot have a "/" in it.')
            cleaned_sites.append((sitename, documentroot))
        return cleaned_sites

    def file_exists(s):
        if not os.path.exists(s):
            msg = 'file must exist.'
            raise argparse.ArgumentTypeError(msg)
        else:
            return s

    def url(s):
        if '.' not in s:
            msg = 'the servername must have a "." in it, eg. something.local'
            raise argparse.ArgumentTypeError(msg)
        else:
            return s

    # help_msg = 'Install various aplications and miscellany to set up a server.'
    help_msg = textwrap.dedent('''
    Install various applications and miscellany to set up a server.

    This can be run standalone or as a Vagrant provider.  When run as
    a vagrant provider its recommended that is be run unprivileged.
    This will run as the default user and the script will use sudo
    when necessary (this assumes the default user can use sudo).  This
    means that any subsequent uses as the default user will be able to
    update the '$HOME/boss-installed-modules' file.  Also if the
    bashrc module is installed during provisioning, then the correct
    home dir will be setup.

    eg:
    config.vm.provision :shell,
                        path: 'boss',
                        args: 'install server.local ...'

    Its recommended to set up Apt-Cacher NG on the host machine.  Once
    that's done adding `aptproxy` to the list of modules will configure
    this server to make use of it.

    boss will attempt to install colorama when it's run.  If for some
    reason that doesn't work, it can be manually installed by:
    `sudo apt install python3-colorama`''')

    epilog_msg = 'https://www.github.com/8cylinder/sink'

    parser = argparse.ArgumentParser(
        description=help_msg, epilog=epilog_msg,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='subparser_name')

    ## INSTALL ##
    ins = subparsers.add_parser('install', help='Install modules')
    ins.add_argument('servername', type=url,
                     help="used for the cert name and apache ServerName, eg: 'something.local'")
    ins.add_argument('modules', nargs='+',
                     help='a list of modules that should be installed')

    ins.add_argument('-d', '--dry-run', action='store_true',
                     help='Only print the commands that would be used')
    ins.add_argument('-o', '--no-required', action='store_true',
                     help="Don't install the required modules")
    ins.add_argument('-O', '--no-dependencies', action='store_true',
                     help="Don't install dependent modules")
    ins.add_argument('--generate-script', action='store_true',
                     help='Output suitable for a bash script instead of running them')
    # unix user
    ins.add_argument('-n', '--new-user-and-pass', type=userpass, metavar='USERNAME,USERPASS',
                     help="a new unix user's name and password (seperated by a comma), they will be added to the www-data group")
    # mysql
    ins.add_argument('-S', '--sql-file', type=file_exists, metavar='SQLFILE',
                     help='sql file to be run during install')
    ins.add_argument('-N', '--db-name', metavar='DB-NAME',
                     required='mysql' in sys.argv or 'lamp' in sys.argv or 'craft3' in sys.argv,
                     help="the name the schema to create")
    ins.add_argument('-P', '--db-root-pass', metavar='PASSWORD',
                     required='mysql' in sys.argv or 'lamp' in sys.argv or 'craft3' in sys.argv or 'phpmyadmin' in sys.argv,
                     help='password for mysql root user, required for the mysql module')
    ins.add_argument('-A', '--new-db-user-and-pass', type=userpass, metavar='USERNAME,PASSWORD',
                     help="a new db user's new username and password (seperated by a comma)")
    # new user
    ins.add_argument('-u', '--new-system-user-and-pass', type=userpass, metavar='USERNAME,PASSWORD',
                     required='newuser' in sys.argv,
                     help="a new system user's new username and password (seperated by a comma)")
    # newsite
    ins.add_argument('-s', '--site-name-and-root', type=newsite, metavar='SITENAME,DOCUMENTROOT[:...]',
                    required='newsite' in sys.argv,
                     help='''SITENAME and DOCUMENTROOT seperated by a comma (doc root will be put in /var/www).
                       Multiple sites can be specified by seperating them with a ":", eg: -s site1,root1:site2,root2''')
    # craft 3
    ins.add_argument('-c', '--craft-credentials', type=userpassemail, metavar='USERNAME,EMAIL,PASSWORD',
                     help='Craft admin credentials. If not set, only system requirements for Craft will be installed')
    # aptproxy
    ins.add_argument('-i', '--host-ip',
                     required='aptproxy' in sys.argv,
                     help='Host ip to be used in aptproxy config')
    # netdata
    ins.add_argument('--netdata-user-pass', type=userpass, metavar='USERNAME,USERPASS',
                     help="a new user's name and password (seperated by a comma)")

    ## UNINSTALL ##
    uni = subparsers.add_parser('uninstall', help='Uninstall modules')
    uni.add_argument('modules', nargs='+',
                     help='a list of modules that should be uninstalled')
    uni.add_argument('-d', '--dry-run', action='store_true',
                     help='run apt but use `apt-get --simulate` (non apt shell commands will still execute)')
    uni.add_argument('-D', '--very-dry-run', action='store_true',
                     help='do not run any shell commands')
    uni.add_argument('-c', '--cert-basename', required='cert' in sys.argv,
                     help='basename of the cert to be removed, should be the same as servername')
    uni.add_argument('-u', '--system-user', required='newuser' in sys.argv,
                     help='name of the user to be deleted (note: all files will be deleted as well)')

    ## LIST ##
    lst = subparsers.add_parser('list', help='List available modules')

    ## HELP ##
    hlp = subparsers.add_parser('help', help='Detailed info for each module')
    hlp.add_argument('module', nargs='?', default='all',
                     help='The name of the module that you want more info about')

    args = parser.parse_args()
    try:
        init(args)
    except KeyboardInterrupt:
        print('\nQuiting.')
        sys.exit(1)

