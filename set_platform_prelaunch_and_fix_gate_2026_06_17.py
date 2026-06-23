"""2026-06-17 — Lock the site to registration-only and fix the pre-launch gate.

Per Irene (urgent): Search, member Profiles and Events were reachable without
login, exposing test/demo accounts. This script:

  1. Uploads the corrected pre-launch gate (upstream/_include/current/
     prelaunch.class.php) which now splits the allowlist into a PUBLIC tier
     (Home/About/Contact/Registration/Login + legal) and a MEMBER-ONLY tier
     (profile/account pages). Search / Events / Advice / member profiles are no
     longer public.
  2. Sets config option platform_mode = 'prelaunch' so the gate is actually
     enforced (a prior i18n deploy may have flipped it to 'live').
  3. Prints before/after for verification.

Connection: explicit FTP over TLS on port 21 (FileZilla-style). Requires PROD_PASS.

Run:
    $env:PROD_PASS = '<production FTPS password>'
    $env:DEPLOY_TARGET = 'prod'
    python set_platform_prelaunch_and_fix_gate_2026_06_17.py
"""
import io
import os
import secrets
import ssl
import sys
import ftplib
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "meetgreeksingles.com"
TOKEN = secrets.token_hex(16)
ROOT = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = os.path.join(ROOT, "upstream")
CONNECT_TIMEOUT = int(os.environ.get("PROD_FTP_TIMEOUT", "120"))

# DEPLOY_TARGET=staging deploys to the chrooted staging account (and the
# /staging URL space); anything else (default) deploys to production root.
TARGET = os.environ.get("DEPLOY_TARGET", "prod").lower()
if TARGET == "staging":
    USER = os.environ.get("STAGING_USER", "staging@meetgreeksingles.com")
    URL_BASE = f"https://{HOST}/staging"
else:
    USER = os.environ.get("PROD_USER", "everett@meetgreeksingles.com")
    URL_BASE = f"https://{HOST}"

PHP = f"""<?php
if (($_GET['token'] ?? '') !== '{TOKEN}') {{ http_response_code(403); exit('forbidden'); }}
header('Content-Type: application/json; charset=utf-8');
$g = array(); require __DIR__ . '/_include/config/db.php';
$m = new mysqli($g['db']['host'], $g['db']['user'], $g['db']['password'], $g['db']['db']);
$m->set_charset('utf8mb4');
$before = $m->query("SELECT value FROM config WHERE module='options' AND `option`='platform_mode'")->fetch_assoc();
$m->query("UPDATE config SET value='prelaunch' WHERE module='options' AND `option`='platform_mode'");
$after = $m->query("SELECT value FROM config WHERE module='options' AND `option`='platform_mode'")->fetch_assoc();
echo json_encode(['ok'=>true,'before'=>$before['value']??null,'after'=>$after['value']??null], JSON_PRETTY_PRINT);
"""


def log(step, message):
    print(f"[{step}] {message}", flush=True)


def fail_tls(stage, exc):
    log("error", f"TLS/connect failed during: {stage}")
    log("error", f"  {type(exc).__name__}: {exc}")
    log("error", "Explicit FTP over TLS on port 21 could not complete.")
    log("error", "Check: host meetgreeksingles.com, username, PROD_PASS, firewall/VPN,")
    log("error", "and that FileZilla is set to 'FTP over TLS (explicit)' on port 21.")
    sys.exit(1)


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    """Explicit FTPS with TLS session reuse on the data channel (GoDaddy needs this)."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


def get_password():
    if TARGET == "staging":
        password = os.environ.get("STAGING_PASS") or os.environ.get("PROD_PASS")
        if not password:
            log("error", "Set STAGING_PASS or PROD_PASS before running (staging deploy).")
            sys.exit(1)
        return password

    password = os.environ.get("PROD_PASS")
    if not password:
        log("error", "Set PROD_PASS before running this script.")
        log("error", "  PowerShell:  $env:PROD_PASS = '<your FTPS password>'")
        sys.exit(1)
    return password


def ftp_connect(password):
    """Connect with explicit FTP over TLS on port 21 (FileZilla default)."""
    port = 21
    log("connect", f"Host={HOST}  Port={port}  Mode=explicit FTP over TLS  User={USER}")
    log("connect", f"Timeout={CONNECT_TIMEOUT}s")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    ftp = FTP_TLS_Reuse(context=ctx)
    try:
        log("connect", f"Opening TCP connection to {HOST}:{port} ...")
        ftp.connect(HOST, port, CONNECT_TIMEOUT)
        welcome = getattr(ftp, "welcome", None)
        log("connect", f"TCP connected. Server banner: {welcome!r}")
    except (TimeoutError, OSError, ssl.SSLError) as exc:
        fail_tls("TCP connect on port 21", exc)

    try:
        log("connect", f"Sending USER/PASS and negotiating TLS (AUTH TLS) ...")
        ftp.login(USER, password)
        log("connect", "Login OK.")
    except (TimeoutError, OSError, ssl.SSLError) as exc:
        fail_tls("login / AUTH TLS handshake", exc)
    except ftplib.error_perm as exc:
        log("error", f"FTP login rejected: {exc}")
        log("error", "Verify PROD_USER / PROD_PASS (or STAGING_USER / STAGING_PASS).")
        sys.exit(1)

    try:
        log("connect", "Enabling TLS on data channel (PROT P) ...")
        ftp.prot_p()
        log("connect", "PROT P OK.")
    except (TimeoutError, OSError, ssl.SSLError) as exc:
        fail_tls("PROT P (data-channel TLS)", exc)
    except ftplib.error_perm as exc:
        log("error", f"PROT P rejected: {exc}")
        sys.exit(1)

    log("connect", "Entering passive mode (PASV) ...")
    ftp.set_pasv(True)
    log("connect", "PASV enabled.")

    try:
        cwd = ftp.pwd()
        log("connect", f"Session ready. Remote cwd={cwd!r}")
    except ftplib.error_perm as exc:
        log("connect", f"Session ready (pwd unavailable: {exc})")

    return ftp


def backup_remote(ftp, remote_path, local_backup_dir):
    """Download the current live copy of remote_path before we overwrite it."""
    os.makedirs(local_backup_dir, exist_ok=True)
    fname = remote_path.replace("\\", "/").split("/")[-1]
    backup_path = os.path.join(local_backup_dir, fname + ".prod-backup")
    log("backup", f"Downloading live {remote_path} ...")
    try:
        with open(backup_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)
        size = os.path.getsize(backup_path)
        log("backup", f"Saved {size} bytes -> {backup_path}")
        return backup_path
    except ftplib.error_perm as exc:
        log("backup", f"No remote backup taken for {remote_path} ({exc})")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return None
    except (TimeoutError, OSError, ssl.SSLError) as exc:
        fail_tls(f"backup RETR {remote_path}", exc)


def upload_file(ftp, local_path, remote_path):
    if not os.path.isfile(local_path):
        log("error", f"Local file missing: {local_path}")
        sys.exit(1)

    parts = remote_path.replace("\\", "/").split("/")
    fname = parts[-1]
    dirs = parts[:-1]
    local_size = os.path.getsize(local_path)

    log("upload", f"Uploading {local_path} ({local_size} bytes) -> {remote_path}")
    ftp.cwd("/")
    for d in dirs:
        try:
            ftp.mkd(d)
        except ftplib.error_perm:
            pass
        ftp.cwd(d)
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {fname}", f)
    log("upload", f"Uploaded {remote_path}")


def set_platform_mode(ftp):
    name = "_mgs_set_prelaunch.php"
    url = f"{URL_BASE}/{name}?token={TOKEN}"

    log("platform_mode", f"Uploading temporary probe {name} ...")
    ftp.cwd("/")
    ftp.storbinary(f"STOR {name}", io.BytesIO(PHP.encode()))
    log("platform_mode", f"Probe uploaded. Calling {url} ...")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "set_platform_prelaunch_and_fix_gate/2026-06-17"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            log("platform_mode", f"HTTP {resp.status} response:")
            print(body, flush=True)
    except urllib.error.URLError as exc:
        log("error", f"Could not run platform_mode probe over HTTPS: {exc}")
        log("error", "FTP upload succeeded; run _check_platform_mode.py or verify in admin.")
        sys.exit(1)
    finally:
        log("platform_mode", f"Removing temporary probe {name} ...")
        try:
            ftp.cwd("/")
            ftp.delete(name)
            log("platform_mode", "Probe removed.")
        except ftplib.error_perm as exc:
            log("platform_mode", f"Could not delete probe (remove manually): {exc}")


def main():
    password = get_password()
    local_gate = os.path.join(UPSTREAM, "_include/current/prelaunch.class.php")
    gate_remote = "_include/current/prelaunch.class.php"

    log("deploy", f"TARGET={TARGET.upper()}  URL_BASE={URL_BASE}")
    log("deploy", f"Local gate file: {local_gate}")
    if not os.path.isfile(local_gate):
        log("error", f"Missing deploy source: {local_gate}")
        sys.exit(1)
    log("deploy", f"Local gate size: {os.path.getsize(local_gate)} bytes")

    ftp = ftp_connect(password)
    ftp.cwd("/")

    backup_remote(
        ftp,
        gate_remote,
        os.path.join(ROOT, "_backup", "prelaunch_2026_06_17"),
    )
    ftp.cwd("/")

    upload_file(ftp, local_gate, gate_remote)

    set_platform_mode(ftp)

    log("deploy", "Closing FTP session ...")
    ftp.quit()
    log("deploy", "Done.")


if __name__ == "__main__":
    main()
