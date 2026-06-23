import io
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
header('Content-Type: text/plain');
$targets = array(
    array('tls://smtp-relay.brevo.com', 587, 'Brevo STARTTLS'),
    array('ssl://smtp-relay.brevo.com', 465, 'Brevo SSL'),
    array('smtp-relay.brevo.com', 25, 'Brevo plain 25'),
    array('tls://smtp-relay.brevo.com', 2525, 'Brevo alt 2525'),
);
foreach ($targets as $t) {{
    list($host, $port, $label) = $t;
    $ctx = stream_context_create(array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false)));
    $start = microtime(true);
    $conn = @stream_socket_client($host . ':' . $port, $errno, $errstr, 8, STREAM_CLIENT_CONNECT, $ctx);
    $ms = round((microtime(true) - $start) * 1000);
    if ($conn) {{
        $banner = trim((string) @fgets($conn, 256));
        fclose($conn);
        echo "[OK] $label " . $ms . "ms banner=$banner\\n";
    }} else {{
        echo "[FAIL] $label " . $ms . "ms errno=$errno err=$errstr\\n";
    }}
}}
echo 'mail_fn=' . (function_exists('mail') ? 'yes' : 'no') . '\\n';
echo 'sendmail_path=' . ini_get('sendmail_path') . '\\n';
"""


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


pwd = os.environ.get("PROD_PASS", "7}K#vi,Ol(DQg)]p")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ftp = FTP_TLS_Reuse(context=ctx)
ftp.connect(HOST, 21, 60)
ftp.login(USER, pwd)
ftp.prot_p()
ftp.set_pasv(True)
ftp.cwd("/")
name = "_mgs_smtp_ports_probe.php"
ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
url = f"https://{HOST}/{name}?token={TOKEN}"
with urllib.request.urlopen(url, timeout=90) as r:
    print(r.read().decode("utf-8", errors="replace"))
ftp.delete(name)
ftp.quit()
