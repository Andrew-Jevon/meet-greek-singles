"""
Full-site smoke for staging — tightened checks, accurate assertions.
"""
from __future__ import annotations
import os, http.cookiejar, urllib.request, urllib.parse, time, ftplib, ssl, sys, re

PASS_FTP = os.environ.get("STAGING_PASS")
if not PASS_FTP: sys.exit("STAGING_PASS not set")
BASE = "https://meetgreeksingles.com/staging"
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
    f = F("meetgreeksingles.com", "staging@meetgreeksingles.com", PASS_FTP, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True); return f


# Real PHP runtime errors only — "<br />" or line-prefix patterns Chameleon emits.
PHP_ERR_RE = re.compile(
    r"(<b>Fatal error</b>|<b>Parse error</b>|<b>Warning</b>|<b>Notice</b>|"
    r"Uncaught \w*Exception|Call to undefined function|"
    r"pp_installator|Stack trace:)"
)


def fetch(url, opener=None, timeout=30, follow=True):
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        if opener is None:
            o = urllib.request.build_opener(NR())
        else:
            o = urllib.request.build_opener(*list(opener.handlers), NR())
    else:
        o = opener or urllib.request.build_opener()
    o.addheaders = [("User-Agent","smoke/2.0")]
    try:
        r = o.open(url, timeout=timeout)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace") if hasattr(e,"read") else ""
        return e.code, body, dict(e.headers)
    except Exception as e:
        return -1, str(e), {}


results = []
def case(label, ok, detail=""):
    results.append((ok, label, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"   {detail}" if detail else ""))


print("=" * 60); print("1. PUBLIC PAGES — content + no PHP runtime errors"); print("=" * 60)
GUEST = [
    ("/",                              ["preparing for our official launch", "Find the Greek Connection", "Join us now"]),
    ("/about.php",                     []),
    ("/contact.php",                   ["Send us a message", "Get in touch", "Browse our help"]),
    ("/help.php",                      ["Common questions about Meet Greek Singles", "How is Meet Greek Singles different", "Join to read full answers"]),
    ("/info.php?page=term_cond",       []),
    ("/info.php?page=priv_policy",     []),
    ("/join",                          []),  # use SEO URL not /join.php (which 302s)
    ("/login",                         ["Welcome Back", "Sign in"]),
    ("/forget_password.php",           []),
    ("/email_not_confirmed.php",       []),
]
for path, must in GUEST:
    status, body, _ = fetch(BASE + path)
    err = PHP_ERR_RE.search(body)
    if err:
        case(f"GET {path}", False, f"PHP issue: {err.group(0)}"); continue
    if status != 200:
        case(f"GET {path}", False, f"status={status}"); continue
    missing = [m for m in must if m not in body]
    if missing:
        case(f"GET {path}", False, f"missing: {missing}")
    else:
        case(f"GET {path}", True, f"size={len(body)}")


print(); print("=" * 60); print("2. PRE-LAUNCH GATE — blocked URLs redirect to landing"); print("=" * 60)
BLOCKED = ["/search_results", "/search.php", "/mail.php", "/messages.php",
           "/upgrade.php", "/community", "/groups.php", "/forum.php"]
for path in BLOCKED:
    status, _, hdrs = fetch(BASE + path, follow=False)
    loc = hdrs.get("Location", "")
    case(f"BLOCKED {path}", status == 302 and "__plfb=1" in loc, f"status={status} loc={loc[:50]}")


print(); print("=" * 60); print("3. FOOTER ORDER — scoped to the actual footer <ul>"); print("=" * 60)
status, body, _ = fetch(BASE + "/")
m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
if not m:
    case("Footer ul present", False)
else:
    items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
    expected = ["About", "Terms & Conditions", "Privacy Policy", "Questions & Answers", "Contact us"]
    case(f"Footer order = {expected}", items == expected, f"got: {items}")
    for unwanted in ["Browse matches", "Events", "Community Ambassadors"]:
        case(f"Footer does NOT contain '{unwanted}'", unwanted not in m.group(1))


print(); print("=" * 60); print("4. ONBOARDING — full logged-in flow"); print("=" * 60)
ftp = ftps()
with open(os.path.join(os.path.dirname(__file__), "_mgs_sqlrun.php"), "rb") as fh:
    ftp.storbinary("STOR _mgs_sqlrun.php", fh)
TS = str(int(time.time())); LOGIN, PASS = f"smk_{TS}", "Tp123!"
sql = (f"INSERT INTO user (name,mail,password,active,onboarding_done,register,is_photo) "
       f"VALUES ('{LOGIN}','{LOGIN}@e.co',MD5('{PASS}'),1,0,NOW(),'Y'); "
       f"INSERT INTO userinfo (user_id) SELECT user_id FROM user WHERE name='{LOGIN}'; "
       f"UPDATE config SET value='N' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
       f"UPDATE config SET value='0' WHERE module='options' AND `option`='min_number_photos_to_use_site';")
with open(os.path.join(os.path.dirname(__file__), "mk.sql"), "w") as f: f.write(sql)
with open(os.path.join(os.path.dirname(__file__), "mk.sql"), "rb") as fh: ftp.storbinary("STOR mk.sql", fh)
urllib.request.urlopen(f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f=mk.sql", timeout=30).read()

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent","smoke/2.0")]
data = urllib.parse.urlencode({"cmd":"login","ajax":"1","user":LOGIN,"password":PASS,"remember":"1"}).encode()
req = urllib.request.Request(f"{BASE}/ajax.php", data=data,
    headers={"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"})
op.open(req, timeout=20).read()

body = op.open(f"{BASE}/onboarding.php", timeout=30).read().decode("utf-8","replace")
case("Onboarding: no PHP runtime errors", not PHP_ERR_RE.search(body))
markers = [
    "How do you connect with Greece?", "We celebrate every kind of Greek connection",
    "Born and raised in Greece", "Greek heritage / roots", "Philhellene (love Greek culture)",
    "What are you hoping to find?", "start with your intention",
    "A serious relationship", "Just exploring",
    "How important is Greek culture", "connection to your roots matters", "part of who I am", "Not a big factor for me",
    "Do shared values and traditions", "Compatibility goes beyond attraction", "Not very important",
]
hits = sum(1 for m in markers if m in body)
case(f"Onboarding: 16 spec markers", hits == len(markers), f"{hits}/{len(markers)}")
case("Onboarding: progress dots present", "obrd_dot" in body)
case("Onboarding: skip-for-now link", "Skip for now" in body)
case("Onboarding: button-style options (radios visually hidden)",
     "opacity: 0; pointer-events: none" in body)


print(); print("=" * 60); print("5. UPGRADE PAGE — file content (auth+prelaunch-gated, can't HTTP-fetch)"); print("=" * 60)
# We can't HTTP-fetch upgrade.php during prelaunch (it redirects). Instead read
# the deployed file via FTP and grep for the new copy markers. That's an honest
# check that the redesign actually shipped.
ftp2 = ftps()
import io
buf = io.BytesIO()
ftp2.retrbinary("RETR _frameworks/main/impact/upgrade.html", buf.write)
ftp2.quit()
upg = buf.getvalue().decode("utf-8","replace")
new_markers = ["A deeper way to connect", "6-month membership", "Become a member",
               "Send a message to anyone, anytime", "A community, not a marketplace", "Cancel anytime"]
old_markers = ["Founder's Special Offer", "Best Value", "Unlock Full Access"]
for m in new_markers: case(f"Upgrade file has new copy: '{m}'", m in upg)
for m in old_markers: case(f"Upgrade file removed old copy: '{m}'", m not in upg)


print(); print("=" * 60); print("6. CLEANUP"); print("=" * 60)
sql2 = (f"DELETE FROM userinfo WHERE user_id IN (SELECT user_id FROM user WHERE name='{LOGIN}'); "
        f"DELETE FROM user WHERE name='{LOGIN}'; "
        "UPDATE config SET value='Y' WHERE module='options' AND `option`='forced_profile_picture_upload'; "
        "UPDATE config SET value='1' WHERE module='options' AND `option`='min_number_photos_to_use_site';")
with open(os.path.join(os.path.dirname(__file__), "cu.sql"), "w") as f: f.write(sql2)
with open(os.path.join(os.path.dirname(__file__), "cu.sql"), "rb") as fh: ftp.storbinary("STOR cu.sql", fh)
urllib.request.urlopen(f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f=cu.sql", timeout=30).read()
for n in ("_mgs_sqlrun.php", "mk.sql", "cu.sql"):
    try: ftp.delete(n); print(f"  deleted: {n}")
    except: pass
ftp.quit()
for n in ("mk.sql", "cu.sql"):
    p = os.path.join(os.path.dirname(__file__), n)
    if os.path.exists(p): os.unlink(p)


print(); print("=" * 60); print("RESULT")
fails = [r for r in results if not r[0]]
print(f"  passed: {len(results) - len(fails)} / {len(results)}")
if fails:
    print("  failures:")
    for _, lbl, det in fails: print(f"    - {lbl}  {det}")
sys.exit(0 if not fails else 1)
