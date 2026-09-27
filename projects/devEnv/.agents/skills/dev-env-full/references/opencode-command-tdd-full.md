---
description: Strict TDD devEnv workflow with behavior tree, red gate, human test review, then implementation
agent: build
---

# TDD-Full Orchestrator

Use for high-rigor feature work from `$ARGUMENTS`. Scan, flow, grill, behavior tree, write all tests first, human review red tests, then implement one test at a time. Do not commit.

## Phase 1: Interactive

### 1. Scan

Run `/scan` for likely scope. Include matching `.project/docs/feature/<feature>/README.md` and `.project/rules/*.md`.

### 2. Flow

Run `/flow` fit/risk sections. Stop for Conditional/Poor verdict unless user explicitly proceeds.

### 3. Grill

Run `/grill` with extra TDD coverage:
- Public interface for each behavior: route response, service fn, DB helper, CLI/script command
- External boundary: network, time, randomness, fs, Fly.io API, Cloudflare headers, DB when unit testing
- Observable signal: response, DB row, redirect URL, generated prefix, emitted command/file
- Edge cases: empty repo, preview empty repo reject, long title, partial commit, missing branch, concurrent preview creation, failed dependency

### 4. Plan

Present vertical slices, target public interfaces, test files, mocks, and verification commands. Ask approval.

Include feature docs that need updates. Do not create ADRs.

### 5. Behavior Tree

Co-author behavior checklist. This is test spec.

```markdown
## <Feature root>
- [ ] <Requirement/state>
  - [ ] <Concrete test case: input -> expected output>
  - [ ] <Concrete test case>
```

Rules:
- One `question` per branch
- Every leaf is one concrete test case
- Leaves test public interface only
- Triangulate behavior with positive/negative or boundary/interior examples when needed
- Keep each root small enough to review

Print finalized tree and ask `question`: Approve tree / Add branch / Edit leaf / Drop leaf. Do not proceed without approval.

### 6. Worktree Decision

Ask before creating/switching worktree. In-place is allowed.

## Phase 2: Autonomous With Human Test Gate

### 7. Baseline

Run baseline tests/checks if feasible:

```bash
just verify
```

If existing failures exist, ask `question`: stop / snapshot existing failures / fix if same scope.

### 8. Track Work

Create `todowrite` slices.

### 9. Per-Slice TDD Loop

#### 9a. Write All Tests

Write tests for every behavior leaf before implementation. Use public interfaces only. Mock external boundaries only. No `.skip`, `.todo`, commented assertions, or own-module mocks.

#### 9b. RED Gate

Run new tests with the narrowest feasible command.

Every new test must fail for the right reason: assertion failure or missing behavior. Not import errors, type errors, setup errors, or vacuous passes.

Loop until red is valid.

#### 9c. Human Review Gate

Stop. Print test paths, concise snippets, and RED report. Ask `question`: Approve all tests / Edit tests / Add missing test / Drop test / Abort slice.

Do not implement until approved.

#### 9d. Implement Per Test

Implement minimum code to make one approved failing test pass without breaking previous green tests.

Forbidden:
- Skipping/deleting tests
- Weakening assertions
- Mocking own modules to bypass logic
- Swallowing errors
- Hardcoding only the single example when tree requires general behavior

After each step, run touched tests. Max 3 attempts per test, then stop and preserve work.

#### 9e. Refactor

After all tests pass for the slice, refactor only if it reduces duplication/clarifies names without broadening scope. Tests stay green.

#### 9f. Verify Acceptance

Check acceptance criteria against diff. Mark todo complete only when behavior and criteria are met.

Update feature docs for changed behavior, data shape, access rules, workflow boundaries, or decision log entries.

### 10. Full Verify

Run feasible full verification:

```bash
just verify
```

### 11. Staged Review

Stage test + impl together by slice if user wants. Show cached stat/diff. Ask LGTM / Fix / Drop. Do not commit.

### 12. Completion

Report tests added, red-to-green transitions, checks run, skipped checks with reason, and residual risks.
