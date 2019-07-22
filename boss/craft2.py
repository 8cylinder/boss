from bash import Bash
from dist import Dist


class Craft2(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['craft2']
        self.requires = ['apache2', 'php', 'mysql']
        if self.distro > (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php-mbstring', 'php-imagick', 'php-mcrypt', 'php-curl',
                             'php-xml', 'php-zip', 'php-gd', 'php-mysql']
        elif self.distro == (Dist.UBUNTU, Dist.V14_04):
            self.apt_pkgs = ['php5', 'php5-imagick', 'php5-mcrypt', 'php5-curl',
                             'php5-gd', 'php5-mysql' , 'libapache2-mod-php5']
