---
name: context-token-optimizer
description: >-
  Techniques for context window curation, token efficiency, surgical code inspections
  with StartLine/EndLine, log verbosity suppression, and preventing context degradation.
  Use when reading large codebases, running noisy commands, or managing token budgets.
---

# Context & Token Optimizer

Operational guidelines to preserve model context, eliminate token waste, and maintain reasoning accuracy across complex sessions.

## 1. Surgical Code Inspections

- **Never read entire large files**: Instead of viewing 800 lines indiscriminately, locate the exact target with `grep_search` or `find_by_name`, then inspect using `StartLine` and `EndLine` bounded to a 30-80 line range.
- **Deduplication over Repetition**: Once a class, schema, or route signature is examined, record its interface in your intermediate thoughts or notes instead of re-reading the file across multiple turns.
- **Targeted Diff Inspections**: When checking changes, run `git diff -U3` or target specific files rather than dumping entire unfiltered multi-commit diffs.

## 2. Command Output & Log Hygiene

- **Suppress Verbose Test Outputs**:
  - Use `pytest -q --tb=short` or filter by test node: `pytest backend/tests/test_x.py::test_specific -v`.
  - Avoid flags that print full tracebacks for passing tests.
- **Filter Compiler & Linter Streams**:
  - When compiling C with GCC, pipe through focused filters or use `-fmax-errors=5`.
  - When running Ruff or Bandit, use summary flags or target specific paths.
- **Log Truncation & Paging**:
  - Always append `| Select-Object -First 30` or `| head -n 30` on exploratory terminal commands that may emit hundreds of lines.

## 3. Cognitive State & Token Pruning

- **Atomic Intermediate Summaries**: Condense multi-step research findings into concise bullet points before initiating complex code edits.
- **Avoid Echoing Large Blobs**: Do not re-state large code blocks or entire specs in responses to the user when referencing files by clickable URI is sufficient.
- **Ephemeral Scratch Usage**: Store scratch data or one-off validation scripts in temporary paths rather than filling conversation transcripts.
