---
name: execute-plan
description: Execute an N-level plan/ folder (orchestrator.md + per-feature folders with feature.md + task files + nested group folders, the /parallel-plan deliverable) by driving an N-tier agent hierarchy — one git worktree+branch per FEATURE off plan-integration, each wave of independent features dispatched as a parallel batch of FEATURE-LEAD agents, each lead itself SPAWNS one task sub-agent per leaf task (or authors a Workflow), one SUB-LEAD per group folder (recursing), and integrates them in its worktree. Arbitrate resources hierarchically (build/test locks, port sub-pools, displays, test DB), run the gate per task/feature/merge, integrate feature branches in merge order. Uses summary/ as the map and refreshes it at the end to match the integrated code; records every changed file + line ranges per task to plan/changes.md (feeds /review-implementation). Use for "execute the plan", "run the orchestrator", "launch the agents", "implement the plan", "spawn the feature/task agents", "ship the plan".
user-invocable: true
disable-model-invocation: true
model: claude-fable-5
---
# /execute-plan — Drive an N-level plan/ folder with a hierarchy of worktree agents

You are the top integrator and build-master of an N-tier team. You do not code features or tasks yourself, and you do not micro-manage tasks (that is the leads' job). You read the plan, stand up one worktree per feature, dispatch one **feature-lead** per feature wave by wave, broker the shared host resources, gate every checkpoint, and integrate the feature branches in order — surfacing failures honestly, never papering over them.

```
YOU (top, main thread)   ── FEATURE waves, one worktree per feature, integrate feature branches
   └─ feature-lead  (you spawn one per feature) ── SPAWNS one task sub-agent per leaf task (or a
                                                    Workflow), one SUB-LEAD per group folder,
                                                    integrates results in its worktree
         └─ task agent  (lead spawns)           ── implements + tests ONE leaf task
         └─ sub-lead    (lead spawns per group) ── reads group.md, recurses same rules one level down
```

The chain: `/codebase-summary`→`summary/` · `/parallel-plan`→`plan/` · `/review-plan` gap-checks · `/fix-plan` patches findings · **`/execute-plan`→runs it** · `/review-implementation` audits the built code (consuming the `plan/changes.md` this skill writes) · `/fix-implementation` patches audit findings.

This skill takes no arguments. It always runs the whole `plan/` at the repo root and auto-resumes from the first unfinished feature wave when a run log exists.

**Spawning agents and creating worktrees at EVERY tier is the core of this skill** (you spawn leads; leads spawn task agents, sub-leads for group folders, and workflows — recursively). It runs **autonomously end to end** — worktree creation, spawns, and merges all proceed without asking whenever their gates are green; never stop for approval. `plan/` stays in place after the run (its ledgers are `/review-implementation`'s input; `plan/` is never auto-retired).

## Model & effort (mandatory)

Run on **Fable 5** (`claude-fable-5`) at **`xhigh`** effort. The tiering is fixed:
- **FEATURE-LEADS via Agent tool, BACKGROUND:** `model: "fable"` and `run_in_background: true` on every lead, with the whole wave dispatched as one parallel batch (one message) and collected via completion notifications. Using the Agent tool (not Workflow) for leads is non-negotiable: Step-3.4 triage re-drives a failed lead via `SendMessage`, which reaches Agent-tool agents (including background ones) but never Workflow `agent()` calls. Background dispatch frees you mid-wave to update ledgers and start triaging early failures while long leads are still running. Effort is inherited from the session, so run the session at `xhigh`.
- **TASK FAN-OUTS via Workflow (inside each lead, PRIMARY):** `model: "fable"` and `effort: "xhigh"` on every `agent()` call, for any fan-out of 3 or more — a deterministic task DAG, per-call effort, and schema-validated returns; it runs as a background task, which is exactly what we want. For a fan-out of 1–2, use a background Agent batch. Workflow nests only ONE level, and **sub-leads are always spawned via the Agent tool, never inside a Workflow** — they must fan out themselves and stay SendMessage-reachable.
- **Propagate:** every lead prompt instructs the lead to spawn its task agents, sub-leads, and workflows with the same `fable` + `xhigh`, recursively at every level. The Step-3 template carries this — keep it.

## Output style — ledgers stay TERSE

Write the run log, changes ledger, and console summaries in clear technical prose, but keep ledger entries strictly structured: ONE line each, no prose recaps, no narration, no timestamps. Preserve EXACTLY: code, `path:line` references, commands, branch names, and tables. Paste failing output verbatim — but only on failure.

## Core principles

1. **`orchestrator.md` and each `feature.md` are the source of truth. Parse them; do not reinvent.** The orchestrator holds the feature roster, feature DAG and waves, cross-feature contracts (C*), per-feature worktree and branch names, lead launch prompts, the shared-file protocol, resource sub-pools, the gate, and the global DoD. Each feature.md holds that feature's task roster, task DAG, intra-feature contracts, execution mode, and feature gate. You drive the top tier and hand each lead its feature.md. On ambiguity: the orchestrator wins cross-feature questions, feature.md wins intra-feature ones, and otherwise fall back to the `Depends on` and `Owns` declarations.
2. **Isolation is non-negotiable at every tier.** One feature = one worktree = one lead. One leaf task = one task agent, working in the feature worktree (with disjoint ownership) or in a sub-worktree the lead forked off the feature branch. One group folder = one sub-lead, applying the same rules one level down (recursively). Never touch a worktree you do not own.
3. **Respect both DAGs.** Independent features in the same wave run concurrently (one batch of lead `Agent` calls in one message). Inside a feature, the lead runs independent tasks concurrently and sequences dependent ones. Dependent features wait (for a merge, or branch off their predecessor).
4. **You are the TOP broker; leads are sub-brokers.** You lease each feature a **sub-pool** (a port range, display slot, test DB) so concurrent features do not overlap; each lead sub-leases distinct slots to its task agents.
5. **Contracts travel with every agent, at every tier.** Each lead prompt carries the cross-feature C* contracts verbatim; the lead passes those plus its intra-feature FC* to every task agent; sub-leads add their group's GC* and pass the full stack down. No agent ever redesigns a contract.
6. **Verify every checkpoint.** A task must meet its task DoD; a lead must run the feature gate before reporting green; you must run the global gate after each feature merge. A wave is incomplete until its features are green and integrated.
7. **Never push to or pull from origin.** Git usage is worktrees plus (where allowed) local integration. Honor the `CLAUDE.md` git policy — if it forbids local merges, leads must use disjoint-path or sequential task modes (no intra-feature merging), and you stop at verified branches and hand them back.
8. **`plan-integration` is both the fork base AND the merge target.** Feature worktrees fork from it; feature merges land back onto it — never onto the user's original base branch. Task sub-worktrees fork from their feature branch and merge back into it (inside the lead). If `plan-integration` is missing (a hand-made plan), create it off the current branch first.
9. **Validation is a ladder, and "done" means verified ACs.** Gates run in order (1 build → 2 unit → 3 integration → 4 perf-if-AC → 5 smoke → 6 GUI/review), stop at the first failure — later results are meaningless — and re-run from Gate 1 after any fix. A task is done only when each of its mapped ACs is individually verified (Verification report: `AC · check · observed`); NEVER on "existing code looks related". A previously-green gate going red is a **regression = P0**: stop forward work on that branch, fix it first.
10. **Circuit breakers, not grinding.** Three consecutive validation failures on one task → `blocked` + a dead-end entry; the same failure signature twice in a row is a **ceiling** — stop re-driving and diagnose the blocker (missing dep? ambiguous spec? tooling?) instead of adding retries. When the loop is not stabilizing, the problem is upstream — the spec, the gates, or the ownership — never the retry count. A task file or contract that contradicts reality is a **spec defect**: agents never code around it; it is returned classified (`missing criterion | incomplete criterion | wrong criterion | missing requirement`) and routed to `/fix-plan`.

## Step 1 — Load and parse the plan (main thread)

1. **Locate `plan/` FIRST.** It lives on `plan-integration`. If it is absent on the current branch but the branch exists, run `git checkout plan-integration`. If `plan/` is still absent, stop and tell the user to run `/parallel-plan` first. If `summary/` is absent, warn and continue without it (leads skip the summary read) — a hand-made plan need not have one.
2. **Read `summary/overview.md`** and skim the linked domain reports for the map. This is grounding; do not re-derive it.
3. **Read `plan/orchestrator.md` in full** and extract: the feature roster (id/folder/lead/branch/worktree/owned paths/#tasks); the feature waves and DAG (concurrent versus sequential, the critical path); the cross-feature contracts (C*, verbatim); the worktree commands; the lead launch prompts and preamble; the shared-file rules and per-feature sub-pools; the gate commands; and the global DoD.
4. **Read each `plan/NN-<feature>/feature.md`** for its task roster, task DAG, intra-feature contracts, execution mode (disjoint-parallel/sub-worktree/sequential), and feature gate. **Recurse into group folders** (`task-NN-<slug>/group.md`) — same shape, any depth. You do not drive the tasks, but you must validate that every feature.md and group.md is coherent before handing it to a lead.
5. **Read the project `CLAUDE.md`/`AGENTS.md`** — conventions and the git policy (which decides whether you merge feature branches and whether leads may use sub-worktree mode).
5b. **Memory (token-savior):** load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<repo/feature> dead end")` — recalled dead ends join `plan/dead-ends.md` (marked `recalled`) and are pasted into the relevant lead prompts. Tools absent → skip silently.
6. **Validate that the plan is runnable.** Every feature folder has a feature.md; every group folder has a group.md; every referenced task file exists; branch and worktree names are unique; every level's DAG is acyclic; parallel nodes own disjoint paths (flag collisions). If the orchestrator is missing, derive the order from the feature.md `Depends on` fields and warn.
7. **Pre-flight the Coverage matrix.** Every AC in orchestrator.md's Requirements maps to at least one task AND a gate. A GAP row, an unmapped AC, or task work tracing to no requirement → **stop and route to `/fix-plan`** (a legacy plan with no Requirements section: warn once and proceed on task DoDs alone). Never silently continue with coverage gaps.

## Step 2 — Pre-flight (main thread)

1. **Ensure `plan-integration` exists** (it is the fork base and merge target). It is normally created by parallel-plan with `plan/` committed on it — use it as-is. If missing (a hand-made plan), run `git branch plan-integration <current-branch>` and check it out.
2. **Working tree clean** on `plan-integration` — a dirty tree means the worktrees about to fork would miss those changes. "Clean" means no tracked modifications; untracked files under `plan/` (this skill's own ledgers from a prior run) do not count as dirty and must not block a resume. If tracked files are modified, report and stop unless told to proceed. **If `plan/` or `summary/` is untracked** (hand-made plan), **commit them now on `plan-integration`** (`git add plan/ summary/ && git commit -m "plan: add plan inputs"`) — untracked files do not propagate into worktrees, and the leads must find their briefs there.
3. **Compute and print the schedule:** the feature waves in order; per wave, the features (id · branch · worktree · owned paths · depends-on · #tasks · lead); **per feature, its task breakdown** (task id · depends-on · owned paths · execution mode); the merge points; and the resource plan (which feature gets which port-range/display/test-DB sub-pool, plus a **fixed lock-file name per host-wide singleton**, e.g. `/tmp/pvn-display.lock`). Mark what is already done per the run log (resume).
4. **Proceed autonomously.** Print the schedule, then mutate — never stop for approval.
5. **Do NOT create worktrees here.** Feature worktrees are created lazily at the start of each wave (Step 3.1) — a wave-2 feature must fork the post-merge state of `plan-integration` (or its dependency's branch), which does not exist yet at pre-flight.
6. **Initialize the run log** `plan/run-log.md` — TERSE: one feature row `NN-slug · branch · status` (`pending`/`running`/`gate-green`/`merged`/`pruned`/`failed`/`blocked`), with nested task rows `task-MM · done/failed/blocked/spec-defect/deferred/skipped · ≤6-word note` (indented one level per group nesting; `deferred`/`skipped` mark tasks intentionally not executed — `/review-implementation` exempts them from no-changes findings). Gate results: `gate PASS`, or `gate FAIL: <cmd>` plus the failing output verbatim (failures only). No timestamps, no prose. The run log doubles as the resume ledger. Also **initialize `plan/changes.md`** (the implementation ledger — Step 3.4 fills it, `/review-implementation` consumes it), **`plan/dead-ends.md`** (`DE-N · <approach attempted> · <root cause — technical, never "it broke"> · verdict: do not reattempt / retry-if-<condition>`; seed it with recalled memories), and **`plan/backprop-log.md`** (one appended entry per spec defect: `id · task node · classification · evidence · pattern_category` — categories like input_validation, concurrency, error_handling, integration, observability; 3+ entries sharing a category = systemic, report a cross-cutting amendment candidate for `/fix-plan`).

## Step 3 — Execute feature waves (loop)

For each feature wave, in order:

1. **Create this wave's feature worktrees and lease the sub-pools.** Create the worktrees now, using the orchestrator's commands, **forking every feature branch off the current `plan-integration`** (append it as the start-point if the command omits one); a feature whose `Depends on` merge was deferred branches off the dependency's branch instead. A worktree or branch already present from an interrupted prior run is reused as-is — create only what is missing. Do not create task sub-worktrees — leads make those. Then lease each feature a port-range/display-slot/test-DB sub-pool with no concurrent overlap; record the leases in the broker ledger. Each lead sub-leases slots within its sub-pool to its task agents.
2. **Dispatch the whole wave as one BACKGROUND parallel batch** — multiple lead `Agent` calls in one message, every one with `run_in_background: true` (use `general-purpose` or the lead type the orchestrator names). Never dispatch leads via Workflow (SendMessage re-drive cannot reach them). Collect results per completion notification — triage failures immediately while sibling leads are still running. The lead prompt:

   ```
   <orchestrator preamble — persona, "match repo conventions per CLAUDE.md", git-is-worktrees-only>

   You are the FEATURE-LEAD for <NN-slug>. Your worktree is the ABSOLUTE path <…/wt-NN-slug> on
   branch <branch>, forked from <START-POINT — plan-integration, or the dependency branch for a
   deferred-merge feature>. Operate ONLY inside it.

   Read summary/overview.md (if present), plan/orchestrator.md (the cross-feature Frozen contracts
   are pasted below), and YOUR brief plan/NN-<slug>/feature.md (tasks, task DAG, intra-feature FC*, execution
   mode, per-task launch prompts).

   YOU ORCHESTRATE THIS FEATURE'S TASKS — do not hand-code them all yourself:
   - SPAWN one sub-agent per leaf task; author a Workflow when fanning out 3 or more (preferred —
     Workflow is available to you because you were spawned via the Agent tool). For 1–2 tasks, use a
     background Agent batch. This is expected and encouraged.
   - A task entry that is a GROUP folder (task-NN-<slug>/group.md) → spawn a SUB-LEAD (via the Agent
     tool, NOT inside your Workflow — it must be able to fan out itself, and Workflow nests only one
     level) with this same prompt shape one level down: it orchestrates group.md's sub-tasks (with
     its GC* contracts plus the full contract stack pasted in), sub-leases from YOUR slot, and
     returns a nested ledger plus CHANGES rolled up. Recurse as deep as the plan nests.
   - Follow the task DAG: run independent tasks CONCURRENTLY (one batch of Agent calls, or a
     parallel()/pipeline() stage); sequence dependent tasks after their predecessors.
   - Honor feature.md's execution mode:
       disjoint-parallel → parallel task agents in THIS worktree; disjoint paths, no collisions.
       sub-worktree → one task sub-worktree off THIS branch per parallel colliding task
         (git worktree add ../wt-NN-taskMM -b task/NN-MM <branch>, or Workflow
         isolation:'worktree'), merged back in task-DAG order. The task/ prefix is mandatory — a
         branch name nested under the existing feature branch (e.g. feat/01-auth/task02) is a git
         ref namespace conflict and fails. Only if the git policy permits local
         merges (feature.md says).
       sequential → tasks one after another in this worktree.
   - Pass EVERY task agent BOTH the cross-feature contracts (below) AND your intra-feature FC*
     verbatim. They code against them; nobody redesigns them.
   - Sub-lease your pool <ports/display/test-DB>: give each task agent a DISTINCT slot; nothing
     outside it. Host-wide singletons ONLY via the flock wrapper (verbatim, passed to every task
     agent): <flock /tmp/pvn-<resource>.lock -c '<cmd>' — one lock file per singleton, names listed here>
   - MODEL & EFFORT: spawn every task agent with model "fable" (Fable 5); in a Workflow, set
     model:"fable" and effort:"xhigh" on every agent() call. Do not downgrade.
   - VALIDATE on the ladder: gates in order (build → unit → integration → perf-if-AC → smoke →
     GUI/e2e per the task's depth), STOP at the first failure, re-run from Gate 1 after a fix. A
     previously-green gate going red is a regression = P0: stop forward work, fix it first.
   - A task is done ONLY when each of its mapped ACs is individually verified — every task agent
     returns a Verification report (`AC<x>.<n> · <check run> · <observed result>`, one line per AC).
     NEVER accept "existing code already handles this" without a check run that proves the AC.
   - A task that fails: re-drive it (re-spawn its agent with the failing output pasted in) up to its
     depth's retry cap (quick 1, standard/thorough 2). The SAME failure signature twice = ceiling —
     stop re-driving, diagnose the blocker instead. After 3 consecutive validation failures mark the
     task `blocked`, append a DEAD END entry (approach · root cause · verdict), and continue only
     with tasks that do not depend on it — never paper over a red.
   - SPEC DEFECT: if the task file or a contract contradicts reality (the code, the ACs, or
     physics), do NOT code around it. Return the task as `spec-defect` with a one-line
     classification — missing criterion | incomplete criterion | wrong criterion | missing
     requirement — plus evidence. The orchestrator routes it to /fix-plan.
   - DEAD ENDS TO AVOID (do not reattempt; root causes documented): <paste relevant
     plan/dead-ends.md entries, or "none">
   - Return prose caveman-compressed (drop articles/filler; fragments fine). Code, paths, commands,
     branch names, error strings, and ALL structured blocks (ledger, CHANGES, Verification reports,
     gate results) stay EXACT — never compress those.

   CROSS-FEATURE FROZEN CONTRACTS (code against these verbatim; never redesign):
   <paste C* block>

   Honor disjoint ownership — this feature touches only the paths feature.md declares, and each task
   only its declared paths. Do not edit other features' files. Use the dependency-delta protocol
   (declare dependencies in the fenced block; do not hand-edit the shared manifest).

   Before declaring the FEATURE done, integrate all task results and run the FEATURE GATE, pasting
   the results:
   <feature gate commands — or the global gate from orchestrator.md if feature.md defers to it>

   Return (structured, no prose recap):
   - the branch name
   - TASK LEDGER: one line per task, `task-MM · done/failed/blocked/spec-defect/deferred/skipped ·
     ≤6 words`; group rows indent their sub-task lines one level under the group row
   - VERIFICATION: per done task, its Verification report lines (`AC · check · observed`)
   - DEAD ENDS: any new `DE · approach · root cause · verdict` lines (omit if none)
   - SPEC DEFECTS: per spec-defect task, `task · classification · evidence` (omit if none)
   - CHANGES: one line per touched file, `path · added <a-b,c-d> / changed <e-f> / deleted · <full
     task node path>` (leaf: `task-03`; nested: `task-04/task-02` — a bare task-MM is ambiguous in an
     N-level plan). Line ranges are NEW-side (post-change numbering). Derive them from
     `git diff -U0 $(git merge-base <START-POINT> HEAD)..HEAD` — START-POINT is the branch you forked
     from (stated above; NOT always plan-integration — a deferred-merge feature forks off a
     dependency branch, and diffing against plan-integration would swallow the dependency's changes).
     Parse the hunks; do not guess.
   - the dependency-delta block (unioned across tasks)
   - the gate result: `PASS`, or `FAIL: <cmd>` plus the failing output verbatim; a 1-line smoke result
   If any task or the gate fails, return the exact failing output — do not claim success.
   ```

3. **Arbitration = static leases + file locks.** Leads run in the background — you act between notifications, but NO agent can ask you anything mid-run, so live brokering is still impossible. Build, typecheck, and lint run inside each feature worktree (separate build directories), in parallel across features. Anything that binds a host-wide singleton (a host-wide port, the X display, a shared test DB), including E2E runs, **self-serializes via `flock`**: every lead prompt carries the wrapper `flock /tmp/pvn-<resource>.lock -c '<cmd>'` (it blocks until the lock is free and releases on command exit), and leads pass the same wrapper to their task agents. One lock file per singleton, with the names fixed in the Step-2.3 schedule — no agent invents lock names.
4. **Collect; update the run log and changes ledger.** Record each feature's task ledger (one line per task) in the run log; append its CHANGES block to `plan/changes.md` under `## NN-<slug>` — one line per file, `path · added <ranges> / changed <ranges> / deleted · <full task node path>`. The ranges reflect the feature branch at gate time; a merge may shift them (`/review-implementation` re-derives when they are stale). Append the lead's DEAD ENDS to `plan/dead-ends.md` and its SPEC DEFECTS to `plan/backprop-log.md` (with `pattern_category`). **Ledger honesty spot-check:** compare the file list from `git diff --stat <start-point>...<feature-branch>` (three dots — diffs from the merge base, same anchoring as the lead's derivation; two dots diverges whenever the start-point ref advanced after the fork) against the lead's CHANGES — on a mismatch, `SendMessage` the lead once to re-derive; if it persists, mark the block `unverified` in changes.md. A `done` task with NO Verification report is not done — `SendMessage` the lead once for it; still missing → downgrade the row to `failed (unverified)`. When the feature gate is green, set the status to `gate-green`. If the gate fails or a task failed, **triage**: `SendMessage` the lead the failing output so it re-drives in context; cap at roughly 2 retries — but the SAME failure signature twice is a ceiling: stop re-driving and diagnose (missing dependency? spec defect → backprop-log + `/fix-plan`? tooling?). If it still fails, mark the feature `failed`, **continue the wave's independent features** (a red feature blocks only its dependents — they defer to a later wave or to a re-run after `/fix-plan`), and report with the failing output. **Never integrate a red feature.** Halt the run entirely only when nothing unblocked remains.
5. **Integrate.** Once every feature in the wave is `gate-green`, integrate per the orchestrator's merge order and shared-file rules:
   - Merge autonomously — no approval stop.
   - **Always merge onto `plan-integration`**, never onto the base branch. Check it out (or use a dedicated integration worktree) and merge the feature branches in the prescribed order. The base branch stays untouched.
   - **Honor the git policy** for the destination. Merging onto `plan-integration` counts as permitted local integration; if the policy forbids local merges entirely, do not merge — leave the verified branches, record them, and tell the user which branches to merge and in what order. Advance only if dependents were branched off their predecessors (deferred-merge).
   - Merge in feature order; resolve shared-file conflicts by the documented rule (union the manifest delta-blocks into one edit and a single reinstall; sequence any multi-owner file in orchestrator order).
   - **Re-run the gate after each feature merge.** If a merge breaks the gate, revert that feature (with a rollback note) — do not patch it in place.
   - **Prune each merged feature branch and worktree once the post-merge gate is green.** Worktree first (`git worktree remove <path>` — it refuses if dirty; do not use `--force`, report instead), then `git branch -d <branch>` (safe delete only, never `-D`). Clean any orphan task sub-worktrees the lead left behind: `git worktree remove <path>` each one explicitly (safe, no `--force`), THEN `git worktree prune` for stale admin entries, then delete their branches — note `git worktree prune` alone only clears metadata for already-deleted directories, it removes nothing on disk. **Skip pruning** (defer to Step 4) for any branch that a not-yet-created feature lists as its branch base (deferred-merge), and for any branch whose post-merge gate was red or reverted. Record the transition `merged` → `pruned`.
   - **Never push to or pull from origin.**
6. **Advance** to the next wave only when the current one is green and integrated (or branched forward).

## Step 4 — Final verification and report (main thread)

1. **Run the global gate** once on the integrated result (or note that it cannot run end to end if branches were left unmerged by policy).
2. **Check the global DoD** item by item — met or unmet, with evidence (gate output, acceptance criteria).
3. **Sweep stale branches and worktrees** that were merged but deferred (dependency bases that are now free, `merged`-but-not-`pruned` rows, orphan task sub-worktrees). With the global gate green: `git worktree remove` each one explicitly (no `--force`), then `git worktree prune` for stale admin entries, then `git branch -d` (safe delete only). Keep any branch the git policy says to keep unmerged, and any dirty worktree (report those).
4. **Refresh `summary/` to match the integrated code** (main thread only, after the global gate is green — the leads never touch `summary/`, so this is the one place it is brought current). Update only the `summary/` docs whose subject materially changed this run — new/removed/renamed symbols, realigned C* contracts, added or deleted modules/features, changed flows — grounded in `plan/changes.md` and the merged diff. Match `summary/`'s existing structure, headings, and terse register exactly; do not rewrite untouched sections, do not restate the plan, do not impose an outside style. `summary/overview.md` gets an edit only when the high-level map actually moved. This documents what shipped; it never edits plan specs.
5. **Finalize the ledgers** (terse rows only): `plan/run-log.md` — each feature's final status with its nested task ledger (including Verification-report evidence lines for done tasks), the branches produced (and pruned), the merge order applied (or pending), the gate results, and any failure with its reason. **Finalize `plan/changes.md`**: every merged feature must have its CHANGES block; fill any gap by deriving it from `git diff -U0` of that feature's merge and mark those rows `derived`. Finalize `plan/dead-ends.md` and `plan/backprop-log.md`; if 3+ backprop entries share a `pattern_category`, add a one-line `SYSTEMIC: <category> — <cross-cutting amendment candidate>` row. **Commit the ledgers and the summary refresh on `plan-integration`**: `git add summary/ plan/run-log.md plan/changes.md plan/dead-ends.md plan/backprop-log.md && git commit -m "plan: run ledgers + summary refresh"` — untracked ledgers would pollute the next cycle's derivation, so commit them.
6. **Print the console summary**: feature waves completed, features green versus failed/blocked (with task counts), AC verification totals (`<n>/<n> ACs verified`), what was integrated and pruned, spec defects routed to `/fix-plan`, new dead ends (stated as durable facts — save them via `mcp__token-savior__memory_save`), what remains (branches awaiting a human merge, unmet DoD items, follow-ups), and the single next action.

## Resource arbitration (top broker; leads are sub-brokers)

The worktrees share one machine. Keep the ledger in the main thread and lease **hierarchically**:
- **Build/test lock** — one build/unit/e2e run per build directory. Distinct feature worktrees have distinct directories (parallel is fine); the same directory serializes. Task agents within a feature share its build directory unless they are in sub-worktrees — the lead serializes them.
- **Port sub-pools** — each concurrent feature gets a range (feature 1 → 7100–7109, feature 2 → 7110–7119); the lead hands each task a distinct port from its range. No range overlap, no intra-feature port reuse.
- **Display** — the headed/screenshot display goes to one E2E run at a time tree-wide, **flock-serialized** (`flock /tmp/pvn-display.lock -c '<cmd>'` — no live broker exists mid-wave); the lead passes the wrapper to its tasks.
- **Test DB** — a throwaway DB per feature; the lead sub-partitions it (a per-task schema) if its tasks run integration tests concurrently.

Tell each lead its sub-pool; tell each lead to tell each task its slot. No agent self-assigns a shared singleton.

## Failure handling and resume

- **Idempotent and resumable.** On re-invocation, read the run log and the existing worktrees/branches; skip everything `merged`, `pruned`, or `gate-green` and resume at the first unfinished wave. When re-spawning a lead for a partially-done feature, **paste that feature's prior task-ledger lines into the lead's prompt** — the run log lives in the main tree, not in the lead's worktree, so the lead cannot read it itself; it skips the tasks marked done.
- **Per-feature retry.** On a failed feature gate (or task), `SendMessage` the lead the exact failure so it re-drives; cap at roughly 2 retries before marking it `failed` and halting the wave.
- **Per-branch rollback.** Each feature is one squashable branch, so a bad merge reverts in isolation. Inside a feature, a bad task sub-worktree merge reverts on the feature branch without disturbing its siblings.
- **Never hide a red.** If a gate fails or the DoD is unmet, say so plainly with the failing output. Never mark something done on an agent's say-so — require the pasted gate result and the per-AC Verification report.
- **Budget-aware.** If the user set a token budget (Workflow `budget` API), check it at wave boundaries; when it cannot fund the next wave, stop CLEANLY at the boundary (ledgers committed, worktrees intact) and report the resume point — an interrupted wave is worse than a shorter run.

## Quality bar

- **Faithful:** the feature waves, contracts, branch names, merge order, and gate all come from `orchestrator.md`; each lead drove its tasks from its `feature.md` — nothing improvised.
- **Isolated at every tier:** every feature in its own worktree; every task in the feature worktree (disjoint) or a task sub-worktree; groups recurse the same rules; no cross-worktree edits; no shared singleton double-bound tree-wide.
- **Verified, not assumed:** every "done" is backed by a pasted gate result (task DoD, feature gate, global gate) AND a per-AC Verification report; merges are re-verified. Regressions are P0.
- **Convergent:** re-drives capped, ceilings diagnosed instead of ground against, spec defects backpropagated to `/fix-plan` instead of coded around, dead ends recorded once and never reattempted.
- **Git-safe:** no origin push/pull; local merges only where allowed, each one gated; merged feature branches and task sub-worktrees pruned (safe deletes only).
- **Honest and resumable:** the run log (with its nested task ledgers) reflects reality including failures; a re-run resumes cleanly.

## Wrap-up

Print the run log location (`plan/run-log.md`) and the changes ledger (`plan/changes.md`), the feature waves completed, the branches produced and their merge state, any unmet DoD items, and the single next action — `/review-implementation` to audit the built code against the plan (it leaves `plan/` intact). `plan/` always stays in place after this run.
