"""Deploy 2026-05-05 — Irene's bug-report round + new logo:
  - login_form.js : redirect to /index.php instead of /<username> (router.php
    not in prelaunch allowlist)
  - register.html : force Greece+Attica default; reduce field heights;
    move Welcome card right
  - login.html    : show Remember me checkbox + label
  - _header.html  : CSS swap for new logo
  - main_impact.svg : new logo file from Irene's Final files 2/MAIN LOGO-01.svg

Templates only — no opcache reset.
"""
from __future__ import annotations
import ftplib, os, ssl, sys, urllib.request

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

def connect():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    f = F(context=ctx); f.connect(HOST, 21, timeout=60)
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

here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.dirname(here)
os.chdir(proj)

files = [
    ("site/upstream/_frameworks/main/impact/js/login_form.js",
     "_frameworks/main/impact/js/login_form.js"),
    ("site/upstream/_frameworks/main/impact/register.html",
     "_frameworks/main/impact/register.html"),
    ("site/upstream/_frameworks/main/impact/login.html",
     "_frameworks/main/impact/login.html"),
    ("site/upstream/_frameworks/main/impact/_header.html",
     "_frameworks/main/impact/_header.html"),
    ("Final files 2/MAIN LOGO-01.svg",
     "_files/logo/main_impact.svg"),
]

print("=== Upload all files ===")
f = connect()
try:
    for local, remote in files:
        stor(f, local, remote)
finally:
    f.quit()

print("\nDONE")
