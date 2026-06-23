import io
import os
import secrets
import ssl
import sys
import ftplib
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
TOKEN = secrets.token_hex(16)
TO = "Andrew.jevon.dev@outlook.com"

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$to = '{TO}';
$from = 'info@meetgreeksingles.com';
$subject = 'Meet Greek Singles - email delivery test';
$body = '<p>Test from meetgreeksingles.com at ' . date('c') . '. If you see this, delivery works.</p>';
$headers = "From: Meet Greek Singles <" . $from . ">\\r\\nMIME-Version: 1.0\\r\\nContent-Type: text/html; charset=utf-8\\r\\n";
$ok = @mail($to, $subject, $body, $headers);
echo 'mail_result=' . ($ok ? 'OK' : 'FAIL') . "\\n";
echo 'to=' . $to . "\\n";
"""


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
name = "_mgs_email_test2.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode("utf-8")))
url = f"https://{HOST}/{name}?token={TOKEN}"
print(f"Sending test to {TO} ...")
with urllib.request.urlopen(url, timeout=60) as resp:
    print(resp.read().decode("utf-8", errors="replace"))
ftp.delete(name)
ftp.quit()
