"""Set smtp.active=N on production so mail uses local sendmail (SMTP ports blocked)."""
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
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$m->query("UPDATE `config` SET `value`='N' WHERE `module`='smtp' AND `option`='active'");
$cfg = [];
$r = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($row = $r->fetch_assoc()) {{ $cfg[$row['option']] = $row['value']; }}
$auto = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='automail' AND `option`='confirm_email'");
$confirm = $auto && $auto->num_rows ? $auto->fetch_assoc() : null;
header('Content-Type: application/json');
echo json_encode(['ok' => true, 'smtp' => $cfg, 'confirm_email_automail' => $confirm], JSON_PRETTY_PRINT);
"""


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


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
ftp.cwd("/")

# Deploy mail.php fallback
local_mail = r"d:\MyProjects\Irene\Irene\Irene\site\upstream\_include\lib\mail.php"
remote_mail = "_include/lib/mail.php"
for part in ["_include", "_include/lib"]:
    try:
        ftp.mkd(part)
    except ftplib.error_perm:
        pass
ftp.cwd("/_include/lib")
with open(local_mail, "rb") as f:
    ftp.storbinary("STOR mail.php", f)
print("Uploaded _include/lib/mail.php")
ftp.cwd("/")

name = "_mgs_disable_smtp_probe.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
url = f"https://{HOST}/{name}?token={TOKEN}"
with urllib.request.urlopen(url, timeout=30) as r:
    print(r.read().decode())
ftp.delete(name)
ftp.quit()
