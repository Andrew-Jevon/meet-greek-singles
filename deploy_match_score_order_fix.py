"""Deploy match_score ORDER BY fix to production."""
import os
import ssl
import ftplib

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(ROOT, "upstream", "_include", "current", "userslist.class.php")
REMOTE = "_include/current/userslist.class.php"


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


def main():
    pwd = os.environ.get("PROD_PASS")
    if not pwd:
        raise SystemExit("set PROD_PASS")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, 60)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.set_pasv(True)
    ftp.cwd("/_include/current")
    with open(LOCAL, "rb") as f:
        ftp.storbinary("STOR userslist.class.php", f)
    print("Uploaded", REMOTE)
    ftp.quit()


if __name__ == "__main__":
    main()
