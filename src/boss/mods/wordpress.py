from ..bash import ModBase


class Wordpress(ModBase):
    provides = ["wordpress"]
    requires = ["phpbin"]
    required_args = []
    title = "Wordpress"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WpCli(ModBase):
    """The wordpress cli application"""

    provides = ["wpcli"]
    requires = ["wordpress"]
    title = "Wordpress CLI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
