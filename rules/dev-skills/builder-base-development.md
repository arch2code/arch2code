---
name: builder-base-development
description: Guidance for modifying Arch2Code builder/base internals, including generator control flow, database/view ownership, template rendering boundaries, and internal code conventions. Use when editing or reviewing files under builder/base.
---

# Builder base development

Use this skill when you change Arch2Code internals under `builder/base`: the generator, templates, schema, project database and Python support code. `GENERATOR_ARCHITECTURE.md` describes the concepts and stage boundaries behind these rules.

## Core rules

1. Ask before changing behavior when the ownership, data contract or intended architecture is unclear.
2. Keep changes to the requested behavior. Do not refactor unrelated code while you are in the generator.
3. Prefer the simplest direct implementation that matches existing builder patterns.
4. Do not edit generated regions by hand. Change the data creation, view helper, template or generator logic, then rerun the make target. `.gen/builder.stamp` picks up edits under `templates/`, `pysrc/`, `config/*.yaml`, `config/*.py`, `arch2code.py`, and Pro's `templates/` and `config/`. After an edit to `include/make/`, or to a template kept inside a project tree, run `make clean` first.
5. Design for real projects. A unit test is not a reason to keep a slower or more complex path. Change the test rather than add a test-only API.

## Comments

Comments explain what the code does not show. A comment that restates the lines below it is noise, so delete it.

- More than a few lines of comment is a signal to stop. Ask whether it is durable and whether it tells the reader anything the code does not. The usual answer is a shorter comment, or none.
- Judge the whole comment block, including when you edit or append to an existing one, not only the sentence you add.
- State standing behavior, positively. Leave out what an edit changed, what the code avoids doing, and plan or ticket detail.
- Lead a docstring with the problem in plain language, not the mechanism and not the caller's vocabulary.
- Write comments and docstrings through `unslop`.

## Generator control flow

Normal project use has two steps, database creation and generator execution. Project makefiles wrap them as `make db` followed by generation targets such as `make gen`.

1. `projectCreate` builds durable project state.
   - Entry point: `arch2code.py` with both `--yaml` and `--db`.
   - Implementation: `pysrc/processYaml.py::projectCreate`.
   - `mergeProjectConfig()` merges the base, Pro and user `project.yaml`. The schema tables come from `pysrc/schema.py::Schema`.
   - Put validation, normalization, schema population, address calculation, post-processing, expensive project-wide derivations and persisted config here, so they run once per database.
   - Do not put migration here. `projectCreate` rejects a project that is not on the current YAML format (`_gateYamlFormat`) and tells the user to run `make migrate`. YAML rewrites belong to `migrateYaml.py`.
   - Persist non-schema project state through the DB-backed `config` object. The derived tables that `projectOpen._loadDerivedTables()` loads (`blockClocksResets`, `instanceClockResetBinds`, `memoryClocks`, `blockParameterizedDecls`, `portDomains`, `containerLocalNets`) are the existing exceptions. A new one needs the user's approval.
2. `projectOpen` opens the database read-only for generators.
   - Entry point: `arch2code.py --readonly --db ...`, or a mode that supplies only `--db`.
   - Implementation: `pysrc/processYaml.py::projectOpen`.
   - It loads schema tables into `prj.data`, reloads config through `prj.config`, and rebuilds helper indexes.
   - Put template-facing, language-neutral views here, such as `getBlockData()`, `getContextData()`, and narrow helpers such as `getBlockConfigView()`.

The SQLite database is the only channel between the steps. Generators assume YAML parsing already happened and read through DB-backed data, config and view helpers.

## Template rendering boundaries

`projectCreate.configTemplates()` takes the merged `templates:` map, expands directory macros, and persists the result as `TEMPLATES`. Generators load that saved mapping. `make newmodule` is the exception: `pysrc/newModule.py` hands its scaffold template to the renderer directly.

Do not re-merge project YAML, search alternate template directories, synthesize missing mappings, or add generator fallback paths. If a mapping is missing, fix `projectCreate` validation or configuration.

For an in-place generated file, the generator opens the target with `codeText` (`pysrc/textfileHelper.py`), keeps user regions, collects `GENERATED_CODE_PARAM` and generated-section commands, asks `projectOpen` for views, renders through `renderer.renderSections()` and `renderer.render()`, and rewrites only the generated regions.

Template utility modules, including `pysrc/intf_gen_utils.py`, are render helpers, not semantic view builders. They may format SystemC or SystemVerilog spelling, choose local syntax, and iterate fields that `projectOpen` views already supply.

Keep templates and template utilities simple: select fields, iterate, apply local formatting, emit text. If code needs to walk `prj.data` across blocks, instances, ports, connections, variants or interface definitions to derive a reusable fact, or needs validation, cross-object lookup, caching or expensive computation, move it into `projectCreate` or a `projectOpen` view helper. The template consumes the precomputed field.

## Where changes belong

`projectCreate` owns durable database truth. `projectOpen` owns read-only access and template-facing views. `renderer` and the templates turn those views into text.

- Put project-wide truth derived from YAML, schema, address calculation or post-processing in `projectCreate`.
- Validate user-authored YAML in `projectCreate`. Validate developer-authored library content, such as interface definitions, schema and shipped templates, in `unittest/`, not on every generator run. Such tests discover the library rather than list it, and explain the rule in the failure message.
- Put language-neutral reshaping for one rendering context in a `projectOpen` view helper. That covers connection annotations, variant and Config ownership, cross-interface bind classification, payload classification, and any derived field `pysrc/intf_gen_utils.py` or a template consumes.
- Preserve the declaration order of user-authored objects. Regenerating after an unrelated edit must not reshuffle unrelated output. A view may classify, annotate or filter, but it does not reorder to suit a consumer.
- Reordering to satisfy one signature is spelling, so it belongs in the template or template utility for that language. Different APIs spell the same declared parameters in different orders. `axi_read_channel`, `axi_read_src_bfm` and `axi_read_port_thunker` each need a different one.
- If a view needs interface-specific facts, read `interface_defs` and the interface YAML instead of hard-coding special cases.
- If a task seems to need a schema change, pause for user input about the data contract and follow `config/SCHEMA_SPECIFICATION.md`.
- Keep language-specific syntax, emitted code structure and output formatting in templates or template utilities.
- Before adding a template input, check whether it already exists in `prj.data` or an existing view.
- Do not reparse YAML or recompute global derivations inside generators, templates or template modules.

## Internal data contracts

The compatibility boundary is user-authored YAML accepted by `projectCreate`. Intermediate Python dictionaries and view rows have no compatibility promise. When an internal shape changes, update its consumers. Do not add fallback lookups to templates or generators.

Read a required field on a DB or view row directly, for example `row["dbfield"]`. Do not write `row.get("dbfield", {})`, `row.get("dbfield") or {}` or a similar fallback for a field the contract guarantees. If a required field is missing, fix `projectCreate` validation, schema or config creation, or the `projectOpen` view helper that defines the contract.

Branching on an optional row or optional relationship is fine. An optional sub-table, for example, is absent in `projectCreate` and `None` in `projectOpen`, and a block with no entry in a derived table has no group, so `self.data['containerLocalNets'].get(blockKey, [])` is correct. Treating a contracted field as optional is not.

## New internal code

- For new internal code, replace the internal shape directly.
- Do not add compatibility wrappers, optional parameters, fallback paths, factories, caches, injectable helpers or future-proof knobs unless a current caller needs them.
- Do not build planned-but-unused flexibility. If a requested option has no call site in the current change, leave it out or ask whether it belongs now.
- Before adding an abstraction, identify its owner and lifetime. If ownership is unclear, ask first.
- Prefer one direct path through the code. Avoid parallel APIs such as `foo()` and `tryFoo()`, or an optional `resolver=None` or `fatal=None`, unless each path has an existing, tested consumer.
- Do not use string processing to extract field information or perform lookups. A row carries its context in `_context`, and `qualifiedKeyContext()` and `splitQualifiedKey()` in `pysrc/processYaml.py` take qualified keys apart. If you think you need another string split, ask first.
- Do not derive semantic names or artifact relationships from filenames, paths, stems, suffixes or string splits in templates or template utilities. Module names, namespaces, package names, Config names, generated class names, sibling files and validation facts come from persisted config or `projectOpen` views.
- Do not query SQL for data already loaded into dicts.
