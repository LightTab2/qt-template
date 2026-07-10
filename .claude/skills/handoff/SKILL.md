---
name: handoff
description: Print a detailed summary of THIS session's work and what to do next, directly to the console (no file written). Use when the user asks to "summarize what we did", "write a summary", "recap this session", "what's next", "checkpoint", or wants a readable handoff of the current session so work can resume later.
user-invocable: true
allowed-tools:
  - Read
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(ls *)
---

# /handoff — Session Summary & Next Steps (console only)

Prints a thorough recap of **the current session's work** and what to do
next, straight to the console. **Do not write any file.** The output is
the deliverable.

Scope is **this session only** — the work done since this conversation
began. Not the whole day, not prior sessions, not unrelated pre-existing
changes. If the working tree contains changes you did not make this
session, mention them briefly as "pre-existing (not this session)" and do
not detail them.

Arguments passed: `$ARGUMENTS`

---

## Gather the facts first (do not guess)

Read the actual state before summarizing. Base the recap on observed
reality plus what you actually did this session — not on a vague memory:

1. `git status` and `git diff --stat` — but attribute only the changes
   *this session* produced. Cross-check against what you edited in this
   conversation.
2. Recall the build/test commands you ran this session and their results.

If the build or tests were not run this session, say so — do not claim
green.

## Output format

Print to the console using this structure. Be detailed and concrete —
name files, functions, classes, test suites, line numbers. Keep it tight:
bullets over paragraphs.

```markdown
## Session summary

**Goal:** one or two sentences — what this session set out to do.

**Done this session**
- <file:symbol> — what changed and why. Tag each item DONE / PARTIAL / BLOCKED,
  and "verified" vs "not tested".
- ...

**Build & tests**
- Last build: <command> → <result, or "not run this session">.
- Last tests: <suites/labels> → <pass/fail, failures quoted, or "not run">.

**What to do next**
1. <single best starting point> — file to touch, change to make, why,
   and the exact command to validate it.
2. ...

**Open questions / blockers**
- <anything that is genuinely the user's call, or an assumption to confirm>.
  Tag each blocker TEMPORARY (resolves on its own — recheck next session) or
  PERMANENT (needs a human decision/action — name what is needed; do not
  reattempt until resolved).

**Gotchas**
- <non-obvious traps hit this session a fresh reader would waste time on>.
```

Omit a section only if it is genuinely empty (e.g. no blockers).

## Quality bar

- **Resumable.** Someone reading only this output plus the repo can
  continue without asking "what were we doing?".
- **Honest.** Failing/skipped/half-done work is labeled as such, with
  output quoted. Never report unverified work as finished.
- **Specific.** "Fixed the parser" is useless; "`StoryExtract.cpp:142`
  `parseWorldDelta()` now tolerates a trailing `END`" is a handoff.
- **This session only.** Don't pad the recap with the day's earlier or
  pre-existing changes.
- **Memorable.** save them via `mcp__token-savior__memory_save` — state dead ends and
  durable decisions as standalone facts ("X failed because Y — do not
  reattempt"), so a future session's recall gets the lesson, not a vague
  reference.
