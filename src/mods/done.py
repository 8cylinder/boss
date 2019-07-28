# run-shell-command :: ../../build.bash

import sys

from bash import Bash
from dist import Dist

class Done(Bash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['done']

    def pre_install(self):
        # https://github.com/pwaller/pyfiglet/blob/master/doc/figfont.txt
        if self.args.generate_script:
            sys.stdout.write('set +x\n')
        self.run('figlet -k -w89 {}'.format(self.args.servername))
        # for title, msg in info:
        #     if self.args.generate_script:
        #         sys.stdout.write("echo '{:20} {}'\n".format(title + ':', msg))
        #     else:
        #         click.echo('{:30} {}'.format(
        #             click.style(title, fg='white'),
        #             click.style(msg, fg='blue')))
        #     sys.stdout.flush()

        sys.stdout.write('\n')
