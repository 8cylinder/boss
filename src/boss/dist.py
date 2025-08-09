"""Compare the current distro version with a known version."""

import enum

import distro

from boss.errors import VersionError


class UbuntuVersion(float, enum.Enum):
    """Ubuntu versions as a numeric Enum that behaves like a float.

    Provides a `current()` classmethod that detects the version from the
    running system using the `distro` package.

    Usage:
    ``` python
    from boss.dist import UbuntuVersion
    UbuntuVersion.current() == UbuntuVersion.V20_04
    UbuntuVersion.current() >= UbuntuVersion.V18_04
    ```
    """

    V14_04 = 14.04  # Trusty Tahr
    V16_04 = 16.04  # Xenial Xerus
    V18_04 = 18.04  # Bionic Beaver
    V20_04 = 20.04  # Focal Fossa
    V22_04 = 22.04  # Jammy Jellyfish
    V24_04 = 24.04  # Noble Numbat

    @classmethod
    def current(cls) -> "UbuntuVersion":
        """Return the current Ubuntu version."""
        detected_name = distro.id().lower()
        if detected_name != "ubuntu":
            err_msg = f"Not an Ubuntu system (detected: {detected_name or 'unknown'})"
            raise VersionError(err_msg)

        ver_str = distro.version()
        if not ver_str:
            err_msg = "Could not detect Ubuntu version"
            raise VersionError(err_msg)

        # Normalize to float for Enum lookup
        try:
            ver_float = float(ver_str)
        except (TypeError, ValueError) as exc:
            err_msg = f"Could not parse Ubuntu version from '{ver_str}'"
            raise VersionError(err_msg) from exc

        # Try direct match to one of the known enum values
        try:
            return cls(ver_float)
        except ValueError:
            # If the exact version isn't part of the enum (e.g., 24.10), raise.
            err_msg = (
                f"Ubuntu version {ver_float} is not represented in {cls.__name__}. "
                f"Known: {[m.value for m in cls]}"
            )
            raise VersionError(err_msg) from ValueError
