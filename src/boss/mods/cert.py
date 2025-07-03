import os

from ..engine import Snap
from ..dist import Dist
from ..errors import PlatformError
from typing import Any
from ..engine import Engine


class LetsEncryptCert(Engine):
    """Let's Encrypt certificate installation and configuration using snap.

    Documentation:

    - https://certbot.eff.org/instructions?ws=apache&os=snap
    - https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu
    """

    provides = ["letsencryptcert"]
    requires: list[str] = []
    required_args = ["servername"]
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
        self.mod.run("sudo ln -s /snap/bin/certbot /usr/bin/certbot")

        # command to get a certificate and have Certbot edit the apache configuration
        # automatically to serve it, turning on HTTPS access in a single step.
        self.mod.run("sudo certbot --apache")

        # to test
        self.mod.run("sudo certbot renew --dry-run")

    def cert_names(self, cert_basename: str) -> tuple[str, str, str, str]:
        """Maintain api compatibility with SelfCert."""
        return ("", "", "", "")


class SelfCert(Engine):
    """A self-signed cert good for 30 years

    Its name is the servername, SERVERNAME.crt and SERVERNAME.key.
    They are installed in /etc/ssl."""

    provides = ["selfcert"]
    requires: list[str] = []
    required_args = []
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
        self.mod.run(f"""sudo openssl \
            req \
            -new \
            -newkey rsa:4096 \
            -days 10950 \
            -nodes \
            -x509 \
            -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN={self.args.servername}" \
            -keyout {cert_basename}.key \
            -out {cert_basename}.crt &>/dev/null
        """)
        self.mod.run(
            "sudo cp {cert_basename}.crt /etc/ssl/certs/{cert_basename}.crt".format(
                cert_basename=cert_basename
            )
        )
        self.mod.run(
            "sudo cp {cert_basename}.key /etc/ssl/private/{cert_basename}.key".format(
                cert_basename=cert_basename
            )
        )
