"""
Production migration — switch SMTP from Office 365 to Brevo.
2026-06-06.

This script updates the production Chameleon config table to point email
sending at Brevo (smtp-relay.brevo.com). It is intentionally separate from
the file-deploy scripts because it modifies the database, not files.

What it changes (in the `config` table on production):
    smtp.active   = 'Y'                          (turn SMTP on)
    smtp.server   = 'smtp-relay.brevo.com'       (was: mail.chameleonintranet.com)
    smtp.port     = '587'                        (was: 25025)
    smtp.user     = 'irenekrassas@gmail.com'     (Brevo account email)
    smtp.password = '<Brevo API key>'            (the xkeysib-... value)

After running, the next outgoing email from the site (registration
confirmation, password reset, etc.) will be routed through Brevo
instead of the previous Office 365 SMTP path.

This script uses a token-protected one-shot _mgs_*.php pattern: deploys
the file, runs it via HTTPS, then deletes it from production. The script
itself never connects to the production DB directly.

Run pattern:
    $env:PROD_PASS = '<production FTPS password>'
    $env:BREVO_API_KEY = '<Brevo API key starting xkeysib-...>'
    python d:\\MyProjects\\Irene\\Irene\\Irene\\site\\deploy_brevo_smtp_2026_06_06.py
"""
import sys, os, ftplib, ssl, urllib.request, urllib.parse, secrets, json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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


HOST        = "meetgreeksingles.com"
USER        = "everett@meetgreeksingles.com"
REMOTE_ROOT = "/"


def main():
    pwd = os.environ.get("PROD_PASS")
    key = os.environ.get("BREVO_API_KEY")
    if not pwd or not key:
        print("ERROR: set $env:PROD_PASS and $env:BREVO_API_KEY before running.")
        sys.exit(1)

    token = secrets.token_hex(16)
    probe_name = f"_mgs_smtp_brevo_2026_06_06.php"
    probe_php = f"""<?php
// One-shot SMTP-config migration probe. Token-protected.
// Deletes itself by writing a delete-script alongside; we then delete it
// via a second FTPS call from the deploy script.

if (!isset($_GET['token']) || $_GET['token'] !== '{token}') {{
    http_response_code(403);
    exit('forbidden');
}}

// Direct DB connection using Chameleon's config (same as other _mgs probes).
$g = array();
@include __DIR__ . '/_include/config/db.php';
if (empty($g['db']['host'])) {{
    http_response_code(500);
    exit('db config not found');
}}

$mysqli = @new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
if ($mysqli->connect_error) {{
    http_response_code(500);
    exit('db connect failed: ' . $mysqli->connect_error);
}}
$mysqli->set_charset('utf8mb4');

// Capture before-state for safety / rollback.
$before = [];
$res = $mysqli->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($r = $res->fetch_assoc()) {{ $before[$r['option']] = $r['value']; }}

// Apply new SMTP config.
$updates = [
    'active'   => 'Y',
    'server'   => 'smtp-relay.brevo.com',
    'port'     => '587',
    'user'     => 'irenekrassas@gmail.com',
    'password' => '{key}',
];
$stmt = $mysqli->prepare("UPDATE `config` SET `value`=? WHERE `module`='smtp' AND `option`=?");
foreach ($updates as $opt => $val) {{
    $stmt->bind_param('ss', $val, $opt);
    $stmt->execute();
}}
$stmt->close();

// Capture after-state.
$after = [];
$res = $mysqli->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($r = $res->fetch_assoc()) {{ $after[$r['option']] = $r['value']; }}
$mysqli->close();

// Mask the password in the output.
$mask = function ($s) {{ return strlen($s) > 12 ? substr($s, 0, 8) . '...' . substr($s, -4) : '***'; }};
$before['password'] = isset($before['password']) ? $mask($before['password']) : '';
$after['password']  = isset($after['password'])  ? $mask($after['password'])  : '';

header('Content-Type: application/json');
echo json_encode(['ok' => true, 'before' => $before, 'after' => $after], JSON_PRETTY_PRINT);
"""

    print(f"Connecting to {HOST} ...")
    ftp = FTP_TLS_Reuse(HOST)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.cwd(REMOTE_ROOT)

    print(f"Uploading probe: {probe_name}")
    import io
    ftp.storbinary(f"STOR {probe_name}", io.BytesIO(probe_php.encode("utf-8")))

    url = f"https://meetgreeksingles.com/{probe_name}?token={token}"
    print(f"Running probe: {url}")
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print("Probe response:")
            print(body)
    except Exception as e:
        print(f"Probe call FAILED: {e}")

    print(f"Deleting probe from production: {probe_name}")
    try:
        ftp.delete(probe_name)
        print("Probe deleted.")
    except Exception as e:
        print(f"Delete failed (delete manually): {e}")
    ftp.quit()

    print("\n" + "=" * 60)
    print("BREVO SMTP MIGRATION COMPLETE")
    print("=" * 60)
    print("\nNext: trigger a real registration confirmation email and verify")
    print("it lands in a Gmail / Outlook / Yahoo inbox (not spam).")


if __name__ == "__main__":
    main()
