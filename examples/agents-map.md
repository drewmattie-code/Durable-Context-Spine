# Example — progressive-disclosure root map (`AGENTS.md`)

DCS principle #6. This is the **map, not the manual.** Keep it short (~100 lines is the OpenAI Codex-harness reference). Its only job is to orient a fresh session and point to deeper, individually-maintained sources of truth — never to hold everything itself. A monolith that tries to hold everything crowds out the task, becomes non-guidance ("when everything is important, nothing is"), and rots.

---

```markdown
# Agent Map — example-chat-app

> Short map for any agent session. Read this first, then follow the pointers.
> Last reviewed: 2026-06-01. If this date is stale (> 30 days), flag it.

## Start here, every session
1. Run the startup sequence: `docs/startup-sequence.md`
2. Ground truth of "done": `completion-ledger.json` (never infer done from code)
3. Recent work: `progress.md` + `git log`

## Where truth lives (don't duplicate it here — link to it)
- **Architecture & layering rules** → `docs/architecture.md`
- **Domain model & data shapes** → `docs/domain.md`
- **API surface** → `docs/api.md`
- **Decisions (dated, immutable log)** → `decisions/` (newest wins; never edit a past decision, supersede it)
- **Environment / how to boot** → `boot.sh` + `docs/environment.md`
- **Test & verification policy** → `docs/testing.md`

## Golden rules (mechanical, enforced by lint/tests — not vibes)
- Dependencies flow down the layer hierarchy only; cross-layer imports fail CI.
- Validate data shapes at every boundary.
- A feature is "done" only when its `completion-ledger.json` entry is verified end-to-end.
- Every session exits clean and committed (see `docs/startup-sequence.md` → "The exit").

## What NOT to do
- Don't put long-form knowledge in this file. Add a focused doc and link it here.
- Don't infer project state from the code. Read the ledger and progress log.
- Don't trust a doc without a recent "Last reviewed" date — flag stale docs as defects.
```

---

**Why this shape works:** a session reads ~100 lines, knows where it is and where to look, and pages in only the deeper docs it needs for the task at hand. Knowledge stays individually dated, cross-linked, and freshness-checkable (principle #8) instead of decaying inside one ever-growing file. This is the durable-knowledge counterpart of the [PDS](https://github.com/drewmattie-code/Progressive-Discovery-Spine) progressive-discovery thesis: PDS scopes *tools* per task; DCS scopes *durable knowledge* per session.
