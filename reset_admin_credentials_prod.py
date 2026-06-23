"""Reset production admin panel + Mary test admin credentials via one-shot PHP."""
import io
import json
import os
import secrets
import ssl
import ftplib
import urllib.request

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
TOKEN = secrets.token_hex(16)
ROOT = os.path.dirname(os.path.abspath(__file__))

ADMIN_PASS = "youandme"
MEMBER_NAME = "Admin"
MEMBER_PASS = "youandme"

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: application/json; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($m->connect_error) {{
    http_response_code(500);
    exit(json_encode(['ok' => false, 'error' => $m->connect_error]));
}}
$m->set_charset('utf8mb4');

$adminPass = {json.dumps(ADMIN_PASS)};
$memberPass = {json.dumps(MEMBER_PASS)};

$before = [];
$r = $m->query("SELECT `option`, value FROM config WHERE module='main' AND `option` IN ('admin_password','admin_password2')");
while ($row = $r->fetch_assoc()) {{ $before[$row['option']] = $row['value']; }}

$m->query("UPDATE config SET value='".$m->real_escape_string($adminPass)."' WHERE module='main' AND `option` IN ('admin_password','admin_password2')");

$memberName = {json.dumps(MEMBER_NAME)};
$memberId = 0;
$r = $m->query("SELECT user_id FROM user WHERE name='".$m->real_escape_string($memberName)."' ORDER BY user_id ASC LIMIT 1");
if ($row = $r->fetch_assoc()) {{ $memberId = (int)$row['user_id']; }}

if ($memberId > 0) {{
    $hash = md5($memberPass);
    $m->query("UPDATE user SET name='".$m->real_escape_string($memberName)."', admin=1, role='admin', password='".$m->real_escape_string($hash)."', active=1, active_code='', onboarding_done=1 WHERE user_id=".$memberId);
}} else {{
    $hash = md5($memberPass);
    $m->query("UPDATE user SET name='".$m->real_escape_string($memberName)."', admin=1, role='admin', password='".$m->real_escape_string($hash)."', active=1, active_code='', onboarding_done=1 WHERE user_id=1");
    $memberId = 1;
}}

$m->query("UPDATE user SET password='".md5($memberPass)."', active=1, active_code='', onboarding_done=1 WHERE name='StefanosKrkds'");
$m->query("DELETE FROM admin_login");

$after = [];
$r = $m->query("SELECT `option`, value FROM config WHERE module='main' AND `option` IN ('admin_password','admin_password2')");
while ($row = $r->fetch_assoc()) {{ $after[$row['option']] = $row['value']; }}

$user = $m->query("SELECT user_id, name, admin, active FROM user WHERE user_id=".$memberId)->fetch_assoc();

echo json_encode([
    'ok' => true,
    'admin_panel_login' => 'admin',
    'admin_panel_password' => $adminPass,
    'member_admin_login' => $user['name'] ?? $memberName,
    'member_admin_password' => $memberPass,
    'before' => $before,
    'after' => $after,
    'member_admin' => $user,
], JSON_PRETTY_PRINT);
"""


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


def ftp_connect():
    pwd = os.environ.get("PROD_PASS")
    if not pwd:
        raise SystemExit("set PROD_PASS environment variable (FTP password for everett@meetgreeksingles.com)")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, 60)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp


def main():
    ftp = ftp_connect()
    name = "_mgs_reset_admin_creds.php"
    ftp.cwd("/")
    ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
    url = f"https://{HOST}/{name}?token={TOKEN}"
    with urllib.request.urlopen(url, timeout=30) as r:
        print(r.read().decode())
    ftp.delete(name)
    ftp.quit()


if __name__ == "__main__":
    main()
