#!/usr/bin/env bash
# Comprehensive E2E test for staging /staging/ — content-aware, not just status codes.
# Writes findings to /tmp/mgs/qa_findings.log

BASE="https://meetgreeksingles.com/staging"
COOKIES=/tmp/mgs/qa_cookies.txt
ADMIN_COOKIES=/tmp/mgs/qa_admin_cookies.txt
OUT=/tmp/mgs/qa_findings.log
rm -f "$COOKIES" "$ADMIN_COOKIES" "$OUT"

pass=0; warn=0; fail=0
note() { echo "$1" | tee -a "$OUT"; }
section() { note ""; note "==============================================================="; note "$1"; note "==============================================================="; }

fetch() {
    # fetch <url> [<cookie_jar_optional>] — writes body to /tmp/mgs/qa_body.html
    local url="$1" jar="${2:-}"
    local opts="-sS --connect-timeout 10 --max-time 20"
    if [ -n "$jar" ]; then opts="$opts -b $jar -c $jar"; fi
    curl $opts "$url" -o /tmp/mgs/qa_body.html -w "status=%{http_code} size=%{size_download} final=%{url_effective}"
}

check_body() {
    # check_body <label> <expected_grep_pattern>
    local label="$1" pattern="$2"
    if grep -qE "$pattern" /tmp/mgs/qa_body.html; then
        note "   ✓ $label"
        pass=$((pass+1))
    else
        note "   ✗ $label  (pattern not found: $pattern)"
        fail=$((fail+1))
    fi
}

check_no_error() {
    local label="$1"
    local errs=$(grep -cE "Fatal error|Parse error|Uncaught|Call to undefined|Access denied" /tmp/mgs/qa_body.html)
    local warns=$(grep -cE "Warning:|Notice:|Deprecated:" /tmp/mgs/qa_body.html)
    if [ "$errs" -gt 0 ]; then
        note "   ✗ PHP ERRORS on $label ($errs)"
        fail=$((fail+1))
        grep -E "Fatal error|Parse error|Uncaught|Call to undefined|Access denied" /tmp/mgs/qa_body.html | head -3 | sed 's/^/     /' | tee -a "$OUT"
    elif [ "$warns" -gt 0 ]; then
        note "   ⚠ PHP warnings on $label ($warns)"
        warn=$((warn+1))
    fi
}

expect_redirect_to() {
    local url="$1" expected_location="$2"
    local out=$(curl -sSI --connect-timeout 10 --max-time 15 "$url")
    local status=$(echo "$out" | head -1 | tr -d '\r')
    local location=$(echo "$out" | grep -i '^Location:' | tr -d '\r' | sed 's/^Location: *//')
    if echo "$status" | grep -q "302"; then
        if [ "$location" = "$expected_location" ]; then
            note "   ✓ $url → $location"
            pass=$((pass+1))
        else
            note "   ⚠ $url → $location  (expected $expected_location)"
            warn=$((warn+1))
        fi
    else
        note "   ✗ $url  NOT blocked  ($status)"
        fail=$((fail+1))
    fi
}

# ===========================================================
# 1. GUEST HOMEPAGE
# ===========================================================
section "1. GUEST HOMEPAGE"
fetch "$BASE/" "$COOKIES" | tee -a "$OUT" | grep -v "^$"
check_body "Homepage 200 + has title" "<title>Meet Greek Singles"
check_body "Pre-launch banner visible" "We are preparing for our official launch"
check_body "Registration is open now copy" "Registration is open now"
check_body "Slogan intact" "Find the Greek Connection"
check_body "Join button present" "Join us now"
check_no_error "homepage"

# ===========================================================
# 2. ALLOWED PAGES (guest access)
# ===========================================================
section "2. ALLOWED PAGES"
for p in "about.php" "contact.php" "info.php" "help.php" "join.php" "join2.php" "join3.php" "forget_password.php" "confirm_email.php" "email_not_confirmed.php"; do
    fetch "$BASE/$p" "$COOKIES" | sed "s|^|$p  |" | tee -a "$OUT"
    check_no_error "$p"
done

# ===========================================================
# 3. BLOCKED PAGES — must redirect to /staging/?__plfb=1
# ===========================================================
section "3. BLOCKED PAGES — redirect to /staging/?__plfb=1"
for p in "search_results" "search.php" "search_advanced.php" "mail.php" "messages.php" "mail_compose.php" "upgrade.php" "events.php" "blogs.php" "community.php" "notify.php" "videochat.php" "audiochat.php" "gallery_index.php" "groups.php" "forum.php" "places.php"; do
    expect_redirect_to "$BASE/$p" "https://meetgreeksingles.com/staging/?__plfb=1"
done

# ===========================================================
# 4. VANITY URL (bare username path)
# ===========================================================
section "4. VANITY URLS"
expect_redirect_to "$BASE/nick_the_greek"   "https://meetgreeksingles.com/staging/?__plfb=1"
expect_redirect_to "$BASE/some_random_user" "https://meetgreeksingles.com/staging/?__plfb=1"

# Then follow one and verify landing page serves cleanly
fetch "$BASE/?__plfb=1" "$COOKIES"
check_body "Landing after gate redirect shows banner" "We are preparing for our official launch"
check_no_error "landing after gate"

# ===========================================================
# 5. STATIC ASSETS
# ===========================================================
section "5. STATIC ASSETS"
for a in "robots.txt" "favicon.ico" "_server/xajax_js/xajax.js" "_frameworks/main/impact/main.css"; do
    st=$(curl -sSI --connect-timeout 10 --max-time 15 "$BASE/$a" | head -1 | tr -d '\r')
    if echo "$st" | grep -q "200"; then
        note "   ✓ $a  $st"
        pass=$((pass+1))
    else
        note "   ✗ $a  $st"
        fail=$((fail+1))
    fi
done

# css.php / js.php — generated assets
fetch "$BASE/css.php"
check_no_error "css.php"
fetch "$BASE/js.php"
check_no_error "js.php"

# ===========================================================
# 6. ADMIN BYPASS ?platform_mode_off=Y
# ===========================================================
section "6. ADMIN-PREVIEW BYPASS"
# First request sets the session flag
BYPASS_COOKIES=/tmp/mgs/qa_bypass_cookies.txt
rm -f "$BYPASS_COOKIES"
curl -sS -c "$BYPASS_COOKIES" "$BASE/?platform_mode_off=Y" -o /tmp/mgs/_landing.html
note "   Set bypass session flag on /staging/?platform_mode_off=Y"
# Now hit a blocked URL — should NOT redirect
st=$(curl -sSI -b "$BYPASS_COOKIES" --connect-timeout 10 --max-time 15 "$BASE/search_results" | head -1 | tr -d '\r')
note "   bypass: /search_results with flag → $st"
if echo "$st" | grep -q "200"; then
    note "   ✓ admin bypass works"
    pass=$((pass+1))
else
    note "   ✗ admin bypass did NOT let through ($st)"
    fail=$((fail+1))
fi

# And ?platform_mode_on=Y clears it
curl -sS -b "$BYPASS_COOKIES" -c "$BYPASS_COOKIES" "$BASE/?platform_mode_on=Y" -o /dev/null
st=$(curl -sSI -b "$BYPASS_COOKIES" --connect-timeout 10 --max-time 15 "$BASE/search_results" | head -1 | tr -d '\r')
note "   after ?platform_mode_on=Y, /search_results → $st"
if echo "$st" | grep -q "302"; then
    note "   ✓ ?platform_mode_on=Y correctly reverts"
    pass=$((pass+1))
else
    note "   ✗ clear-flag didn't revert ($st)"
    fail=$((fail+1))
fi

# ===========================================================
# 7. ADMIN LOGIN
# ===========================================================
section "7. ADMIN LOGIN"
# Get login page first
curl -sS -c "$ADMIN_COOKIES" "$BASE/administration/" -o /tmp/mgs/admin_login.html
note "   loaded admin login page"

# Attempt login (Chameleon admin usually POSTs user+password to index.php?cmd=login)
curl -sS -b "$ADMIN_COOKIES" -c "$ADMIN_COOKIES" \
    -d "login=admin" -d "password=AdminR@1!" -d "cmd=login" \
    "$BASE/administration/index.php" \
    -o /tmp/mgs/admin_postlogin.html \
    -w "login POST status=%{http_code}\n" | tee -a "$OUT"

# Follow-up: fetch a known admin page to check if we're in
curl -sS -b "$ADMIN_COOKIES" -c "$ADMIN_COOKIES" "$BASE/administration/site_options.php" \
    -o /tmp/mgs/admin_site_options.html \
    -w "site_options status=%{http_code} size=%{size_download}\n" | tee -a "$OUT"

# Check if we're logged in — look for logout link / admin UI markers
if grep -qiE "logout|sign.out|platform_mode" /tmp/mgs/admin_site_options.html; then
    note "   ✓ admin auth succeeded"
    pass=$((pass+1))
    if grep -q "platform_mode" /tmp/mgs/admin_site_options.html; then
        note "   ✓ platform_mode dropdown visible in Site Options"
        pass=$((pass+1))
    else
        note "   ✗ platform_mode NOT found on Site Options page"
        fail=$((fail+1))
    fi
else
    note "   ⚠ admin auth may have failed — no 'logout' marker found"
    warn=$((warn+1))
fi
check_no_error "admin site_options"

# ===========================================================
# 8. SUMMARY
# ===========================================================
section "SUMMARY"
note "PASS:  $pass"
note "WARN:  $warn"
note "FAIL:  $fail"
