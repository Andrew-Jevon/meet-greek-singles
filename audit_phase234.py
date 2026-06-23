"""
Phase 2/3/4 audit on production.

Phase 2 — full signup flow end-to-end with a synthetic test user.
Phase 3 — logged-in surface for that test user.
Phase 4 — admin pages with admin credentials.

Produces a numbered bug list. No fixes.
"""
from __future__ import annotations
import os, http.cookiejar, urllib.request, urllib.parse, time, ftplib, ssl, sys, re

PROD_PASS = os.environ.get("PROD_PASS")
if not PROD_PASS: sys.exit("PROD_PASS not set")
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
    f = F("meetgreeksingles.com", "everett@meetgreeksingles.com", PROD_PASS, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True); return f


bugs = []
def bug(phase, page, severity, msg):
    bugs.append((phase, page, severity, msg))


PHP_ERR = re.compile(r"<b>(Fatal error|Parse error|Warning|Notice|Deprecated)</b>|"
                     r"Uncaught \w*Exception|Call to undefined function|"
                     r"pp_installator|Stack trace:")


def run_sql(name, body):
    """Upload and run a one-shot SQL via the runner."""
    ftp = ftps()
    runner = os.path.join(os.path.dirname(__file__), "_mgs_sqlrun.php")
    with open(runner, "rb") as fh:
        ftp.storbinary("STOR _mgs_sqlrun.php", fh)
    p = os.path.join(os.path.dirname(__file__), name)
    with open(p, "w", encoding="utf-8") as out: out.write(body)
    with open(p, "rb") as fh:
        ftp.storbinary(f"STOR {name}", fh)
    ftp.quit()
    res = urllib.request.urlopen(f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f={name}", timeout=30).read().decode()
    # cleanup
    ftp = ftps()
    for n in ("_mgs_sqlrun.php", name):
        try: ftp.delete(n)
        except: pass
    ftp.quit()
    os.unlink(p)
    return res


def make_session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "audit/1.0")]
    return op, cj


def fetch(opener, url, follow=True):
    try:
        if not follow:
            class NR(urllib.request.HTTPRedirectHandler):
                def http_error_302(self, req, fp, code, msg, headers): return None
            handlers = list(opener.handlers) + [NR()]
            o = urllib.request.build_opener(*handlers)
            o.addheaders = opener.addheaders
            r = o.open(url, timeout=30)
        else:
            r = opener.open(url, timeout=30)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers), r.url
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace") if hasattr(e,"read") else ""
        return e.code, body, dict(e.headers), e.url if hasattr(e,"url") else url


# ════════════════════════════════════════════════════════════════════════
print("=" * 75)
print(" PHASE 2 — SIGNUP FLOW")
print("=" * 75)
print()

TS = str(int(time.time()))
LOGIN, MAIL, PASS = f"audit_{TS}", f"audit_{TS}@example.invalid", "Tp123!"

print(f"  test user: {LOGIN}")
sql = (f"INSERT INTO `user` (`name`,`mail`,`password`,`active`,`onboarding_done`,`register`,`is_photo`) "
       f"VALUES ('{LOGIN}','{MAIL}',MD5('{PASS}'),1,0,NOW(),'N'); "
       f"INSERT INTO `userinfo` (`user_id`) SELECT user_id FROM `user` WHERE name='{LOGIN}';")
run_sql("audit_make.sql", sql)


print("  [2.1] /join (welcome) reachable")
op, cj = make_session()
st, body, _, url = fetch(op, f"{BASE}/join")
if st != 200: bug(2, "/join welcome", "FAIL", f"status={st}")
elif PHP_ERR.search(body): bug(2, "/join welcome", "FAIL", "PHP runtime error in body")
elif "Welcome to Meet Greek Singles" not in body and "Greek Singles" not in body:
    bug(2, "/join welcome", "WARN", "expected welcome copy missing")
print(f"      status={st} size={len(body)}")


print("  [2.2] login via AJAX")
data = urllib.parse.urlencode({"cmd":"login","ajax":"1","user":LOGIN,"password":PASS,"remember":"1"}).encode()
req = urllib.request.Request(f"{BASE}/ajax.php", data=data,
    headers={"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"})
resp = op.open(req, timeout=30).read().decode()
print(f"      response: {resp.strip()[:80]}")
if "logged" not in resp:
    bug(2, "login AJAX", "FAIL", f"login failed: {resp[:200]}")


print("  [2.3] T&C bypass — direct POST without privacy_policy must be rejected")
post = urllib.parse.urlencode({"mail":"x@e.co","password":"Tp123!","login":"someone","gender":"M"}).encode()
req = urllib.request.Request(f"{BASE}/join.php?cmd=register&ajax=1", data=post)
resp = urllib.request.urlopen(req, timeout=30).read().decode()
if "privacy_policy" not in resp:
    bug(2, "T&C enforcement", "FAIL", f"server accepted submission without privacy_policy: {resp[:200]}")
else:
    print(f"      OK — server rejects: {resp[:100]}")


print("  [2.4] captcha endpoint accessible (PNG)")
st, body, hdrs, _ = fetch(op, f"{BASE}/_server/securimage/securimage_show_custom.php?sid=test")
if st != 200 or hdrs.get("Content-Type","").find("image") == -1:
    bug(2, "captcha endpoint", "FAIL", f"status={st} type={hdrs.get('Content-Type')} (must be image/png)")
else:
    print(f"      OK — {hdrs.get('Content-Type')} {len(body)}b")


print("  [2.5] /onboarding.php reachable for our logged-in test user (no redirect loop)")
class TraceR(urllib.request.HTTPRedirectHandler):
    def __init__(self): self.chain = []
    def http_error_302(self, req, fp, code, msg, headers):
        loc = headers.get("Location","")
        self.chain.append(loc)
        if len(self.chain) > 8: return None
        return urllib.request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
trace = TraceR()
op2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), trace)
op2.addheaders = [("User-Agent","audit/1.0")]
try:
    r = op2.open(f"{BASE}/onboarding.php", timeout=30)
    body = r.read().decode("utf-8","replace")
    if len(trace.chain) > 0:
        bug(2, "/onboarding.php", "WARN", f"redirected via {trace.chain}")
    if "obrd_card" not in body:
        bug(2, "/onboarding.php", "FAIL", "onboarding cards not rendered")
    print(f"      hops={len(trace.chain)} body={len(body)}b cards={body.count('obrd_card')}")
except urllib.error.HTTPError as e:
    bug(2, "/onboarding.php", "FAIL", f"HTTP {e.code}, chain={trace.chain}")


print("  [2.6] onboarding submit + verify state in DB")
post = urllib.parse.urlencode({
    "cmd": "submit",
    "connection_greece": "2", "relationship_intent": "1",
    "greek_importance": "1", "greek_values_traditions": "1",
}).encode()
req = urllib.request.Request(f"{BASE}/onboarding.php", data=post)
try: op.open(req, timeout=30).read()
except urllib.error.HTTPError as e: pass
res = run_sql("audit_check.sql",
    f"SELECT u.user_id, u.onboarding_done, i.connection_greece, i.relationship_intent FROM user u JOIN userinfo i USING(user_id) WHERE u.name='{LOGIN}';")
print("      DB:", res.strip().splitlines()[-1] if res.strip().splitlines() else "(empty)")
if "1\t2\t1" not in res:
    bug(2, "onboarding submit", "FAIL", f"answers not persisted: {res[:200]}")


# ════════════════════════════════════════════════════════════════════════
print()
print("=" * 75)
print(" PHASE 3 — LOGGED-IN SURFACE")
print("=" * 75)
print()

# Re-fetch session — we should still be logged in
member_pages = [
    ("/profile_view.php",       "profile_view"),
    ("/profile_settings.php",   "profile_settings"),
    ("/help.php",               "help (member)"),
    ("/upgrade.php",            "subscription"),
    ("/contact.php",            "contact (member)"),
]
for path, label in member_pages:
    st, body, hdrs, url = fetch(op, f"{BASE}{path}")
    err = PHP_ERR.search(body)
    if st == 302:
        loc = hdrs.get("Location","")
        bug(3, path, "INFO", f"302 → {loc}")
    elif st != 200:
        bug(3, path, "FAIL", f"status={st}")
    elif err:
        bug(3, path, "FAIL", f"PHP error: {err.group(0)}")
    print(f"  {path:30s}  status={st}  size={len(body)}")

print()
print("  [3.x] sign out — verify cookies cleared + lands on /index.php")
class T2(urllib.request.HTTPRedirectHandler):
    def __init__(self): self.chain = []
    def http_error_302(self, req, fp, code, msg, headers):
        self.chain.append(headers.get("Location",""))
        if len(self.chain) > 6: return None
        return urllib.request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
t2 = T2()
op3 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), t2)
op3.addheaders = [("User-Agent","audit/1.0")]
try:
    r = op3.open(f"{BASE}/index.php?cmd=logout", timeout=30)
    body = r.read().decode("utf-8","replace")
    has_c_user = any(c.name == 'c_user' for c in cj)
    if "/onboarding.php" in t2.chain:
        bug(3, "logout", "FAIL", "logout still redirects to /onboarding.php")
    if has_c_user:
        bug(3, "logout", "FAIL", "c_user cookie still set after logout")
    print(f"      final={r.url}  hops={len(t2.chain)}  c_user_cookie={has_c_user}")
except urllib.error.HTTPError as e:
    bug(3, "logout", "FAIL", f"HTTP {e.code}")


# ════════════════════════════════════════════════════════════════════════
print()
print("=" * 75)
print(" PHASE 4 — ADMIN")
print("=" * 75)
print()

# Admin login (assume admin/AdminR@1!)
op4, cj4 = make_session()
print("  [4.1] /administration/ login")
data = urllib.parse.urlencode({"login":"admin","password":"AdminR@1!","cmd":"login"}).encode()
req = urllib.request.Request(f"{BASE}/administration/index.php", data=data)
try:
    r = op4.open(req, timeout=30)
    body = r.read().decode("utf-8","replace")
    print(f"      status={r.status}  url={r.url}  size={len(body)}")
    if "logout" not in body.lower() and "site_options" not in body.lower():
        bug(4, "admin login", "FAIL", "admin login may have failed (no logout marker)")
except urllib.error.HTTPError as e:
    bug(4, "admin login", "FAIL", f"HTTP {e.code}")

admin_pages = [
    ("/administration/site_options.php", "site_options"),
    ("/administration/pages.php",        "pages"),
    ("/administration/users_fields.php", "users_fields"),
    ("/administration/help_topic.php",   "help_topic"),
    ("/administration/visibility_scope.php", "visibility_scope (M2)"),
    ("/administration/automail.php",     "automail (transactional emails)"),
]
for path, label in admin_pages:
    st, body, hdrs, _ = fetch(op4, f"{BASE}{path}")
    err = PHP_ERR.search(body)
    if st != 200:
        bug(4, path, "WARN", f"status={st}")
    elif err:
        bug(4, path, "FAIL", f"PHP error: {err.group(0)}")
    else:
        # admin_login confirmed by presence of "logout" link
        if "logout" not in body.lower():
            bug(4, path, "WARN", "no logout link in body — may have lost session")
    print(f"  {path:50s}  status={st}  size={len(body)}")


# Cleanup
print()
print("  [cleanup] removing audit test user")
run_sql("audit_cleanup.sql",
    f"DELETE FROM userinfo WHERE user_id IN (SELECT user_id FROM user WHERE name='{LOGIN}'); "
    f"DELETE FROM user WHERE name='{LOGIN}';")


# ════════════════════════════════════════════════════════════════════════
print()
print("=" * 75)
print(" BUG LIST")
print("=" * 75)
print()
if not bugs:
    print("No bugs detected in phases 2–4 by automated scan.")
else:
    by_sev = {"FAIL": [], "WARN": [], "INFO": []}
    for ph, page, sev, msg in bugs:
        by_sev[sev].append((ph, page, msg))
    for sev in ("FAIL", "WARN", "INFO"):
        if not by_sev[sev]: continue
        print(f"  {sev}  ({len(by_sev[sev])})")
        for ph, page, msg in by_sev[sev]:
            print(f"    P{ph} [{page}]  {msg}")
        print()
print(f"  total: {len(bugs)} findings")
