"""Probe the three smoke failures from post_deploy_finish to determine whether
they are real regressions or false-positive smoke patterns."""
from __future__ import annotations
import urllib.request, sys, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def http_get(url, follow=True):
    if not follow:
        class NR(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers): return None
        op = urllib.request.build_opener(NR())
    else:
        op = urllib.request.build_opener()
    op.addheaders = [("User-Agent","probe/1.0")]
    try:
        r = op.open(url, timeout=45)
        return r.status, r.read().decode("utf-8","replace"), dict(r.headers), r.url
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8","replace") if hasattr(e,"read") else ""), dict(e.headers), url

# 1. Homepage check — what landing copy is actually there?
print("== /  (no follow) ==")
st, body, hdrs, url = http_get("https://meetgreeksingles.com/", follow=False)
print(f"  status={st}  Content-Type={hdrs.get('Content-Type','?')}  Location={hdrs.get('Location','(none)')}")
print(f"  size={len(body)}")
# Find the H1 / hero text
for label, pat in [
    ("title<>", r"<title>(.*?)</title>"),
    ("hero h1", r"<h1[^>]*>(.*?)</h1>"),
    ("hero h2", r"<h2[^>]*>(.*?)</h2>"),
    ("preparing", r"(preparing[^<\"]{0,80})"),
    ("connection", r"(connection[^<\"]{0,80})"),
    ("launch", r"(launch[^<\"]{0,80})"),
    ("find the", r"(find[^<\"]{0,40})"),
]:
    m = re.findall(pat, body, re.IGNORECASE | re.DOTALL)
    print(f"  {label}: {m[:5]}")

print()
print("== /login (follow) ==")
st, body, hdrs, url = http_get("https://meetgreeksingles.com/login", follow=True)
print(f"  status={st}  final_url={url}  size={len(body)}")
for label, pat in [
    ("title", r"<title>(.*?)</title>"),
    ("welcome", r"(Welcome[^<\"]{0,30})"),
    ("login text", r"(Log[ -]?in[^<\"]{0,30})"),
    ("h1", r"<h1[^>]*>(.*?)</h1>"),
    ("h2", r"<h2[^>]*>(.*?)</h2>"),
    ("email", r"<form[^>]*>(.{200,800})"),
]:
    m = re.findall(pat, body, re.IGNORECASE | re.DOTALL)
    print(f"  {label}: {[s[:120] for s in m[:3]]}")

print()
print("== /login (no follow) ==")
st, body, hdrs, url = http_get("https://meetgreeksingles.com/login", follow=False)
print(f"  status={st}  Location={hdrs.get('Location','(none)')}  size={len(body)}")

print()
print("== /email_not_confirmed.php (no follow) ==")
st, body, hdrs, url = http_get("https://meetgreeksingles.com/email_not_confirmed.php", follow=False)
print(f"  status={st}  Location={hdrs.get('Location','(none)')}  size={len(body)}")
for label, pat in [
    ("title", r"<title>(.*?)</title>"),
    ("h1", r"<h1[^>]*>(.*?)</h1>"),
    ("h2", r"<h2[^>]*>(.*?)</h2>"),
]:
    m = re.findall(pat, body, re.IGNORECASE | re.DOTALL)
    print(f"  {label}: {[s[:120] for s in m[:3]]}")

print()
print("== /join2.php — context for 'weight' / 'height' ==")
st, body, hdrs, url = http_get("https://meetgreeksingles.com/join2.php", follow=True)
print(f"  status={st}  size={len(body)}")
# Find what surrounds 'weight' and 'height'
for term in ['weight', 'height']:
    for m in re.finditer(re.escape(term), body, re.IGNORECASE):
        s = max(0, m.start() - 60); e = min(len(body), m.end() + 60)
        snippet = body[s:e].replace('\n', ' ')
        print(f"  [{term}] ...{snippet}...")
print()
# Also check: are there yes/no card-flip elements on /join2?
# Chameleon's encoded core renders question_title items as elements with class 'question_box' or similar
for cls_pat in ['question_box', 'question_title', 'card_flip', 'card-flip', 'yes_no', 'btn-yes', 'btn_yes', 'card_question']:
    n = len(re.findall(re.escape(cls_pat), body, re.IGNORECASE))
    print(f"  class/element '{cls_pat}' occurrences: {n}")

# Look for the "Kickstart your profile" copy that appears in step 3 — should be present after our changes
for label in ['Kickstart', 'About me', 'about_me', 'Interested in', 'interested_in', 'captcha']:
    n = len(re.findall(re.escape(label), body, re.IGNORECASE))
    print(f"  copy '{label}' occurrences: {n}")
