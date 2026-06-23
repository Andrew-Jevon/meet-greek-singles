"""Finish 2026-05-09 deploy — upload _mgs_opc.php (it wasn't on prod), reset
opcache, then run the smoke phase again with a fresh request."""
from __future__ import annotations
import os, ftplib, ssl, sys, urllib.request, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("PROD_PASS")
if not PASSWORD: sys.exit("ERROR: PROD_PASS env var not set")

SITE  = Path(__file__).parent
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
BASE  = "https://meetgreeksingles.com"

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
    f = F(HOST, USER, PASSWORD, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True); return f

def upload(ftp, local: Path, remote: str):
    with open(local, "rb") as fh: ftp.storbinary(f"STOR {remote}", fh)
    print(f"  uploaded {remote}")

def http_get(url, timeout=45, follow=True):
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(NR())
    else:
        op = urllib.request.build_opener()
    op.addheaders = [("User-Agent","post-deploy/1.0")]
    try:
        r = op.open(url, timeout=timeout)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else ""), dict(e.headers)

def main():
    print(f"[1/4] FTPS connect")
    ftp = ftps()

    print(f"[2/4] Upload _mgs_opc.php")
    upload(ftp, SITE / "_mgs_opc.php", "_mgs_opc.php")

    print(f"[3/4] Reset opcache (no follow, plain text expected)")
    st, body, hdrs = http_get(f"{BASE}/_mgs_opc.php?token={TOKEN}", follow=False)
    print(f"  HTTP {st}  Content-Type={hdrs.get('Content-Type','?')}")
    print(f"  Location={hdrs.get('Location','(none)')}")
    print(f"  body[:500]={body[:500]!r}")

    print(f"[4/4] Smoke (post-opcache-reset)")
    smoke = []
    def case(label, ok, det=""):
        smoke.append((ok, label, det))
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {det}" if det else ""))

    php_err_re = re.compile(r"(<b>Fatal error</b>|<b>Parse error</b>|<b>Warning</b>|<b>Notice</b>|"
                            r"Uncaught \w*Exception|Call to undefined function|pp_installator)")

    public = [
        ("/",                          ["preparing for our official launch", "Find the Greek Connection"]),
        ("/about.php",                 []),
        ("/contact.php",               ["Send us a message"]),
        ("/help.php",                  ["Common questions about Meet Greek Singles"]),
        ("/login",                     ["Welcome Back"]),
        ("/email_not_confirmed.php",   []),
        ("/join.php",                  []),
        ("/join2.php",                 []),
    ]
    for path, must in public:
        st, body, _ = http_get(f"{BASE}{path}")
        err = php_err_re.search(body)
        if err: case(f"GET {path}", False, f"PHP issue {err.group(0)}"); continue
        if st != 200: case(f"GET {path}", False, f"status={st}"); continue
        miss = [m for m in must if m not in body]
        case(f"GET {path}", not miss, f"size={len(body)}" + (f" missing {miss}" if miss else ""))

    # /join2.php — confirm none of the 6 question titles still leak
    st, body, _ = http_get(f"{BASE}/join2.php")
    old = ["What's your hair colour", "What is your hair colour", "What's your hair color",
           "Hair colour", "Hair color",
           "i_am_here_to", "What are you looking for", "I am here to",
           "weight", "How tall", "height",
           "Where are you from", "country of origin", "orign",
           "What's your status", "marital status"]
    leaked = [q for q in old if q.lower() in body.lower()]
    case("/join2.php has no leaked yes/no question text", not leaked, f"leaked={leaked}" if leaked else "")

    # Footer order check
    st, body, _ = http_get(f"{BASE}/")
    m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
    if m:
        items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
        expected = ["About", "Terms & Conditions", "Privacy Policy", "Questions & Answers", "Contact us"]
        case(f"Footer order = {expected}", items == expected, f"got {items}")

    # Pre-launch gate sanity
    for path in ("/search_results", "/messages.php", "/upgrade.php"):
        st, _, hdrs = http_get(f"{BASE}{path}", follow=False)
        loc = hdrs.get("Location", "")
        case(f"BLOCKED {path}", st == 302 and "__plfb=1" in loc, f"loc={loc[:60]}")

    ftp.quit()

    fails = [r for r in smoke if not r[0]]
    print(f"\nRESULT: {len(smoke)-len(fails)} / {len(smoke)} passed")
    for ok, lbl, det in smoke:
        if not ok: print(f"  - {lbl}  {det}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
