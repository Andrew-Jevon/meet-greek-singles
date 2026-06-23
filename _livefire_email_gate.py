"""LIVE-FIRE TEST — confirm EmailVerification gate actually bounces an
unconfirmed user end-to-end.

Approach (no impact on real users):
  1. Snapshot uid=2 (test account 'acidrocker') current active_code.
  2. Set active_code='LIVEFIRE_TEST_2026_05_10' on uid=2 + ensure
     onboarding_done=1 (so the onboarding gate doesn't muddle the result).
  3. Bypass prelaunch on this Python session, log in as uid=2.
  4. Hit /profile_settings.php (a non-allowlisted page). Expected: 302
     redirect with Location header pointing to /email_not_confirmed.php.
     If we instead get 200 or a redirect to /onboarding.php or homepage,
     the gate is NOT firing and we have a real bug.
  5. Hit /email_not_confirmed.php directly. Expected: 200 — the gate
     allows the verification page itself.
  6. Restore active_code to its snapshot value.

Reads PROD_PASS env var.
"""
from __future__ import annotations
import os, ssl, sys, time, urllib.request, urllib.parse, http.cookiejar, ftplib
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
SITE = Path(__file__).parent
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
TEST_USER = "acidrocker"
TEST_PASS = "mgsTest!2026"
TEST_UID  = 2
ORIG_HASH = "$2y$10$5nSGJgRO6rZzyDUS0fYZ0.NffVCM8MVHtNETGQ3a06Hv14q44Z2Ve"
LIVE_AC   = "LIVEFIRE_TEST_2026_05_10"

PASSWORD = os.environ.get("PROD_PASS")
if not PASSWORD: sys.exit("ERROR: PROD_PASS env var not set")

ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(cj),
)
opener.addheaders = [('User-Agent', 'MGS-Livefire/1.0')]


def get(url, follow=True):
    if not follow:
        # Build a non-following opener that shares the cookiejar
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPCookieProcessor(cj),
            NR(),
        )
        op.addheaders = [('User-Agent', 'MGS-Livefire/1.0')]
        try:
            r = op.open(url, timeout=60)
            return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else ""), dict(e.headers)
    try:
        r = opener.open(url, timeout=60)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace"), dict(e.headers)


def post(url, data, ajax=True):
    body = urllib.parse.urlencode(data).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if ajax: headers["X-Requested-With"] = "XMLHttpRequest"
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        r = opener.open(req, timeout=60)
        return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")


# FTP helpers
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
    f.login("everett@meetgreeksingles.com", PASSWORD); f.prot_p(); f.set_pasv(True); return f
def ftp_stor(local, remote):
    f = ftp_connect()
    try: f.cwd("/"); fp = open(local, "rb"); f.storbinary(f"STOR {remote}", fp); fp.close()
    finally: f.quit()
def ftp_delete(name):
    f = ftp_connect()
    try:
        f.cwd("/")
        try: f.delete(name)
        except ftplib.error_perm: pass
    finally: f.quit()


print("=" * 70)
print("LIVE-FIRE EmailVerification GATE — uid=2 (acidrocker)")
print("=" * 70)

# Step 0: snapshot + arm
print("\n[STEP 0] Snapshot + arm test user (set active_code, ensure onboarding_done=1, set test pw)")
prep = """<?php
$EXPECTED_TOKEN = '%(tok)s';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
$row = $d->query("SELECT active_code, onboarding_done, admin FROM `user` WHERE user_id=%(uid)d")->fetch_assoc();
echo "snapshot active_code=" . var_export($row['active_code'], true) . "\\n";
echo "snapshot onboarding_done=" . $row['onboarding_done'] . "\\n";
echo "snapshot admin=" . $row['admin'] . "\\n";
$hash = password_hash('%(pw)s', PASSWORD_BCRYPT);
$d->query("UPDATE `user` SET active_code='%(ac)s', onboarding_done=1, admin=0, password='" . $d->real_escape_string($hash) . "' WHERE user_id=%(uid)d");
echo "armed: active_code='%(ac)s', onboarding_done=1, admin=0, password=fresh\\n";
""" % {"tok": TOKEN, "uid": TEST_UID, "ac": LIVE_AC, "pw": TEST_PASS}
(SITE / "_livefire_prep.php").write_text(prep, encoding="utf-8")
ftp_stor(SITE / "_livefire_prep.php", "_livefire_prep.php")
code, body, _ = get(f"https://{HOST}/_livefire_prep.php?token={TOKEN}")
print(body)
ftp_delete("_livefire_prep.php")
(SITE / "_livefire_prep.php").unlink(missing_ok=True)

# Capture original values for restore
orig_ac = "''"
orig_done = "0"
orig_admin = "0"
for line in body.splitlines():
    if line.startswith("snapshot active_code="):
        orig_ac = line.split("=", 1)[1]
    elif line.startswith("snapshot onboarding_done="):
        orig_done = line.split("=", 1)[1].strip()
    elif line.startswith("snapshot admin="):
        orig_admin = line.split("=", 1)[1].strip()

# Step 1: prelaunch bypass + login
print("\n[STEP 1] Prelaunch bypass + login as test user")
get(f"https://{HOST}/?platform_mode_off=Y")
print(f"  cookies after bypass: {[c.name for c in cj]}")
code, body = post(f"https://{HOST}/ajax.php?action=login",
                  {"user": TEST_USER, "password": TEST_PASS, "cmd": "login", "ajax": "1"})
print(f"  POST /ajax.php?action=login → HTTP {code}")
print(f"  body[:300]: {body[:300]!r}")
print(f"  cookies after login: {[c.name for c in cj]}")

# Step 2: hit a gated URL — expect 302 → /email_not_confirmed.php
print("\n[STEP 2] Hit /profile_settings.php — expect 302 → /email_not_confirmed.php")
code, body, hdrs = get(f"https://{HOST}/profile_settings.php?nocache={int(time.time())}", follow=False)
loc = hdrs.get("Location", "(none)")
print(f"  HTTP {code}  Location={loc}")
gate_fired = (code == 302 and "email_not_confirmed" in loc)
print(f"  GATE FIRED: {'YES' if gate_fired else 'NO'}")

# Step 2b: also try the homepage / which is NOT allowlisted by EmailVerification
print("\n[STEP 2b] Hit /  — expect 302 → /email_not_confirmed.php")
code, body, hdrs = get(f"https://{HOST}/?nocache={int(time.time())}", follow=False)
loc = hdrs.get("Location", "(none)")
print(f"  HTTP {code}  Location={loc}")
home_gated = (code == 302 and "email_not_confirmed" in loc)
print(f"  HOMEPAGE GATED: {'YES' if home_gated else 'NO'}")

# Step 3: hit /email_not_confirmed.php directly — expect 200
print("\n[STEP 3] Hit /email_not_confirmed.php directly — expect 200")
code, body, hdrs = get(f"https://{HOST}/email_not_confirmed.php?nocache={int(time.time())}", follow=False)
print(f"  HTTP {code}  Location={hdrs.get('Location','(none)')}")
print(f"  title: ", end="")
if "<title>" in body:
    print("'" + body.split("<title>")[1].split("</title>")[0] + "'")
else:
    print("(no title)")
allowed = (code == 200)
print(f"  PAGE ALLOWED: {'YES' if allowed else 'NO'}")

# Step 4: confirm /confirm_email.php is also allowed (for the email link)
print("\n[STEP 4] Hit /confirm_email.php?hash=junk — expect 302 to /index.php (not /email_not_confirmed)")
code, body, hdrs = get(f"https://{HOST}/confirm_email.php?hash=junkjunkjunk", follow=False)
print(f"  HTTP {code}  Location={hdrs.get('Location','(none)')}")

# Step 4b: logout (cmd=logout) is exempt
print("\n[STEP 4b] Hit /logout.php?cmd=logout — gate must let it through")
code, body, hdrs = get(f"https://{HOST}/logout.php?cmd=logout", follow=False)
print(f"  HTTP {code}  Location={hdrs.get('Location','(none)')}")

# Step 5: restore prelaunch on session
get(f"https://{HOST}/?platform_mode_on=Y")

# Step 6: restore test user
print("\n[STEP 5] Restore test user to snapshot state")
restore = """<?php
$EXPECTED_TOKEN = '%(tok)s';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
$d->query("UPDATE `user` SET active_code=%(ac)s, onboarding_done=%(done)s, admin=%(admin)s, password='%(orig)s' WHERE user_id=%(uid)d");
$row = $d->query("SELECT active_code, onboarding_done, admin FROM `user` WHERE user_id=%(uid)d")->fetch_assoc();
echo "restored active_code=" . var_export($row['active_code'], true) . "  onboarding_done=" . $row['onboarding_done'] . "  admin=" . $row['admin'] . "\\n";
""" % {
    "tok": TOKEN, "uid": TEST_UID,
    # orig_ac came back as PHP var_export form (e.g. "'somecode'" or "''")
    "ac": orig_ac if orig_ac.strip() else "''",
    "done": orig_done or "0",
    "admin": orig_admin or "0",
    "orig": ORIG_HASH,
}
(SITE / "_livefire_restore.php").write_text(restore, encoding="utf-8")
ftp_stor(SITE / "_livefire_restore.php", "_livefire_restore.php")
code, body, _ = get(f"https://{HOST}/_livefire_restore.php?token={TOKEN}")
print(body)
ftp_delete("_livefire_restore.php")
(SITE / "_livefire_restore.php").unlink(missing_ok=True)

# Final verdict
print("\n" + "=" * 70)
verdict_ok = gate_fired and home_gated and allowed
print(f"  VERDICT: {'PASS — gate works as expected' if verdict_ok else 'FAIL — gate did not behave as expected'}")
print("=" * 70)
sys.exit(0 if verdict_ok else 1)
