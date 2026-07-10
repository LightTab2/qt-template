---
name: fix-implementation
description: Apply the findings in plan/reviewImplementation/implementationReview.md (the /review-implementation deliverable) to the EXECUTED CODE — patches source and tests on plan-integration (and on gate-green unmerged feature branches) to close every BLOCKER/MAJOR/MINOR finding (implement missed spec steps, realign code to frozen C*/FC*/GC* contracts, strengthen weak or missing tests, close edge-case/error-path gaps, remove strays, apply worthwhile #10 simplifications), records a resolution per finding, appends fix ranges to plan/changes.md, re-runs the gate, refreshes summary/ to match the shipped code, commits. Edits source + tests, then refreshes summary/ at the end — never plan specs (that is /fix-plan), never retires plan/. Use for "fix the implementation", "apply the impl review", "patch the code per the review", "close the impl-review findings", between /review-implementation and its re-run.
user-invocable: true
disable-model-invocation: true
model: claude-fable-5
---
# /fix-implementation — Patch the code per the plan/reviewImplementation/implementationReview.md findings

You are a staff engineer closing post-execution review findings on code a fleet of agents built. The input is `plan/reviewImplementation/implementationReview.md` — its findings and verdict. The output is patched source and tests, a resolution ledger, an honest `plan/changes.md` appendix, a re-run gate, a `summary/` refresh, and a commit. **You edit source code and its tests, then refresh `summary/` to match the shipped code** — never orchestrator.md, feature.md, group.md, or task files (a wrong SPEC is `/fix-plan`'s job), and never implementationReview.md's findings themselves (you only append a resolution section). The `summary/` refresh is a main-thread act at the very end (Step 4.6) — the parallel fixers never touch it. Every finding is either fixed or consciously rejected; none is silently skipped. You never retire `plan/` — it stays intact as the durable record; nothing in this chain auto-retires it.

The chain: `/execute-plan`→runs the plan and writes `plan/changes.md` · `/review-implementation`→`plan/reviewImplementation/implementationReview.md` · **`/fix-implementation`→patches the code** · then `/review-implementation` again — the cycle repeats until the verdict is SHIP. `plan/` is never auto-retired.

This skill takes no arguments. It always processes the whole `plan/reviewImplementation/implementationReview.md` at the repo root.

## Model & effort (mandatory)

Run on **Fable 5** (`claude-fable-5`) at **`xhigh`** effort:
- **Per-feature fixers via Workflow (PRIMARY):** set `model: "fable"` and `effort: "xhigh"` on every `agent()` call. With 3 or more affected features, use one Workflow; otherwise a background Agent batch (`run_in_background: true`).
- **Re-drives are fresh spawns.** A fixer whose fix fails the gate is not messaged — spawn a NEW targeted fixer with the failing output pasted in (Step 4). Fire-once semantics keep Workflow viable.
- **Everything runs in the background** — collect via completion notifications; no foreground blocking.

## Output style

All patched code matches the repo conventions exactly (`CLAUDE.md`/summary) — style, naming, error idiom, test layout; never impose an outside style. Ledger and resolution rows are TERSE: one line each, no prose recaps. Preserve EXACTLY: code, `path:line` references, commands, branch names, and tables. Paste failing output verbatim — but only on failure.

## Step 1 — Load the review, the plan, and the code map (main thread)

1. **Be on `plan-integration`.** If `plan/` is absent on the current branch but the branch exists, run `git checkout plan-integration`. If `plan-integration` never existed (a hand-made plan run on the current branch), stay here — all commits land on this branch. If `plan/reviewImplementation/implementationReview.md` is missing, **stop**: "run `/review-implementation` first." If its verdict is SHIP, **stop**: nothing to fix (MINOR-only polish was accepted; `plan/` stays intact). **Resume:** if implementationReview.md already carries a `## Resolution (fix-implementation)` section, process ONLY the findings that have no resolution row (a prior run was interrupted or partial).
2. **Parse every finding row** (the Blockers, Major, and Minor tables): bucket, location (`path:range` or task file), task, gap, suggested fix, and evidence (the Minor table has no Evidence column — that field is simply absent there). Also parse the `## Improvements` entries (bucket #10, non-blocking) — each is a candidate to apply, not an obligation.
3. **Read the context each finding needs:** `plan/orchestrator.md` (the frozen C* contracts, feature roster with owned paths, the global gate), the relevant `feature.md`/`group.md` (FC*/GC* contracts, feature gate), and the task files a #1 spec miss cites — the SPEC is the fix's target, not a suggestion. Read `plan/run-log.md` and `plan/changes.md` for each feature's status and code location: `merged`/`pruned` features live in the integrated `plan-integration` checkout; a `gate-green` unmerged feature lives on its own branch (fix it THERE — recreate its worktree with `git worktree add <path> <branch>` if its worktree was removed). Findings do not exist for `failed`/`pending` features (review-implementation lists them unaudited) — finishing those is `/execute-plan`'s resume job, not yours.
4. **Read the project `CLAUDE.md`/`AGENTS.md`** — conventions, layering rules, test registration rules, and the git policy.
4b. **Memory (token-savior):** load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<repo/feature> recurring bug pattern")`, `memory_search("<module> dead end")` — a recalled pattern may show a finding is already systemic (fix it one layer up and log the `pattern_category` in Step 4.5), and a recalled dead end warns off a fix that already failed. Fetch the top hits with `memory_get`; verify any recalled file/command against the code before acting on it. Tools absent → skip silently, never block.
5. **Partition the findings:**
   - **GLOBAL** — spans features or lives at a boundary: cross-feature contract drift (#2 with two sides), a seam nobody owns (#9 between features), logic duplicated across features (#10), ledger repairs (#8).
   - **PER-FEATURE** — the location falls inside one feature's `Owns` globs: spec misses (#1), one-sided contract breaches (#2), ownership strays to revert or legitimize (#3, #7), test insufficiency (#4), convention breaches (#5), quality (#6), in-feature gaps (#9), in-feature simplifications (#10).
   - **REJECT candidates** — findings that are wrong, or whose true defect is the PLAN (a bad spec, a wrong contract): record them with a reason — a wrong contract is rejected here and routed to `/fix-plan`, never silently recoded around.
   - **Improvements** — apply an entry only when its payoff clearly exceeds its risk and scope; otherwise record it `deferred` with a reason. A deferred improvement is not a defect.

## Step 2 — Apply the GLOBAL fixes (main thread, first)

Cross-feature decisions need one mind — never delegate them:
1. For boundary contract drift (#2), open BOTH sides and realign the CODE to the contract text verbatim — the contract never moves to meet the code. Own the unowned seams (#9): pick the layer the repo's architecture dictates, implement, and test it. Collapse cross-feature duplication (#10) into the existing helper (or the one right new home). Repair ledger rows (#8) by re-deriving from `git diff -U0`.
2. **Record resolutions immediately:** as each global fix lands, append its resolution row to the `## Resolution (fix-implementation)` section of implementationReview.md (create the section on the first append; on a resumed run, merge rows into the existing section — never start a second one). Incremental rows are what make the Step-1 resume rule work.

## Step 3 — Fan out one fixer per affected feature (parallel, background)

Only features with PER-FEATURE findings get a fixer. Fixers share the `plan-integration` checkout, so each owns exactly its feature's `Owns` globs (plus that feature's test paths) — disjoint, no collisions; an unmerged gate-green feature's fixer works in that feature's worktree instead. Prompt each:

```
You are patching ONE feature's IMPLEMENTATION per review findings. Edit ONLY source and test files
inside this feature's owned paths: <globs>. Never edit plan/, summary/, or other features' files.
If you spawn sub-agents, use model "fable" (Fable 5) at xhigh effort.

WORKTREE: <the plan-integration checkout | worktree <path> on branch <name> for a gate-green
unmerged feature — operate only there>.

READ: plan/NN-<slug>/feature.md and the task files the findings cite (a #1 spec miss is implemented
per the task file's Implementation steps — the spec is the target); the frozen contracts pasted
below (C* + FC* + GC*); the repo conventions per CLAUDE.md/summary.

FINDINGS to close (verbatim rows): <paste this feature's finding rows + applicable Improvements>

RULES:
- Realign code TO contracts (#2) — never redesign a contract; if the contract itself is wrong,
  return the finding as `rejected · contract defect, route to /fix-plan`.
- Test insufficiency (#4) → write or strengthen the tests: real edge and failure assertions, not
  smoke; register them per the repo's registration rules; GUI/e2e where the flow is user-facing.
- A gap beyond the plan (#9) → handle the edge case or error path properly AND add the test that
  proves it. A spec miss (#1) → implement the missing steps. A stray (#3/#7) → revert it, or keep
  it with a one-line justification in your resolution row. Quality (#6) → remove dead code and
  stubs, surface swallowed errors. Apply #10 entries exactly as scoped — no opportunistic rewrites.
- REGRESSION DISCIPLINE for every behavioral fix (#1/#2/#4/#9): first write the regression test
  that asserts the violated AC/behavior and CONFIRM IT FAILS against the broken code, commit it
  separately (`test: regression for <finding> (<AC id>)`), then fix until it passes — the pair of
  commits is the audit trail. A test that never failed proves nothing.
- Every fix line also carries a root-cause classification: `code-defect`, or `spec-defect
  (missing|incomplete|wrong criterion | missing requirement)` — spec-defects are rejected here and
  routed to /fix-plan, never recoded around.
- Run the targeted tests for what you changed and paste the result. Build/test etiquette: one build
  per build directory; anything binding a host-wide singleton (display, shared test DB) wrapped in
  `flock /tmp/pvn-<resource>.lock -c '<cmd>'`. Use the dependency-delta protocol for any shared
  manifest (declare in a fenced block; do not hand-edit it).

Return (structured, no prose recap):
- one line per finding: `<finding> · fixed/rejected/applied/deferred · <what changed / why not>`
- CHANGES: one line per touched file, `path · added <a-b,c-d> / changed <e-f> / deleted · fix
  (<severity> · <bucket> · <location>)` — ranges NEW-side, derived from `git diff -U0`, not guessed
- the targeted test result: PASS, or FAIL: <cmd> plus the failing output verbatim
```

As each fixer returns, append its resolution rows to implementationReview.md's `## Resolution (fix-implementation)` section immediately (same incremental rule as Step 2.2) — an interrupted run then resumes with only the unresolved findings.

## Step 4 — Gate, verify, and update the ledgers (main thread)

1. **Run the gates:** the feature gate on each patched unmerged branch, then the GLOBAL GATE from orchestrator.md on `plan-integration` (build + full suite + lint/format/typecheck), with the same flock etiquette. Paste the results.
2. **On a red gate, re-drive:** spawn a fresh targeted fixer with the failing output pasted in; cap at roughly 2 retries. Still red → **stop and report honestly** with the failing output; do not commit the red state as done, never paper over it.
3. **Confirm every finding is resolved:** fixed, rejected (with a reason), applied, or deferred. An unaddressed finding is your defect — fix it now. Final resolution shape:

```markdown
## Resolution (fix-implementation)
| Finding (severity · bucket · location) | Resolution | Note |
|----------------------------------------|------------|------|
| BLOCKER · #2 · src/api/routes.ts:88 | fixed | signature realigned to C3 verbatim |
| MAJOR · #4 · test/auth.test.ts | fixed | added expiry + malformed-token failure assertions |
| MINOR · #6 · src/ui/Panel.tsx:12 | rejected | flagged block is a registered fixture, reviewer misread |
| IMPROVEMENT · #10 · src/db/query.ts:40 | deferred | batching helper lands with next schema change |
```

4. **Append the fix ranges to `plan/changes.md`** so the ledger stays honest for the re-review: each CHANGES row goes into the owning feature's `## NN-<slug>` section verbatim (`path · added <a-b,c-d> / changed <e-f> / deleted · fix (<severity> · <bucket> · <location>)`); global fixes with no single owner go under a `## fix-implementation (global)` section. Prior rows' ranges may now be stale — expected; `/review-implementation` attributes `fix (…)` rows to the Resolution section and trusts the git diff over stale ranges.
5. **Append to `plan/backprop-log.md`** — one entry per behavioral finding fixed: `id · classification · <location> · <AC id or "no AC covered it"> · failing_test · fix_commit · pattern_category` (input_validation / concurrency / error_handling / integration / observability / …). One entry per finding, never bulk — patterns only emerge when each is logged separately. **3+ entries sharing a `pattern_category` (this cycle plus execute-plan's) = systemic:** print a warning and a cross-cutting amendment candidate for `/fix-plan` (fix it one layer up, not per-bug).
6. **Refresh `summary/` to match the shipped code** (main thread only, after the gate is green — never mid-run, never delegated to a fixer). Update only the `summary/` docs whose subject materially changed this cycle — new/removed/renamed symbols, realigned C*/FC*/GC* contracts, added or deleted modules, changed flows — grounded in `plan/changes.md` and the diff. Match `summary/`'s existing structure, headings, and terse register exactly; do not rewrite untouched sections, do not restate the plan, do not impose an outside style. `summary/overview.md` gets an edit only when the high-level map actually moved. This documents what shipped; it still never edits plan specs.

## Step 5 — Commit and report (main thread)

1. Commit each patched unmerged feature branch in its worktree: `git add <touched paths> && git commit -m "plan: apply implementationReview fixes (<feature>)"`. Then on `plan-integration` (or the current branch for a hand-made plan): `git add <touched source/test paths> summary/ plan/changes.md plan/backprop-log.md plan/reviewImplementation/implementationReview.md && git commit -m "plan: apply implementationReview fixes (<f> fixed, <r> rejected, <i> applied)"`. (Regression-test commits were already made separately per finding.) Stage the fix's paths ONLY — never sweep unrelated changes. Never push to or pull from origin.
2. Print to the console: the fixed/rejected/applied/deferred counts by severity, the features patched, the gate results, any SYSTEMIC `pattern_category` warning, and the single next action: "Re-run `/review-implementation` — the cycle continues until the verdict is SHIP." State the systemic patterns and any new dead ends as durable facts — save them via `mcp__token-savior__memory_save`; make it worth recalling next cycle.

## Quality bar

- **Specs frozen, summary current:** zero edits to plan specs; implementationReview.md is touched only by appending the Resolution section; changes.md only by appending fix rows. `summary/` is refreshed at the end (Step 4.6, main thread only) to match the shipped code — never mid-run, never by a fixer.
- **Complete:** every finding row has a resolution; rejections are reasoned, never silent; contract defects are routed to `/fix-plan`, not recoded around.
- **Verified, not assumed:** every fix is backed by a pasted targeted-test result and a green gate; a red gate is reported, never committed as done.
- **Contract-faithful:** code moves toward the frozen C*/FC*/GC* text — the contracts never move toward the code.
- **Honest ledgers:** changes.md reflects every fix range; the resolution table matches reality including deferrals.
- **Clear prose:** the console output and resolution notes in precise technical prose; code, `path:line` references, and tables exact.
