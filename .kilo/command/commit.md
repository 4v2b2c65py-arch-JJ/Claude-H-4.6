---
description: Generate a commit message from staged changes
agent: code
subtask: true
---
Generate a concise, conventional commit message from the staged changes.

Run `git diff --cached` and `git diff --cached --stat` to inspect the staged changes.

Rules:
- Use the Conventional Commits format: `type(scope): description`
- Types: feat, fix, chore, docs, style, refactor, test, perf, build, ci
- Keep the subject line under 72 characters
- Add a body with bullet points only when multiple distinct changes exist
- Output only the commit message, no preamble