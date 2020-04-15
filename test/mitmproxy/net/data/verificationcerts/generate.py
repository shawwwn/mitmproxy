"""
Generate SSL test certificates.
"""
import subprocess
import shlex
import os
import shutil
import textwrap

ROOT_CA = "trusted-root"
SUBJECT = "example.mitmproxy.org"


def do(args):
    print("> %s" % args)
    args = shlex.split(args)
    output = subprocess.check_output(args)
    return output


def genrsa(cert: str):
    do(f"openssl genrsa -out {cert}.key 2048")


def sign(cert: str, subject: str):
    with open(f"openssl-{cert}.conf", "w") as f:
        f.write(textwrap.dedent(f"""
        authorityKeyIdentifier=keyid,issuer
        basicConstraints=CA:FALSE
        keyUsage = digitalSignature, keyEncipherment
        subjectAltName = {subject}
        """))
    do(f"openssl x509 -req -in {cert}.csr "
       f"-CA {ROOT_CA}.crt "
       f"-CAkey {ROOT_CA}.key "
       f"-CAcreateserial "
       f"-days 7300 "
       f"-sha256 "
       f"-extfile \"openssl-{cert}.conf\" "
       f"-out {cert}.crt"
       )
    os.remove(f"openssl-{cert}.conf")


def mkcert(cert, subject):
    genrsa(cert)
    do(f"openssl req -new -nodes -batch "
       f"-key {cert}.key "
       f"-addext \"subjectAltName = {subject}\" "
       f"-out {cert}.csr"
       )
    sign(cert, subject)
    os.remove(f"{cert}.csr")


# create trusted root CA
genrsa("trusted-root")
do("openssl req -x509 -new -nodes -batch "
   "-key trusted-root.key "
   "-days 7300 "
   "-out trusted-root.crt"
   )
h = do("openssl x509 -hash -noout -in trusted-root.crt").decode("ascii").strip()
shutil.copyfile("trusted-root.crt", "{}.0".format(h))

# create trusted leaf cert.
mkcert("trusted-leaf", f'DNS:{SUBJECT}')

# create self-signed cert
genrsa("self-signed")
do("openssl req -x509 -new -nodes -batch "
   "-key self-signed.key "
   f'-addext "subjectAltName = DNS:{SUBJECT}" '
   "-days 7300 "
   "-out self-signed.crt"
   )