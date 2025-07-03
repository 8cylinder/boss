from ..engine import Engine


class Wordpress(Engine):
    provides = ["wordpress"]
    requires = ["phpbin"]
    required_args = []
    title = "Wordpress"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WpCli(Engine):
    """The wordpress cli application"""

    provides = ["wpcli"]
    requires = ["wordpress"]
    title = "Wordpress CLI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
