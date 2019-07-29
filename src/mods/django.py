# run-shell-command :: ../../build.bash

from bash import Bash
from dist import Dist
from errors import *


class Django(Bash):
    """


    """
    provides = ['django']
    requires = ['apache', 'mysql']
    title = 'Django'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apt_pkgs = ['python3-pip', 'libapache2-mod-wsgi-py3', 'python3-mysqldb', 'python3-virtualenv', 'python3-venv']

    def pre_install(self):

        ['cd $HOME/ && mkdir django',
         'python3 -m venv djangoenv',     # create a virtualenv using the sytem's python3
         'source djangoenv/bin/activate', # activate virtualenv
         'pip install django',            # use the pip in the virtualenv
         '',
        ]
        self.run()


class Wagtail(Bash):
    provides = ['wagtail']
    requires = ['django']
    title = 'Wagtail'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
