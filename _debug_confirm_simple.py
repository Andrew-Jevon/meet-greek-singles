import io, os, secrets, ssl, sys, ftplib, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, USER, TOKEN = "meetgreeksingles.com", "everett@meetgreeksingles.com", secrets.token_hex(16)
HASH = "o8UU7QtyOOEncHsokO7LgMvDtN1vwMbSvJPiwIoQ"
PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$hash = $_GET['h'] ?? '{HASH}';
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$esc = $m->real_escape_string($hash);
$r = $m->query("SELECT user_id, name, LENGTH(active_code) len, active_code FROM user WHERE active_code='" . $esc . "'");
echo "hash_len=" . strlen($hash) . "\\n";
echo "query_rows=" . ($r ? $r->num_rows : 0) . "\\n";
if ($r && $r->num_rows) {{
  $row = $r->fetch_assoc();
  echo "user_id=" . $row['user_id'] . " db_code_len=" . $row['len'] . "\\n";
  echo "codes_match=" . ($row['active_code'] === $hash ? 'yes' : 'no') . "\\n";
}}
$r2 = $m->query("SELECT user_id, active_code FROM user WHERE mail='andrew.jevon.dev@outlook.com'");
if ($r2 && $r2->num_rows) {{
  $u = $r2->fetch_assoc();
  echo "current_code=" . $u['active_code'] . "\\n";
  echo "current_matches_param=" . ($u['active_code'] === $hash ? 'yes' : 'no') . "\\n";
}}
"""
class F(ftplib.FTP_TLS):
    def ntransfercmd(self,cmd,rest=None):
        c,s=ftplib.FTP.ntransfercmd(self,cmd,rest)
        if self._prot_p: c=self.context.wrap_socket(c,server_hostname=self.host,session=self.sock.session)
        return c,s
pwd=os.environ.get("PROD_PASS","7}K#vi,Ol(DQg)]p")
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
ftp=F(context=ctx); ftp.connect(HOST,21,60); ftp.login(USER,pwd); ftp.prot_p(); ftp.set_pasv(True); ftp.cwd('/')
name='_mgs_debug_confirm2.php'
ftp.storbinary('STOR '+name, io.BytesIO(PHP.encode()))
with urllib.request.urlopen(f'https://{HOST}/{name}?token={TOKEN}', timeout=30) as r:
    print(r.read().decode('utf-8','replace'))
ftp.delete(name); ftp.quit()
