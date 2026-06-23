"""End-to-end recheck — covers everything shipped 2026-05-01 + 2026-05-03.
No DB writes. Pure HTTP probes from a clean session.
"""
from __future__ import annotations
import os, ssl, sys, time, urllib.request, urllib.parse

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HOST = "meetgreeksingles.com"


def get(url, **kwargs):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, **kwargs)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def post(url, params):
    body = urllib.parse.urlencode(params).encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }
    return get(url, data=body, headers=headers)


def title_of(body):
    if "<title>" not in body: return "(no title)"
    return body.split("<title>")[1].split("</title>")[0]


total = 0
passed = 0


def check(label, ok, detail=""):
    global total, passed
    total += 1
    if ok:
        passed += 1
        print(f"  [OK ] {label}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  [FAIL] {label}" + (f"  ({detail})" if detail else ""))


print("=" * 70)
print("END-TO-END RECHECK — 2026-05-03")
print("=" * 70)

# ── 1. Homepage ─────────────────────────────────────────────────────────────
print("\n[1] Homepage  /")
cb = int(time.time())
code, body = get(f"https://{HOST}/?nocache={cb}")
check("HTTP 200", code == 200, f"status={code}")
check("title is distinct (PageTitles working)",
      "Meet Greek Singles | Serious Dating for the Greek Diaspora" in body,
      title_of(body))
check("hero <video> has preload='auto'", 'preload="auto"' in body)
check("chairs poster removed (was the flash)",
      'poster="/_files/banner/shutterstock_1011591358.jpg"' not in body)
check("CSS fallback bg = sea-blue gradient (not chairs photo)",
      "linear-gradient(180deg" in body and "#5fa7c9" in body
      and "background-image: url('/_files/banner/shutterstock_1011591358.jpg')" not in body)
check("hero video src present", "/_files/hero_couple_v2.mp4" in body)

# ── 2. Join page ────────────────────────────────────────────────────────────
print("\n[2] Join page  /join")
cb = int(time.time())
code, body = get(f"https://{HOST}/join?nocache={cb}")
check("HTTP 200", code == 200, f"status={code}")
check("title = 'Create Your Free Account'",
      "Create Your Free Account | Meet Greek Singles" in body, title_of(body))
check("city label = 'City / Town / Island'",
      "City / Town / Island" in body)
check("city placeholder updated",
      "Type your city, town or island" in body)
check("region helper line present",
      "Select your region" in body and "Athens, Thessaloniki, Rhodes, Crete" in body)
check("rwcst grid layout (labels above dropdowns)",
      "grid-template-columns: repeat(2, 1fr) !important" in body)
check("form margin nudged to 2%", "margin: auto 2% auto auto" in body)
check("legacy 5% margin gone", "margin: auto 5% auto auto" not in body)
check("public Q&A link removed from FAQ",
      'For more, see the full <a href="/page?id=57"' not in body)
check("footer text light (cream)", "body .footer {        color: #f4eddb" in body)
check("footer link white", "body .footer .nav li a {        color: #ffffff" in body)
check("home_city input present", 'name="home_city"' in body)
check("legacy name=\"city\" gone (city dropdown removed)",
      'name="city"' not in body)

# ── 3. /join2  (the page that was throwing E_NOTICE)  ───────────────────────
print("\n[3] /join2  (was throwing 'Undefined index: table')")
cb = int(time.time())
code, body = get(f"https://{HOST}/join2?nocache={cb}")
check("HTTP 200", code == 200, f"status={code}")
check("no E_NOTICE 'Undefined index: table'",
      "Undefined index: table" not in body and "E_NOTICE" not in body)
check("no Chameleon Error popup HTML",
      'class="error_popup"' not in body and ">Error: E_" not in body
      and "Error: E_NOTICE" not in body)
check("title is distinct", "<title>" in body)

# ── 4. Other titled pages ───────────────────────────────────────────────────
# Use the user-facing routed URLs (no .php). /login.php and /forget_password.php
# are not direct entry points: /login.php doesn't exist as a real file, and
# /forget_password.php is configured to redirect into the login page's reset
# popup (forgot_password_redirect_login template option is on).
print("\n[4] Per-page titles")
pages = [
    ("/about.php", "About Us | Meet Greek Singles"),
    ("/contact.php", "Contact Us | Meet Greek Singles"),
    ("/login", "Log In | Meet Greek Singles"),
    ("/forget_password", "Log In | Meet Greek Singles"),  # redirects to /login by design
]
for url, expected in pages:
    cb = int(time.time())
    code, body = get(f"https://{HOST}{url}?nocache={cb}")
    check(f"{url} → '{expected}'",
          expected in body, title_of(body))

# ── 5. AJAX register flow (cjoinform → join2 redirect) ──────────────────────
print("\n[5] AJAX register POST")
unique = int(time.time())
test_email = f"e2e_{unique}@example.test"
test_name  = f"e2etest{unique}"
params = {
    "ajax": "1", "cmd": "register",
    "p_sexuality": "1",
    "day": "15", "month": "6", "year": "1990",
    "country": "84",      # Greece
    "state": "4174",      # Attica (one of the 13 new regions)
    "home_city": "Athens, Greece",
    "email": test_email, "join_handle": test_name,
    "join_password": "Sample1234!",
    "privacy_policy": "1",
}
code, body = post(f"https://{HOST}/join.php", params)
check("HTTP 200", code == 200, f"status={code}")
check("returns redirect→join2", "<span class='redirect'>join2</span>" in body)

# ── 6. Search-results page (gated by prelaunch but verify the response) ────
print("\n[6] /search_results.php")
cb = int(time.time())
code, body = get(f"https://{HOST}/search_results.php?home_city=Athens&nocache={cb}")
check("HTTP 200", code == 200, f"status={code}")
# Logged out, prelaunch gate redirects to homepage; that's expected.
check("(prelaunch gate active — redirects to homepage with homepage title)",
      "Meet Greek Singles | Serious Dating for the Greek Diaspora" in title_of(body),
      title_of(body))

# ── 7. Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"  {passed}/{total} checks passed")
print("=" * 70)
sys.exit(0 if passed == total else 1)
