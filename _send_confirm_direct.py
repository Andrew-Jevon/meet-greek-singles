"""Send confirmation-style email directly via mail() with user's active hash."""
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
TO = "andrew.jevon.dev@outlook.com"

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$email = '{TO}';
$r = $m->query("SELECT user_id, name, active_code FROM user WHERE mail='" . $m->real_escape_string($email) . "'");
if (!$r || !$r->num_rows) {{ echo "user_not_found\\n"; exit; }}
$u = $r->fetch_assoc();
$hash = $u['active_code'];
if (!$hash) {{ echo "already_confirmed\\n"; exit; }}
$link = 'https://meetgreeksingles.com/confirm_email.php?hash=' . urlencode($hash);
$name = $u['name'];
$subject = 'Please confirm your email - Meet Greek Singles';
$body = '<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1f2937;">'
  . '<h2 style="color:#0f3a6a;">Confirm your email</h2>'
  . '<p>Hi ' . htmlspecialchars($name) . ',</p>'
  . '<p>Please click the button below to confirm your email address and activate your Meet Greek Singles account.</p>'
  . '<p style="margin:28px 0;"><a href="' . htmlspecialchars($link) . '" style="display:inline-block;background:#1e3a8a;color:#e6c069;text-decoration:none;padding:14px 28px;border-radius:999px;font-weight:700;">Confirm My Email</a></p>'
  . '<p style="font-size:13px;color:#64748b;">Or copy this link:<br>' . htmlspecialchars($link) . '</p>'
  . '<p style="font-size:13px;color:#64748b;">Sent at ' . date('Y-m-d H:i:s T') . '</p>'
  . '</div>';
$from = 'info@meetgreeksingles.com';
$headers = "From: Meet Greek Singles <" . $from . ">\\r\\nReply-To: " . $from . "\\r\\nMIME-Version: 1.0\\r\\nContent-Type: text/html; charset=utf-8\\r\\n";
$ok = @mail($email, $subject, $body, $headers);
echo "user_id=" . $u['user_id'] . " name=" . $name . "\\n";
echo "confirm_link=" . $link . "\\n";
echo "mail_result=" . ($ok ? 'OK' : 'FAIL') . "\\n";
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
name = "_mgs_confirm_direct.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode("utf-8")))
url = f"https://{HOST}/{name}?token={TOKEN}"
print(f"Sending confirmation email to {TO} ...")
with urllib.request.urlopen(url, timeout=60) as resp:
    print(resp.read().decode("utf-8", errors="replace"))
ftp.delete(name)
ftp.quit()
