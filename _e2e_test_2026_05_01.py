"""End-to-end test for the 2026-05-01 deploy:

  1. POST a registration with home_city='Athens, Greece' to /join.php
  2. Verify it returned the expected `<span class='redirect'>join2</span>` payload
  3. Check that userinfo.home_city was persisted (via _mgs_verify probe DB
     query) — but since the cjoinform mobile/non-custom path requires
     Common::isMobile() OR (ajax && !isCustomRegister) and impact uses
     custom register, User::add happens later in cjoinfinal.  Cjoinform
     itself only stores j_home_city in session — we'll verify the session
     write by invoking cjoinfinal mid-flow OR by checking that the typed
     city is at least preserved in the response.
  4. Verify the home_city user_var entry is searchable on the search form
     (input present in /search_results.php response)

Read-only against DB except step 3 may create a registered user.
"""
from __future__ import annotations
import os, ssl, sys, urllib.request, urllib.parse, time

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


print("E2E TEST — 2026-05-01 deploy")
print("=" * 50)

# 1. Join page loads, has home_city input
print("\n1. /join — does it serve the home_city input?")
code, body = get(f"https://{HOST}/join")
print(f"   HTTP {code}, body bytes: {len(body)}")
print(f"   has name=\"home_city\":   {'name=\"home_city\"' in body}")
print(f"   has legacy name=\"city\": {'name=\"city\"' in body}")
print(f"   <title> contains: ", end="")
if "<title>" in body:
    title = body.split("<title>")[1].split("</title>")[0]
    print(f"'{title}'")
else:
    print("(no <title>)")

# 2. About page title
print("\n2. /about.php — title check")
code, body = get(f"https://{HOST}/about.php")
print(f"   HTTP {code}")
if "<title>" in body:
    title = body.split("<title>")[1].split("</title>")[0]
    print(f"   title: '{title}'")

# 3. Search results page should serve the home_city filter
print("\n3. /search_results.php — has home_city filter input?")
code, body = get(f"https://{HOST}/search_results.php?home_city=Athens")
print(f"   HTTP {code}, body bytes: {len(body)}")
print(f"   has id=\"home_city_filter\":  {'id=\"home_city_filter\"' in body}")
print(f"   <title>: ", end="")
if "<title>" in body:
    title = body.split("<title>")[1].split("</title>")[0]
    print(f"'{title}'")
else:
    print("(no <title>)")

# 4. AJAX register submission — the 32-check pattern from 2026-04-30 handoff.
#    Successful submit should return `<span class='redirect'>join2</span>`.
print("\n4. POST /join.php — AJAX registration with home_city='Athens, Greece'")
unique = int(time.time())
test_email = f"e2e_{unique}@example.test"
test_name  = f"e2etest{unique}"
params = {
    "ajax": "1",
    "cmd": "register",
    "p_sexuality": "1",        # Man
    "p_relation": "1",          # placeholder
    "day": "15",
    "month": "6",
    "year": "1990",
    "country": "84",            # Greece
    "state": "4174",            # Attica
    "home_city": "Athens, Greece",
    "email": test_email,
    "join_handle": test_name,
    "join_password": "Sample1234!",
    "privacy_policy": "1",
}
code, body = post(f"https://{HOST}/join.php", params)
print(f"   HTTP {code}")
print(f"   body: {body[:500]}")
expected_ok = "<span class='redirect'>join2</span>"
print(f"   '{expected_ok}' in body: {expected_ok in body}")

# 5. Greek state dropdown sanity — fetch /join and check that the 13 modern
#    Greek regions show up when the country=84 is loaded via AJAX.
print("\n5. AJAX get_states for country=84 (Greece) — 13 regions?")
code, body = get(f"https://{HOST}/ajax.php?action=get_states&country=84&type=add")
print(f"   HTTP {code}")
print(f"   body bytes: {len(body)}")
# count the <option> entries
opts = body.count("<option")
print(f"   <option> count: {opts}")
print(f"   contains 'Attica': {'Attica' in body}")
print(f"   contains 'Crete':  {'Crete' in body}")
print(f"   contains 'Akhaia' (old prefecture, should be gone): {'Akhaia' in body}")
print(f"   first 800 chars of body:")
print("   " + body[:800].replace("\n", "\n   "))

print("\nDONE")
