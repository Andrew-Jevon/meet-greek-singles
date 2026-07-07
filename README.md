# Meet Greek Singles

PHP dating site built on **Chameleon Social Software 5.7**. This repo holds the
source; the runnable site is **assembled** by `setup.ps1` (the webroot is not
committed because it is derived).

## Repository layout

| Path | What it is | In git? |
|------|-----------|---------|
| `_core_extract/chameleon_social_software_5.7/` | Framework core (`_include/core`, `_include/lib`) | ✅ |
| `upstream/` | Site content + customizations + brand media (`_files`) | ✅ |
| `db/meetgreeksingles.sql` | Schema + seed dump (clean baseline, no member data) | ✅ |
| `_local_run/` | Local dev harness: `router.php`, `start-local.ps1`, `start-both.ps1` | ✅ (webroot excluded) |
| `_deploy_tars/`, `_vendor_installer/` | Deploy tarballs / product installer (100s of MB) | ❌ ignored |

> **Why the split?** Neither `_core_extract` nor `upstream` runs alone — the core
> provides the framework, `upstream` overlays the site. `setup.ps1` merges them
> (core first, `upstream` on top) into `_local_run/webroot/`.

## Quick start

```powershell
# 1. Assemble webroot + write db.php + import the database
powershell -ExecutionPolicy Bypass -File setup.ps1

# 2. Run it
powershell -ExecutionPolicy Bypass -File _local_run\start-local.ps1
#    → http://127.0.0.1:8080
```

### Requirements
- PHP 8.2+ on PATH with the **mysqli** extension enabled
- MariaDB/MySQL running locally (root reachable)

## Notes / gotchas
- **mysqli required** — the app auto-selects it on PHP 8.2; enable `extension=mysqli` in `php.ini`.
- **Legacy PHP warnings** — `start.php` lowers `error_reporting` so PHP 8.2 `foreach(null)`
  warnings don't render fatal pages.
- **Pretty URLs** — `_local_run/router.php` emulates the `.htaccess` rewrites
  (`/login` → `join.php?cmd=please_login`, MultiViews, SEO profile URLs) and spoofs
  the production hostname so the ionCube domain-locked license validates.
- **No member data** — the DB dump is a clean baseline (`users` table empty).
  Some production-only media (e.g. `hero_couple_v2.jpg` hero poster) live only on
  the production server and are not in this repo.
- **Secrets** — `_include/config/db.php` is git-ignored; `setup.ps1` generates it.
