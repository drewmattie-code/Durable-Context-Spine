# Example: deterministic session startup sequence

DCS principle #5. Paste this (adapted to your stack) into the opening of every **worker** session's operating instructions. The goal: orient in a few cheap, deterministic steps before touching any new work, and never build on a foundation you haven't verified is intact.

> The first thing you do in this session, before any new work, is run the orientation sequence below. Do not skip a step. Do not start a new unit of work until step 5 passes.

## The five steps

1. **Confirm location.** Run `pwd` and `git branch --show-current`. Confirm you are in the project root on the expected branch.

2. **Read what happened last.** Read `progress.md` and `git log --oneline -20`. Understand the last session's work and where it left off. Do not re-derive this from the code.

3. **Read the ground truth of "done."** Read `completion-ledger.json`. Choose the highest-priority item with `"passes": false`. That is this session's target. Do not infer completeness from the code: the ledger is the truth (principle #2).

4. **Boot the environment.** Run `./boot.sh`. This script (created once by the initializer, principle #4) starts the dev environment, database, and any services. You should not be figuring out how to start the project from scratch. That is the re-derivation tax this step exists to defeat.

5. **Verify the baseline.** Run the baseline end-to-end check. **If it fails, fixing that breakage is this session's work, not the ledger item you picked in step 3.** Never start a new feature on top of a broken baseline; you will only make the underlying fault harder to isolate.

Only after step 5 passes do you begin the targeted work.

## The exit (principle #3)

Symmetrically, every session ends clean and resumable:

1. Bring the working tree to a coherent, mergeable state (revert any half-applied edits).
2. Update `progress.md`: what you worked on, what you completed, what state you left things in, what the next session should do first.
3. If you verified a ledger item end-to-end, flip its `"passes"` to `true` with a `verified_at` timestamp, otherwise leave it `false`.
4. Commit with a descriptive message.

A session is not "done" until the durable store reflects a clean state. The next session (possibly days later, possibly a different agent) must be able to start from step 1 above without untangling anything.
