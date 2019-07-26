# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist


class Example(Bash):
    """Short doc string here for the list command

    The full doc string is used for the help command.  This should list
    the command line args this module needs."""

    # sel.provides is used for depencency management, each module can
    # provide more than one.  See lamp.py for an example.
    self.provides = ['example']

    # Any mods that this mod needs as a prerequisite.  These names are
    # matched to self.provides.
    self.requires = ['example2', 'example3']

    # A human readable name that is used in help and listing.
    self.title = 'Pretty name'

    # List of apt packages to be installed via apt.
    self.apt_pkgs = ['package1', 'package2']

    # dist can be used to different things based on what version of
    # linux being used.
    if self.distro == (Dist.UBUNTU, Dist.V18_04):
        self.apt_pkgs = ['package1', 'package2', '18.04_package_only']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bash provides several methods
        self.sed('sed expression', 'file')
        self.apt(['list', 'of', 'packages'])
        self.curl('url', 'output-filename', capture=True)
        self.info('title', 'message')
        self.run('any valid bash command string')


    # Run before apt installs the apt_pkgs.
    def pre_install(self):
        pass

    # Run after apt installs the apt_pkgs.
    def post_install(self):
        pass

    # Run before apt uninstalls the apt_pkgs.
    def pre_uninstall(self):
        pass

    # Run after apt uninstalls the apt_pkgs.
    def post_uninstall(self):
        pass
