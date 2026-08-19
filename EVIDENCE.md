# Verification evidence

Recorded 2026-08-19 against Sutando revision
`538e5a07aa7135418e516eaea1f62042ac5bd832`. Task contents, nonces, provider
session IDs, credentials, and user data are omitted.

## Repeated coverage execution

Command:

```bash
PYTHON=/path/to/venv/bin/python \
  SUTANDO_REPO=/path/to/sutando \
  ./scripts/test.sh --repeat 5 --coverage
```

Result:

```text
PASS — session-worker.py imports the shared guard and redefines none of its 3 symbols
[1/5] coverage
task workstream session worker tests passed
[2/5] coverage
task workstream session worker tests passed
[3/5] coverage
task workstream session worker tests passed
[4/5] coverage
task workstream session worker tests passed
[5/5] coverage
task workstream session worker tests passed
```

## Real Codex end to end

Command:

```bash
SUTANDO_REPO=/path/to/sutando python3 scripts/e2e_codex.py
```

Sanitized result:

```json
{
  "checks": {
    "different_session_ids": true,
    "different_workstream_isolated": true,
    "first_result_published": true,
    "run_marks_cleaned": true,
    "same_workstream_resumed": true
  },
  "session_fingerprints": {
    "workstream-alpha": "f54237589c23",
    "workstream-beta": "81dc4385a27f"
  },
  "status": "pass",
  "sutando_revision": "538e5a07aa7135418e516eaea1f62042ac5bd832"
}
```

The first task established a random nonce without returning it. A second task
assigned to the same workstream returned that nonce from resumed conversation
context. A third task assigned to a different workstream reported no prior
nonce, and the two workstreams recorded different provider session IDs.
