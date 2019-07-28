# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class Apache2(Bash):
    """Stand alone Apache

    With a default site at /var/www/html.
    """

    provides = ['apache2']
    requires = []
    title = 'Apache2'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['apache2']


class Nginx(Bash):
    provides = ['nginx']
    requires = []
    title = 'Nginx'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['nginx']

