---
name: run-regression-tests
description: Authoritative Arch2Code workflow for creating, editing, running, filtering, and triaging regression tests with regrLauncher.py and project make targets. Use when the user mentions regression tests, regrLauncher.py, regression JSON files, make regr, CI regressions, labels, seeds, or JUnit regression reports.
---
# Skill: Run Regression Tests

## Purpose

Guide creation and execution of Arch2Code regression tests using the regression launcher. Prefer the project `make regr` target when it exists; use `regrLauncher.py` directly only when the project has no wrapper or the user needs an explicit launcher command.

## References

* Official launcher docs: `builder/base/document/source/modules/ROOT/pages/regrLauncher.adoc`
* Local examples: project regression JSON files, rules files, and `rundir/Makefile`
* Related skills: `manage-build`, `run-tandem`, `verify-testbench`

## Running Regressions

1. Run commands from `rundir` unless the project Makefile says otherwise.
2. Prefer the local wrapper:

   ```text
   cd rundir
   make regr
   ```

3. Pass launcher options through `REGR_USER_OPTS`:

   ```text
   make regr REGR_USER_OPTS="--labels mdl,~unstable --count 1"
   make regr REGR_USER_OPTS="hdl_tests/default --labels hdl --attr session.lrp=1"
   ```

4. If invoking the launcher directly, use the builder copy and include `--build` when the regression build step should run:

   ```text
   ../builder/regrLauncher.py --build -j8 <regression>.json
   ../builder/regrLauncher.py --labels tandem,~unstable <regression>.json model_tests/tandem
   ```

5. `--dir` defaults to `regr/` in the current launcher. Override it when a specific output location is required.

## Regression File Structure

Regression files are JSON. The root containers are `session`, `build`, and `run`.

```json
{
  "session": {
    "name": "regr_name",
    "jobs": 1,
    "lrp": 0
  },
  "build": {
    "command": "make -j all VL_DUT=1",
    "timeout": 120
  },
  "run": {
    "command": "build/run <testbench>",
    "args": "",
    "timeout": 240,
    "rules": ["default.json"],
    "count": 1,
    "seed": 0,
    "labels": [],
    "group_name": {
      "labels+": ["mdl"],
      "test_group": {
        "test_name": {}
      }
    }
  }
}
```

Use `command`, `args`, `timeout`, `rules`, `count`, `seed`, and `labels` at the highest hierarchy level where they apply. Child groups and tests inherit parent attributes.

## Adding Tests

1. Read the existing regression JSON before editing and preserve its grouping style.
2. Add new tests under a `test_group`; `test_group` is a leaf container and should contain only tests.
3. Use nested groups to represent categories such as `model_tests`, `hdl_tests`, `tandem`, or block names.
4. Use `args+`, `rules+`, and `labels+` to append to inherited values. Without `+`, the child replaces the inherited value.
5. Keep run commands relative to `rundir` when the regression is launched from `rundir`.
6. For tandem tests, set the correct `--vlInst`, `--vlType model|verif`, and `--vlTandem`; consult `run-tandem` for instance path rules.
7. For HDL or RTL/model tests, make sure the build command enables the needed Verilator or simulator flow, typically `VL_DUT=1`.
8. Use labels deliberately. Common labels include `mdl`, `hdl`, `tandem`, `delay`, and `unstable`.

## Seeds, Counts, And Filters

* `--count N` overrides `run.count`; `--count 0` lets a seed list determine run count.
* `seed: "random"` gives each queued run a random 32-bit seed.
* `seed: [1, "0xabcd1234"]` queues fixed seed runs.
* Reference the resolved seed in commands with `${RL_SEED}`.
* `--labels a,b` includes tests with matching labels.
* `--labels a,~unstable` includes label `a` and excludes label `unstable`.
* The optional positional `group` selects a hierarchy path, for example `model_tests/tandem`.
* `--seq` queues all runs for a test before moving to the next test; default scheduling is round-robin.

## Rules And Failure Triage

Rules files parse logs after each run. Use `default.json` unless a project-specific rule file is required.

* A rules file has `name`, `description`, `filters`, and `modifiers`.
* `filters` match log patterns and classify severity as `info`, `warning`, `error`, or `fatal`.
* `modifiers` normalize failure messages so repeated failures group together.
* If an `error` or `fatal` filter matches, the run fails even if the process exits with status 0.
* If no filter matches, a nonzero exit status or timeout fails the run.

After a run, inspect:

```text
regr/<session.name>.<user>.<date-time>.<pid>/build.log
regr/<session.name>.<user>.<date-time>.<pid>/runs/**/<test>.log
regr/<session.name>.<user>.<date-time>.<pid>/test-reports/junit.xml
```

## Constraints

* Do not hand-edit generated source to make a regression pass; fix YAML, model, RTL, templates, or testbench sources and regenerate/build normally.
* Do not add broad fallback logic to tests or rules to hide failures.
* Keep regression changes small and label-selectable so users can run focused subsets locally.
* When changing existing regressions, preserve current labels and group paths unless the user explicitly asks to reorganize them.
