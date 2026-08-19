#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE=plain
REPEAT=1

usage() {
  echo "usage: $0 [--coverage] [--repeat N]" >&2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --coverage) MODE=coverage ;;
    --repeat)
      shift
      [ $# -gt 0 ] || { usage; exit 2; }
      REPEAT="$1"
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
  shift
done

case "$REPEAT" in
  ''|*[!0-9]*|0) echo "--repeat must be a positive integer" >&2; exit 2 ;;
esac

PYTHON_BIN="${PYTHON:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "python is unavailable: $PYTHON_BIN" >&2
  exit 127
}

RUN_TMP="$(mktemp -d "${TMPDIR:-/tmp}/workstream-sessions-test.XXXXXX")"
cleanup() { rm -rf "$RUN_TMP"; }
trap cleanup EXIT INT TERM

SUTANDO_CHECKOUT="${SUTANDO_REPO:-}"
if [ -z "$SUTANDO_CHECKOUT" ]; then
  SUTANDO_CHECKOUT="$RUN_TMP/sutando"
  COMPAT_REF="$(tr -d '[:space:]' < "$ROOT/SUTANDO_COMPAT_REF")"
  git init -q "$SUTANDO_CHECKOUT"
  git -C "$SUTANDO_CHECKOUT" remote add origin https://github.com/sonichi/sutando.git
  git -C "$SUTANDO_CHECKOUT" fetch -q --depth 1 origin "$COMPAT_REF"
  git -C "$SUTANDO_CHECKOUT" checkout -q --detach FETCH_HEAD
fi
SUTANDO_CHECKOUT="$(cd "$SUTANDO_CHECKOUT" && pwd -P)"
if [ ! -f "$SUTANDO_CHECKOUT/src/team_result_guard.py" ]; then
  echo "not a compatible Sutando checkout: $SUTANDO_CHECKOUT" >&2
  exit 2
fi
export SUTANDO_REPO="$SUTANDO_CHECKOUT"

"$PYTHON_BIN" "$ROOT/task-workstream-sessions/scripts/session-worker.py" --help >/dev/null
"$PYTHON_BIN" "$ROOT/tests/shared-guard-contract.test.py"

if [ "$MODE" = coverage ]; then
  "$PYTHON_BIN" -m coverage --version >/dev/null 2>&1 || {
    echo "coverage is unavailable; install requirements-dev.txt" >&2
    exit 2
  }
fi

run=1
while [ "$run" -le "$REPEAT" ]; do
  echo "[$run/$REPEAT] $MODE"
  if [ "$MODE" = coverage ]; then
    export COVERAGE_FILE="$RUN_TMP/.coverage.$run"
    "$PYTHON_BIN" -m coverage run --branch \
      "$ROOT/tests/task-workstream-session-worker.test.py"
  else
    "$PYTHON_BIN" "$ROOT/tests/task-workstream-session-worker.test.py"
  fi
  run=$((run + 1))
done
