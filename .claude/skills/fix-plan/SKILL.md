---
name: fix-plan
description: Apply the findings in plan/review.md (the /review-plan deliverable) to the current plan/ folder — patches orchestrator.md, feature.md, group.md and task files to close every BLOCKER/MAJOR/MINOR gap (freeze missing contracts, fix DAG edges, re-cut ownership collisions, split oversized tasks into group folders, add missing test tasks, correct stale refs, de-ambiguate steps), records a resolution per finding, commits the patched plan on plan-integration. Edits ONLY plan/ — never source code, never summary/. Use for "fix the plan", "apply the review", "patch the plan", "close the review findings", between /review-plan and /execute-plan.
user-invocable: true
disable-model-invocation: true
model: claude-fable-5
---
# /fix-plan — Patch plan/ per the plan/review.md findings

You are a staff engineer closing review findings on your own plan. The input is `plan/review.md` — its findings and verdict. The output is the patched plan files, a resolution ledger, and a commit. **You edit ONLY `plan/`** — never source code, never `summary/`, and never `plan/review.md`'s findings themselves (you only append a resolution section). Every finding is either fixed or consciously rejected; none is silently skipped.

The chain: `/parallel-plan`→`plan/` · `/review-plan`→`plan/review.md` · **`/fix-plan`→patches plan/** · then `/review-plan` again (in a BLOCK cycle) or `/execute-plan`.

This skill takes no arguments. It always processes the whole `plan/` plus `plan/review.md` at the repo root.

## Model & effort (mandatory)

Run on **Fable 5** (`claude-fable-5`) at **`xhigh`** effort:
- **Per-feature fixers via Workflow (PRIMARY):** set `model: "fable"` and `effort: "xhigh"` on every `agent()` call — fixers are fire-once writers with nothing to re-drive. With 3 or more affected features, use one Workflow; otherwise a background Agent batch (`run_in_background: true`).
- **Everything runs in the background** — collect via completion notifications; no foreground blocking.

## Output style

Keep all patched plan prose in clear, precise technical prose, following the same preservation rules as `/parallel-plan`: code, contracts, `path:line` references, commands, tables, headings, and the ORDER of numbered steps stay exact. The resolution ledger is one line per finding.

## Step 1 — Load the review and the plan (main thread)

1. **Be on `plan-integration`.** If `plan/` is absent on the current branch but the branch exists, run `git checkout plan-integration`. If `plan-integration` never existed (a hand-made plan reviewed on the current branch), stay here — all commits land on this branch. If `plan/review.md` is missing, **stop**: "run `/review-plan` first." If the verdict is SHIP with zero findings, **stop**: nothing to fix. **Resume:** if review.md already carries a `## Resolution (fix-plan)` section, process ONLY the findings that have no resolution row (a prior run was interrupted or partial).
2. **Parse every finding row** (the Blockers, Major, and Minor tables): bucket, location, gap, suggested fix, and evidence (the Minor table has no Evidence column — that field is simply absent there). Also parse the Coverage matrix's UNCOVERED rows.
2b. **Memory (token-savior):** load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<repo/feature> dead end")` — never patch the plan back into a documented dead end. A suggested fix that re-attempts one gets reworked to address the root cause instead, with the recall noted in its resolution row. Fetch hits with `memory_get`; verify each recall against the current plan/code before acting on it. Tools absent → skip silently, never block.
3. **Read the plan files each finding touches** (orchestrator.md, the relevant feature.md/group.md, task files) and skim `summary/overview.md` for grounding on coverage fixes.
4. **Partition the findings:**
   - **GLOBAL** — touches orchestrator.md or spans more than one feature: cross-feature contracts (#2), the feature DAG (#3), cross-feature ownership collisions (#4), sub-pools (#8), the merge order, a missing `ZZ-tests/` (#6), Requirements/AC text and Coverage-matrix repairs (#11 — sharpen an unverifiable AC into `Given/when/then` or metric-threshold form, map every GAP AC to a task+gate, add the missing requirement for orphan work or cut the work).
   - **PER-FEATURE** — lives inside one `plan/NN-<slug>/` folder: coverage additions (#1), FC*/GC* freezes (#2), the task DAG (#3), intra-feature ownership (#4), granularity/group splits (#5), the per-feature test task (#6), stale refs (#7), the execution mode (#9), ambiguity (#10), spec/validation defects scoped to one feature's tasks (#11).
   - **REJECT candidates** — findings that are wrong or consciously out of scope: record them with a reason; do not patch.

## Step 2 — Apply the GLOBAL fixes (main thread, first)

Cross-feature decisions need one mind — never delegate them:
1. Freeze the missing C* contracts (as real code, not prose), fix the feature DAG edges, re-cut colliding ownership (re-assign globs, or hoist the shared file to one owner plus the delta-block protocol), resize the sub-pools, fix the merge order, and add a `ZZ-tests/` skeleton if it is missing.
2. **Ripple the changes:** every feature.md and task file referencing a changed contract id, glob, or wave must be updated to match — grep `plan/` for the old id and leave no dangling references.
3. **Record resolutions immediately:** as each global fix lands, append its resolution row to the `## Resolution (fix-plan)` section of review.md (create the section on the first append; on a resumed run, merge rows into the existing section — never start a second one). Incremental rows are what make the Step-1 resume rule work.

## Step 3 — Fan out one fixer per affected feature (parallel, background)

Only features with PER-FEATURE findings get a fixer. Each fixer owns exactly its `plan/NN-<slug>/` folder — disjoint, so there are no collisions. Prompt each:

```
You are patching ONE feature's plan slice per review findings. Edit ONLY files under
plan/NN-<slug>/. Spawn nothing.

READ: plan/orchestrator.md (the updated C* contracts, pasted below); your plan/NN-<slug>/feature.md
plus all of its task-*.md files and nested group folders; and the summary domain report(s) if a
coverage fix needs grounding: <list>.

FINDINGS to close (verbatim rows): <paste this feature's finding rows>

RULES:
- Apply each finding's fix (or a better one — say why). An oversized task (#5) converts into a GROUP
  folder: a group.md (feature.md shape, GC<node-path>.k contracts, sub-task DAG, launch prompts) plus
  sub-task files.
- A missing test task (#6) → add task-NN-tests.md, last in the DAG. A stale ref (#7) → verify the
  real code and fix the path:line (paths marked `(new)` are checked against the restructure
  move-map). Ambiguity (#10) → replace it with concrete steps and code. A #11 inside this feature →
  tighten the task's Implements/Testing sections so every mapped AC names its proving test and gate;
  cut task work no AC demands (or return it as a proposed-requirement note for the main thread).
- Use namespaced contract ids only (FC<NN>.k, GC<node-path>.k). Keep the template sections and the order
  of numbered steps intact. Match the repo conventions per the summary.
- Do not touch other features' folders, orchestrator.md, review.md, or source code.

Return one line per finding — `<finding> · fixed/rejected · <what changed / why rejected>` — plus the
list of files you touched.
```

As each fixer returns, append its resolution rows to review.md's `## Resolution (fix-plan)` section immediately (same incremental rule as Step 2.3) — an interrupted run then resumes with only the unresolved findings.

## Step 4 — Verify and write the resolution ledger (main thread)

1. **Run self-checks over the patched plan:** every DAG (feature level plus each task/group level) topologically sorts; the ownership matrix is disjoint per wave; contract ids are unique and namespaced; every referenced task file exists; `ZZ-tests/` is present; no dangling old contract ids remain; the Coverage matrix shows 100% of ACs COVERED (task + gate each) and every AC is testable.
2. **Confirm every finding is resolved:** fixed, or rejected with a reason. An unaddressed finding is your defect — fix it now.
3. **Verify the resolution section is complete** (rows were appended incrementally in Steps 2–3; fill any missing ones now). Final shape:

```markdown
## Resolution (fix-plan)
| Finding (severity · bucket · location) | Resolution | Note |
|----------------------------------------|------------|------|
| BLOCKER · #4 · 02-api/feature.md | fixed | src/shared/types.ts hoisted to C3, sole owner 01-core |
| MINOR · #10 · 03-ui/task-02 | rejected | step already concrete, reviewer misread |
```

## Step 5 — Commit and report (main thread)

1. On `plan-integration` (or the current branch for a hand-made plan): `git add plan/ && git commit -m "plan: apply review fixes (<f> fixed, <r> rejected)"`. Stage `plan/` ONLY.
2. Print to the console: the fixed/rejected counts by severity, the features patched, any group splits made, and the single next action. State any dead end the fix designed around as a durable fact — save them via `mcp__token-savior__memory_save` so the next planning cycle recalls it:
   - If the prior verdict was BLOCK → "Re-run `/review-plan` — the blockers were structural, verify the patch."
   - If the prior verdict was REVISE → "`/execute-plan`" (re-review optional).
   - If the prior verdict was SHIP (with MINOR findings patched) → "`/execute-plan`".

## Quality bar

- **Plan-only:** zero edits outside `plan/`; review.md is touched only by appending the Resolution section.
- **Complete:** every finding row has a resolution; rejections are reasoned, never silent.
- **Consistent:** the patched plan passes the same self-checks `/review-plan` runs (DAGs, ownership, ids, references).
- **Grounded:** coverage and stale-ref fixes are verified against `summary/` and the real code, not invented.
- **Clear prose:** patched plan text in precise, complete-sentence technical prose; code, contracts, and tables exact.
