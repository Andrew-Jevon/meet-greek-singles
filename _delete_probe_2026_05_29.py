"""
Delete the onboarding-options probe from production after running it.

Run after the probe output has been captured to disk:
    $env:PROD_PASS = '<password>'
    python d:\MyProjects\Irene\Irene\Irene\site\_delete_probe_2026_05_29.py
"""

import os, sys, ftplib, ssl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PROBE = "_mgs_probe_onboarding_options_2026_05_28.php"

password = os.environ.get("PROD_PASS")
if not password:
    print("ERROR: set $env:PROD_PASS first.")
    sys.exit(1)

ftp = FTP_TLS_Reuse(HOST)
ftp.login(USER, password)
ftp.prot_p()
ftp.cwd("/")

try:
    ftp.delete(PROBE)
    print(f"DELETED /public_html/{PROBE}")
except ftplib.error_perm as e:
    print(f"Could not delete (may already be gone): {e}")

ftp.quit()
