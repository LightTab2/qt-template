---
name: review-plan-opus
description: Gap-check an N-level plan/ folder (the /parallel-plan-opus deliverable — orchestrator.md + per-feature folders with feature.md + task files + nested group folders) against the codebase map in summary/. Read-only on the plan — never edits it; dispatches one read-only reviewer agent per feature to cross-check that slice vs summary domains + real code, runs global cross-feature checks (coverage, DAG, ownership collisions, contract completeness, stale refs, sub-pools, tests), writes a severity-tagged gap report to plan/review.md + prints verdict SHIP/REVISE/BLOCK. Use for "review the plan", "check the plan for gaps", "audit the plan", "is the plan complete", "validate plan/ against summary", before /execute-plan-opus.
user-invocable: true
disable-model-invocation: true
model: claude-opus-4-8
---
# /review-plan-opus — Adversarially gap-check plan/ against summary/

You are a principal engineer doing a brutal pre-execution plan review. Your only job is to find what the plan **misses, gets wrong, or leaves ambiguous** before a fleet of agents executes it. Your job is to find what the planner missed — not to agree; a review that says "looks good" without evidence of what was checked is a wasted review. You are **read-only on the plan** — never edit orchestrator.md, feature.md, or the task files. Find the gaps and report them; `/fix-plan-opus` patches them.

This is the gap-check step between `/parallel-plan-opus` and `/execute-plan-opus`: `summary/` is the map · `plan/` holds the orchestrator, feature.md files, and tasks · **`/review-plan-opus` audits the plan against the summary** · `/fix-plan-opus` patches the findings · `/execute-plan-opus` runs it · `/review-implementation-opus` audits the built code · `/fix-implementation-opus` patches it.

This skill takes no arguments. It always reviews the whole `plan/` at the repo root.

## Model & effort (mandatory)

Run on **Opus 4.8** (`claude-opus-4-8`) at **`xhigh`** effort, and spawn the reviewers the same way:
- **Workflow tool (PRIMARY):** set `model: "opus"` and `effort: "xhigh"` on every `agent()` call — the default for reviewer fan-outs of 3 or more.
- **Agent tool (fallback, 1–2 agents):** set `model: "opus"` and `run_in_background: true` on every reviewer call. Effort is inherited from the session, so run the session at `xhigh`.

## Output style

Write `plan/review.md` and the console output in clear, precise technical prose. Preserve EXACTLY: code, inline `code`, `path:line` references, commands, type definitions, tables, and headings. Never drop a finding's substance for the sake of brevity.

## Gap taxonomy — what you hunt

Every finding gets one bucket and one severity. **Boldness is not a gap:** a whole-repo restructure (re-layering, mass moves/renames) is a legitimate plan — never flag scope or drasticness itself, only the taxonomy buckets below. The opposite direction IS a finding: a plan that contorts itself around bad existing structure it should have redrawn is a #10 ambiguity/design finding, MAJOR.
1. **Coverage** — a summary domain, risk, debt item, invariant, or gotcha that matters for this change but that no feature or task addresses.
2. **Contract** — a type/API/schema/event/signature that two or more features (or tasks) share but that is NOT frozen in C* (orchestrator), FC* (feature.md), or GC* (group.md). Each agent would invent its own version, and they would conflict.
3. **DAG** — any level's DAG (feature, task, or group) has a cycle, a missing edge (a node consumes a non-predecessor's output), or a false edge (needless serialization).
4. **Ownership collision** — two SAME-WAVE features own overlapping paths, OR two parallel nodes (same wave, any level) own overlapping paths. Sequenced overlap is legitimate: a wave-A restructure feature handing paths to later features that then own and edit them is the prescribed pattern, not a collision.
5. **Granularity** — a feature not split into tasks (a blob), a task too big yet not converted into a GROUP folder, a group nested with no size justification, or a lead with no real task structure.
6. **Test** — a feature missing its per-feature test task, the plan missing the final `ZZ-tests/` feature, or user-facing work with no GUI/e2e coverage.
7. **Stale/false ref** — a `path:line`, symbol, or command that does not exist in the real code, or an imposed convention that contradicts the repo's actual style. Exception: paths marked `(new)` are post-restructure — verify them against the restructure feature's move-map, not against disk; an UNMARKED missing path is still a finding, and so is a `(new)` path absent from the move-map.
8. **Resource** — concurrent features without distinct sub-pools, or a sub-pool too small for a feature's parallel tasks, causing a singleton collision at execution time.
9. **Execution-mode error** — `sub-worktree` mode where the git policy forbids merges, or `disjoint-parallel` for tasks that actually share files.
10. **Ambiguity** — a step, edge case, or error path so vague that a fresh agent would have to invent behavior.
11. **Spec/validation defect** — a requirement with no acceptance criteria; an AC no automated test or gate can verify (subjective — "looks good", "feels fast" — or non-deterministic); an AC missing from the Coverage matrix or mapped to no task/gate (AC-level coverage is the bar — "task covers R1" is insufficient when R1 has 6 ACs and the task addresses 2); a task whose work traces to NO requirement (over-build / scope creep); or a plan binding a task to a tool the summary's discovered-capabilities list does not contain.

Severity: **BLOCKER** (execution fails or corrupts — cycles, collisions, missing contracts, a Coverage-matrix GAP row) · **MAJOR** (real rework — coverage, test, granularity gaps, unverifiable ACs) · **MINOR** (polish).

## Step 1 — Load the map and the plan (main thread)

1. **Locate `plan/`** on `plan-integration`. If it is absent on the current branch but the branch exists, run `git checkout plan-integration` and read there. If `summary/` or `plan/` is missing, **stop** and tell the user to run `/codebase-summary-opus` and/or `/parallel-plan-opus` first.
2. **Read `summary/overview.md` in full** and skim the linked domain reports. Build the expected-coverage checklist: the domains, the cross-cutting flows, and the **"Risks, debt & open questions"** section — each item is something the plan should address or consciously scope out.
3. **Read `plan/orchestrator.md` in full**, plus **every `feature.md` and every nested `group.md`**, and skim the task files. Extract: the feature roster and DAG, the cross-feature C* contracts, each feature's tasks with their task DAG and FC* contracts (plus group GC* contracts, recursively), the execution modes, the owned paths, the sub-pools, and the test features/tasks.
4. **Read the project `CLAUDE.md`/`AGENTS.md`** — conventions and the git policy (needed for findings #9 and #7).
4b. **Memory (token-savior):** load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<feature/repo> dead end")` and `memory_search("<repo> recurring defect pattern")` — a plan that re-attempts a documented dead end without addressing its root cause is a #10 MAJOR. Tools absent → skip silently.
5. **Prior cycle:** if plan/review.md already exists with a `## Resolution (fix-plan-opus)` section (this is a re-review after `/fix-plan-opus`), read its rows first. A finding marked `rejected` there is settled — re-open it only with NEW evidence; otherwise carry it into the fresh report's `## What is good` as one `rejected-upheld` line.
6. **Build the global matrices** (before fanning out):
   - **Ownership matrix** — each owned glob mapped to the feature/task claiming it. A glob claimed by more than one feature, or by more than one parallel task within a feature, is a candidate **collision** (#4).
   - **Coverage matrix** — each summary domain and risk mapped to the feature/task covering it, or marked "UNCOVERED" (#1).
   - **AC matrix** — re-derive the orchestrator's Coverage matrix independently: every AC of every R\* → the task(s) implementing it → the test/gate proving it. A GAP row, an AC the orchestrator's matrix silently omits, or an untestable AC is a #11 finding. Also sweep the reverse direction: task work no AC requires (#11 over-build).
   - **DAG check** — topologically sort the feature DAG and each task/group DAG; any cycle is a BLOCKER (#3).

## Step 2 — One read-only reviewer per feature (parallel)

Fan out **one reviewer per feature**, each cross-checking its slice against the real code and the summary domains it touches. Launch all of them in one BACKGROUND batch: one Workflow when there are 3 or more, otherwise multiple `Agent` calls in one message with `run_in_background: true`. Collect via completion notifications. Use a **read-only** agent type (`Explore`, `general-purpose` told not to edit, or a project reviewer). Reviewers write NO files — they return findings as text, and you aggregate. Prompt each:

```
You are doing an ADVERSARIAL, read-only review of ONE feature's plan slice. Find gaps; do not fix
them; do not edit any file; reply with findings only. If you spawn sub-agents, use model "opus"
(Opus 4.8) at xhigh effort.

READ: summary/overview.md plus the per-domain report(s) for the domains this feature touches: <list>;
plan/orchestrator.md (the C* contracts, feature DAG, and sub-pools); YOUR feature's
plan/NN-<slug>/feature.md plus all of its task-*.md files and nested group folders (group.md plus
sub-tasks — recurse fully).

METHOD — understand, don't pattern-match. Read the cited code to verify the plan's claims:
- Confirm that every path:line, symbol, and command the feature cites ACTUALLY EXISTS (via the MCP
  recall/graph tools or by opening the file). Flag stale references. Paths marked `(new)` are
  post-restructure: verify them against the restructure feature's move-map (the `## Move-map
  (old → new)` section of its feature.md — restructure feature: <name it, or "none in this plan">)
  instead of disk.
- Confirm the plan matches the repo conventions the summary documents.

TAXONOMY — tag every finding with exactly one bucket:
  #1 coverage (summary domain/risk unaddressed) · #2 contract (shared type/API/schema not frozen in
  C*/FC*/GC*) · #3 DAG (cycle / missing edge / false edge, any level) · #4 ownership collision (same-wave
  nodes with overlapping paths; sequenced overlap is legitimate) · #5 granularity (blob feature /
  oversized task not made a group) · #6 test (missing per-feature test task / ZZ-tests / GUI-e2e) ·
  #7 stale or false ref · #8 resource (sub-pool overlap or undersized) · #9 execution-mode error ·
  #10 ambiguity (fresh agent must invent behavior) · #11 spec/validation defect (AC untestable or
  unmapped to task+gate; task work no requirement demands; a tool the capability list lacks)

CHECK against that taxonomy, each finding on ONE line:
  <BLOCKER|MAJOR|MINOR> · <bucket #1-#10> · <plan file:section> · <gap> · <one-line fix>
Specifically check: coverage of this feature's summary domains and risks; intra-feature contracts
(FC*, and GC* inside groups) frozen wherever tasks share a boundary; task DAG cycles, missing edges, or false edges; tasks
that are too big; ownership overlap between parallel tasks; the per-feature test task plus GUI/e2e
for user-facing work; execution-mode errors; and ambiguous steps a fresh agent would guess at.

For a large feature you MAY spawn one read-only sub-agent per task (opus, xhigh) to drill in, then
aggregate; stay read-only throughout.

Reply with the findings table (one-line format) sorted by severity, plus a 2-bullet verdict: is the
feature EXECUTABLE as written, and what is its single worst gap?
```

## Step 3 — Global cross-feature checks (main thread)

The reviewers cannot see across features — you can. Using the Step-1 matrices:
1. **Cross-feature ownership collisions** — any glob claimed by more than one feature IN THE SAME WAVE (#4, BLOCKER). Overlap between sequenced features (e.g. a restructure feature feeding later ones) is legitimate — do not flag it.
2. **Cross-feature contract gaps** — any type/API/schema/event that two or more features touch but that is not in C* (#2). Also verify that C* entries are real code, not prose.
3. **Feature DAG correctness** — a cycle (BLOCKER), a missing edge (a feature consumes another's output without depending on it), or a false edge (needless serialization).
4. **Coverage of summary risks** — walk the "Risks, debt & open questions" list and the domain map; each item must be covered or explicitly scoped out (the orchestrator's `Out of scope` section). UNCOVERED and unexplained is a #1 finding.
4b. **AC coverage & verifiability** — from the Step-1 AC matrix: 100% of ACs mapped to a task AND a gate; every AC automatable (a criterion an agent cannot validate will not be met); no orphan work (#11).
5. **The final cross-feature test feature** — does `ZZ-tests/` exist and depend on every implementation feature? Missing means a #6 MAJOR.
6. **Resource sub-pools** — every same-wave feature set has distinct, non-overlapping sub-pools sized for its parallel tasks (#8).
7. **Merge order sanity** — the orchestrator's merge order respects the feature DAG; shared-file owners and the delta-block protocol are defined for any manifest more than one feature edits.

## Step 4 — Synthesize the report and verdict (main thread)

Aggregate the reviewer and global findings. **De-duplicate** (the same gap found by a reviewer and by a global check is one row). Write `plan/review.md`:

```markdown
# Plan review — <feature set name>   (gap-check vs summary/)

## Verdict: <SHIP | REVISE | BLOCK>
One line: SHIP = no BLOCKER/MAJOR findings, execute as-is · REVISE = MAJOR gaps, patch then execute ·
BLOCK = BLOCKER gaps, do not execute until fixed.

## Blockers
| Bucket | Location (plan file:section) | Gap | Fix | Evidence |
|--------|------------------------------|-----|-----|----------|
| #4 ownership | 02-api/feature.md, 03-ui/feature.md | both own src/shared/types.ts | hoist to C* or make one feature sole owner | summary 01-core.md, path:line |

## Major
| Bucket | Location | Gap | Fix | Evidence |

## Minor
| Bucket | Location | Gap | Fix |

## Coverage matrix
Each summary domain/risk → covered by (feature/task) or **UNCOVERED**. Every UNCOVERED row must have
a finding above or an explicit "out of scope: <why>".

## AC matrix (verification-level coverage)
`<n>/<n> ACs covered.` One row per GAP/untestable/orphan finding: R · AC · defect · fix. (All
covered → the single summary line suffices.)

## Per-feature verdicts
One row per feature: executable as written? worst gap?

## What is good
The checks that PASSED (contracts frozen, DAGs acyclic, ownership disjoint, tests present) — so that
"no findings" demonstrably means checked-and-clean, not skipped.
```

**Verdict logic:** any BLOCKER → BLOCK. No BLOCKER but at least one MAJOR → REVISE. Only MINOR findings or none → SHIP.

After writing the report, commit it: `git add plan/review.md && git commit -m "plan: review verdict <VERDICT>"` — on `plan-integration`, or on the current branch if `plan-integration` does not exist (a hand-made plan). Committing keeps the review in the plan's git history and the working tree clean for the next step.

## Step 5 — Report and next action (main thread)

Print to the console: the verdict, the finding counts by severity, the top 3 BLOCKER/MAJOR findings (one line each), the report location (`plan/review.md`), and the single next action:
- BLOCK → "Run `/fix-plan-opus` to patch the findings, then `/review-plan-opus` again."
- REVISE → "Run `/fix-plan-opus` (or accept the risk), then `/execute-plan-opus`."
- SHIP → "Plan is sound — run `/execute-plan-opus`."

## Quality bar

- **Read-only on the plan:** no edits to orchestrator.md, feature.md, or task files. Only `plan/review.md` is written.
- **Evidence-based:** every finding cites a plan location plus a summary section or a real `path:line`. No vibes.
- **Every tier:** feature-level checks (DAG, contracts, ownership, sub-pools) AND task/group-level checks (granularity, FC*/GC*, node ownership, per-feature tests, recursed) — via the per-feature reviewers plus the global matrices.
- **Verified:** stale-ref findings come from opening the cited code, not from guessing.
- **Honest verdict:** SHIP/REVISE/BLOCK follows the severity logic; clean areas are listed explicitly.
- **Clear prose:** the report and console output in precise, complete-sentence technical prose; tables, `path:line` references, and code preserved exactly.
