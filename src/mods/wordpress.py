# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist


class Wordpress(Bash):
    provides = ['wordpress']
    requires = ['php']
    title = 'Wordpress'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WpCli(Bash):
    """The wordpress cli application"""

    provides = ['wpcli']
    requires = ['wordpress']
    title = 'Wordpress CLI'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
