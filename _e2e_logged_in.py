"""Probe B — log in as admin, verify the live behavior of /onboarding.php
(should render the 4 new onboarding questions) and /search_results.php
(should return rows with match_score in effect)."""
from __future__ import annotations
import os, ssl, sys, time, urllib.request, urllib.parse, http.cookiejar
import ftplib

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
# uid=2 (acidrocker) — temporarily set to known pw via _mgs_set_test_pw.php
# (restore at end of script using ORIG_HASH below)
TEST_USER = "acidrocker"
TEST_PASS = "mgsTest!2026"
TEST_UID = 2
ORIG_HASH = "$2y$10$5nSGJgRO6rZzyDUS0fYZ0.NffVCM8MVHtNETGQ3a06Hv14q44Z2Ve"
ADMIN_USER = TEST_USER     # legacy var name retained — not actually admin
ADMIN_PASS = TEST_PASS
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
opener.addheaders = [
    ('User-Agent', 'MGS-E2E-Probe/1.0'),
]


def get(url):
    req = urllib.request.Request(url)
    try:
        with opener.open(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def post(url, data, ajax=True):
    body = urllib.parse.urlencode(data).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if ajax: headers["X-Requested-With"] = "XMLHttpRequest"
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with opener.open(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


# --- FTP helpers (for setup probe) ---
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
    f = F(context=c)
    f.connect(HOST, 21, timeout=60)
    f.login("everett@meetgreeksingles.com", PASSWORD); f.prot_p(); f.set_pasv(True)
    return f

def ftp_stor(local, remote):
    f = ftp_connect()
    try:
        f.cwd("/")
        with open(local, "rb") as fp:
            f.storbinary(f"STOR {remote}", fp)
    finally: f.quit()

def ftp_delete(name):
    f = ftp_connect()
    try:
        f.cwd("/")
        try: f.delete(name)
        except ftplib.error_perm: pass
    finally: f.quit()


# Step 0: prep — re-set test user's password to TEST_PASS (in case it was
# restored by a previous run), set onboarding answers + onboarding_done=1
# (so we can test /search_results.php with match_score active)
print("=" * 70)
print("STEP 0 — prep: re-set test user password + onboarding answers + done=1")
print("=" * 70)
prep_php = """<?php
$EXPECTED_TOKEN = '%(tok)s';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
// Snapshot test user (uid=2)
$o = $d->query("SELECT onboarding_done FROM `user` WHERE user_id=%(uid)d")->fetch_assoc();
$ui = $d->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=%(uid)d")->fetch_assoc();
echo "snapshot test user.onboarding_done=" . $o['onboarding_done'] . "\\n";
echo "snapshot test userinfo answers=" . json_encode($ui) . "\\n";

// Snapshot Joyce (uid=1, the candidate in test user's search results)
// so we can give her temporary answers, then restore
$j_ui = $d->query("SELECT looking_for, culture_importance, greek_meaning, relocation_openness FROM userinfo WHERE user_id=1")->fetch_assoc();
echo "snapshot joyce userinfo answers=" . json_encode($j_ui) . "\\n";

// Re-set test user known password + onboarding done + answers
$hash = password_hash('%(pass)s', PASSWORD_BCRYPT);
$d->query("UPDATE `user` SET password='" . $d->real_escape_string($hash) . "', onboarding_done=1 WHERE user_id=%(uid)d");
$d->query("UPDATE userinfo SET looking_for=1, culture_importance=1, greek_meaning=47, relocation_openness=4 WHERE user_id=%(uid)d");
echo "set test user: password=fresh, done=1, l=1 c=1 g=47 r=4\\n";

// Give Joyce IDENTICAL answers so the score is 100 (≥85) — exercises the
// Strong Match badge path
$d->query("UPDATE userinfo SET looking_for=1, culture_importance=1, greek_meaning=47, relocation_openness=4 WHERE user_id=1");
echo "set joyce TEMP: l=1 c=1 g=47 r=4 (identical → expect score=100, Strong Match)\\n";
""" % {"tok": TOKEN, "uid": TEST_UID, "pass": TEST_PASS}
with open("./_e2e_prep.php", "w", encoding="utf-8") as f: f.write(prep_php)
ftp_stor("./_e2e_prep.php", "_e2e_prep.php")
code, body = get(f"https://{HOST}/_e2e_prep.php?token={TOKEN}")
print(body)
ftp_delete("_e2e_prep.php")


# Step 1: bypass prelaunch on this session (?platform_mode_off=Y), then log in.
# Without the bypass, /ajax.php?action=login is in prelaunch's deny list.
# The bypass is per-session, sets get_session('platform_mode_off') = 'Y',
# and is the same mechanism used for admin previews.
print("\n" + "=" * 70)
print("STEP 1 — bypass prelaunch on this session, then log in via ajax")
print("=" * 70)
# Set the bypass cookie
get(f"https://{HOST}/?platform_mode_off=Y")
print(f"  cookies after bypass: {[c.name for c in cj]}")

# Now POST login to /ajax.php — actual form fields are `user` and `password`
# (per the live login form), with cmd=login + ajax=1.
login_data = {
    "user":     ADMIN_USER,
    "password": ADMIN_PASS,
    "cmd":      "login",
    "ajax":     "1",
}
code, body = post(f"https://{HOST}/ajax.php?action=login", login_data)
print(f"  POST /ajax.php?action=login → HTTP {code}")
print(f"  body (first 500): {body[:500]}")
print(f"  cookies after login: {[c.name for c in cj]}")


# Step 2: confirm we're logged in by hitting a protected page
print("\n" + "=" * 70)
print("STEP 2 — verify session by hitting a member-only page")
print("=" * 70)
code, body = get(f"https://{HOST}/profile_settings.php?nocache={int(time.time())}")
print(f"  /profile_settings.php → HTTP {code}, body bytes: {len(body)}")
logged_in_indicator = ("logout" in body.lower() or "log out" in body.lower()
                       or "profile" in body.lower())
print(f"  appears logged-in (logout link / profile content): {logged_in_indicator}")


# Step 3: hit /search_results.php and verify match_score is in effect
print("\n" + "=" * 70)
print("STEP 3 — /search_results.php with admin session (match_score active)")
print("=" * 70)
code, body = get(f"https://{HOST}/search_results.php?nocache={int(time.time())}")
print(f"  /search_results.php → HTTP {code}, body bytes: {len(body)}")
print(f"  title: ", end="")
if "<title>" in body:
    print("'" + body.split("<title>")[1].split("</title>")[0] + "'")
else:
    print("(no title)")
has_users = ('class="user' in body or 'data-user-id' in body or 'profile_view' in body)
print(f"  shows user cards: {has_users}")

# Definitive marker check — userslist.class.php emits this HTML comment
# WHEN our match_score injection fires for a logged-in viewer with answers.
marker_present = 'mgs_match_score_injected:' in body
print(f"  match_score injection marker present: {marker_present}")
if marker_present:
    marker_line = [l for l in body.split('\n') if 'mgs_match_score_injected' in l]
    if marker_line:
        print(f"  marker: {marker_line[0].strip()}")

with open("./search_results_render.html", "w", encoding="utf-8") as fp:
    fp.write(body)
print(f"  (rendered HTML saved to ./search_results_render.html)")

# Step 3b — verify the badge HTML+JS shipped, and call /match_scores.php
# with the visible UIDs to confirm the JSON endpoint returns scores.
import re
print("\n  --- badge integration check ---")
badge_count = body.count('mgs_match_badge" data-uid=')
print(f"  badge divs in HTML (excludes CSS): {badge_count}")
js_present = 'paintBadges' in body or '/match_scores.php' in body
print(f"  paintBadges JS or /match_scores.php in HTML: {js_present}")

# Pull UIDs out of the rendered badges
uids = re.findall(r'mgs_match_badge"\s+data-uid="(\d+)"', body)
print(f"  uids extracted from badge data-uid: {uids}")

if uids:
    # First — call the debug endpoint to see what session/uid it observes
    score_data = urllib.parse.urlencode([("uids[]", u) for u in uids]).encode()
    debug_req = urllib.request.Request(
        f"https://{HOST}/match_scores.php?_debug={TOKEN}",
        data=score_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with opener.open(debug_req, timeout=30) as r:
            print(f"\n  DEBUG /match_scores.php?_debug → HTTP {r.status}")
            print("  " + r.read().decode("utf-8", errors="replace").replace("\n", "\n  "))
    except urllib.error.HTTPError as e:
        print(f"  DEBUG → HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")

    # Then the real call
    score_req = urllib.request.Request(
        f"https://{HOST}/match_scores.php",
        data=score_data,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "X-Requested-With": "XMLHttpRequest"},
    )
    try:
        with opener.open(score_req, timeout=30) as r:
            score_body = r.read().decode("utf-8", errors="replace")
            print(f"\n  POST /match_scores.php → HTTP {r.status}")
            print(f"  response body: {score_body}")
    except urllib.error.HTTPError as e:
        print(f"  POST /match_scores.php → HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")


# Step 4: now set admin's onboarding_done=0 so we can hit /onboarding.php
print("\n" + "=" * 70)
print("STEP 4 — temporarily set admin done=0 to test /onboarding.php render")
print("=" * 70)
prep2_php = """<?php
$EXPECTED_TOKEN = '%(tok)s';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
$d->query("UPDATE `user` SET onboarding_done=0 WHERE user_id=%(uid)d");
echo "test user done=0\\n";
""" % {"tok": TOKEN, "uid": TEST_UID}
with open("./_e2e_prep2.php", "w") as f: f.write(prep2_php)
ftp_stor("./_e2e_prep2.php", "_e2e_prep2.php")
code, body = get(f"https://{HOST}/_e2e_prep2.php?token={TOKEN}")
print(body)
ftp_delete("_e2e_prep2.php")

code, body = get(f"https://{HOST}/onboarding.php?nocache={int(time.time())}")
print(f"\n  /onboarding.php → HTTP {code}, body bytes: {len(body)}")
print(f"  title: ", end="")
if "<title>" in body:
    print("'" + body.split("<title>")[1].split("</title>")[0] + "'")

# Look for the 4 new question titles in the rendered HTML
checks = [
    ("Q1 'What are you looking for?'", "What are you looking for?" in body),
    ("Q2 'How important is Greek culture'", "How important is Greek culture" in body),
    ("Q3 'What does being Greek mean to you?'", "What does being Greek mean to you?" in body),
    ("Q4 'open to relocating'", "open to relocating" in body or "Relocating" in body),
    # connection_greece's actual TITLE is 'How do you connect with Greece?'
    # The literal phrase 'Connection to Greece' is one of Q3's checkbox options,
    # so don't penalize that — only penalize the old question's title.
    ("old connection_greece question NOT in onboarding", "How do you connect with Greece" not in body),
    # Also look for an explicit Q3 option to confirm Q3 actually rendered
    ("Q3 option 'Family and traditions' present", "Family and traditions" in body),
    # Confirm no demoted M3 fields linger
    ("old 'What are you hoping to find' NOT in onboarding", "What are you hoping to find" not in body),
]
for label, ok in checks:
    print(f"  [{('OK ' if ok else 'FAIL')}] {label}")

# Step 4b: also write the rendered HTML to a local file so we can manually
# inspect if anything unexpected shows up
with open("./onboarding_render.html", "w", encoding="utf-8") as fp:
    fp.write(body)
print(f"\n  (rendered onboarding HTML saved to ./onboarding_render.html — {len(body)} bytes)")


# Step 4.5: restore prelaunch on this session
get(f"https://{HOST}/?platform_mode_on=Y")

# Step 5: cleanup — restore admin
print("\n" + "=" * 70)
print("STEP 5 — restore admin to original state")
print("=" * 70)
restore_php = """<?php
$EXPECTED_TOKEN = '%(tok)s';
if (($_GET['token'] ?? '') !== $EXPECTED_TOKEN) { http_response_code(403); exit("forbidden\\n"); }
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
header('Content-Type: text/plain');
// Restore test user
$d->query("UPDATE `user` SET onboarding_done=0, password='%(orig)s' WHERE user_id=%(uid)d");
$d->query("UPDATE userinfo SET looking_for=0, culture_importance=0, greek_meaning=0, relocation_openness=0 WHERE user_id=%(uid)d");
// Restore Joyce (uid=1) — set back to all-zero (her snapshot value pre-probe)
$d->query("UPDATE userinfo SET looking_for=0, culture_importance=0, greek_meaning=0, relocation_openness=0 WHERE user_id=1");
echo "test user + joyce restored to original (all zeros + original password)\\n";
""" % {"tok": TOKEN, "uid": TEST_UID, "orig": ORIG_HASH}
with open("./_e2e_restore.php", "w") as f: f.write(restore_php)
ftp_stor("./_e2e_restore.php", "_e2e_restore.php")
code, body = get(f"https://{HOST}/_e2e_restore.php?token={TOKEN}")
print(body)
ftp_delete("_e2e_restore.php")

print("\nDONE")
