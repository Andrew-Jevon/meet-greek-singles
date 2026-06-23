"""Resend confirm_email automail to Andrew.jevon.dev@outlook.com via production."""
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
$email = '{TO}';
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$r = $m->query("SELECT user_id, name, active_code FROM user WHERE mail='" . $m->real_escape_string($email) . "'");
if (!$r || !$r->num_rows) {{
    echo "user_not_found for $email\\n";
    exit(0);
}}
$user = $r->fetch_assoc();
echo "user_id=" . $user['user_id'] . " name=" . $user['name'] . "\\n";
echo "has_active_code=" . ($user['active_code'] ? 'yes' : 'no') . "\\n";

define('AREA', 'login');
$_SERVER['REQUEST_URI'] = '/_mgs_resend_confirm_test.php';
ob_start();
include __DIR__ . '/_include/core/main_start.php';
ob_end_clean();

$errors = [];
set_error_handler(function($s, $msg) use (&$errors) {{ $errors[] = $msg; return true; }});
user_change_email($user['user_id'], $email);
restore_error_handler();

echo "confirm_email_resent=OK\\n";
foreach ($errors as $e) echo "ERR: $e\\n";
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
name = "_mgs_resend_confirm_test.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode("utf-8")))
url = f"https://{HOST}/{name}?token={TOKEN}"
print(f"Resending confirmation to {TO} ...")
try:
    with urllib.request.urlopen(url, timeout=90) as resp:
        print(resp.read().decode("utf-8", errors="replace")[:2000])
except Exception as e:
    print("ERROR:", e)
ftp.delete(name)
ftp.quit()
