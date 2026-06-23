"""Send one test email via production mail() path."""
import io
import os
import secrets
import ssl
import ftplib
import urllib.parse
import urllib.request

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
TOKEN = secrets.token_hex(16)
TO = "Andrew.jevon.dev@outlook.com"


def probe_php():
    return f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$to = '{TO}';
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$smtp = [];
$r = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($row = $r->fetch_assoc()) {{ $smtp[$row['option']] = $row['value']; }}
echo "smtp.active=" . ($smtp['active'] ?? '?') . "\\n";
echo "mail_fn=" . (function_exists('mail') ? 'yes' : 'no') . "\\n";

require_once __DIR__ . '/_include/core/main_start.php';

$subject = 'Meet Greek Singles — email delivery test';
$body = '<div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;">'
    . '<h2 style="color:#0f3a6a;">Email delivery test</h2>'
    . '<p>This is a test message from <strong>meetgreeksingles.com</strong> sent at '
    . date('Y-m-d H:i:s T') . '.</p>'
  . '<p>If you received this, confirmation emails should now be able to reach your inbox.</p>'
  . '<p style="color:#64748b;font-size:13px;">You can ignore this message — no action needed.</p>'
  . '</div>';

$from = Common::getOption('info_mail', 'main');
if (!$from) {{ $from = 'info@meetgreeksingles.com'; }}

$errors = [];
set_error_handler(function($s, $msg) use (&$errors) {{ $errors[] = $msg; return true; }});
$sent = false;
try {{
    send_mail($to, $from, $subject, $body, 'Meet Greek Singles');
    $sent = true;
}} catch (Throwable $e) {{
    $errors[] = $e->getMessage();
}}
restore_error_handler();

echo "from=" . $from . "\\n";
echo "to=" . $to . "\\n";
echo "result=" . ($sent ? 'SENT (send_mail completed)' : 'FAIL') . "\\n";
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
    ftp.cwd("/")
    name = "_mgs_email_test_probe.php"
    ftp.storbinary(f"STOR {name}", io.BytesIO(probe_php().encode("utf-8")))
    url = f"https://{HOST}/{name}?token={TOKEN}"
    print(f"Sending test to {TO} ...")
    print(f"GET {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            print(resp.read().decode("utf-8", errors="replace"))
    finally:
        try:
            ftp.delete(name)
        except ftplib.error_perm as e:
            print(f"cleanup: {e}")
    ftp.quit()


if __name__ == "__main__":
    main()
