"""Ensure production has an Admin member account with youandme password."""
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

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: application/json; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');

$before = [];
$r = $m->query("SELECT user_id, name, admin, active FROM user WHERE admin=1 OR name IN ('Admin','Mary') ORDER BY user_id LIMIT 20");
while ($row = $r->fetch_assoc()) {{ $before[] = $row; }}

$minId = 0;
$r = $m->query("SELECT MIN(user_id) AS id FROM user");
if ($row = $r->fetch_assoc()) {{ $minId = (int) $row['id']; }}
$hash = md5('youandme');
$updated = 0;
if ($minId > 0) {{
    $m->query("UPDATE user SET name='Admin', admin=1, role='admin', password='".$m->real_escape_string($hash)."', active=1, active_code='', onboarding_done=1 WHERE user_id=".$minId);
    $updated = $m->affected_rows;
}}

$after = [];
$r = $m->query("SELECT user_id, name, admin, active FROM user WHERE admin=1 ORDER BY user_id LIMIT 10");
while ($row = $r->fetch_assoc()) {{ $after[] = $row; }}

echo json_encode(['ok'=>true,'min_user_id'=>$minId,'updated_rows'=>$updated,'before'=>$before,'after'=>$after], JSON_PRETTY_PRINT);
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
    name = "_mgs_fix_admin_user.php"
    ftp.cwd("/")
    ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
    url = f"https://{HOST}/{name}?token={TOKEN}"
    with urllib.request.urlopen(url, timeout=30) as r:
        print(r.read().decode())
    ftp.delete(name)
    ftp.quit()


if __name__ == "__main__":
    main()
