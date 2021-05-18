# run-shell-command :: ../../build.bash

import os

from bash import Bash
from dist import Dist
from errors import *
from mods.cert import Cert
from collections import namedtuple


class VirtualHost(Bash):
    """Create virtualhost configuration files for http and https"""

    provides = ['virtualhost']
    requires = ['apache2', 'cert']
    title = 'Virtual host'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _http(self, servername, document_root):
        https_redirect = '# Redirect permanent "/" https://{servername}/'.format(
            servername=servername
        )
        vhost = '''
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
            </VirtualHost>'''.format(
            servername=servername,
            document_root=document_root,
            https_redirect=https_redirect
        )
        vhost = '\n'.join([i[12:] for i in vhost.split('\n')])
        return vhost

    def _https(self, servername, document_root, cert, key):
        vhost = '''

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
            </VirtualHost>'''.format(
            servername=servername,
            document_root=document_root,
            cert=cert,
            key=key
        )
        vhost = '\n'.join([i[12:] for i in vhost.split('\n')])
        return vhost

    def existing_cert(self, servername):
        # retrieve the existing cert for servername
        cert = Cert()
        _, _, crt, key = cert.cert_names(servername)
        return (crt, key)

    def new_cert(self, site_name):
        # create a new cert using this site's site_name
        CertArgs = namedtuple('CertArgs', 'servername dry_run')
        cert_args = CertArgs(site_name, self.args.dry_run)
        cert = Cert(dry_run=self.args.dry_run, args=cert_args)
        cert.pre_install()
        _, _, crt, key = cert.cert_names(site_name)
        return (crt, key)

    def create_doc_root(self, document_root):
        # make www-root owner of the doc root
        doc_root = os.path.join('/var/www', document_root)
        if not os.path.exists(doc_root):
            self.run('sudo mkdir {}'.format(doc_root))
        self.run('sudo chown www-data:www-data {}'.format(doc_root))

    def post_install(self):
        mods = ['ssl', 'rewrite', 'headers']
        for m in mods:
            self.run('sudo a2enmod {}'.format(m))

        self.run("find /etc/apache2/sites-available/ -type f -exec basename '{}' \; | xargs -n 1 sudo a2dissite")

        for site in self.args.site_name_and_root:
            site_name = site[0]
            full_document_root = os.path.join('/var/www', site[1])
            vhost_config = self._http(site_name, full_document_root)

            crt, key = self.existing_cert(self.args.servername)
            vhost_config += self._https(site_name, full_document_root, crt, key)

            conf_file = '/etc/apache2/sites-available/{}.conf'.format(site_name)

            self.append_to_file(conf_file, vhost_config, backup=False, append=False)

            if(site[2] == 'y'):
                document_root = site[1]
                self.create_doc_root(document_root)

            # enable this site
            self.run('sudo a2ensite {}'.format(site_name))
            self.info('Website', 'https://{}'.format(site_name))
            self.info(' └─ Apache conf', conf_file)

        self.restart_apache()
