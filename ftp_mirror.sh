#!/usr/bin/env bash
# Selective FTPS mirror using curl (Pure-FTPd-friendly).
# Requires MGS_PASS env var.
set -u

HOST="meetgreeksingles.com"
USER="everett@meetgreeksingles.com"
: "${MGS_PASS:?MGS_PASS must be set}"
AUTH="${USER}:${MGS_PASS}"

DEST="/d/Freelancer-Project/Everetts/Irene/site/upstream"
mkdir -p "$DEST"

# Global counters
FILES_DONE=0
BYTES_DONE=0
DIRS_SKIPPED=0
T0=$(date +%s)

# Directories to skip anywhere in the tree
SKIP_DIRS="gallery photo video music music_musician_images music_song_images wall events_event_images groups_group_images outside_images audio_greeting im_audio_message postcard gifts banner bio profile_bg_cover profile_bg_cover_group places_images adv_images editor 3dchat yahoo temp city cache blogs tmp logs"

is_skip_dir() {
    local n="$1"
    for s in $SKIP_DIRS; do [[ "$n" == "$s" ]] && return 0; done
    return 1
}

log() {
    printf "[%4ds] %s\n" $(( $(date +%s) - T0 )) "$*"
}

fetch_file() {
    local remote="$1" local_path="$2" size="$3"
    if [[ -f "$local_path" && $(stat -c%s "$local_path" 2>/dev/null) == "$size" ]]; then
        return 0
    fi
    mkdir -p "$(dirname "$local_path")"
    if curl -s --connect-timeout 20 --max-time 120 --ftp-ssl -k \
            --user "$AUTH" -o "$local_path" \
            "ftp://${HOST}${remote}"; then
        FILES_DONE=$((FILES_DONE + 1))
        BYTES_DONE=$((BYTES_DONE + size))
        if (( FILES_DONE % 25 == 0 )); then
            log "$FILES_DONE files, $((BYTES_DONE/1024)) KB"
        fi
    else
        log "  ERROR $remote"
        rm -f "$local_path"
    fi
}

fetch_dir() {
    local remote="$1" local_dir="$2"
    mkdir -p "$local_dir"
    local listing
    listing=$(curl -s --connect-timeout 20 --max-time 60 --ftp-ssl -k \
              --user "$AUTH" "ftp://${HOST}${remote}/") || {
        log "  LIST FAILED $remote"
        return 1
    }
    # Parse BSD-style ls output: perms links user group size mon day hh:mm name
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local perms size name
        perms=$(awk '{print $1}' <<< "$line")
        size=$(awk '{print $5}' <<< "$line")
        # name = everything after field 8, preserves spaces
        name=$(awk '{for(i=9;i<=NF;i++) printf "%s%s", $i, (i<NF?" ":"")}' <<< "$line")
        [[ "$name" == "." || "$name" == ".." || -z "$name" ]] && continue
        if [[ "$perms" == d* ]]; then
            if is_skip_dir "$name"; then
                DIRS_SKIPPED=$((DIRS_SKIPPED + 1))
                continue
            fi
            fetch_dir "${remote}/${name}" "${local_dir}/${name}"
        else
            fetch_file "${remote}/${name}" "${local_dir}/${name}" "$size"
        fi
    done <<< "$listing"
}

log "starting mirror of ${HOST}"

# 1. root files + specific top-level dirs we want
#    We want: .well-known, _cron, _frameworks, _include, _lang, _pay, _server,
#             administration, ioncube, m, partner
#    Skip at root: _files (handled separately), tmp
log "fetching root listing"
root_listing=$(curl -s --connect-timeout 20 --max-time 60 --ftp-ssl -k \
               --user "$AUTH" "ftp://${HOST}/")
log "root listing: $(wc -l <<< "$root_listing") lines"

# Root-level files first (small, fast)
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    perms=$(awk '{print $1}' <<< "$line")
    size=$(awk '{print $5}' <<< "$line")
    name=$(awk '{for(i=9;i<=NF;i++) printf "%s%s", $i, (i<NF?" ":"")}' <<< "$line")
    [[ "$name" == "." || "$name" == ".." || -z "$name" ]] && continue
    if [[ "$perms" != d* ]]; then
        fetch_file "/${name}" "${DEST}/${name}" "$size"
    fi
done <<< "$root_listing"
log "root files done: $FILES_DONE files, $((BYTES_DONE/1024)) KB"

# Top-level dirs
for d in .well-known _cron _frameworks _include _lang _pay _server administration ioncube m partner; do
    # Check if it exists at root
    if grep -qE "^d.* ${d}\$" <<< "$root_listing"; then
        log "mirroring /${d}"
        fetch_dir "/${d}" "${DEST}/${d}"
        log "  /${d} done (running: $FILES_DONE files, $((BYTES_DONE/1024)) KB)"
    fi
done

# _files/logo and _files/tmpl only
log "mirroring /_files/logo and /_files/tmpl"
for sub in logo tmpl; do
    fetch_dir "/_files/${sub}" "${DEST}/_files/${sub}"
done

log "DONE. $FILES_DONE files, $((BYTES_DONE/1024)) KB, $DIRS_SKIPPED dirs skipped"
