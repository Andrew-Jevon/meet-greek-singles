"""Deploy email confirmation redirect fixes."""
import os
import ssl
import ftplib

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
LOCAL = r"d:\MyProjects\Irene\Irene\Irene\site\upstream"
FILES = [
    "email_not_confirmed.php",
    "confirm_email.php",
]


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


pwd = os.environ.get("PROD_PASS", "7}K#vi,Ol(DQg)]p")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ftp = FTP_TLS_Reuse(context=ctx)
ftp.connect(HOST, 21, 60)
ftp.login(USER, pwd)
ftp.prot_p()
ftp.set_pasv(True)
ftp.cwd("/")
for rel in FILES:
    local = os.path.join(LOCAL, rel)
    with open(local, "rb") as f:
        ftp.storbinary(f"STOR {rel}", f)
    print(f"-> {rel}")
ftp.quit()
print("Deploy complete.")
