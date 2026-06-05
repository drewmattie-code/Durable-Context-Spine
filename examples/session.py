#!/usr/bin/env python3
"""
DCS runnable example: durable state and verification-gated 'done' across sessions.
================================================================================

Demonstrates the core Durable Context Spine mechanic end to end, with no
dependencies (stdlib only). Three separate "sessions" run against one durable
ledger on disk. Each session shares NOTHING with the last except that file:

  Session 1  initializes the ledger and completes one task, marking it done
             ONLY after its verification gate passes, then exits clean.
  Session 2  starts fresh, reads the ledger, orients, picks the next pending
             task, does the work, but its verification gate FAILS, so the task
             stays pending. 'Done' is never inferred from the work being done.
  Session 3  starts fresh, sees the task still pending, redoes it correctly,
             the gate passes, and the task is finally marked done.

The point: the context window is disposable; the ledger is the system of record,
and 'done' is a verification-gated entry, never a session's optimistic guess.
Every write is validated against schema/completion-ledger.v1.json. Run:

    python3 examples/session.py

License: MIT
"""

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = HERE.parent / "schema"

_TYPES = {
    "object": dict, "array": list, "string": str,
    "boolean": bool, "number": (int, float), "integer": int,
}


def validate(instance, schema, path="$"):
    errs = []
    t = schema.get("type")
    if t:
        if t in ("number", "integer") and isinstance(instance, bool):
            return [f"{path}: expected {t}, got boolean"]
        if not isinstance(instance, _TYPES[t]):
            return [f"{path}: expected {t}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in {schema['enum']}")
    if t == "object" and isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errs.append(f"{path}: missing required '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errs.append(f"{path}: unexpected property '{key}'")
        for key, sub in props.items():
            if key in instance:
                errs += validate(instance[key], sub, f"{path}.{key}")
    if t == "array" and isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            errs += validate(item, schema["items"], f"{path}[{i}]")
    return errs


SCHEMA_DOC = json.loads((SCHEMA / "completion-ledger.v1.json").read_text())


def load(ledger_path):
    return json.loads(ledger_path.read_text())


def save(ledger_path, ledger):
    errs = validate(ledger, SCHEMA_DOC)
    if errs:
        raise AssertionError(f"ledger failed schema validation: {errs}")
    ledger_path.write_text(json.dumps(ledger, indent=2))


def orient(ledger):
    done = [i for i in ledger["items"] if i["passes"]]
    pending = [i for i in ledger["items"] if not i["passes"]]
    return done, pending


# The "work" each task represents, and whether a given attempt is correct.
# In a real project this is code the agent writes; here it is simulated so the
# verification gate has something deterministic to check.
def do_work(task_id, attempt):
    # chat-history-persists is buggy on its first attempt, correct on the retry
    if task_id == "chat-history-persists" and attempt == 1:
        return {"reload_keeps_messages": False}
    return {"reload_keeps_messages": True, "feature": task_id}


def verify(task_id, result):
    """The verification gate. Returns True only if the behavior actually holds."""
    if task_id == "chat-history-persists":
        return result.get("reload_keeps_messages") is True
    return bool(result.get("feature"))


def run_session(name, ledger_path, attempt_for=None):
    """A fresh session. Its only inheritance is the ledger file on disk."""
    if not ledger_path.exists():
        ledger = {
            "project": "example-chat-app",
            "ledger_version": "1.0",
            "items": [
                {"id": "chat-new-conversation", "category": "functional",
                 "description": "New Chat button creates a fresh conversation",
                 "verification": "browser-e2e", "passes": False},
                {"id": "chat-history-persists", "category": "functional",
                 "description": "Conversation history persists across a page reload",
                 "verification": "browser-e2e", "passes": False},
            ],
        }
        save(ledger_path, ledger)
        print(f"[{name}] initialized ledger ({len(ledger['items'])} items, all pending)")
    else:
        ledger = load(ledger_path)

    done, pending = orient(ledger)
    print(f"[{name}] oriented from disk: {len(done)} done, {len(pending)} pending")
    if not pending:
        print(f"[{name}] nothing left to do, exiting clean")
        return ledger

    task = pending[0]
    attempt = attempt_for or 1
    result = do_work(task["id"], attempt)
    passed = verify(task["id"], result)

    if passed:
        task["passes"] = True
        task["verified_at"] = "2026-06-05T12:00:00Z"
        task.pop("note", None)
        ledger["last_verified_session"] = name
        print(f"[{name}] worked '{task['id']}', verification PASSED -> marked done")
    else:
        task["note"] = "implemented but verification failed; NOT marked done"
        print(f"[{name}] worked '{task['id']}', verification FAILED -> stays pending")

    save(ledger_path, ledger)  # clean, resumable exit
    return ledger


def main():
    ledger_path = pathlib.Path(tempfile.mkdtemp(prefix="dcs-")) / "completion-ledger.json"
    print(f"Durable ledger (system of record): {ledger_path}\n")

    run_session("session-1", ledger_path)
    print()
    run_session("session-2", ledger_path, attempt_for=1)   # buggy attempt, gate fails
    print()
    run_session("session-3", ledger_path, attempt_for=2)   # fixed attempt, gate passes

    final = load(ledger_path)
    done, pending = orient(final)
    print(f"\nFinal ledger: {len(done)}/{len(final['items'])} done, {len(pending)} pending")
    schema_ok = not validate(final, SCHEMA_DOC)
    print(f"Ledger valid against completion-ledger.v1.json: {schema_ok}")
    print("\nWhat this proves: each session oriented purely from the durable file,")
    print("and session 2 could not mark a task done just because it did the work.")
    print("'Done' is a verification-gated entry, which is the whole DCS discipline.")

    all_done = len(pending) == 0
    return 0 if all_done and schema_ok else 1


if __name__ == "__main__":
    sys.exit(main())
