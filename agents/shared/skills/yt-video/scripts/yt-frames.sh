#!/usr/bin/env bash
# Extract selected YouTube video frames without opening a browser or playing audio.
# Usage: yt-frames.sh <url-or-id> <seconds|MM:SS|HH:MM:SS> [more timestamps...]
# Options: --out DIR --width PIXELS --force --cookies-from-browser NAME --cookies FILE --no-cookies

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=yt-common.sh
. "$SCRIPT_DIR/yt-common.sh"

usage() { sed -n '2,4p' "$0" >&2; exit 1; }
command -v yt-dlp >/dev/null || { echo "yt-dlp not installed (brew install yt-dlp)" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg not installed (brew install ffmpeg)" >&2; exit 1; }

URL="${1:-}"; [ -n "$URL" ] || usage; shift
OUT_DIR="${YT_FRAMES_DIR:-${TMPDIR:-/tmp}/yt-subtitles/frames}"
WIDTH=960
FORCE=0
COOKIE_ARGS=()
times=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out) [ $# -ge 2 ] || usage; OUT_DIR="$2"; shift 2 ;;
    --width) [ $# -ge 2 ] || usage; WIDTH="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --cookies-from-browser) [ $# -ge 2 ] || usage; COOKIE_ARGS=(--cookies-from-browser "$2"); shift 2 ;;
    --cookies) [ $# -ge 2 ] && [ -f "$2" ] || usage; COOKIE_ARGS=(--cookies "$2"); shift 2 ;;
    --no-cookies) COOKIE_ARGS=(); shift ;;
    --*) echo "unknown option: $1" >&2; usage ;;
    *) times+=("$1"); shift ;;
  esac
done
[ ${#times[@]} -gt 0 ] || usage
[[ "$WIDTH" =~ ^[0-9]+$ ]] && [ "$WIDTH" -ge 320 ] && [ "$WIDTH" -le 3840 ] || { echo "width must be 320-3840 pixels" >&2; exit 1; }

# Accept the same common YouTube URL forms as yt-subtitles.sh. A video id is
# required for stable, per-video cache names.
id=""
if [[ "$URL" =~ ^[A-Za-z0-9_-]{11}$ ]]; then id="$URL"
elif [[ "$URL" =~ [\?\&]v=([A-Za-z0-9_-]{11}) ]]; then id="${BASH_REMATCH[1]}"
elif [[ "$URL" =~ (youtu\.be/|/shorts/|/live/|/embed/)([A-Za-z0-9_-]{11}) ]]; then id="${BASH_REMATCH[2]}"
fi
[ -n "$id" ] || { echo "expected a YouTube video URL or 11-character video id" >&2; exit 1; }
URL="https://www.youtube.com/watch?v=$id"

# Canonicalize timestamps to milliseconds for cache keys. Reject negative,
# malformed, and out-of-range minute/second fields before any network call.
millis=()
for at in "${times[@]}"; do
  ms=$(awk -v at="$at" 'BEGIN {
    n=split(at, a, ":"); if (n<1 || n>3) exit 1
    for (i=1;i<=n;i++) if (a[i] !~ /^[0-9]+([.][0-9]+)?$/) exit 1
    for (i=1;i<n;i++) if (a[i] !~ /^[0-9]+$/) exit 1
    if (n==3 && a[2]>=60) exit 1
    if (n>1 && a[n]>=60) exit 1
    s=0; for (i=1;i<=n;i++) s=s*60+a[i]
    if (s>864000) exit 1
    printf "%.0f", s*1000
  }') || { echo "invalid timestamp: $at" >&2; exit 1; }
  millis+=("$ms")
done

mkdir -p "$OUT_DIR"
duration_path="$OUT_DIR/$id.duration-ms"
validate_duration() {
  local duration_ms="$1" i
  for i in "${!millis[@]}"; do
    if [ "${millis[$i]}" -ge "$duration_ms" ]; then
      echo "timestamp ${times[$i]} is at or past the video duration ($(awk -v ms="$duration_ms" 'BEGIN { printf "%.3f", ms/1000 }')s)" >&2
      exit 1
    fi
  done
}
# Cached images are trustworthy only when the requested times fit the video's
# known duration. This sidecar keeps a complete cache hit offline.
if [ "$FORCE" -eq 0 ] && [ -s "$duration_path" ]; then
  cached_duration=$(cat "$duration_path")
  if [[ "$cached_duration" =~ ^[0-9]+$ ]] && [ "$cached_duration" -gt 0 ]; then
    validate_duration "$cached_duration"
  fi
fi
paths=()
missing=0
for ms in "${millis[@]}"; do
  path="$OUT_DIR/$id-${ms}ms-w${WIDTH}.jpg"
  paths+=("$path")
  if [ "$FORCE" -eq 1 ] || [ ! -s "$path" ]; then missing=1; fi
done
if [ "$missing" -eq 0 ] && [ -n "${cached_duration:-}" ] && [[ "$cached_duration" =~ ^[0-9]+$ ]] && [ "$cached_duration" -gt 0 ]; then
  printf '%s\n' "${paths[@]}"; exit 0
fi

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
err="$tmp/yt-dlp.err"
stream_url=""
resolve_stream() {
  local selector="$1"; shift
  local extra=("$@")
  # HLS seeking works with YouTube videos whose direct DASH URL rejects remote
  # range requests. The 720p cap keeps frame decoding reasonably cheap.
  yt_wait_rate_limit
  stream_info=$(yt-dlp "${extra[@]}" "${yt_user_args[@]}" "${yt_network_args[@]}" \
    --no-playlist --no-warnings -f "$selector" \
    --print '%(duration)s' --get-url "$URL" 2>"$err")
  [[ "$stream_info" == *$'\n'* ]] || return 1
  duration="${stream_info%%$'\n'*}"
  stream_url="${stream_info#*$'\n'}"
  [[ "$duration" =~ ^[0-9]+([.][0-9]+)?$ ]] || return 1
  [ -n "$stream_url" ] && [[ "$stream_url" != *$'\n'* ]]
}
fail_stream() {
  yt_mark_rate_limit "$err"
  yt_report_error "yt-dlp could not resolve a video stream with known duration" "$err" "$id"
  exit 1
}
PRIMARY_FORMAT='b[protocol^=m3u8][height<=720]/bv*[height<=720]/b[height<=720]'
FALLBACK_FORMAT='bv*[height<=720]/b[height<=720]'
if ! resolve_stream "$PRIMARY_FORMAT" "${COOKIE_ARGS[@]}"; then
  if ! yt_is_rate_limited "$err" && grep -Eiq 'HTTP (Error )?403|Forbidden' "$err"; then
    printf 'YouTube rejected the first stream lookup; trying one alternate format.\n' >&2
    resolve_stream "$FALLBACK_FORMAT" "${COOKIE_ARGS[@]}" || fail_stream
  else
    fail_stream
  fi
fi
duration_ms=$(awk -v s="$duration" 'BEGIN { printf "%.0f", s*1000 }')
[ "$duration_ms" -gt 0 ] || { echo "video duration is unavailable; cannot safely seek" >&2; exit 1; }
printf '%s\n' "$duration_ms" > "$tmp/duration-ms"
mv "$tmp/duration-ms" "$duration_path"
validate_duration "$duration_ms"
if [ "$missing" -eq 0 ]; then printf '%s\n' "${paths[@]}"; exit 0; fi

fallback_used=0
for i in "${!millis[@]}"; do
  path="${paths[$i]}"; ms="${millis[$i]}"
  if [ "$FORCE" -eq 0 ] && [ -s "$path" ]; then continue; fi
  # Input seeking requests nearby bytes from the remote media URL. No browser
  # or audio output is opened; -an also excludes audio from the output.
  seconds=$(awk -v ms="$ms" 'BEGIN { printf "%.3f", ms/1000 }')
  partial="$tmp/frame-$i.jpg"
  if ffmpeg -nostdin -hide_banner -loglevel error -ss "$seconds" -i "$stream_url" \
      -map 0:v:0 -an -sn -dn -frames:v 1 \
      -vf "scale=min(${WIDTH}\\,iw):-2" \
      -q:v 3 -y "$partial" 2>"$tmp/ffmpeg.err"; then
    :
  else
    if yt_is_rate_limited "$tmp/ffmpeg.err"; then
      yt_mark_rate_limit "$tmp/ffmpeg.err"
      yt_report_error "ffmpeg could not read the video stream at ${times[$i]}" "$tmp/ffmpeg.err" "$id"
      exit 1
    fi
    if [ "$fallback_used" -eq 0 ] && grep -Eiq 'HTTP (Error )?403|Forbidden|Invalid data|server returned' "$tmp/ffmpeg.err"; then
      fallback_used=1
      printf 'The first stream was rejected at %s; resolving one fresh URL with an alternate format.\n' "${times[$i]}" >&2
      resolve_stream "$FALLBACK_FORMAT" "${COOKIE_ARGS[@]}" || fail_stream
      if ! ffmpeg -nostdin -hide_banner -loglevel error -ss "$seconds" -i "$stream_url" \
          -map 0:v:0 -an -sn -dn -frames:v 1 \
          -vf "scale=min(${WIDTH}\\,iw):-2" \
          -q:v 3 -y "$partial" 2>"$tmp/ffmpeg.err"; then
        yt_mark_rate_limit "$tmp/ffmpeg.err"
        yt_report_error "failed to extract video frame at ${times[$i]} after one fresh stream attempt" "$tmp/ffmpeg.err" "$id"
        exit 1
      fi
    else
      yt_report_error "failed to extract video frame at ${times[$i]}" "$tmp/ffmpeg.err" "$id"
      exit 1
    fi
  fi
  [ -s "$partial" ] || { echo "no video frame at ${times[$i]} (past the end?)" >&2; exit 1; }
  mv "$partial" "$path"
done
printf '%s\n' "${paths[@]}"
