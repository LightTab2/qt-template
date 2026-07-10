---
name: ship
description: One-shot spec-driven build loop over a single SPEC.md at repo root (cavekit v4 shape) — grill the idea sharp, write the caveman-encoded spec (§G §C §I §R §V §T §B), research unknowns into §R, adversarially review to a go/no-go, then plan-execute task by task with a verification contract (named test per invariant), backprop failures into §B/§V, and finish with a read-only drift check. Right-sized: trivial fixes skip straight to build; genuinely parallel multi-domain work gets routed to /parallel-plan instead. Use for "ship this", "spec and build this", "run the loop on this", small-to-medium features built single-thread end to end.
user-invocable: true
disable-model-invocation: true
model: claude-fable-5
---
# /ship — the loop: grill → spec → research → review → build → check

One file, one loop, one thread. `SPEC.md` at repo root is the durable memory — it survives context resets: lose the window, reload the spec, keep going. You run the whole loop end to end without user gates; every verb owns only its sections; the spec is the only artifact that earns its tokens.

The idea arrives in `$ARGUMENTS`. Run on **Fable 5** at **`xhigh`**. No sub-agents for the build itself — main thread plans and executes; a sub-agent is allowed only to keep bulk research pages out of context (it returns distilled findings + sources only).

## Right-size FIRST — ceremony scales to blast radius, never to ego

- **Trivial, reversible, well-understood** (one-liner, typo-class): skip straight to BUILD against the existing `SPEC.md` (or no spec at all — just fix, test, report). Grilling a typo wastes the budget.
- **Uncertain or high-blast-radius, single-thread-sized**: the full loop below.
- **Genuinely multi-domain, parallel-worker-sized** (would need worktrees, feature waves, disjoint ownership): this loop is the wrong tool — say so and route to `/parallel-plan` (the heavy chain). Do not swarm from here.

**Memory (token-savior):** before the loop, load recall via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`); `memory_search("<topic> dead end")`, `memory_search("<topic> prior decision")` — hits become §C bullets or parked `?`s. Tools absent → skip silently.

## SPEC.md format (embedded FORMAT rules)

Fixed order, fixed headers, addressable as `§<S>.<n>` (`§V.2` = invariants item 2); a section may be absent, never reordered. **Caveman-encoded**: drop articles/filler/aux verbs, fragments fine, symbols `→ ∴ ∀ ∃ ! ? ⊥ ≠ ∈ ∉ ≤ ≥ & |`; preserve verbatim code, paths, identifiers, URLs, numbers, error strings. Big project → more sections, not more files; >500 lines → compact §B (drop oldest rows, show the diff).

```
# SPEC
## §G GOAL          one line. what code must do.
## §C CONSTRAINTS   bullets. non-negotiables, locked tech, out-of-scope, parked `?` unknowns.
## §I INTERFACES    external surface: cmd/api/file/env, exact shapes.
## §R RESEARCH      optional pipe table: id|topic|finding|src — only if research ran.
## §V INVARIANTS    numbered, testable: V1: ∀ req → auth check before handler
## §T TASKS         pipe table: id|status|task|cites — status `.` todo / `~` wip / `x` done; ids monotonic.
## §B BUGS          pipe table: id|date|cause|fix — backprop log; fix column cites the catching §V.
```

Sectioned ownership: grill sharpens §G+§C · research appends §R · review hardens §V · build flips §T status cells ONLY · backprop appends §B+§V · cross-cutting edits go through the spec-write step deliberately. No step rewrites a section it does not own.

## 1 — GRILL (self-interrogation; user unavailable mid-run)

Climb the ladder against `$ARGUMENTS`, the repo, and recall — answering yourself from evidence, parking what evidence cannot answer: goal (one line, one reading) · done (the observable) · boundary (out of scope) · lock (non-negotiable tech; forbidden things) · surface (cmd/api/file/env) · edge (the input that breaks the happy path) · unknown (park as `?` §C bullet — **never guess a constraint into existence**). Stop the moment the spec would be unambiguous. Only a load-bearing unknown that changes WHAT gets built stops the run for one user question; everything else proceeds with the `?` parked and stated.

## 2 — SPEC

Write `SPEC.md` per the format: §G, §C, §I, initial §V (numbered, testable), §T (ordered tasks, all `.`, each row's `cites` listing the §V/§I it serves), §B header row. If `SPEC.md` already exists, amend the named sections only — never clobber foreign content; task/invariant numbering is monotonic, never reused.

## 3 — RESEARCH (only if a `?` or a §C/§I/§V decision hinges on external facts)

Scope 1–3 concrete questions; prefer primary sources (official docs, repo, RFC); two independent sources beat one confident blog; distill each answer to one caveman row `R<n>|topic|finding|src` and append §R. **No source → flag `?` in the finding, never write a guess as fact.** Conflicting sources → log both. Local truth beats web guess — never research what the repo already answers.

## 4 — REVIEW (adversarial, evidence-anchored, go/no-go)

Construct the senior from evidence — grep/read the touched modules, honor §R, fetch anything you would otherwise assume — then try to REFUTE the spec: goal vs real problem · missing invariant (most findings live here) · §I vs what callers already expect (cite caller file:line) · §C conflicts · unowned edge/failure/concurrency case · §T altitude (too vague / just typing). Classify each finding `evidence → claim → severity`: **BLOCK** (build ships a defect) / **HARDEN** (add or sharpen a §V) / **NOTE**. No evidence → NOTE + `[unverified]`, never inflated. HARDEN findings become new §V lines now. End with the explicit gate: **GO**, or **NO-GO → fix the spec (amend §C/§I/§T per the BLOCKs) and re-review once**; a second NO-GO stops the run with the verdict printed — a confident wrong build is the thing this gate exists to stop.

## 5 — BUILD (plan-execute per task, verification contract)

For each §T row in order (`.` → take it):
1. Flip status `.` → `~` in SPEC.md.
2. Plan natively: cite every §V that applies and every §I touched; list files; write the **verification contract — name the EXACT test that proves each §V touched** (which test, not "add tests"; new §V → a named test that fails first, e.g. `TestV7_RefundIdempotent`); name the oracle command (test/build/lint). Green = done; ⊥ "looks done".
3. Execute minimally — every diff line traces to a §T/§V; adjacent bugs get a §B candidate note, not an in-scope fix.
4. Run the oracle. **Pass** → flip `~` → `x`, commit `T<n>: <task> (§V cites)`. **Fail** → BACKPROP, never a blind retry.

**Backprop on failure:** trace to file:line and name the root cause in one caveman line; classify — (a) my code bug → fix, re-run, no spec change; (b) spec wrong or (c) unspecified edge → append `§B B<n>|<date>|<cause>|V<N>` and (usually) a new testable §V, write the failing test named after it, fix until green, run the full suite for regressions, commit `backprop §B.<n> + §V.<N>: <cause>` (spec edit + test + fix together). Mechanical one-off typo → §B row only, no §V. Same failure signature twice = ceiling: stop retrying, record the blocker in §B, move to the next non-dependent task.

Circuit breakers: 3 consecutive oracle failures on one task → mark it back to `.` with a `?blocked` note in the row, continue with non-dependent tasks; nothing unblocked left → stop and report honestly.

## 6 — CHECK (read-only drift report, always last)

Zero writes. For each §V: HOLD / VIOLATE / UNVERIFIABLE with file:line evidence. For each §I item: MATCH / DRIFT / MISSING / EXTRA. For each §T `x` row: evidence present, else STALE. Report caveman, grouped by severity, with one-line remedy hints (fix code at cited line, `bug:` backprop, or amend §T) — hints, never auto-fixes.

## Wrap-up

Print: the gate verdict and cycles used, §T scoreboard (`x`/`~`/`.` counts), §B entries added, §V hardened, the drift summary, and the single next action. Durable facts stated plainly — save them via `mcp__token-savior__memory_save`. `cat SPEC.md` is the dashboard; there is no other state file.
