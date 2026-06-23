"""Re-run the (corrected) home_city installer to fix the E_NOTICE on /join2.
Also re-runs the inspection so we can verify the new blob shape on prod.
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

# Upload + run + delete the home_city installer (idempotent — UPDATEs the
# existing config row with the corrected blob shape).
print("=== Upload + run home_city installer ===")
f = connect()
try:
    stor(f, "site/_mgs_homecity_install.php", "_mgs_homecity_install.php")
finally:
    f.quit()

body = hit(f"https://{HOST}/_mgs_homecity_install.php?token={TOKEN}")
print("\n  Output:\n  " + body.replace("\n", "\n  "))

print("\n=== Cleanup ===")
delete("_mgs_homecity_install.php")

# Re-run the inspector to confirm the new blob shape on prod
print("\n=== Re-inspect home_city blob ===")
f = connect()
try:
    stor(f, "site/_mgs_inspect_uvars.php", "_mgs_inspect_uvars.php")
finally:
    f.quit()

body = hit(f"https://{HOST}/_mgs_inspect_uvars.php?token={TOKEN}")
# Pull just the home_city section
if "=== home_city" in body:
    section = body.split("=== home_city", 1)[1].split("=== ", 1)[0]
    print("\n  home_city blob now:")
    print("  === home_city" + section)
else:
    print("  home_city section not found in inspector output:")
    print(body[:1000])

delete("_mgs_inspect_uvars.php")

print("\nDONE")
