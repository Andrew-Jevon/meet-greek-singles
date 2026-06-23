"""
Deploy 2026-05-01 — three-part scope:
  1. home_city user_var + userinfo column + register/search wiring
  2. Greek regions cleanup (replace geo_state with 13 modern admin regions)
  3. Per-page <title> + meta description override

Order is critical:
  Phase A: upload + run installer scripts (DB migrations), then delete them
  Phase B: upload code + template files
  Phase C: upload + hit OPcache reset, then delete it (PHP edits won't take
           effect otherwise because OPcache caches compiled bytecode)
  Phase D: curl-based smoke checks

Run from the project root:
  $env:MGS_PASS='<production FTPS password from credentials.md>'; python site/_deploy_2026_05_01.py
"""
from __future__ import annotations
import ftplib, os, ssl, sys, time, urllib.request

# Windows: force UTF-8 stdout so we can print Greek/Unicode from the
# install scripts' audit logs without 'charmap' encode errors.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST  = "meetgreeksingles.com"
USER  = "everett@meetgreeksingles.com"
TOKEN = "429924c65fda7a12ff86d2c73eb838bc"

PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD:
    sys.exit("ERROR: MGS_PASS env var not set")


# Pure-FTPd needs control->data TLS session reuse.
class _ReusedSSL(ssl.SSLSocket):
    def unwrap(self): pass

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
    ctx.verify_mode    = ssl.CERT_NONE
    f = FTP_TLS_Reuse(context=ctx)
    f.connect(HOST, 21, timeout=60)
    f.login(USER, PASSWORD)
    f.prot_p()
    f.set_pasv(True)
    return f


def stor(f, local_path, remote_path):
    print(f"  STOR  {local_path}  ->  {remote_path}")
    # Always start from /, then walk into the file's parent directory.
    # If the file is at root (no '/' in remote_path), skip the walk entirely.
    f.cwd("/")
    parts = remote_path.strip("/").split("/")
    name = parts.pop()  # basename
    for part in parts:
        if not part: continue
        try:
            f.cwd(part)
        except ftplib.error_perm:
            try: f.mkd(part)
            except ftplib.error_perm: pass
            f.cwd(part)
    with open(local_path, "rb") as fp:
        f.storbinary(f"STOR {name}", fp)


def delete_remote(f, remote_path):
    print(f"  DELE  {remote_path}")
    f.cwd("/")
    name = remote_path.lstrip("/")
    try:
        f.delete(name)
    except ftplib.error_perm as e:
        # Some FTP servers want a fresh session for DELE if the file was
        # just executed via HTTP. Retry once with a new connection.
        print(f"        first attempt — {e}; retrying with fresh connection")
        try:
            f2 = connect()
            try:
                f2.cwd("/")
                f2.delete(name)
                print(f"        retry OK")
            finally:
                f2.quit()
        except Exception as e2:
            print(f"        retry failed — {e2}")


def hit(url):
    print(f"  GET   {url}")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, context=ctx, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print("        " + body.replace("\n", "\n        "))
            return body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"        HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print(f"        ERR: {e}")
        return None


# ----------------------------------------------------------------------------
# Phase A — installer scripts (DB migrations)
# ----------------------------------------------------------------------------
INSTALLERS = [
    ("site/_mgs_homecity_install.php",  "_mgs_homecity_install.php"),
    ("site/_mgs_greek_regions.php",     "_mgs_greek_regions.php"),
]

# ----------------------------------------------------------------------------
# Phase B — code + template files
# ----------------------------------------------------------------------------
CODE_FILES = [
    ("site/upstream/_include/current/page_titles.class.php",
        "_include/current/page_titles.class.php"),
    ("site/upstream/_include/current/common.class.php",
        "_include/current/common.class.php"),
    ("site/upstream/_include/current/cjoinform.class.php",
        "_include/current/cjoinform.class.php"),
    ("site/upstream/_include/current/cjoinfinal.class.php",
        "_include/current/cjoinfinal.class.php"),
    ("site/upstream/search_results.php",
        "search_results.php"),
    ("site/upstream/_frameworks/main/impact/register.html",
        "_frameworks/main/impact/register.html"),
    ("site/upstream/_frameworks/main/impact/_list_users_filter.html",
        "_frameworks/main/impact/_list_users_filter.html"),
]

OPCACHE = ("site/_mgs_opc.php", "_mgs_opc.php")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    proj = os.path.dirname(here)
    os.chdir(proj)

    print("=" * 70)
    print("Phase A — DB migrations (installer scripts)")
    print("=" * 70)
    f = connect()
    try:
        for local, remote in INSTALLERS:
            stor(f, local, remote)
    finally:
        f.quit()

    print("\n  Running home_city installer...")
    hit(f"https://{HOST}/_mgs_homecity_install.php?token={TOKEN}")

    print("\n  Running Greek regions cleanup...")
    hit(f"https://{HOST}/_mgs_greek_regions.php?token={TOKEN}")

    print("\n  Cleaning up installer scripts...")
    f = connect()
    try:
        for _, remote in INSTALLERS:
            delete_remote(f, remote)
    finally:
        f.quit()

    print("\n" + "=" * 70)
    print("Phase B — code + template uploads")
    print("=" * 70)
    f = connect()
    try:
        for local, remote in CODE_FILES:
            stor(f, local, remote)
    finally:
        f.quit()

    print("\n" + "=" * 70)
    print("Phase C — OPcache reset (PHP edits visible)")
    print("=" * 70)
    f = connect()
    try:
        stor(f, OPCACHE[0], OPCACHE[1])
    finally:
        f.quit()

    print("\n  Resetting OPcache...")
    hit(f"https://{HOST}/_mgs_opc.php?token={TOKEN}")

    print("\n  Removing OPcache reset endpoint...")
    f = connect()
    try:
        delete_remote(f, OPCACHE[1])
    finally:
        f.quit()

    print("\n" + "=" * 70)
    print("Phase D — smoke checks")
    print("=" * 70)
    cb = int(time.time())
    print("\n  Homepage title:")
    body = hit(f"https://{HOST}/?nocache={cb}")
    if body and "<title>" in body:
        title = body.split("<title>")[1].split("</title>")[0]
        print(f"        => '{title}'")

    cb = int(time.time())
    print("\n  Join page title:")
    body = hit(f"https://{HOST}/join?nocache={cb}")
    if body and "<title>" in body:
        title = body.split("<title>")[1].split("</title>")[0]
        print(f"        => '{title}'")

    cb = int(time.time())
    print("\n  About page title:")
    body = hit(f"https://{HOST}/about.php?nocache={cb}")
    if body and "<title>" in body:
        title = body.split("<title>")[1].split("</title>")[0]
        print(f"        => '{title}'")

    cb = int(time.time())
    print("\n  Join page — home_city input present?")
    body = hit(f"https://{HOST}/join?nocache={cb}")
    if body:
        print(f"        name=\"home_city\" present: {'name=\"home_city\"' in body}")
        print(f"        legacy name=\"city\" gone:    {'name=\"city\"' not in body}")

    print("\nDONE")

if __name__ == "__main__":
    main()
