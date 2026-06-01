# Durable Context Spine — Specification

> **Status:** v1.0 · Drew Mattie · 2026-06-01
> **License:** [CC BY 4.0](LICENSE-CC-BY-4.0)

This is the full technical specification for the Durable Context Spine pattern. The [README](README.md) is the elevator pitch; this document is the build reference.

---

## 1. Context — what DCS solves

By 2026 the question for AI agents is no longer "can the agent finish a task inside one context window." It is "can a *project* — a codebase, an investigation, a migration, a long-lived operation — advance correctly across dozens of disconnected agent sessions, run over days or weeks, by agents that never share a context window and may never run at the same time."

That is a different axis from coordination. [ACS](https://github.com/drewmattie-code/Adversarial-Coordination-Spine) solves coordination **across agents inside a single run** — the concurrency axis. DCS solves continuity **across the context-window boundary, across disconnected sessions, across time** — the temporal axis. A single agent working alone, picking a project back up two weeks later, hits every DCS failure mode and zero ACS failure modes.

**DCS is the architectural discipline that lets project state, memory, and knowledge survive the context-window boundary so the next session — possibly a different agent, possibly weeks later — picks up the thread without loss, re-derivation, or a false sense of "done."** DCS does not replace any framework — Claude Agent SDK, Letta, OpenAI Codex harness, LangGraph checkpoints, custom file-system state all implement it — it names the pattern production teams converge on once their work outgrows a single window.

Four failure modes recur across long-lived agent projects:

1. **False completion.** A fresh session looks at a codebase, sees that a lot of code exists, infers the job is done, and stops — declaring victory on a half-built project. The completeness was *inferred from the artifact* instead of *read from a ground-truth ledger*. Anthropic documented this precisely: a coding agent in a fresh session "would look around, see that progress had been made, and conclude that the job was done."
2. **Inherited mess.** A session runs out of context window mid-implementation and leaves no clean, resumable state — half-applied edits, broken tests, undocumented decisions. The next session burns most of its budget on archaeology instead of progress. The root cause is the *absence of a clean-state exit discipline*, not model intelligence.
3. **Re-derivation tax.** Every new session re-discovers how to boot the environment, where things live, and what was already decided — because no durable orientation substrate exists. Tokens and wall-clock bleed on rediscovery that should have been a two-second read.
4. **Durable-state rot.** A monolithic or stale memory artifact actively *misleads* future sessions. A giant `AGENTS.md` crowds out the task and becomes non-guidance ("when everything is important, nothing is"); a compaction summary survives but the load-bearing nuance does not; a manual goes stale and now points sessions at decisions that were reversed months ago. Stale durable state is worse than none.

DCS is the implementation discipline that addresses all four.

---

## 2. The architectural layer

DCS is not a coordination layer between agents and it is not a tool layer between an agent and its backends. It is the **persistence substrate beneath time** — the system of record that every session, in every run, reads from at the start and writes to at the end. It is orthogonal to PDS (which tools) and ACS (which agents); it answers *which state survives*.

```
        TIME ──────────────────────────────────────────────────▶

  ┌─ Session T0 ─┐   ┌─ Session T1 ─┐        ┌─ Session Tn ─┐
  │ INITIALIZER  │   │ WORKER       │   ...  │ WORKER        │
  │ builds the   │   │ orients,     │        │ orients,      │
  │ substrate    │   │ does 1 unit, │        │ does 1 unit,  │
  │ once         │   │ exits clean  │        │ exits clean   │
  └──────┬───────┘   └──┬────────┬──┘        └──┬─────────┬──┘
         │ write        │ read   │ write        │ read    │ write
         ▼              ▼        ▼              ▼         ▼
  ┌────────────────────────────────────────────────────────────┐
  │ DURABLE CONTEXT SPINE — the system of record               │
  │                                                            │
  │  completion-ledger.json   ← ground truth of "done"         │
  │  progress.md              ← human-readable session log     │
  │  decisions/ · docs/       ← progressively-disclosed map    │
  │  boot.sh                  ← deterministic env startup      │
  │  version history (git)    ← recovery + provenance          │
  │  memory blocks            ← working / episodic / semantic  │
  │                                                            │
  │  Every artifact: identity-scoped · freshness-tracked       │
  └────────────────────────────────────────────────────────────┘
         ▲                                          ▲
         │ ACS writes run handoffs here             │ AGS binds identity
         │ PDS reads scoped tool context here       │ + audit to partitions
```

The transient context window is scratch. The durable store is truth. Every session assumes nothing about another session's context window survived — because nothing did.

---

## 3. The 10 principles

### 3.1 — The durable store is the system of record; context is disposable

**Problem.** Teams treat the context window like the place where project knowledge lives, then watch that knowledge evaporate at the window boundary. Anything held only in a session's context — a decision, a convention, a half-finished plan — does not exist to the next session.

**Pattern.** Make a durable store (a repository, a database, a structured workspace directory) the single system of record. OpenAI's framing from the Codex harness experiment is the cleanest statement of the rule: *from an agent's perspective, anything it cannot access in context while running effectively does not exist.* Knowledge in Slack, a doc, or someone's head is invisible. So the discipline is: if a future session needs it, it gets written to the store, in a form a future session can read.

**Implementation.** Pick the store. For code, the repository. For operations, a workspace directory under version control. The store holds the completion ledger, the progress log, the decision/architecture docs, and the boot script. Context is where work *happens*; the store is where state *lives*.

**Anti-pattern.** "The next session can read the conversation history." There is no conversation history across sessions. The window is gone.

---

### 3.2 — Ground-truth-of-done is an explicit, inviolable ledger — never inferred from the work

**Problem.** An agent that infers completeness from the artifact gets it wrong often enough to be dangerous. Code can exist and be non-functional. Functionality can exist and be incomplete. A session that reads the code and reasons about what is done will, reliably, declare victory early (failure mode #1).

**Pattern.** Maintain an explicit, machine-readable completion ledger that is the *only* source of truth for "done." Each unit of work has a boolean `passes` field, flipped to `true` only after end-to-end verification — not after the code is written, not after a unit test passes, after the behavior is verified the way a user would experience it. Anthropic's reference shape:

```json
{
  "category": "functional",
  "description": "New chat button creates a fresh conversation",
  "steps": ["Navigate to main interface", "Click 'New Chat'",
            "Verify a new conversation is created"],
  "passes": false
}
```

**Implementation.** Store the ledger as **JSON, not Markdown.** This is a behavioral choice, not a cosmetic one: empirically, models are far less likely to casually rewrite or "tidy" a rigid JSON structure than free-form prose. The ledger should feel inviolable. Accompany it with an explicit instruction that removing or weakening entries is unacceptable. A session reads the ledger and *knows* what is done — no inference required.

**Anti-pattern.** A prose "progress so far" paragraph the agent rewrites freely each session. It drifts, softens, and eventually lies.

---

### 3.3 — Every session ends in a clean, resumable state

**Problem.** Without an explicit exit discipline, sessions stop wherever the context window happens to fill up — half-implemented features, broken tests, undocumented changes. The next session inherits the mess (failure mode #2) and spends its budget untangling instead of advancing.

**Pattern.** Make clean state a first-class exit requirement, not a nice-to-have. Every session ends by: committing with a descriptive message, updating the progress log, and reverting any half-applied work to a coherent baseline. "Clean" means *mergeable* — code a developer could pick up without first untangling someone else's half-finished work. Version control is not just history here; it is the **recovery mechanism** — when a change breaks something, revert to last-known-good and retry, exactly as a human engineer would.

**Implementation.** Encode the exit sequence into the session's operating instructions: commit → update `progress.md` → confirm the baseline still boots. A session is not "done" until the store reflects a clean state.

**Anti-pattern.** "We'll clean it up next session." The next session doesn't know what "it" was.

---

### 3.4 — Separate the initializer from the workers

**Problem.** If every session has to both set up the world *and* do the work, the setup cost is paid on every run, and early sessions leave a half-built environment that later sessions can't reliably boot.

**Pattern.** Split the very first session into a distinct **initializer** role whose entire job is to build the durable substrate that all later sessions consume. It writes no features. It produces: a reliable environment-boot script, the completion ledger (every entry initially `false`), the progress log, the initial commit, and the top-level knowledge map. Every subsequent **worker** session is cheap to start because the substrate already exists.

**Implementation.** Give the initializer a distinct system prompt: "you set up the environment future sessions operate in; you do not implement features." This mirrors Anthropic's documented two-part architecture (initializer agent + coding agent) that turned multi-session builds from "consistently fails" into "months of incremental progress."

**Anti-pattern.** Letting session #1 start implementing features immediately, leaving every later session to reverse-engineer how to start the project.

---

### 3.5 — A deterministic startup sequence orients every session before any new work

**Problem.** A session that dives into new work without orienting builds on assumptions — and often on a broken foundation, compounding an existing fault into a harder-to-isolate one.

**Pattern.** Every session runs the same orientation sequence before touching anything new:

1. Confirm location / environment (`pwd`, branch).
2. Read the progress log and recent version history — what happened last.
3. Read the completion ledger; pick the highest-priority incomplete item.
4. Boot the environment via the boot script.
5. Run the baseline check. **If the baseline is broken, fix that before starting anything new.**

Only then does new work begin. The sequence is deterministic so it is cheap, repeatable, and itself debuggable.

**Implementation.** Encode the five steps as the opening of every worker session's instructions. The boot script (from principle #4) makes step 4 a single command instead of a rediscovery exercise — which is most of how you defeat the re-derivation tax (failure mode #3).

**Anti-pattern.** Starting a new feature on top of a foundation you didn't verify is intact.

---

### 3.6 — Progressive disclosure of durable knowledge — a small stable map, not a monolith

**Problem.** The instinct is to put everything an agent might need into one big instruction file. It fails in four documented ways (OpenAI): context is scarce and the monolith crowds out the actual task; too much guidance becomes non-guidance ("when everything is important, nothing is"); it rots instantly into a graveyard of stale rules; and it can't be verified, freshness-tracked, or cross-linked.

**Pattern.** A short, stable entry point (OpenAI used a ~100-line `AGENTS.md`) that serves as a *map* — pointing to deeper, indexed, individually-maintained sources of truth. Sessions start with the minimum needed to orient and are taught where to look next, rather than being buried up front. This is the durable-knowledge counterpart of the [PDS](https://github.com/drewmattie-code/Progressive-Discovery-Spine) thesis: PDS scopes *tools* per task; DCS scopes *durable knowledge* per session. The same cognitive economics — attention is finite and front-loaded — drive both.

**Implementation.** One short map file at the root; a `docs/` or `decisions/` tree of focused, cross-linked, individually-dated documents behind it. The map points; the documents hold.

**Anti-pattern.** A 2,000-line `AGENTS.md` that everyone stops reading and no one keeps current.

---

### 3.7 — Compaction is lossy by construction — persist load-bearing state before the window closes

**Problem.** Compaction (summarizing old context to make room) is necessary for long sessions but lossy by design: the summary survives, the nuance does not. State that lives only in the window and is load-bearing for a future session is exactly the state most likely to be silently dropped.

**Pattern.** Treat the summary as untrustworthy for anything that matters downstream. Anything a future session needs is written to the durable store *before* the window compacts, not left in context to be summarized. Adopt an explicit memory hierarchy:

| Tier | Where it lives | Lifetime |
|---|---|---|
| **Working** | the active context window | this turn |
| **Episodic** | append-only run logs (`critique-log.md`, `debug.log`) | this session |
| **Semantic** | the canonical store (ledger, decisions, docs) | the project's life |

This is the MemGPT insight rendered as a discipline: the model has a small fast tier and must page the durable tiers in and out deliberately rather than hoping the window holds everything.

**Implementation.** Before any compaction-triggering boundary, flush load-bearing decisions and state to the semantic tier. Never rely on the post-compaction summary to carry a commitment forward.

**Anti-pattern.** Storing "what I committed to do" in the window and trusting compaction to preserve it.

---

### 3.8 — Durable knowledge carries provenance and freshness, or it rots into a liability

**Problem.** Durable state that isn't maintained becomes the most dangerous kind of state: confidently wrong. A stale decision doc actively points sessions at the opposite of the current intent. Drift is inevitable without a mechanism against it.

**Pattern.** Every durable artifact carries provenance (who/what wrote it, when, against what version) and a freshness expectation. Recurring cleanup passes scan for drift, regrade quality, prune dead rules, and open targeted corrections — the same way OpenAI's harness used recurring background tasks to keep an agent-generated codebase legible. Documentation here is not for humans first; it is an **interface for agents**, and an out-of-date interface produces wrong behavior, not just confusion.

**Implementation.** Timestamp and version every durable artifact. Schedule a recurring freshness sweep (a cleanup session whose only job is to detect and correct drift). Treat a stale artifact as a defect, not a cosmetic debt.

**Anti-pattern.** Write-once durable docs that nobody is responsible for keeping true.

---

### 3.9 — Durable state is partitioned by project / tenant / agent identity — no cross-context bleed

**Problem.** A shared, unpartitioned memory store lets one project's state silently contaminate another's — a catastrophic failure in any multi-tenant or multi-project deployment, and a quiet correctness bug even in a single team's many repos.

**Pattern.** Durable state is scoped and identity-bound. Each project / tenant / agent reads and writes only its own partition; cross-partition access is explicit and governed, never ambient. This is where DCS composes with [AGS](https://github.com/drewmattie-code/Agent-Governance-Spine): the same per-agent cryptographic identity that AGS uses to authorize *actions* scopes DCS *memory*. "Whose memory is this" should never be a guess.

**Implementation.** Namespace the store by a stable identity key. Make cross-partition reads a deliberate, audited operation. In enterprise settings, this is the difference between a durable-memory system that passes a tenancy review and one that fails it.

**Anti-pattern.** One global memory blob that every agent and project writes into.

---

### 3.10 — The continuity record is also the audit surface

**Problem.** When a long-lived agent project produces a wrong outcome, the post-mortem question is "what did we know, and when did we know it?" If state was never persisted with provenance, the answer is "we can't reconstruct it."

**Pattern.** Because DCS already persists state with provenance and freshness (principle #8) under partitioned identity (principle #9), the continuity record *is* the forensic record. You can reconstruct what any session knew at any timestamp, which decision was live when an action was taken, and which stale artifact misled a run. This is what lets "bad continuity / lost or stale durable state" become a first-class entry in a cross-layer failure-attribution model, alongside bad tools (PDS), bad coordination (ACS), bad external data (ESF), bad scoring (CRI), and bad governance (AGS).

**Implementation.** Keep the version history immutable and queryable. Treat every durable write as an audit event. Compose with AGS so the same audit surface covers both actions and memory.

**Anti-pattern.** A durable store you overwrite in place with no history — convenient until the first incident, then useless.

---

## 4. SLAs and success metrics

| Metric | Target | Rationale |
|---|---|---|
| Cold-start orientation cost (orient → first new action) | < 5% of session budget | A session should spend its budget on work, not archaeology |
| False-completion incidents (declared done on unverified work) | 0 | The ledger, not inference, defines done (principle #2) |
| Resumability (sessions that start without manual untangling) | 100% | Clean-state exit is the contract (principle #3) |
| "Done" claims backed by a verified ledger entry | 100% | No done without an end-to-end-verified ledger flip |
| Load-bearing state lost across a compaction event | 0 | If compaction breaks continuity, the discipline is wrong (principle #7) |
| Durable artifacts past their freshness SLA | trended to 0 | Stale state is a defect, not debt (principle #8) |
| Cross-partition memory-bleed incidents | 0 | Memory is identity-scoped (principle #9) |
| Reconstructable "what did the session know, and when" | 100% | Continuity doubles as audit (principle #10) |
| Re-derivation token tax per session (env / layout rediscovery) | bounded; trended down | The substrate exists so sessions don't re-derive it |

---

## 5. Build sequence

DCS is built from substrate to first reference deployment. Each step depends on the previous one. Pace varies by team and tooling; the sequence does not.

| Step | Deliverable | Why |
|---|---|---|
| 1 | Pick the durable store; define the system-of-record file convention (completion ledger, progress log, decision log, boot script) | Everything else reads and writes here |
| 2 | Completion-ledger format — JSON, per-item `passes`, verification-gated; explicit "inviolable" instruction | The load-bearing source of truth for "done" |
| 3 | Clean-state exit discipline — commit + progress-log update + baseline-intact check, enforced every session | Makes every handoff resumable |
| 4 | Initializer role — a distinct first session that builds the substrate (boot script, ledger, progress log, first commit, knowledge map) | Sets up the world once; workers stay cheap |
| 5 | Deterministic startup sequence — the five-step orientation every worker runs before new work | Defeats the re-derivation tax; prevents building on breakage |
| 6 | Progressive-disclosure knowledge map — short root map + indexed, dated docs behind it | Durable knowledge that doesn't rot or crowd context |
| 7 | Compaction policy + memory hierarchy — what gets flushed to the semantic tier before the window closes | Survives lossy compaction |
| 8 | Freshness/cleanup sweep + provenance + identity partitioning (and the AGS audit composition) | Keeps the substrate true, scoped, and auditable |

---

## 6. Anti-patterns to avoid

| Anti-pattern | Why it breaks | What to do instead |
|---|---|---|
| Infer "done" from the code | False completion; code exists ≠ behavior works | Explicit verification-gated ledger (principle #2) |
| State lives only in the context window | Evaporates at the window boundary | Durable store as system of record (principle #1) |
| No exit discipline | Inherited mess; next session does archaeology | Clean, mergeable, committed exit (principle #3) |
| Every session sets up its own world | Re-derivation tax on every run | Initializer / worker split (principle #4) |
| Start new work without orienting | Build on a broken foundation | Deterministic startup sequence (principle #5) |
| One monolithic `AGENTS.md` | Crowds context, becomes non-guidance, rots | Short map → indexed docs (principle #6) |
| Trust the compaction summary | Load-bearing nuance silently dropped | Flush to the semantic tier first (principle #7) |
| Write-once durable docs | Stale state confidently misleads | Provenance + freshness sweeps (principle #8) |
| One global shared memory blob | Cross-project / cross-tenant bleed | Identity-partitioned store (principle #9) |
| Overwrite the store in place, no history | No post-mortem possible | Immutable, queryable continuity record (principle #10) |

---

## 7. Compatibility with existing frameworks

DCS is framework-agnostic. The pattern can be implemented in any of these stacks:

- **Anthropic Claude Agent SDK** — context compaction, the memory tool, and file-system tools map directly to the working/episodic/semantic hierarchy (principle #7) and the system-of-record store (principle #1).
- **OpenAI Codex harness** — the `docs/` system of record + ~100-line `AGENTS.md` map are principles #1 and #6 in production.
- **Letta (formerly MemGPT)** — memory blocks and the page-in/page-out memory hierarchy operationalize principle #7; identity-scoped blocks operationalize principle #9.
- **LangGraph** — checkpointers and persisted state graphs implement the durable store and resumability (principles #1, #3).
- **`AGENTS.md` / `CLAUDE.md` conventions** — the progressive-disclosure knowledge map (principle #6).
- **git** — the recovery mechanism and immutable provenance/audit substrate (principles #3, #10).
- **Custom** — a workspace directory under version control with the four canonical artifacts is sufficient.

DCS composes with the rest of the Spine catalog:

- **[PDS](https://github.com/drewmattie-code/Progressive-Discovery-Spine)** scopes tools per task; DCS scopes durable knowledge per session — same progressive-disclosure economics, different axis.
- **[ACS](https://github.com/drewmattie-code/Adversarial-Coordination-Spine)** coordinates agents within a run and writes its handoffs (`feature-list.json`, `progress.md`, `contract.md`) *into the DCS store* — ACS owns the within-run concurrency axis; DCS owns the across-run temporal axis. They share the substrate.
- **[AGS](https://github.com/drewmattie-code/Agent-Governance-Spine)** binds per-agent identity and tamper-evident audit to DCS's partitions (principles #9, #10).

---

## 8. References

### Foundational sources

- OpenAI, *Harness Engineering: Leveraging Codex in an Agent-First World* (2026) — repository as system of record, `AGENTS.md` as a map, recurring cleanup tasks, application legibility ([openai.com](https://openai.com/index/harness-engineering/))
- Anthropic, *Harness Design for Long-Running Application Development* — the initializer + coding-agent architecture, `feature_list.json`, progress files, clean-state requirement, startup sequence ([anthropic.com](https://www.anthropic.com/engineering/harness-design-long-running-apps))
- Anthropic, *Effective Harnesses for Long-Running Agents* ([anthropic.com](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents))
- Anthropic, *Building Effective Agents* — context compaction and memory framing ([anthropic.com](https://www.anthropic.com/research/building-effective-agents))
- Yang, Jimenez, et al., *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering* — capped tool output and the collapse of stale observations into single-line summaries (context management) ([arXiv:2405.15793](https://arxiv.org/abs/2405.15793))
- Packer, et al., *MemGPT: Towards LLMs as Operating Systems* — the working / episodic / semantic memory hierarchy and deliberate paging ([arXiv:2310.08560](https://arxiv.org/abs/2310.08560))
- Letta, *Stateful Agents — Memory* — memory blocks, shared blocks, persistent cross-session state ([docs.letta.com](https://docs.letta.com/guides/agents/memory/))
- *The Awesome Agent Harness* taxonomy — the "frameworks vs runtimes" distinction, where runtimes provide persistent long-running memory and scheduled execution across sessions (Layer 6)

### Adjacent specifications

- Progressive Discovery Spine — [github.com/drewmattie-code/Progressive-Discovery-Spine](https://github.com/drewmattie-code/Progressive-Discovery-Spine)
- Adversarial Coordination Spine — [github.com/drewmattie-code/Adversarial-Coordination-Spine](https://github.com/drewmattie-code/Adversarial-Coordination-Spine)
- Agent Governance Spine — [github.com/drewmattie-code/Agent-Governance-Spine](https://github.com/drewmattie-code/Agent-Governance-Spine)

---

## 9. Versioning

This specification follows semantic versioning. Breaking changes to the conceptual model bump the major version; new principles or refinements bump the minor. Editorial fixes bump the patch.

- **v0.1-draft** — initial draft (2026-06-01). Internal review.
- **v1.0** — first public release under CC BY 4.0 + MIT (2026-06-01). The temporal layer of the Spine catalog (PDS · ACS · ESF · CRI · AGS · DCS).

---

## 10. Author

[Drew Mattie](https://www.linkedin.com/in/drew-mattie-88084826/) · SaaSquach AI Labs (a division of Charles & Roe Inc.) · 2026

DCS was developed at SaaSquach AI Labs (a division of Charles & Roe Inc.) as the temporal-persistence layer of the Spine catalog — the substrate that lets agent work survive across sessions and time. It is the companion specification to the [Progressive Discovery Spine (PDS)](https://github.com/drewmattie-code/Progressive-Discovery-Spine) and the [Adversarial Coordination Spine (ACS)](https://github.com/drewmattie-code/Adversarial-Coordination-Spine): PDS scopes one agent's tools, ACS coordinates many agents within a run, and DCS persists the state all of them share across runs.
