"""
Deploy — 2026-06-01 homepage mockup redesign.

Uploads:
  _frameworks/main/impact/index.html   — hero, features, early-join CTA
  _frameworks/main/impact/_header.html   — nav active-state style

HTML only — no OPcache reset required.

Run:
    $env:PROD_PASS = '<production FTPS password>'
    python d:\MyProjects\Irene\Irene\Irene\site\deploy_2026_06_01.py
"""

import sys
import os
import ftplib
import ssl
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


HOST = "meetgreeksingles.com"
USER = "Final@meetgreeksingles.com"
REMOTE_ROOT = "/"
LOCAL_UPSTREAM = r"d:\MyProjects\Irene\Irene\Irene\site\upstream"

FILES = [
    "_frameworks/main/impact/index.html",
    "_frameworks/main/impact/_header.html",
    "_frameworks/main/impact/_footer.html",
    "_frameworks/main/impact/login.html",
    "_frameworks/main/impact/register.html",
    "_frameworks/main/impact/join2.html",
    "_files/banner/ChangedBackgroundImage.png",
]


def ensure_dir(ftp, path):
    if not path:
        return
    cur = ""
    for p in path.split("/"):
        cur = cur + "/" + p if cur else p
        try:
            ftp.mkd(cur)
        except ftplib.error_perm:
            pass


def upload(ftp, local_path, remote_rel):
    parts = remote_rel.strip("/").split("/")
    name = parts.pop()
    if parts:
        ensure_dir(ftp, "/".join(parts))
        ftp.cwd(REMOTE_ROOT + "/" + "/".join(parts))
    else:
        ftp.cwd(REMOTE_ROOT)
    print(f"  -> {remote_rel}")
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {name}", f)
    ftp.cwd(REMOTE_ROOT)


def smoke():
    url = f"https://{HOST}/"
    req = urllib.request.Request(url, headers={"User-Agent": "deploy-2026-06-01/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        code = resp.status
        body = resp.read().decode("utf-8", errors="replace")
    join_url = f"https://{HOST}/join"
    req2 = urllib.request.Request(join_url, headers={"User-Agent": "deploy-2026-06-01/1.0"})
    with urllib.request.urlopen(req2, timeout=30) as resp2:
        join_body = resp2.read().decode("utf-8", errors="replace")
        join_code = resp2.status
    ok_home = code == 200 and "mgs_hero_layout" in body
    ok_join = join_code == 200 and "mgs_join_layout" in join_body and "ChangedBackgroundImage" in join_body
    join2_url = f"https://{HOST}/join2"
    req3 = urllib.request.Request(join2_url, headers={"User-Agent": "deploy-2026-06-01/1.0"})
    try:
        with urllib.request.urlopen(req3, timeout=30) as resp3:
            join2_body = resp3.read().decode("utf-8", errors="replace")
            join2_code = resp3.status
    except Exception:
        join2_code = 0
        join2_body = ""
    ok_join2 = join2_code == 200 and "mgs_join2_hero" in join2_body and "Complete Your Profile" in join2_body
    print(f"\nSmoke: GET {url} -> HTTP {code} (homepage: {ok_home})")
    print(f"Smoke: GET {join_url} -> HTTP {join_code} (register: {ok_join})")
    print(f"Smoke: GET {join2_url} -> HTTP {join2_code} (join2: {ok_join2})")
    return ok_home and ok_join and ok_join2


def main():
    password = os.environ.get("PROD_PASS")
    if not password:
        print("ERROR: set $env:PROD_PASS before running this script.")
        sys.exit(1)

    print(f"Connecting to {HOST} ...")
    ftp = FTP_TLS_Reuse(HOST)
    ftp.login(USER, password)
    ftp.prot_p()
    ftp.cwd(REMOTE_ROOT)
    print(f"Logged in. cwd={REMOTE_ROOT}\n")

    print("=== Uploading homepage mockup files ===")
    for rel in FILES:
        local = os.path.join(LOCAL_UPSTREAM, rel.replace("/", os.sep))
        if not os.path.exists(local):
            print(f"  SKIP — missing: {local}")
            sys.exit(1)
        upload(ftp, local, rel)

    ftp.quit()
    print("\nUpload complete.\n")

    try:
        if smoke():
            print("\nDEPLOY OK — homepage shows new content.")
        else:
            print("\nWARN — upload succeeded but smoke check did not find expected strings.")
            sys.exit(2)
    except Exception as e:
        print(f"\nWARN — could not run smoke check: {e}")
        print("Verify manually: https://meetgreeksingles.com/")


if __name__ == "__main__":
    main()
