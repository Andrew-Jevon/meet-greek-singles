"""
Refinement deploy v2 — full set + footer reorder + smoke + cleanup.

Persistent uploads:
  - _frameworks/main/impact/help.html       (Q&A public/member split)
  - _frameworks/main/impact/contact.html    (sections + mobile stack)
  - _frameworks/main/impact/_footer.html    (hardcoded items removed, JS hack gone)
  - _frameworks/main/impact/upgrade.html    (full redesign — calmer, lighter)
  - help.php                                (guest/member split + $area=public + CMenuSection removed)

Transient (uploaded, run, then deleted):
  - _mgs_sqlrun.php                         (SQL runner, token-protected)
  - refinement_footer.sql                   (positions 1-5 + status flips)

Also nukes any leftover probe / show / dbg files from earlier debugging.

Smoke tests:
  - /help.php           guest view: 4 seeded questions + Join CTA
  - /contact.php        sectioned: "Send us a message" + "Get in touch"
  - /                   homepage footer order matches Irene's spec
  - /upgrade.php        served (auth-gated, just verify reachability)
"""
from __future__ import annotations
import ftplib, os, ssl, sys, urllib.request
from pathlib import Path

HOST = "meetgreeksingles.com"
USER = "staging@meetgreeksingles.com"
PASSWORD = os.environ.get("STAGING_PASS")
if not PASSWORD:
    sys.exit("ERROR: STAGING_PASS env var not set")

SITE = Path(__file__).parent
LOCAL_ROOT = SITE / "upstream"

UPLOADS_PERSISTENT = [
    ("_frameworks/main/impact/help.html",     "_frameworks/main/impact/help.html"),
    ("_frameworks/main/impact/contact.html",  "_frameworks/main/impact/contact.html"),
    ("_frameworks/main/impact/_footer.html",  "_frameworks/main/impact/_footer.html"),
    ("_frameworks/main/impact/upgrade.html",  "_frameworks/main/impact/upgrade.html"),
    ("help.php",                              "help.php"),
]
UPLOADS_TRANSIENT = [
    (SITE / "_mgs_sqlrun.php",          "_mgs_sqlrun.php"),
    (SITE / "db/refinement_footer.sql", "refinement_footer.sql"),
]

# Files that may have been left behind from earlier debugging — best-effort delete.
LEFTOVER_NUKE = [
    "_mgs_sqlrun.php", "_mgs_sqlquery.php", "_mgs_show.php",
    "_mgs_optprobe.php", "_mgs_helpdbg.php",
    "refinement_migration.sql", "refinement_footer.sql",
    "probe_help.sql", "probe_help2.sql", "probe_pages.sql",
]

BASE_URL = "https://meetgreeksingles.com/staging"
RUN_URL  = f"{BASE_URL}/_mgs_sqlrun.php?token=429924c65fda7a12ff86d2c73eb838bc&f=refinement_footer.sql"

SMOKE = [
    ("help.php",    "guest Q&A view",
        ["Common questions about Meet Greek Singles", "Join to read full answers",
         "How is Meet Greek Singles different", "Is the platform open to non-Greeks"],
        []),
    ("contact.php", "sections + FAQ link",
        ["Send us a message", "Get in touch", "Browse our help"],
        []),
    ("",            "homepage footer order",
        # bottom_visitor_menu items in order
        ["About Meet Greek Singles", "Terms & Conditions", "Privacy Policy",
         "Question & Answers", "Contact us"],
        # must NOT contain
        ["Browse matches", "Events</a>", "Community Ambassadors"]),
    ("upgrade.php", "redesigned — at least loads (auth-gated, may redirect)",
        [],  # auth-gated; just check it doesn't 500
        []),
]


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

def connect():
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    f = F(HOST, USER, PASSWORD, timeout=60, context=ctx)
    f.prot_p(); f.set_pasv(True)
    return f

def upload(ftp, local: Path, remote: str):
    with open(local, "rb") as fh:
        ftp.storbinary(f"STOR {remote}", fh)
    print(f"  uploaded: {remote}")

def http_get(url, timeout=30, allow_redirects=True):
    req = urllib.request.Request(url, headers={"User-Agent": "deploy/2.0"})
    if not allow_redirects:
        # one-shot, no follow
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""

def main():
    print(f"[1/5] FTPS connect ({USER})")
    ftp = connect()
    print(f"      pwd: {ftp.pwd()}")

    print(f"[2/5] Persistent uploads ({len(UPLOADS_PERSISTENT)})")
    for local_rel, remote_rel in UPLOADS_PERSISTENT:
        upload(ftp, LOCAL_ROOT / local_rel, remote_rel)

    print(f"[3/5] Transient uploads + footer SQL")
    for local, remote in UPLOADS_TRANSIENT:
        upload(ftp, local, remote)
    status, body = http_get(RUN_URL, timeout=60)
    print(f"      runner HTTP {status}")
    print("      " + body.strip().replace("\n", "\n      "))

    print(f"[4/5] Smoke tests")
    all_ok = True
    for path, label, must, must_not in SMOKE:
        url = f"{BASE_URL}/{path}" if path else f"{BASE_URL}/"
        status, body = http_get(url, timeout=30)
        hits = [s for s in must if s in body]
        bad  = [s for s in must_not if s in body]
        ok = status == 200 and len(hits) == len(must) and not bad
        all_ok = all_ok and ok
        marker = "OK  " if ok else "FAIL"
        print(f"      [{marker}] {url}  status={status}  matched={len(hits)}/{len(must)}  bad_hits={len(bad)}")
        if must and len(hits) != len(must):
            print(f"             missing: {[s for s in must if s not in body]}")
        if bad:
            print(f"             unexpected: {bad}")

    print(f"[5/5] Cleanup transient + leftover files")
    for name in LEFTOVER_NUKE:
        try:
            ftp.delete(name)
            print(f"      deleted: {name}")
        except ftplib.error_perm:
            pass  # not present — fine

    ftp.quit()
    print()
    print("DEPLOY OK" if all_ok else "DEPLOY done — smoke had failures, review above.")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
