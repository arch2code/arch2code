# Builder Base Generator Rules

These rules apply when working under `builder/base`, especially generator,
template, and project database code.

## General Rules
1. Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.
2. Simplest solution first. Always implement the simplest thing that could work. Do not add abstractions or flexibility that weren't explicitly requested.
3. Don't touch unrelated code. If a file or function is not directly part of the current task, do not modify it, even if you think it could be improved.
4. Flag uncertainty explicitly. If you are not confident about an approach or technical detail, say so before proceeding. Confidence without certainty causes more damage than admitting a gap.
5. `builder/base` is a git submodule. Do not stage or commit any changes - user will manage.

## Generator Control Flow

Normal project use is a two-step flow. Do not treat generation as one Python run
that parses YAML and immediately renders templates.

Project makefiles wrap this as `make db` followed by generation targets
such as `make gen`, but the Python dispatch still follows this split.
Use `make clean` to force db rebuild. Use make with `-j` for performance. 

1. `projectCreate` builds the database.
  - Entry point: `arch2code.py` with both `--yaml` and `--db`.
  - Implementation: `pysrc/processYaml.py::projectCreate`.
  - It merges base/pro/user project config, resolves directory macros, expands
  the unified `templates:` map, creates SQLite tables from
  `pysrc/processYaml.py::Schema`, reads system and project YAML, runs
  post-parse scripts, computes derived persisted facts, and writes config
  blobs such as `TEMPLATES`, `DIRS`, `FILEMAP`, `YAMLCONTEXT`, and
  `INCLUDENAME`.
  - Put validation, normalization, migration of accepted user YAML, expensive
  project-wide derivations, and durable facts here so they run once per
  database creation.
2. `projectOpen` opens the database for generators.
  - Entry point: `arch2code.py --readonly --db ...` or a mode that supplies
   only `--db`.
  - Implementation: `pysrc/processYaml.py::projectOpen`.
  - It opens SQLite read-only, loads schema tables into `prj.data`, reloads
  config through `prj.config`, rebuilds helper indexes, and exposes query or
  view helpers used by generators.
  - Create template-facing, language-neutral views here, such as
  `getBlockData()`, `getContextData()`, and narrowly scoped helper views like
  `getBlockConfigView()`.

The SQLite database is the only communication channel between these execution
steps. Generators should assume YAML parsing already happened and should read
through DB-backed data, config, and view helpers.
Schema-backed design data is stored in tables defined by
`pysrc/processYaml.py::Schema`; non-schema project state is persisted through
the DB-backed `config` object. Exceptions to this rule must be generally avoided
unless explicitly qualified by the user.

## Template Rendering

`projectCreate.configTemplates()` selects and expands template mappings from the
merged `templates:` section in `project.yaml`, then persists the result in the
DB-backed config as `TEMPLATES`. Later generator invocations must load this
saved mapping. Do not re-merge project YAML, search alternate template
directories, synthesize missing mappings, or add generator fallback paths. If a
mapping is missing, fix `projectCreate` validation or configuration.

For in-place generated files, generators open the target with `codeText`,
preserve user regions, collect `GENERATED_CODE_PARAM` and generated-section
commands, ask `projectOpen` for views, render through
`renderer.renderSections()` and `renderer.render()`, then rewrite only generated
regions.

Template utility modules, including `pysrc/intf_gen_utils.py`, are render
helpers, not view builders. They may format SystemC/SystemVerilog spelling,
choose local syntax, and iterate fields already supplied by `projectOpen` views
such as `block_data`, `context_data`, connection rows, and `interface_defs`.

Do not create new semantic views in template utilities. If a change needs to
walk `prj.data` across blocks, instances, ports, connections, variants, or
interface definitions to derive a fact that multiple template lines consume,
add that fact to a `projectOpen` view helper instead. The template utility
should then consume the precomputed field directly.

## Where Changes Belong

- Put project-wide truth derived from YAML, schema, address calculation, or
post-processing in `projectCreate`.
- Put language-neutral reshaping for one rendering context in a `projectOpen`
view helper. This includes connection annotations, variant/config ownership,
cross-interface bind classification, payload ordering, and any derived field
later consumed by `pysrc/intf_gen_utils.py` or templates.
- If view creation needs interface-specific facts, prefer `interface_defs` and
the corresponding interface YAML files over hard-coded special cases.
- If a task appears to require schema changes, pause for any needed user input
about the data contract and follow `config/SCHEMA_SPECIFICATION.md`.
- Keep language-specific implementation, syntax selection, emitted code
structure, and output formatting in the template or template utility for that
language.
- Before adding a template input, check whether it already exists in `prj.data`
or an existing view.
- Do not reparse YAML or recompute global derivations inside generators,
templates, or template modules.
- Do not preserve compatibility with old internal generator data shapes by
layering fallback lookups into templates or generators. The compatibility
boundary is user-authored YAML accepted by `projectCreate`, not intermediate
Python dictionaries.
- Keep templates and template utility functions simple: select fields, iterate,
apply local language-specific formatting, and emit text. Move extensive data
manipulation, validation, cross-object lookup logic, caching, or expensive
computation into `projectCreate` or a language-neutral `projectOpen` view.
- Do not use fallback defaults for fields guaranteed by the DB/view contract.
Required fields on existing DB/view rows must be read directly, for example
`row["dbfield"]`, not `row.get("dbfield", {})`, `row.get("dbfield") or {}`,
or similar defensive fallback patterns. If a required field is missing, fix
`projectCreate` validation, schema/config creation, or the `projectOpen` view
helper that defines the contract. Branching on optional rows or optional
relationships is fine; treating contracted fields as optional is not.
- Do not edit generated regions by hand. Change the data creation, view helper,
or template, then rerun the normal make target.
- Do not add plan specific comments. Instead add durable behavior comments

Keep the ownership split clear: `projectCreate` owns durable project database
truth; `projectOpen` owns read-only access and template-facing views; `renderer`
owns turning those views into text.

## Simplicity And New Internal Code

- For new internal code, replace the internal shape directly. Do not add compatibility wrappers, optional parameters, fallback paths, or “future-proof” knobs unless a current caller requires them.
- Before adding an abstraction, identify its owner and lifetime. If ownership is unclear, pause and ask instead of adding factories, caches, or injectable helpers.
- Do not implement planned-but-unused flexibility. If a requested option has no concrete call site in the current change, leave it out or ask whether it should be included now.
- Prefer one direct path through the code. Avoid parallel APIs such as `foo()`, `tryFoo()`, optional `resolver=None`, or `fatal=None` unless each path has an existing, tested consumer.