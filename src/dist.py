# run-shell-command :: ../build.bash

try:
    import distro
except ImportError:
    import platform


class Dist:
    """Test whether the current distro meets certain version requirments.

    d = Dist()
    d == Dist.UBUNTU
    d == (Dist.UBUNTU, Dist.V16_10)
    d > (Dist.UBUNTU, Dist.V16_10)
    """
    UBUNTU = 'Ubuntu'
    V14_04 = 14.04
    V16_04 = 16.04
    V18_04 = 18.04
    V20_04 = 20.04

    REDHAT = 'Redhat'
    CENTOS = 'CentOS'
    V4 = 4
    V5 = 5
    V6 = 6
    V7 = 7

    def __init__(self):
        try:
            self.name = distro.name()
            self.version = distro.version()
        except NameError:
            self.name = platform.dist()[0]
            self.version = platform.dist()[1]

    def __str__(self):
        return '{name} {version}'.format(**self.__dict__)

    def __eq__(self, other):
        """Comparison can be done with the distro name or the distro name and version.

        d = Distro()
        d == Distro.UBUNTU
        d == (Distro.UBUNTU, Distro.V16_04)"""
        if len(other) == 2:
            return self.name == other[0] and float(self.version) == float(other[1])
        else:
            return self.name == other

    def __ne__(self, other):
        return self.name != other[0] or float(self.version) != float(other[1])

    def __lt__(self, other):
        return self.name == other[0] and float(self.version) < float(other[1])

    def __le__(self, other):
        return self.name == other[0] and float(self.version) <= float(other[1])

    def __gt__(self, other):
        return self.name == other[0] and float(self.version) > float(other[1])

    def __ge__(self, other):
        return self.name == other[0] and float(self.version) >= float(other[1])
