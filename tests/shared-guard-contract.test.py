#!/usr/bin/env python3
"""The worker must IMPORT the shared team-result guard, never restate it.

Ported from sonichi/sutando `tests/team-result-guard.test.py` when this skill was
extracted (PR #3148). That file asserted this contract over both the Discord bridge
and this worker; removing the worker from that repo removed the worker half, so the
four assertions below would otherwise have been silently dropped.

The policy this protects is CLAUDE.md's: one owner defines the guard, adapters bind
it. A copy that drifts is the failure mode.

Run: python3 tests/shared-guard-contract.test.py    (exit 0 pass, 1 fail)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKER = REPO / "task-workstream-sessions" / "scripts" / "session-worker.py"


def main() -> int:
    if not WORKER.exists():
        print(f"FAIL: missing {WORKER}")
        return 1
    src = WORKER.read_text()
    fails = []

    # Consumers import the policy, never restate it.
    for pattern, what in (
        (r"^\s*TEAM_RESULT_CONTROL\s*=\s*re\.compile", "TEAM_RESULT_CONTROL"),
        (r"^class TeamResultLeakError", "TeamResultLeakError"),
        (r"^def resolve_access_tier", "resolve_access_tier"),
    ):
        if re.search(pattern, src, re.M):
            fails.append(f"session-worker redefines {what} instead of importing it")

    if "from team_result_guard import" not in src:
        fails.append("session-worker must import the shared guard")

    for f in fails:
        print(f"FAIL: {f}")
    if fails:
        return 1
    print(f"PASS — {WORKER.name} imports the shared guard and redefines none of its 3 symbols")
    return 0


if __name__ == "__main__":
    sys.exit(main())
