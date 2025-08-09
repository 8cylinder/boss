"""Certificate management modules for boss: Let's Encrypt and self-signed certs."""

from pathlib import Path
from typing import ClassVar

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine, Snap
from boss.errors import PlatformError


class LetsEncryptCert(Engine):
    """Let's Encrypt certificate installation and configuration using snap."""

    provides: ClassVar[list[str]] = ["letsencryptcert"]
    requires: ClassVar[list[str]] = []
    required_args: ClassVar[list[str]] = ["servername"]
    title = "Let's Encrypt cert"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize LetsEncryptCert."""
        super().__init__(args=args, dry_run=dry_run, ubuntu_version=ubuntu_version)
        if self.ubuntu == UbuntuVersion.V24_04:
            self.snap_pkgs = [
                ("certbot", Snap.CLASSIC),
            ]
        else:
            msg = "Certbot install for non Ubuntu 24.04 not implemented"
            raise PlatformError(msg)

    def post_install(self) -> None:
        """Post-installation steps for Let's Encrypt cert."""
        self.mod.run("sudo ln -s /snap/bin/certbot /usr/bin/certbot")
        self.mod.run("sudo certbot --apache")
        self.mod.run("sudo certbot renew --dry-run")

    def cert_names(self, cert_basename: str) -> tuple[str, str, str, str]:
        """Maintain API compatibility with SelfCert. Argument is unused."""
        _ = cert_basename
        return ("", "", "", "")


class SelfCert(Engine):
    """A self-signed cert good for 30 years.

    Its name is the servername, SERVERNAME.crt and SERVERNAME.key.
    They are installed in /etc/ssl.
    """

    provides: ClassVar[list[str]] = ["selfcert"]
    requires: ClassVar[list[str]] = []
    required_args: ClassVar[list[str]] = []
    title = "Self signed cert"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize SelfCert."""
        super().__init__(args=args, dry_run=dry_run, ubuntu_version=ubuntu_version)

    def cert_names(self, cert_basename: str) -> tuple[str, str, str, str]:
        """Return home and system paths for cert and key files."""
        crt = f"{cert_basename}.crt"
        key = f"{cert_basename}.key"
        home = Path.home()
        home_crt = str(home / crt)
        home_key = str(home / key)
        cert_loc = Path("/etc/ssl")
        real_crt = str(cert_loc / "certs" / crt)
        real_key = str(cert_loc / "private" / key)
        self.info("cert", real_crt)
        self.info("key", real_key)
        return home_crt, home_key, real_crt, real_key

    def pre_install(self) -> None:
        """Generate and install a self-signed certificate."""
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
            f"sudo cp {cert_basename}.crt /etc/ssl/certs/{cert_basename}.crt",
        )
        self.mod.run(
            f"sudo cp {cert_basename}.key /etc/ssl/private/{cert_basename}.key",
        )
