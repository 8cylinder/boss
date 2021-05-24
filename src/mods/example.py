# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class Example(Bash):
    """Short doc string here for the list command

    The full doc string is used for the help command.  This should list
    the command line args this module needs.

    Required class variables:
      provides
      requires
      title
    """

    # sel.provides is used for dependency management, each module can
    # provide more than one.  See lamp.py for an example.
    provides = ['example']

    # Any mods that this mod needs as a prerequisite.  These names are
    # matched to provides.
    requires = ['example2', 'example3']

    # A human readable name that is used in help and listing.
    title = 'Pretty name'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # List of apt packages to be installed via apt.
        self.apt_pkgs = ['package1', 'package2']

        # dist can be used to different things based on what version of
        # linux being used.
        if self.distro == (Dist.UBUNTU, Dist.V18_04):
            self.apt_pkgs = ['package1', 'package2', '18.04_package_only']

        # bash provides several methods
        self.sed('sed expression', 'file')
        self.apt(['list', 'of', 'packages'])
        self.curl('url', 'output-filename', capture=True)
        self.info('title', 'message')
        self.restart_apache()
        self.run('any valid bash command string', wrap=True, capture=False)
        # capture the result of the command
        result = self.run('any valid bash command string', wrap=True, capture=True)


    # Run before apt installs the apt_pkgs.
    def pre_install(self):
        pass

    # Run after apt installs the apt_pkgs.
    def post_install(self):
        pass
