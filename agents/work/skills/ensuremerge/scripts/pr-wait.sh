#!/usr/bin/env bash
# Block until a PR reaches an actionable state, so no model turns are spent polling.
# Usage: pr-wait.sh <owner/repo> <pr-number> [interval_s=30] [timeout_s=7200]
#
# Always exits 0 with a final "RESULT=..." line (exit 1 = usage error, 7 = persistent gh failure):
#   RESULT=merged commit=<sha>
#   RESULT=closed-without-merge
#   RESULT=checks-failed names=<...>
#   RESULT=automerge-dropped
#   RESULT=queue-dropped (was in the merge queue, left it without merging)
#   RESULT=conflicts (merge_state DIRTY)
#   RESULT=timeout
# Intermediate lines are printed only on state transitions.
set -uo pipefail

repo="${1:?usage: pr-wait.sh <owner/repo> <pr-number> [interval_s] [timeout_s]}"
number="${2:?usage: pr-wait.sh <owner/repo> <pr-number> [interval_s] [timeout_s]}"
interval="${3:-30}"
timeout="${4:-7200}"

gh_clean() { env -u GITHUB_TOKEN -u GH_TOKEN gh "$@"; }

# A queued PR has no autoMergeRequest (the queue owns the merge), so queue membership is tracked separately.
queued() {
  gh_clean api graphql \
    -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){isInMergeQueue}}}' \
    -f o="${repo%/*}" -f r="${repo#*/}" -F n="$number" \
    --jq 'if .data.repository.pullRequest.isInMergeQueue then "ON" else "OFF" end' 2>/dev/null || echo "OFF"
}

fetch() {
  gh_clean pr view "$number" -R "$repo" \
    --json state,mergeStateStatus,autoMergeRequest,mergeCommit,statusCheckRollup \
    --jq '
      def cs: [.statusCheckRollup[]? |
        if .__typename == "CheckRun"
        then {n: .name, s: (if .status != "COMPLETED" then "PENDING" else (.conclusion // "PENDING") end)}
        else {n: .context, s: .state} end];
      def isbad: .s as $s | (["FAILURE","ERROR","TIMED_OUT","ACTION_REQUIRED","CANCELLED"] | index($s)) != null;
      cs as $c |
      [.state,
       .mergeStateStatus,
       (if .autoMergeRequest then "ON" else "OFF" end),
       ([$c[] | select(isbad)] | length | tostring),
       ([$c[] | select(isbad) | .n] | join(",")),
       ([$c[] | select(.s == "PENDING" or .s == "EXPECTED" or .s == "QUEUED" or .s == "IN_PROGRESS" or .s == "STALE")] | length | tostring),
       (.mergeCommit.oid // "-")
      ] | join("|")'
}

start=$SECONDS
errors=0
am_seen=0
q_seen=0
last=""
while :; do
  if ! line=$(fetch 2>&1); then
    errors=$((errors + 1))
    if [ "$errors" -ge 5 ]; then
      echo "RESULT=gh-error detail=$line"
      exit 7
    fi
    sleep "$interval"
    continue
  fi
  errors=0
  IFS='|' read -r state mstate am nfail failnames npending mcommit <<<"$line"

  if [ "$state" = "MERGED" ]; then
    echo "RESULT=merged commit=$mcommit"
    exit 0
  fi
  if [ "$state" = "CLOSED" ]; then
    echo "RESULT=closed-without-merge"
    exit 0
  fi
  if [ "${nfail:-0}" -gt 0 ]; then
    echo "RESULT=checks-failed names=$failnames pending=$npending"
    exit 0
  fi
  if [ "$mstate" = "DIRTY" ]; then
    echo "RESULT=conflicts merge_state=DIRTY"
    exit 0
  fi
  q=$(queued)
  if [ "$q" = "ON" ]; then
    q_seen=1
  elif [ "$q_seen" = 1 ]; then
    echo "RESULT=queue-dropped merge_state=$mstate pending=$npending"
    exit 0
  fi
  if [ "$am" = "ON" ]; then
    am_seen=1
  elif [ "$am_seen" = 1 ] && [ "$q" = "OFF" ]; then
    echo "RESULT=automerge-dropped merge_state=$mstate pending=$npending"
    exit 0
  fi
  if [ $((SECONDS - start)) -ge "$timeout" ]; then
    echo "RESULT=timeout state=$state merge_state=$mstate auto_merge=$am queued=$q pending=$npending"
    exit 0
  fi

  if [ "$line" != "$last" ]; then
    echo "$(date +%H:%M:%S) state=$state merge_state=$mstate auto_merge=$am queued=$q pending=$npending"
    last="$line"
  fi
  sleep "$interval"
done
