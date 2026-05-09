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
`config` object, which also persists into the database.

## Two-Step Model

1. `projectCreate` builds the database.
   - Entry point: `arch2code.py` with both `--yaml` and `--db`.
   - Implementation: `pysrc/processYaml.py::projectCreate`.
   - It merges base/pro/user project config, resolves directory macros,
     expands the unified `templates:` map, creates SQLite tables from the
     `Schema` class, reads system YAML and project YAML, processes post-parse
     scripts, computes derived persisted facts, and writes config blobs such as
     `TEMPLATES`, `DIRS`, `FILEMAP`, `YAMLCONTEXT`, and `INCLUDENAME`.
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
   view. These view dictionaries are the template input surface.
4. `renderer.renderSections()` parses each generated-section command, calls the
   generator handler, and then `renderer.render()` dispatches to either a Jinja
   template file or a Python template module from `TEMPLATES`.
5. `codeText.genFile()` rewrites only the generated regions, leaving the rest of
   the file intact.

## Where To Put Changes

- If the value is a project-wide truth derived from YAML, schema, address
  calculation, or post-processing, compute and persist it in `projectCreate`.
- If the value is only a convenient shape for one rendering context, build it in
  a `projectOpen` view helper such as `getBlockData()` or `getContextData()`.
- If a template needs a new input, first check whether the input already exists
  in `prj.data` or an existing view. Avoid reparsing YAML or recomputing global
  derivations inside template modules.
- Do not edit generated regions by hand. Change the data creation, view helper,
  or template, then rerun the normal make target.

Keep this split in mind: `projectCreate` owns the durable project database;
`projectOpen` owns read-only access and template-facing views; `renderer` owns
turning those views into text.
