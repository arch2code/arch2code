---
name: migrate-project
description: Migrate an existing arch2code project to the current authoring format using `make migrate` (eval Python→SV, addressControl→per-block, include header→cppm modules) and resolve every manual item the tool reports. Use whenever a project fails the projectCreate yamlFormat gate, still pins context includes to header mode, or the user asks to run/finish a project migration.
---
# Skill: Project Migration

This is the single operational guide for migrating an arch2code project. It
supplements the programmatic migration: the tool (`make migrate`) does every
mechanical edit, and this skill explains how to invoke it and resolve the items
it can only report.

## 1. Run the tool

```text
make migrate
```

`make migrate` wraps `migrateYaml.py --write <project.yaml>`. It is a standalone,
text-only converter (it never opens the database) and is idempotent — re-running
a fully migrated project is a no-op. It runs these phases over the project's YAML
file set and prints one combined report:

- **Phase A — eval Python→SV.** Rewrites Python-syntax `eval` strings into the
  frozen SV subset (for example `($X-1).bit_length()` → `$clog2($X)`).
- **Phase B — addressControl → per-block.** Emits `addressBlock:` on each
  resolved router, moves policy sections to `project.yaml`, normalizes
  `postProcess:`, removes the `addressControl:` pointer, and deletes the legacy
  `addressControl.yaml` when clean.
- **Includes — include header → cppm module.** Removes a legacy
  `fileGeneration.fileMap` `include` override (paired `.h`/`.cpp`) so the project
  inherits the base `cppm` module-interface definition, and deletes the orphaned
  generated `<context>Includes.{h,cpp}` files. The firmware
  `<context>IncludesFW.{h,cpp}` files are left in place (firmware headers remain
  header mode by design). This conversion is part of `yamlFormat: 2`; it runs
  before the stamp short-circuit so a project stamped before the phase existed
  still has its includes migrated.
- **Phase C — stamp.** Writes `yamlFormat: 2` only when Phases A, B, and the
  includes phase all leave no manual work.

A `--write` run returns non-zero while any manual item remains, so `make migrate`
does not report success on a project that still fails to build.

## 2. Read the report

Applied edits are listed under `applied:`. Items the tool cannot complete are
listed under `manual TODO:` as:

```text
<file>:<line>  <KIND>  <message>
```

Resolve every reported item, complete the recreation steps below if the includes
phase ran, then re-run `make migrate` to confirm a clean report.

### Manual-TODO kinds

| Tool report `KIND` | Meaning | Resolve with |
| --- | --- | --- |
| `TODO_ROUTER_RESOLUTION` | An `AddressGroups` row's router cannot be resolved. | `address-migration` skill, Step 3 |
| `TODO_INTERFACE_SCOPE` | A router has no `addressBus: true` interface in its load-time scope. | `address-migration` skill, Step 2 |
| `TODO_LEAF_REGISTER_PORTS` | A routed leaf needs `registerPorts:`. | `address-migration` skill, Step 4 |
| `TODO_USER_IMPORT` | Hand-written user code `#include`s a migrated context header. | Section 3 below |
| eval `NEEDS_MANUAL` | A real-valued eval (e.g. `$DWORD / 2.0`) cannot be expressed in the SV subset. | Replace the `eval:` with a literal `value:` (hand decision). |

The address-control kinds are documented in depth in the `address-migration`
skill; the converter messages point at its step numbers.

## 3. Finish an includes (header → cppm) migration

When the report shows an `Includes` phase that applied edits, the project moved
from paired-header context includes to C++20 module interfaces. The tool deleted
the stale generated `.h`/`.cpp`; you must recreate the module interface and fix
any hand-written code.

1. **Recreate the module interfaces.** `newmodule` is create-only (it never
   deletes); it writes the missing `.cppm` from the current file map:

   ```text
   make clean      # rebuild the database from the migrated project.yaml
   make newmodule  # create the <context>Includes.cppm module interfaces
   make gen        # fill the generated regions
   ```

2. **Fix `TODO_USER_IMPORT` sites.** A hand-written source file that does:

   ```cpp
   #include "<context>Includes.h"
   ```

   must instead import the module. The module name is the context stem without
   the `Includes` suffix and its namespace is `<module>_ns` (see the top of the
   generated `<context>Includes.cppm`: `export module <module>;` /
   `export namespace <module>_ns`). For example a file that included
   `axi4sDemo_tbIncludes.h` becomes:

   ```cpp
   import axi4sDemo_tb;
   using namespace axi4sDemo_tb_ns;
   ```

   Generated files (those carrying `GENERATED_CODE_BEGIN`) are **not** reported —
   `make gen` rewrites their include into an `import` automatically. Only
   user-authored files need this edit.

3. **Clear stale build artifacts.** A prior header-mode build leaves `.d`
   dependency files that reference the deleted `.h`. The example `clean` target
   removes only the database and `.gen`, not the rundir build tree, so a stale
   `.d` can break the next build with `No rule to make target ...Includes.h`.
   Remove the rundir build tree before rebuilding:

   ```text
   rm -rf <project>/rundir/build
   ```

4. **Verify.** Rebuild and run the project's normal targets (for example
   `make -C <project>/rundir all run`). A clean build and run confirms the
   migration.

## References

- `make migrate` / `migrateYaml.py` — the unified orchestrator.
- `pysrc/evalPyToSv.py` (Phase A), `pysrc/migrateAddressControl.py` (Phase B),
  `pysrc/migrateIncludes.py` (Includes phase) — the phase libraries.
- `address-migration` skill — the in-depth reference for the address-control
  manual-TODO kinds.
- `manage-build` skill — `make` targets (`db`, `gen`, `newmodule`, `clean`).
