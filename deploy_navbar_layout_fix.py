"""Deploy navbar layout fixes to production."""
import os
import ssl
import ftplib

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upstream", "_frameworks", "main", "impact")

FILES = [
    ("_header.html", "_frameworks/main/impact/_header.html"),
    ("js/mgs_i18n.js", "_frameworks/main/impact/js/mgs_i18n.js"),
    ("js/mgs_translations.js", "_frameworks/main/impact/js/mgs_translations.js"),
]


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


def upload_file(ftp, local_path, remote_path):
    parts = remote_path.replace("\\", "/").split("/")
    fname = parts[-1]
    dirs = parts[:-1]
    ftp.cwd("/")
    for d in dirs:
        try:
            ftp.mkd(d)
        except ftplib.error_perm:
            pass
        ftp.cwd(d)
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {fname}", f)
    print(f"Uploaded {remote_path}")


def main():
    pwd = os.environ.get("PROD_PASS", "7}K#vi,Ol(DQg)]p")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, 60)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.set_pasv(True)
    for local_rel, remote in FILES:
        upload_file(ftp, os.path.join(ROOT, local_rel), remote)
    ftp.quit()


if __name__ == "__main__":
    main()
