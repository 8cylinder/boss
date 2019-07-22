from bash import Bash
from dist import Dist


class Php(Bash):
    """Base PHP, nothing else."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['php']
        self.requires = ['apache2']
        if self.distro > (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php']
        elif self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php5']
