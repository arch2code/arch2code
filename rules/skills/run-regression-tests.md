---
name: run-regression-tests
description: Authoritative Arch2Code workflow for creating, editing, running, filtering, and triaging regression tests with regrLauncher.py and project make targets. Use when the user mentions regression tests, regrLauncher.py, regression JSON files, make regr, CI regressions, labels, seeds, or JUnit regression reports.
---
# Skill: Run regression tests

## References
*   Launcher documentation: `builder/base/document/source/modules/ROOT/pages/regrLauncher.adoc`.
*   Working example: `examples/apbDecode/rundir` (`regr_apbDecode.json`, `default.json`, `Makefile`).
*   Related skills: `manage-build`, `verify-testbench`, and in A2C Pro, `run-tandem`.

## Running regressions
1.  Run from `rundir/`. `make regr` runs `regrLauncher.py --build` on `regr_<projectName>.json`. A new project's Makefile has this target, but no regression file and no rules file exist until you write them.

    ```text
    cd rundir
    make regr
    ```

2.  Pass launcher options through `REGR_USER_OPTS`. The make target puts them after the regression file, so a group path can come first:

    ```text
    make regr REGR_USER_OPTS="--labels mdl --count 1"
    make regr REGR_USER_OPTS="/hdl_tests/default --labels hdl"
    ```

    `REGR_JOBS` (default 8) sets how many runs go in parallel. Make's own `-j` does not: `make regr REGR_JOBS=4`.

3.  To run the launcher directly, use the builder copy. Add `--build` to run the regression's build step first:

    ```text
    ../builder/regrLauncher.py --build -j8 <regression>.json
    ../builder/regrLauncher.py <regression>.json /model_tests --labels mdl
    ```

4.  Output goes under `regr/` unless `--dir` names another directory.

## Regression file structure
A regression file is JSON with three sections: `session`, `build` and `run`.

```json
{
  "session": { "name": "regr_name", "jobs": 1, "lrp": 0 },
  "build":   { "command": "make -j all VL_DUT=1", "timeout": 120 },
  "run": {
    "command": "build/run <testbench>",
    "args": "",
    "timeout": 240,
    "rules": ["default.json"],
    "count": 1,
    "seed": 0,
    "labels": [],
    "model_tests": {
      "labels+": ["mdl"],
      "test_group": {
        "test_name": {}
      }
    }
  }
}
```

*   Every run needs `session.name`, `session.lrp`, and `command`, `args`, `timeout`, `rules` and `labels` under `run`. `--build` also needs `build.command` and `build.timeout`. A missing key stops the launcher with a `KeyError`, which can come after the build has run. `count` defaults to 1 and `seed` to 0.
*   `session.lrp` sets log retention: 0 keeps every log, 1 deletes the logs of passing runs, 2 deletes every log, 3 deletes passing logs and gzips failing ones, 4 gzips every log.
*   Set an attribute at the highest level it applies to. Child groups and tests inherit it.
*   A key ending in `+` (`args+`, `rules+`, `labels+`) appends to the inherited value. Without `+`, the child replaces it. A `+` key with no parent value to append to raises a `KeyError`.
*   `run.command` is relative to the directory the launcher runs from, normally `rundir/`.

## Adding tests
1.  Read the existing regression file first and keep its grouping style.
2.  Put tests inside a `test_group`. A `test_group` holds only tests.
3.  Use nested groups for categories such as `model_tests`, `hdl_tests` or a block name.
4.  Give each test its own arguments with `args+`. To run one test of a testbench that declares its tests with `testController`, pass `--test <name>`. See `verify-testbench` for which tests can run alone, and for why a run that cannot complete a test fails or hangs.

    ```json
    "test_group": {
      "rdy_vld": { "args+": "--test test_rdy_vld" },
      "req_ack": { "args+": "--test test_req_ack" }
    }
    ```

5.  An RTL test needs `VL_DUT=1` in the build command and `--vlInst <path>` in its arguments; see `verify-cosimulation`. A tandem test also needs `--vlType model|verif` and `--vlTandem`; see `run-tandem` (A2C Pro).
6.  Give tests labels to select them by. `examples/apbDecode` uses `mdl` and `hdl`.

## Seeds, counts and filters
*   `seed` is a number, a list, or `"random"`, which gives each run a random 32-bit seed.
*   For each run the launcher replaces `${RL_SEED}` in `run.command` and `run.args` with that run's seed. The started process does not get `RL_SEED` in its environment. `build/run` reads the seed only from its `--seed` option, so `run.args` must pass it: `"args": "--seed ${RL_SEED}"`. The shipped example regression files do not, so their runs ignore `seed` and use the simulator's default.
*   With a seed list, `count` caps the runs, so the default count of 1 runs only the first seed. `--count 0` runs every seed in the list. With a single seed, `--count 0` queues nothing and the launcher exits 1.
*   `--count N` overrides the top-level `run.count`. A group or test that sets its own `count` keeps it.
*   `--labels a,b` keeps tests that carry both `a` and `b`. `--labels a,~unstable` keeps tests labelled `a` and drops those labelled `unstable`. `examples/apbDecode` has no `unstable` label, so this one only illustrates the syntax. The launcher drops a label that no test carries and prints a warning, so a misspelt label filters nothing.
*   The optional positional group selects tests whose path starts with it. Paths start with `/`, for example `/model_tests` or `/hdl_tests/default`. Without the leading `/` nothing matches, the queue is empty and the launcher exits 1. Shell-style wildcards also work.
*   To run one test with one fixed seed, set the positional group to the test's full path and add `--attr run.seed=42`. In `examples/apbDecode`, first add `--seed ${RL_SEED}` to `run.args`, then run `/hdl_tests/default/blockA --attr run.seed=42`. The group matches by prefix, so it also selects any test whose path extends this one. `run.seed` always exists at the top level, so `--attr` accepts it. A group or test that sets its own `seed` keeps it; give that test `"seed": 42` instead.
*   `--seq` queues all runs of one test before the next test. The default is round-robin.
*   `--attr <section>.<key>=<value>` overrides a key that already exists at the top level of `session`, `build` or `run`, and `<key>+=` appends to it. It ignores an unknown key with a warning. `--attr` takes every argument after it up to the next option but applies only the first. Give one assignment per `--attr`, and never put the regression file or group directly after it.

## Rules and failure triage
Rules files parse each run's log. `examples/apbDecode/rundir/default.json` is a working rules file to copy.

*   A rules file has `name`, `filters` and `modifiers`. All three are required, and `modifiers` may be `{}`. Each filter has `re`, `msg`, `file` and `sev`.
*   `sev` is `info`, `warning`, `error` or `fatal`. An `error` or `fatal` match fails the run even when the process exits 0. `info` and `warning` matches never fail it.
*   A nonzero exit, a timeout at `run.timeout`, or a missing command always fails the run, whatever the filters say. A run that hangs ends at its timeout and fails.
*   `modifiers` rewrite failure messages so repeated failures group together.
*   `"rules": []` is accepted. The run's result then comes from its exit status alone.
*   A relative `rules` entry resolves against the directory of the regression file, not the directory the launcher runs from. The same holds for files given with `--attr run.rules=<file>` or `--attr run.rules+=<file>`.

After a run, inspect:

```text
regr/<session.name>.<user>.<date-time>.<pid>/build.log
regr/<session.name>.<user>.<date-time>.<pid>/runs/<group path>/<test>/run_<n>/<test>.log
regr/<session.name>.<user>.<date-time>.<pid>/test-reports/junit.xml
```

With `lrp` set to 1 or above, some of those logs are deleted or gzipped; see `session.lrp` above.

## Constraints
*   Never hand-edit generated regions to make a regression pass. Fix the YAML, model, RTL, templates or testbench, then regenerate and rebuild.
*   Do not add fallback logic to tests or rules that hides failures.
*   Keep regression changes small and label-selectable so users can run focused subsets.
*   When changing a regression, keep its labels and group paths unless the user asks to reorganize them.
