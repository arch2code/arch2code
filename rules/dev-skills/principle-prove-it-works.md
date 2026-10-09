---
name: principle-prove-it-works
description: "Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'"
---

# Prove it works

Check the real thing before you call a task done. A file mtime, a cached result, a passing compile or an agent's summary is a proxy, and a proxy can be wrong while the work is broken.

After each task, ask how you would prove it works, then do that:

1. Build it. A clean build is necessary and proves nothing more.
2. Run the feature path you changed, with input that reaches the change.
3. Read the output the change affects, from input to output.

When a check fails, make sure the check itself is sound. A failure that reproduces is real. Do not explain it away.

A delegate's report says what it meant to do. Read its diff and the files it produced.

## Script the check when you can

A deterministic script that re-runs the comparison beats a one-time look. A script that diffs the old and new generated output catches what a glance misses. Write it, run it, and keep the script and its output where the user can see and re-run them. Name that location in your report. Do not stage or commit them. The user decides whether the script belongs in the tree, for example as the audit trail of a large port or migration.

## What counts as proof here

Run the generator to prove a generator change. Reading the template diff is not proof.

- `.gen/builder.stamp` tracks `templates/`, `pysrc/`, `config/*.yaml`, `config/*.py`, `arch2code.py`, and Pro's `templates/` and `config/`. An edit to any of these rebuilds the db and regenerates everything on the next `make`. After an edit to `include/make/`, or to a template kept inside the project tree, run `make clean` first.
- `make gen` succeeding proves the run finished. Read the emitted file to prove its content.
- `make run` proves the SystemC model. It does not touch RTL.
- `make run VL_DUT=1` substitutes only `HDL_TOP_MODULE`. Where a project has `run-vl`, use it to cover every RTL instance. `make lint`, from the project's `rtl/` directory, checks that the RTL compiles.
- Prove a change to shared generator code with `make -C builder push-test`, run from the workspace root without `-j`. It cleans both trees, runs the unit suite, then runs the base and Pro pipelines.
- Never run the unit suite while any example builds. The suite regenerates the examples in place, so the two corrupt each other.
- Use `-j` on other build and gen commands.

<!--
from the `principle-prove-it-works` skill in the pstack plugin,
https://github.com/cursor/plugins/tree/main/pstack, MIT License,
Copyright (c) 2026 Lauren Tan. The MIT permission notice ships with the upstream
repository.
-->
