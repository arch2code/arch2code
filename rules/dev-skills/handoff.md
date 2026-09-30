---
name: handoff
description: Compact the current conversation into a handoff prompt for a fresh agent to pick up. Invoke explicitly with /handoff before starting a new session.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff prompt summarising the current conversation so a fresh agent can continue the work.

Print it in the reply as one fenced block the user can copy. Do not write it to a file.

Do not duplicate content already captured in other artifacts (plans, schema docs, issues, commits, diffs). Reference them by path instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the prompt accordingly.

## Required contents

State each of these, because the next agent starts with none of them:

- **Where.** Working directory, and the submodule if the work is under one. `builder/base` and `builder/pro` are separate git repos.
- **Branch.** Name it. Say whether changes are staged, committed, or pushed.
- **Skills to load first.** Name the skills the next agent must call the Skill tool for before editing, and say to load them before reading or editing anything. Use the routing table in `CLAUDE.md` to pick them.
- **The plan and the stage.** Path to the plan file under `builder/base/plans/`, and which stage or item comes next. Do not restate the stage; the plan holds it.
- **What just landed.** One or two lines on the state the previous session left, including anything half-finished.
- **How to verify.** The exact make target that proves the work, with `-j`.

Leave out anything the plan file already says. A handoff that restates the plan is a handoff that goes stale the moment the plan is updated.

<!--
Adapted from the `handoff` skill in https://github.com/mattpocock/skills,
MIT License, Copyright (c) 2026 Matt Pocock. The MIT permission notice ships
with the upstream repository.
-->
