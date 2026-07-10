---
name: todo
description: Investigate the real codebase, then append one or more painstakingly detailed, workstream-sized task specs to ./NextThingsToDo.md — written as ideal input for the /parallel-plan skill (real path:line, exact type/function signatures to freeze as contracts, explicit file ownership for disjoint worktrees, dependency/parallelism hints for the DAG, and unit+integration+GUI test specs with labels). Use when the user wants to "add a todo", "write a task", "queue work", "note next steps", "append to NextThingsToDo", "/todo", or prepare work for planning/parallelization.
user-invocable: true
disable-model-invocation: true
---

# /todo — Append parallel-plan-ready task specs to `NextThingsToDo.md`

You act as a **staff engineer scoping work for a planning team**. Your output is a precise written spec, not implementation. The spec is consumed *directly* by `/parallel-plan`, which decomposes it into worktree-ready agent plans. Write so that decomposition is mechanical: every fact `/parallel-plan` needs is already on the page, grounded in the real codebase, with zero placeholders.

Work to scope is in `$ARGUMENTS`. If empty, ask the user what to add (one line). If a single piece of genuine ambiguity would change the spec, ask **one** sharp clarifying question, then proceed; otherwise pick the most idiomatic default, state the assumption inline, and continue.

**Deliverable = appended task block(s) in `./NextThingsToDo.md`.** Do not implement, do not launch agents. Investigate, append, summarize what you added, stop.

---

## Why the detail matters — write *for* `/parallel-plan`

`/parallel-plan` does five things with this file. Each one needs a specific kind of fact, so capture it now:

| `/parallel-plan` step | What it needs from your task block |
|---|---|
| **Extract requirements (R\*) and build the Coverage Matrix** (every acceptance criterion → task → gate) | **R-numbered requirements with testable acceptance criteria.** Every AC must answer "how would an automated test verify this?" — observable, deterministic, automatable. An AC that can't map to a test/gate is a spec bug; sharpen it here, not at plan time. |
| **Freeze shared contracts** (types, signatures, API/DB/event shapes decided once) | **Exact code** — real type defs, function signatures, enum values, serialization IDs. Not prose like "a getter". |
| **Assign disjoint ownership** (one worktree = one agent = non-overlapping files) | An explicit **files-to-change list with real paths**. Two tasks that edit the same file cannot run in parallel — say so. |
| **Model the dependency DAG** (sequential vs concurrent) | A **depends-on / blocks** line per task: which task or contract must land first, which are independent. |
| **Write the Testing section** (unit + integration + GUI, real commands) | Named **test files, test labels, and the cases** to cover, plus the exact run command. |
| **Honor constraints** (off-limits paths, repo rules) | The **repo rules** that bound this work (layering, banned APIs, no-backward-compat, build/test commands). |

A vague todo forces `/parallel-plan` to re-investigate and guess ownership — which produces colliding worktrees and merge hell. A precise todo makes it trivial to draw clean, parallel boundaries. Precision here is the whole point.

---

## Step 1 — Ground in the real codebase (never write blind)

A todo written without reading code is fiction `/parallel-plan` will inherit. Before writing anything:

1. **Read project rules.** `CLAUDE.md` / `AGENTS.md` / `README` (often already in context). Capture the **real** build, test, and lint commands and the test-label scheme verbatim.
2. **Locate the exact code the work touches.** Prefer MCP tools when available (`mcp__token-savior__find_symbol`, `get_function_source`, `search_codebase`; `mcp__graphify__query_graph`, `get_neighbors`) before Grep/Glob/Read. Find the real files, types, call sites, and their `path:line`.
3. **Copy real signatures.** Paste the actual constructor/method/type signatures the work depends on or must produce — these become `/parallel-plan`'s frozen contracts. If a symbol is a stub or has a `\todo`, note it so the plan doesn't call it.
4. **Map the test + UI surface.** How are unit / integration / GUI tests written, named, registered, and run here? Which label does new work get? Where does a new test file get registered (build list **and** label list)?
5. **Find collisions.** For each file the work edits, note any *other* pending task in `NextThingsToDo.md` that edits the same file — that's a serialization constraint `/parallel-plan` must respect.

Carry concrete facts into the spec. Cite real `path:line`, real names, real commands — never "the relevant file".

---

## Step 2 — Shape the work into workstream-sized tasks

One task block ≈ one candidate worktree for `/parallel-plan`. So:

- **Split by ownership, not by feature.** If the work naturally divides into chunks that touch **disjoint files**, emit one `## Task N` block per chunk so they can parallelize. If two chunks must edit the same file, keep them in one block (or mark the dependency explicitly).
- **Make each block independently mergeable and testable.** State what it delivers in isolation.
- **Order by dependency.** Number tasks so prerequisites come first; record the dependency explicitly (don't rely on number alone).
- **Don't fake parallelism.** If the work is genuinely sequential, say so and emit ordered phases.
- **YAGNI ruthlessly.** Strip requirements the user did not ask for — smaller specs are better specs. This is orthogonal to boldness: an ideal-end-state restructure that serves the goal is in scope; speculative features are not.

Scale depth to the work: a one-file tweak gets a short block, but every template section is still considered (mark a section **N/A** when it truly doesn't apply — e.g. GUI tests for a pure data-layer change). Never drop Testing.

**Memory (token-savior):** before writing, load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`) and `memory_search("<topic> dead end")` / `memory_search("<topic> prior attempt")` — a documented dead end becomes a **Constraints** bullet ("do not reattempt X: <root cause>"). Tools absent → skip silently.

---

## Step 3 — Append without clobbering

`NextThingsToDo.md` is shared state. Edit surgically:

1. **Read the current `./NextThingsToDo.md`** (target is the repo-root file; if the user named a different file, use that). If it does not exist, create it with a `# Next Things To Do` heading.
2. **Find the next task number** — scan for the highest `## Task N` heading and continue from `N+1`.
3. **Insert before the trailing global section.** If the file ends with a shared `## Constraints` (or similar) section, insert the new task block(s) **immediately before it**, separated by `---`, so global constraints stay last. Otherwise append at the end.
4. **Augment, don't duplicate, global constraints.** If your work introduces a new repo-wide rule, add one bullet to the existing global `## Constraints` section instead of repeating it in every block.
5. **Match the existing file's style** — the bold-label format (`**Problem**:`, `**Goal**:`, …) and `---` separators already in use.

Use `Edit` for an in-place insertion when the anchor is unique; otherwise `Read` the whole file and `Write` it back with the block inserted. Never overwrite existing tasks.

---

## Task block template

Append one block per workstream-sized unit, in this shape (drop a section only when genuinely N/A, and say so):

```markdown
## Task N — <short imperative title>

**Problem**: What is wrong or missing, with real `path:line` evidence. Quote the offending code or comment if one exists.

**Goal**: What to build, concretely. The user-facing or structural outcome.

**Requirements** (R-numbered; `/parallel-plan` freezes these and builds its Coverage Matrix from the ACs):
- **R1 — <name>**: one-sentence behavior — WHAT, never HOW (no framework names or file paths here; those live in Contracts/Files below).
  - AC1.1: testable criterion — `Given <precondition>, when <action>, then <observable result>` or `<metric> meets <threshold> under <conditions>`. Observable, deterministic, automatable.
  - AC1.2: …
- **R2 — …**

Weak → strong calibration: "handle errors gracefully" → "network failure shows a retry prompt with exponential backoff (1s, 2s, 4s)". A criterion you cannot name a test for will not be reliably met — rewrite it now.

**Contracts / signatures** (freeze these): Exact code the work consumes or must produce — real type defs, method signatures, enum values, serialization IDs. Paste the actual signature, not a description.

**Files to change** (ownership for one worktree):
- `src/.../Foo.h`, `src/.../Foo.cpp` — what changes
- `test/testFoo.cpp` — new/updated

**Depends on / blocks**: Which prior task or frozen contract must land first; which later work consumes this. "Independent — parallelizable with Task X" when nothing blocks it. Note any file shared with another pending task.

**Tests**:
- **Unit**: file name, the label, the functions/branches and edge+failure cases to cover.
- **Integration**: cross-module/IO behavior against the contracts, with the harness/fixtures. (N/A if none.)
- **GUI / E2E**: the user flow to drive with the repo's runner, happy + one error path. (N/A if not user-facing.)
- **Run command**: the exact invocation.

**Acceptance**: All R\*/AC checkboxes above green, plus any observable condition that spans multiple requirements. Do not restate the ACs.

**Constraints**: Repo rules that bind this task — layering, banned APIs, no-backward-compat, naming, build/test commands. (Reference the global `## Constraints` section rather than repeating it.)
```

---

## Quality bar before you finish

- Every path, signature, command, and test name is **real and verified against the codebase** — no placeholders.
- Ownership lists are **disjoint** across the new blocks (or collisions are called out).
- Dependencies are explicit, so the DAG draws itself.
- A fresh agent could hand any single block to `/parallel-plan` and get a clean workstream out — no re-investigation required.

After appending, tell the user which task numbers you added and a one-line summary of each, and remind them they can run `/parallel-plan` to decompose them.
