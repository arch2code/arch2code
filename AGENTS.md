# Builder Base Generator Rules

These rules apply when working under `builder/base`, especially generator,
template, and project database code.

## Generator Control Flow

Normal project use is a two-step flow. Do not treat generation as one Python run
that parses YAML and immediately renders templates.

Project makefiles usually wrap this as `make db` followed by generation targets
such as `make gen`, but the Python dispatch still follows this split.

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
the DB-backed `config` object.

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

## Where Changes Belong

- Put project-wide truth derived from YAML, schema, address calculation, or
  post-processing in `projectCreate`.
- Put language-neutral reshaping for one rendering context in a `projectOpen`
  view helper.
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
- Avoid defensive programming in view creation and template functions for
  fields guaranteed by the DB/view contract. If a required field is missing, fix
  `projectCreate` validation, schema/config creation, or the view helper that
  defines the contract. Branching on optional rows or relationships is fine;
  treating fields on existing contracted rows as optional is not.
- Do not edit generated regions by hand. Change the data creation, view helper,
  or template, then rerun the normal make target.

Keep the ownership split clear: `projectCreate` owns durable project database
truth; `projectOpen` owns read-only access and template-facing views; `renderer`
owns turning those views into text.
