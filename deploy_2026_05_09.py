"""
2026-05-09 deploy — two fixes for Irene:
  A) Clear question_title + answer JSON on 6 user_var entries (hair / status /
     i_am_here_to / weight / orign / height) so Chameleon's encoded core no
     longer renders the yes/no card-flip step on /join2 (duplicates removed).
     Also clears active_code on the 18 existing unconfirmed test accounts so
     the new EmailVerification gate doesn't retroactively lock them out.

  B) Deploy EmailVerification gate (new class + hook in common.class.php) so
     newly-registered users with a non-empty active_code get bounced to
     /email_not_confirmed.php until they click the link in their email.

Order of operations:
  1. FTPS connect to prod
  2. Upload + run + delete one-shot install script (A)
  3. Upload new email_verification.class.php
  4. Upload modified common.class.php (with the EmailVerification hook)
  5. Hit opcache-reset endpoint so the new code is picked up
  6. Smoke /, /join2.php, /email_not_confirmed.php, pre-launch 302s, footer
  7. Report

Reads PROD_PASS env var.
"""
from __future__ import annotations
import os, ftplib, ssl, sys, urllib.request, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("PROD_PASS")
if not PASSWORD: sys.exit("ERROR: PROD_PASS env var not set")

SITE  = Path(__file__).parent
LOCAL = SITE / "upstream"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
BASE  = "https://meetgreeksingles.com"

PERSISTENT = [
    ("_include/current/email_verification.class.php", "_include/current/email_verification.class.php"),
    ("_include/current/common.class.php",             "_include/current/common.class.php"),
]

# --- FTPS reuse boilerplate ---
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

def ensure_dir(ftp, dpath):
    if not dpath or dpath in (".", "/"): return
    cur = ""
    for p in dpath.strip("/").split("/"):
        cur = cur + "/" + p if cur else p
        try: ftp.cwd("/" + cur)
        except ftplib.error_perm:
            try: ftp.mkd("/" + cur)
            except ftplib.error_perm: pass
    ftp.cwd("/")

def upload(ftp, local: Path, remote: str):
    parts = remote.strip("/").split("/")
    parts.pop()  # drop filename — only ensure the directory exists
    ensure_dir(ftp, "/".join(parts))
    with open(local, "rb") as fh: ftp.storbinary(f"STOR {remote}", fh)
    print(f"      {remote}")

def http_get(url, timeout=45, follow=True):
    req = urllib.request.Request(url, headers={"User-Agent":"deploy-2026-05-09/1.0"})
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(NR())
    else:
        op = urllib.request.build_opener()
    op.addheaders = [("User-Agent","deploy-2026-05-09/1.0")]
    try:
        r = op.open(url, timeout=timeout)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else ""), dict(e.headers)

def run_php(ftp, local_php_relsite, remote_name=None):
    name = remote_name or Path(local_php_relsite).name
    upload(ftp, SITE / local_php_relsite, name)
    status, out, _ = http_get(f"{BASE}/{name}?token={TOKEN}")
    print(f"      runner HTTP {status}")
    print("      " + out.strip().replace("\n", "\n      "))
    return status, out

def main():
    print(f"[1/6] FTPS connect to PRODUCTION ({USER})")
    ftp = ftps()
    print(f"      pwd: {ftp.pwd()}")

    print(f"[2/6] Run install script (clear question_title + clear active_code)")
    status, out = run_php(ftp, "_mgs_install_2026_05_09.php")
    if status != 200 or "DONE" not in out:
        print("      ! install script did NOT report DONE — aborting deploy")
        ftp.quit(); sys.exit(2)

    print(f"[3/6] Delete install script (one-shot)")
    try: ftp.delete("_mgs_install_2026_05_09.php"); print("      deleted _mgs_install_2026_05_09.php")
    except ftplib.error_perm as e: print(f"      ! delete failed: {e}")

    print(f"[4/6] Upload {len(PERSISTENT)} source files")
    for local_rel, remote_rel in PERSISTENT:
        upload(ftp, LOCAL / local_rel, remote_rel)

    print(f"[5/6] Reset opcache")
    status, out, _ = http_get(f"{BASE}/_mgs_opc.php?token={TOKEN}")
    print(f"      runner HTTP {status}")
    print("      " + out.strip().replace("\n", "\n      "))

    print(f"[6/6] Smoke production")
    smoke = []
    def case(label, ok, det=""):
        smoke.append((ok, label, det))
        print(f"      [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {det}" if det else ""))

    php_err_re = re.compile(r"(<b>Fatal error</b>|<b>Parse error</b>|<b>Warning</b>|<b>Notice</b>|"
                            r"Uncaught \w*Exception|Call to undefined function|pp_installator)")

    public = [
        ("/",                          ["preparing for our official launch", "Find the Greek Connection"]),
        ("/about.php",                 []),
        ("/contact.php",               ["Send us a message", "Get in touch"]),
        ("/help.php",                  ["Common questions about Meet Greek Singles"]),
        ("/login",                     ["Welcome Back"]),
        ("/info.php?page=term_cond",   []),
        ("/info.php?page=priv_policy", []),
        ("/email_not_confirmed.php",   []),
    ]
    for path, must in public:
        st, body, _ = http_get(f"{BASE}{path}")
        err = php_err_re.search(body)
        if err: case(f"GET {path}", False, f"PHP issue {err.group(0)}"); continue
        if st != 200: case(f"GET {path}", False, f"status={st}"); continue
        miss = [m for m in must if m not in body]
        case(f"GET {path}", not miss, f"size={len(body)}" + (f" missing {miss}" if miss else ""))

    # /join2.php — fix A — no question_title cards left to render. Anonymous
    # GET hits the gate and gets the form; we just want it to be 200 + clean.
    st, body, _ = http_get(f"{BASE}/join2.php")
    err = php_err_re.search(body)
    if err:
        case("GET /join2.php", False, f"PHP issue {err.group(0)}")
    else:
        case(f"GET /join2.php (status={st}, size={len(body)})", st == 200)
        # And that none of the 6 question titles still bleed through.
        old_q_strings = ["What's your hair colour", "What's your status", "I'm here to",
                         "What's your weight", "Where are you from", "What's your height"]
        leaked = [q for q in old_q_strings if q in body]
        case("/join2.php has no leaked yes/no question text", not leaked, f"leaked={leaked}" if leaked else "")

    # Footer order on the homepage
    st, body, _ = http_get(f"{BASE}/")
    m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
    if m:
        items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
        expected = ["About", "Terms & Conditions", "Privacy Policy", "Questions & Answers", "Contact us"]
        case(f"Footer order = {expected}", items == expected, f"got {items}")

    # Pre-launch gate sanity (still 302s blocked URLs to ?__plfb=1)
    for path in ("/search_results", "/messages.php", "/upgrade.php"):
        st, _, hdrs = http_get(f"{BASE}{path}", follow=False)
        loc = hdrs.get("Location", "")
        case(f"BLOCKED {path}", st == 302 and "__plfb=1" in loc, f"loc={loc[:60]}")

    ftp.quit()

    fails = [r for r in smoke if not r[0]]
    print(f"\nRESULT: {len(smoke)-len(fails)} / {len(smoke)} passed")
    if fails:
        print("      failures:")
        for _, lbl, det in fails:
            print(f"        - {lbl}  {det}")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
