"""Deploy 2026-05-03 part 2 — homepage video poster fix.
Single-file deploy: index.html (template — no OPcache needed).
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
print("Phase A — Upload index.html")
print("=" * 70)
f = connect()
try:
    stor(f, "site/upstream/_frameworks/main/impact/index.html",
         "_frameworks/main/impact/index.html")
finally:
    f.quit()

print("\n" + "=" * 70)
print("Phase B — Smoke checks")
print("=" * 70)
cb = int(time.time())
body = hit(f"https://{HOST}/?nocache={cb}")

checks = [
    ("hero <video> has preload='auto'",
     'preload="auto"' in body and 'class="mgs_hero_video"' in body),
    ("hero <video> no longer references shutterstock_1011591358 as poster",
     'poster="/_files/banner/shutterstock_1011591358.jpg"' not in body),
    ("hero CSS no longer uses chairs photo as background",
     "background-image: url('/_files/banner/shutterstock_1011591358.jpg')" not in body),
    ("hero CSS now has sea-blue gradient fallback",
     'linear-gradient(180deg' in body and '#5fa7c9' in body),
    ("hero video src still hero_couple_v2.mp4",
     '/_files/hero_couple_v2.mp4' in body),
    ("homepage title still set by PageTitles",
     '<title>Meet Greek Singles | Serious Dating for the Greek Diaspora</title>' in body),
    ("Our Promise section still rendering",
     'OUR PROMISE' in body or 'Our Promise' in body),
    ("CTA still 'Create Account'",
     'Create Account' in body),
]

print("\n  Smoke checks:")
all_ok = True
for label, ok in checks:
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] {label}")
    if not ok: all_ok = False

print("\n  =>", "ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
print("\nDONE")
