"""
Production deploy — push everything currently on staging to live.

Order of operations:
  1. Connect FTPS to production (everett@meetgreeksingles.com).
  2. Upload SQL runner + all 4 migration files to webroot (transient).
  3. Run migrations on production DB in the correct order:
        a. refinement_migration.sql   — help_topic public_visible/position + sample data + help=Y
        b. refinement_footer.sql      — footer reorder positions
        c. _mgs_m3_install.php        — onboarding fields + var_* tables + visibility_scope + user.onboarding_done
        d. _mgs_m3_update.php         — Irene's 2026-04-25 exact wording / Q4 swap
        e. backfill_onboarding.sql    — UPDATE user SET onboarding_done = 1 (so existing accounts skip)
  4. Upload all changed source files.
  5. Smoke-test against meetgreeksingles.com.
  6. Cleanup transient files.

Reads PROD_PASS env var.
"""
from __future__ import annotations
import os, ftplib, ssl, sys, urllib.request, re, time
from pathlib import Path

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("PROD_PASS")
if not PASSWORD: sys.exit("ERROR: PROD_PASS env var not set")

SITE = Path(__file__).parent
LOCAL = SITE / "upstream"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"
BASE  = "https://meetgreeksingles.com"

PERSISTENT = [
    ("help.php",                                              "help.php"),
    ("join2.php",                                             "join2.php"),
    ("onboarding.php",                                        "onboarding.php"),
    ("_include/current/common.class.php",                     "_include/current/common.class.php"),
    ("_include/current/prelaunch.class.php",                  "_include/current/prelaunch.class.php"),
    ("_include/current/onboarding.class.php",                 "_include/current/onboarding.class.php"),
    ("_include/current/visibility.class.php",                 "_include/current/visibility.class.php"),
    ("_frameworks/main/impact/help.html",                     "_frameworks/main/impact/help.html"),
    ("_frameworks/main/impact/contact.html",                  "_frameworks/main/impact/contact.html"),
    ("_frameworks/main/impact/_footer.html",                  "_frameworks/main/impact/_footer.html"),
    ("_frameworks/main/impact/upgrade.html",                  "_frameworks/main/impact/upgrade.html"),
    ("_frameworks/main/impact/index.html",                    "_frameworks/main/impact/index.html"),
    ("_frameworks/main/impact/onboarding.html",               "_frameworks/main/impact/onboarding.html"),
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
    ensure_dir(ftp, "/".join(remote.split("/")[:-1]))
    with open(local, "rb") as fh: ftp.storbinary(f"STOR {remote}", fh)
    print(f"      {remote}")

def http_get(url, timeout=45, follow=True):
    req = urllib.request.Request(url, headers={"User-Agent":"deploy-prod/1.0"})
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(NR())
    else:
        op = urllib.request.build_opener()
    op.addheaders = [("User-Agent","deploy-prod/1.0")]
    try:
        r = op.open(url, timeout=timeout)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else ""), dict(e.headers)

def run_sql(ftp, name, body):
    """Upload an SQL file and run it via _mgs_sqlrun.php."""
    p = SITE / name
    p.write_text(body, encoding="utf-8")
    upload(ftp, p, name)
    url = f"{BASE}/_mgs_sqlrun.php?token={TOKEN}&f={name}"
    status, out, _ = http_get(url)
    print(f"      runner HTTP {status}")
    print("      " + out.strip().replace("\n", "\n      "))
    p.unlink()
    return out

def run_php(ftp, local_php_relsite):
    """Upload and run a one-shot PHP installer."""
    name = Path(local_php_relsite).name
    upload(ftp, SITE / local_php_relsite, name)
    status, out, _ = http_get(f"{BASE}/{name}?token={TOKEN}")
    print(f"      runner HTTP {status}")
    print("      " + out.strip().replace("\n", "\n      "))
    return out


def main():
    print(f"[1/7] FTPS connect to PRODUCTION ({USER})")
    ftp = ftps()
    print(f"      pwd: {ftp.pwd()}")

    print(f"[2/7] Upload SQL runner")
    upload(ftp, SITE / "_mgs_sqlrun.php", "_mgs_sqlrun.php")

    print(f"[3/7] Run migrations on production DB")
    print(f"  -- refinement_migration.sql --")
    run_sql(ftp, "refinement_migration.sql",
            (SITE / "db" / "refinement_migration.sql").read_text(encoding="utf-8"))
    print(f"  -- refinement_footer.sql --")
    run_sql(ftp, "refinement_footer.sql",
            (SITE / "db" / "refinement_footer.sql").read_text(encoding="utf-8"))
    print(f"  -- _mgs_m3_install.php --")
    run_php(ftp, "_mgs_m3_install.php")
    print(f"  -- _mgs_m3_update.php --")
    run_php(ftp, "_mgs_m3_update.php")
    print(f"  -- backfill_onboarding.sql (existing users skip onboarding) --")
    run_sql(ftp, "backfill_onboarding.sql",
            "UPDATE `user` SET `onboarding_done` = 1 WHERE `onboarding_done` = 0;")

    print(f"[4/7] Upload {len(PERSISTENT)} source files to PRODUCTION")
    for local_rel, remote_rel in PERSISTENT:
        upload(ftp, LOCAL / local_rel, remote_rel)

    print(f"[5/7] Smoke production")
    smoke_results = []
    def case(label, ok, det=""):
        smoke_results.append((ok, label, det))
        print(f"      [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {det}" if det else ""))

    php_err_re = re.compile(r"(<b>Fatal error</b>|<b>Parse error</b>|<b>Warning</b>|<b>Notice</b>|"
                            r"Uncaught \w*Exception|Call to undefined function|pp_installator)")

    public = [
        ("/",                      ["preparing for our official launch", "Find the Greek Connection"]),
        ("/about.php",             []),
        ("/contact.php",           ["Send us a message", "Get in touch"]),
        ("/help.php",              ["Common questions about Meet Greek Singles"]),
        ("/login",                 ["Welcome Back"]),
        ("/info.php?page=term_cond", []),
        ("/info.php?page=priv_policy", []),
    ]
    for path, must in public:
        st, body, _ = http_get(f"{BASE}{path}")
        err = php_err_re.search(body)
        if err: case(f"GET {path}", False, f"PHP issue {err.group(0)}"); continue
        if st != 200: case(f"GET {path}", False, f"status={st}"); continue
        miss = [m for m in must if m not in body]
        case(f"GET {path}", not miss, f"size={len(body)}" + (f" missing {miss}" if miss else ""))

    # Footer order on the homepage
    st, body, _ = http_get(f"{BASE}/")
    m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
    if m:
        items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
        expected = ["About", "Terms & Conditions", "Privacy Policy", "Questions & Answers", "Contact us"]
        case(f"Footer order = {expected}", items == expected, f"got {items}")

    # Pre-launch gate sanity (a couple of blocked URLs)
    for path in ("/search_results", "/messages.php", "/upgrade.php"):
        st, _, hdrs = http_get(f"{BASE}{path}", follow=False)
        loc = hdrs.get("Location", "")
        case(f"BLOCKED {path}", st == 302 and "__plfb=1" in loc, f"loc={loc[:60]}")

    print(f"[6/7] Cleanup transient files")
    for n in ("_mgs_sqlrun.php", "_mgs_m3_install.php", "_mgs_m3_update.php",
              "refinement_migration.sql", "refinement_footer.sql", "backfill_onboarding.sql"):
        try: ftp.delete(n); print(f"      deleted {n}")
        except ftplib.error_perm: pass

    ftp.quit()

    fails = [r for r in smoke_results if not r[0]]
    print(f"[7/7] RESULT: {len(smoke_results)-len(fails)} / {len(smoke_results)} passed")
    if fails:
        print("      failures:")
        for _, lbl, det in fails:
            print(f"        - {lbl}  {det}")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
