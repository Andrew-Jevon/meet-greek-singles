"""2026-06-17 — Hide test/demo accounts from public view (SAFE & REVERSIBLE).

This NEVER deletes a user and NEVER touches an admin (admin <> 0) row. It only
flips `user.active` (1 -> 0 to hide, 0 -> 1 to restore). Setting active=0 removes
a profile from search/listings and blocks its login, which is exactly what Irene
asked for ("mark them hidden/inactive instead of deleting").

Workflow (run from a machine that can reach FTP — set PROD_USER / PROD_PASS):

  1. AUDIT (default, read-only) — list likely test/demo accounts so you can review:
        python hide_test_accounts_2026_06_17.py
     Tune the patterns it searches with --like (repeatable), e.g.:
        python hide_test_accounts_2026_06_17.py --like "%test%" --like "%demo%" --like "%@example.%"

  2. HIDE — only the user_ids you confirmed from the audit (comma-separated):
        python hide_test_accounts_2026_06_17.py --apply --ids 12,15,16,22

  3. UNHIDE — reverse it at any time:
        python hide_test_accounts_2026_06_17.py --unhide --ids 12,15,16,22

Email addresses are masked in all output. Admin rows are filtered out server-side.
"""
import argparse
import io
import os
import secrets
import ssl
import ftplib
import urllib.request

HOST = "meetgreeksingles.com"
USER = os.environ.get("PROD_USER", "everett@meetgreeksingles.com")
DEFAULT_LIKES = ["%test%", "%demo%", "%example.%", "%mailinator%", "%+test@%"]


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


class ImplicitFTP_TLS(FTP_TLS_Reuse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value, server_hostname=self.host)
        self._sock = value


def ftp_connect():
    pwd = os.environ.get("PROD_PASS", "7}K#vi,Ol(DQg)]p")
    mode = os.environ.get("PROD_FTP_MODE", "explicit").lower()
    port = int(os.environ.get("PROD_FTP_PORT", "990" if mode == "implicit" else "21"))
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    cls = ImplicitFTP_TLS if mode == "implicit" else FTP_TLS_Reuse
    ftp = cls(context=ctx)
    ftp.connect(HOST, port, 60)
    ftp.login(USER, pwd)
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp


def run_php(php_body):
    """Upload a one-shot token-guarded PHP file, call it over HTTPS, delete it."""
    token = secrets.token_hex(16)
    php = "<?php\n" + (
        "if (($_GET['token'] ?? '') !== '%s') { http_response_code(403); exit('forbidden'); }\n" % token
    ) + php_body
    ftp = ftp_connect()
    ftp.cwd("/")
    name = "_mgs_test_accounts.php"
    ftp.storbinary(f"STOR {name}", io.BytesIO(php.encode()))
    url = f"https://{HOST}/{name}?token={token}"
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            print(r.read().decode())
    finally:
        try:
            ftp.delete(name)
        except Exception:
            pass
        ftp.quit()


DB_BOOT = (
    "header('Content-Type: text/plain; charset=utf-8');\n"
    "$g = array(); require __DIR__ . '/_include/config/db.php';\n"
    "$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);\n"
    "$m->set_charset('utf8mb4');\n"
    "function mask($e){ if(!$e) return ''; $a=strpos($e,'@'); return $a===false? substr($e,0,2).'***' : substr($e,0,2).'***'.substr($e,$a); }\n"
)


def audit(likes):
    conds = " OR ".join(
        "name LIKE '%s' OR mail LIKE '%s'" % (lk.replace("'", "''"), lk.replace("'", "''"))
        for lk in likes
    )
    body = DB_BOOT + (
        "$where = \"admin = 0 AND (%s)\";\n" % conds
    ) + (
        "echo \"== Candidate test/demo accounts (admin rows excluded) ==\\n\";\n"
        "$r = $m->query(\"SELECT user_id,name,mail,active,ban_global,active_code FROM user WHERE $where ORDER BY user_id\");\n"
        "$n=0; while($r && $row=$r->fetch_assoc()){ $n++;\n"
        "  printf(\"  uid=%-6s name='%-20s' mail=%-26s active=%s ban=%s unconfirmed=%s\\n\",\n"
        "    $row['user_id'], substr($row['name'],0,20), mask($row['mail']), $row['active'], $row['ban_global'],\n"
        "    ($row['active_code']!==''&&$row['active_code']!==null)?'Y':'N'); }\n"
        "echo \"\\n  matched: $n  (review these, then run with --apply --ids <list>)\\n\";\n"
    )
    run_php(body)


def set_active(ids, value):
    id_list = ",".join(str(int(i)) for i in ids)
    body = DB_BOOT + (
        "$ids = '%s';\n" % id_list
    ) + (
        "echo \"== BEFORE ==\\n\";\n"
        "$r=$m->query(\"SELECT user_id,name,mail,active,admin FROM user WHERE user_id IN ($ids) ORDER BY user_id\");\n"
        "while($r && $row=$r->fetch_assoc()){ printf(\"  uid=%-6s name='%-20s' mail=%-26s active=%s admin=%s\\n\",\n"
        "  $row['user_id'],substr($row['name'],0,20),mask($row['mail']),$row['active'],$row['admin']); }\n"
        # admin = 0 guard: never change an admin account
        "$m->query(\"UPDATE user SET active=%d WHERE user_id IN ($ids) AND admin = 0\");\n" % value
    ) + (
        "echo \"\\n== AFTER (admin rows left untouched) ==\\n\";\n"
        "$r=$m->query(\"SELECT user_id,name,mail,active,admin FROM user WHERE user_id IN ($ids) ORDER BY user_id\");\n"
        "while($r && $row=$r->fetch_assoc()){ printf(\"  uid=%-6s name='%-20s' mail=%-26s active=%s admin=%s\\n\",\n"
        "  $row['user_id'],substr($row['name'],0,20),mask($row['mail']),$row['active'],$row['admin']); }\n"
    )
    run_php(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="hide the given --ids (active=0)")
    ap.add_argument("--unhide", action="store_true", help="restore the given --ids (active=1)")
    ap.add_argument("--ids", default="", help="comma-separated user_ids to hide/unhide")
    ap.add_argument("--like", action="append", help="LIKE pattern for audit (repeatable)")
    args = ap.parse_args()

    if args.apply or args.unhide:
        ids = [s for s in args.ids.replace(" ", "").split(",") if s]
        if not ids:
            raise SystemExit("--apply/--unhide requires --ids (e.g. --ids 12,15,16)")
        set_active(ids, 0 if args.apply else 1)
    else:
        audit(args.like or DEFAULT_LIKES)


if __name__ == "__main__":
    main()
