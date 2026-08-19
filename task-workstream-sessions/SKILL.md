---
name: task-workstream-sessions
description: Execute scheduler-assigned owner tasks in durable provider sessions isolated by workstream. This optional adapter never schedules, classifies, or runs non-owner work.
user-invocable: false
---

# Task workstream sessions

The skill reads existing owner-task assignments from
`<workspace>/data/task-workstreams.json`; it never classifies tasks or changes
the grouping sidecar. For each assigned owner task it resumes a headless Claude
or Codex provider session dedicated to that workstream and atomically publishes
the final result body. Session IDs live in
`<workspace>/state/task-workstream-sessions.json`, so provider context remains
separate and resumable across core restarts.

The intended architecture keeps priority, dependencies, supersession,
cancellation, and task lifecycle in one central Sutando scheduler. Not all of
those capabilities exist there today. This adapter only executes owner work
made eligible by its caller; it does not scan the queue or create a competing
scheduling rule.

Team and Guest tasks are always unhandled. Ungrouped, invalid, or unavailable
owner assignments also return unhandled so Sutando can use the selected core's
legacy task path. An isolated provider failure remains retryable and may fall
back to that live core through Sutando's generic handler protocol.

Provider runs are serialized per workstream, bounded by hard and no-progress
deadlines, and publish results atomically. Their session IDs and run markers live
under the workspace. Credentials remain owned by the configured provider and
are never persisted by this skill.

This repository is external and experimental after `sonichi/sutando#3148`.
Passing its proof bar does not automatically re-enable or bundle it in Sutando.
