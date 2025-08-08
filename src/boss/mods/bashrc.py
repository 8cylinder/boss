import os
from typing import Any, ClassVar

from boss.engine import Engine


class Bashrc(Engine):
    """A custom bashrc from GitHub and symlink boss to ~/bin/.

    1. Downloads a bashrc from GitHub and creates a bin dir in the $HOME dir.
    2. Backups the orginal .bashrc
    3. Symlinks the ~/bin/bashrc to ~/.bashrc
    4. Symlink /project/boss to ~/bin/boss
    """

    provides: ClassVar[list[str]] = ["bashrc"]
    requires: ClassVar[list[str]] = []
    required_args: ClassVar[list[str]] = []
    title = "Custom .bashrc"

    def __init__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Initialize the Bashrc module."""
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ["emacs-nox"]

    def install_bashrc(self) -> None:
        """Install a custom .bashrc setup on a user's system.

        This method sets up essential bash configuration files by downloading them
        from a specified source and placing them in the appropriate location within
        the user's home directory. If a previous .bashrc exists, it is backed up
        prior to making any changes, and symbolic links are created to avoid duplication.
        Additionally, permissions for specific scripts are adjusted to ensure they
        are executable.
        """
        self.mod.run("if [[ ! -d $HOME/bin ]]; then mkdir $HOME/bin; fi")
        gh_files = {
            "bashrc": "https://raw.githubusercontent.com/8cylinder/bin/master/bashrc",
            "bashrc_prompt.py": "https://raw.githubusercontent.com/8cylinder/bin/master/bashrc_prompt.py",
            "bashrc_prompt.themes": "https://raw.githubusercontent.com/8cylinder/bin/master/bashrc_prompt.themes",
        }
        for ghname, ghurl in gh_files.items():
            self.mod.curl(ghurl, "$HOME/bin/" + ghname)

        # if .bashrc is not a link, back it up
        self.mod.run(
            "if [[ ! -L $HOME/.bashrc ]]; then mv $HOME/.bashrc $HOME/.bashrc.original; fi",
        )
        # if .bashrc does not exist, make a link to bin/bashrc
        self.mod.run(
            "if [[ ! -e $HOME/.bashrc ]]; then ln -s $HOME/bin/bashrc $HOME/.bashrc; fi",
        )
        self.mod.run("chmod +x $HOME/bin/bashrc_prompt.py")

    def link_boss(self) -> None:
        """Create a symbolic link to the current script in the user's $HOME/bin directory.

        This method checks if the symbolic link already exists. If not, it creates one
        pointing to the script's current location. The link is created in the user's
        $HOME/bin directory, which is commonly used to store executable scripts.
        """
        source = __file__
        name = os.path.basename(source)
        dest = os.path.expanduser(os.path.join("$HOME/bin", name))
        self.mod.run(
            f"if [[ ! -h {dest} ]]; then ln -s {source} {dest}; fi",
        )

    def post_install(self) -> None:
        """Post-installation steps for the Bashrc module."""
        self.install_bashrc()
        self.link_boss()

    def uninstall(self) -> None:
        """Uninstall the Bashrc module."""
        self.mod.run("if [[ -d $HOME/bin ]]; then sudo rm -rf $HOME/bin; fi")
        # if .bashrc.original exists, restore it
        self.mod.run(
            "if [[ -e $HOME/.bashrc.original ]]; then mv .bashrc.original .bashrc; fi",
        )
