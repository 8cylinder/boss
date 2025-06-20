# run-shell-command :: ../build.bash

import sys
import re
import subprocess
import socket
from pprint import pprint as pp  # noqa
import click
from click.core import Parameter, Context
import importlib.metadata
from typing import Any

from .errors import DependencyError, PlatformError, SecurityError, ModuleRequestError
from .util import error, title
from .bash import Args
from .mods.aptproxy import AptProxy
from .mods.bashrc import Bashrc
from .mods.cert import SelfCert
from .mods.cert import LetsEncryptCert
from .mods.craft import Craft
from .mods.databases import Mysql
from .mods.databases import PhpMyAdmin
from .mods.databases import Adminer
from .mods.last import Last
from .mods.fakesmtp import FakeSMTP  # noqa: F401
from .mods.first import First
from .mods.lamp import Lamp  # noqa: F401
from .mods.netdata import Netdata
from .mods.newuser import NewUserAsRoot
from .mods.newuser import Personalize
from .mods.phpbin import PhpBin
from .mods.phpbin import Xdebug
from .mods.phpbin import PhpInfo
from .mods.phpbin import Composer
from .mods.virtualhost import VirtualHost
from .mods.webmin import Webmin
from .mods.webservers import Apache2
from .mods.webservers import Nginx


# DIST_VERSION = None
__version__ = importlib.metadata.version("boss")

DIST_VERSION: float | None = None

# All the mods available in the order they should be run
MODS = (
    AptProxy,
    First,  # required
    NewUserAsRoot,
    Personalize,
    LetsEncryptCert,
    SelfCert,
    # Lamp,
    Apache2,
    Nginx,
    PhpBin,
    Mysql,
    Composer,
    Xdebug,
    PhpMyAdmin,
    Adminer,
    VirtualHost,
    PhpInfo,
    Craft,
    # FakeSMTP,
    Netdata,
    Webmin,
    Bashrc,
    Last,  # required
)


def is_server(server: str) -> bool:
    if "." not in server:
        return False
    return True


def is_email(email: str) -> bool:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True


def is_ipaddress(ip: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except OSError:
        return False


def get_matching_modules(wanted_mods: list[str]) -> list[Any]:
    """Return a list of modules that match the requested module names.

    Try and match partial names too, but if there are multiple matches
    raise an error.

    Sort the list of modules by their order in MODS and remove duplicates.
    """
    matching_mods: list[Any] = []
    for wanted in wanted_mods:
        wanted = wanted.lower()
        error_matches: list[str] = []
        matched_count = 0
        for mod in MODS:
            module_name = mod.__name__.lower()
            if module_name == wanted:
                matching_mods.append(mod)
                continue
            elif module_name.startswith(wanted):
                error_matches.append(module_name)
                matching_mods.append(mod)
                matched_count += 1
        if matched_count > 1:
            # Convert a list of items to: '"itema", "itemb" and "itemc"'
            quoted = [f'"{i}"' for i in error_matches]
            matches = ", ".join(quoted[:-2] + [" and ".join(quoted[-2:])])
            raise ModuleRequestError(
                f'Module name "{wanted}" is ambiguous, it matches: {matches}'
            )

    # sort the matching_mods by their order in MODS
    matching_mods.sort(key=lambda x: MODS.index(x))

    # remove duplicates from the list
    seen = set()
    deduped_mods: list[Any] = []
    for x in matching_mods:
        if x not in seen:
            deduped_mods.append(x)
            seen.add(x)

    return deduped_mods


# ---------------------------- Custom types ----------------------------


class Server(click.ParamType):
    """Check if a string sort of looks like a url by checking for a '.' in it"""

    name = "server"

    def convert(self, value: str, param: Parameter | None, ctx: Context | None) -> str:
        if not is_server(value):
            msg = 'the servername must have a "." in it, eg. something.local'
            self.fail(msg, param, ctx)
        else:
            return value


SERVER = Server()


class UserPass(click.ParamType):
    """Check if a string is a username and password

    format: username,password"""

    name = "user_pass"

    def convert(
        self, value: str, param: Parameter | None, ctx: Context | None
    ) -> tuple[str, str]:
        try:
            username, password = [i.strip() for i in value.split(",", 1) if i.strip()]
        except ValueError:
            msg = """must be a username and password seperated by a comma
            (the password can have a comma in it, but not the username)."""
            self.fail(msg, param, ctx)
        return username.strip(), password.strip()


USER_PASS = UserPass()


class SiteDocroot(click.ParamType):
    """Check if a string is a sitename and document root

    Format: SITENAME,DOCROOT,CREATEDIR[:...]
    Example: siteone.local,siteone,y/html:sitetwo.local,sitetwo,n/html"""

    name = "site_docroot"

    def convert(
        self, value: str, param: Parameter | None, ctx: Context | None
    ) -> list[tuple[str, str, str]]:
        sites = value.split(":")
        cleaned_sites = []
        msg = 'must be a sitename, document root and a "y" or "n" (create site dir) seperated by a comma, and sitename must have a . in it'
        msg = " ".join(msg.split())
        for site in sites:
            try:
                sitename, documentroot, createdir = [
                    i.strip() for i in site.split(",", 2) if i.strip()
                ]
            except ValueError:
                self.fail(msg, param, ctx)
            if not is_server(sitename):
                self.fail(msg, param, ctx)
            if createdir.lower() not in ["y", "n"]:
                self.fail(msg, param, ctx)
            cleaned_sites.append((sitename, documentroot, createdir))
        return cleaned_sites


SITE_DOCROOT = SiteDocroot()


class UserEmailPass(click.ParamType):
    """Check if a string is a username, email and password seperated by a comma."""

    name = "user_email_pass"

    def convert(
        self, value: str, param: Parameter | None, ctx: Context | None
    ) -> tuple[str, str, str]:
        msg = """must be a username, email and password seperated by a comma
                 (the password can have a comma in it, but not the username or email)."""
        msg = " ".join(msg.split())
        try:
            username, email, password = [
                i.strip() for i in value.split(",", 2) if i.strip()
            ]
        except ValueError:
            self.fail(msg, param, ctx)
        if not is_email(email):
            self.fail(msg, param, ctx)
        return username.strip(), email.strip(), password.strip()


USER_EMAIL_PASS = UserEmailPass()


class IpAddress(click.ParamType):
    name = "ip_address"

    def convert(self, value: str, param: Parameter | None, ctx: Context | None) -> str:
        msg = "Ip address is not vaid"
        if not is_ipaddress(value):
            self.fail(msg, param, ctx)
        return value


IP_ADDRESS = IpAddress()


def deps(*dependencies: str) -> bool:
    # remove the first three arguments and any options so only
    # the wanted modules are left
    cmd_mods = [i for i in sys.argv if not i.startswith("-")][3:]
    for i in dependencies:
        if i in cmd_mods:
            return True
    return False


# --------------------------------- UI ---------------------------------

CONTEXT_SETTINGS = {
    # add -h in addition to --help
    "help_option_names": ["-h", "--help"],
    # allow case insensitive commands
    "token_normalize_func": lambda x: x.lower(),
}


@click.command(no_args_is_help=True, context_settings=CONTEXT_SETTINGS)
@click.argument("servername", type=SERVER)
@click.argument("modules", nargs=-1, required=True)
@click.option(
    "-d", "--dry-run", is_flag=True, help="Only print the commands that would be used"
)
@click.option(
    "-o", "--no-required", is_flag=True, help="Don't install the required modules"
)
@click.option(
    "-O", "--no-dependencies", is_flag=True, help="Don't install dependent modules"
)
@click.option(
    "--generate-script",
    is_flag=True,
    help="Output suitable for a bash script instead of running them",
)
@click.option(
    "--dist-version",
    type=float,
    help="The version of Ubuntu to assume instead of autodetect.",
)
# unix user
@click.option(
    "-n",
    "--new-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,USERPASS",
    help="a new unix user's name and password (seperated by a comma), they will be added to the www-data group",
)
# mysql
@click.option(
    "-S",
    "--sql-file",
    type=click.Path(exists=True, dir_okay=False),
    metavar="SQLFILE",
    help="sql file to be run during install",
)
@click.option(
    "-N",
    "--db-name",
    metavar="DB-NAME",
    required=deps("mysql", "lamp", "craft"),
    help="the name the schema to create",
)
@click.option(
    "-P",
    "--db-root-pass",
    default="password",
    metavar="PASSWORD",
    required=deps("mysql", "lamp", "phpmyadmin"),
    help="password for mysql root user, required for the mysql module",
)
@click.option(
    "-A",
    "--new-db-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,PASSWORD",
    required=deps("craft"),
    help="a new db user's new username and password (seperated by a comma)",
)
# new user
@click.option(
    "-u",
    "--new-system-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,PASSWORD",
    required=deps("newuser"),
    help="a new system user's new username and password (seperated by a comma)",
)
# virtualhost
@click.option(
    "-s",
    "--site-name-and-root",
    type=SITE_DOCROOT,
    metavar="SITENAME,DOCUMENTROOT[:...]",
    required=deps("virtualhost", "craft"),
    help="""SITENAME, DOCUMENTROOT and CREATEDIR seperated by a comma (doc root will be put in /var/www).
                CREATEDIR is an optional y/n that indicates if to create the dir or not (default:n).
                Multiple sites can be specified by seperating them with a ":", eg: -s site1,root1,y:site2,root2""",
)
# craft
@click.option(
    "-c",
    "--craft-credentials",
    type=USER_EMAIL_PASS,
    metavar="USERNAME,EMAIL,PASSWORD",
    help="Craft admin credentials. If not set, only system requirements for Craft will be installed",
)
# aptproxy
@click.option(
    "-i",
    "--host-ip",
    type=IP_ADDRESS,
    required=deps("aptproxy"),
    help="Host ip to be used in aptproxy config",
)
# netdata
@click.option(
    "--netdata-user-pass",
    type=USER_PASS,
    metavar="USERNAME,USERPASS",
    help="a new user's name and password (seperated by a comma)",
)
@click.version_option(version=__version__)
def boss(**all_args: Any) -> None:
    """👔 Install various applications and miscellany to set up a server.

    MODULES is the list of modules, see `boss list` for available modules.
    SERVERNAME is used to set up the self-signed certificate and virtual host.
    """

    # convert the args dict to a namedtuple
    args = Args(**all_args)

    if args.dist_version:
        global DIST_VERSION
        DIST_VERSION = args.dist_version

    wanted_mods = [i.lower() for i in args.modules]

    wanted: list[Any] = []
    try:
        wanted = get_matching_modules(wanted_mods)
    except ModuleRequestError as e:
        error(str(e))

    if not args.no_required:
        # AptProxy is a special case, it should always be first
        if AptProxy in wanted:
            # remove AptProxy from the list of wanted modules
            wanted = [i for i in wanted if i != AptProxy]
            # and add it to the front
            wanted = [AptProxy, First] + wanted + [Last]
        else:
            wanted = [First] + wanted + [Last]

    # check if the requested modules have their dependencies met
    if not args.no_dependencies:
        provided = []
        requires = []
        for mod in wanted:
            provided += mod.provides
            requires += mod.requires
        missing = set(requires) - set(provided)
        if missing:
            pretty_missing = ", ".join(missing)
            error(f"Requirements not met, missing {pretty_missing}")

    if args.generate_script:
        script_header = (
            "#!/usr/bin/env bash",
            "",
            "# Boss command used to generate this script",
            "# {}".format(" ".join(sys.argv)),
            "",
            "set -x",
        )
        click.echo("\n".join(script_header))
    else:
        if not args.dry_run:
            print("Installing:", ", ".join([i.__name__ for i in wanted]))
            if not click.confirm("Continue?", default=True, abort=True):
                sys.exit()

    for App in wanted:
        module_name = App.title
        title(module_name, script=args.generate_script)
        try:
            app = App(dry_run=args.dry_run, args=args)
            app.pre_install()
            app.install()
            app.post_install()
            app.log(module_name)
        except subprocess.CalledProcessError as e:
            error(str(e))
        except DependencyError as e:
            error(str(e))
        except PlatformError as e:
            error(str(e))
        except SecurityError as e:
            error(str(e))
        except FileNotFoundError as e:
            error(e.args[0])
