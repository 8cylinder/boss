import os
import sys
import re
from .dist import Dist
import datetime
import subprocess
from typing import NamedTuple
from dataclasses import dataclass
from .errors import *
from .util import display_cmd, error, notify
from enum import Enum, auto


class Args(NamedTuple):
    servername: str
    modules: tuple[str, ...]
    dry_run: bool
    no_required: bool
    no_dependencies: bool
    generate_script: bool
    dist_version: float | None
    new_user_and_pass: tuple[str, str]  # ...?
    sql_file: str | None
    db_name: str | None
    db_root_pass: str
    new_db_user_and_pass: tuple[str, str]
    new_system_user_and_pass: tuple[str, str]
    site_name_and_root: list[tuple[str, str, str]]
    craft_credentials: tuple[str, str, str]
    host_ip: str | None
    netdata_user_pass: tuple[str, str]


class Snap(Enum):
    CLASSIC = auto()
    DEFAULT = auto()


@dataclass
class Settings:
    timezone: str = "America/Los_Angeles"


class Bash:
    APTUPDATED = False
    # info_messages: list[list[str]] = []
    info_messages: dict[str, list[tuple[str, str, str]]] = {}
    WWW_USER = "www-data"
    title: str

    def __init__(self, args: Args, dry_run: bool = False) -> None:
        self.ok_code = 0
        self.requires: list[str] = []
        self.apt_pkgs: list[str] = []
        self.snap_pkgs: list[tuple[str, Snap]] = []
        self.provides: list[str] = []
        self.distro = Dist()
        self.dry_run = dry_run
        self.args = args
        self.scriptname = os.path.basename(__file__)
        if args and not dry_run:
            # action = args.subparser_name
            self.log(self.__class__.__name__)
        self.now = datetime.datetime.now().strftime("%y-%m-%d-%X")

    @staticmethod
    def log(name: str) -> None:
        """Logs a module name.

        The method ensures that the file contains a record of unique module names.
        If the log file does not exist, it creates one and records the provided
        module name.
        """
        log_name = "~/boss-installed-modules"
        mod = "{}\n".format(name)
        try:
            with open(os.path.expanduser(log_name), "r") as f:
                installed_mods = f.readlines()
        except FileNotFoundError:
            installed_mods = []

        normalized_mods: set[str] = set(installed_mods)
        normalized_mods.add(mod)

        with open(os.path.expanduser(log_name), "w") as f:
            f.writelines(installed_mods)

    def sed(self, sed_exp: str, config_file: str) -> None:
        new_ext = ".original-{}".format(self.now)
        sed_cmd = f'sudo sed --in-place="{new_ext}" "{sed_exp}" "{config_file}"'
        self.run(sed_cmd)

    def append_to_file(
        self,
        filename: str,
        text: str,
        user: str | None = None,
        nosudo: bool = False,
        backup: bool = True,
        append: bool = True,
    ) -> None:
        if backup:
            new_ext = ".original-{}".format(self.now)
            copy_cmd = 'sudo cp "{file}" "{file}{now}"'.format(
                file=filename, now=new_ext
            )
            self.run(copy_cmd)

        www_user = ""
        if user == self.WWW_USER:
            www_user = "-u {}".format(self.WWW_USER)

        append_flag = ""
        if append is True:
            append_flag = "-a"

        sudo = "" if nosudo else "sudo"

        # add_cmd = f"""#-----------------------------------------------------------------
        # read -r -d '' boss_text <<'EOF'
        # {text}
        # EOF
        # # echo "$boss_text"
        # if [[ ! -e "{filename}" ]] then
        #     # echo 'A'
        #     echo | {sudo} {www_user} tee "{filename}" < <(echo "$boss_text")
        # elif ! grep -Ff < <(echo "$boss_text") "{filename}" >/dev/null; then
        #     # echo 'B'
        #     echo | {sudo} {www_user} tee {append_flag} "{filename}" < <(echo "$boss_text")
        # else
        #     echo "File {filename} already contains the text, not appending."
        # fi
        # #-----------------------------------------------------------------
        # """
        add_cmd = f'echo | sudo {www_user} tee {append_flag} "{filename}" <<EOF\n{text}\nEOF'
        # remove leading spaces from add_cmd using regex
        add_cmd = re.sub(r"^\s+", "", add_cmd, flags=re.MULTILINE)
        self.run(add_cmd, wrap=False)

    def apt(self, progs: list[str]) -> None:
        self._apt(progs)

    def install(self) -> None:
        self._apt(self.apt_pkgs)
        self._snap(self.snap_pkgs)

    def pre_install(self) -> None:
        return

    def post_install(self) -> None:
        return

    def run(
        self, cmd: str, wrap: bool = True, capture: bool = False, comment: str = ""
    ) -> str | int | bytes | None:
        if wrap:
            pretty_cmd = " ".join(cmd.split())
            display_cmd(
                pretty_cmd, wrap=True, script=self.args.generate_script, comment=comment
            )
        else:
            display_cmd(
                cmd, wrap=False, script=self.args.generate_script, comment=comment
            )

        if self.args.dry_run or self.args.generate_script:
            return None
        if capture:
            # result = subprocess.run(cmd, shell=True, check=True, executable='/bin/bash', stdout=subprocess.PIPE)
            result = subprocess.check_output(cmd, shell=True, executable="/bin/bash")
            sys.stdout.flush()
        else:
            # result = subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
            result = subprocess.check_call(cmd, shell=True, executable="/bin/bash")
        return result

    def curl(
        self, url: str, output: str, capture: bool = False
    ) -> str | int | bytes | None:
        cmd = "curl -sSL {url} --output {output}".format(url=url, output=output)
        result = self.run(cmd, capture=capture)
        return result

    def restart_apache(self) -> None:
        """Restart Apache using the appropriate command

        Details about whether to use service or systemctl
        https://askubuntu.com/a/903405"""

        if self.distro == Dist.UBUNTU:
            self.run("sudo service apache2 restart")
        else:
            error("restart_apache has unknown platform")

    def _apt(self, packages_list: list[str]) -> None:
        if not packages_list:
            return
        dry = "--dry-run" if self.dry_run else ""
        packages = " ".join(packages_list)
        if not Bash.APTUPDATED:
            self.run("sudo apt-get --quiet update")
            # self.run('sudo apt-get --quiet --yes upgrade')   # not really necessary
            Bash.APTUPDATED = True
        self.run(
            "export DEBIAN_FRONTEND=noninteractive; sudo apt-get {dry} --yes --quiet install {packages}".format(
                dry=dry, packages=packages
            )
        )

    def _snap(self, packages: list[tuple[str, Snap]]) -> None:
        try:
            for package, snap_mode in packages:
                mode = "--classic" if snap_mode == Snap.CLASSIC else ""
                self.run(f"sudo snap install {mode} {package}")
        except ValueError as e:
            notify(f"Snaps: {packages}")
            error(f"Snap package not defined correctly: {e}")

    def info(self, title: str, msg: str) -> None:
        child_title = self.title
        row = ("├─", title, msg)
        try:
            self.info_messages[child_title].append(row)
        except KeyError:
            self.info_messages[child_title] = [row]
