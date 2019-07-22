from bash import Bash
from dist import Dist


class example(Bash):
    """Short doc string for the list command

    As much details about this module for the help command."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['example']   # why is this required?
        self.requires = ['']  # any deps this mod needs.
