"""Set platform_mode=live on production and deploy prelaunch/i18n fixes."""
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
UPSTREAM = os.path.join(ROOT, "upstream")

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: application/json; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$before = $m->query("SELECT value FROM config WHERE module='options' AND `option`='platform_mode'")->fetch_assoc();
$m->query("UPDATE config SET value='live' WHERE module='options' AND `option`='platform_mode'");
$after = $m->query("SELECT value FROM config WHERE module='options' AND `option`='platform_mode'")->fetch_assoc();
$langs = [];
$r = $m->query("SELECT module, `option`, value FROM config WHERE module IN ('language','main') AND (`option` LIKE 'lang%' OR `option`='active')");
while ($row = $r->fetch_assoc()) {{ $langs[$row['module'].'.'.$row['option']] = $row['value']; }}
echo json_encode(['ok'=>true,'before'=>$before['value']??null,'after'=>$after['value']??null,'lang'=>$langs], JSON_PRETTY_PRINT);
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
        raise SystemExit("set PROD_PASS environment variable")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, 60)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp


def ensure_dir(ftp, path):
    for part in path.strip("/").split("/"):
        try:
            ftp.mkd(part)
        except ftplib.error_perm:
            pass
        ftp.cwd(part)
    for _ in path.strip("/").split("/"):
        ftp.cwd("..")


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
    ftp = ftp_connect()
    ftp.cwd("/")

    deploys = [
        (
            os.path.join(UPSTREAM, "_frameworks/main/impact/js/mgs_i18n.js"),
            "_frameworks/main/impact/js/mgs_i18n.js",
        ),
        (
            os.path.join(UPSTREAM, "_frameworks/main/impact/_header.html"),
            "_frameworks/main/impact/_header.html",
        ),
        (
            os.path.join(UPSTREAM, "_frameworks/main/impact/index.html"),
            "_frameworks/main/impact/index.html",
        ),
        (
            os.path.join(UPSTREAM, "_include/current/prelaunch.class.php"),
            "_include/current/prelaunch.class.php",
        ),
        (
            os.path.join(UPSTREAM, "_include/current/router.class.php"),
            "_include/current/router.class.php",
        ),
    ]
    for local, remote in deploys:
        upload_file(ftp, local, remote)

    name = "_mgs_set_live.php"
    ftp.cwd("/")
    ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
    url = f"https://{HOST}/{name}?token={TOKEN}"
    with urllib.request.urlopen(url, timeout=30) as r:
        print(r.read().decode())
    ftp.delete(name)
    ftp.quit()


if __name__ == "__main__":
    main()
