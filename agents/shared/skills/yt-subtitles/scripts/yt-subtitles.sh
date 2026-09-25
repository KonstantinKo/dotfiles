#!/usr/bin/env bash
# yt-subtitles.sh — fetch a YouTube video's subtitles + metadata as one markdown file.
#
# Usage:
#   yt-subtitles.sh <url-or-id>                 # write to cache dir, print the file path
#   yt-subtitles.sh <url-or-id> --stdout        # print the markdown instead of a path
#   yt-subtitles.sh <url-or-id> --out DIR       # write into DIR instead of the cache
#   yt-subtitles.sh <url-or-id> --lang de       # preferred subtitle language(s), comma-separated
#   yt-subtitles.sh <url-or-id> --force         # refetch even if cached
#   yt-subtitles.sh <url-or-id> --cookies-from-browser firefox | --cookies FILE | --no-cookies
#
# Cache: $YT_SUBTITLES_DIR, default ${TMPDIR:-/tmp}/yt-subtitles/<video-id>.md
#
# YouTube sometimes blocks unauthenticated yt-dlp ("Sign in to confirm you're
# not a bot"). By default we try without cookies and fall back to browser
# cookies (chrome, or $YT_COOKIES_FROM_BROWSER) only on failure.
#
# Networking: --force-ipv4 is always passed (YouTube over IPv6 stalls on some
# networks); YT_DLP_ARGS adds extra yt-dlp flags, e.g. YT_DLP_ARGS="--proxy ...".
#
# Exit codes: 0 ok · 3 no subtitles for this video · 1 other error

set -euo pipefail

usage() { sed -n '2,20p' "$0" >&2; exit 1; }

URL="${1:-}"; [ -n "$URL" ] || usage
shift || true

command -v yt-dlp >/dev/null || { echo "yt-dlp not installed (brew install yt-dlp)" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not installed" >&2; exit 1; }

OUT_DIR="${YT_SUBTITLES_DIR:-${TMPDIR:-/tmp}/yt-subtitles}"
TO_STDOUT=0
FORCE=0
LANGS="en,en-US,en-GB,en-AU,en-CA,en-orig"
COOKIE_MODE="auto"   # auto | forced | none
COOKIE_ARGS=(--cookies-from-browser "${YT_COOKIES_FROM_BROWSER:-chrome}")

while [ $# -gt 0 ]; do
  case "$1" in
    --stdout) TO_STDOUT=1; shift ;;
    --force) FORCE=1; shift ;;
    --out) [ $# -ge 2 ] || usage; OUT_DIR="$2"; shift 2 ;;
    --lang) [ $# -ge 2 ] || usage; LANGS="$2"; shift 2 ;;
    --cookies-from-browser) [ $# -ge 2 ] || usage; COOKIE_MODE="forced"; COOKIE_ARGS=(--cookies-from-browser "$2"); shift 2 ;;
    --cookies) [ $# -ge 2 ] || usage; [ -f "$2" ] || { echo "cookies file not found: $2" >&2; exit 1; }
               COOKIE_MODE="forced"; COOKIE_ARGS=(--cookies "$2"); shift 2 ;;
    --no-cookies) COOKIE_MODE="none"; COOKIE_ARGS=(); shift ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

# Normalise to https://www.youtube.com/watch?v=<id> when the id is recognisable
# (bare id, watch?v=, youtu.be/, shorts/, live/, embed/). Playlist params are
# dropped so we always fetch one video. Other URL forms are passed through.
id=""
if [[ "$URL" =~ ^[A-Za-z0-9_-]{11}$ ]]; then id="$URL"
elif [[ "$URL" =~ [?\&]v=([A-Za-z0-9_-]{11}) ]]; then id="${BASH_REMATCH[1]}"
elif [[ "$URL" =~ (youtu\.be/|/shorts/|/live/|/embed/)([A-Za-z0-9_-]{11}) ]]; then id="${BASH_REMATCH[2]}"
fi
[ -n "$id" ] && URL="https://www.youtube.com/watch?v=$id"

mkdir -p "$OUT_DIR"

# Cache hit needs no network at all.
if [ -n "$id" ] && [ "$FORCE" -eq 0 ] && [ -s "$OUT_DIR/$id.md" ]; then
  if [ "$TO_STDOUT" -eq 1 ]; then cat "$OUT_DIR/$id.md"; else echo "$OUT_DIR/$id.md"; fi
  exit 0
fi
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
err="$tmp/yt-dlp.err"

fetch() {
  local extra=("$@")
  rm -rf "$tmp"/*
  ( cd "$tmp" && yt-dlp ${extra[@]+"${extra[@]}"} ${YT_DLP_ARGS:-} \
      --force-ipv4 --socket-timeout 30 --skip-download --write-subs --write-auto-subs --sub-langs "$LANGS" --convert-subs srt \
      --write-info-json --no-playlist --no-warnings -o "%(id)s" "$URL" >/dev/null 2>"$err" )
}

fail() { echo "yt-dlp failed for $URL" >&2; sed 's/^/  /' "$err" >&2; exit 1; }
needs_login() { grep -qiE "sign in|log in|not a bot|age.?restricted|private video|members.only" "$err"; }

case "$COOKIE_MODE" in
  forced) fetch "${COOKIE_ARGS[@]}" || fail ;;
  none)   fetch || fail ;;
  auto)
    if ! fetch; then
      needs_login || fail
      echo "yt-dlp without cookies failed; retrying with ${COOKIE_ARGS[*]}..." >&2
      fetch "${COOKIE_ARGS[@]}" || fail
    fi ;;
esac

info=$(ls "$tmp"/*.info.json 2>/dev/null | head -1)
[ -n "$info" ] || { echo "no info.json for $URL" >&2; exit 1; }
id=$(basename "$info" .info.json)
out="$OUT_DIR/$id.md"

srt=$(find "$tmp" -maxdepth 1 -name "$id.*.srt" | head -1)
[ -n "$srt" ] || srt=$(find "$tmp" -maxdepth 1 -name "$id.*.vtt" | head -1)
[ -n "$srt" ] && [ -f "$srt" ] || { echo "no subtitles for $URL (langs: $LANGS)" >&2; exit 3; }
sub_lang=$(basename "$srt" | sed -E "s/^$id\.//; s/\.(srt|vtt)$//")

title=$(jq -r '.title' "$info")
channel=$(jq -r '.channel // .uploader' "$info")
upload_date=$(jq -r '.upload_date // ""' "$info" | sed 's/\(....\)\(..\)\(..\)/\1-\2-\3/')
duration=$(jq -r '.duration_string // ((.duration|tostring) + "s")' "$info")
description=$(jq -r '.description // ""' "$info")

# YouTube SRTs use a rolling window: each cue repeats the tail of the previous
# one. Take the text lines of each cue, trim, drop blanks, dedupe consecutive.
transcript=$(tr -d '\r' < "$srt" | awk '
  BEGIN { RS = ""; FS = "\n"; prev = "" }
  {
    started = 0
    for (i = 1; i <= NF; i++) {
      if (!started) { if ($i ~ /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9][,.][0-9]+ --> /) started = 1; continue }
      line = $i; gsub(/^[ \t]+|[ \t]+$/, "", line)
      if (line == "" || line == prev) continue
      print line; prev = line
    }
  }')

{
  printf -- '---\n'
  printf 'title: %s\n' "$(printf '%s' "$title" | jq -Rs .)"
  printf 'channel: %s\n' "$(printf '%s' "$channel" | jq -Rs .)"
  printf 'url: %s\nvideo_id: %s\nupload_date: %s\nduration: %s\nsubtitle_lang: %s\nfetched: %s\n' \
    "$URL" "$id" "$upload_date" "$duration" "$sub_lang" "$(date +%Y-%m-%d)"
  printf -- '---\n\n# %s\n\n' "$title"
  printf '**Channel:** %s  \n**Uploaded:** %s  \n**Duration:** %s  \n**URL:** %s\n\n' "$channel" "$upload_date" "$duration" "$URL"
  if [ -n "$description" ] && [ "$description" != "null" ]; then printf '## Description\n\n%s\n\n' "$description"; fi
  if [ "$(jq -c '.chapters // []' "$info")" != "[]" ]; then
    printf '## Chapters\n\n'
    jq -r '.chapters[] | "\(.start_time|floor)\t\(.title)"' "$info" | while IFS=$'\t' read -r s t; do
      printf -- '- %02d:%02d:%02d  %s\n' $((s/3600)) $(((s%3600)/60)) $((s%60)) "$t"
    done
    printf '\n'
  fi
  printf '## Transcript\n\n%s\n' "$transcript"
} > "$out"

if [ "$TO_STDOUT" -eq 1 ]; then cat "$out"; else echo "$out"; fi
