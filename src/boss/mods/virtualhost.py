"""Create virtual host configuration files for HTTP and HTTPS.

This module contains the `VirtualHost` class, and is responsible for managing
Apache virtual host configurations. It supports both HTTP and HTTPS setups,
provides SSL integration, and can handle operations such as enabling
necessary Apache modules, creating document roots, and managing certificates.
"""

from pathlib import Path
from typing import ClassVar, NamedTuple

from boss.dist import UbuntuVersion
from boss.engine import Args, Engine
from boss.mods.cert import LetsEncryptCert, SelfCert


class CertArgs(NamedTuple):
    """Arguments for certificate management."""

    servername: str
    dry_run: bool = False


class VirtualHost(Engine):
    """Create virtualhost configuration files for http and https."""

    provides: ClassVar = ["virtualhost"]
    requires: ClassVar = ["apache2"]
    required_args: ClassVar = ["site_name_and_root", "servername"]
    title = "Virtual host"

    def __init__(
        self,
        args: Args,
        ubuntu_version: UbuntuVersion,
        dry_run: bool = False,
    ) -> None:
        """Initialize the VirtualHost engine."""
        super().__init__(args=args, ubuntu_version=ubuntu_version, dry_run=dry_run)

    def _http(self, servername: str, document_root: str) -> str:
        https_redirect = f'# Redirect permanent "/" https://{servername}/'
        vhost = f"""
            # HTTP
            <VirtualHost *:80>
                ServerAdmin webmaster@localhost

                ServerName {servername}
                {https_redirect}
                DocumentRoot {document_root}
                <Directory "{document_root}">
                    AllowOverride All
                    Header Set Access-Control-Allow-Origin "*"
                </Directory>

                # ErrorLog ${{APACHE_LOG_DIR}}/error.log
                # CustomLog ${{APACHE_LOG_DIR}}/access.log combined
            </VirtualHost>"""
        return "\n".join([i[12:] for i in vhost.split("\n")])

    def _https(self, servername: str, document_root: str, cert: str, key: str) -> str:
        vhost = f"""

            # HTTPS
            <VirtualHost *:443>
                ServerAdmin webmaster@localhost

                ServerName {servername}
                # ServerAlias www.{servername}

                DocumentRoot {document_root}
                <Directory "{document_root}">
                    AllowOverride All
                    Header Set Access-Control-Allow-Origin "*"
                </Directory>

                # ErrorLog ${{APACHE_LOG_DIR}}/error.log
                # CustomLog ${{APACHE_LOG_DIR}}/access.log combined

                SSLEngine on
                SSLOptions +StrictRequire
                SSLCertificateFile {cert}
                SSLCertificateKeyFile {key}
            </VirtualHost>"""
        return "\n".join([i[12:] for i in vhost.split("\n")])

    def existing_cert(self, servername: str) -> tuple[str, str]:
        """Retrieve the existing certificate for the given server name."""
        # retrieve the existing cert for servername
        if SelfCert in self.args.wanted:
            cert = SelfCert(
                dry_run=self.args.dry_run,
                args=self.args,
                ubuntu_version=self.ubuntu,
            )
            _, _, crt, key = cert.cert_names(servername)
        elif LetsEncryptCert in self.args.wanted:
            cert = LetsEncryptCert([], [])
            _, _, crt, key = cert.cert_names(servername)
        else:
            crt = key = ""
        return crt, key

    def new_cert(self, site_name: str) -> tuple[str, str]:
        """Create a new self-signed certificate for the given site name."""
        # create a new cert using this site's site_name
        # CertArgs = namedtuple("CertArgs", "servername dry_run")
        cert_args = CertArgs(site_name, self.args.dry_run)
        cert = SelfCert(
            dry_run=self.args.dry_run,
            args=cert_args,
            ubuntu_version=self.ubuntu,
        )
        cert.pre_install()
        _, _, crt, key = cert.cert_names(site_name)
        return (crt, key)

    def create_doc_root(self, document_root: str) -> None:
        """Create the document root directory and set permissions."""
        # make www-root owner of the doc root
        doc_root = Path("/var/www") / document_root
        if not doc_root.exists():
            self.mod.run(f'sudo mkdir "{doc_root}"')
        self.mod.run(f'sudo chown www-data:www-data "{doc_root}"')
        self.mod.run(f'sudo chmod g+rw "{doc_root}"')

    def post_install(self) -> None:
        """Post-installation steps for the VirtualHost engine."""
        mods = ["ssl", "rewrite", "headers"]
        for m in mods:
            self.mod.run(f"sudo a2enmod {m}")

        # then create the new sites and enable them
        for site in self.args.site_name_and_root:
            site_name = site[0]
            full_document_root = Path("/var/www") / site[1]
            vhost_config = self._http(site_name, str(full_document_root))

            crt, key = self.existing_cert(self.args.servername)
            if crt:
                vhost_config += self._https(
                    site_name,
                    str(full_document_root),
                    crt,
                    key,
                )

            conf_file = f"/etc/apache2/sites-available/{site_name}.conf"
            self.mod.write_new_file(conf_file, vhost_config)

            if site[2] == "y":
                document_root = site[1]
                self.create_doc_root(document_root)
                html_file = "/var/www" / Path(document_root) / "index.html"
                html_content = (
                    f"<h1>Site: {site_name}</h1>\n<p>Document root: {document_root}</p>"
                )
                self.mod.write_new_file(html_file, html_content)

            # enable this site
            self.mod.run(f"sudo a2ensite {site_name}")

            self.info("Website", f"https://{site_name}")
            public_ip = self.mod.run("hostname -I", capture=True)
            self.info("Public IP", f"http://{public_ip}")
            self.info("Root", str(full_document_root))
            self.info("Apache conf", conf_file)

        self.mod.restart_apache()
