"""
Mobile QA pass — fetches public pages with a mobile User-Agent, checks for
viewport meta, verifies our new pages have responsive media queries, and
detects any auto-redirect to the /m/ legacy mobile theme that would bypass
the polished impact templates.
"""
from __future__ import annotations
import urllib.request, sys, re

UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
             "Mobile/15E148 Safari/604.1")
UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://meetgreeksingles.com"

results = []
def case(label, ok, det=""):
    results.append((ok, label, det))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {det}" if det else ""))

def fetch(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    class NR(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            # capture the redirect target without following
            new = headers.get("Location") or headers.get("location")
            return None  # raise as HTTPError so we can read the Location
    op = urllib.request.build_opener(NR())
    try:
        r = op.open(req, timeout=30)
        return r.status, r.read().decode("utf-8", "replace"), r.headers.get("Location",""), r.url
    except urllib.error.HTTPError as e:
        return e.code, "", e.headers.get("Location", "") if hasattr(e, "headers") else "", ""

PUBLIC = ["/", "/about.php", "/contact.php", "/help.php", "/login", "/info.php?page=term_cond"]

print(f"=== Mobile QA against {BASE} ===\n")

print("1. Mobile UA fetches — does the impact theme render or do we redirect to /m/?")
for path in PUBLIC:
    st, body, loc, _ = fetch(BASE + path, UA_MOBILE)
    redirects_to_m = "/m/" in (loc or "") or "/m/" in body[:1000]
    case(f"  {path}: served by impact theme (no /m/ redirect)", not redirects_to_m,
         f"status={st} loc={loc[:60] if loc else '-'}")

print()
print("2. Viewport meta tag present on every public page")
for path in PUBLIC:
    st, body, _, _ = fetch(BASE + path, UA_DESKTOP)
    has_vp = '<meta name="viewport"' in body or "<meta name='viewport'" in body
    case(f"  {path}: <meta name=viewport>", has_vp)

print()
print("3. Our refined templates contain responsive @media queries")
new_pages = [
    ("/help.php",     ["@media (max-width: 480px)", "bl_help_page"]),
    ("/contact.php",  ["@media (min-width: 768px)", "bl_contact_v2"]),
]
for path, must in new_pages:
    st, body, _, _ = fetch(BASE + path, UA_DESKTOP)
    for m in must:
        case(f"  {path}: contains '{m}'", m in body)

print()
print("4. Subscription page on disk has its responsive @media block")
import io, ftplib, ssl, os
PROD_PASS = os.environ.get("PROD_PASS")
if PROD_PASS:
    class _R(ssl.SSLSocket):
        def unwrap(self): pass
    class F(ftplib.FTP_TLS):
        def ntransfercmd(self, cmd, rest=None):
            c, s = ftplib.FTP.ntransfercmd(self, cmd, rest)
            if self._prot_p:
                sess = getattr(self.sock, "session", None)
                c = self.context.wrap_socket(c, server_hostname=self.host, session=sess); c.__class__=_R
            return c, s
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    ftp = F("meetgreeksingles.com", "everett@meetgreeksingles.com", PROD_PASS, timeout=60, context=ctx)
    ftp.prot_p(); ftp.set_pasv(True)
    for path, must in [
        ("_frameworks/main/impact/upgrade.html",      ["@media (max-width: 700px)", "upg_pricing"]),
        ("_frameworks/main/impact/onboarding.html",   ["@media (max-width: 480px)", "obrd_card"]),
        ("_frameworks/main/impact/events.html",       ["@media (max-width: 480px)", "ev_card"]),
    ]:
        buf = io.BytesIO()
        try:
            ftp.retrbinary(f"RETR {path}", buf.write)
            content = buf.getvalue().decode("utf-8","replace")
            for m in must:
                case(f"  {path}: '{m}'", m in content)
        except Exception as e:
            case(f"  fetch {path}", False, str(e))
    ftp.quit()
else:
    case("  PROD_PASS env var", False, "skipping disk check")

print()
fails = [r for r in results if not r[0]]
print(f"RESULT: {len(results)-len(fails)} / {len(results)} passed")
if fails:
    for _, lbl, det in fails:
        print(f"  - {lbl}  {det}")
sys.exit(0 if not fails else 1)
