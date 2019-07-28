# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist


class Wordpress(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['wordpress']


class WpCli(Bash):
    """The wordpress cli application"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['wpcli']
