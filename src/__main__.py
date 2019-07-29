# run-shell-command :: ../build.bash

import sys
import os
import argparse
import textwrap
import subprocess
import socket
from pprint import pprint as pp
import deps.click as click
from collections import namedtuple

from errors import DependencyError
from errors import PlatformError
from errors import SecurityError
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
# from mods.django import Django
# from mods.django import Wagtail
from mods.databases import Mysql
from mods.databases import PhpMyAdmin
from mods.done import Done
# from mods.example import Example
from mods.fakesmtp import FakeSMTP
from mods.first import First
from mods.lamp import Lamp
from mods.netdata import Netdata
from mods.newuser import NewUser
from mods.php import Php
from mods.php import Xdebug
from mods.php import PhpInfo
from mods.php import Composer
from mods.virtualhost import VirtualHost
from mods.webmin import Webmin
from mods.webservers import Apache2
from mods.webservers import Nginx
from mods.wordpress import Wordpress
from mods.wordpress import WpCli


mods = [
    AptProxy,
    First,      # required module
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
    Netdata,
    Webmin,
    Bashrc,
    Done,       # required module
]


# ---------------------------- Custom types ----------------------------

class Server(click.ParamType):
    """Check if a string sort of looks like a url by checking for a '.' in it"""
    name = 'server'
    def convert(self, value, param, ctx):
        if '.' not in value:
            msg = 'the servername must have a "." in it, eg. something.local'
            self.fail(msg, param, ctx)
            # raise argparse.ArgumentTypeError(msg)
        else:
            return value
SERVER = Server()

class UserPass(click.ParamType):
    """Check if a string is a username and password

    format: username,password"""

    name = 'user_pass'
    def convert(self, value, param, ctx):
        try:
            username, password = [i.strip() for i in value.split(',', 1) if i.strip()]
        except ValueError:
            msg = '''must be a username and password seperated by a comma
            (the password can have a comma in it, but not the username).'''
            self.fail(msg, param, ctx)
            # raise argparse.ArgumentTypeError(msg)
        return username.strip(), password.strip()
USER_PASS = UserPass()

class SiteDocroot(click.ParamType):
    """Check if a string is a sitename and document root

    Format: sitename,docroot[:...]
    Example: siteone.local,siteone/html:sitetwo.local,sitetwo/html"""

    name = 'site_docroot'
    def convert(self, value, param, ctx):
        sites = value.split(':')
        cleaned_sites = []
        for site in sites:
            try:
                sitename, documentroot = [i.strip() for i in site.split(',', 1) if i.strip()]
            except ValueError:
                msg = 'must be a sitename and document root seperated by a comma.'
                self.fail(msg, param, ctx)
                # raise argparse.ArgumentTypeError(msg)
            # if '/' in documentroot:
            #     raise argparse.ArgumentTypeError('DOCUMENTROOT cannot have a "/" in it.')
            cleaned_sites.append((sitename, documentroot))
        return cleaned_sites
SITE_DOCROOT = SiteDocroot()

class UserEmailPass(click.ParamType):
    name = 'user_email_pass'
    def convert(self, value, param, ctx):
        try:
            username, email, password = [i.strip() for i in value.split(',', 2) if i.strip()]
        except ValueError:
            msg = '''must be a username, email and password seperated by a comma
            (the password can have a comma in it, but not the username or email).'''
            self.fail(msg, param, ctx)
            # raise argparse.ArgumentTypeError(msg)
        return username.strip(), email.strip(), password.strip()
USER_EMAIL_PASS = UserEmailPass()

class IpAddress(click.ParamType):
    name = 'ip_address'
    def convert(self, value, param, ctx):
        try:
            socket.inet_pton(socket.AF_INET, value)
        except OSError:
            msg = 'Ip address is not vaid'
            self.fail(msg, param, ctx)
        return value
IP_ADDRESS = IpAddress()

def deps(*dependencies):
    # remove the first three arguments and any options so only
    # the wanted modules are left
    cmd_mods = [i for i in sys.argv if not i.startswith('-')][3:]
    for i in dependencies:
        if i in cmd_mods:
            return True
    return False


# --------------------------------- UI ---------------------------------

CONTEXT_SETTINGS = {
    # add -h in addition to --help
    'help_option_names': ['-h', '--help'],
    # allow case insensitive commands
    'token_normalize_func': lambda x: x.lower(),
}

@click.group(no_args_is_help=True, context_settings=CONTEXT_SETTINGS)
def boss():
    """👔 Install various applications and miscellany to set up a dev server.

    This can be run standalone or as a Vagrant provider.  When run as
    a vagrant provider its recommended that is be run unprivileged.
    This will run as the default user and the script will use sudo
    when necessary (this assumes the default user can use sudo).  This
    means that any subsequent uses as the default user will be able to
    update the '$HOME/boss-installed-modules' file.  Also if the
    bashrc module is installed during provisioning, then the correct
    home dir will be setup.

    \b
    eg:
    config.vm.provision :shell,
                        path: 'boss',
                        args: 'install server.local ...'

    Its recommended to set up Apt-Cacher NG on the host machine.  Once
    that's done adding `aptproxy` to the list of modules will configure
    this server to make use of it."""


@boss.command()     # no_args_is_help=True # Click 7.1
@click.argument('servername', type=SERVER)
@click.argument('modules', nargs=-1, required=True)

@click.option('-d', '--dry-run', is_flag=True,
              help='Only print the commands that would be used')
@click.option('-o', '--no-required', is_flag=True,
              help="Don't install the required modules")
@click.option('-O', '--no-dependencies', is_flag=True,
              help="Don't install dependent modules")
@click.option('--generate-script', is_flag=True,
              help='Output suitable for a bash script instead of running them')

# unix user
@click.option('-n', '--new-user-and-pass', type=USER_PASS, metavar='USERNAME,USERPASS',
              help="a new unix user's name and password (seperated by a comma), they will be added to the www-data group")
# mysql
@click.option('-S', '--sql-file', type=click.Path(exists=True, dir_okay=False), metavar='SQLFILE',
              help='sql file to be run during install')
@click.option('-N', '--db-name', metavar='DB-NAME',
              required=deps('mysql', 'lamp', 'craft3'),
              help="the name the schema to create")
@click.option('-P', '--db-root-pass', default="password", metavar='PASSWORD',
              required=deps('mysql', 'lamp', 'craft3', 'phpmyadmin'),
              help='password for mysql root user, required for the mysql module')
@click.option('-A', '--new-db-user-and-pass', type=USER_PASS, metavar='USERNAME,PASSWORD',
              help="a new db user's new username and password (seperated by a comma)")
# new user
@click.option('-u', '--new-system-user-and-pass', type=USER_PASS, metavar='USERNAME,PASSWORD',
              required=deps('newuser'),
              help="a new system user's new username and password (seperated by a comma)")
# virtualhost
@click.option('-s', '--site-name-and-root', type=SITE_DOCROOT, metavar='SITENAME,DOCUMENTROOT[:...]',
              required=deps('virtualhost'),
              help='''SITENAME and DOCUMENTROOT seperated by a comma (doc root will be put in /var/www).
Multiple sites can be specified by seperating them with a ":", eg: -s site1,root1:site2,root2''')
# craft 3
@click.option('-c', '--craft-credentials', type=USER_EMAIL_PASS, metavar='USERNAME,EMAIL,PASSWORD',
              help='Craft admin credentials. If not set, only system requirements for Craft will be installed')
# aptproxy
@click.option('-i', '--host-ip', type=IP_ADDRESS,
              required=deps('aptproxy'),
              help='Host ip to be used in aptproxy config')
# netdata
@click.option('--netdata-user-pass', type=USER_PASS, metavar='USERNAME,USERPASS',
              help="a new user's name and password (seperated by a comma)")

def install(**args):
    """
    used for the cert name and apache ServerName, eg: 'something.local'
    """
    Args = namedtuple('Args', sorted(args))
    args = Args(**args)

    available_mods = mods
    wanted_mods = [i.lower() for i in args.modules]
    required_mods = ['first', 'done']
    # extract the requested modules and the required from available_mods list
    if args.no_required:
        wanted_apps = [i for i in available_mods if i.__name__.lower() in wanted_mods]
    else:
        wanted_apps = [i for i in available_mods if i.__name__.lower() in wanted_mods or i.__name__.lower() in required_mods]

    # check if the user is asking for non-existent modules
    mapping_keys = [i.__name__.lower() for i in available_mods]
    invalid_modules = [i for i in wanted_mods if i not in mapping_keys]
    if invalid_modules:
        error('module(s) "{invalid}" does not exist.\nValid modules are:\n{valid}'.format(
            valid=', '.join(mapping_keys),
            invalid=', '.join(invalid_modules)
        ))

    # check if the requested modules have their dependencies met
    if not args.no_dependencies:
        install_reqs = []
        for app in wanted_apps:
            install_reqs += app.provides
            provided = set(install_reqs)
            required = set(app.requires)
            if len(required - provided):
                error('Requirements not met for {}: {}.'.format(
                    app.__name__.lower(), ', '.join(app.requires)))

    if args.generate_script:
        sys.stdout.write('#!/usr/bin/env bash\n\n')
        sys.stdout.write('# {}\n\n'.format(' '.join(sys.argv)))
        sys.stdout.write('PS4=\'+ ${LINENO}: \'\n')
        sys.stdout.write('set -x\n')

    for App in wanted_apps:
        module_name = App.title
        title(module_name, script=args.generate_script)
        try:
            app = App(dry_run=args.dry_run, args=args)
            app.pre_install()
            app.install()
            app.post_install()
            app.log('install', module_name)
        except subprocess.CalledProcessError as e:
            error(e)
        except DependencyError as e:
            error(e)
        except PlatformError as e:
            error(e)
        except SecurityError as e:
            error(e)
        except FileNotFoundError as e:
            error(e.args[0])

@boss.command()
def list():
    """List available modules"""
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

@boss.command()
def help():
    """Show help for each module"""

    content = []
    w = textwrap.TextWrapper(initial_indent='', subsequent_indent='  ', break_on_hyphens=False)
    for mod in mods:
        try:
            app = mod()
        except PlatformError as e:
            content.append('')
            warn(e)
        content.append('')

        title = '{} ({})'.format(app.title, app.__class__.__name__.lower())
        under = '-' * len(title)
        content.append(click.style(title, fg='blue', bold=True))
        content.append(click.style(under, fg='blue'))

        if app.__doc__:
            lines = app.__doc__.split('\n')
            lines = [i.strip() for i in lines]
            content.append('\n'.join(lines))
        else:
            content.append(click.style('(No documentation)', dim=True))
        if app.apt_pkgs:
            content.append('')
            installed = w.wrap('Installed packages: {}'.format(', '.join(app.apt_pkgs)))
            content.append('\n'.join(installed))
        if app.requires:
            content.append('')
            content.append('Requires: {}'.format(', '.join(app.requires)))
    click.echo_via_pager('\n'.join(content))


if __name__ == '__main__':
    boss()
