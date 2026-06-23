"""Deploy 2026-05-03 — Irene's six small join-page polish items.
Single-file deploy: register.html (template — no OPcache needed).

  $env:MGS_PASS='<prod password>'; python site/_deploy_2026_05_03.py
"""
from __future__ import annotations
import ftplib, os, ssl, sys, time, urllib.request

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
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


here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.dirname(here)
os.chdir(proj)

print("=" * 70)
print("Phase A — Upload register.html")
print("=" * 70)
f = connect()
try:
    stor(f, "site/upstream/_frameworks/main/impact/register.html",
         "_frameworks/main/impact/register.html")
finally:
    f.quit()

print("\n" + "=" * 70)
print("Phase B — Smoke checks")
print("=" * 70)
cb = int(time.time())
body = hit(f"https://{HOST}/join?nocache={cb}")

checks = [
    ("city label = 'City / Town / Island'",
     'City / Town / Island' in body),
    ("city placeholder updated",
     'Type your city, town or island' in body),
    ("region helper line present",
     'Select your region' in body and 'Athens, Thessaloniki, Rhodes, Crete' in body),
    ("rwcst grid CSS in place",
     'grid-template-columns: repeat(2, 1fr) !important' in body),
    ("step-1 form margin nudged to 2%",
     'margin: auto 2% auto auto' in body),
    ("legacy 5% margin gone",
     'margin: auto 5% auto auto' not in body),
    ("public Q&A 'For more, see' link removed",
     'For more, see the full <a href="/page?id=57"' not in body),
    ("footer text light (cream)",
     'body .footer {        color: #f4eddb' in body),
    ("footer link white",
     'body .footer .nav li a {        color: #ffffff' in body),
    ("home_city input still present",
     'name="home_city"' in body),
    ("title still set by PageTitles",
     '<title>Create Your Free Account | Meet Greek Singles</title>' in body),
]

print("\n  Smoke checks:")
all_ok = True
for label, ok in checks:
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] {label}")
    if not ok: all_ok = False

print("\n  =>", "ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
print("\nDONE")
