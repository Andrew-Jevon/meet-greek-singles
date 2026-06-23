import io, os, secrets, ssl, sys, ftplib, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, USER, TOKEN = "meetgreeksingles.com", "everett@meetgreeksingles.com", secrets.token_hex(16)
HASH = "o8UU7QtyOOEncHsokO7LgMvDtN1vwMbSvJPiwIoQ"
PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$hash = '{HASH}';
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$esc = $m->real_escape_string($hash);
$r = $m->query("SELECT user_id, name, active_code FROM user WHERE active_code='" . $esc . "'");
echo "raw_query_rows=" . ($r ? $r->num_rows : 0) . "\\n";
if ($r && $r->num_rows) {{ $row=$r->fetch_assoc(); echo "found user_id=" . $row['user_id'] . "\\n"; }}

define('AREA', 'login');
$_SERVER['REQUEST_URI'] = '/confirm_email.php?hash=' . urlencode($hash);
$_GET['hash'] = $hash;
ob_start();
include __DIR__ . '/_include/core/main_start.php';
ob_end_clean();

$user = DB::select('user', "`active_code` = " . to_sql($hash));
echo "DB::select count=" . count($user) . "\\n";
if (!empty($user)) echo "select user_id=" . $user[0]['user_id'] . "\\n";
echo "to_sql=" . to_sql($hash) . "\\n";
"""
class F(ftplib.FTP_TLS):
    def ntransfercmd(self,cmd,rest=None):
        c,s=ftplib.FTP.ntransfercmd(self,cmd,rest)
        if self._prot_p: c=self.context.wrap_socket(c,server_hostname=self.host,session=self.sock.session)
        return c,s
pwd=os.environ.get("PROD_PASS","7}K#vi,Ol(DQg)]p")
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
ftp=F(context=ctx); ftp.connect(HOST,21,60); ftp.login(USER,pwd); ftp.prot_p(); ftp.set_pasv(True); ftp.cwd('/')
name='_mgs_debug_confirm.php'
ftp.storbinary('STOR '+name, io.BytesIO(PHP.encode()))
with urllib.request.urlopen(f'https://{HOST}/{name}?token={TOKEN}', timeout=60) as r:
    print(r.read().decode('utf-8','replace')[:3000])
ftp.delete(name); ftp.quit()
