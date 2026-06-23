"""
2026-05-13 — Read-only audit of the production user table before a planned
bulk delete of test accounts. Uploads _mgs_audit_users_2026_05_13.php,
runs it, prints output, deletes the script.

Reads PROD_PASS env var.
"""
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
SCRIPT = "_mgs_audit_users_2026_05_13.php"

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

def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent":"audit-2026-05-13/1.0"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8", "replace") if hasattr(e, "read") else "")

def main():
    print(f"[1/4] FTPS connect to PRODUCTION")
    ftp = ftps()
    print(f"      pwd: {ftp.pwd()}")

    print(f"[2/4] Upload {SCRIPT}")
    with open(SITE / SCRIPT, "rb") as fh:
        ftp.storbinary(f"STOR {SCRIPT}", fh)

    print(f"[3/4] Run audit")
    status, out = http_get(f"{BASE}/{SCRIPT}?token={TOKEN}")
    print(f"      runner HTTP {status}")
    print("---- output ----")
    print(out)
    print("---- end output ----")

    print(f"[4/4] Delete one-shot script")
    try:
        ftp.delete(SCRIPT); print(f"      deleted {SCRIPT}")
    except ftplib.error_perm as e:
        print(f"      ! delete failed: {e}")
    ftp.quit()

if __name__ == "__main__":
    main()
