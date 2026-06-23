"""
Fix production SMTP (Brevo) and run a live send test.
"""
import io
import json
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
BREVO_KEY = os.environ.get(
    "BREVO_API_KEY",
    "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",
)


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


def ftp_connect(password):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(context=ctx)
    ftp.connect(HOST, 21, timeout=60)
    ftp.login(USER, password)
    ftp.prot_p()
    ftp.set_pasv(True)
    ftp.cwd("/")
    return ftp


def run_probe(ftp, name, php):
    ftp.storbinary(f"STOR {name}", io.BytesIO(php.encode("utf-8")))
    url = f"https://{HOST}/{name}?token={TOKEN}"
    print(f"GET {url}")
    try:
        with urllib.request.urlopen(url, timeout=45) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(body)
            return resp.status, body
    finally:
        try:
            ftp.delete(name)
        except ftplib.error_perm as e:
            print(f"delete {name}: {e}")


def smtp_fix_php():
    key = BREVO_KEY.replace("'", "\\'")
    return f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($m->connect_error) {{ http_response_code(500); exit('db err: ' . $m->connect_error); }}
$m->set_charset('utf8mb4');
$before = [];
$r = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($row = $r->fetch_assoc()) {{ $before[$row['option']] = $row['value']; }}
$updates = [
    'active' => 'Y',
    'server' => 'smtp-relay.brevo.com',
    'port' => '587',
    'user' => 'irenekrassas@gmail.com',
    'password' => '{key}',
];
$stmt = $m->prepare("UPDATE `config` SET `value`=? WHERE `module`='smtp' AND `option`=?");
foreach ($updates as $opt => $val) {{
    $stmt->bind_param('ss', $val, $opt);
    $stmt->execute();
}}
$stmt->close();
$after = [];
$r = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($row = $r->fetch_assoc()) {{ $after[$row['option']] = $row['value']; }}
$mask = function ($s) {{ return strlen($s) > 12 ? substr($s, 0, 8) . '...' . substr($s, -4) : '***'; }};
if (isset($before['password'])) $before['password'] = $mask($before['password']);
if (isset($after['password'])) $after['password'] = $mask($after['password']);
header('Content-Type: application/json');
echo json_encode(['ok' => true, 'before' => $before, 'after' => $after], JSON_PRETTY_PRINT);
"""


def smtp_test_php():
    return f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
$g = array(); require __DIR__ . '/_include/config/db.php';
$d = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$d->set_charset('utf8mb4');
header('Content-Type: text/plain');
$to = $_GET['to'] ?? 'info@meetgreeksingles.com';
if (!filter_var($to, FILTER_VALIDATE_EMAIL)) {{ echo "bad to\\n"; exit(1); }}
$cfg = [];
$r = $d->query("SELECT `option`, value FROM `config` WHERE module='smtp'");
while ($row = $r->fetch_assoc()) {{ $cfg[$row['option']] = $row['value']; }}
echo "SMTP active=" . ($cfg['active'] ?? '?') . " server=" . ($cfg['server'] ?? '?') . " port=" . ($cfg['port'] ?? '?') . "\\n";
echo "user=" . ($cfg['user'] ?? '?') . " password_len=" . strlen($cfg['password'] ?? '') . "\\n";
require_once __DIR__ . '/_include/current/smtp.class.php';
$errors = [];
set_error_handler(function($s, $msg) use (&$errors) {{ $errors[] = $msg; return true; }});
$smtp = new Smtp($cfg['server'], $cfg['user'], $cfg['password'], intval($cfg['port'] ?? 587), 'meetgreeksingles.com');
$smtp->setFrom($cfg['user'], 'Meet Greek Singles');
$smtp->setTo($to, '');
$smtp->setSubject('MGS SMTP test ' . date('Y-m-d H:i:s'));
$smtp->setMessage('<p>SMTP test from Meet Greek Singles at ' . date('c') . '</p>');
$ok = $smtp->send();
restore_error_handler();
echo "send=" . ($ok ? 'OK' : 'FAIL') . "\\n";
foreach ($errors as $e) echo "ERR: $e\\n";
echo "auth=" . substr((string)$smtp->logGetValue('auth'), 0, 120) . "\\n";
echo "send_resp=" . substr((string)$smtp->logGetValue('send'), 0, 120) . "\\n";
"""


def main():
    pwd = os.environ.get("PROD_PASS")
    if not pwd:
        print("ERROR: set PROD_PASS")
        sys.exit(1)
    ftp = ftp_connect(pwd)
    print("=== Apply Brevo SMTP ===")
    code, body = run_probe(ftp, "_mgs_smtp_fix_probe.php", smtp_fix_php())
    if code != 200:
        ftp.quit()
        sys.exit(1)
    try:
        data = json.loads(body)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        pass
    print("\n=== SMTP send test to info@meetgreeksingles.com ===")
    run_probe(ftp, "_mgs_smtp_send_probe.php", smtp_test_php())
    ftp.quit()


if __name__ == "__main__":
    main()
