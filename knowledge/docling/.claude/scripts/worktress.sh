#!/usr/bin/env bash
set -euo pipefail

# scripts/worktrees.sh
# Usage:
#   ./scripts/worktrees.sh init <topic> <n>
#   ./scripts/worktrees.sh add <name> <branch>
#   ./scripts/worktrees.sh list
#   ./scripts/worktrees.sh rm <name>
#
# Creates worktrees under ./trees/<name>

ROOT="$(git rev-parse --show-toplevel)"
TREES_DIR="${ROOT}/trees"

cmd="${1:-}"
shift || true

mkdir -p "$TREES_DIR"

add_worktree () {
  local name="$1"
  local branch="$2"
  local dir="$TREES_DIR/$name"

  if [[ -d "$dir" ]]; then
    echo "exists: $dir" >&2
    exit 1
  fi

  git worktree add "$dir" -b "$branch"
  echo "added: $dir  (branch: $branch)"
}

case "$cmd" in
  init)
    topic="${1:?topic required}"
    n="${2:?n required}"
    for i in $(seq 1 "$n"); do
      add_worktree "${topic}-${i}" "${topic}-${i}"
    done
    ;;
  add)
    name="${1:?name required}"
    branch="${2:?branch required}"
    add_worktree "$name" "$branch"
    ;;
  list)
    git worktree list
    ;;
  rm)
    name="${1:?name required}"
    dir="$TREES_DIR/$name"
    git worktree remove "$dir"
    echo "removed: $dir"
    ;;
  *)
    echo "Unknown command. Try: init|add|list|rm" >&2
    exit 1
    ;;
esac
