# task-workstream-sessions — EXPERIMENTAL

> **Status: experimental. Not wired into the public `sonichi/sutando` repo.**
> Extracted 2026-08-19 so it can be iterated on without gating anyone's CI.

Runs opted-in Team tasks and assigned owner work in bounded provider sessions,
via `SUTANDO_TASK_EVENT_HANDLER`.

## Why it was extracted

- Its test (`tests/task-workstream-session-worker.test.py`) fails **deterministically under
  coverage** — measured 2026-08-19 on macOS: `plain 8/8 pass`, `coverage 0/3 pass`. Because
  `sonichi/sutando` runs a `diff coverage >= 95% (python)` lane, that turned into a recurring
  red check on PRs whose diffs could not reach this code.
- `#3067` had already removed the Team execution path as unreachable-after-`probe()`.
- On the host it was measured, it had **never recorded a session** —
  `state/task-workstream-sessions.json` was absent while sibling state files were current.

None of that means it is worthless; it means it should prove itself somewhere that isn't
the critical path.

## Re-integration bar

Do not re-add to the public repo until:
1. the test passes under coverage, repeatedly, and
2. there is evidence of it actually handling a task end-to-end.

## Deliberately no CI here

This repo is private, and private-repo Actions minutes are billed per job. Add workflows
only when someone decides to spend that budget.
