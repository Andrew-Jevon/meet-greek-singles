"""Upload + run + delete the 2026-05-09 verification probe."""
from __future__ import annotations
import os, ftplib, ssl, sys, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("PROD_PASS")
if not PASSWORD: sys.exit("ERROR: PROD_PASS env var not set")

SITE  = Path(__file__).parent
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
BASE  = "https://meetgreeksingles.com"

class _R(ssl.SSLSocket):
    def unwrap(self): pass
class F(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        c, s = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            sess = getattr(self.sock, "session", None)
            c = self.context.wrap_socket(c, server_hostname=self.host, session=sess); c.__class__=_R
        return c, s

def ftps():
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    f = F(HOST, USER, PASSWORD, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True); return f

ftp = ftps()
with open(SITE / "_mgs_verify_2026_05_09.php", "rb") as fh:
    ftp.storbinary("STOR _mgs_verify_2026_05_09.php", fh)
print("uploaded probe")

req = urllib.request.Request(f"{BASE}/_mgs_verify_2026_05_09.php?token={TOKEN}",
                             headers={"User-Agent":"verify/1.0"})
r = urllib.request.urlopen(req, timeout=45)
print(f"HTTP {r.status}")
print(r.read().decode("utf-8","replace"))

try: ftp.delete("_mgs_verify_2026_05_09.php"); print("\ndeleted probe")
except ftplib.error_perm as e: print(f"delete failed: {e}")
ftp.quit()
