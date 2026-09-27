#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin" "$tmp/cache" "$tmp/state"

cat > "$tmp/bin/yt-dlp" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
selector=""
want_selector=0
for arg in "$@"; do
  if [ "$want_selector" -eq 1 ]; then selector="$arg"; want_selector=0; continue; fi
  [ "$arg" = "-f" ] && want_selector=1
done
printf 'selector=%s\nargs=%s\n' "$selector" "$*" >> "$YT_CALLS"
if [[ "$*" == *"--write-info-json"* ]]; then
  if [ "${FAKE_SUBTITLE_MODE:-ok}" = "429" ]; then
    echo 'ERROR: HTTP Error 429: Too Many Requests https://media.invalid/subs?signature=super-secret' >&2
    exit 1
  fi
  cat > video123456.info.json <<'JSON'
{"id":"video123456","title":"Test","channel":"Test channel","upload_date":"20260101","duration":10,"duration_string":"10s","description":"","chapters":[]}
JSON
  cat > video123456.en.srt <<'SRT'
1
00:00:00,000 --> 00:00:01,000
hello
SRT
else
  if [[ "$selector" == *"protocol^=m3u8"* ]]; then
    printf '10.0\nhttps://media.invalid/primary?signature=super-secret\n'
  else
    printf '10.0\nhttps://media.invalid/fresh?signature=super-secret\n'
  fi
fi
MOCK

cat > "$tmp/bin/ffmpeg" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
input=""
output=""
previous=""
for arg in "$@"; do
  if [ "$previous" = "input" ]; then input="$arg"; previous=""; continue; fi
  [ "$arg" = "-i" ] && previous=input
  output="$arg"
done
printf '%s\n' "$input" >> "$FFMPEG_CALLS"
if [[ "$input" == *primary* ]]; then
  echo 'https://media.invalid/primary?signature=super-secret: HTTP error 403 Forbidden' >&2
  exit 1
fi
printf 'jpeg' > "$output"
MOCK

cat > "$tmp/bin/sleep" <<'MOCK'
#!/usr/bin/env bash
printf '%s\n' "$1" >> "$SLEEP_CALLS"
MOCK

chmod +x "$tmp/bin/yt-dlp" "$tmp/bin/ffmpeg" "$tmp/bin/sleep"
export PATH="$tmp/bin:$PATH"
export YT_CALLS="$tmp/yt-calls"
export FFMPEG_CALLS="$tmp/ffmpeg-calls"
export SLEEP_CALLS="$tmp/sleep-calls"
export YT_VIDEO_STATE_DIR="$tmp/state"
export YT_RATE_LIMIT_COOLDOWN=60

if FAKE_SUBTITLE_MODE=429 "$skill_dir/scripts/yt-subtitles.sh" video123456 --out "$tmp/cache" >"$tmp/subtitles.out" 2>"$tmp/subtitles.err"; then
  echo "expected the simulated subtitle 429 to fail" >&2
  exit 1
fi
grep -q 'HTTP 429' "$tmp/subtitles.err"
! grep -q 'super-secret' "$tmp/subtitles.err"
[ -s "$YT_VIDEO_STATE_DIR/.rate-limit-until" ]
grep -q -- '--sleep-requests 1' "$YT_CALLS"
grep -q -- '--sleep-subtitles 1' "$YT_CALLS"
grep -q -- 'http:exp=1:16' "$YT_CALLS"

# The marker also delays later subtitle requests. Fake sleep records the wait
# so this test can prove the cooldown without waiting in real time.
: > "$YT_CALLS"
FAKE_SUBTITLE_MODE=ok YT_RATE_LIMIT_COOLDOWN=0 YT_DLP_IP_FAMILY=auto "$skill_dir/scripts/yt-subtitles.sh" video123456 --out "$tmp/cache" >"$tmp/subtitles.ok" 2>"$tmp/subtitles.ok.err"
grep -q 'hello' "$tmp/cache/video123456.md"
! grep -q -- '--force-ipv4' "$YT_CALLS"
[ "$(wc -l < "$SLEEP_CALLS" | tr -d ' ')" -eq 1 ]

# The same cooldown state applies to frame extraction.
now=$(date +%s)
printf '%s\n' "$((now + 60))" > "$YT_VIDEO_STATE_DIR/.rate-limit-until"
YT_RATE_LIMIT_COOLDOWN=0 "$skill_dir/scripts/yt-frames.sh" video123456 1 --out "$tmp/frames" >"$tmp/frames.out" 2>"$tmp/frames.err"
[ -s "$tmp/frames/video123456-1000ms-w960.jpg" ]
[ "$(wc -l < "$FFMPEG_CALLS" | tr -d ' ')" -eq 2 ]
[ "$(wc -l < "$SLEEP_CALLS" | tr -d ' ')" -eq 2 ]
grep -q 'one fresh URL' "$tmp/frames.err" || grep -q 'alternate format' "$tmp/frames.err"
! grep -q 'super-secret' "$tmp/frames.err"
grep -q 'selector=b\[protocol\^=m3u8\]' "$YT_CALLS"
grep -q 'selector=bv\*\[height<=720\]' "$YT_CALLS"

printf 'yt-video retry tests passed\n'
