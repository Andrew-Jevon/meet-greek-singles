import re
import urllib.request

url = "https://meetgreeksingles.com/?set_language=greek"
req = urllib.request.Request(url, headers={"User-Agent": "MGS-test"})
with urllib.request.urlopen(req, timeout=25) as r:
    body = r.read().decode("utf-8", "replace")
print("len", len(body))
print("mgs_i18n.js", "mgs_i18n.js" in body)
print("data-mgs-i18n count", body.count("data-mgs-i18n"))
print("nav_home", "data-mgs-i18n=\"nav_home\"" in body)
m = re.search(r"MGS_LANG = '([^']+)'", body)
print("MGS_LANG", m.group(1) if m else "missing")
