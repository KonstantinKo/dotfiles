#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: upload-r2.sh [--temporary|--durable] <path-to-file>" >&2
  exit 2
}

retention="temporary"
if [ "${1:-}" = "--temporary" ] || [ "${1:-}" = "--durable" ]; then
  retention="${1#--}"
  shift
fi
[ "$#" -eq 1 ] || usage
file="$1"
[ -f "$file" ] || { echo "file not found: $file" >&2; exit 2; }
file="$(realpath "$file")"

command -v wrangler >/dev/null 2>&1 || {
  echo "missing dependency: wrangler CLI" >&2
  exit 2
}

bucket="${R2_BUCKET:-agent-file-uploads}"
public_base_url="${FILE_PUBLIC_BASE_URL:-https://pub-aff1b2f7b68c42fbbbecedb6984cefb0.r2.dev}"

basename="${file##*/}"
if [[ "$basename" == *.* && "$basename" != .* ]]; then
  stem="${basename%.*}"
  extension=".${basename##*.}"
else
  stem="$basename"
  extension=""
fi

slug="$(printf '%s' "$stem" \
  | iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' || true)"
[ -n "$slug" ] || slug="file"
extension="$(printf '%s' "$extension" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^.a-z0-9]//g')"
suffix="$(date -u +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
prefix="${FILE_UPLOAD_PREFIX:-$retention}"
prefix="${prefix#/}"
prefix="${prefix%/}"
key="${prefix:+$prefix/}${slug}-${suffix}${extension}"
content_type="$(file --brief --mime-type "$file")"
wrangler --cwd "${TMPDIR:-/tmp}" r2 object put "${bucket}/${key}" \
  --file "$file" \
  --content-type "$content_type" \
  --storage-class Standard \
  --remote \
  --force >&2

printf '%s/%s\n' "${public_base_url%/}" "$key"
