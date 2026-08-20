# Architecture

## Role in the task pipeline

```text
owner request                         opted-in AG2 Space room request
    ↓                                             ↓
future central Sutando scheduler      broker-authored session_scope: room
  priority · lifecycle · dependencies · supersession · cancellation
    ↓ approved dispatch                           ↓
generic SUTANDO_TASK_EVENT_HANDLER protocol
    ↓
workstream-session executor
  assignment/room key · per-session lock · provider resume/new · atomic result
    ↓
Sutando result delivery
```

This diagram describes the intended contract, not a claim that every listed
scheduler capability exists in Sutando today. The executor is downstream of
scheduling. It may reject a dispatch, serialize execution, or fail safely, but
it must not choose a different task to run.

## Adapter contract

`session-worker.py` supports the generic Sutando handler arguments:

- `--runtime`: `claude` or `codex`;
- `--workspace`: owner workspace containing task, assignment, state, and result
  directories;
- `--task-file`: one scheduler-selected task under `<workspace>/tasks`;
- `--results-dir`: the caller-resolved result directory;
- `--repo`: the compatible Sutando checkout used by provider prompts/tools;
- `--probe`: eligibility check with no provider side effects.

Exit `0` means handled or eligible. Exit `3` (`UNHANDLED`) returns the task to
Sutando's owner fallback. Other exits are retryable handler failures. Team and
Guest tasks always return `UNHANDLED` before any provider launch.

An AG2 Space room is eligible only when the broker supplies exact
`session_scope: room` metadata on an owner task with a valid Matrix room ID.
The executor hashes that ID into one stable session key. All messages from the
same room share the key and persisted provider session; different rooms do not.
Absent or invalid opt-in metadata returns `UNHANDLED` and preserves the legacy
path.

The adapter imports `resolve_access_tier` from Sutando's
`src/team_result_guard.py`. `SUTANDO_REPO` resolves that dependency when the
feature is external; parent-checkout discovery remains for a future installed
skill. Shared policy is never copied here.

## Durable state

All mutable data remains owner-local under the selected workspace:

- `data/task-workstreams.json`: scheduler/classifier-owned assignments, read only;
- `state/task-workstream-sessions.json`: session IDs keyed by runtime and stable workstream/room key;
- `state/task-workstream-session-locks/`: one provider run per stable session key;
- `state/task-workstream-runs/`: provider start markers for health monitoring;
- `results/`: atomic publish-once result files owned by the normal delivery path.

The executor rechecks for an existing result after acquiring the workstream
lock. That closes the wait-time race without making this component a scheduler.

## Failure semantics

Provider processes have hard and no-progress deadlines and run in their own
process group. On failure, the process group is terminated and no partial
stdout becomes a result. For owner work the generic handler can then fall back
to the live core, with the documented possibility of at-least-once retry.

The executor does not persist credentials. Provider authentication and runtime
configuration remain in the owner's existing Claude or Codex installation.

## Future scheduler integration

Task relationships such as `depends_on` and `supersedes` belong in Sutando's
central scheduler. That scheduler should validate a task before dispatch and at
lifecycle boundaries. This executor should consume the approved dispatch and,
when a versioned cancellation/lease contract exists, revalidate it before the
provider launch and before result publication. It must not invent a second
relationship schema locally.
