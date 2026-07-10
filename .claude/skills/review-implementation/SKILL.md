---
name: review-implementation
description: Audit the EXECUTED implementation of an N-level plan/ folder (the /execute-plan result) on three axes — (1) plan conformance: reads plan/changes.md (per-task changed files + line ranges /execute-plan recorded), verifies code at those ranges implements task specs + honors frozen contracts (C*/FC*/GC*); (2) real-world quality: gaps the plan itself missed (edge cases, error paths, integration holes), designs that could be simpler/better; (3) test sufficiency: promised tests exist, registered, green, AND actually cover edge/failure paths meaningfully. One read-only reviewer agent per feature + global cross-feature checks, optionally re-runs the global gate, writes severity-tagged plan/reviewImplementation/implementationReview.md (a dedicated folder that leaves the original plan untouched) + prints verdict SHIP/FIX/BLOCK; leaves plan/ intact for /fix-implementation. Use for "review the implementation", "audit what the agents built", "check the code against the plan", "post-execute review", after /execute-plan.
user-invocable: true
disable-model-invocation: true
model: claude-fable-5
---
# /review-implementation — Audit the executed code against plan/

You are a principal engineer doing a brutal post-execution code review. Your job is to find what the builders missed — not to agree; agreement is not useful, finding defects is. You work **goal-backward from the acceptance criteria** — the builders report what they did; you determine whether they did it. Four jobs, all mandatory:
1. **Conformance** — find where the built code diverges from the plan, breaks contracts, skips promised tests, or edits what it should not.
2. **AC gap analysis** — walk every R\*/AC in orchestrator.md goal-backward against the actual code and classify it MET (cite file:line + the proving test) / STUB (placeholder, always-true return, hard-coded success, TODO in the primary path, assertions checking type not value, mocks left in production paths) / PARTIAL (name the uncovered case) / NOT_MET (say where you looked) / UNVERIFIABLE (spec defect — tag it; `/fix-implementation` handles it). A run-log `done` task with STUB/PARTIAL ACs is **falsely complete** — the worst finding class. Also sweep the reverse: code no AC requires is OVER-BUILT — it gets formalized (a proposed requirement, handed to `/fix-implementation`) or removed; silent scope creep is never accepted.
3. **Real-world quality** — find gaps the PLAN itself missed but the code exposes (unhandled edge cases, error paths, races, integration holes), and places where a simpler, cleaner, or more idiomatic design was possible. Plan conformance is not the same as good code; judge the code on its own merits too.
4. **Test sufficiency** — not "tests exist" but "tests are MEANINGFUL": edge and failure paths actually asserted rather than smoke-only, coverage matching the risk, GUI/e2e present wherever the work is user-facing.

You are **read-only on source and plan** — never edit code, orchestrator.md, feature.md, group.md, the task files, the run-log, or changes.md. Find the gaps and report them; `/fix-implementation` patches them (an `/execute-plan` re-run finishes `failed`/`pending` features). The only file you write is the report under `plan/reviewImplementation/` — a dedicated folder that leaves the original plan untouched. You never retire `plan/`; it stays intact for the fix cycle.

This is the chain's final gate: `/codebase-summary`→`summary/` · `/parallel-plan`→`plan/` · `/review-plan` gap-checks · `/fix-plan` patches · `/execute-plan` runs it and writes `plan/changes.md` · **`/review-implementation` audits the result** · `/fix-implementation` patches the findings — the cycle repeats until SHIP.

This skill takes no arguments. It always audits the whole implementation, with the plan root at `plan/`.

## Model & effort (mandatory)

Run on **Fable 5** (`claude-fable-5`) at **`xhigh`** effort, and spawn the reviewers the same way:
- **Workflow tool (PRIMARY):** set `model: "fable"` and `effort: "xhigh"` on every `agent()` call — the default for reviewer fan-outs of 3 or more.
- **Agent tool (fallback, 1–2 agents):** set `model: "fable"` and `run_in_background: true` on every reviewer call. Effort is inherited from the session, so run the session at `xhigh`.

## Output style

Write `plan/reviewImplementation/implementationReview.md` (create the `plan/reviewImplementation/` folder if absent) and the console output in clear, precise technical prose. Preserve EXACTLY: code, inline `code`, `path:line` references, commands, type definitions, tables, and headings. Never drop a finding's substance.

## Finding taxonomy — what you hunt

Every finding gets one bucket and one severity.
1. **Spec miss** — a task Implementation step is absent, or implemented differently with no justification. A task with zero changes is the worst case.
2. **Contract breach** — the code deviates from a frozen C* (orchestrator), FC* (feature.md), or GC* (group.md) contract: a signature, shape, route, schema, or event differs from the contract text.
3. **Ownership violation** — a file was changed outside its task's or feature's declared `Owns` globs.
4. **Test insufficiency** — promised unit/integration/GUI tests are absent, unregistered (per the repo's registration rules), or never run green per the run-log — OR they are present but WEAK: happy-path-only, no edge or failure assertions, asserting nothing meaningful, coverage far below the risk, or a user-facing flow with no GUI/e2e.
5. **Convention breach** — the code violates the repo conventions (`CLAUDE.md`/summary): style, layering, error idiom, naming.
6. **Quality** — dead code, duplication, TODO stubs, swallowed error paths, or a task's Maintainability/UX requirements left unmet.
7. **Stray edit** — a changes.md range traceable to NO task (an unplanned change).
8. **Ledger drift** — changes.md is wrong against the actual git diff (a missing file, a phantom file, wrong ranges), the run-log has a `merged` row without a pasted gate PASS, or a `done` task row without a per-AC Verification report (a hand-waved verification log is itself a finding).
9. **Gap beyond the plan** — a hole the PLAN never covered but the built code exposes: an unhandled edge case or error path, a race, missing input validation, an integration seam nobody owns, behavior undefined for real inputs. Plan silence is no excuse; judge the code against reality.
10. **Better design** — a materially simpler, cheaper, or more idiomatic implementation was possible: needless abstraction, a reinvented existing helper, the wrong layer, an N+1 pattern, over-complex state, or a module/file living where it fights the domain (flag this even when the PLAN put it there — up to whole-structure redraws when the gains justify it). Only findings worth real rework — no taste nits.

Severity: **BLOCKER** (a contract breach, an unimplemented or falsely-complete task, a red gate, a layering break, or a #9 that corrupts data or crashes) · **MAJOR** (test insufficiency, an ownership violation, a spec miss needing rework, a real #9 gap, a #10 with concrete payoff, unacknowledged over-build) · **MINOR** (polish, small drift, nice-to-have #10 items).

**Defect origin:** every finding also carries `code-defect` (the code must change — `/fix-implementation`) or `spec-defect` (the plan/AC was missing, incomplete, or wrong — `/fix-implementation` resolves it; classification: missing criterion | incomplete criterion | wrong criterion | missing requirement). Bugs are spec bugs until proven otherwise — before filing a pure code-defect, check whether any AC actually covered the failing behavior.

## Step 1 — Load the ledger and the plan (main thread)

1. **Locate `plan/`** on `plan-integration`. If it is absent on the current branch but the branch exists, run `git checkout plan-integration` and read there. If `plan/` is missing, **stop** — there is nothing to audit.
2. **Read the ledgers:** `plan/changes.md` (file · ranges · task, per feature) and `plan/run-log.md` (what merged, failed, or was deferred). If changes.md is missing or partial, **derive it**: the anchor is the commit that created the plan (`git log --diff-filter=A --format=%H -- plan/orchestrator.md | head -1` — the NEWEST add; an older add exists when a previous cycle's plan was retired and a new one created); run `git diff -U0 <anchor>..plan-integration`, excluding `plan/` itself; map each file to its owning feature via the plan's `Owns` globs; mark those rows `derived` and warn. Where ranges are stale (post-merge drift), trust the git diff over the ledger and note a #8 finding. A block marked `unverified` re-derives the same way. On a re-review after `/fix-implementation`: rows whose task field is `fix (…)` — and the `## fix-implementation (global)` section — attribute to the prior fix cycle (its Resolution rows), never to #1/#3/#7 strays; range drift those fixes caused is expected, not a #8 finding.
3. **Read `plan/orchestrator.md` in full** (the cross-feature C* contracts, the feature roster with owned paths, the global gate, the global DoD) plus **every merged feature's `feature.md`** (task roster, FC* contracts, feature gate), and skim the task files, **recursing into group folders** (`group.md` plus sub-tasks, any depth). If `summary/` exists, skim `overview.md` for the conventions and risks.
4. **Read the project `CLAUDE.md`/`AGENTS.md`** — conventions and layering rules (needed for #5 findings).
5. **Prior cycle:** if `plan/reviewImplementation/implementationReview.md` already exists with a `## Resolution (fix-implementation)` section (this is a re-review after `/fix-implementation`), read its rows first. A finding marked `rejected` there is settled — re-open it only with NEW evidence; otherwise carry it into the fresh report's `## What is good` as one `rejected-upheld` line. A `deferred` improvement is not a defect — do not re-file it as a finding.
5b. **Memory (token-savior):** load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<repo/feature> recurring defect pattern")` and `memory_search("<repo> dead end")` — a recalled pattern is a hunting lead, not a finding on its own: audit that bug class harder in the code it touches, and where the built code re-attempts a documented dead end without addressing its root cause, that is a #9 (or #3 if it strayed to do so). Fetch hits with `memory_get`; verify each recall against the current code before citing it. Tools absent → skip silently, never block.
6. **Build the matrices** (before fanning out):
   - **Ownership matrix** — each changes.md file mapped to its actual changing task versus its plan-declared owner. A mismatch is #3; no owner at all is #7.
   - **Task-coverage matrix** — each task mapped to its changes.md rows, or marked "NO CHANGES". An auditable feature's task with no changes is a #1 BLOCKER candidate (unless its run-log row says `deferred` or `skipped`).
   - **Ledger sanity** — the changes.md file set compared against `git diff --stat` of the integrated range. Missing or phantom files are #8.

## Step 2 — One read-only reviewer per merged feature (parallel)

Fan out **one reviewer per auditable feature** — auditable means run-log status `merged`, `pruned`, or `gate-green` (verified but left unmerged by git policy; audit it on its branch). Skip `failed`/`pending`/`running` features — list them as unauditable. Launch all reviewers in one BACKGROUND batch: one Workflow when there are 3 or more, otherwise multiple `Agent` calls in one message with `run_in_background: true`. Collect via completion notifications. Use a read-only agent type (`Explore`, a project reviewer, or `general-purpose` told not to edit). Reviewers write NO files — they return findings as text, and you aggregate. Prompt each:

```
You are doing an ADVERSARIAL, read-only review of ONE feature's IMPLEMENTATION against its plan. Do
not edit any file; reply with findings only. If you spawn sub-agents, use model "fable" (Fable 5) at
xhigh effort.

READ: plan/NN-<slug>/feature.md plus all of its task-*.md files and nested group folders (group.md
plus sub-tasks — recurse fully); the frozen contracts pasted below (C* + FC* + GC*); this feature's
changes.md slice, pasted below (file · ranges · task); and this feature's run-log rows, pasted below
(task ledger + gate result — your evidence for what ran green).

CODE LOCATION: <merged/pruned feature → the integrated plan-integration checkout | gate-green
unmerged feature → branch <name>, worktree <path, if kept> — read the code THERE (`git show
<branch>:<path>` works without a checkout); on plan-integration this feature's code does not exist>.

METHOD — open the CODE; do not trust the ledger. FOUR AXES, all mandatory:
AC VERIFICATION (goal-backward — work from the criteria, not forward from the diff):
- For every AC this feature implements (listed in its tasks' Implements sections): classify MET
  (cite file:line + the proving test) / STUB (always-true, hard-coded success, TODO in primary path,
  type-only assertions, mocks in production paths) / PARTIAL (name the uncovered case) / NOT_MET
  (say where you looked) / UNVERIFIABLE (tag spec-defect). Read the actual code before citing —
  never infer from commit messages or the run-log's Verification lines; those are claims, you are
  the check. A done task with STUB/PARTIAL ACs → report `falsely_complete` (#1 BLOCKER).
- Reverse sweep: changed code no AC requires → OVER-BUILT (#10, or #7 if untraceable to any task).
CONFORMANCE:
- Open EVERY listed file at the listed ranges, plus enough surrounding code to judge. If ranges are
  stale, re-derive them from the git diff and flag the drift (#8).
- Per task: is each Implementation step actually present at the cited locations? Flag deviations with
  evidence, one line each (#1).
- Contracts: compare the code against the contract text VERBATIM — signatures, shapes, routes,
  schemas (#2).
- Conventions and layering per CLAUDE.md/summary (#5). Quality: dead code, stubs, swallowed errors (#6).
- Changed ranges outside every task's Owns are stray (#7); outside the feature's Owns is an ownership
  violation (#3).
REAL-WORLD QUALITY — judge the code on its merits; plan silence is no excuse:
- Hunt for gaps the plan never covered: unhandled edge cases, error paths, races, missing input
  validation, undefined behavior for real inputs, integration seams nobody owns (#9). Ask: "what
  breaks in production that no task mentions?"
- Better design: needless abstraction, a reinvented existing helper (name it), the wrong layer, N+1
  patterns, over-complex state — only rework-worthy findings, no taste nits (#10).
TEST SUFFICIENCY — open the TEST CODE; do not just check existence:
- The promised tests exist, are registered per the repo rules, and ran green per the run-log (#4).
- Read the assertions: are edge and failure paths actually asserted? Happy-path-only is a finding.
  Does coverage match the risk? Does every user-facing flow have GUI/e2e? A weak test is a #4 finding
  even when it is green.
- If a cheap suite command is available, you may run it — but respect the lock etiquette: one build
  per build directory, and anything binding a host-wide singleton (display, shared test DB) wrapped
  in `flock /tmp/pvn-<resource>.lock -c '<cmd>'`.

Findings, ONE line each:
  <BLOCKER|MAJOR|MINOR> · <bucket #1-#10> · <code-defect|spec-defect> · <path:range or task file> ·
  <gap> · <one-line fix>
Plus an AC LEDGER: one line per AC — `AC<x>.<n> · MET/STUB/PARTIAL/NOT_MET/UNVERIFIABLE · <evidence>`.

For a large feature you MAY spawn one read-only sub-agent per task (fable, xhigh) and aggregate;
stay read-only throughout.

Reply with the findings table sorted by severity, plus a 2-bullet verdict: is the feature SHIPPABLE
as built, and what is its worst gap?
```

## Step 3 — Global cross-feature checks (main thread)

The reviewers each see one feature — you see across all of them. From the Step-1 matrices and the reviewer output:
1. **Contract drift at boundaries** — for every C* contract touched by two or more features, open BOTH sides and confirm an identical interpretation (#2, BLOCKER if divergent).
2. **Ownership violations and strays** — matrix mismatches not already reported (#3, #7).
3. **Task coverage** — every "NO CHANGES" task must be resolved: deferred (per the run-log) or a finding (#1).
4. **The test feature** — `ZZ-tests/` ran and is green per the run-log; user-facing tasks have GUI/e2e evidence (#4).
5. **Ledger honesty** — the remaining #8 rows (phantom or missing files, `merged` rows without a gate PASS).
6. **Cross-feature gap sweep** — the per-feature reviewers wear blinders; you skim the WHOLE integrated diff once, hunting #9 gaps that live between features: a seam nobody owns, inconsistent error handling across a boundary, duplicated logic that two features each built (#10).
7. **Live gate** — if the verdict is borderline (zero BLOCKERs but 3 or more MAJORs) or the run-log's gate evidence is missing, re-run the global gate from orchestrator.md and paste the result. Respect the build/test lock etiquette (one build per directory).

## Step 4 — Synthesize the report and verdict (main thread)

Aggregate the reviewer and global findings and **de-duplicate** (the same gap from a reviewer and a matrix is one row). Write `plan/reviewImplementation/implementationReview.md`:

```markdown
# Implementation review — <feature set name>   (built code vs plan/)

## Verdict: <SHIP | FIX | BLOCK>
One line: SHIP = no BLOCKER/MAJOR findings, merge to base · FIX = MAJOR gaps, patch then re-gate ·
BLOCK = BLOCKER gaps, do not merge to base until fixed.

## Blockers
| Bucket | Location (path:range) | Task | Gap | Fix | Evidence |
|--------|----------------------|------|-----|-----|----------|

## Major
| Bucket | Location | Task | Gap | Fix | Evidence |

## Minor
| Bucket | Location | Task | Gap | Fix |

## Acceptance-criteria matrix   ← goal-backward ground truth; SHIP requires it clean
`<n>/<n> ACs MET.` One row per non-MET AC: R · AC · status (STUB/PARTIAL/NOT_MET/UNVERIFIABLE) ·
evidence · owning task · origin (code-defect/spec-defect). List falsely-complete tasks explicitly.
Over-built code (no AC requires it): formalize-or-remove rows.

## Task coverage matrix
Each task → its changes.md rows → the reviewer verdict (implemented / partial / missing / deferred).

## Per-feature verdicts
One row per feature: shippable as built? worst gap? (List unaudited failed/pending features too.)

## Gate evidence
The global gate: the run-log result or the live re-run output. PASS/FAIL per command.

## Improvements (bucket #10, non-blocking)
Rework-worthy simplifications, ranked by payoff. Each entry: location, current shape, better shape, why.

## What is good
The checks that PASSED (contracts honored, ownership clean, tests present AND meaningful, no gaps
found) — so that "no findings" demonstrably means checked-and-clean, not skipped.
```

**Verdict logic:** any BLOCKER → BLOCK. No BLOCKER but at least one MAJOR → FIX. Only MINOR findings or none → SHIP. **Additional SHIP preconditions:** every feature in the run log is `merged`, `pruned`, or `gate-green`-by-policy — any `failed`/`blocked`/`pending` feature caps the verdict at FIX (an unfinished feature means the implementation is incomplete) — AND the AC matrix shows every AC MET (or explicitly deferred in the run log).

After writing the report, commit it on `plan-integration`: `git add plan/reviewImplementation/ && git commit -m "plan: reviewImplementation verdict <VERDICT>"` (keeps the review in the plan's git history; the original plan files stay untouched).

## Step 5 — Report and next action (main thread)

Print to the console: the verdict, the finding counts by severity, the top 3 BLOCKER/MAJOR findings (one line each), the report location (`plan/reviewImplementation/implementationReview.md`), and the single next action. State any recurring defect pattern the audit confirmed as a durable fact — save them via `mcp__token-savior__memory_save`, so the next cycle's recall surfaces the class before it recurs:
- BLOCK → "Run `/fix-implementation` to patch the blockers, then re-run `/review-implementation`." Keep `plan/`.
- FIX → "Run `/fix-implementation` (or accept the risk), then re-run `/review-implementation`." Keep `plan/`.
- SHIP → echo any MINOR findings AND any `gate-green` unmerged branches with their merge order to the console, then tell the user: "Implementation verified — merge the echoed `gate-green` branches in order (if any), then `plan-integration` into base." **Leave `plan/` intact** — `/review-implementation` never retires it; the plan and its ledgers stay as the durable record.

## Quality bar

- **Read-only:** only the report under `plan/reviewImplementation/` is written. No source, plan, or ledger edits, and `plan/` is never retired — it stays intact for `/fix-implementation`.
- **Code-verified:** every finding comes from OPENED code at a real `path:line`, never from trusting the ledger or from vibes. Test findings come from READ assertions, not existence checks. AC verdicts are goal-backward — the run-log's Verification lines are claims, the reviewer is the check.
- **Origin-routed:** every finding tagged code-defect or spec-defect; spec defects go to `/fix-implementation` as well, never get silently coded around.
- **Beyond the plan:** real-world gaps (#9) and better designs (#10) are hunted, not just conformance — plan silence never excuses broken code.
- **Every tier:** feature-level checks (contracts, ownership, gate) AND task/group-level checks (spec steps, tests, quality, recursed) — via the per-feature reviewers plus the global matrices.
- **Complete:** every changes.md row is traced to a task; every task is traced to changes or an explicit deferral.
- **Honest verdict:** SHIP/FIX/BLOCK follows the severity logic; unaudited features are named; clean areas are listed.
- **Clear prose:** the report, console output, and reviewer replies in precise, complete-sentence technical prose; tables, `path:line` references, and code preserved exactly.
