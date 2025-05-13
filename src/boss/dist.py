# run-shell-command :: ../build.bash

import distro

class Dist:
    """Test whether the current distro meets certain version requirments.

    d = Dist()
    d == Dist.UBUNTU
    d == (Dist.UBUNTU, Dist.V16_10)
    d > (Dist.UBUNTU, Dist.V16_10)
    """
    UBUNTU = 'Ubuntu'
    V14_04 = 14.04  # Trusty Tahr
    V16_04 = 16.04  # Xenial Xerus
    V18_04 = 18.04  # Bionic Beaver
    V20_04 = 20.04  # Focal Fossa
    V22_04 = 22.04  # Jammy Jellyfish
    V24_04 = 24.04  # Oracular Oriole

    def __init__(self, version:float|None=None) -> None:
        self.name = distro.name()
        version = 24.04
        if version:
            self.version = str(version)
        else:
            self.version = distro.version()
        print(distro.version())

    def __str__(self) -> str:
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
