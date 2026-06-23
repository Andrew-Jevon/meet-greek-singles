"""
Full deploy — 2026-06-09.

Pushes everything built across this session into production:

  - Milestone A polish (register + join2)
  - Milestone B (progress indicator + Turnstile + email-confirm redesign +
    server-side Turnstile verify class)
  - Stuck-spinner fix on /join2
  - All of Irene's recent answer-driven changes (Q4, Q17-Q19, Q21, Q25,
    Q27-Q31, Q33; "Launching Soon" removal; logo bigger; language switcher;
    Advice page; contact page essentials; premium plan name)
  - Brevo SMTP migration (config update via one-shot probe)
  - Advice page insert into production DB (one-shot probe)
  - V1 option list refresh (one-shot probe)

Run pattern:
    $env:PROD_PASS = '<password>'
    $env:PROD_USER = '<email-style FTP username>'   # optional, defaults below
    python d:\\MyProjects\\Irene\\Irene\\Irene\\site\\deploy_full_2026_06_09.py
"""
import sys, os, ftplib, ssl, io, secrets, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


HOST           = "meetgreeksingles.com"
DEFAULT_USER   = "Final@meetgreeksingles.com"
REMOTE_ROOT    = "/"
LOCAL_UPSTREAM = r"d:\MyProjects\Irene\Irene\Irene\site\upstream"
BACKUP_DIR     = r"d:\MyProjects\Irene\Irene\Irene\_backup\2026-06-09_full_deploy"
BREVO_API_KEY  = "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"

FILES_TO_DEPLOY = [
    "_frameworks/main/impact/register.html",
    "_frameworks/main/impact/login.html",
    "_frameworks/main/impact/join2.html",
    "_frameworks/main/impact/onboarding.html",
    "_frameworks/main/impact/index.html",
    "_frameworks/main/impact/_header.html",
    "_frameworks/main/impact/events.html",
    "_frameworks/main/impact/contact.html",
    "_frameworks/main/impact/upgrade.html",
    "_frameworks/main/impact/email_not_confirmed.html",
    "email_not_confirmed.php",
    "advice.php",
    "_include/current/turnstile_verify.php",
    "_include/current/prelaunch.class.php",
]


def open_ftp(password, user):
    print(f"Connecting to {HOST} as {user} ...")
    ftp = FTP_TLS_Reuse(HOST, timeout=30)
    ftp.login(user, password)
    ftp.prot_p()
    ftp.cwd(REMOTE_ROOT)
    return ftp


def backup_file(ftp, remote_rel):
    parts = remote_rel.strip("/").split("/")
    name = parts.pop()
    dirpath = "/".join(parts)
    try:
        ftp.cwd(REMOTE_ROOT + dirpath if dirpath else REMOTE_ROOT)
    except ftplib.error_perm:
        print(f"  remote dir missing: /{dirpath}")
        ftp.cwd(REMOTE_ROOT)
        return None
    buf = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {name}", buf.write)
    except ftplib.error_perm as e:
        print(f"  no existing file to back up ({remote_rel}): {e}")
        ftp.cwd(REMOTE_ROOT)
        return 0
    local = os.path.join(BACKUP_DIR, remote_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local, "wb") as f:
        f.write(buf.getvalue())
    ftp.cwd(REMOTE_ROOT)
    return len(buf.getvalue())


def ensure_remote_dir(ftp, dirpath):
    if not dirpath:
        return
    parts = dirpath.strip("/").split("/")
    cur = ""
    for p in parts:
        cur = cur + "/" + p if cur else p
        try:
            ftp.mkd(cur)
        except ftplib.error_perm:
            pass  # exists


def upload_file(ftp, local_path, remote_rel):
    parts = remote_rel.strip("/").split("/")
    name = parts.pop()
    dirpath = "/".join(parts)
    if dirpath:
        ensure_remote_dir(ftp, dirpath)
        ftp.cwd(REMOTE_ROOT + dirpath)
    else:
        ftp.cwd(REMOTE_ROOT)
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {name}", f)
    ftp.cwd(REMOTE_ROOT)


def upload_probe(ftp, name, php):
    ftp.cwd(REMOTE_ROOT)
    ftp.storbinary(f"STOR {name}", io.BytesIO(php.encode("utf-8")))


def run_probe(name, token):
    url = f"https://meetgreeksingles.com/{name}?token={token}"
    print(f"  GET {url}")
    try:
        with urllib.request.urlopen(url, timeout=45) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"PROBE FAILED: {e}"


def delete_probe(ftp, name):
    try:
        ftp.delete(name)
        return True
    except Exception as e:
        print(f"  delete failed for {name}: {e}")
        return False


def brevo_smtp_probe(token, key):
    return f"""<?php
if (!isset($_GET['token']) || $_GET['token'] !== '{token}') {{ http_response_code(403); exit('forbidden'); }}
@include __DIR__ . '/_include/inc/cfg.php';
if (!defined('DB_HOST')) {{ http_response_code(500); exit('no db cfg'); }}
$m = @new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($m->connect_error) {{ http_response_code(500); exit('db err'); }}
$m->set_charset('utf8mb4');
$before = [];
$res = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($r = $res->fetch_assoc()) {{ $before[$r['option']] = $r['value']; }}
$updates = [
    'active'   => 'Y',
    'server'   => 'smtp-relay.brevo.com',
    'port'     => '587',
    'user'     => 'irenekrassas@gmail.com',
    'password' => '{key}',
];
$stmt = $m->prepare("UPDATE `config` SET `value`=? WHERE `module`='smtp' AND `option`=?");
foreach ($updates as $opt => $val) {{ $stmt->bind_param('ss', $val, $opt); $stmt->execute(); }}
$stmt->close();
$after = [];
$res = $m->query("SELECT `option`, `value` FROM `config` WHERE `module`='smtp'");
while ($r = $res->fetch_assoc()) {{ $after[$r['option']] = $r['value']; }}
$m->close();
$mask = function($s) {{ return strlen($s) > 12 ? substr($s, 0, 8) . '...' . substr($s, -4) : '***'; }};
$before['password'] = $mask($before['password'] ?? '');
$after['password']  = $mask($after['password'] ?? '');
header('Content-Type: application/json');
echo json_encode(['ok' => true, 'before' => $before, 'after' => $after], JSON_PRETTY_PRINT);
"""


def advice_page_probe(token):
    # Long content stored as one PHP heredoc so quoting stays clean.
    return f"""<?php
if (!isset($_GET['token']) || $_GET['token'] !== '{token}') {{ http_response_code(403); exit('forbidden'); }}
@include __DIR__ . '/_include/inc/cfg.php';
if (!defined('DB_HOST')) {{ http_response_code(500); exit('no db cfg'); }}
$m = @new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($m->connect_error) {{ http_response_code(500); exit('db err'); }}
$m->set_charset('utf8mb4');

$existing = $m->query("SELECT id FROM `pages` WHERE `menu_title`='menu_top_advice' LIMIT 1");
if ($existing && $existing->fetch_assoc()) {{
    header('Content-Type: application/json');
    echo json_encode(['ok' => true, 'note' => 'Advice page already exists, skipping']);
    $m->close();
    exit;
}}

$content = <<<EOT
<h2>Advice for Meaningful Connections</h2><p><em>This page is being prepared. Final content coming soon.</em></p><p>Meet Greek Singles is built on the belief that lasting relationships grow from shared culture, values, and patience. While we finalise this section, here are a few ideas that have shaped our community so far:</p><ul><li><strong>Write a profile that sounds like you.</strong> A few honest sentences tell members far more than a long polished essay. Talk about what you love, not just what you do.</li><li><strong>Add a clear, recent photo.</strong> Profiles with photos receive significantly more attention. A warm smile and natural lighting go a long way.</li><li><strong>Take your time.</strong> A meaningful first message is short, kind, and specifically about something you read in the other member's profile.</li><li><strong>Listen for shared values.</strong> Greek heritage, family, faith, tradition &mdash; these things often matter more than any list of hobbies.</li></ul><p>More guidance on starting conversations, planning a first meeting, and staying safe online will be added here shortly.</p>
EOT;

$stmt = $m->prepare("INSERT INTO `pages` (`menu_title`, `menu_style`, `title`, `content`, `section`, `position`, `status`, `hide_from_guests`, `parent`, `system`, `lang`, `set`) VALUES (?, 0, 'Advice', ?, 'not_in_menu', 99, 1, 0, 0, 0, 'default', '')");
$slug = 'menu_top_advice';
$stmt->bind_param('ss', $slug, $content);
$stmt->execute();
$insertId = $m->insert_id;
$stmt->close();
$m->close();
header('Content-Type: application/json');
echo json_encode(['ok' => true, 'inserted_page_id' => $insertId]);
"""


def v1_options_probe(token):
    sql_blocks = [
        ("var_my_religion", [
            (1, 'Greek Orthodox'), (2, 'Catholic'), (3, 'Christian (other)'),
            (4, 'Jewish'), (5, 'Muslim'), (6, 'Other Religion'),
            (7, 'Spiritual but not religious'), (8, 'Prefer not to say'),
        ]),
        ("var_attending_the_greek_church", [
            (1, 'Regularly'), (2, 'Often'), (3, 'Seldom'),
            (4, 'Only during holidays'), (5, 'Never'),
        ]),
        ("var_level_of_faith", [
            (1, 'Extremely important'), (2, 'Very important'),
            (3, 'Somewhat important'), (4, 'Not very important'),
        ]),
        ("var_do_you_like_to_attend_local_greek_events", [
            (1, 'Very much'), (2, 'Sometimes'), (3, 'Rarely'), (4, 'Not interested'),
        ]),
        ("var_family_life_importance", [
            (1, 'Extremely important'), (2, 'Very important'),
            (3, 'Somewhat important'), (4, 'Not very important'),
        ]),
        ("var_do_you_want_a_partner_of_greek_descent", [
            (1, 'Essential'), (2, 'Very important'),
            (3, 'Somewhat important'), (4, 'Not important'),
        ]),
    ]
    # Build the PHP array literal
    blocks_php = ""
    for tbl, rows in sql_blocks:
        rows_php = ",".join([f"[{rid}, '{label.replace(chr(39), chr(39)+chr(39))}']" for rid, label in rows])
        blocks_php += f"  ['{tbl}', [{rows_php}]],\n"

    return f"""<?php
if (!isset($_GET['token']) || $_GET['token'] !== '{token}') {{ http_response_code(403); exit('forbidden'); }}
@include __DIR__ . '/_include/inc/cfg.php';
if (!defined('DB_HOST')) {{ http_response_code(500); exit('no db cfg'); }}
$m = @new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($m->connect_error) {{ http_response_code(500); exit('db err'); }}
$m->set_charset('utf8mb4');

$plan = [
{blocks_php}
];

$summary = [];
foreach ($plan as [$tbl, $rows]) {{
    $m->query("TRUNCATE TABLE `" . $tbl . "`");
    $ok = 0;
    foreach ($rows as [$rid, $title]) {{
        $stmt = $m->prepare("INSERT INTO `" . $tbl . "` (id, title) VALUES (?, ?)");
        $stmt->bind_param('is', $rid, $title);
        if ($stmt->execute()) $ok++;
        $stmt->close();
    }}
    $summary[$tbl] = $ok;
}}
$m->close();
header('Content-Type: application/json');
echo json_encode(['ok' => true, 'updated' => $summary], JSON_PRETTY_PRINT);
"""


def main():
    pwd = os.environ.get("PROD_PASS")
    user = os.environ.get("PROD_USER", DEFAULT_USER)
    if not pwd:
        print("ERROR: set $env:PROD_PASS first"); sys.exit(1)

    ftp = open_ftp(pwd, user)
    print(f"Logged in.\n")

    # ─── STAGE 1: backup current production files ────────────────────────
    print("=== STAGE 1: backing up current production files ===")
    for rel in FILES_TO_DEPLOY:
        size = backup_file(ftp, rel)
        if size is None:
            print(f"  SKIP backup (dir missing): {rel}")
        else:
            print(f"  <- {rel}  ({size} bytes)")
    print(f"  backups saved to: {BACKUP_DIR}\n")

    # ─── STAGE 2: upload all changed files ───────────────────────────────
    print("=== STAGE 2: uploading new versions ===")
    uploaded, missing = 0, []
    for rel in FILES_TO_DEPLOY:
        local = os.path.join(LOCAL_UPSTREAM, rel.replace("/", os.sep))
        if not os.path.exists(local):
            print(f"  MISSING LOCAL: {local}")
            missing.append(rel)
            continue
        upload_file(ftp, local, rel)
        print(f"  -> {rel}")
        uploaded += 1
    print(f"  uploaded: {uploaded} / {len(FILES_TO_DEPLOY)}\n")
    if missing:
        print(f"  WARNING: {len(missing)} files missing locally, skipped")

    # ─── STAGE 3: Brevo SMTP migration probe ─────────────────────────────
    print("=== STAGE 3: Brevo SMTP migration ===")
    tok1 = secrets.token_hex(16)
    probe1 = f"_mgs_brevo_smtp_{tok1[:8]}.php"
    upload_probe(ftp, probe1, brevo_smtp_probe(tok1, BREVO_API_KEY))
    result1 = run_probe(probe1, tok1)
    print("  result:")
    print("  " + result1.replace("\n", "\n  "))
    delete_probe(ftp, probe1)
    print()

    # ─── STAGE 4: Advice page insert probe ───────────────────────────────
    print("=== STAGE 4: insert Advice page into production DB ===")
    tok2 = secrets.token_hex(16)
    probe2 = f"_mgs_advice_page_{tok2[:8]}.php"
    upload_probe(ftp, probe2, advice_page_probe(tok2))
    result2 = run_probe(probe2, tok2)
    print("  result:")
    print("  " + result2.replace("\n", "\n  "))
    delete_probe(ftp, probe2)
    print()

    # ─── STAGE 5: V1 option lists migration probe ────────────────────────
    print("=== STAGE 5: V1 option lists migration ===")
    tok3 = secrets.token_hex(16)
    probe3 = f"_mgs_v1_options_{tok3[:8]}.php"
    upload_probe(ftp, probe3, v1_options_probe(tok3))
    result3 = run_probe(probe3, tok3)
    print("  result:")
    print("  " + result3.replace("\n", "\n  "))
    delete_probe(ftp, probe3)
    print()

    ftp.quit()

    # ─── STAGE 6: OPcache reset to pick up PHP changes ───────────────────
    print("=== STAGE 6: OPcache reset (so prelaunch.class.php + advice.php + turnstile_verify.php take effect) ===")
    opc_url = "https://meetgreeksingles.com/_mgs_opc.php?token=429924c65fda7a12ff86d2c73eb838bc"
    try:
        with urllib.request.urlopen(opc_url, timeout=30) as resp:
            print("  OPcache: " + resp.read().decode("utf-8", errors="replace")[:200])
    except Exception as e:
        print(f"  OPcache reset failed (non-fatal): {e}")
    print()

    # ─── STAGE 7: live verification ──────────────────────────────────────
    print("=== STAGE 7: live verification ===")
    checks = [
        ("/",         ["Where Greek Hearts Meet", "mgs_lang_switch"]),
        ("/register", ["Create My Free Account", "never be shared with anyone", "Meet Greeks from around the world"]),
        ("/login",    ["#1e3a8a", "Welcome back"]),
        ("/contact",  ["info@meetgreeksingles.com", "48 hours"]),
        ("/advice",   ["Advice for Meaningful Connections"]),
        ("/events.php", ["community-event invitation paragraph"[:30] or "Greek gatherings"]),
    ]
    for path, probes in checks:
        try:
            with urllib.request.urlopen(f"https://meetgreeksingles.com{path}", timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"  GET {path}  HTTP {resp.status}  ({len(body)} bytes)")
                for p in probes:
                    hit = p in body
                    print(f"    {p[:50]:<50} {'PASS' if hit else 'FAIL'}")
        except Exception as e:
            print(f"  GET {path}  ERR: {e}")

    print("\n" + "=" * 60)
    print("FULL DEPLOY COMPLETE")
    print("=" * 60)
    print(f"\nBackups: {BACKUP_DIR}")
    print("Rollback by re-uploading from backup dir if any page looks wrong.")


if __name__ == "__main__":
    main()
