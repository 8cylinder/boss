from bash import Bash
from dist import Dist


class Xdebug(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['xdebug']
        self.requires = ['php']
        self.apt_pkgs = ['php-xdebug']    # good enough?
