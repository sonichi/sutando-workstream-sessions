#!/usr/bin/env python3
"""Prove new/resumed/isolated Codex workstream sessions with owner-local fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "task-workstream-sessions" / "scripts" / "session-worker.py"


def write_task(workspace: Path, task_id: str, body: str) -> Path:
    path = workspace / "tasks" / f"{task_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"id: {task_id}\nsource: e2e\naccess_tier: owner\ntask: {body}\n",
        encoding="utf-8",
    )
    return path


def session_fingerprint(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:12]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="retain the temporary fixture")
    args = parser.parse_args()

    sutando = Path(os.environ.get("SUTANDO_REPO", "")).expanduser().resolve()
    if not (sutando / "src" / "team_result_guard.py").is_file():
        raise SystemExit("set SUTANDO_REPO to a compatible Sutando checkout")
    if not shutil.which("codex"):
        raise SystemExit("codex CLI is unavailable")
    if subprocess.run(["codex", "login", "status"], capture_output=True).returncode:
        raise SystemExit("codex CLI is not authenticated")

    root = Path(tempfile.mkdtemp(prefix="workstream-session-e2e."))
    try:
        workspace = root / "workspace"
        project = root / "project"
        results = workspace / "results"
        project.mkdir(parents=True)
        results.mkdir(parents=True)
        (project / "AGENTS.md").write_text(
            "Complete only the supplied verification task. Return the requested exact "
            "answer with no explanation. Do not create task or result files.\n",
            encoding="utf-8",
        )

        nonce = secrets.token_hex(12)
        tasks = [
            write_task(
                workspace,
                "task-alpha-first",
                f"Remember this verification nonce for the workstream: {nonce}. "
                "Reply exactly FIRST_OK.",
            ),
            write_task(
                workspace,
                "task-alpha-resume",
                "Reply with only the verification nonce established in the previous task. "
                "The nonce is intentionally not repeated here.",
            ),
            write_task(
                workspace,
                "task-beta-isolated",
                "Reply exactly ISOLATED if no verification nonce was established earlier "
                "in this conversation; otherwise reply CONTAMINATED.",
            ),
        ]
        assignments = {
            tasks[0].stem: {"workstream_id": "workstream-alpha"},
            tasks[1].stem: {"workstream_id": "workstream-alpha"},
            tasks[2].stem: {"workstream_id": "workstream-beta"},
        }
        data = workspace / "data"
        data.mkdir(parents=True)
        (data / "task-workstreams.json").write_text(
            json.dumps({
                "schema_version": 1,
                "workstreams": {
                    "workstream-alpha": {"title": "Alpha"},
                    "workstream-beta": {"title": "Beta"},
                },
                "assignments": assignments,
            }),
            encoding="utf-8",
        )

        environment = {
            **os.environ,
            "SUTANDO_REPO": str(sutando),
            "SUTANDO_ISOLATED_WORKING_DIR": str(project),
            "SUTANDO_TIER_HARD_TIMEOUT": "300",
            "SUTANDO_TIER_STALL_TIMEOUT": "120",
        }
        for task in tasks:
            command = [
                sys.executable,
                str(WORKER),
                "--runtime", "codex",
                "--workspace", str(workspace),
                "--task-file", str(task),
                "--results-dir", str(results),
                "--repo", str(sutando),
            ]
            completed = subprocess.run(command, env=environment, capture_output=True, text=True)
            if completed.returncode:
                raise RuntimeError(
                    f"{task.name} failed rc={completed.returncode}: {completed.stderr.strip()}"
                )

        first = (results / tasks[0].name).read_text().strip()
        resumed = (results / tasks[1].name).read_text().strip()
        isolated = (results / tasks[2].name).read_text().strip()
        state = json.loads(
            (workspace / "state" / "task-workstream-sessions.json").read_text()
        )["sessions"]["codex"]
        alpha = state["workstream-alpha"]["session_id"]
        beta = state["workstream-beta"]["session_id"]

        checks = {
            "first_result_published": first == "FIRST_OK",
            "same_workstream_resumed": resumed == nonce,
            "different_workstream_isolated": isolated == "ISOLATED",
            "different_session_ids": alpha != beta,
            "run_marks_cleaned": not any(
                (workspace / "state" / "task-workstream-runs").glob("*.started")
            ),
        }
        report = {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "session_fingerprints": {
                "workstream-alpha": session_fingerprint(alpha),
                "workstream-beta": session_fingerprint(beta),
            },
            "sutando_revision": subprocess.run(
                ["git", "-C", str(sutando), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    finally:
        if args.keep:
            print(f"fixture retained at {root}", file=sys.stderr)
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
