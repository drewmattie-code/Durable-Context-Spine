# Contributing to DCS

Thanks for your interest in the Durable Context Spine specification.

DCS is a **pattern specification**, not a software library. Contributions are most useful in three forms:

## 1. Implementation reports

If you have built a long-lived agent system that implements DCS (or pieces of it) in production, an issue or PR describing what worked, what didn't, and what you'd refine is the highest-value contribution. Anonymized is fine — patterns and surprises matter more than vendor names.

Template: open an issue titled `[Implementation] <one-line summary>` and include:

- Stack (model family, agent framework, durable store, harness shape)
- Which of the 10 principles you implemented and which you skipped, and why
- Which of the four failure modes you hit — false completion, inherited mess, re-derivation tax, durable-state rot — and what the fix was
- What SLAs you measured against the targets in [SPEC.md](SPEC.md#4-slas-and-success-metrics)

## 2. Pattern refinements and additions

If you find a missing principle, an unhandled continuity failure mode, or a refinement to an existing principle, open an issue first to discuss before sending a PR. The spec is intentionally tight — every principle has earned its place. New principles need to be load-bearing, not nice-to-have, and must be on the temporal/persistence axis (continuity across the boundary), not the concurrency axis (which belongs to [ACS](https://github.com/drewmattie-code/Adversarial-Coordination-Spine)).

## 3. Examples and reference materials

The [`examples/`](examples/) directory is open to:

- Completion-ledger shapes for additional domains (research, ops runbooks, data migrations)
- Startup-sequence templates for specific stacks
- Progressive-disclosure knowledge-map examples
- Memory-hierarchy / compaction-policy sketches for specific frameworks (Claude Agent SDK, Letta, LangGraph checkpoints)

Keep examples small and concrete. The point is to show the shape; production implementations belong in your own repo.

## What we won't accept

- Vendor advertising — examples that exist primarily to promote a product. Keep examples vendor-neutral.
- Speculative principles — additions without an implementation that supports them.
- Concurrency-axis material — multi-agent coordination patterns belong in ACS, not DCS. If a contribution is really about agents talking to each other within a run, it's an ACS contribution.

## Style

- Prose: declarative, no fluff. Match the existing voice in [SPEC.md](SPEC.md).
- Diagrams: Mermaid where possible (renders natively in GitHub).
- Code samples: minimal, runnable, no external dependencies beyond declared manifests.
- Markdown: GitHub-flavored. Wrap at natural sentence boundaries, not at fixed columns.

## License agreement

Contributions are accepted under the project's dual license (CC BY 4.0 for prose, MIT for code). By opening a PR, you agree to license your contribution under those terms.

## Relationship to the catalog

DCS is the temporal-persistence layer of the Spine. It composes with [PDS](https://github.com/drewmattie-code/Progressive-Discovery-Spine) (tools per task), [ACS](https://github.com/drewmattie-code/Adversarial-Coordination-Spine) (agents per run), and [AGS](https://github.com/drewmattie-code/Agent-Governance-Spine) (identity + audit). Cross-cutting contributions that touch more than one spec are welcome — open an issue on the most-affected repo first.

## Contact

Open an issue for anything spec-related. For something that doesn't fit an issue, the author's contact is in the repository About section.
