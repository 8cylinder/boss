from bash import Bash
from dist import Dist


class Cert(Bash):
    """A self signed cert good for 30 years

    It's name is the servername, SERVERNAME.crt and SERVERNAME.key.
    They are install in /etc/ssl."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provides = ['cert']

    def cert_names(self, cert_basename):
        crt = '{}.crt'.format(cert_basename)
        key = '{}.key'.format(cert_basename)

        home_crt = os.path.join(os.path.expanduser('~'), crt)
        home_key = os.path.join(os.path.expanduser('~'), key)

        cert_loc = '/etc/ssl'
        real_crt = os.path.join(cert_loc, 'certs', crt)
        real_key = os.path.join(cert_loc, 'private', key)

        return home_crt, home_key, real_crt, real_key

    def pre_install(self):
        cert_basename = self.args.servername
        self.run('''
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
        '''.format(
            servername=self.args.servername,
            cert_basename=cert_basename
        ))
        self.run('sudo cp {cert_basename}.crt /etc/ssl/certs/{cert_basename}.crt'.format(
            cert_basename=cert_basename))
        self.run('sudo cp {cert_basename}.key /etc/ssl/private/{cert_basename}.key'.format(
            cert_basename=cert_basename))

    def post_uninstall(self):
        cert_basename = self.args.cert_basename
        home_crt, home_key, real_crt, real_key = self.cert_names(cert_basename)

        self.run('[[ -e {f} ]] && sudo rm {f}'.format(f=home_crt))
        self.run('[[ -e {f} ]] && sudo rm {f}'.format(f=home_key))
        self.run('sudo test -e {f} && sudo rm {f}'.format(f=real_crt))
        self.run('sudo test -e {f} && sudo rm {f}'.format(f=real_key))