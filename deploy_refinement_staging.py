"""
Refinement-phase staging deploy.

Uploads:
  - _frameworks/main/impact/help.html       (NEW)
  - _frameworks/main/impact/contact.html    (modified — sectioned + mobile stack)
  - help.php                                (modified — guest/member split)
  - _mgs_sqlrun.php                         (transient SQL runner)
  - refinement_migration.sql                (transient — adds public_visible + position to help_topic)

Then runs the SQL via the runner over HTTPS, smoke-tests the new pages,
and deletes the two transient files.

Reads STAGING_PASS from env (the FTP password). If not set, exits.
Default user: staging@meetgreeksingles.com (chrooted to public_html/staging).
"""
from __future__ import annotations
import ftplib, os, ssl, sys, time, urllib.request
from pathlib import Path

HOST = "meetgreeksingles.com"
USER = "staging@meetgreeksingles.com"
PASSWORD = os.environ.get("STAGING_PASS")
if not PASSWORD:
    sys.exit("ERROR: STAGING_PASS env var not set")

LOCAL_ROOT = Path(__file__).parent / "upstream"
SQL_LOCAL  = Path(__file__).parent / "db" / "refinement_migration.sql"
RUNNER     = Path(__file__).parent / "_mgs_sqlrun.php"

# (local_relative, remote_relative_under_chroot)
UPLOADS_PERSISTENT = [
    ("_frameworks/main/impact/help.html",    "_frameworks/main/impact/help.html"),
    ("_frameworks/main/impact/contact.html", "_frameworks/main/impact/contact.html"),
    ("help.php",                             "help.php"),
]
UPLOADS_TRANSIENT = [
    (str(RUNNER.relative_to(Path(__file__).parent)), "_mgs_sqlrun.php", RUNNER),
    (str(SQL_LOCAL.relative_to(Path(__file__).parent)), "refinement_migration.sql", SQL_LOCAL),
]

BASE_URL  = "https://meetgreeksingles.com/staging"
RUN_URL   = f"{BASE_URL}/_mgs_sqlrun.php?token=429924c65fda7a12ff86d2c73eb838bc&f=refinement_migration.sql"
SMOKE_URLS = [
    (f"{BASE_URL}/help.php",    ["Common questions", "Join to read full answers"]),
    (f"{BASE_URL}/contact.php", ["Send us a message", "Get in touch"]),
]


# --- FTPS reuse helper (Pure-FTPd needs TLS session reuse) ---
class _ReusedSSL(ssl.SSLSocket):
    def unwrap(self):
        pass

class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            session = getattr(self.sock, "session", None)
            conn = self.context.wrap_socket(conn, server_hostname=self.host, session=session)
            conn.__class__ = _ReusedSSL
        return conn, size

def connect():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode   = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(HOST, USER, PASSWORD, timeout=60, context=ctx)
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp

def ensure_dir(ftp, remote_dir):
    if not remote_dir or remote_dir in (".", "/"):
        return
    parts = remote_dir.strip("/").split("/")
    cur = ""
    for p in parts:
        cur = cur + "/" + p if cur else p
        try:
            ftp.cwd("/" + cur)
        except ftplib.error_perm:
            try: ftp.mkd("/" + cur)
            except ftplib.error_perm: pass
    ftp.cwd("/")

def upload(ftp, local_path: Path, remote_path: str):
    ensure_dir(ftp, "/".join(remote_path.split("/")[:-1]))
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)
    print(f"  uploaded: {remote_path}")

def http_get(url, timeout=30) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "deploy/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return -1, str(e)

def main():
    print(f"[1/5] Connecting FTPS to {HOST} as {USER} ...")
    ftp = connect()
    print(f"      pwd: {ftp.pwd()}")

    print(f"[2/5] Uploading {len(UPLOADS_PERSISTENT)} persistent + {len(UPLOADS_TRANSIENT)} transient files ...")
    for local_rel, remote_rel in UPLOADS_PERSISTENT:
        upload(ftp, LOCAL_ROOT / local_rel, remote_rel)
    for _, remote_rel, local_path in UPLOADS_TRANSIENT:
        upload(ftp, local_path, remote_rel)

    print(f"[3/5] Running SQL: {RUN_URL}")
    status, body = http_get(RUN_URL, timeout=60)
    print(f"      HTTP {status}")
    print("      ----- runner output -----")
    print("      " + body.replace("\n", "\n      ").rstrip())
    print("      -------------------------")

    print(f"[4/5] Smoke-testing public pages ...")
    smoke_ok = True
    for url, must_contain in SMOKE_URLS:
        status, body = http_get(url, timeout=30)
        hits = [s for s in must_contain if s in body]
        ok   = status == 200 and len(hits) == len(must_contain)
        smoke_ok = smoke_ok and ok
        marker = "OK " if ok else "FAIL"
        print(f"      [{marker}] {url}  status={status}  found={len(hits)}/{len(must_contain)}")
        if not ok:
            missing = [s for s in must_contain if s not in body]
            print(f"             missing: {missing}")

    print(f"[5/5] Cleaning up transient files ...")
    for _, remote_rel, _ in UPLOADS_TRANSIENT:
        try:
            ftp.delete(remote_rel)
            print(f"      deleted: {remote_rel}")
        except ftplib.error_perm as e:
            print(f"      WARN delete failed for {remote_rel}: {e}")

    ftp.quit()
    print()
    print("DONE." if smoke_ok else "DONE — but smoke tests had failures, review above.")

if __name__ == "__main__":
    main()
