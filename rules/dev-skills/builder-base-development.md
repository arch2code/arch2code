---
name: builder-base-development
description: Guidance for modifying Arch2Code builder/base internals, including generator control flow, database/view ownership, template rendering boundaries, and internal code conventions. Use when editing or reviewing files under builder/base.
---

# Builder Base Development

Use this skill when changing Arch2Code internals under `builder/base`, especially generator, template, schema, project database, and Python support code.

## Core Rules

1. Ask before changing behavior when the ownership, data contract, or intended architecture is unclear.
2. Keep changes scoped to the requested behavior. Do not refactor unrelated code while touching generator internals.
3. Prefer the simplest direct implementation that matches existing builder patterns.
4. Do not edit generated regions by hand. Change the data creation, view helper, template, or generator logic, then rerun the normal make target.

## Generator Control Flow

Normal project use is split into database creation and generator execution.

1. `projectCreate` builds durable project state.
   - Entry point: `arch2code.py` with both `--yaml` and `--db`.
   - Implementation owner: `pysrc/processYaml.py::projectCreate`.
   - Put accepted YAML migration, validation, normalization, schema population, address calculation, post-processing, expensive project-wide derivations, and persisted config here.
   - Persist non-schema project state through the DB-backed `config` object.
2. `projectOpen` opens the database read-only for generators.
   - Entry point: `arch2code.py --readonly --db ...` or a mode that supplies only `--db`.
   - Implementation owner: `pysrc/processYaml.py::projectOpen`.
   - Put template-facing, language-neutral views here, such as `getBlockData()`, `getContextData()`, and narrowly scoped helper views.

The SQLite database is the communication channel between these steps. Generators should assume YAML parsing already happened and should read through DB-backed data, config, and view helpers.

## Template Rendering Boundaries

`projectCreate.configTemplates()` selects and expands the merged `templates:` map from `project.yaml`, then persists it as `TEMPLATES`. Later generator invocations must load that saved mapping.

Do not re-merge project YAML, search alternate template directories, synthesize missing mappings, or add generator fallback paths. If a mapping is missing, fix `projectCreate` validation or configuration.

Template utility modules, including `pysrc/intf_gen_utils.py`, are render helpers, not semantic view builders. They may format SystemC/SystemVerilog spelling, choose local syntax, and iterate fields already supplied by `projectOpen` views.

If code needs to walk `prj.data` across blocks, instances, ports, connections, variants, or interface definitions to derive a reusable fact, add that fact to a `projectOpen` view helper. The template or template utility should consume the precomputed field directly.

## Where Changes Belong

- Put project-wide truth derived from YAML, schema, address calculation, or post-processing in `projectCreate`.
- Put language-neutral reshaping for one rendering context in a `projectOpen` view helper.
- If view creation needs interface-specific facts, prefer `interface_defs` and the corresponding interface YAML over hard-coded special cases.
- If a task appears to require schema changes, pause for any needed user input about the data contract and follow `config/SCHEMA_SPECIFICATION.md`.
- Keep language-specific syntax, emitted code structure, and output formatting in templates or template utilities.
- Before adding a template input, check whether it already exists in `prj.data` or an existing view.
- Do not reparse YAML or recompute global derivations inside generators, templates, or template modules.

## Internal Data Contracts

Do not preserve compatibility with old internal generator data shapes by layering fallback lookups into templates or generators. The compatibility boundary is user-authored YAML accepted by `projectCreate`, not intermediate Python dictionaries.

For required fields on existing DB/view rows, read directly, for example `row["dbfield"]`. Do not use `row.get("dbfield", {})`, `row.get("dbfield") or {}`, or similar fallback patterns for fields guaranteed by the DB/view contract. If a required field is missing, fix `projectCreate` validation, schema/config creation, or the `projectOpen` view helper that defines the contract.

Branching on optional rows or optional relationships is fine. Treating contracted fields as optional is not.

## New Internal Code

- For new internal code, replace the internal shape directly.
- Do not add compatibility wrappers, optional parameters, fallback paths, factories, caches, injectable helpers, or future-proof knobs unless a current caller requires them.
- Before adding an abstraction, identify its owner and lifetime. If ownership is unclear, ask before adding it.
- Prefer one direct path through the code. Avoid parallel APIs such as `foo()`, `tryFoo()`, optional `resolver=None`, or `fatal=None` unless each path has an existing, tested consumer.
- string processing should not be needed for extracting field information or performing lookup. There are functions already provided that utilize schema and data contracts that are robust. If you think you need to split strings expressly ask permission.
- Avoid using SQL for data already in dicts
