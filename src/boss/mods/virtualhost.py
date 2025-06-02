# run-shell-command :: ../../build.bash

import os

from .cert import SelfCert
from ..bash import Bash
from ..errors import *
from collections import namedtuple
from typing import Any
from pathlib import Path


class VirtualHost(Bash):
    """Create virtualhost configuration files for http and https"""

    provides = ["virtualhost"]
    requires = ["apache2", "cert"]
    # requires = ["apache2"]
    title = "Virtual host"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def _http(self, servername: str, document_root: str) -> str:
        https_redirect = '# Redirect permanent "/" https://{servername}/'.format(
            servername=servername
        )
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
        vhost = "\n".join([i[12:] for i in vhost.split("\n")])
        return vhost

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
        vhost = "\n".join([i[12:] for i in vhost.split("\n")])
        return vhost

    def existing_cert(self, servername: str) -> tuple[str, str]:
        # retrieve the existing cert for servername
        cert = SelfCert([], [])
        _, _, crt, key = cert.cert_names(servername)
        return (crt, key)

    def new_cert(self, site_name: str) -> tuple[str, str]:
        # create a new cert using this site's site_name
        CertArgs = namedtuple("CertArgs", "servername dry_run")
        cert_args = CertArgs(site_name, self.args.dry_run)
        cert = SelfCert(dry_run=self.args.dry_run, args=cert_args)
        cert.pre_install()
        _, _, crt, key = cert.cert_names(site_name)
        return (crt, key)

    def create_doc_root(self, document_root: str) -> None:
        # make www-root owner of the doc root
        doc_root = os.path.join("/var/www", document_root)
        if not os.path.exists(doc_root):
            self.run("sudo mkdir {}".format(doc_root))
        self.run("sudo chown www-data:www-data {}".format(doc_root))

    def post_install(self) -> None:
        mods = ["ssl", "rewrite", "headers"]
        for m in mods:
            self.run("sudo a2enmod {}".format(m))

        # disable all existing sites
        self.run(
            r"find /etc/apache2/sites-available/ -type f -exec basename '{}' \; | xargs -n 1 sudo a2dissite"
        )
        # then create the new sites and enable them
        for site in self.args.site_name_and_root:
            site_name = site[0]
            full_document_root = os.path.join("/var/www", site[1])
            vhost_config = self._http(site_name, full_document_root)

            crt, key = self.existing_cert(self.args.servername)
            vhost_config += self._https(site_name, full_document_root, crt, key)

            conf_file = "/etc/apache2/sites-available/{}.conf".format(site_name)

            print(vhost_config)
            self.write_new_file(conf_file, vhost_config)

            if site[2] == "y":
                document_root = site[1]
                self.create_doc_root(document_root)
                html_file = "/var/www" / Path(document_root) / "index.html"
                html_content = (
                    f"<h1>Site: {site_name}</h1>\n<p>Document root: {document_root}</p>"
                )
                self.write_new_file(html_file, html_content)

                info = "<?php phpinfo();"

            # enable this site

            self.run("sudo a2ensite {}".format(site_name))

            self.info("Website", "https://{}".format(site_name))
            public_ip = self.run("hostname -I", capture=True)
            self.info("Public IP", f"http://{public_ip}")
            self.info("Root", full_document_root)
            self.info("Apache conf", conf_file)

        self.restart_apache()
