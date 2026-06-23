"""
Deploy join2.html column-overlap fix to production.

Run (PowerShell):
    $env:PROD_PASS = '<your FTPS password>'
    python d:\MyProjects\Irene\Irene\Irene\site\deploy_join2_2026_06_10.py

Optional — try alternate FTP user:
    $env:PROD_USER = 'everett@meetgreeksingles.com'
"""
import os
import sys
import ftplib
import ssl
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
DEFAULT_USER = "Final@meetgreeksingles.com"
REMOTE = "_frameworks/main/impact/join2.html"
LOCAL = r"d:\MyProjects\Irene\Irene\Irene\site\upstream\_frameworks\main\impact\join2.html"


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


def upload(password, user):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Connecting to {HOST} as {user} ...")
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, timeout=60)
    ftp.login(user, password)
    ftp.prot_p()
    ftp.set_pasv(True)

    parts = REMOTE.strip("/").split("/")
    name = parts.pop()
    dirpath = "/".join(parts)
    for p in dirpath.split("/"):
        try:
            ftp.mkd(p)
        except ftplib.error_perm:
            pass
    ftp.cwd("/" + dirpath if dirpath else "/")

    print(f"Uploading -> /{REMOTE}")
    with open(LOCAL, "rb") as f:
        ftp.storbinary(f"STOR {name}", f)
    ftp.quit()
    print("Upload complete.")


def smoke():
    url = f"https://{HOST}/join2"
    req = urllib.request.Request(url, headers={"User-Agent": "deploy-join2/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    ok = "mgs_join2_shell .card_join .bl" in body or "Beat legacy card.css" in body
    print(f"Smoke: GET {url} -> HTTP {resp.status}")
    print(f"  overlap fix present: {ok}")
    return ok


def main():
    password = os.environ.get("PROD_PASS")
    if not password:
        print("ERROR: set $env:PROD_PASS before running.")
        sys.exit(1)
    user = os.environ.get("PROD_USER", DEFAULT_USER)
    if not os.path.exists(LOCAL):
        print(f"ERROR: missing {LOCAL}")
        sys.exit(1)

    upload(password, user)
    try:
        if smoke():
            print("\nDEPLOY OK — test at https://meetgreeksingles.com/join2 (Ctrl+F5)")
        else:
            print("\nWARN — uploaded but smoke check did not find fix markers.")
    except Exception as e:
        print(f"\nWARN — could not smoke-test: {e}")
        print("Verify manually: https://meetgreeksingles.com/join2")


if __name__ == "__main__":
    main()
