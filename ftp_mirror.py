"""
Selective FTPS mirror for meetgreeksingles.com production review.
Password is read from /tmp/mgs/p (file, 0600).
Produces a local tree under the DEST dir with progress + retry.
"""

from __future__ import annotations
import ftplib, os, posixpath, socket, ssl, sys, time
from pathlib import Path


# Pure-FTPd requires TLS session reuse between control and data channels.
# Standard Python ftplib.FTP_TLS does not do this by default → data channel
# hangs silently. This subclass wires the control-channel session into each
# new data channel. Canonical workaround; known-good pattern.
class _ReusedSSL(ssl.SSLSocket):
    def unwrap(self):
        pass


class FTP_TLS_Reuse(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            session = getattr(self.sock, "session", None)
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=session
            )
            conn.__class__ = _ReusedSSL
        return conn, size

HOST = "meetgreeksingles.com"
USER = "everett@meetgreeksingles.com"
PASSWORD = os.environ.get("MGS_PASS")
if not PASSWORD:
    sys.exit("ERROR: MGS_PASS env var not set")

# Directories to skip anywhere in the tree (basename match).
SKIP_DIRS = {
    # User-uploaded content — we do not need any of it for source review.
    "gallery", "photo", "video", "music", "music_musician_images",
    "music_song_images", "wall", "events_event_images", "groups_group_images",
    "outside_images", "audio_greeting", "im_audio_message", "postcard",
    "gifts", "banner", "bio", "profile_bg_cover", "profile_bg_cover_group",
    "places_images", "adv_images", "editor", "3dchat", "yahoo", "temp",
    "city", "cache", "blogs",
    # tmp buckets and logs (not useful for source review)
    "tmp", "logs",
    # Non-essential theme variants (we have Impact desktop; skip installer,
    # mobile templates, and affiliate theme for first pull — cheap to add later
    # with a targeted run if M4/M5/M6 actually need them)
    "install", "mobile", "partner",
    # Translations — ~50 languages × ~50 files each = thousands of tiny files.
    # We do not need them for structural code work.
    "_lang",
    # Current/parent pointers
    ".", "..",
}

# Roots to mirror under the FTP home. Everything else at root is copied by file.
TOP_LEVEL_DIRS_TO_MIRROR = {
    "_cron", "_frameworks", "_include", "_lang", "_pay", "_server",
    "administration", "ioncube", "m", "partner", ".well-known",
    # _files is special: we mirror its small config subdirs only
}

# Subset of _files to pull (small, config-like)
FILES_SUBDIR_ALLOWLIST = {"logo", "tmpl"}

DEST = Path("/d/Freelancer-Project/Everetts/Irene/site/upstream")
DEST.mkdir(parents=True, exist_ok=True)

def connect() -> FTP_TLS_Reuse:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS_Reuse(HOST, USER, PASSWORD, timeout=60, context=ctx)
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp

class Stats:
    files = 0
    bytes = 0
    skipped = 0

stats = Stats()
t0 = time.time()

def log(msg: str):
    print(f"[{int(time.time()-t0):4d}s] {msg}", flush=True)

def list_dir(ftp: ftplib.FTP_TLS, remote: str):
    entries = []
    ftp.cwd(remote)
    ftp.retrlines("LIST -a", entries.append)
    ftp.cwd("/")
    parsed = []
    for line in entries:
        parts = line.split(None, 8)
        if len(parts) < 9:
            continue
        perms, _, _, _, size, _, _, _, name = parts
        if name in (".", ".."):
            continue
        is_dir = perms.startswith("d")
        parsed.append((is_dir, int(size) if size.isdigit() else 0, name))
    return parsed

def download_file(ftp: ftplib.FTP_TLS, remote: str, local: Path, expected_size: int = -1):
    # Skip if already on disk with matching size — massive win on resumed runs.
    if expected_size >= 0 and local.exists() and local.stat().st_size == expected_size:
        return -1  # sentinel: skipped, caller does not count
    local.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            with local.open("wb") as f:
                ftp.retrbinary(f"RETR {remote}", f.write)
            return local.stat().st_size
        except Exception as e:
            log(f"  retry {attempt+1} on {remote}: {e}")
            time.sleep(2)
            try:
                ftp.voidcmd("NOOP")
            except Exception:
                pass
    raise RuntimeError(f"Failed to download {remote}")

def mirror(ftp: ftplib.FTP_TLS, remote: str, local: Path, files_allowlist: set[str] | None = None):
    entries = list_dir(ftp, remote)
    for is_dir, size, name in entries:
        rpath = posixpath.join(remote, name) if remote != "/" else "/" + name
        lpath = local / name
        if is_dir:
            if name in SKIP_DIRS:
                stats.skipped += 1
                continue
            if files_allowlist is not None and name not in files_allowlist:
                stats.skipped += 1
                continue
            lpath.mkdir(parents=True, exist_ok=True)
            mirror(ftp, rpath, lpath)
        else:
            if files_allowlist is not None:
                continue
            try:
                n = download_file(ftp, rpath, lpath, expected_size=size)
                if n == -1:
                    stats.skipped += 1
                else:
                    stats.files += 1
                    stats.bytes += n
                    if stats.files % 50 == 0:
                        log(f"  {stats.files} new files, {stats.bytes//1024} KB pulled (skipped {stats.skipped} existing)")
            except Exception as e:
                log(f"  ERROR {rpath}: {e}")

def main():
    log(f"connecting {HOST}")
    ftp = connect()
    log(f"logged in as {USER}")

    # 1. All root-level files
    log("listing root")
    root_entries = list_dir(ftp, "/")
    root_files = [(s, n) for d, s, n in root_entries if not d]
    log(f"root has {len(root_files)} files")
    for size, name in root_files:
        lpath = DEST / name
        try:
            n = download_file(ftp, "/" + name, lpath, expected_size=size)
            if n == -1:
                stats.skipped += 1
            else:
                stats.files += 1
                stats.bytes += n
        except Exception as e:
            log(f"  ERROR /{name}: {e}")
    log(f"root files done. {stats.files} files, {stats.bytes//1024} KB so far")

    # 2. Top-level dirs we want
    for d in sorted(TOP_LEVEL_DIRS_TO_MIRROR):
        if any(rd_name == d for _, _, rd_name in [(True, 0, e[2]) for e in root_entries if e[0]]):
            log(f"mirroring /{d}")
            mirror(ftp, "/" + d, DEST / d)
            log(f"  /{d} done. cumulative: {stats.files} files, {stats.bytes//1024} KB")

    # 3. _files/logo and _files/tmpl only
    log("mirroring /_files (allowlist: logo, tmpl)")
    mirror(ftp, "/_files", DEST / "_files", files_allowlist=FILES_SUBDIR_ALLOWLIST)
    log(f"  /_files done. cumulative: {stats.files} files, {stats.bytes//1024} KB")

    ftp.quit()
    log(f"DONE. {stats.files} files, {stats.bytes//1024} KB, {stats.skipped} dirs skipped")

if __name__ == "__main__":
    main()
