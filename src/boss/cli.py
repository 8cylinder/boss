"""CLI for Boss - a tool to install and configure a server."""

import importlib.metadata
import os
import re
import socket
import subprocess
import sys
import textwrap
from pathlib import Path
from pprint import pprint as pp  # noqa
from typing import Any

import click
from click.core import Context, Parameter
from dotenv import load_dotenv

from boss.dist import UbuntuVersion
from boss.engine import Args
from boss.errors import (
    DependencyError,
    ModuleRequestError,
    PlatformError,
    SecurityError,
)
from boss.mods.aptproxy import AptProxy
from boss.mods.bashrc import Bashrc
from boss.mods.cert import LetsEncryptCert, SelfCert
from boss.mods.craft import Craft
from boss.mods.databases import Adminer, Mysql, PhpMyAdmin
from boss.mods.fakesmtp import FakeSMTP  # noqa: F401
from boss.mods.firewall import Firewall
from boss.mods.first import First
from boss.mods.last import Last
from boss.mods.netdata import Netdata
from boss.mods.newuser import NewUserAsRoot, Personalize
from boss.mods.phpbin import Composer, PhpBin, PhpInfo, Xdebug
from boss.mods.virtualhost import VirtualHost
from boss.mods.webmin import Webmin
from boss.mods.webservers import Apache2, Nginx
from boss.util import error, title

# Load environment variables from .env file in current dir or parent directories
# load_dotenv(dotenv_path=".env.boss")


def find_dotenv_file() -> Path | None:
    """Search for .env or .env.boss file in current and parent directories."""
    current = Path.cwd()
    while current != current.parent:
        env_file = current / ".env"
        env_boss = current / ".env.boss"

        if env_boss.exists():
            return env_boss
        if env_file.exists():
            return env_file

        current = current.parent
    return None


if dotenv_path := find_dotenv_file():
    click.echo(
        click.style("Loading vars from: ", fg="green")
        + click.style(f'"{dotenv_path}"', fg="green", bold=True),
    )
    load_dotenv(dotenv_path)

# Prefix for environment variables
PREFIX = "BOSS_"

__version__ = importlib.metadata.version("boss")

# All the mods available in the order they should be run
MODS = (
    AptProxy,
    First,  # required
    NewUserAsRoot,
    Personalize,
    LetsEncryptCert,
    SelfCert,
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
    Firewall,
    Last,  # required
)


def is_server(server: str) -> bool:
    """Check if a string sort of looks like a url by checking for a '.' in it."""
    return "." in server
    # if "." not in server:
    #     return False
    # return True


def is_email(email: str) -> bool:
    """Check if a string is a valid email address."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def is_ipaddress(ip: str) -> bool:
    """Check if a string is a valid IPv4 address."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except OSError:
        return False
    return True


def get_matching_modules(wanted_mods: list[str]) -> list[Any]:
    """Return a list of modules that match the requested module names.

    Try and match partial names too, but if there are multiple matches,
    raise an error.

    Sort the list of modules by their order in MODS and remove duplicates.
    """
    matching_mods: list[Any] = []
    for wanted_mod in wanted_mods:
        wanted = wanted_mod.lower()
        error_matches: list[str] = []
        matched_count = 0
        for mod in MODS:
            module_name = mod.__name__.lower()
            if module_name == wanted:
                matching_mods.append(mod)
                continue
            if module_name.startswith(wanted):
                error_matches.append(module_name)
                matching_mods.append(mod)
                matched_count += 1
        if matched_count > 1:
            # Convert a list of items to: '"itema", "itemb" and "itemc"'
            quoted = [f'"{i}"' for i in error_matches]
            matches = ", ".join([*quoted[:-2], " and ".join(quoted[-2:])])
            error_msg = f'Module name "{wanted}" is ambiguous, it matches: {matches}'
            raise ModuleRequestError(error_msg)

    # sort the matching_mods by their order in MODS
    matching_mods.sort(key=lambda x: MODS.index(x))

    # remove duplicates from the list
    seen = set()
    deduped_mods: list[Any] = []
    for x in matching_mods:
        if x not in seen:
            deduped_mods.append(x)
            seen.add(x)
    if First in deduped_mods:
        deduped_mods.remove(First)
    if Last in deduped_mods:
        deduped_mods.remove(Last)

    return deduped_mods


# ---------------------------- Custom types ----------------------------


class Server(click.ParamType):
    """Check if a string sort of looks like a url by checking for a '.' in it."""

    name = "server"

    def convert(
        self,
        value: str,
        param: Parameter | None,
        ctx: Context | None,
    ) -> str | None:
        """Convert the value to a valid server name if possible."""
        if not is_server(value):
            msg = 'the servername must have a "." in it, eg. something.local'
            self.fail(msg, param, ctx)
        return value


SERVER = Server()


class UserPass(click.ParamType):
    """Check if a string is a username and password.

    format: username,password
    """

    name = "user_pass"

    def convert(
        self,
        value: str,
        param: Parameter | None,
        ctx: Context | None,
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
    """Check if a string is a sitename and document root.

    Format: SITENAME,DOCROOT,CREATEDIR[:...]
    Example: siteone.local,siteone,y/html:sitetwo.local,sitetwo,n/html
    """

    name = "site_docroot"

    def convert(
        self,
        value: str,
        param: Parameter | None,
        ctx: Context | None,
    ) -> list[tuple[str, str, str]]:
        """Convert the value to a tuple of (sitename, documentroot, createdir)."""
        sites = value.split(":")
        cleaned_sites = []
        msg = (
            'must be a sitename, document root and a "y" or "n" '
            "(create site dir) seperated by a comma, and sitename "
            "must have a . in it"
        )
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
        self,
        value: str,
        param: Parameter | None,
        ctx: Context | None,
    ) -> tuple[str, str, str]:
        """Convert the value to a tuple of (username, email, password)."""
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
            msg = f"{msg}\n\nEmail is not valid"
            self.fail(msg, param, ctx)
        return username.strip(), email.strip(), password.strip()


USER_EMAIL_PASS = UserEmailPass()


class IpAddress(click.ParamType):
    """Check if a string is a valid IPv4 address."""

    name = "ip_address"

    def convert(self, value: str, param: Parameter | None, ctx: Context | None) -> str:
        """Convert the value to a valid IPv4 address if possible."""
        msg = "Ip address is not vaid"
        if not is_ipaddress(value):
            self.fail(msg, param, ctx)
        return value


IP_ADDRESS = IpAddress()


def deps(*dependencies: str) -> bool:
    """Check if the command line arguments contain any of the dependencies.

    Iterate over the requested modules and check if any of the
    dependencies are in the command line arguments.
    """
    # remove the first three arguments and any options so only
    # the wanted modules are left
    cmd_mods = [i for i in sys.argv if not i.startswith("-")][3:]
    return any(i in cmd_mods for i in dependencies)


# --------------------------------- UI ---------------------------------

CONTEXT_SETTINGS = {
    # add -h in addition to --help
    "help_option_names": ["-h", "--help"],
    "show_default": True,
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
def boss() -> None:
    """👔 Boss - a tool to install and configure a server.

    Use `boss --help` for more information on how to use it.
    """


@boss.command(context_settings=CONTEXT_SETTINGS)
@click.argument("modules", nargs=-1, required=True, envvar=f"{PREFIX}MODULES")
@click.option(
    "--bash/--ansible",
    " /-a",
    default=True,
    help="Use bash or ansible for the commands",
)
@click.option(
    "-U",
    "--servername",
    type=SERVER,
    metavar="SERVERNAME",
    envvar=f"{PREFIX}SERVERNAME",
    help="The server name to use for the self-signed certificate and virtual host.",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Only print the commands that would be used",
)
@click.option(
    "--required/--no-required",
    " /-R",
    default=True,
    help="Install the required modules, first & last",
)
@click.option(
    "--dependencies/--no-dependencies",
    " /-D",
    default=True,
    help="Require dependencies",
)
@click.option(
    "--generate-script",
    is_flag=True,
    help="Output suitable for a bash script instead of running them",
)
@click.option(
    "--dist-version",
    type=click.Choice(UbuntuVersion),
    help="The version of Ubuntu to assume instead of autodetect.",
)
# unix user
@click.option(
    "-n",
    "--new-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,USERPASS",
    envvar=f"{PREFIX}NEW_USER_AND_PASS",
    help="a new unix user's name and password (seperated by a comma), they will be added to the www-data group",
)
# mysql
@click.option(
    "-S",
    "--sql-file",
    type=click.Path(exists=True, dir_okay=False),
    metavar="SQLFILE",
    envvar=f"{PREFIX}SQLFILE",
    help="sql file to be run during install",
)
@click.option(
    "-N",
    "--db-name",
    metavar="DB-NAME",
    envvar=f"{PREFIX}DB_NAME",
    required=deps("mysql", "lamp", "craft"),
    help="the name the schema to create",
)
@click.option(
    "-P",
    "--db-root-pass",
    metavar="PASSWORD",
    envvar=f"{PREFIX}DB_ROOT_PASS",
    required=deps("mysql", "lamp", "phpmyadmin"),
    help="password for mysql root user, required for the mysql module",
)
@click.option(
    "-A",
    "--new-db-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,PASSWORD",
    envvar=f"{PREFIX}NEW_DB_USER_AND_PASS",
    required=deps("craft"),
    help="a new db user's new username and password (seperated by a comma)",
)
# new user
@click.option(
    "-u",
    "--new-system-user-and-pass",
    type=USER_PASS,
    metavar="USERNAME,PASSWORD",
    envvar=f"{PREFIX}NEW_SYSTEM_USER_AND_PASS",
    required=deps("newuser"),
    help="a new system user's new username and password (seperated by a comma)",
)
# virtualhost
@click.option(
    "-s",
    "--site-name-and-root",
    type=SITE_DOCROOT,
    metavar="SITENAME,DOCUMENTROOT[:...]",
    envvar=f"{PREFIX}SITE_NAME_AND_ROOT",
    required=deps("virtualhost", "craft"),
    help="""SITENAME, DOCUMENTROOT and CREATEDIR seperated by a comma (doc root will be put in /var/www).
        CREATEDIR is an optional y/n that indicates if to create the dir or not (default:n).
        Multiple sites can be specified by seperating them with a ":", eg: -s site1,root1,y:site2,root2""",  # noqa: E501
)
# craft
@click.option(
    "-c",
    "--craft-credentials",
    type=USER_EMAIL_PASS,
    metavar="USERNAME,EMAIL,PASSWORD",
    envvar=f"{PREFIX}CRAFT_CREDENTIALS",
    help="Craft admin credentials. If not set, only system requirements for Craft will be installed",  # noqa: E501
)
# aptproxy
@click.option(
    "-i",
    "--host-ip",
    type=IP_ADDRESS,
    envvar=f"{PREFIX}HOST_IP",
    required=deps("aptproxy"),
    help="Host ip to be used in aptproxy config",
)
# netdata
@click.option(
    "--netdata-user-pass",
    type=USER_PASS,
    metavar="USERNAME,USERPASS",
    envvar=f"{PREFIX}NETDATA_USER_PASS",
    help="a new user's name and password (seperated by a comma)",
)
def install(**all_args: Any) -> None:
    """👔 Install various applications and miscellany to set up a server.

    MODULES is the list of modules, see `boss list` for available modules.

    Arguments and options can be provided in environment variables and can
    be provided in a .env or .env.boss file in the current directory or
    parent directories.
    """
    # convert the args dict to a namedtuple
    args = Args(**all_args)

    dist_version = args.dist_version or UbuntuVersion.current()
    #     global DIST_VERSION
    #     DIST_VERSION = args.dist_version.value

    wanted_mods = [i.lower() for i in args.modules]

    wanted: list[Any] = []
    try:
        wanted = get_matching_modules(wanted_mods)
    except ModuleRequestError as e:
        error(str(e))

    if args.required:
        # AptProxy is a special case, it should always be first
        if AptProxy in wanted:
            # remove AptProxy from the list of wanted modules
            wanted = [i for i in wanted if i != AptProxy]
            # and add it to the front
            wanted = [AptProxy, First, *wanted, Last]
        else:
            wanted = [First, *wanted, Last]

    # check if the requested modules have their dependencies met
    if args.dependencies:
        provided = []
        requires = []
        for mod in wanted:
            provided += mod.provides
            requires += mod.requires
        missing = set(requires) - set(provided)
        if missing:
            pretty_missing = ", ".join(missing)
            error(f"Requirements not met. Missing: {pretty_missing}")

    if args.generate_script:
        script_header = (
            "#!/usr/bin/env bash",
            "",
            "# Boss command used to generate this script",
            "# {}".format(" ".join(sys.argv)),
            "",
            "set -x",
            r"PS4=$'\e[30;103m+\e[0m '",
        )
        click.echo("\n".join(script_header))
    elif not args.dry_run:
        wanted_list = ", ".join([i.__name__ for i in wanted])
        click.echo(f"Installing: {wanted_list}")
        try:
            if not click.confirm("Continue?", default=True, abort=True):
                sys.exit()
        except (KeyboardInterrupt, click.Abort):
            # don't show the 'Aborted!' message
            sys.exit(1)

    # ensure that the required arguments are provided
    is_error = False
    for app_class in wanted:
        try:
            app = app_class(dry_run=True, args=args, ubuntu_version=dist_version)
            app.ensure_arg_requirements()
        except DependencyError as e:
            is_error = True
            click.secho(str(e), fg="red")
        except PlatformError as e:
            error(str(e))
    if is_error:
        sys.exit(1)

    # add the wanted modules to the args
    args.wanted.extend(wanted)

    for app_class in wanted:
        module_name = app_class.title
        title(module_name, script=args.generate_script)
        try:
            app = app_class(
                dry_run=args.dry_run,
                args=args,
                ubuntu_version=dist_version,
            )
            app.pre_install()
            # app.mod.install()
            app.install()
            app.post_install()
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
        except (KeyboardInterrupt, click.Abort):
            # don't show the 'Aborted!' message
            sys.exit(1)


@boss.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-f/-s",
    "--full/--simple",
    default=False,
    help="Show full or simple output",
)
@click.option("--write-env", is_flag=True, help="Write an env file, .env.boss")
def info(full: bool, write_env: bool) -> None:
    """List any vars defined in a .env and available modules."""
    is_env = False
    for key, val in os.environ.items():
        if key.startswith(PREFIX):
            is_env = True
            click.echo(f'{key}="{val}"')

    if not is_env:
        click.secho(
            f'\nNo environment variables starting with "{PREFIX}" found.',
            fg="yellow",
        )

    click.echo("\n")

    if not full:
        click.secho("Available modules:", fg="green")
        available = ", ".join([i.__name__ for i in MODS])
        available = textwrap.fill(available)
        click.echo(available)

    else:
        indent = "  "
        for mod in MODS:
            click.secho(f"{', '.join(mod.provides)}", bold=True, fg="green")
            if mod.requires:
                click.echo(
                    click.style(f"{indent}Req mods: ", dim=True, fg="cyan")
                    + click.style(", ".join(mod.requires), fg="cyan"),
                )
            if mod.required_args:
                required_args = ", ".join(
                    [f"--{i.replace('_', '-')}" for i in mod.required_args],
                )
                click.echo(
                    click.style(f"{indent}Req opts: ", dim=True, fg="yellow")
                    + click.style(required_args, fg="yellow"),
                )

    if write_env:
        env_content: list[str] = []
        modlist = [i.__name__ for i in MODS]
        env_content.append(f"{PREFIX}MODULES={' '.join(modlist)}")

        for mod in MODS:
            for var in mod.required_args:
                env_content.append(f"{PREFIX}{var.upper()}=")

        overwrite = False
        env_file = Path(".env.boss")
        if env_file.exists():
            overwrite = click.confirm(
                '".env.boss" already exists, overwrite?',
                abort=True,
            )
        if overwrite or not env_file.exists():
            with env_file.open("w") as f:
                f.write("\n".join(env_content))
