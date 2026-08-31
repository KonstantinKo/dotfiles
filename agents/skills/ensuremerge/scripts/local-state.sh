#!/usr/bin/env bash
# Compact local git facts for /ensuremerge verify/cleanup. Read-only; run `git fetch` first.
# Usage (from inside the repo): local-state.sh <head-branch> [default-branch]
set -uo pipefail

head_branch="${1:?usage: local-state.sh <head-branch> [default-branch]}"
default_branch="${2:-}"
if [ -z "$default_branch" ]; then
  default_branch=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
  [ -z "$default_branch" ] && default_branch=main
fi
echo "default_branch=$default_branch"

# Worktrees: path, branch, dirty count (incl. untracked), role tags
git worktree list --porcelain | awk '/^worktree /{print $2}' | while IFS= read -r wt; do
  br=$(git -C "$wt" symbolic-ref --short HEAD 2>/dev/null || echo "DETACHED")
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  role=""
  [ "$br" = "$head_branch" ] && role=" <-- PR-HEAD"
  [ "$br" = "$default_branch" ] && role=" <-- DEFAULT"
  echo "worktree: $wt branch=$br dirty=$dirty$role"
done

# Head branch facts
if git show-ref --verify --quiet "refs/heads/$head_branch"; then
  echo "head_local=yes"
  if git show-ref --verify --quiet "refs/remotes/origin/$head_branch"; then
    unpushed=$(git rev-list --count "origin/$head_branch..$head_branch" 2>/dev/null || echo "?")
    echo "head_unpushed_vs_origin_head=$unpushed"
  else
    not_on_default=$(git rev-list --count "origin/$default_branch..$head_branch" 2>/dev/null || echo "?")
    echo "head_unpushed_vs_origin_head=no-remote-tracking commits_not_on_origin_default=$not_on_default"
  fi
else
  echo "head_local=no"
fi
# ls-remote exit 2 = ref genuinely absent; anything else = lookup failed (network/auth)
GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
  git ls-remote --exit-code --heads origin "$head_branch" >/dev/null 2>&1
case $? in
  0) echo "remote_head_branch=exists" ;;
  2) echo "remote_head_branch=absent" ;;
  *) echo "remote_head_branch=unknown (ls-remote failed; verify before deleting)" ;;
esac

# Default branch position vs origin
if git show-ref --verify --quiet "refs/heads/$default_branch"; then
  behind=$(git rev-list --count "$default_branch..origin/$default_branch" 2>/dev/null || echo "?")
  ahead=$(git rev-list --count "origin/$default_branch..$default_branch" 2>/dev/null || echo "?")
  echo "default_local=yes behind_origin=$behind ahead_origin=$ahead"
else
  echo "default_local=no"
fi
