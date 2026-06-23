"""Deploy 2026-05-03 part 3 — page_titles.class.php URI-based matching for
/login and /forget_password. PHP file change → needs OPcache reset.
"""
from __future__ import annotations
import ftplib, os, ssl, sys, urllib.request

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

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
    print(f"  STOR  {local}  ->  {remote}")
    f.cwd("/")
    parts = remote.strip("/").split("/")
    name = parts.pop()
    for p in parts:
        if not p: continue
        try: f.cwd(p)
        except ftplib.error_perm:
            try: f.mkd(p)
            except ftplib.error_perm: pass
            f.cwd(p)
    with open(local, "rb") as fp:
        f.storbinary(f"STOR {name}", fp)


def hit(url):
    print(f"  GET   {url}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=120) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"


def delete(name):
    f = connect()
    try:
        f.cwd("/")
        try: f.delete(name)
        except ftplib.error_perm as e: print(f"  DELE skip — {e}")
    finally:
        f.quit()


here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.dirname(here)
os.chdir(proj)

print("=== Upload page_titles.class.php ===")
f = connect()
try:
    stor(f, "site/upstream/_include/current/page_titles.class.php",
         "_include/current/page_titles.class.php")
    stor(f, "site/_mgs_opc.php", "_mgs_opc.php")
finally:
    f.quit()

print("\n=== Reset OPcache ===")
body = hit(f"https://{HOST}/_mgs_opc.php?token={TOKEN}")
print("  " + body.replace("\n", "\n  "))

print("\n=== Cleanup OPcache endpoint ===")
delete("_mgs_opc.php")

print("\nDONE")
