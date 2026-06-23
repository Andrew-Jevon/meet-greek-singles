"""One-shot cleanup: remove the accidental directories
    /_mgs_homecity_install.php/
    /_mgs_greek_regions.php/
created by the earlier buggy stor() in _deploy_2026_05_01.py.
Each contains a single PHP file of the same name.
"""
from __future__ import annotations
import ftplib, os, ssl, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD: sys.exit("ERROR: MGS_PASS env var not set")


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
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    f = FTP_TLS_Reuse(context=ctx)
    f.connect(HOST, 21, timeout=60)
    f.login(USER, PASSWORD); f.prot_p(); f.set_pasv(True)
    return f


BAD_DIRS = ["_mgs_homecity_install.php", "_mgs_greek_regions.php"]


def cleanup_dir(f, dirname):
    print(f"\nCleaning /{dirname}/ ...")
    f.cwd("/")
    try:
        f.cwd(dirname)
    except ftplib.error_perm as e:
        print(f"  cwd failed — {e}; skipping (probably already cleaned)")
        return
    # List contents
    files = []
    f.retrlines("NLST", files.append)
    print(f"  contents: {files}")
    for entry in files:
        # Skip . and ..
        if entry in (".", ".."): continue
        try:
            f.delete(entry)
            print(f"  + deleted {entry}")
        except ftplib.error_perm as e:
            print(f"  ! couldn't delete {entry}: {e}")
    # Now remove the directory itself
    f.cwd("/")
    try:
        f.rmd(dirname)
        print(f"  + RMD /{dirname}")
    except ftplib.error_perm as e:
        print(f"  ! RMD failed: {e}")


def main():
    f = connect()
    try:
        for d in BAD_DIRS:
            cleanup_dir(f, d)
    finally:
        f.quit()
    print("\nDONE")


if __name__ == "__main__":
    main()
