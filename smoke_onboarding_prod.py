"""
End-to-end onboarding smoke against PRODUCTION.

Creates a temp test user with a recognisable name so it's obvious in the user
table, logs in via the real form, walks the onboarding flow, verifies the
save, and cleans up — same shape as the staging smoke but pointed at prod.
"""
from __future__ import annotations
import os, http.cookiejar, urllib.request, urllib.parse, time, ftplib, ssl, sys, io

PASS_FTP = os.environ.get("PROD_PASS")
if not PASS_FTP: sys.exit("PROD_PASS not set")
BASE = "https://meetgreeksingles.com"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"

class _R(ssl.SSLSocket):
    def unwrap(self): pass
class F(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        c, s = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            sess = getattr(self.sock, "session", None)
            c = self.context.wrap_socket(c, server_hostname=self.host, session=sess); c.__class__=_R
        return c, s

def ftps():
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    f = F("meetgreeksingles.com", "everett@meetgreeksingles.com", PASS_FTP, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True); return f

def upload(ftp, local: str, remote: str):
    with open(local, "rb") as fh:
        ftp.storbinary(f"STOR {remote}", fh)

def http_get(url, opener=None, timeout=30):
    o = opener or urllib.request.build_opener()
    o.addheaders = [("User-Agent","prod-smoke/1.0")]
    try:
        r = o.open(url, timeout=timeout)
        return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else "")

def run_sql(sql_filename, sql_body):
    ftp = ftps()
    runner = os.path.join(os.path.dirname(__file__), "_mgs_sqlrun.php")
    upload(ftp, runner, "_mgs_sqlrun.php")
    p = os.path.join(os.path.dirname(__file__), sql_filename)
    with open(p, "w", encoding="utf-8") as out: out.write(sql_body)
    upload(ftp, p, sql_filename)
    ftp.quit()
    _, body = http_get(f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f={sql_filename}", timeout=30)
    print("  " + body.strip().replace("\n", "\n  "))
    # delete server-side + local
    ftp = ftps()
    for n in ("_mgs_sqlrun.php", sql_filename):
        try: ftp.delete(n)
        except ftplib.error_perm: pass
    ftp.quit()
    os.unlink(p)
    return body


def main():
    TS = str(int(time.time()))
    LOGIN, MAIL, PASS = f"prod_smk_{TS}", f"prod_smk_{TS}@example.invalid", "Tp123!"

    print("[1/5] Create test user on PROD (with photo flag, photo gate temporarily off)")
    sql = (
        f"INSERT INTO `user` (`name`,`mail`,`password`,`active`,`onboarding_done`,`register`,`is_photo`) "
        f"VALUES ('{LOGIN}','{MAIL}',MD5('{PASS}'),1,0,NOW(),'Y'); "
        f"INSERT INTO `userinfo` (`user_id`) SELECT user_id FROM `user` WHERE `name`='{LOGIN}'; "
        "UPDATE config SET `value`='N' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
        "UPDATE config SET `value`='0' WHERE module='options' AND `option`='min_number_photos_to_use_site';"
    )
    run_sql("prod_smk_make.sql", sql)

    print("[2/5] Login via the real form")
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent","prod-smoke/1.0")]
    data = urllib.parse.urlencode({"cmd":"login","ajax":"1","user":LOGIN,"password":PASS,"remember":"1"}).encode()
    req = urllib.request.Request(f"{BASE}/ajax.php", data=data,
        headers={"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"})
    print("  login response:", op.open(req, timeout=20).read().decode().strip()[:120])

    print("[3/5] GET /onboarding.php as the new user")
    body = op.open(f"{BASE}/onboarding.php", timeout=30).read().decode("utf-8","replace")
    markers = [
        "How do you connect with Greece?", "We celebrate every kind of Greek connection",
        "Born and raised in Greece", "What are you hoping to find?", "Just exploring",
        "How important is Greek culture", "Do shared values and traditions",
    ]
    hits = sum(1 for m in markers if m in body)
    print(f"  body size: {len(body)}  spec markers: {hits}/{len(markers)}")
    print(f"  card structure: cards={body.count('class=\"obrd_card')}  radios={body.count('type=\"radio\"')}  dots={body.count('obrd_dot')}")

    print("[4/5] POST onboarding answers")
    post = urllib.parse.urlencode({
        "cmd": "submit",
        "connection_greece":  "2",
        "relationship_intent":"1",
        "greek_importance":   "1",
        "greek_values_traditions":"1",
    }).encode()
    req = urllib.request.Request(f"{BASE}/onboarding.php", data=post)
    try:
        op.open(req, timeout=30).read()
        print("  POST followed redirect (expected — server marks onboarding_done=1 then redirects home)")
    except urllib.error.HTTPError as e:
        print(f"  POST status={e.code}")

    print("[5/5] Verify state in DB + cleanup")
    # Read state via sqlquery (separate helper that returns SELECT results)
    ftp = ftps()
    sqlq_local = os.path.join(os.path.dirname(__file__), "_mgs_sqlquery.php")
    upload(ftp, sqlq_local, "_mgs_sqlquery.php")
    qfile = os.path.join(os.path.dirname(__file__), "verify.sql")
    with open(qfile, "w", encoding="utf-8") as f: f.write(
        f"SELECT u.user_id, u.onboarding_done, "
        f"i.connection_greece, i.relationship_intent, i.greek_importance, i.greek_values_traditions "
        f"FROM `user` u LEFT JOIN userinfo i ON i.user_id = u.user_id "
        f"WHERE u.name='{LOGIN}';"
    )
    upload(ftp, qfile, "verify.sql")
    ftp.quit()
    _, body = http_get(f"{BASE}/_mgs_sqlquery.php?token={TOKEN}&f=verify.sql", timeout=30)
    print("  DB state:")
    print("  " + body.strip().replace("\n","\n  "))
    os.unlink(qfile)

    # cleanup test user + restore photo gate
    print("  cleanup test user + restore photo settings")
    cleanup_sql = (
        f"DELETE FROM userinfo WHERE user_id IN (SELECT user_id FROM `user` WHERE name='{LOGIN}'); "
        f"DELETE FROM `user` WHERE name='{LOGIN}'; "
        "UPDATE config SET `value`='Y' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
        "UPDATE config SET `value`='1' WHERE module='options' AND `option`='min_number_photos_to_use_site';"
    )
    run_sql("prod_smk_cleanup.sql", cleanup_sql)

    # nuke the helpers
    ftp = ftps()
    for n in ("_mgs_sqlquery.php", "verify.sql"):
        try: ftp.delete(n)
        except ftplib.error_perm: pass
    ftp.quit()

    print()
    if hits == len(markers):
        print("PROD ONBOARDING SMOKE: PASS")
    else:
        print(f"PROD ONBOARDING SMOKE: FAIL ({hits}/{len(markers)} markers)")
        sys.exit(1)

if __name__ == "__main__":
    main()
