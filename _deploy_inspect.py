"""Quick inspection — upload _mgs_inspect_2026_05_01.php, run it, delete it.
Read-only. Safe to run anytime.

  $env:MGS_PASS='<prod password>'; python site/_deploy_inspect.py
"""
from __future__ import annotations
import ftplib, os, ssl, sys, urllib.request

HOST  = "meetgreeksingles.com"
USER  = "everett@meetgreeksingles.com"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD: sys.exit("ERROR: MGS_PASS env var not set")


class _ReusedSSL(ssl.SSLSocket):
    def unwrap(self): pass

class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            session = getattr(self.sock, "session", None)
            conn = self.context.wrap_socket(conn, server_hostname=self.host, session=session)
            conn.__class__ = _ReusedSSL
        return conn, size


def connect():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    f = FTP_TLS_Reuse(context=ctx)
    f.connect(HOST, 21, timeout=60)
    f.login(USER, PASSWORD); f.prot_p(); f.set_pasv(True)
    return f


def stor(f, local, remote):
    f.cwd("/")
    parts = remote.strip("/").split("/")
    name = parts.pop()
    for p in parts:
        try: f.cwd(p)
        except ftplib.error_perm: f.mkd(p); f.cwd(p)
    with open(local, "rb") as fp:
        f.storbinary(f"STOR {name}", fp)


def hit(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=120) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    proj = os.path.dirname(here)
    os.chdir(proj)

    print("Uploading inspection script...")
    f = connect()
    try:
        stor(f, "site/_mgs_inspect_2026_05_01.php", "_mgs_inspect_2026_05_01.php")
    finally:
        f.quit()

    print("\nRunning inspection...\n")
    body = hit(f"https://{HOST}/_mgs_inspect_2026_05_01.php?token={TOKEN}")
    print(body)

    print("\nDeleting inspection script...")
    f = connect()
    try:
        f.cwd("/"); f.delete("_mgs_inspect_2026_05_01.php")
    finally:
        f.quit()

    print("DONE")

if __name__ == "__main__":
    main()
