"""Deploy 2026-05-04 — onboarding refresh.
Runs the installer, then re-inspects user_var rows so we can verify shape.
"""
from __future__ import annotations
import ftplib, os, ssl, sys, urllib.request

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
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


def connect():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    f = F(context=ctx)
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
        with urllib.request.urlopen(url, context=ctx, timeout=180) as r:
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

print("=== Upload + run onboarding refresh installer ===")
f = connect()
try:
    stor(f, "site/_mgs_onboarding_refresh.php", "_mgs_onboarding_refresh.php")
finally:
    f.quit()

body = hit(f"https://{HOST}/_mgs_onboarding_refresh.php?token={TOKEN}")
print("\n  Output:\n  " + body.replace("\n", "\n  "))

print("\n=== Cleanup ===")
delete("_mgs_onboarding_refresh.php")

print("\n=== Re-inspect user_var rows to confirm shape ===")
f = connect()
try:
    stor(f, "site/_mgs_inspect_uvars.php", "_mgs_inspect_uvars.php")
finally:
    f.quit()

body = hit(f"https://{HOST}/_mgs_inspect_uvars.php?token={TOKEN}")

want = ['looking_for', 'culture_importance', 'greek_meaning', 'relocation_openness',
        'connection_greece', 'relationship_intent', 'greek_importance', 'greek_future_plans']
for fld in want:
    if f"=== {fld} " in body:
        section = body.split(f"=== {fld} ", 1)[1].split("=== ", 1)[0]
        print(f"  === {fld} {section.rstrip()}")
    else:
        print(f"  ! {fld} not found in inspect output")

delete("_mgs_inspect_uvars.php")
print("\nDONE")
