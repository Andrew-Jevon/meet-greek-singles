"""Check Andrew's confirmation status on production."""
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
EMAIL = "andrew.jevon.dev@outlook.com"

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$email = '{EMAIL}';
$r = $m->query("SELECT user_id, name, mail, active_code, active, onboarding_done FROM user WHERE mail='" . $m->real_escape_string($email) . "'");
if (!$r || !$r->num_rows) {{ echo "user_not_found\\n"; exit; }}
$u = $r->fetch_assoc();
echo "user_id=" . $u['user_id'] . "\\n";
echo "name=" . $u['name'] . "\\n";
echo "mail=" . $u['mail'] . "\\n";
echo "active_code=" . ($u['active_code'] ? $u['active_code'] : '(empty - confirmed)') . "\\n";
echo "active=" . $u['active'] . "\\n";
echo "onboarding_done=" . $u['onboarding_done'] . "\\n";
if ($u['active_code']) {{
    echo "confirm_url=https://meetgreeksingles.com/confirm_email.php?hash=" . urlencode($u['active_code']) . "\\n";
}}
echo "status=" . ($u['active_code'] ? 'AWAITING_EMAIL_CONFIRM' : 'EMAIL_CONFIRMED') . "\\n";
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
name = "_mgs_check_confirm.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode("utf-8")))
with urllib.request.urlopen(f"https://{HOST}/{name}?token={TOKEN}", timeout=30) as resp:
    print(resp.read().decode("utf-8", errors="replace"))
ftp.delete(name)
ftp.quit()
