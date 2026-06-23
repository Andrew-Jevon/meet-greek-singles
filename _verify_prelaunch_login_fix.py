"""Verify prelaunch login fix — POST to /ajax.php?action=login WITHOUT setting
the platform_mode_off bypass. Should now return 'logged' instead of the
'prelaunch_mode' 403.
"""
from __future__ import annotations
import os, ssl, sys, urllib.request, urllib.parse, http.cookiejar
import ftplib

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
TEST_USER = "acidrocker"
TEST_PASS = "mgsTest!2026"
TEST_UID = 2
ORIG_HASH = "$2y$10$5nSGJgRO6rZzyDUS0fYZ0.NffVCM8MVHtNETGQ3a06Hv14q44Z2Ve"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD: sys.exit("ERROR: MGS_PASS env var not set")


# --- urllib with cookie jar ---
ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(cj),
)
opener.addheaders = [('User-Agent', 'MGS-Probe/1.0')]


def get(url):
    try:
        with opener.open(urllib.request.Request(url), timeout=60) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")

def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "X-Requested-With": "XMLHttpRequest"}
    try:
        with opener.open(urllib.request.Request(url, data=body, headers=headers), timeout=60) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


# --- FTP helpers (just for password reset) ---
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

def ftp_connect():
    c = ssl.create_default_context()
    c.check_hostname = False; c.verify_mode = ssl.CERT_NONE
    f = F(context=c); f.connect(HOST, 21, timeout=60)
    f.login("everett@meetgreeksingles.com", PASSWORD); f.prot_p(); f.set_pasv(True)
    return f

def ftp_stor(local, remote):
    f = ftp_connect()
    try:
        f.cwd("/")
        with open(local, "rb") as fp: f.storbinary(f"STOR {remote}", fp)
    finally: f.quit()

def ftp_delete(name):
    f = ftp_connect()
    try:
        f.cwd("/")
        try: f.delete(name)
        except ftplib.error_perm: pass
    finally: f.quit()


print("=" * 70)
print("Setup — re-set test user password (in case prior probe restored it)")
print("=" * 70)
prep = """<?php
$T='%(t)s'; if(($_GET['token']??'')!==$T){http_response_code(403);exit;}
$g=array(); require __DIR__.'/_include/config/db.php';
$d=new mysqli($g['db']['host'],$g['db']['user'],$g['db']['password'],$g['db']['db']);
$h=password_hash('%(p)s',PASSWORD_BCRYPT);
$d->query("UPDATE `user` SET password='".$d->real_escape_string($h)."' WHERE user_id=%(uid)d");
header('Content-Type: text/plain'); echo "test pw re-set\\n";
""" % {"t": TOKEN, "p": TEST_PASS, "uid": TEST_UID}
with open("./_prep_pw.php", "w") as f: f.write(prep)
ftp_stor("./_prep_pw.php", "_prep_pw.php")
print(get(f"https://{HOST}/_prep_pw.php?token={TOKEN}")[1])
ftp_delete("_prep_pw.php")
os.remove("./_prep_pw.php")


print("\n" + "=" * 70)
print("TEST — POST /ajax.php?action=login WITHOUT prelaunch bypass")
print("=" * 70)
print("(if the fix works, this should NOT return prelaunch_mode 403)")

# Bootstrap a clean session by hitting the homepage
get(f"https://{HOST}/")
print(f"  cookies: {[c.name for c in cj]}")

login_data = {
    "user":     TEST_USER,
    "password": TEST_PASS,
    "cmd":      "login",
    "ajax":     "1",
}
code, body = post(f"https://{HOST}/ajax.php?action=login", login_data)
print(f"\n  POST /ajax.php?action=login → HTTP {code}")
print(f"  body: {body[:300]}")

# Verify result
ok = (code == 200 and "logged" in body and "prelaunch_mode" not in body)
print(f"\n  RESULT: {'OK — prelaunch login fix works' if ok else 'FAIL — login still blocked'}")


print("\n" + "=" * 70)
print("Cleanup — restore test user password")
print("=" * 70)
restore = """<?php
$T='%(t)s'; if(($_GET['token']??'')!==$T){http_response_code(403);exit;}
$g=array(); require __DIR__.'/_include/config/db.php';
$d=new mysqli($g['db']['host'],$g['db']['user'],$g['db']['password'],$g['db']['db']);
$d->query("UPDATE `user` SET password='%(orig)s' WHERE user_id=%(uid)d");
header('Content-Type: text/plain'); echo "restored\\n";
""" % {"t": TOKEN, "orig": ORIG_HASH, "uid": TEST_UID}
with open("./_restore_pw.php", "w") as f: f.write(restore)
ftp_stor("./_restore_pw.php", "_restore_pw.php")
print(get(f"https://{HOST}/_restore_pw.php?token={TOKEN}")[1])
ftp_delete("_restore_pw.php")
os.remove("./_restore_pw.php")

print("\nDONE")
