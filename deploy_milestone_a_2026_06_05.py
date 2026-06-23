"""
Deploy script — Milestone A (Polish Bundle), 2026-06-05.

Uploads two Impact theme templates that contain the eight Polish Bundle
improvements from Irene's review email of 2026-06-04:

    _frameworks/main/impact/register.html
    _frameworks/main/impact/join2.html

Before uploading, downloads the current production copies of those two
files into _backup/2026-06-05_milestone_a/ so rollback is one command if
needed. HTML-only — no OPcache reset, no probe, no PHP changes.

Run:
    $env:PROD_PASS = '<production FTPS password>'
    python d:\\MyProjects\\Irene\\Irene\\Irene\\site\\deploy_milestone_a_2026_06_05.py

Rollback (if anything looks wrong on the live site):
    Set $env:PROD_PASS, then re-run with --rollback:
    python d:\\MyProjects\\Irene\\Irene\\Irene\\site\\deploy_milestone_a_2026_06_05.py --rollback
"""
import sys, os, ftplib, ssl, io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    """Pure-FTPd reuses the SSL session for the data channel."""
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


HOST        = "meetgreeksingles.com"
USER        = "everett@meetgreeksingles.com"
REMOTE_ROOT = "/"  # FTPS user is chrooted — / IS the webroot

LOCAL_UPSTREAM = r"d:\MyProjects\Irene\Irene\Irene\site\upstream"
BACKUP_DIR     = r"d:\MyProjects\Irene\Irene\Irene\_backup\2026-06-05_milestone_a"

FILES = [
    "_frameworks/main/impact/register.html",
    "_frameworks/main/impact/join2.html",
]


def open_ftp(password):
    print(f"Connecting to {HOST} ...")
    ftp = FTP_TLS_Reuse(HOST)
    ftp.login(USER, password)
    ftp.prot_p()
    ftp.cwd(REMOTE_ROOT)
    print(f"Logged in. cwd={REMOTE_ROOT}\n")
    return ftp


def backup_one(ftp, remote_rel):
    parts = remote_rel.strip("/").split("/")
    name = parts.pop()
    dirpath = "/".join(parts)
    ftp.cwd(REMOTE_ROOT + dirpath if dirpath else REMOTE_ROOT)
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {name}", buf.write)
    local = os.path.join(BACKUP_DIR, remote_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local, "wb") as f:
        f.write(buf.getvalue())
    ftp.cwd(REMOTE_ROOT)
    return len(buf.getvalue())


def upload_one(ftp, local_path, remote_rel):
    parts = remote_rel.strip("/").split("/")
    name = parts.pop()
    dirpath = "/".join(parts)
    ftp.cwd(REMOTE_ROOT + dirpath if dirpath else REMOTE_ROOT)
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {name}", f)
    ftp.cwd(REMOTE_ROOT)


def deploy(password):
    ftp = open_ftp(password)

    print(f"=== Step 1: backup current production files to {BACKUP_DIR} ===")
    for rel in FILES:
        size = backup_one(ftp, rel)
        print(f"  <- {rel}  ({size} bytes)")

    print("\n=== Step 2: upload Milestone A versions ===")
    for rel in FILES:
        local = os.path.join(LOCAL_UPSTREAM, rel.replace("/", os.sep))
        if not os.path.exists(local):
            print(f"  ABORT — local missing: {local}")
            ftp.quit()
            sys.exit(1)
        upload_one(ftp, local, rel)
        print(f"  -> {rel}")

    ftp.quit()

    print("\n" + "=" * 60)
    print("MILESTONE A DEPLOYED")
    print("=" * 60)
    print("\nVerify (run in PowerShell):\n")
    print('  curl.exe -sI "https://meetgreeksingles.com/register"')
    print('  curl.exe -sI "https://meetgreeksingles.com/join2"')
    print('  curl.exe -s  "https://meetgreeksingles.com/register" | findstr "Create My Free Account"')
    print('  curl.exe -s  "https://meetgreeksingles.com/register" | findstr "Meet Greeks from around the world"')
    print('  curl.exe -s  "https://meetgreeksingles.com/join2"    | findstr "What Are You Looking For in a Partner"')


def rollback(password):
    ftp = open_ftp(password)
    print(f"=== ROLLBACK — restoring from {BACKUP_DIR} ===")
    for rel in FILES:
        local = os.path.join(BACKUP_DIR, rel.replace("/", os.sep))
        if not os.path.exists(local):
            print(f"  ABORT — backup missing: {local}")
            ftp.quit()
            sys.exit(1)
        upload_one(ftp, local, rel)
        print(f"  -> {rel}  (restored from backup)")
    ftp.quit()
    print("\nROLLBACK COMPLETE.")


def main():
    password = os.environ.get("PROD_PASS")
    if not password:
        print("ERROR: set $env:PROD_PASS before running this script.")
        sys.exit(1)

    if "--rollback" in sys.argv:
        rollback(password)
    else:
        deploy(password)


if __name__ == "__main__":
    main()
