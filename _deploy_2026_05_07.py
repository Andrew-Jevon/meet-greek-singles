"""Deploy 2026-05-07 — Irene's logo placement round.

Per her message:
  - Navbar/every page: full horizontal logo "Meet Greek + WHERE GREEK HEARTS MEET"
    in the line-art design from her mockup, transparent, larger, more padded
  - Login + onboarding + favicon: heart-icon-only mark
  - Share preview: wider banner with full logo + tagline

The design she mocked up isn't in any of the SVG/PNG files she sent (those
all show the older "Meet Greek SINGLES" lockup with gold swoosh). The
mockup PNG IS the design she wants — so we cropped the logo and heart icon
from her mockup file and built a 1200x630 share banner around the cropped
logo on cream brand-bg.

Files (image assets):
  mgs_navbar_logo.png  (960x250 transparent, line-art design from mockup)
    -> /_files/logo/main_impact.png      (overwrites Chameleon's default)
  mgs_heart_icon.png   (512x512 transparent, line-art heart icon)
    -> /_files/logo/heart_icon.png       (login + onboarding + apple-touch)
  mgs_heart_icon_32    (32x32 transparent)
    -> /_files/logo/heart_icon_32.png    (browser favicon)
  mgs_social_share.jpg (1200x630, logo on cream)
    -> /_files/banner/social_share.jpg   (og:image + twitter:image)

Templates:
  _header.html      navbar size 44->56px / 180->260px wide; new favicon links;
                    og:image swapped to social_share.jpg; old SVG content-swap removed
  login.html        brand img: /favicon.ico -> /_files/logo/heart_icon.png
  register.html     same swap (2 places)
  onboarding.html   added heart icon above "Welcome -- let's set up..." intro
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

def hit(url):
    print(f"  GET   {url}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=60) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"

def delete(name):
    f = connect()
    try:
        f.cwd("/")
        try: f.delete(name)
        except ftplib.error_perm as e: print(f"  DELE skip — {e}")
    finally: f.quit()


here = os.path.dirname(os.path.abspath(__file__))
proj = os.path.dirname(here)
os.chdir(proj)

# Image assets
images = [
    ("Final files 2/New folder/mgs_navbar_logo.png",  "_files/logo/main_impact.png"),
    ("Final files 2/New folder/mgs_heart_icon_512.png","_files/logo/heart_icon.png"),
    ("Final files 2/New folder/mgs_heart_icon_32.png", "_files/logo/heart_icon_32.png"),
    ("Final files 2/New folder/mgs_social_share.jpg",  "_files/banner/social_share.jpg"),
]

templates = [
    ("site/upstream/_frameworks/main/impact/_header.html",
     "_frameworks/main/impact/_header.html"),
    ("site/upstream/_frameworks/main/impact/login.html",
     "_frameworks/main/impact/login.html"),
    ("site/upstream/_frameworks/main/impact/register.html",
     "_frameworks/main/impact/register.html"),
    ("site/upstream/_frameworks/main/impact/onboarding.html",
     "_frameworks/main/impact/onboarding.html"),
]

print("=== Phase A — upload image assets ===")
f = connect()
try:
    for local, remote in images:
        stor(f, local, remote)
finally:
    f.quit()

print("\n=== Phase B — upload templates ===")
f = connect()
try:
    for local, remote in templates:
        stor(f, local, remote)
finally:
    f.quit()

# Templates only (no PHP changes); no opcache reset needed
# But we might want to delete the old main_impact.svg we uploaded earlier
print("\n=== Phase C — clean up obsolete main_impact.svg (no longer referenced) ===")
delete("_files/logo/main_impact.svg")

print("\nDONE")
