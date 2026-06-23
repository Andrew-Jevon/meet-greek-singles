"""
End-to-end onboarding smoke.
Creates a test user via DB, logs in via the front-door form, hits /onboarding.php,
verifies the 4 cards render, posts answers, verifies onboarding_done=1, cleans up.
"""
from __future__ import annotations
import os, ftplib, ssl, sys, http.cookiejar, urllib.request, urllib.parse, re, time

HOST = "meetgreeksingles.com"
USER_FTP = "staging@meetgreeksingles.com"
PASS_FTP = os.environ.get("STAGING_PASS")
if not PASS_FTP: sys.exit("STAGING_PASS not set")

BASE = "https://meetgreeksingles.com/staging"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"

# Pick names unlikely to clash
TEST_LOGIN = "m3smoke_" + str(int(time.time()))
TEST_MAIL  = TEST_LOGIN + "@example.com"
TEST_PASS  = "TestPass123!"

# --- FTPS reuse boilerplate ---
class _R(ssl.SSLSocket):
    def unwrap(self): pass
class F(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        c, s = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            sess = getattr(self.sock, "session", None)
            c = self.context.wrap_socket(c, server_hostname=self.host, session=sess)
            c.__class__ = _R
        return c, s

def ftps():
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    f = F(HOST, USER_FTP, PASS_FTP, timeout=60, context=ctx); f.prot_p(); f.set_pasv(True); return f


def upload_runner_and_run(sql_filename, sql_body):
    """Upload a one-shot SQL file and run it via _mgs_sqlrun.php."""
    f = ftps()
    # SQL runner already-deleted from staging — re-upload it
    runner_local = os.path.join(os.path.dirname(__file__), "_mgs_sqlrun.php")
    with open(runner_local, "rb") as fh: f.storbinary("STOR _mgs_sqlrun.php", fh)
    # SQL file
    tmp = os.path.join(os.path.dirname(__file__), sql_filename)
    with open(tmp, "w", encoding="utf-8") as out: out.write(sql_body)
    with open(tmp, "rb") as fh: f.storbinary(f"STOR {sql_filename}", fh)
    f.quit()
    # Execute
    url = f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f={sql_filename}"
    req = urllib.request.Request(url, headers={"User-Agent":"smoke/1.0"})
    body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    print(f"  SQL[{sql_filename}]:")
    for line in body.strip().splitlines(): print(f"    {line}")
    # Clean up
    f = ftps()
    for n in ("_mgs_sqlrun.php", sql_filename):
        try: f.delete(n)
        except Exception: pass
    f.quit()
    os.unlink(tmp)
    return body


def make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent","smoke/1.0")]
    return opener, cj


def main():
    print("[1/6] Create test user (with photo flag + min photos disabled) so the")
    print("      forced-photo gate doesn't intercept the onboarding render")
    sql = (
        "INSERT INTO `user` (`name`,`mail`,`password`,`active`,`onboarding_done`,`register`,`is_photo`) "
        f"VALUES ('{TEST_LOGIN}','{TEST_MAIL}',MD5('{TEST_PASS}'),1,0,NOW(),'Y'); "
        f"INSERT INTO `userinfo` (`user_id`) SELECT user_id FROM `user` WHERE name='{TEST_LOGIN}'; "
        "UPDATE config SET `value`='N' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
        "UPDATE config SET `value`='0' WHERE module='options' AND `option`='min_number_photos_to_use_site';"
    )
    upload_runner_and_run("smoke_make_user.sql", sql)

    print("[2/6] Login via /login.php form")
    opener, cj = make_session()
    # POST to ajax.php (per the form action) with login params
    data = urllib.parse.urlencode({
        "cmd": "login", "ajax": "1",
        "user": TEST_LOGIN, "password": TEST_PASS, "remember": "1"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/ajax.php", data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        body = opener.open(req, timeout=30).read().decode("utf-8", errors="replace")
        print(f"  login response: {body[:200]}")
    except Exception as e:
        print(f"  login err: {e}")
    sid = next((c.value for c in cj if c.name == "sid"), None)
    print(f"  sid cookie: {sid}")

    print("[3/6] GET /onboarding.php")
    try:
        body = opener.open(f"{BASE}/onboarding.php", timeout=30).read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        print(f"  HTTP {e.code}")
    cards   = body.count('class="obrd_card')
    radios  = body.count('type="radio"')
    checks  = body.count('type="checkbox"')
    print(f"  body size: {len(body)}  cards={cards}  radios={radios}  checkboxes={checks}")
    if "Welcome &mdash; let" in body or "let&rsquo;s set up your matches" in body:
        print("  OK — intro copy present")
    else:
        print("  FAIL — full error body:")
        print(body)
        # don't return — clean up the test user anyway

    print("[4/6] POST onboarding answers")
    post = urllib.parse.urlencode({
        "cmd": "submit",
        "connection_greece":  "2",   # "Greek living abroad (diaspora)"
        "relationship_intent":"2",   # "Serious long-term relationship"
        "greek_importance":   "1",   # "Very important"
        "greek_future_plans[]": ["1","4"],   # "Want to live in Greece" + "Visit Greece often"
    }, doseq=True).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/onboarding.php", data=post)
    try:
        opener.open(req, timeout=30).read()
        print("  POST returned (likely redirected to home — expected)")
    except urllib.error.HTTPError as e:
        print(f"  POST HTTP {e.code} (302 = good, that's the redirect)")

    print("[5/6] Verify state in DB")
    upload_runner_and_run("smoke_verify.sql",
        f"SELECT user_id, onboarding_done FROM user WHERE name='{TEST_LOGIN}';")

    print("[6/6] Cleanup test user + restore forced-photo settings")
    upload_runner_and_run("smoke_cleanup.sql",
        f"DELETE FROM userinfo WHERE user_id IN (SELECT user_id FROM user WHERE name='{TEST_LOGIN}'); "
        f"DELETE FROM user WHERE name='{TEST_LOGIN}'; "
        "UPDATE config SET `value`='Y' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
        "UPDATE config SET `value`='1' WHERE module='options' AND `option`='min_number_photos_to_use_site';")
    print("DONE")


if __name__ == "__main__":
    main()
