# Generator Control Flow

This note is a short orientation guide for agents working on generators in
`builder/base`. The most common mistake is treating generation as one Python
run that parses YAML and immediately renders templates. In normal project use
it is a two-step flow.

The project makefiles usually wrap these invocations (`make db`, then
generation targets such as `make gen`), but the Python dispatch still follows
the structure below.

The SQLite database is the only communication channel between the two
execution steps. Schema-backed design data is stored in tables defined by
`pysrc/processYaml.py::Schema`; non-schema project state is stored through the
`config` object, which also persists into the database. This boundary is
intentional: do validation, normalization, and expensive project-wide
derivations once while creating the database, then expose simple read-only
views when opening it for generation.

## Two-Step Model

1. `projectCreate` builds the database.
   - Entry point: `arch2code.py` with both `--yaml` and `--db`.
   - Implementation: `pysrc/processYaml.py::projectCreate`.
   - It merges base/pro/user project config, resolves directory macros,
     expands the unified `templates:` map, creates SQLite tables from the
     `Schema` class, reads system YAML and project YAML, processes post-parse
     scripts, computes derived persisted facts, and writes config blobs such as
     `TEMPLATES`, `DIRS`, `FILEMAP`, `YAMLCONTEXT`, and `INCLUDENAME`.
   - Put as much data validation, normalization, and expensive computation here
     as possible so it runs once per database creation, not once per generator,
     block, file, or template render.
   - Put durable facts here when templates need the same answer in every later
     generator pass. Examples include derived block fields persisted on DB rows.

2. `projectOpen` opens the database for generators.
   - Entry point: `arch2code.py --readonly --db ...` or a mode that supplies
     only `--db`.
   - Implementation: `pysrc/processYaml.py::projectOpen`.
   - It opens the SQLite DB read-only, loads schema tables into `prj.data`,
     reloads config blobs through `prj.config`, rebuilds helper indexes such as
     hierarchy and parent-child table maps, and exposes query/view helpers used
     by generators.
   - Create template-facing data views here. These views should collect,
     reshape, and name language-neutral data for the rendering context without
     changing durable project truth.
   - Generators should assume YAML parsing already happened. They should read
     through `prj.data`, `prj.config`, `getBlockData()`, `getContextData()`, or
     narrowly scoped helper views such as `getBlockConfigView()`.

## Template Rendering Path

Template mappings are selected during `projectCreate` by
`projectCreate.configTemplates()`. The merged `templates:` section in
`project.yaml` is expanded to absolute paths and saved in the project config as
`TEMPLATES`. Later generator invocations do not re-merge project YAML to find
templates; they load this saved mapping from the DB-backed config.

For in-place generated files, the path is:

1. A generator such as `genSystemC`, `systemVerilogGenerator`, or
   `documentGenerator` opens the target source file with `codeText`.
2. `codeText` preserves user-written regions and extracts
   `GENERATED_CODE_PARAM` plus each `GENERATED_CODE_BEGIN ... END` command.
3. The generator asks `projectOpen` for a block, context, hierarchy, or document
   view. These view dictionaries are the template input surface and should
   already be in the shape that templates need.
4. `renderer.renderSections()` parses each generated-section command, calls the
   generator handler, and then `renderer.render()` dispatches to either a Jinja
   template file or a Python template module from `TEMPLATES`.
5. `codeText.genFile()` rewrites only the generated regions, leaving the rest of
   the file intact.

## Where To Put Changes

- If the value is a project-wide truth derived from YAML, schema, address
  calculation, or post-processing, compute and persist it in `projectCreate`.
  This includes validation and expensive derived data that should not be
  repeated during generation.
- If the value is only a convenient, language-neutral shape for one rendering
  context, build it in a `projectOpen` view helper such as `getBlockData()` or
  `getContextData()`. View creation is the right place for data reshaping that
  would otherwise make templates complex.
- Interface-specific code note: if view creation needs special cases for a
  particular interface type, use `interface_defs` and the corresponding
  interface YAML files as the abstraction mechanism. The interface-specific
  facts should usually live there, not be hard-coded in a view helper.
- Schema-change note: if the task appears to require schema changes, pause for
  any needed user input about the data contract. See
  [Schema Specification](config/SCHEMA_SPECIFICATION.md) for the schema rules.
- If the behavior is language-specific implementation, syntax selection, emitted
  code structure, or output formatting, keep it in the template or template
  utility for that language. Do not bake SystemC, SystemVerilog, C++, Markdown,
  or other target-language choices into shared view creation.
- If a template needs a new input, first check whether the input already exists
  in `prj.data` or an existing view. Avoid reparsing YAML or recomputing global
  derivations inside template modules.
- Templates and template utility functions must stay simple: select fields,
  iterate, apply language-specific local formatting, and emit text. Extensive
  data manipulation, validation, cross-object lookup logic, caching, or
  expensive computation in templates or their helpers is expressly prohibited;
  move that work into `projectCreate` or a language-neutral `projectOpen` view
  helper instead.
- Data-related error checks in view creation or template functions are a bad
  code smell. They usually indicate that `projectCreate` validation is missing
  a required invariant or diagnostic.
- Do not edit generated regions by hand. Change the data creation, view helper,
  or template, then rerun the normal make target.

Keep this split in mind: `projectCreate` owns the durable project database;
`projectOpen` owns read-only access and template-facing views; `renderer` owns
turning those views into text.
