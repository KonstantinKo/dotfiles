#!/bin/bash
# Custom Claude Code statusline.
# Shows: caveman rock (when active) · context-token usage · cwd git branch.
#
# Wired in ~/.claude/settings.json:
#   "statusLine": { "type": "command", "command": "bash /Users/konstantin/.claude/statusline.sh" }

input=$(cat)

# --- inputs from Claude Code statusline JSON ---
transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty')
cwd=$(printf '%s' "$input" | jq -r '.workspace.current_dir // .cwd // empty')

# --- caveman rock: only render for whitelisted active modes ---
ROCK=""
FLAG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.caveman-active"
if [ -f "$FLAG" ] && [ ! -L "$FLAG" ]; then
  MODE=$(head -c 64 "$FLAG" 2>/dev/null | tr -d '\n\r' | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-')
  case "$MODE" in
    off) ;;
    lite|full|ultra|wenyan-lite|wenyan|wenyan-full|wenyan-ultra|commit|review|compress|"") ROCK="🪨 " ;;
  esac
fi

# --- context-token usage: last usage line in transcript (near EOF, cheap) ---
TOKENS=""
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  usage=$(tac "$transcript" 2>/dev/null | grep -m1 '"usage"')
  if [ -n "$usage" ]; then
    ctx=$(printf '%s' "$usage" | jq -r '
      (.message.usage // .usage) as $u
      | (($u.input_tokens // 0)
        + ($u.cache_creation_input_tokens // 0)
        + ($u.cache_read_input_tokens // 0))' 2>/dev/null)
    if [ -n "$ctx" ] && [ "$ctx" -gt 0 ] 2>/dev/null; then
      # window: >200k can only happen on a 1M-context model → flip denominator
      win=200000; denom="200k"
      [ "$ctx" -gt 200000 ] && { win=1000000; denom="1M"; }
      k=$(awk "BEGIN{printf \"%.1f\", $ctx/1000}")
      # green <100k, yellow >=100k, red >80% of window
      color=2
      [ "$ctx" -ge 100000 ] && color=3
      [ "$ctx" -gt $((win * 8 / 10)) ] && color=1
      TOKENS=$(printf '\033[38;5;%sm%sk/%s\033[0m' "$color" "$k" "$denom")
    fi
  fi
fi

# --- git branch of cwd ---
BRANCH=""
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  b=$(git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null \
      || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
  [ -n "$b" ] && BRANCH=$(printf '\033[38;5;75m \033[0m%s' "$b")
fi

# --- assemble: rock first, then tokens · branch ---
out="$ROCK"
[ -n "$TOKENS" ] && out="$out$TOKENS"
[ -n "$TOKENS" ] && [ -n "$BRANCH" ] && out="$out \033[2m·\033[0m "
[ -z "$TOKENS" ] && [ -n "$BRANCH" ] && out="$out"
out="$out$BRANCH"

printf '%b' "$out"
