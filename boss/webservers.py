from bash import Bash
from dist import Dist


class Apache2(Bash):
    """Stand alone Apache

    With a default site at /var/www/html.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['apache2']
        self.apt_pkgs = ['apache2']

    def post_uninstall(self):
        self.run('if sudo test -d /etc/apache2; then sudo rm -rf /etc/apache2; fi')


class Nginx(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['nginx']
        self.apt_pkgs = ['nginx']

