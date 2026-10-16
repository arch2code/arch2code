# Builder base generator rules

These rules apply when working under `builder/base`, especially generator,
template, and project database code.

## General rules
1. Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.
2. Simplest solution first. Implement the simplest thing that could work. Do not add abstractions or flexibility that were not requested.
3. Don't touch unrelated code. If a file or function is not part of the current task, do not modify it, even if you think it could be improved.
4. Flag uncertainty. If you are not confident about an approach or technical detail, say so before proceeding.
5. `builder/base` is a git submodule. Do not stage or commit any changes. The user manages them.
6. Write every document through the `unslop` skill. Load it at the start of the session and apply it before handing anything back.

## Skill routing

Load the development skill that matches the task before you edit, build, test or verify. Treat these as
instructions to follow, not background reading.

| Task | Skill |
| :--- | :--- |
| **Editing generator internals** | `builder-base-development` (control flow, database and view ownership, template rendering boundaries) |
| **Reviewing Python changes** | `review-python-code` (defensive code, fallback paths, compatibility wrappers, agent-added guards) |
| **Adding or changing an interface protocol** | `authoring-interface-definitions` (`interface_defs` layout, companion files, declaration rules) |
| **Writing or editing any prose** | `unslop` (always applies, see below) |
| **Building, running the gates, declaring a task done** | `principle-prove-it-works` (verify the real artefact, which gate proves what) |

`wait-what` (re-pitch an explanation in plain language) and `handoff` (write a
prompt the next agent can start from) are commands the user runs. Agents cannot
load them.

### unslop applies to every agent

Every agent working under `builder/base` loads `unslop`, including subagents you
spawn. Name it in the subagent prompt, because a subagent inherits these rules
but reaches the skill only when told to.

The skill states what it governs. Use the vocabulary in `CONTEXT.md`.

## Generator control flow

Normal project use has two steps, database creation and generator execution.
Do not treat generation as one Python run that parses YAML and immediately
renders templates.

Project makefiles wrap the two steps as `make db` followed by generation
targets such as `make gen`.
The db rebuilds when its YAML changes, when the builder stamp changes, or when
the build manifest is stale. `.gen/builder.stamp` and the manifest
`.gen/build.mk` work as follows:
- `builder.stamp` lists every file under `templates/`, `pysrc/`, `config/*.yaml`,
  `config/*.py`, `arch2code.py`, and Pro's `templates/` and `config/` when Pro is
  present, each with its mtime. Adding, removing or touching one of those files
  rebuilds the db and regenerates every generated file.
- `build.mk` records the project root it was written for. A manifest written
  for another root (a copied or moved tree), or one that names a missing YAML
  file (a moved builder, a deleted include), forces a db rebuild. A failed
  rebuild leaves the manifest stale, so the next `make` forces again.

A tree with no builder stamp rebuilds its db and regenerates everything on its
next `make`. Nothing tracks templates kept inside the project tree or other
builder files such as `include/make/`. Run `make clean` after changing those.
Use make with `-j`, except for `push-test`.

1. `projectCreate` builds durable project state.
   - Entry point: `arch2code.py` with both `--yaml` and `--db`.
   - Implementation: `pysrc/processYaml.py::projectCreate`.
   - `mergeProjectConfig()` merges the base, Pro and user `project.yaml`.
     `projectCreate` resolves directory macros, persists the `templates:` map,
     creates SQLite tables from `pysrc/schema.py::Schema`, reads system and
     project YAML, runs post-parse scripts, computes derived persisted facts,
     and writes config blobs such as `TEMPLATES`, `DIRS`, `FILEMAP`,
     `YAMLCONTEXT`, and `INCLUDENAME`.
   - Put validation, normalization, schema population, address calculation,
     post-processing, expensive project-wide derivations and persisted config
     here, so they run once per database.
   - Do not put migration here. `projectCreate` rejects a project that is not
     on the current YAML format and tells the user to run `make migrate`.
     YAML rewrites belong to `migrateYaml.py`.
2. `projectOpen` opens the database read-only for generators.
   - Entry point: `arch2code.py --readonly --db ...`, or a mode that supplies
     only `--db`.
   - Implementation: `pysrc/processYaml.py::projectOpen`.
   - It loads schema tables into `prj.data`, reloads config through
     `prj.config`, and rebuilds helper indexes.
   - Put template-facing, language-neutral views here, such as
     `getBlockData()`, `getContextData()`, and narrow helpers such as
     `getBlockConfigView()`.

The SQLite database is the only channel between the steps. Generators assume
YAML parsing already happened and read through DB-backed data, config and view
helpers. Schema-backed design data lives in tables defined by
`pysrc/schema.py::Schema`. Persist non-schema project state through the
DB-backed `config` object. The derived tables that
`projectOpen._loadDerivedTables()` loads are the existing exceptions. A new one
needs the user's approval.

## Template rendering

`projectCreate.configTemplates()` takes the merged `templates:` map, expands
directory macros, and persists the result as `TEMPLATES`. Generators load that saved mapping.
`make newmodule` is the exception: `pysrc/newModule.py` hands its scaffold
template to the renderer directly. Do not re-merge project YAML, search
alternate template directories, synthesize missing mappings, or add generator
fallback paths. If a mapping is missing, fix `projectCreate` validation or
configuration.

For an in-place generated file, the generator opens the target with `codeText`,
keeps user regions, collects `GENERATED_CODE_PARAM` and generated-section
commands, asks `projectOpen` for views, renders through
`renderer.renderSections()` and `renderer.render()`, and rewrites only the
generated regions.

Template utility modules, including `pysrc/intf_gen_utils.py`, are render
helpers, not semantic view builders. They may format SystemC or SystemVerilog
spelling, choose local syntax, and iterate fields that `projectOpen` views
already supply.

Keep templates and template utilities simple: select fields, iterate, apply
local formatting, emit text. If code needs to walk `prj.data` across blocks,
instances, ports, connections, variants or interface definitions to derive a
reusable fact, or needs validation, cross-object lookup, caching or expensive
computation, move it into `projectCreate` or a `projectOpen` view helper. The
template consumes the precomputed field.

## Where changes belong

- Put project-wide truth derived from YAML, schema, address calculation or
  post-processing in `projectCreate`.
- Validate user-authored YAML in `projectCreate`. Validate developer-authored
  library content, such as interface definitions, schema and shipped templates,
  in `unittest/`, not on every generator run. Such tests discover the library
  rather than list it, and explain the rule in the failure message.
- Put language-neutral reshaping for one rendering context in a `projectOpen`
  view helper. That covers connection annotations, variant and Config
  ownership, cross-interface bind classification, payload classification, and
  any derived field `pysrc/intf_gen_utils.py` or a template consumes.
- Preserve the declaration order of user-authored objects. Regenerating after an
  unrelated edit must not reshuffle unrelated output. A view may classify,
  annotate or filter, but it does not reorder to suit a consumer.
- Reordering to satisfy one signature is spelling, so it belongs in the template
  or template utility for that language. Different APIs spell the same declared
  parameters in different orders. `axi_read_channel`, `axi_read_src_bfm` and
  `axi_read_port_thunker` each need a different one.
- If a view needs interface-specific facts, read `interface_defs` and the
  interface YAML instead of hard-coding special cases.
- If a task seems to need a schema change, pause for user input about the data
  contract and follow `config/SCHEMA_SPECIFICATION.md`.
- Keep language-specific syntax, emitted code structure and output formatting in
  templates or template utilities.
- Before adding a template input, check whether it already exists in `prj.data`
  or an existing view.
- Do not reparse YAML or recompute global derivations inside generators,
  templates or template modules.
- The compatibility boundary is user-authored YAML accepted by `projectCreate`.
  Intermediate Python dictionaries and view rows have no compatibility promise.
  When an internal shape changes, update its consumers. Do not add fallback
  lookups to templates or generators.
- Read a required field on a DB or view row directly, for example
  `row["dbfield"]`. Do not write `row.get("dbfield", {})`,
  `row.get("dbfield") or {}` or a similar fallback for a field the contract
  guarantees. If a required field is missing, fix `projectCreate` validation,
  schema or config creation, or the `projectOpen` view helper that defines the
  contract. Branching on an optional row or optional relationship is fine.
  Treating a contracted field as optional is not.
- Do not edit generated regions by hand. Change the data creation, view helper,
  template or generator logic, then rerun the make target.
- Comments explain what the code does not show. State standing behavior, never
  plan-specific detail. More than a few lines of comment is a signal to stop
  and ask whether it says anything the code does not. Judge the whole comment
  block, not just the sentence being added.

`projectCreate` owns durable database truth. `projectOpen` owns read-only
access and template-facing views. `renderer` and the templates turn those views
into text.

## Simplicity and new internal code

- For new internal code, replace the internal shape directly. Do not add compatibility wrappers, optional parameters, fallback paths, factories, caches, injectable helpers or future-proof knobs unless a current caller needs them.
- Before adding an abstraction, identify its owner and lifetime. If ownership is unclear, ask first.
- Do not build planned-but-unused flexibility. If a requested option has no call site in the current change, leave it out or ask whether it belongs now.
- Prefer one direct path through the code. Avoid parallel APIs such as `foo()` and `tryFoo()`, or an optional `resolver=None` or `fatal=None`, unless each path has an existing, tested consumer.
- Do not use string processing to extract field information or perform lookups. A row carries its context in `_context`, and `qualifiedKeyContext()` and `splitQualifiedKey()` in `pysrc/processYaml.py` take qualified keys apart. If you think you need another string split, ask first.
- Do not query SQL for data already loaded into dicts.
