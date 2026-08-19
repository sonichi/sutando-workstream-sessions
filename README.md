# task-workstream-sessions — experimental

An optional executor for owner tasks that Sutando has already assigned to a
workstream. It preserves provider context by maintaining one durable Claude or
Codex session per `(runtime, workstream_id)`.

This repository is public and is not wired into `sonichi/sutando` after
[`sonichi/sutando#3148`](https://github.com/sonichi/sutando/pull/3148). It must
prove itself here before anyone proposes bundling it again.

## Boundary

The architectural contract keeps scheduling policy in one central Sutando
scheduler: global priority, FIFO ordering, lifecycle, leases, dependencies,
supersession, cancellation, workstream assignment, and the final decision to
dispatch a task. Not all of those capabilities exist in Sutando today; this is
the boundary future scheduler work must preserve, not a claim about the current
implementation.

This repository owns execution after that decision:

- resume or create the provider session for the assigned workstream;
- serialize provider runs within one workstream;
- enforce hard and no-progress timeouts;
- retain session IDs and provider-run marks under the workspace;
- publish one result atomically;
- return `UNHANDLED` when isolation is unavailable so owner work can use the
  live-core fallback.

It does not watch the task directory, reorder work, infer priority, classify
workstreams, or decide whether old work has been superseded. Team and Guest
tasks are always `UNHANDLED`; the former Team execution path was removed in
[`sonichi/sutando#3067`](https://github.com/sonichi/sutando/pull/3067).

See [ARCHITECTURE.md](ARCHITECTURE.md) for the adapter and state contracts.

## Reproducible validation

The feature intentionally imports shared authorization policy from Sutando
instead of copying it. `scripts/test.sh` checks out the compatible Sutando
revision recorded in `SUTANDO_COMPAT_REF` unless `SUTANDO_REPO` already
points to a checkout:

```bash
./scripts/test.sh
./scripts/test.sh --coverage
./scripts/test.sh --repeat 5 --coverage
```

The first command is the plain suite. The second exercises the same suite under
coverage. The repeated form is the minimum evidence for the instrumentation
failure that motivated extraction.

To test a different Sutando revision:

```bash
SUTANDO_REPO=/path/to/sutando ./scripts/test.sh --coverage
```

No credential or provider login is needed for the deterministic suite.

With an authenticated Codex CLI, the opt-in live proof creates only temporary
owner-local fixtures and prints sanitized session fingerprints:

```bash
SUTANDO_REPO=/path/to/sutando python3 scripts/e2e_codex.py
```

It proves initial execution, same-workstream resume, different-workstream
isolation, distinct provider sessions, atomic result publication, and run-marker
cleanup. The temporary task bodies and provider session IDs are not printed.

## Opt-in adapter invocation

When configured, Sutando's generic task handler calls the executable twice:
`--probe` first, then without `--probe` when it accepts responsibility.
Standalone invocation must identify the Sutando checkout so the adapter can
import the shared tier policy:

```bash
export SUTANDO_REPO=/path/to/sutando
export SUTANDO_TASK_EVENT_HANDLER="$PWD/task-workstream-sessions/scripts/session-worker.py"
```

This repository deliberately does not modify Sutando launchers or automatically
enable itself. Persistent external-capability configuration is separate from
proving the executor.

## Proof bar

Before reintegration is proposed:

1. the full suite must pass under coverage repeatedly;
2. a real provider task must publish a result end-to-end;
3. a second task in the same workstream must resume the same provider session;
4. a task in another workstream must use a different session; and
5. a provider failure or timeout must leave owner work eligible for live-core
   fallback.

Evidence must name repository revisions and omit credentials and private task
content. Passing this bar provides evidence; it is not automatic approval to
reintegrate.
