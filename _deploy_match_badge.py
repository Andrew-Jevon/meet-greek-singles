"""Deploy the compatibility badge templates (HTML only, no opcache needed)."""
from __future__ import annotations
import ftplib, os, ssl, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD: sys.exit("ERROR: MGS_PASS env var not set")


class _R(ssl.SSLSocket):
    def unwrap(self): pass

class F(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        c, s = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            ses = getattr(self.sock, "session", None)
            c = self.context.wrap_socket(c, server_hostname=self.host, session=ses)
            c.__class__ = _R
        return c, s

ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
f = F(context=ctx); f.connect(HOST, 21, timeout=60)
f.login(USER, PASSWORD); f.prot_p(); f.set_pasv(True); f.cwd("/")

here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.dirname(here)
os.chdir(proj)

files = [
    ("site/upstream/_frameworks/main/impact/_list_users_info.html",
     "_frameworks/main/impact/_list_users_info.html"),
    ("site/upstream/_frameworks/main/impact/_list_users_info_items.html",
     "_frameworks/main/impact/_list_users_info_items.html"),
]
for local, remote in files:
    print(f"  STOR  {local}  ->  {remote}")
    f.cwd("/")
    parts = remote.strip("/").split("/")
    name = parts.pop()
    for p in parts:
        try: f.cwd(p)
        except ftplib.error_perm: f.mkd(p); f.cwd(p)
    with open(local, "rb") as fp:
        f.storbinary(f"STOR {name}", fp)
f.quit()
print("\nDONE")
