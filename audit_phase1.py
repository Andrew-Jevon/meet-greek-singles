"""
Phase 1 audit — guest surface.

For each public-facing URL fetches with desktop + iPhone UA, inspects the
HTML body for: status, viewport meta, page title, key content markers,
PHP runtime errors, broken templates, suspect inline content, and surface
visual issues we can detect from HTML alone.

Output: bug findings, one per line, machine-friendly.
"""
from __future__ import annotations
import urllib.request, sys, re, html

BASE = "https://meetgreeksingles.com"
UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"

PHP_ERR_RE = re.compile(r"<b>(Fatal error|Parse error|Warning|Notice|Deprecated)</b>|"
                        r"Uncaught \w*Exception|"
                        r"Call to undefined function|"
                        r"pp_installator|Stack trace:")

def fetch(url, ua, follow=True):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "en"})
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(NR())
    else:
        op = urllib.request.build_opener()
    op.addheaders = [("User-Agent", ua)]
    try:
        r = op.open(req, timeout=30)
        return r.status, r.read().decode("utf-8", errors="replace"), dict(r.headers), r.url
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace") if hasattr(e,"read") else ""
        return e.code, body, dict(e.headers), e.url if hasattr(e,"url") else url

bugs = []
def bug(page, severity, msg):
    bugs.append((page, severity, msg))

PAGES = [
    ("/",                              "homepage",          ["preparing for our official launch", "Find the Greek Connection", "Join us now"]),
    ("/about.php",                     "about",             []),
    ("/contact.php",                   "contact",           ["Send us a message", "Get in touch"]),
    ("/help.php",                      "help (guest Q&A)",  ["Common questions about Meet Greek Singles", "Join to read full answers"]),
    ("/info.php?page=term_cond",       "terms",             []),
    ("/info.php?page=priv_policy",     "privacy",           []),
    ("/login",                         "login",             ["Welcome", "Sign in"]),
    ("/forget_password.php",           "forget_password",   []),
    ("/join",                          "join welcome",      ["Welcome to Meet Greek Singles", "Greek Singles!"]),
    ("/email_not_confirmed.php",       "email_not_confirmed", []),
]

print("=" * 75)
print(" PHASE 1 — GUEST SURFACE AUDIT")
print("=" * 75)
print()

for path, label, must_have in PAGES:
    print(f"--- {label}  ({BASE}{path}) ---")
    # Desktop fetch
    st, body, hdrs, final = fetch(BASE + path, UA_DESKTOP)

    # 1. Status code check
    if st == 302:
        loc = hdrs.get("Location", "")
        bug(label, "INFO", f"302 → {loc}  (expected for some auth-gated pages)")
    elif st != 200:
        bug(label, "FAIL", f"non-200 status: {st}")

    # 2. PHP error check
    err = PHP_ERR_RE.search(body)
    if err:
        bug(label, "FAIL", f"PHP runtime error in body: {err.group(0)}")

    # 3. Viewport meta
    if "<meta name=\"viewport\"" not in body and "<meta name='viewport'" not in body:
        bug(label, "FAIL", "no <meta name=\"viewport\">")
    elif "device-width" not in body[:5000]:
        bug(label, "WARN", "viewport not responsive (no device-width)")

    # 4. Mobile-safety CSS present
    if "impact-mobile-safety-head" not in body and "impact-mobile-safety-final" not in body:
        bug(label, "WARN", "mobile-safety CSS not in body")

    # 5. Footer order check
    m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
    if m and "About" in m.group(1):
        items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
        expected = ["About", "Terms & Conditions", "Privacy Policy", "Questions & Answers", "Contact us"]
        if items != expected and len(items) > 0:
            bug(label, "WARN", f"footer order odd: {items}")

    # 6. Mandatory content present
    for marker in must_have:
        if marker not in body:
            bug(label, "FAIL", f"missing expected content: {marker!r}")

    # 7. Mobile UA check — same page, mobile UA, look for /m/ redirect
    st_m, body_m, hdrs_m, _ = fetch(BASE + path, UA_IPHONE, follow=False)
    if st_m == 302:
        loc = hdrs_m.get("Location", "")
        if "/m/" in loc:
            bug(label, "FAIL", f"mobile UA redirected to legacy /m/ theme: {loc}")
    elif st_m == 200:
        # Mobile served impact theme — quick check: viewport responsive?
        if "device-width" not in body_m[:5000]:
            bug(label, "WARN", "mobile UA: viewport not device-width")

    # 8. Inline error attribs (e.g., disabled buttons, broken onclick=)
    if "onclick=\"\"" in body or "onclick=''" in body:
        bug(label, "WARN", "empty onclick handler")
    if "href=\"\"" in body[:50000]:
        # too noisy; only flag if it's on a primary button
        pass

    # 9. Empty form actions
    forms = re.findall(r'<form\s+[^>]*action="([^"]*)"', body)
    for fa in forms:
        if not fa.strip() or fa == "#":
            bug(label, "WARN", f"form has empty/# action: {fa!r}")

    # 10. Specific layout pitfalls
    if "calc(100vw" in body and "100vw - " in body:
        # noisy — skip if already overridden
        pass

    # 11. Page-specific marker checks
    if label == "homepage":
        if "joinpage" in body:
            bug(label, "INFO", "joinpage class on homepage body (likely from JS)")
        # Banner present?
        if "begin_prelaunch_banner" in body:
            bug(label, "WARN", "begin_prelaunch_banner unparsed marker leaking into body")
    elif label == "help (guest Q&A)":
        # 4 sample topics?
        topic_count = sum(1 for t in [
            "How is Meet Greek Singles different",
            "Is the platform open to non-Greeks",
            "How do you keep the community safe",
            "What is included in a free account",
        ] if t in body)
        if topic_count != 4:
            bug(label, "WARN", f"only {topic_count}/4 sample help topics rendered")
    elif label == "join welcome":
        # Should have the welcome card or the form
        has_welcome = "Welcome to Meet Greek Singles" in body
        has_form = "frm_register_submit" in body or "type=\"submit\"" in body
        if not has_welcome and not has_form:
            bug(label, "WARN", "neither welcome card nor sign-up form on /join")
    elif label == "login":
        if "Sign in" not in body:
            bug(label, "FAIL", "Sign in button missing on login page")
    elif label == "contact":
        if "Browse our help" not in body:
            bug(label, "WARN", "help link missing on contact page (help option may be off)")

    # 12. Dump the matched bugs for this page
    print(f"  status={st}  body={len(body)}b  mobile_status={st_m}")
    print()

# Footer order on homepage vs join (must be the 5 keepers in order)
print("--- footer rendering across pages ---")
for path, label, _ in PAGES[:5]:  # check first 5 pages
    _, body, _, _ = fetch(BASE + path, UA_DESKTOP)
    m = re.search(r'<ul class="nav">(.*?)</ul>', body, re.DOTALL)
    if m:
        items = re.findall(r'>([A-Za-z& ]+?)</a>', m.group(1))
        print(f"  {label}: {items}")

# Performance summary
print()
print("--- render timings (desktop UA) ---")
import time
for path, label, _ in PAGES:
    t0 = time.time()
    fetch(BASE + path, UA_DESKTOP)
    elapsed = (time.time() - t0) * 1000
    print(f"  {label:25s}  {elapsed:>6.0f} ms")

# === FINAL BUG LIST ===
print()
print("=" * 75)
print(" BUG LIST")
print("=" * 75)
print()

if not bugs:
    print("No bugs detected by automated scan. Manual visual review still needed.")
else:
    by_severity = {"FAIL": [], "WARN": [], "INFO": []}
    for page, sev, msg in bugs:
        by_severity[sev].append((page, msg))
    for sev in ("FAIL", "WARN", "INFO"):
        if not by_severity[sev]: continue
        print(f"  {sev}  ({len(by_severity[sev])})")
        print("  " + "-" * 65)
        for page, msg in by_severity[sev]:
            print(f"    [{page}]  {msg}")
        print()

print(f"  total: {len(bugs)} findings  ({sum(1 for _,s,_ in bugs if s=='FAIL')} FAIL, "
      f"{sum(1 for _,s,_ in bugs if s=='WARN')} WARN, "
      f"{sum(1 for _,s,_ in bugs if s=='INFO')} INFO)")
