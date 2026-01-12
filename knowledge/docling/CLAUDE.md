# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent & Subagent Workflow Rules

IMPORTANT:
- Agents and subagents must be used to control scope, cost, and complexity.
- read docs/integration for latest agent workflow contract, migrations steps and status - 

### When to Use Subagents
- Use subagents for their intended purposes as in the subagent mission
- use MCP as need - specifically mcp__serena__*  for codebase understanding and impact analysis, and mcp__context7__* for documentation/troubleshooting
- Do NOT use subagents for final decisions, projectplan tracking, or project-wide planning.
- If the subagent task is long-running, maintain updates and inter-agent communciations as part of status.md file with the current progress and next steps. Main agent (you) should not rely on reading the full execution log for state.

### Collaboration Model
- Subagents collaborate ONLY through shared artifacts:
  - docs/integration/CONTRACT.md
  - docs/integration/STATUS.md
  - shared types and integration tests
- Subagents must NOT negotiate behavior in chat.
- If behavior is unclear, write a question to STATUS.md.

### Output Discipline
- Subagents must return:
  - a concise summary
  - files changed or created
  - verification steps
- Do NOT paste large logs, code dumps, or raw reasoning into the main thread.

### Authority
- The main agent (this session) is the final decision-maker.
- Subagents propose; the main agent approves and integrates.

## Token Budget & Context Discipline

IMPORTANT:
Tokens are a shared, finite resource. Claude must actively manage context size.

### Budget Priorities (Highest → Lowest)
1. Current task goal and approved plan
2. Integration contracts and shared types
3. Minimal code required for the change
4. Summaries of prior work (not raw history)

### Rules
- Prefer summaries over raw logs, code, or transcripts.
- Never paste large logs or files into the main thread if a subagent can analyze them.
- Do not restate previously agreed plans or contracts unless they change.
- Avoid reloading files that have already been summarized.
- If writting markdown file/memory/overview - write into /docs folder with hierchichal naming convention

### Subagent Token Discipline
- Use subagents for any task that:
  - requires reading many files
  - involves long logs or traces
  - explores multiple options
- Subagents must return:
  - a concise summary (≤15 bullets when possible)
  - file paths or artifacts created
  - verification steps
- Do NOT merge raw subagent reasoning or large excerpts into main context.

### Phase-Based Spending
- Planning phase: allow deeper reasoning, but stop once a plan is approved.
- Execution phase: minimize explanation; follow the plan exactly.
- Debugging phase: reason locally about the failure; avoid global re-analysis.

### Context Reset Guidance
- If context becomes cluttered or unfocused:
  - Prefer `/compact` to retain a summary.
  - Use `/clear` when switching to an unrelated task.
- Final decisions and outcomes should be recorded in docs, not relied on from chat history.

### Anti-Patterns to Avoid
- Re-planning during execution
- Re-explaining architecture during debugging
- Keeping exploratory dead ends in context
- Using high-reasoning behavior for mechanical tasks


## Project Overview

Zoocari is a voice-first, kid-friendly zoo Q&A chatbot for Leesburg Animal Park. It uses RAG (Retrieval-Augmented Generation) with a LanceDB vector database to provide accurate, hallucination-free responses about animals for children ages 6-12.

always respond in a very concise and direct manner, providing only relevant information. 

**Repository:** https://github.com/rodrigjm/zoogpt.git


## Important Constraints

- Python 3.12+ required for Kokoro compatibility
- HTTPS required for browser microphone access in production
- LanceDB must be built before running chatbot
- Vector database stored in `data/zoo_lancedb/`
