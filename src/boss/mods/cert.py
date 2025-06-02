# run-shell-command :: ../../build.bash

import os

from ..bash import Bash, Snap
from ..dist import Dist
from ..errors import PlatformError
from typing import Any


class LetsEncryptCert(Bash):
    """Let's Encrypt certificate installation and configuration using snap.

    Documentation:
    - https://certbot.eff.org/instructions?ws=apache&os=snap
    - https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu
    """

    provides = ["cert"]
    requires: list[str] = []
    title = "Let's Encrypt cert"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.distro == (Dist.UBUNTU, Dist.V24_04):
            self.snap_pkgs = [
                ("certbot", Snap.CLASSIC),
            ]
        else:
            raise PlatformError("Certbot install for non Ubuntu 20.04 not implemented")

    def post_install(self) -> None:
        self.run("sudo ln -s /snap/bin/certbot /usr/bin/certbot")

        # command to get a certificate and have Certbot edit the apache configuration
        # automatically to serve it, turning on HTTPS access in a single step.
        self.run("sudo certbot --apache")

        # to test
        self.run("sudo certbot renew --dry-run")


class SelfCert(Bash):
    """A self-signed cert good for 30 years

    Its name is the servername, SERVERNAME.crt and SERVERNAME.key.
    They are installed in /etc/ssl."""

    provides = ["cert"]
    requires: list[str] = []
    title = "Self signed cert"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def cert_names(self, cert_basename: str) -> tuple[str, str, str, str]:
        crt = "{}.crt".format(cert_basename)
        key = "{}.key".format(cert_basename)

        home_crt = os.path.join(os.path.expanduser("~"), crt)
        home_key = os.path.join(os.path.expanduser("~"), key)

        cert_loc = "/etc/ssl"
        real_crt = os.path.join(cert_loc, "certs", crt)
        real_key = os.path.join(cert_loc, "private", key)

        self.info("cert", f"{real_crt}")
        self.info("key", f"{real_key}")

        return home_crt, home_key, real_crt, real_key

    def pre_install(self) -> None:
        cert_basename = self.args.servername
        self.run(
            """
            sudo openssl \
                 req \
                 -new \
                 -newkey rsa:4096 \
                 -days 10950 \
                 -nodes \
                 -x509 \
                 -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN={servername}" \
                 -keyout {cert_basename}.key \
                 -out {cert_basename}.crt &>/dev/null
        """.format(servername=self.args.servername, cert_basename=cert_basename)
        )
        self.run(
            "sudo cp {cert_basename}.crt /etc/ssl/certs/{cert_basename}.crt".format(
                cert_basename=cert_basename
            )
        )
        self.run(
            "sudo cp {cert_basename}.key /etc/ssl/private/{cert_basename}.key".format(
                cert_basename=cert_basename
            )
        )
