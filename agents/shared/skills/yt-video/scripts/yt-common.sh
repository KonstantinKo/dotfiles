#!/usr/bin/env bash
# Shared retry, cooldown, and diagnostic helpers for the YouTube scripts.

YT_VIDEO_STATE_DIR="${YT_VIDEO_STATE_DIR:-${TMPDIR:-/tmp}/yt-subtitles}"
YT_RATE_LIMIT_FILE="$YT_VIDEO_STATE_DIR/.rate-limit-until"

# Leave time between extractor requests and use yt-dlp's own bounded retries.
# This keeps a transient 429 from becoming a burst of immediate new requests.
yt_network_args=(
  --socket-timeout 30
  --retries 4
  --extractor-retries 3
  --retry-sleep 'http:exp=1:16'
  --retry-sleep 'extractor:exp=1:16'
  --sleep-requests 1
)
case "${YT_DLP_IP_FAMILY:-ipv4}" in
  ipv4) yt_network_args+=(--force-ipv4) ;;
  ipv6) yt_network_args+=(--force-ipv6) ;;
  auto) ;;
  *) printf 'YT_DLP_IP_FAMILY must be ipv4, ipv6, or auto.\n' >&2; exit 2 ;;
esac

yt_user_args=()
if [ -n "${YT_DLP_ARGS:-}" ]; then
  # YT_DLP_ARGS is a space-separated list of additional yt-dlp options.
  read -r -a yt_user_args <<< "$YT_DLP_ARGS"
fi

yt_is_rate_limited() {
  [ -f "$1" ] && grep -Eiq 'HTTP (Error )?429|Too Many Requests|status code:?[[:space:]]*429' "$1"
}

yt_mark_rate_limit() {
  local err_file="$1" cooldown now tmp_file
  yt_is_rate_limited "$err_file" || return 0
  cooldown="${YT_RATE_LIMIT_COOLDOWN:-120}"
  [[ "$cooldown" =~ ^[0-9]+$ ]] || cooldown=120
  [ "$cooldown" -gt 0 ] || return 0
  mkdir -p "$YT_VIDEO_STATE_DIR"
  now=$(date +%s)
  tmp_file="$YT_RATE_LIMIT_FILE.$$"
  printf '%s\n' "$((now + cooldown))" > "$tmp_file"
  mv -f "$tmp_file" "$YT_RATE_LIMIT_FILE"
}

yt_wait_rate_limit() {
  local until now remaining
  [ -s "$YT_RATE_LIMIT_FILE" ] || return 0
  read -r until < "$YT_RATE_LIMIT_FILE"
  [[ "$until" =~ ^[0-9]+$ ]] || { rm -f "$YT_RATE_LIMIT_FILE"; return 0; }
  now=$(date +%s)
  remaining=$((until - now))
  if [ "$remaining" -gt 0 ]; then
    printf 'YouTube recently rate-limited a request; waiting %ss before trying again.\n' "$remaining" >&2
    sleep "$remaining"
  fi
  rm -f "$YT_RATE_LIMIT_FILE"
}

yt_redact_file() {
  # Signed media URLs contain short-lived signatures and IP-bound query values.
  # Keep the host/path for diagnosis while removing the entire query string.
  sed -E 's#(https?://[^[:space:]?"<>]+)\?[^[:space:]"<>]*#\1?[query redacted]#g' "$1"
}

yt_report_error() {
  local context="$1" err_file="$2" video_id="${3:-unknown}" cooldown="${YT_RATE_LIMIT_COOLDOWN:-120}"
  [[ "$cooldown" =~ ^[0-9]+$ ]] || cooldown=120
  if yt_is_rate_limited "$err_file"; then
    if [ "$cooldown" -gt 0 ]; then
      printf 'YouTube rate-limited this request (HTTP 429) for video %s. Pacing and retries were applied; a %ss cooldown is saved for the next request.\n' "$video_id" "$cooldown" >&2
    else
      printf 'YouTube rate-limited this request (HTTP 429) for video %s. Pacing and retries were applied; cooldown is disabled.\n' "$video_id" >&2
    fi
  elif [ -f "$err_file" ] && grep -Eiq 'HTTP (Error )?403|Forbidden|403 Forbidden' "$err_file"; then
    printf '%s for video %s (HTTP 403). The stream may have expired or been rejected.\n' "$context" "$video_id" >&2
  else
    printf '%s for video %s.\n' "$context" "$video_id" >&2
  fi
  if [ -s "$err_file" ]; then yt_redact_file "$err_file" | sed 's/^/  /' >&2; fi
}
