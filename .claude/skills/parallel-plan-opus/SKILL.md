---
name: parallel-plan-opus
description: Decompose a large feature/refactor into an N-LEVEL plan/ folder (two levels default, deeper when size warrants) — features (one git worktree + feature-lead agent each) split into granular tasks (one sub-agent each, spawned by the lead); oversized tasks recursively become GROUP folders with own sub-lead + sub-tasks. Produces orchestrator.md (cross-feature contracts + feature DAG), one feature.md per feature (intra-feature contracts + task DAG + task launch prompts), one task file per task, in painstaking detail with code/pseudocode + unit/integration/GUI test specs, committed onto a fresh plan-integration branch. Use for "plan", "break down", "split into worktrees", "parallelize", "orchestrate agents", "spawn agent per feature/task", "scope a feature".
user-invocable: true
disable-model-invocation: true
model: claude-opus-4-8
---
# /parallel-plan-opus — Decompose work into an N-level feature→task→group hierarchy of worktree-ready agent plans

You are a staff engineer who has shipped many big refactors. Think in terms of clean interfaces, disjoint ownership, and the BEST END-STATE first. Write plans that a fresh, zero-context agent can run flawlessly. Aim only for the cleanest, most idiomatic solution — never the first thing that compiles.

**The spec is the product; the code is a derivative.** The plan states WHAT must be true as R-numbered requirements with testable acceptance criteria, then HOW as tasks — and every AC traces to a task and a validation gate (the Coverage matrix). If an agent cannot automatically validate a requirement, that requirement will not be met — an untestable AC is a plan defect, fixed at plan time.

**Drastic changes are welcome — plan the ideal, not the timid.** If the best end-state demands restructuring the repository entirely (a new directory layout, re-layering, moving/renaming/splitting/killing modules, replacing legacy seams wholesale), then plan exactly that. Never shrink a right design into an incremental patch to feel safe; judge by net gains, not diff size — timidity is a plan defect. The current structure has zero inherent authority: it earns its keep or gets redrawn. The only hard constraints: frozen contracts stay frozen once written, disjoint ownership holds, and all gates are green at the end.

The task arrives in `$ARGUMENTS`. If it is empty or vague, ask **one** sharp question, then proceed. There are no flags and no other arguments.

**The deliverable is plan files committed onto a fresh `plan-integration` branch.** Not implementation, and not launching agents. Step 0 resolves the base branch; Steps 1–4 write the plan; Step 5 commits it onto a fresh `plan-integration`. Write, commit, stop, summarize. Spawn agents only if the user asks for that in the same breath.

## Model & effort (mandatory)

Run on **Opus 4.8** (`claude-opus-4-8`) at **`xhigh`** effort. Plans prescribe the following tiering (execute-plan-opus enforces it):
- **LEADS (feature-leads, sub-leads) via Agent tool, BACKGROUND:** `model: "opus"`, `run_in_background: true`, the whole wave as one parallel batch, collected via completion notifications. The Agent tool is required for leads because failed-feature re-drives use `SendMessage`, which reaches only Agent-tool agents — never Workflow `agent()` calls. Effort is inherited from the session, so run the session at `xhigh`.
- **Fire-once worker fan-outs via Workflow (PRIMARY):** `model: "opus"` and `effort: "xhigh"` on every `agent()` call, for any fan-out of 3 or more (task agents, reviewers) — Workflow runs as a background task by nature, which is exactly what we want. For 1–2 agents, use a background Agent batch instead. Workflow nests only ONE level, and **sub-leads are always spawned via the Agent tool, never inside a Workflow** — they must fan out themselves and stay SendMessage-reachable.
- **Everything runs in the background** — no foreground blocking; orchestrators act between completion notifications.
- **Propagate:** feature-leads (and sub-leads at every deeper level) spawn their agents and workflows with the same `opus` + `xhigh`. State this verbatim in every launch prompt.

## Execution model this plan targets — N tiers (three by default)

```
top orchestrator  (main thread)         ── drives FEATURE waves, one git worktree per feature
   └─ feature-lead agent  (per feature) ── reads feature.md, SPAWNS one sub-agent per task
                                            (or authors a Workflow), integrates results in worktree
         └─ task agent  (per task)      ── reads ONE task file, implements + tests it
               └─ (recurse as needed)   ── oversized task = GROUP folder w/ group.md → own SUB-LEAD
                                            spawning sub-task agents; same rules every level down
```

Decompose at **two levels minimum, deeper when warranted**:
- **Feature** — the big plan split into features. One feature = one worktree = one feature-lead. Features code against the **cross-feature contracts** (orchestrator.md, ids C*).
- **Task** — each feature split into granular tasks. One task = one sub-agent. Tasks code against the **intra-feature contracts** (feature.md, ids FC*).
- **Group (recursive, any depth)** — when a task is still too big for one focused agent session, make it a GROUP folder: a `group.md` (same shape as feature.md — intra-group contracts with ids `GC<node-path>.k`, e.g. `GC02.04.1`, a sub-task DAG, an execution mode, and launch prompts) plus sub-task files. Its sub-lead orchestrates exactly like a feature-lead. Groups may nest further; each level repeats the same machinery (frozen contracts at the boundary, a DAG, disjoint ownership, a test node last).

Granularity rules: **plan granularly, down to leaf tasks.** A leaf task is something one agent finishes in one focused session. A feature is never a single blob. Add a level ONLY when a node stays too big for one session or has more than roughly 8 heterogeneous children — spawn as many agents as the work genuinely needs, but never decompose for its own sake. A genuinely single-unit feature is one feature with one task.

## What you produce

```
plan/
  orchestrator.md              # TOP: cross-feature contracts, feature DAG, per-feature worktree,
                               #   feature-lead launch prompts, merge order
  01-<feature>/
    feature.md                 # LEAD brief: intra-feature contracts, task DAG, task ownership,
                               #   task launch prompts / workflow shape, feature gate + DoD
    task-01-<slug>.md          # one task — painstaking detail, one task sub-agent
    task-02-<slug>.md
  02-<feature>/
    feature.md
    task-01-<slug>.md
    task-02-<slug>/            # oversized task → GROUP folder, own sub-lead
      group.md                 #   same shape as feature.md: GC* contracts, sub-task DAG, prompts
      task-01-<slug>.md
      task-02-<slug>.md        #   may nest further if still too big
  ZZ-tests/                    # ALWAYS-last feature: cross-feature integration + e2e/GUI + coverage
    feature.md
    task-01-<slug>.md
```

One feature folder = one worktree = one feature-lead. One leaf task file = one task sub-agent. One group folder = one sub-lead. Number folders and tasks in dependency order. Keep slugs short (`01-auth/task-01-db-schema`).

## Output style

Write orchestrator.md, every feature.md, and all task files in clear, precise technical prose — complete sentences, unambiguous instructions. Preserve EXACTLY: code and pseudocode, frozen contracts, inline `code`, `path:line` references, commands, type definitions, tables, headings, and the ORDER of numbered steps. A zero-context agent must be able to follow every step without guessing.

## Step 0 — Resolve base (fail fast)

The plan commits onto a fresh `plan-integration` branch (Step 5).

1. Set `$base = git branch --show-current`. If it is empty (detached HEAD), stop. If `$base` equals `plan-integration`, stop and tell the user to check out the real base branch first.
2. An existing `plan-integration` branch is the previous plan cycle — Step 5 drops it with a safe `git branch -d` (which refuses and stops if the branch is actually unmerged) and recreates it fresh.
3. **A pre-existing `plan/` folder on `$base` is stale.** If a `plan/` folder already exists here (tracked or untracked), stop and report — it is the residue of an interrupted run, a cycle merged without `/review-implementation-opus`'s SHIP retire, or a hand-made plan. The user must move, delete, or retire it first; a fresh plan must never mix with stale plan files.

## Step 1 — Ground in the real codebase (never plan blind)

-1. **Memory (token-savior).** Load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<feature/repo> dead end")`, `memory_search("<feature> prior plan decision")`. Recalled dead ends become plan Constraints ("do not reattempt X: <root cause>"); recalled contracts/decisions get re-verified against the code before reuse. Tools absent → skip silently, never block.
0. **Reuse `summary/` if it exists** (the deliverable of `/codebase-summary-opus`). **Check freshness first:** overview.md carries a `Generated: commit <hash>` stamp — run `git diff --stat <hash>..HEAD`; if a domain shows heavy churn, re-verify that domain against the code and note the drift. Read the summary first and treat it as the primary grounding for architecture, domains, contracts, conventions, gotchas, and the test surface. Its **domain map is the starting point for FEATURE decomposition** (Step 2). Only then hit the code, to (a) confirm the summary is accurate for the files you will touch and (b) fill gaps. Where the summary is stale or contradicts the code, trust the code and note the drift. With no `summary/`, do the full investigation below.
1. **Learn the project.** Read `CLAUDE.md`/`AGENTS.md`, the `README`, and the manifest. Note the build/test/lint/format commands and the **git policy** (worktree-only? local merges allowed? — this decides the Step 3.5 sub-worktree mode).
2. **Find the code.** Prefer the MCP recall/graph tools (`search_codebase`, `find_symbol`, `god_nodes`, `query_graph`) over Grep. Locate the exact files, modules, types, and call sites.
3. **Extract the conventions to obey.** Indentation, braces, imports, naming, type strictness, file layout, path aliases, error idiom, test framework and location. The plan must tell agents to **match repo style** — never impose an outside style.
4. **Map the test and UI surface.** How do unit tests run? Is there an integration/DB harness? An E2E/GUI runner? Record the exact invocations.
5. **Inventory subagents.** Check `.claude/agents/` and `~/.claude/agents/`. Read each frontmatter (`name`/`description`/`tools`) for its specialty and whether it can edit (`Edit`/`Write`) or is read-only. These `subagent_type`s are what execute-plan-opus and the leads launch (Step 2.5). Flag read-only reviewers for the review gate. If none exist, use generic personas.
6. **Bind to discovered capabilities only.** The summary's "Available tooling" list (MCP servers, CLI tools, runners) is what tasks may use — the plan never invents a tool. A genuinely needed missing tool becomes an explicit setup task, never an assumption.

Carry concrete facts forward: real `path:line` references, real names, real commands — never "the relevant file".

## Step 1.5 — Extract requirements (R\*) with testable acceptance criteria

Before decomposing, turn the ask into the spec the whole chain validates against. If `NextThingsToDo.md` blocks (the `/todo`//`/sketch-opus` deliverable) carry `R*`/AC lists already, lift them verbatim; otherwise derive them from `$ARGUMENTS` and the summary:
- **R-numbered requirements** — one sentence each, WHAT not HOW, implementation-agnostic.
- **Acceptance criteria per requirement** (`AC<R>.<n>`) — observable, deterministic, automatable: `Given <precondition>, when <action>, then <observable result>`, or `<metric> meets <threshold> under <conditions>`. Every AC must answer "how would an automated test verify this?" — rewrite any that cannot.
- **YAGNI ruthlessly:** strip requirements the user did not ask for. Boldness is orthogonal — an ideal-end-state restructure that serves the requirements is in scope; speculative features are not.
- Each AC will be mapped to its **validation gate** (Gate 1 build · 2 unit · 3 integration · 4 perf · 5 smoke/launch · 6 GUI/human) and to the task(s) implementing it — that mapping is the Coverage matrix in orchestrator.md, and **AC-level coverage is the bar; requirement-level coverage is not sufficient** (one task "covers R1" means nothing if R1 has 6 ACs and the task addresses 2).

## Step 2 — Decompose at N levels for *true* parallelism

Work top-down: features first, then tasks, then groups where tasks stay too big. The same rules apply at every level. Bad decomposition means collisions and merge hell.

### 2A — Carve into FEATURES
0. **Question the existing structure first.** If the current layout or layering fights the goal, plan the restructure as its OWN foundation feature (usually wave A: moves, renames, re-layering, new seams — mechanical and verifiable), and let later features build on the NEW structure. Do not contort features around bad seams the plan could simply delete. **Path labeling:** the restructure feature carries an explicit old→new **move-map**; every later feature citing a post-restructure path marks it `(new)` — reviewers verify `(new)` paths against the move-map and unmarked paths against disk.
1. **Freeze cross-feature contracts.** Anything two features share — types/interfaces, API shapes, DB schema/migrations, event payloads, signatures, error enums — is decided once and written verbatim into `orchestrator.md`. No redesign later.
2. **Model the feature DAG.** Separate what is sequential (schema before API) from what is independent. Group independent features into waves. Maximize parallel width without write conflicts.
3. **One worktree, one feature, one lead.** Each feature must be completable, testable, and mergeable on its own branch with no sibling chatter — coordination happens only via contracts and the orchestrator.
4. **Disjoint feature ownership.** Two features never own the same paths. Otherwise re-cut the boundary or sequence them.

### 2B — Carve each feature into TASKS
1. **Freeze intra-feature contracts (FC*), NAMESPACED.** The boundaries between this feature's tasks — internal signatures, shared helpers, the agreed file layout, internal shapes — go verbatim into `feature.md`. Ids carry the feature number: `FC02.1`, `FC02.2` — never a bare `FC1` (two features each minting an FC1 makes the contract stack ambiguous). Group contracts follow the same rule with the full node path: `GC02.04.1`.
2. **Model the task DAG.** Order what must be ordered (types before their users) and group independent tasks into intra-feature waves the lead runs concurrently.
3. **Disjoint task ownership in the feature worktree.** Task agents share ONE worktree (the feature's), so parallel tasks must **own disjoint paths**. Record each task's globs.
   - **Unavoidable collision** → the lead runs the colliding tasks in **sub-worktrees** forked off the feature branch (`isolation:'worktree'` or `git worktree add`) and merges them back — only if the git policy permits local merges. Otherwise prefer disjoint paths or **sequence** the tasks. State the mode per feature.
4. **Per-feature test task.** The last task of every feature (`task-NN-tests.md`) depends on the implementation tasks; it covers intra-feature integration, feature-level GUI/e2e, and coverage. Each task's own Testing section still covers that task in isolation.
4b. **Score complexity per task** — five axes, 0–4 each (files touched · type chore→architectural · judgment mechanical→critical · cross-component · novelty known→unknown), summed: 0–6 **quick**, 7–13 **standard**, 14+ **thorough**. Upgrade one step if ANY of: auth/crypto/secrets/PII, irreversible migration, breaking public API, hot-path perf. Downgrade only if ALL of: no new deps, existing test coverage, no user-visible change, single file+function. Depth drives execution rigor (execute-plan-opus enforces): quick = Gates 1–2 + 1 re-drive · standard = Gates 1–3 + 2 re-drives · thorough = full ladder incl. GUI/e2e + 2 re-drives + mandatory reviewer pass. Models/effort are NOT downgraded by depth.
5. **Recurse oversized tasks into GROUPS.** A task that fails the one-focused-session bar becomes a GROUP folder: a `group.md` (feature.md shape — intra-group GC* contracts, sub-task DAG, execution mode, sub-task launch prompts, group gate) plus sub-task files. Apply rules 2B.1–2B.4 inside the group (test sub-task last). Nest deeper only while the bar still fails. The group's sub-lead is spawned by the feature-lead exactly like a task agent, but it orchestrates instead of coding.

### 2C — Final cross-feature test FEATURE
The last wave is a dedicated `ZZ-tests/` feature that depends on every implementation feature. It covers what only exists once **features** integrate: cross-feature integration, e2e/GUI across features, coverage fill, and a full-suite green run against the contracts. Never skip it (with a single implementation feature, it is simply wave B). Its tasks may parallelize (one per flow). Assign `<test/QA subagent or generic>` agents.

If the work cannot be parallelized at the feature level, say so and emit **sequential feature phases** (same format, order enforced). Tasks inside a feature may still parallelize. The final test-feature rule still holds.

## Step 2.5 — Assign agents at both levels

Match agents on their `description`, not their name.
- **Feature-lead** (one per feature) — must be able to **spawn sub-agents and author workflows**. Default is `general-purpose`. Name a project agent only if it both fits the work AND can edit and delegate. Never a read-only agent.
- **Task agent** (one per task) — match the work and stack to a project executor (with `Edit`/`Write`); name it and shrink the persona to a one-line pointer. With no fit, use the generic persona (Step 4). Never force a misfit.
- **Read-only agents** are NOT executors. Use them as a **review gate** (Step 3) or via `/review-plan-opus`.

Record the chosen `subagent_type` (or "generic") per lead and per task.

## Step 3 — Write `plan/orchestrator.md` (TOP)

The single source of truth tying the **features** together:

```markdown
# Orchestrator — <feature set name>

## Goal
2–4 sentences: what and why, with the user-facing outcome.

## Requirements & acceptance criteria  ← the spec everything downstream validates against · ids R1, R2…
- **R1 — <name>**: one-sentence WHAT.
  - AC1.1: testable criterion (Given/when/then or metric-threshold). → Gate <1-6>
  - AC1.2: … → Gate <n>
- **R2 — …**

## Out of scope   ← review-plan-opus checks uncovered summary risks against this list
Summary risks, domains, or debt items consciously NOT addressed — one line each with why. (State
"nothing scoped out" when empty.) Explicit exclusions prevent scope creep: work no R\* requires is
over-build, and reviewers flag it.

## Context & constraints
Stack, entry points (real paths), conventions to match, build/test/lint commands,
git policy (do leads merge task sub-branches locally?), and things that must NOT change.

## Cross-feature frozen contracts  ← features code against these · ids C1, C2…
- Types/interfaces: exact code.
- API: routes, methods, request/response shapes, status codes.
- DB schema/migrations: tables, columns, indexes, constraints.
- Events/messages: names and payloads.
- Shared signatures: the exact module boundaries between features.

## Features
| # | Folder | Summary | Implements | Owns (paths) | Depends on | Wave | Lead agent | #tasks |
|---|--------|---------|------------|--------------|------------|------|-----------|--------|
| 1 | 01-auth/  | … | R1, R3 | src/auth/**, migrations/** | — | A | general-purpose | 4 |
| 2 | 02-api/   | … | R2 | src/api/**          | 1 | B | <type/generic> | 3 |
| Z | ZZ-tests/ | cross-feature integration + e2e/GUI + coverage | all ACs | test dirs | 1,2 | C (last) | <test/generic> | 3 |

The last row is ALWAYS the cross-feature test feature (2C).

## Coverage matrix  ← every AC lands somewhere; a GAP row is a plan defect — fix before committing
| R | AC | Implemented by (feature/task) | Proved by (test/gate) | Status |
|---|----|-------------------------------|----------------------|--------|
| R1 | AC1.1 | 01-auth/task-02 | test file + Gate 2 | COVERED |
Every acceptance criterion gets a row; Status is COVERED or GAP. execute-plan-opus pre-flights this
matrix and refuses to run with GAP rows; review-implementation-opus walks it goal-backward at audit time.

## Feature dependency graph
Plain-text or mermaid DAG showing feature order and concurrency.

## Worktree setup
One branch per FEATURE, forked off `plan-integration`:
    git worktree add ../wt-01-auth -b feat/01-auth plan-integration
    git worktree add ../wt-02-api  -b feat/02-api  plan-integration
(Task sub-worktrees are made BY the lead off its feature branch — not here.)

## Feature-lead launch prompts  ← paste-ready, one per feature
Each prompt states: the feature worktree path and branch (operate only inside it); what to read —
summary/overview.md, this orchestrator (cross-feature contracts pasted in), and
plan/NN-<feature>/feature.md; the instruction **"You orchestrate this feature's tasks. SPAWN one
sub-agent per task (Agent tool) or author a Workflow, following feature.md's task DAG. Run
independent tasks concurrently, sequence dependent ones. Integrate in this worktree."**; the resource
SUB-POOL the lead sub-leases to its task agents; the feature gate to run before reporting done; what
to return; and **spawn task agents with model "opus" at xhigh effort**.
If a `subagent_type` is assigned, add "launch with subagent_type: <agent>" and a one-line persona.

## Review gates  ← only if Step 1 found a read-only reviewer agent
- **Plan gate** (optional): run the whole plan through it (or `/review-plan-opus`) before executing; fix findings.
- **Per-feature gate**: before merging a feature, run the reviewer on its diff; block until APPROVE.
Omit this section entirely when there is no reviewer agent.

## Shared resources & collision rules
- **Broker pool:** the ports, X display, and test DB the concurrent waves need. Carve per-feature
  SUB-POOLS so a lead can hand each task a distinct slot without colliding tree-wide. List the
  sub-pool per feature.
- **Shared files** (manifests/configs/barrels touched by more than one feature): name an owner and a
  merge sequence. Dependency manifests use the delta-block protocol — each feature and task declares
  its dependencies in a fenced block, and the integrator unions them into ONE edit and one install.

## Integration & merge order
The order in which to merge FEATURE branches, who owns conflicts, and the post-merge smoke check to
run before the next merge. The test feature merges LAST; its green full suite is the final gate.

## Global gate — the validation ladder   ← run after every feature merge and once on the final result
Ordered, each gate pricier than the last; run in order, STOP at the first failure (later results are
meaningless), and after any fix re-run from Gate 1:
- Gate 1 build · Gate 2 unit · Gate 3 integration · Gate 4 perf/bench (only if an AC sets a
  threshold) · Gate 5 smoke/launch (start the app / load the entry point, health-check) · Gate 6
  GUI/human review surface.
One exact copy-pasteable command per gate (lift from summary's gate ladder), plus
lint/format/typecheck. Mark a gate "none" honestly rather than inventing a command.

## Global definition of done
All feature DoDs met, full suite green (unit + integration + GUI), lint/format/typecheck clean, and
the feature set works end to end.
```

## Step 3.5 — Write each `plan/NN-<feature>/feature.md` (lead brief)

This is the orchestrator for ONE feature, read by its lead. It does for tasks what orchestrator.md does for features:

```markdown
# Feature NN — <title>  (lead brief)

## Feature-lead persona
If a `subagent_type` is assigned: "Run as `<agent>`." Otherwise: "You are a lead engineer. You do not
decompose past the tasks below — you orchestrate them: spawn one sub-agent per task or author a
Workflow, integrate the results in this worktree, and verify the feature as a whole. Choose the
simplest correct design and match the repo."

## Mission
1–3 sentences: this feature's user-facing slice, in isolation.

## Owns / off-limits (feature scope)
- Owns (its tasks edit): path globs.
- Do NOT touch: other features' paths; cross-feature contracts.

## Depends on
The cross-feature contracts (C*) consumed; the features that must merge first; what this feature
produces for later ones.

## Move-map (old → new)   ← RESTRUCTURE feature only; omit the section otherwise
Table: old path → new path, one row per moved/renamed/split file or directory. This is the reference
reviewers use to verify `(new)`-marked paths in later features. Exhaustive — every path the
restructure touches.

## Intra-feature frozen contracts  ← tasks code against these · ids FC<NN>.1, FC<NN>.2… (feature-number prefix mandatory)
The boundaries between this feature's tasks: internal signatures, shared helpers, file layout,
internal shapes. Exact code. (May be empty for a tiny feature — say so explicitly.)

## Tasks
| # | File | Summary | Implements | Owns (paths) | Depends on | Task wave | Depth | Task agent |
|---|------|---------|------------|--------------|------------|-----------|-------|-----------|
| 1 | task-01-<slug>.md | … | R1: AC1.1–1.3 | <disjoint globs> | — | a | standard | <type/generic> |
| 2 | task-02-<slug>.md | … | R1: AC1.4 | <disjoint globs> | 1 | b | quick | <type/generic> |
| N | task-NN-tests.md  | intra-feature integration + feature GUI/e2e + coverage | feature ACs | test dirs | impl | last | standard | <test/generic> |

Parallel tasks (same wave) own disjoint paths. The last row is the per-feature test task (2B.4).
For a group row: File = the `task-NN-<slug>/` folder, Task agent = sub-lead; its group.md carries the sub-DAG.

## Task dependency graph
Plain-text or mermaid sub-DAG showing task order and concurrency.

## Execution mode  ← how the lead runs tasks. State exactly ONE:
- **disjoint-parallel** (default): spawn parallel task agents in THIS worktree; disjoint paths mean no
  collision. Sequence dependent tasks after their predecessors.
- **sub-worktree** (only if parallel tasks share files AND the git policy allows merges): the lead
  makes a task sub-worktree off the feature branch per parallel task (`git worktree add
  ../wt-NN-taskMM -b task/NN-MM <feature-branch>` or Workflow `isolation:'worktree'`) and merges
  them back in DAG order. (The `task/` prefix avoids the git ref namespace conflict a name nested
  under the existing feature branch would cause.)
- **sequential**: tasks run one after another in this worktree (serial work, or merges forbidden
  while paths collide).

## Task-agent launch prompts (or workflow shape)  ← one per task
Each prompt gives: the worktree path (the feature's, or the task sub-worktree just created), the task
file to follow, the intra-feature contracts (FC*) and cross-feature contracts (C*) to honor, the
sub-leased resource slot, the DoD, and **opus + xhigh**.
If using a Workflow instead, give its shape: which tasks are stages versus parallel batches, where
isolation applies, and what each returns.

## Feature gate
The exact commands (build + unit + integration + feature GUI/e2e) to run before reporting the branch green.

## Feature definition of done
Every task DoD met, intra-feature integration green, the feature gate green, contracts honored, and
the branch ready to merge.
```

## Step 4 — Write each `plan/NN-<feature>/task-MM-<slug>.md` (painstaking detail)

Each task file must be executable by an agent reading ONLY this file plus the two contract sets (C* in orchestrator.md, FC* in feature.md). No hand-waving:

```markdown
# Task NN.MM — <title>

## Agent persona
If a `subagent_type` is assigned, a one-line pointer: "Run as `<agent>`; its system prompt owns the
persona and conventions." Otherwise the generic persona: an experienced engineer who chooses the
simplest correct design, follows repo conventions exactly, and picks the more maintainable option,
justifying it in one line.

## Mission
1–3 sentences: what this task delivers, in isolation.

## Implements   ← the ACs this task exists for; the Verification report walks exactly these
`R<x>: AC<x>.<n>…` — the acceptance criteria (verbatim from orchestrator.md) this task makes true,
each with its gate. Complexity depth: `quick | standard | thorough` (score + one-line axis note).

## Owns / off-limits
- Owns (create/edit): explicit globs (disjoint from sibling tasks in the same wave).
- Do NOT touch: other tasks' and features' paths; the frozen contracts (C*, FC*).

## Depends on
The contracts consumed (C*, FC*); the tasks that must finish first; what this task produces for later ones.

## Implementation — step by step
Numbered, concrete steps. Every non-trivial unit gets **core code or detailed pseudocode** — real
signatures, data structures, the algorithm, error handling, edge cases. Real files and line ranges.
The agent should be typing it in, not inventing it.

## Maintainability requirements
Single responsibility; no duplication (point to the existing helper); intent-revealing names matching
the repo; no dead code, commented-out blocks, or TODOs; small functions; isolated side effects;
explicit error paths.
**Guardrails (enforced at review):** the correct amount of code is the minimum that meets the ACs —
no speculative features, no abstraction "in case", no new dependency when an existing one fits;
every diff line traces to an AC or a contract; no "while I'm in here" edits — a real adjacent bug
gets one line in your report as a backlog candidate, never a fix inside this task's diff. A
load-bearing unverified assumption is flagged, not guessed through.

## UX requirements  (whenever user-facing)
Loading/empty/error/success states; accessibility (semantics, keyboard, focus, labels, contrast);
responsive with no layout shift; clear feedback for every action; optimistic versus pending behavior stated.

## Testing  (extensive — not optional)
- **Unit:** functions and branches, including edge and failure cases; name the test files and the
  exact run command.
- **Integration:** cross-module/DB/API/socket behavior against the contracts, on the real harness;
  the command plus fixtures/seed data.
- **GUI/E2E:** (for user-facing work) the flows on the repo's runner — happy path plus at least one
  error path plus a visual check; the command.
- **Acceptance:** the mapped ACs verbatim — each names the test/check that proves it.

## Definition of done
Code complete; the relevant test layers green (gates in ladder order for this task's depth);
lint/format/typecheck clean; conventions matched; contracts honored; and a **Verification report**
returned — one line per mapped AC: `AC<x>.<n> · <check run> · <observed result>`. A task is NEVER
done because existing code "looks related": each AC is individually verified with code written or
tests run for it.
```

Scale depth to the work: a tiny task gets a short file, but consider every section (mark it N/A only when truly inapplicable, e.g. GUI for a pure migration). Never drop Testing. If a task outgrows one focused session while you are writing it, convert it to a GROUP folder (2B.5) instead of bloating the file.

## Step 5 — Commit the plan onto a fresh `plan-integration`

**`plan-integration` is a NORMAL branch in the main working tree, NOT a worktree.** Use `git checkout -b` in place. No `git worktree add` and no EnterWorktree for it. Worktrees come later (the per-feature `feat/NN-*` branches plus lead-made task sub-worktrees), only at `/execute-plan-opus` time. This skill stays in the current checkout throughout.

1. **Re-resolve the base** — the current branch (`$base` from Step 0). Confirm you are still on it.
2. **Drop the stale branch:** by default `git branch -d plan-integration` (the previous cycle is assumed integrated). If it refuses because the branch is unmerged, **stop and report** — the tree changed since the last cycle; do not force-drop. Only if the user says `force`, use `git branch -D plan-integration`. Skip this step if the branch never existed.
3. **Create and switch:** `git checkout -b plan-integration "$base"`. The untracked `plan/` folder carries over.
4. **Commit the plan and the summary:** `git add plan/`; if `summary/` exists with untracked OR modified files, `git add summary/` as well (feature worktrees fork from this branch, and untracked files DO NOT propagate into worktrees — leads must find summary/ committed; a `/codebase-summary-opus` re-run after a merged previous cycle leaves summary/ tracked-but-modified — stage that too, or the worktrees fork stale docs and the dirty tree trips execute-plan-opus's pre-flight). Then `git commit -m "plan: <feature set> parallel feature/task workstreams"`. Stage `plan/` (plus `summary/`) ONLY — never sweep unrelated changes into the commit.
5. **Stay on `plan-integration`.**

Stop and summarize: what the plan covers, the requirement/AC counts and the Coverage-matrix result (`<n>/<n> ACs covered` — it must be 100%), the feature count and waves, the total number of tasks, that it is committed on `plan-integration`, and the next actions — `/review-plan-opus` to gap-check, `/fix-plan-opus` to patch findings, `/execute-plan-opus` to run it, `/review-implementation-opus` to audit the built code, `/fix-implementation-opus` to patch audit findings. State the frozen contracts and key decisions as durable facts — save them via `mcp__token-savior__memory_save`.
