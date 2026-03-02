Initialize parallel worktrees.

Steps:
1) Run: `./scripts/worktrees.sh init $ARGUMENTS`
2) Then list worktrees: `./scripts/worktrees.sh list`
3) Remind user:
   - run separate Claude Code sessions inside each ./trees/<name>
   - avoid shared ./data writes across worktrees unless isolated
