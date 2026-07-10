---
name: codebase-summary-opus
description: Produce a summary/ folder documenting a codebase by dispatching one specialist agent per domain — each READS + reasons about its subsystem (control/data flow, contracts, invariants, gotchas) instead of grepping, writes its own file. A final overview.md ties domains together. Built to feed /parallel-plan-opus, /review-plan-opus, /execute-plan-opus: emits owned-path globs per domain, exact build/test/lint commands, cross-domain contract candidates, a risks checklist. Use for "summarize the codebase", "document the architecture", "explain this repo", "onboarding doc", "analyze the code", "map the system".
user-invocable: true
disable-model-invocation: true
model: claude-opus-4-8
---
# /codebase-summary-opus — Deep per-domain analysis by specialist agents

You are a tech lead onboarding onto an unfamiliar system, and skimming is not acceptable. Do not read everything yourself — deploy domain specialists: one agent per subsystem, each of which genuinely understands its slice and writes its findings in exhaustive, evidence-backed detail. Afterwards, synthesize their reports into one map.

This skill takes no arguments. It always covers the whole repository.

Spawning agents is the core of this skill. Carve the codebase into domains, dispatch one specialist per domain in parallel, and synthesize the results. Do not deep-analyze in the main thread; your job is to scope, delegate, and integrate.

## Model & effort (mandatory)

**Orchestrate on Opus 4.8 (`claude-opus-4-8`) — the main thread only carves domains, dispatches, and synthesizes. It never deep-analyzes.** Every specialist fans out on **Opus 4.8 at `xhigh`**:
- **Workflow tool (PRIMARY):** set `model: "opus"` and `effort: "xhigh"` on every `agent()` call. This is the default for domain fan-outs of 3 or more.
- **Agent tool (fallback, 1–2 agents):** set `model: "opus"` and `run_in_background: true` on every call. The Agent tool has no per-call effort knob, so prefer Workflow whenever the `xhigh` guarantee matters.
- Specialists that spawn their own sub-agents propagate the same `opus` + `xhigh`.

## Memory (token-savior)

Before carving domains, load the token-savior memory tools via ToolSearch (`select:mcp__token-savior__memory_search,mcp__token-savior__memory_get`) and query prior knowledge: `memory_search("<repo> architecture domains")`, `memory_search("<repo> gotcha dead end")`; fetch the top hits with `memory_get` and fold them into recon. Memories reflect when they were written — verify any recalled file/command against the code before repeating it. If the memory tools are absent, skip silently; never block on memory. Capture is explicit — at wrap-up, save the durable facts via `mcp__token-savior__memory_save` and restate them (domain map, key contracts, top risks) in the console summary so they persist.

## Downstream contract — this output feeds the planning chain

`summary/` is the grounding for `/parallel-plan-opus` (which carves FEATURES from the domain map), `/review-plan-opus` (which builds coverage and ownership matrices from it), and `/execute-plan-opus` (which lifts the gate commands and conventions). Emit the fields they consume, precisely:
- **Owned-path globs per domain** — disjoint where possible. parallel-plan-opus assigns feature ownership from these, and review-plan-opus builds its ownership-collision matrix from them. Vague paths are unusable downstream.
- **Exact commands** — build / test (unit, integration, e2e/GUI) / lint / format / typecheck, all copy-pasteable. execute-plan-opus's gate is lifted from here verbatim.
- **Cross-domain contract candidates** — types, APIs, schemas, and events that two or more domains share. parallel-plan-opus freezes these as C* contracts.
- **Risks, debt & open questions** — this becomes review-plan-opus's coverage checklist; every item is something a plan must address or consciously scope out.
- **Conventions** — naming, indentation, error idiom, test layout, and git policy, stated in actionable form rather than loose prose.

## What you produce

```
summary/
  overview.md          # system index: purpose, domain map (+owned paths), conventions+commands,
                       #   contract candidates, cross-domain flows, glossary, risks checklist
  01-<domain>.md       # one detailed report per domain, written BY its specialist
  02-<domain>.md
```

One domain = one specialist = one file. Number the files in reading order (foundation and infrastructure first, leaf features last).

## Core principle: understand, don't pattern-match

Grep-and-summarize produces shallow, wrong documentation. Enforce the following in every agent prompt:
- **Read whole files and trace execution.** Follow call chains, data flow, and lifecycles end to end. Build a real mental model before writing anything.
- **Structural tools over string search.** The MCP graph/recall tools (`query_graph`, `god_nodes`, `get_community`, `get_neighbors`, `shortest_path`, `find_symbol`, `get_call_chain`, `get_function_source`) reveal what grep cannot.
- **Grep/Glob locate a starting point only** — they are never the analysis. Banned: "found 12 matches for `auth`". The bar: "session token minted at `auth.ts:88`, verified at `gateway.ts:41` on every request".
- **Every claim cites real evidence** — `path:line` references and real symbol names. Anything unverified must be labeled as such.

## Step 1 — Carve into domains (light recon, main thread)

Do just enough to draw clean boundaries — no deep-diving here:
1. Read `CLAUDE.md`/`AGENTS.md`, the `README`, and the manifest for the stated architecture, stack, run/test commands, and **git policy**.
2. If an MCP graph exists, use `god_nodes` and `get_community` for a free decomposition. Otherwise scan the top-level layout.
2b. **Discover capabilities — never let downstream plans invent tools.** Record what actually exists: MCP servers (`.mcp.json`, `~/.claude.json`), the stack's CLI tools on PATH, test runners, and any knowledge-graph/index artifacts. These go into the overview's Tech-stack section verbatim; `/parallel-plan-opus` binds tasks only to discovered capabilities.
3. Identify **domains** with crisp boundaries and the paths each covers. Domains are subsystems, not folders (for example: Auth & session, Data/DB layer, Routing/SSR shell, Live chat + socket bridge, UI component library, Build & config, Background jobs). Split domains that are too large; group trivial ones.
4. Write the domain → **path globs** mapping, disjoint where possible — downstream feature ownership depends on it. This mapping becomes both the dispatch table and the overview's domain map.

## Step 2 — Dispatch one specialist per domain (parallel)

Launch **all** specialists in one BACKGROUND batch: one Workflow when there are 3 or more domains, otherwise multiple Agent calls in one message with `run_in_background: true`. Collect results via completion notifications. Use an agent type that reads code AND **writes a file** (`general-purpose`) — each agent writes its own report so nothing is lost in relaying. Prompt each:

```
You are a senior engineer reverse-engineering the **<domain>** domain. Analyze it and write a
painstakingly detailed report.

SCOPE: <explicit path globs>. You may READ anything in the repo for context; WRITE only
summary/NN-<domain>.md.

METHOD — understand, don't pattern-match:
- Read the domain's files in full; trace control and data flow end to end.
- Prefer the MCP graph/recall tools (callers/callees, call chains, impact, semantic search) over grep.
- Use Grep/Glob only to locate a starting point.
- Back every claim with a real path:line and real symbols. Label anything unverified.
- Do not modify source. Write only your report.

STYLE — clear, precise technical prose. Complete sentences. Keep code, inline `code`, path:line
references, symbols, commands, tables, and headings exact. Be thorough but not padded.

OUTPUT — write summary/NN-<domain>.md with exactly the sections below, in painstaking detail:
<paste Domain report template>

DOWNSTREAM — this report feeds planning skills, so be precise on: OWNED PATHS (disjoint globs),
PUBLIC API / CONTRACTS (what other domains rely on), TEST SURFACE (exact commands), GOTCHAS
(include known dead ends: approaches the git history or comments show were tried and abandoned,
with the why).

Reply caveman-compressed (drop articles/filler; fragments fine) — 3-bullet TL;DR plus the path you
wrote. Code, paths, commands, and symbols stay exact. The report FILE stays clear full prose.
```

Each agent owns exactly one output file, so there are no write collisions.

## Domain report template (each agent fills)

```markdown
# <Domain> — analysis

## Purpose
What this subsystem is for, in 2–4 sentences. The problem it solves.

## Owned paths   ← downstream feature-ownership; keep disjoint
Path globs this domain owns (source and tests). Flag any paths shared with another domain.

## Key files & symbols
Table: load-bearing files (real paths) → central functions/types/classes → one line on each.

## Architecture & responsibilities
Internal structure, layers/modules, and who owns what. Include a small ASCII or mermaid diagram.

## Data structures & models
The important types, schemas, and DB tables — their shape and meaning, with real definitions.

## Control & data flow
Walk the primary path(s) step by step — entry → … → result — naming the functions crossed. Cover the
happy path plus important branches. Add a diagram if it clarifies.

## Public API / contracts   ← downstream contract candidates
What this domain exposes (functions, routes, events, types) and what it guarantees. What other
domains may rely on.

## Dependencies
- Inbound: real callers into this domain.
- Outbound: libraries, other domains, and external services it depends on.

## Invariants & assumptions
Rules that must hold (auth, ordering, ownership, null-ness, single-instance). What breaks if violated.

## Error handling & edge cases
How failures are detected, surfaced, and recovered. Notable edge cases and how they are handled (or not).

## Concurrency / async / lifecycle
Async boundaries, races, ordering guarantees, and mount/teardown/connection lifecycles.

## Performance
Hot paths, caching, pagination, N+1 patterns — anything that scales poorly.

## Gotchas & footguns   ← downstream must-address
Non-obvious traps a newcomer would hit: misleading names, spelling quirks, implicit coupling,
"don't touch X because Y".

## Tech debt & smells
An honest list of fragile, duplicated, or outdated parts, each with a path:line.

## Test surface   ← downstream gate
What is tested and how (framework, locations), with the EXACT run command(s). What is conspicuously untested.

## Extension points
Where and how to add functionality safely; the seams designed for extension.
```

Scale depth to domain size, but keep every section (mark a section N/A only when it truly does not apply).

## Step 3 — Synthesize `summary/overview.md` (main thread, after agents finish)

This is the system-wide index no single agent could write. Keep code, `path:line` references, tables, and headings exact:

```markdown
# <Project> — codebase summary

Generated: commit `<git rev-parse --short HEAD>`   ← freshness stamp; consumers diff against it

## What this is
Purpose and user-facing function, in a short paragraph.

## Tech stack & how to run   ← downstream conventions + gate
Languages, frameworks, datastore, package manager. EXACT build / dev / test (unit, integration,
e2e/GUI) / lint / format / typecheck commands. Git policy (worktree-only? local merges allowed?).
**Available tooling (discovered, not assumed):** MCP servers, CLI tools, runners, graph/index
artifacts that actually exist here — downstream plans bind only to these.

## Validation gate ladder   ← execute-plan-opus runs these in order, stops at first failure
Gate 1 build · Gate 2 unit · Gate 3 integration · Gate 4 perf/bench (only if the repo has one) ·
Gate 5 smoke/launch (start the app or load the entry point, health-check it) · Gate 6 human/GUI
review surface. One exact copy-pasteable command per gate that exists; mark a gate "none" honestly
rather than inventing one.

## Domain map   ← downstream FEATURE seams + ownership matrix
Table: domain → report file → one-line summary → **owned paths (globs)** → key contracts exposed.
Link each NN-<domain>.md. Owned paths should be disjoint where possible; flag overlaps explicitly.

## Cross-domain contract candidates   ← parallel-plan-opus freezes these as C*
Types/APIs/schemas/events that two or more domains share — the boundaries any multi-domain change
must freeze. Give real definitions and name the domains on each side.

## Architecture at a glance
Diagram of the domains and how they connect (data and control across boundaries).

## End-to-end flows that cross domains
2–4 whole-system journeys (request → auth → query → render; user message → socket → bridge → channel),
naming the domains and entry points each step passes through.

## Cross-cutting concerns
Auth, config/secrets, error handling, logging, i18n, state — how each is handled repo-wide and where it lives.

## Conventions
Naming, indent/brace style, import grouping, type strictness, file layout, error idiom, test framework
and location. Keep this actionable (downstream skills tell agents "match these"), not loose prose.

## Glossary
Project-specific terms as named in code, defined plainly.

## Risks, debt & open questions   ← review-plan-opus coverage checklist
The biggest fragilities and unknowns the specialists surfaced, aggregated and prioritized. Each item
is something a plan must address or consciously scope out.
```

## Quality bar

- **Evidence-based:** claims cite real `path:line` references and symbols; no invented behavior.
- **Understanding over matching:** flows are traced, not keyword-counted.
- **Painstaking detail:** a new engineer could navigate and safely change the system from these docs alone.
- **Downstream-ready:** owned-path globs disjoint, commands exact and copy-pasteable, contract candidates given as real code, risks itemized.
- **No collisions:** each agent wrote exactly one file; the main thread wrote only `overview.md`.
- **Read-only on source:** no agent modified code.
- **Honest:** unverified or sampled areas are labeled.
- **Clear prose:** every `.md` in precise, complete-sentence technical prose; code, `path:line` references, tables, and headings exact.

## Wrap-up

Print a console summary: domains covered, files written under `summary/`, top cross-cutting findings, and the biggest risks — stated as durable facts (save them via `mcp__token-savior__memory_save`; make it worth recalling). Point the user at `summary/overview.md`, then at the next action — `/parallel-plan-opus` to scope features from the domain map (or `/ship-opus` for right-sized single-thread work over a SPEC.md).
