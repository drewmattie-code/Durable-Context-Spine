# DCS Claude skills

This directory holds the DCS architectural-consultant skill in a format that drops directly into Claude Code, Codex, Cursor, and other clients that support the skills convention.

## Install for Claude Code

```bash
mkdir -p ~/.claude/skills/dcs
cp dcs/SKILL.md ~/.claude/skills/dcs/SKILL.md
```

Restart your Claude Code session (or run `/help` and confirm the skill appears).

The skill will then activate automatically when you ask architectural questions about agent memory, cross-session continuity, system-of-record design, completion ledgers, context compaction, or any of the other triggering contexts described in the SKILL frontmatter.

## What the skill does

It's an architectural consultant, not a code library. When triggered, Claude (or another supporting agent) will:

1. Diagnose which of the four documented continuity failure modes you're hitting (false completion, inherited mess, re-derivation tax, durable-state rot)
2. Recommend the 2–3 DCS principles that address it
3. Give one concrete next step
4. Link to the full spec for deeper reading

It will NOT install software, pretend to be a runnable library, or recite the whole spec at you. The point is fast diagnosis.

## Composition with the rest of the Spine

If the user is also coordinating multiple agents within a run, the [ACS skill](https://github.com/drewmattie-code/Adversarial-Coordination-Spine) applies in parallel — ACS owns the concurrency axis, DCS owns the temporal axis. If the user is scoping tools for a single agent, the [PDS skill](https://github.com/drewmattie-code/Progressive-Discovery-Spine) applies. Install whichever combination matches the architecture.

```bash
mkdir -p ~/.claude/skills/dcs
cp dcs/SKILL.md ~/.claude/skills/dcs/SKILL.md
```

## Other clients

The SKILL.md format is portable. Drop it into:

- **Cursor** — `~/.cursor/skills/dcs/SKILL.md`
- **Codex** — `~/.codex/skills/dcs/SKILL.md`
- Any other agent that supports the SKILL.md / agent-skill convention

For agents that don't natively support the skills convention, the SKILL.md is also readable as a prompt — paste it into a system prompt or context.

## Versioning

The skill version tracks the spec version. Current: v0.1-draft (matches SPEC.md v0.1-draft).

## Attribution

Durable Context Spine by Drew Mattie · SaaSquach AI Labs (a division of Charles & Roe Inc.) · CC BY 4.0
