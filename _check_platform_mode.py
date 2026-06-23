import io, os, secrets, ssl, ftplib, urllib.request
HOST, USER, TOKEN = "meetgreeksingles.com", "everett@meetgreeksingles.com", secrets.token_hex(16)
PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: text/plain; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$r = $m->query("SELECT module, `option`, value FROM config WHERE `option` IN ('platform_mode','lang_value','lang_active') OR module='language'");
while ($row = $r->fetch_assoc()) echo $row['module'] . '.' . $row['option'] . '=' . $row['value'] . "\\n";
"""
class F(ftplib.FTP_TLS):
    def ntransfercmd(self,cmd,rest=None):
        c,s=ftplib.FTP.ntransfercmd(self,cmd,rest)
        if self._prot_p: c=self.context.wrap_socket(c,server_hostname=self.host,session=self.sock.session)
        return c,s
pwd=os.environ.get("PROD_PASS","7}K#vi,Ol(DQg)]p")
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
ftp=F(context=ctx); ftp.connect(HOST,21,60); ftp.login(USER,pwd); ftp.prot_p(); ftp.set_pasv(True); ftp.cwd('/')
name='_mgs_check_mode.php'
ftp.storbinary('STOR '+name, io.BytesIO(PHP.encode()))
with urllib.request.urlopen(f'https://{HOST}/{name}?token={TOKEN}', timeout=30) as r:
    print(r.read().decode())
ftp.delete(name); ftp.quit()
