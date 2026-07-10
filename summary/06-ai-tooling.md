# AI-assisted development tooling - analysis

## Purpose

This domain is the repository's vendored Claude Code skill toolkit: a set of slash-command "skills" (prompt programs) under `.claude/skills/` that drive spec-driven, agent-orchestrated software development on top of this C++/Qt6 template. It solves the problem of turning a rough idea into shipped, verified code without losing rigor - by forcing every requirement to become an R-numbered, testable acceptance criterion, decomposing large work into disjoint git-worktree feature/task plans that a fleet of background agents execute in parallel, and gating each step against a validation ladder. Nothing here compiles into the product; the toolkit is an optional accelerator layered beside the build system, plus the small amount of repo configuration (`.claude/settings.local.json`, the AI sections of `CLAUDE.md`/`README.md`, and one `.gitignore` negation) that makes it work. This very repository was modernized by running the chain end to end (git history: `1414adc` planned it, `54f3db7` closed it with "all 6 features merged, 35/35 ACs verified").

## Owned paths   <- downstream feature-ownership; keep disjoint

Solely owned by this domain (safe to treat as disjoint):

- `.claude/skills/**` - the 23 vendored skill folders, each a `SKILL.md` (graphify additionally ships a `references/**` subtree). See the drift note below: git HEAD tracks 23 skill dirs, the working tree currently has 22 (graphify deleted, uncommitted).
- `.claude/settings.local.json` - the tracked permission allowlist.

Shared with other domains (flagged - do NOT claim these wholesale):

- `CLAUDE.md` - SHARED. This domain owns only the "AI-Assisted Development" section (`CLAUDE.md:82-95`). The "Build System" and "Architecture" sections (`CLAUDE.md:1-80`) belong to the build/deps and app domains.
- `README.md` - SHARED. This domain owns only the "AI-assisted development" section (`README.md:125-189`). Install, build, features, troubleshooting, license belong to other domains.
- `.gitignore` - SHARED. This domain owns only the settings-tracking negation (`.gitignore:372-373`); the `docs/`, `actionlint`, and `build-*/` entries belong to the docs/CI/build domains.

Generated artifacts (produced BY these skills, not source owned here; treat like build output): `plan/**`, `summary/**`, `SPEC.md`, `NextThingsToDo.md`, `graphify-out/**`. `.claude/scheduled_tasks.lock` is a runtime lock excluded via `.git/info/exclude`, not tracked.

## Key files & symbols

| File | Central content | One line |
|------|-----------------|----------|
| `.claude/skills/parallel-plan/SKILL.md` | 5-step planner prompt; `plan/` folder shape; C*/FC*/GC*/R*/AC* id scheme | Decomposes a feature set into an N-level worktree-ready plan committed on `plan-integration`. |
| `.claude/skills/execute-plan/SKILL.md` | 4-step orchestrator prompt; lead launch-prompt template; run-log/changes ledgers | Drives the N-tier agent hierarchy that builds the plan, one worktree per feature. |
| `.claude/skills/codebase-summary/SKILL.md` | Domain-carve + specialist fan-out; Domain report template; `overview.md` template | Produces the `summary/` map that grounds the whole chain (this file is one of its outputs). |
| `.claude/skills/ship/SKILL.md` | grill -> spec -> research -> review -> build -> check loop; `SPEC.md` section grammar | Standalone single-thread spec-driven loop over one `SPEC.md`; not part of the parallel chain. |
| `.claude/skills/review-plan/SKILL.md` | Read-only per-feature reviewer fan-out; verdict SHIP/REVISE/BLOCK | Gap-checks `plan/` against `summary/`, writes `plan/review.md`. |
| `.claude/skills/fix-plan/SKILL.md` | Applies `plan/review.md` findings to plan files only | Patches the plan; never touches source. |
| `.claude/skills/review-implementation/SKILL.md` | Conformance + AC gap + test-sufficiency audit; SHIP retires `plan/` | Audits built code against the plan, writes `plan/impl-review.md`. |
| `.claude/skills/fix-implementation/SKILL.md` | Applies `plan/impl-review.md` to source+tests, refreshes `summary/` | Patches the code; never touches plan specs. |
| `.claude/skills/sketch/SKILL.md` / `todo/SKILL.md` | R-numbered requirement capture into `NextThingsToDo.md` | Capture step: fuzzy idea (`/sketch`) or scoped task (`/todo`) into planner-ready specs. |
| `.claude/skills/revise/SKILL.md` | One-failure-at-a-time backprop protocol | Traces a bug to the requirement/AC that should have caught it, outside a plan cycle. |
| `.claude/skills/handoff/SKILL.md` | Session recap template; `allowed-tools` restricted to read-only | Prints a resumable session summary to console; writes no file. |
| `.claude/settings.local.json` | `permissions.allow[]` array of `Bash(...)` globs | Force-tracked build/test/docs permission allowlist shared across the team. |
| `CLAUDE.md:82-95` | "AI-Assisted Development" section | Human-facing map of the chain and the optional MCP companions. |
| `README.md:125-189` | "AI-assisted development" section | Public README description of the toolkit, the `-opus` note, and companion installs. |

## Architecture & responsibilities

The toolkit is a flat directory of self-contained prompt programs; there is no shared code or library. Each skill is a single `SKILL.md` whose YAML frontmatter registers it as a slash command and whose body is the instruction set the model executes. Responsibility is split along a linear pipeline (the "parallel chain") plus one standalone loop and two helpers.

```
  CAPTURE            PLAN                         BUILD              AUDIT
  -------            ----                         -----              -----
  /sketch  \                      /review-plan                /review-implementation
           }-> NextThingsToDo -> /parallel-plan  ->  /execute-plan  ->                  }-> ships
  /todo    /                      /fix-plan                     /fix-implementation
                                  (writes plan/)   (writes code + (audits code,
   /codebase-summary -> summary/  <-- grounds -->   changes.md)    SHIP retires plan/)

  standalone:  /ship  (grill->spec->research->review->build->check over one SPEC.md)
  helpers:     /handoff (session recap)   /revise (backprop a bug into the spec)
  companion:   /graphify (build graphify-out/ knowledge graph)  [tracked, deleted in worktree]
```

Layering by artifact ownership - each verb owns a disjoint slice of state, which is the core design invariant of the whole toolkit:

- `/codebase-summary` writes `summary/**` (read-only on source).
- `/sketch`, `/todo` write `NextThingsToDo.md` (the requirement backlog).
- `/parallel-plan` writes `plan/**` on a fresh `plan-integration` branch (read-only on source).
- `/review-plan` writes `plan/review.md` only (read-only on the rest of the plan and on source).
- `/fix-plan` edits `plan/**` only (never source, never `summary/`).
- `/execute-plan` writes source + tests in per-feature worktrees, plus the ledgers `plan/run-log.md`, `plan/changes.md`, `plan/dead-ends.md`, `plan/backprop-log.md`; refreshes `summary/` at the end.
- `/review-implementation` writes `plan/impl-review.md`; on a SHIP verdict it `git rm`s `plan/` (the chain's final act).
- `/fix-implementation` edits source + tests, appends to `plan/changes.md`, refreshes `summary/`; never edits plan specs.

The second architectural axis is the `-opus` doubling. Every workflow skill exists twice: a base variant pinned to `model: claude-fable-5` and an `-opus` variant pinned to `model: claude-opus-4-8`. The two files are byte-identical except for (1) the `name:` field, (2) the `model:` field, (3) the H1 title, and (4) every in-body reference to the model or a sibling skill (for example `execute-plan` -> `execute-plan-opus`, `` `model: "fable"` `` -> `` `model: "opus"` ``). The chain is otherwise the same; the `-opus` set just runs it on the stronger model. `handoff` and `todo` have no `-opus` twin.

## Data structures & models

### SKILL.md frontmatter schema

Each skill begins with a YAML block. Observed fields:

```yaml
name: parallel-plan            # slash-command name (required)
description: <one long line>   # trigger phrases + what it does (required); drives model auto-invocation
user-invocable: true           # present on all 23 skills
disable-model-invocation: true # present on 22 of 23; ABSENT only on handoff
model: claude-fable-5          # base pin; -opus variants use claude-opus-4-8. ABSENT on handoff and todo
allowed-tools:                 # present ONLY on handoff (read-only sandbox)
  - Read
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(ls *)
```

Notable: `handoff` is the only skill with `allowed-tools` (it is deliberately read-only, no file writes) and the only one lacking `disable-model-invocation`. `handoff` and `todo` are the only skills with no `model:` pin (they inherit the session model).

### settings.local.json schema

```json
{ "permissions": { "allow": [ "Bash(<glob>)", ... ] } }
```

The single object tracks a `permissions.allow` array of 10 `Bash(...)` permission globs covering the build/test/docs commands the chain runs headlessly (`cmake --preset:*`, `cmake . -G Ninja -B build:*`, `cmake --build build:*`, `ctest:*`, `cd build && ctest:*`, `conan install conan/:*`, `conan profile detect:*`, `make:*`, `bash scripts/run_doxygen.sh:*`, `QT_QPA_PLATFORM=offscreen ctest:*`). It carries no `deny` list and no hooks.

### plan/ folder shape (parallel-plan output; deleted in the current worktree)

The `/parallel-plan` deliverable, reconstructed from `parallel-plan/SKILL.md:48-67` and confirmed by the deleted paths in git status:

```
plan/
  orchestrator.md            # TOP: R*/AC requirements, cross-feature C* contracts, feature DAG+waves,
                             #   Coverage matrix, worktree setup, lead launch prompts, gate ladder, DoD
  NN-<feature>/
    feature.md               # LEAD brief: intra-feature FC* contracts, task DAG, execution mode,
                             #   task launch prompts, feature gate
    task-MM-<slug>.md        # one leaf task, painstaking detail (Mission/Implements/Owns/Depends/
                             #   Implementation/Testing/DoD with a per-AC Verification report)
    task-MM-<slug>/group.md  # oversized task -> GROUP folder, GC* contracts, own sub-lead (recursive)
  ZZ-tests/                  # ALWAYS-last cross-feature integration/e2e/coverage feature
  run-log.md changes.md dead-ends.md backprop-log.md   # execute-plan ledgers
  review.md impl-review.md   # review-plan / review-implementation outputs
```

The real run that built this repo had features `01-deps-build`, `02-doxygen-style`, `03-makefile`, `04-ci`, `05-ai-docs`, `ZZ-tests`.

Contract-id grammar (frozen once, never redesigned downstream): `R<n>` requirement, `AC<n>.<m>` acceptance criterion, `C<n>` cross-feature contract, `FC<NN>.<k>` intra-feature contract (feature-number-prefixed, e.g. `FC02.1`), `GC<node-path>.<k>` intra-group contract (e.g. `GC02.04.1`). Task complexity depth is `quick | standard | thorough`, scored on five 0-4 axes (`parallel-plan/SKILL.md:121`).

### SPEC.md section grammar (ship)

`/ship` uses a single caveman-encoded `SPEC.md` with fixed-order sections addressable as `§<S>.<n>` (`ship/SKILL.md:26-35`):

```
# SPEC
## §G GOAL        one line
## §C CONSTRAINTS non-negotiables, parked `?` unknowns
## §I INTERFACES  external surface (cmd/api/file/env)
## §R RESEARCH    optional table id|topic|finding|src
## §V INVARIANTS  numbered testable (V1: ...)
## §T TASKS       table id|status|task|cites  (status . todo / ~ wip / x done)
## §B BUGS        table id|date|cause|fix     (backprop log)
```

### summary/ shape (codebase-summary output)

`summary/overview.md` (system index, carries a `Generated: commit <hash>` freshness stamp) plus one `NN-<domain>.md` per domain (this file is the `06-ai-tooling` domain report). Template at `codebase-summary/SKILL.md:100-156`.

## Control & data flow

Primary path - the parallel chain, entry to shipped code:

1. `/codebase-summary` (main thread on Fable 5) carves the repo into domains and dispatches one specialist agent per domain on Opus 4.8 at `xhigh` (Workflow for 3+ domains, background Agent calls for 1-2). Each specialist reads its slice, writes `summary/NN-<domain>.md`; the main thread synthesizes `summary/overview.md` with the `Generated: commit` stamp. (`codebase-summary/SKILL.md:56-160`)
2. `/sketch` (conversation) or `/todo` (direct) turn the ask into R-numbered requirement blocks with testable ACs appended to `NextThingsToDo.md`.
3. `/parallel-plan` Step 0 resolves the base branch and refuses if a stale `plan/` exists; Step 1 grounds in `summary/` (diffing the freshness stamp) and the code; Step 1.5 extracts `R*`/`AC*`; Step 2 carves features (2A), tasks (2B), recursive groups (2B.5), and the always-last `ZZ-tests` feature (2C); Step 2.5 assigns agents; Steps 3-4 write `orchestrator.md`, each `feature.md`, and every task file; Step 5 commits the plan on a fresh `plan-integration` branch. The Coverage matrix must be 100% (every AC mapped to a task and a gate) or it is a plan defect.
4. `/review-plan` dispatches one read-only reviewer per feature, runs global checks (coverage, DAG acyclicity, ownership collisions, contract completeness, stale refs), writes `plan/review.md`, and prints SHIP/REVISE/BLOCK. `/fix-plan` applies those findings to plan files only and re-commits. (History shows this looped: BLOCK -> REVISE -> REVISE with fix commits `df2575a`, `185310f`, `3c53e14`.)
5. `/execute-plan` (main thread = top integrator) parses `plan/`, pre-flights the Coverage matrix (refuses on a GAP row), initializes the ledgers, then loops feature waves: for each wave it lazily creates one git worktree+branch per feature off `plan-integration`, leases resource sub-pools, dispatches the whole wave as one background batch of FEATURE-LEAD agents (Agent tool, `run_in_background: true`), and collects via completion notifications. Each lead reads its `feature.md`, spawns one task sub-agent per leaf task (Workflow for 3+, Agent batch for 1-2, a recursing SUB-LEAD per group folder), passes down the C*/FC*/GC* contract stack, runs the validation ladder per task, and runs the feature gate before reporting green. The integrator records CHANGES to `plan/changes.md`, spot-checks ledger honesty against `git diff --stat`, merges gate-green features onto `plan-integration` in order (re-running the gate after each merge, reverting on breakage), prunes merged branches/worktrees, and advances. Step 4 runs the global gate, refreshes `summary/`, finalizes and commits the ledgers.
6. `/review-implementation` audits the executed code goal-backward from the ACs (conformance, AC gap MET/STUB/PARTIAL/NOT_MET/UNVERIFIABLE, test sufficiency) and prints SHIP/FIX/BLOCK; `/fix-implementation` patches source+tests per `plan/impl-review.md`, refreshes `summary/`, re-runs the gate. On SHIP, `/review-implementation` retires `plan/` with `git rm` - which is exactly the deleted-`plan/` state visible in the current worktree.

Standalone path - `/ship` (`ship/SKILL.md:39-73`): right-size first (trivial -> straight to build; multi-domain parallel -> route out to `/parallel-plan`), then GRILL (self-interrogate, park unknowns as `?`) -> SPEC (write `SPEC.md`) -> RESEARCH (only if a decision hinges on external facts) -> REVIEW (adversarial go/no-go, HARDEN findings become new `§V` lines, second NO-GO stops the run) -> BUILD (per `§T` task: plan with a named test per invariant, execute minimally, run the oracle, backprop failures into `§B`+`§V`) -> CHECK (read-only drift report). `cat SPEC.md` is the only dashboard.

## Public API / contracts   <- downstream contract candidates

What this domain exposes and guarantees for other domains and for the human operator:

- **Slash commands** (23 base names + 20 `-opus` twins): `codebase-summary`, `sketch`, `todo`, `parallel-plan`, `review-plan`, `fix-plan`, `execute-plan`, `review-implementation`, `fix-implementation`, `revise`, `ship`, `handoff`, `graphify`, each with an `-opus` variant except `handoff`, `todo`, and `graphify`.
- **Branch contract:** `plan-integration` is both the fork base for feature worktrees and the merge target; the user's base branch is never pushed to and never merged onto (`execute-plan/SKILL.md:47`). Feature branches are `feat/NN-<slug>`; task sub-worktree branches use the mandatory `task/` prefix to avoid a git ref namespace conflict.
- **Artifact contracts** consumed across skills: `summary/overview.md` (+ `NN-*.md`), `NextThingsToDo.md`, `plan/orchestrator.md`, `plan/NN-*/feature.md`, task files, `plan/changes.md` (per-task changed files + NEW-side line ranges, feeds `/review-implementation`), `plan/review.md`, `plan/impl-review.md`, `plan/run-log.md`, `plan/dead-ends.md`, `plan/backprop-log.md`, `SPEC.md`.
- **Id conventions:** `R*`, `AC*.*`, `C*`, `FC<NN>.*`, `GC<path>.*` (frozen contracts), depth `quick|standard|thorough`, verdicts `SHIP|REVISE|BLOCK` (plan) and `SHIP|FIX|BLOCK` (impl).
- **Validation gate ladder** (six gates, run in order, stop at first failure, re-run from Gate 1 after any fix): 1 build, 2 unit, 3 integration, 4 perf (only if an AC sets a threshold), 5 smoke/launch, 6 GUI/human. This is the contract `/codebase-summary` emits and `/execute-plan` lifts verbatim.
- **Permission contract:** `.claude/settings.local.json` guarantees the harness may run the listed build/test/docs Bash commands without prompting. Other domains that add a new build/test entrypoint should expect to add a matching `Bash(...)` glob here.
- **Model ids:** `claude-fable-5` (base) and `claude-opus-4-8` (`-opus`); agents fan out with `model: "fable"`/`"opus"` at `effort: "xhigh"`.

## Dependencies

Inbound (callers into this domain):

- The human operator, via slash commands typed in Claude Code (each skill is `user-invocable: true`).
- The Claude Code model's auto-invocation, gated off for 22 of 23 skills by `disable-model-invocation: true` (so they only run when explicitly called); `handoff` alone may be model-invoked.
- The Claude Code harness itself reads `.claude/settings.local.json` for the permission allowlist.

Outbound (what the skills depend on):

- **Claude Code agent primitives:** the Agent tool (`run_in_background`, `SendMessage` re-drive) and the Workflow tool (`agent()`, `parallel()`, `pipeline()`, `isolation:'worktree'`, `budget`). The Agent-vs-Workflow choice is load-bearing: leads MUST be Agent-tool agents because `SendMessage` re-drive cannot reach Workflow calls, and Workflow nests only one level.
- **git worktrees** for feature isolation; the skills assume a worktree-capable git and honor the repo git policy from `CLAUDE.md` (no origin push/pull, local merges only where allowed).
- **Models:** Fable 5 and Opus 4.8 at `xhigh` effort.
- **Optional MCP companions** (skills degrade silently if absent): `cavemem` (cross-session memory, loaded via `ToolSearch(select:mcp__cavemem__search,...)`), `token-savior` (symbol-level find/read/edit), `graphify` (knowledge graph at `graphify-out/`). Also `deep-research`/web tools for `/ship`'s research step.
- **The build system domain** for the actual gate commands (`make`, `cmake`, `ctest`, `conan`, `scripts/run_doxygen.sh`) that the plan's gate ladder invokes.

## Invariants & assumptions

- **Disjoint ownership at every tier.** Two features never own the same paths; parallel tasks in one feature own disjoint globs; violated -> merge collisions. This is enforced by `review-plan`'s ownership matrix and pre-flighted by `execute-plan`.
- **Frozen contracts stay frozen.** Once `C*`/`FC*`/`GC*` are written, no downstream agent redesigns them; every task codes against the pasted contract stack.
- **`plan-integration` is the sole fork base and merge target.** The user's base branch is never mutated. Feature worktrees fork from it; merges land back on it.
- **AC-level coverage is the bar.** Every acceptance criterion maps to a task AND a gate; a GAP row is a plan defect that halts `/execute-plan` and routes to `/fix-plan`. Requirement-level coverage alone is insufficient.
- **"Done" means verified, not asserted.** A task is done only when each mapped AC has an individual `AC.n . check . observed` Verification report; a `done` task with a STUB/PARTIAL AC is "falsely complete", the worst finding class.
- **One specialist = one output file.** In `/codebase-summary` and the review fan-outs, each agent writes exactly one file, so there are no write collisions (why this report is written by exactly one agent).
- **Sectioned ownership of state.** Each verb writes only its own artifact slice (see Architecture); no step rewrites a section it does not own. `/fix-plan` never touches source; `/fix-implementation` never touches plan specs.
- **A stale `plan/` blocks a fresh plan.** `/parallel-plan` Step 0 refuses to run if a `plan/` folder already exists on the base.

## Error handling & edge cases

- **Circuit breakers, not grinding.** Three consecutive validation failures on a task -> `blocked` + a `plan/dead-ends.md` entry. The same failure signature twice is a "ceiling": stop re-driving and diagnose the blocker instead of adding retries. Retry caps are depth-scaled (quick 1, standard/thorough 2).
- **Spec defects are backpropagated, never coded around.** A task file or contract that contradicts reality is returned classified (`missing criterion | incomplete criterion | wrong criterion | missing requirement`) and routed to `/fix-plan`; `execute-plan` logs it to `plan/backprop-log.md` with a `pattern_category`. Three-plus entries sharing a category flag a systemic cross-cutting amendment.
- **Regression = P0.** A previously-green gate going red halts forward work on that branch until fixed.
- **Red features do not integrate.** A failed feature blocks only its dependents; independent siblings in the wave continue; the run halts entirely only when nothing unblocked remains.
- **Dead ends are recorded once and never reattempted**, seeded from cavemem recall and written to `plan/dead-ends.md` (`DE-N . approach . root cause . verdict`).
- **`/ship` go/no-go gate:** a second NO-GO stops the run with the verdict printed rather than building a confident wrong artifact.
- **Idempotent resume:** `/execute-plan` reads `plan/run-log.md`, skips `merged`/`pruned`/`gate-green` work, and pastes prior task-ledger lines into a re-spawned lead (the lead cannot read the main-tree run log itself).
- **Missing tooling degrades gracefully:** absent cavemem/token-savior/graphify -> skip silently, never block.

## Concurrency / async / lifecycle

Concurrency is the whole point of the parallel chain, and it is managed by static leasing plus file locks because no live broker exists mid-wave (leads run in the background and cannot ask the integrator anything).

- **Worktree isolation per feature.** One feature = one worktree = one lead; one leaf task = one task agent in the feature worktree (disjoint paths) or a sub-worktree forked off the feature branch.
- **Background batches.** A whole feature wave is dispatched as one background batch of Agent calls; the integrator acts between completion notifications and triages early failures while siblings still run.
- **Resource sub-pools, leased hierarchically.** The top integrator leases each feature a port range (feature 1 -> 7100-7109, feature 2 -> 7110-7119), a display slot, and a test DB; each lead sub-leases distinct slots to its task agents. No node self-assigns a shared singleton.
- **Host-wide singletons self-serialize via `flock`.** The display, host-wide ports, and shared test DBs are wrapped `flock /tmp/pvn-<resource>.lock -c '<cmd>'`, one lock file per singleton, names fixed in the pre-flight schedule. (Note the `pvn-` lock-name prefix - see Gotchas.)
- **Workflow nests only one level;** sub-leads for group folders are therefore always spawned via the Agent tool (never inside a Workflow) so they can fan out themselves and stay `SendMessage`-reachable.
- **Merge lifecycle:** create worktree lazily at wave start -> gate-green -> merge onto `plan-integration` -> re-run gate -> prune worktree (safe `git worktree remove`, no `--force`) then branch (`git branch -d`, never `-D`). Deferred-merge dependents fork off their predecessor's branch instead of waiting.
- **Budget-aware:** if a Workflow `budget` is set, the run stops cleanly at a wave boundary rather than mid-wave.

## Performance

Not a runtime-performance domain (these are prompt documents, not compiled code). The performance concerns are token/context economy and wall-clock throughput of the agent fleet:

- **Caveman compression.** Agent return prose is compressed (drop articles/filler, fragments fine) while code, paths, commands, branch names, and all structured blocks (ledgers, CHANGES, Verification reports, gate results) stay exact. This shrinks the tool-result injected back into the orchestrator's context.
- **Ledgers stay terse** (one structured line each, no timestamps, no prose narration) so the run log and changes ledger do not balloon the main-thread context.
- **Parallel width** is maximized by the feature/task DAG waves, bounded by disjoint ownership and the shared-resource sub-pools.
- **`summary/` is refreshed incrementally** (only the domains whose subject materially changed), not rewritten wholesale.
- The `-opus` doubling has a maintenance cost, not a runtime cost (see Tech debt).

## Gotchas & footguns   <- downstream must-address

- **graphify reference removed (resolved).** `README.md` and `CLAUDE.md` no longer advertise a `/graphify` skill and carry no hardcoded skill count: `grep -ri graphify README.md CLAUDE.md .github/` and `grep -E '[0-9]+ skills' README.md CLAUDE.md` both return zero (R11/C8). The earlier drift - docs pointing at a `/graphify` skill absent from the tree - is closed. (NB: the skill inventory elsewhere in this report still lists `graphify`/`revise`; those folders were removed outside this cycle and are flagged as residual drift.)
- **`plan/` is deleted but the deletion is uncommitted.** All of `plan/**` shows `D` (worktree deletion, not staged). This is the expected `/review-implementation` SHIP retire (`git rm` on `plan-integration`) after "35/35 ACs verified" (`54f3db7`), but until it is committed the tree is dirty - which would trip `/parallel-plan` Step 0's stale-`plan/` guard and `/execute-plan`'s clean-tree pre-flight on the next cycle. `scripts/*` also show `M`; a fresh plan cycle wants a clean `plan-integration` first.
- **`settings.local.json` is force-tracked against a global ignore.** `.gitignore:372-373` carries `!.claude/settings.local.json` specifically to override Claude Code's default ignore of `*.local.json`. Delete that negation and the shared permissions silently stop being tracked. Do not "clean up" the negation.
- **The 20 `-opus` files are exact clones.** Editing a base skill (e.g. `parallel-plan/SKILL.md`) without applying the same edit, with the model/name/sibling-name substitutions, to `parallel-plan-opus/SKILL.md` silently drifts the two variants. There is no generator and no test that keeps them in sync.
- **Model ids are literal and unusual.** `claude-fable-5` and `claude-opus-4-8` are hard-coded in every frontmatter and body. If those ids are not valid in the running harness, the `model:` pin and the `model: "fable"`/`"opus"` agent spawns fail. Do not assume they are placeholders.
- **`handoff` and `todo` have no `model:` pin** (they inherit the session model), and `handoff` is the only skill that is model-invocable and the only one sandboxed by `allowed-tools`. Do not copy `handoff`'s frontmatter as a template for a writing skill - it cannot write files.
- **The `pvn-` lock prefix and "PVN architecture".** Lock files are named `/tmp/pvn-<resource>.lock` and commit `30fb61d` mentions "PVN architecture". "PVN" is an unexplained term of art in these prompts; keep the prefix stable so concurrent runs share the same lock name.
- **Skill files use non-ASCII punctuation** (em-dashes, `->` written as the Unicode arrow, `§`), which directly contradicts the repo's own `CLAUDE.md` ASCII-only rule for README/commit messages. The rule is scoped to README and commit messages, so the skills are not in violation, but a newcomer editing a skill to "match repo style" may wrongly strip the arrows the prompts rely on.
- **`disable-model-invocation: true` means these are opt-in.** They will not fire automatically from a vague user message; the user must type the slash command (or the orchestrating skill must invoke the sibling by name).

## Tech debt & smells

- **Wholesale duplication of the `-opus` skills** (`*-opus/SKILL.md`), 2x the maintenance surface with no sync mechanism. `parallel-plan-opus/SKILL.md:1` is a clone of `parallel-plan/SKILL.md:1` differing only by mechanical substitution.
- **Uncommitted retire state:** `plan/**` deleted and `scripts/filter_doxygen_graphs.py`, `scripts/run_doxygen.sh`, `scripts/serve_doxygen.sh` modified but not committed - a dirty `plan-integration` that the next chain run's pre-flight guards will reject.
- **No validation of the frontmatter/skill contract.** Nothing lints that every skill has the required fields, that `-opus` twins stay in sync, or that model ids are valid; a typo in `name:` or `model:` fails only at invocation time.
- **`.claude/scheduled_tasks.lock` exists** as a runtime lock excluded via `.git/info/exclude` (not `.gitignore`), so the exclusion is local-only and not shared with collaborators.

## Test surface   <- downstream gate

This domain has NO automated tests of its own - the skills are prompt documents, not executable code, and there is no linter or schema check over `SKILL.md`. Their "test" is behavioral: running the chain and checking the gate ladder is green. The gate commands the chain drives (and the permissions in `settings.local.json`) are the closest thing to a verifiable surface. The exact repo-verified commands, from `CLAUDE.md` and `.claude/settings.local.json`:

```bash
# Configure + build (Gate 1)
cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# Tests headless (Gates 2-3) - the offscreen form the chain uses
cd build && ctest -C Release -VV
QT_QPA_PLATFORM=offscreen ctest -C Release -VV     # headless environments

# Via the Makefile convenience entrypoint
make configure && make build && make test           # make test sets QT_QPA_PLATFORM=offscreen
make docs                                            # bash scripts/run_doxygen.sh

# Dependencies
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release
```

Conspicuously untested: the skills themselves (no frontmatter schema check, no `-opus` sync check, no dead-link check for the `/graphify` reference), the `plan/`/`summary/` artifact grammars, and the model-id validity. All of these fail only at invocation time.

## Extension points

- **Add a skill:** create `.claude/skills/<name>/SKILL.md` with the frontmatter contract (`name`, `description` with trigger phrases, `user-invocable: true`, usually `disable-model-invocation: true`, a `model:` pin, and `allowed-tools` if it should be sandboxed). The harness auto-discovers it as `/<name>`. Add an `-opus` twin only if it belongs to the workflow chain, applying the mechanical substitutions.
- **Add a permission:** append a `Bash(<glob>)` entry to `.claude/settings.local.json`'s `allow` array when a new build/test entrypoint is introduced, so the chain can run it headlessly without a prompt.
- **Extend the chain:** the seams are the artifact contracts. A new step should own a disjoint artifact slice (a new `plan/*.md` ledger or a new `summary/*` file) and read the upstream artifacts by name, matching the existing terse register.
- **Tune model/effort:** the `model:` frontmatter and the `model:`/`effort:` on agent spawns are the single knobs; the `-opus` variant is the canonical "run the same chain on a stronger model" example.
- **Wire an MCP companion:** the skills probe cavemem/token-savior/graphify via `ToolSearch(select:mcp__<server>__*)` and degrade silently, so a new companion is added by exposing its MCP tools and referencing them in the same guarded way.
- **Human-facing docs:** update the AI sections of `CLAUDE.md` and `README.md` when the chain changes; keep them count-free (no hardcoded skill count) and free of dangling skill references.
