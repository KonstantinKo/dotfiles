#!/usr/bin/env bash
# Compact PR status for /ensuremerge — one gh call + two GraphQL calls, ~17 output lines.
# Usage: pr-status.sh [target]
#   target: PR URL | owner/repo#number | PR number | branch name | empty (PR of current branch)
set -euo pipefail

gh_clean() { env -u GITHUB_TOKEN -u GH_TOKEN gh "$@"; }

target="${1:-}"
args=()
if [[ "$target" =~ ^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  args=("${BASH_REMATCH[3]}" -R "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}")
elif [[ "$target" =~ ^([^/#[:space:]]+)/([^/#[:space:]]+)#([0-9]+)$ ]]; then
  args=("${BASH_REMATCH[3]}" -R "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}")
elif [[ -n "$target" ]]; then
  args=("$target")
fi

json_fields='number,url,title,state,isDraft,author,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,mergeable,mergeStateStatus,reviewDecision,autoMergeRequest,mergedAt,mergeCommit,statusCheckRollup'

# Bash 3.2-safe empty-array expansion
out=$(gh_clean pr view ${args[@]+"${args[@]}"} --json "$json_fields" --jq '
  def cs: [.statusCheckRollup[]? |
    if .__typename == "CheckRun"
    then {n: .name, s: (if .status != "COMPLETED" then "PENDING" else (.conclusion // "PENDING") end)}
    else {n: .context, s: .state} end];
  def isbad: .s as $s | (["FAILURE","ERROR","TIMED_OUT","ACTION_REQUIRED","CANCELLED"] | index($s)) != null;
  def ispass: .s == "SUCCESS" or .s == "NEUTRAL" or .s == "SKIPPED";
  cs as $c |
  (.url | capture("github.com/(?<o>[^/]+)/(?<r>[^/]+)/")) as $repo |
  "repo=\($repo.o)/\($repo.r)",
  "pr=\(.number) state=\(.state)\(if .isDraft then " DRAFT" else "" end)",
  "title=\(.title)",
  "url=\(.url)",
  "author=\(.author.login)",
  "base=\(.baseRefName) head=\(.headRefName) head_sha=\(.headRefOid)",
  "head_repo=\(.headRepositoryOwner.login)/\(.headRepository.name) fork=\(if .headRepositoryOwner.login != $repo.o then "yes" else "no" end)",
  "mergeable=\(.mergeable) merge_state=\(.mergeStateStatus)",
  "review_decision=\(.reviewDecision // "NONE")",
  "auto_merge=\(if .autoMergeRequest then .autoMergeRequest.mergeMethod else "OFF" end)",
  "merged_at=\(.mergedAt // "-") merge_commit=\(.mergeCommit.oid // "-")",
  "checks: total=\($c | length) pass=\([$c[] | select(ispass)] | length) fail=\([$c[] | select(isbad)] | length) pending=\([$c[] | select((ispass or isbad) | not)] | length)",
  ($c[] | select(isbad) | "fail: \(.n) [\(.s)]"),
  ($c[] | select((ispass or isbad) | not) | "pending: \(.n)")
')
echo "$out"

repo=$(sed -n 's/^repo=//p' <<<"$out")
number=$(sed -n 's/^pr=\([0-9]*\) .*/\1/p' <<<"$out")
unresolved=$(gh_clean api graphql \
  -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved}}}}}' \
  -f o="${repo%/*}" -f r="${repo#*/}" -F n="$number" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)] | length' 2>/dev/null || echo "?")
echo "unresolved_threads=$unresolved"

# Merge queue on the base branch (its method is fixed server-side; `gh pr merge --auto` with no method flag enqueues)
base=$(sed -n 's/^base=\([^ ]*\) .*/\1/p' <<<"$out")
queue=$(gh_clean api graphql \
  -f query='query($o:String!,$r:String!,$n:Int!,$b:String!){repository(owner:$o,name:$r){mergeQueue(branch:$b){configuration{mergeMethod mergingStrategy}} pullRequest(number:$n){mergeQueueEntry{position state}}}}' \
  -f o="${repo%/*}" -f r="${repo#*/}" -F n="$number" -f b="$base" \
  --jq '.data.repository | (if .mergeQueue then "merge_queue=yes method=\(.mergeQueue.configuration.mergeMethod) strategy=\(.mergeQueue.configuration.mergingStrategy)" else "merge_queue=no" end), (if .pullRequest.mergeQueueEntry then "queue_entry=position=\(.pullRequest.mergeQueueEntry.position) state=\(.pullRequest.mergeQueueEntry.state)" else "queue_entry=-" end)' 2>/dev/null || printf 'merge_queue=?\nqueue_entry=?\n')
echo "$queue"
