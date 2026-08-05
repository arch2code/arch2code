# Plan: Split `processYaml.py` into `projectCreate`, `projectOpen`, `config`, and a shared module

## Goal

`builder/base/pysrc/processYaml.py` is a 6564-line module holding three classes
plus a layer of module-level helpers and state. Split it into four focused
modules along the ownership lines the builder-base rules already describe
(`projectCreate` owns durable DB truth, `projectOpen` owns read-only views,
`config` owns persisted non-schema state), and move the helpers shared by both
classes into one shared module. After the split, delete `processYaml.py` and
repoint every importer at the new modules (no re-export facade).

This is **behavior-preserving**: no validation, view output, or data-contract
changes, and the generated DB and all generated artifacts must be byte-identical
before and after. The split itself is a mechanical move; the one piece of logic
that changes shape is the `dirMacros` handling, which is refactored from a
mutable module global into pure helpers + project instance state (see the
dirMacros section). That refactor preserves the final `DIRS` value and all
expanded paths.

## Current Contents (single file, by line range)

| Lines | Symbol | Destination module |
| :--- | :--- | :--- |
| 1–17 | imports | distributed per module (only what each uses) |
| 19 | `continueOnError = False` | `projectShared.py` |
| 21–25 | `CURRENT_YAML_FORMAT = 2` | `projectShared.py` |
| 28 | `yaml = YAMLRAW.YAML(typ='rt')` | `projectShared.py` |
| 30–34 | `dict_factory` | `projectShared.py` |
| 36–42 | `basePathRelative` | `projectShared.py` |
| 45–54 | `existsLoad` | `projectShared.py` |
| 56 | `dirMacros = None` (mutable module state) | **removed** — becomes `self.dirMacros` instance state (see refactor) |
| 59–69 | `_expand_with_macros` | `projectShared.py` — **unchanged** (already pure `(path, macros)`) |
| 72–76 | `expandDirMacros` | `projectShared.py` — same body, signature gains `macros` (drops the global) |
| 78–92 | `expandNewModulePath` | `projectShared.py` — same body, signature gains `macros` |
| 95–100 | `loadIfExists` | `projectShared.py` |
| 102–109 | `resolveFilePath` | `projectShared.py` — same body, signature gains `macros` |
| 111–122 | `camelCase` | `projectShared.py` |
| 124–130 | `getKeyPriority` | `projectShared.py` |
| 132–134 | `getPortChannelName` | `projectShared.py` |
| 136–145 | `getTypeWidthContext` | `projectShared.py` |
| 147–152 | `splitQualifiedKey` | `projectShared.py` |
| 154–166 | `qualifiedKeyContext` | `projectShared.py` |
| 168–178 | `loadModule` | `projectShared.py` |
| 183–247 | `class config` | `projectConfig.py` |
| 250–308 | `generateHierarchy` **free function** (used by both classes) | `projectShared.py` |
| 314–2852 | `class projectOpen` (64 methods) | `projectOpen.py` |
| 2853–6564 | `class projectCreate` (83 methods) | `projectCreate.py` |

> Absolute line numbers are approximate anchors only — the file shifted ~12
> lines during analysis. Locate each site by the symbol/method name given in
> this plan, not by line number.

**Three `generateHierarchy` definitions — only the free function is shared:**

- The **free function** `generateHierarchy(inputInstances, inputBlocks, withContext=False)`
  (≈250) holds the logic and moves to `projectShared.py`.
- `projectOpen.generateHierarchy(self)` (≈697) and
  `projectCreate.generateHierarchy(self)` (≈3217) are **separate methods that
  stay in their own classes.** Their bodies are near-identical (assign
  `self.hier / hierKey / instances / instanceContainer / blocks`) but they are
  **not** the same call: `projectOpen` invokes the free function with the
  default `withContext=False`; `projectCreate` invokes it with
  `withContext=True`. That flag selects different input-nesting handling in the
  free function, so the two methods are intentionally distinct and must **not**
  be merged or hoisted into the shared module.
- Mechanical effect of the move: inside each method, the bare
  `generateHierarchy(...)` call becomes `projectShared.generateHierarchy(...)`.
  The `self.generateHierarchy()` call sites (`projectOpen.__init__` ≈357,
  `projectCreate` ≈3157) continue to resolve to each class's own method and need
  no change.

### Key facts established by inspection
- **The two classes are independent.** `projectCreate` does not subclass or
  instantiate `projectOpen`; every `projectOpen` token inside the
  `projectCreate` line range is a comment. No new import cycle is created by
  separating them.
- **`config` is self-contained** (uses only `g`, `printError`,
  `warningAndErrorReport`, `pickle`, `sqlite3`).
- **`generateHierarchy` is shared** by `projectCreate` and `projectOpen`, so it
  belongs in `projectShared.py`, not in either class module.
- **`dirMacros` is the one piece of mutable cross-module state** — see the
  hazard section below.

## Target Module Layout (all under `builder/base/pysrc/`)

- `projectShared.py` — module state (`continueOnError`, `CURRENT_YAML_FORMAT`,
  `yaml`, `dirMacros`) + all free helper functions + `generateHierarchy`.
- `projectConfig.py` — `class config`.
- `projectOpen.py` — `class projectOpen`.
- `projectCreate.py` — `class projectCreate`.
- `processYaml.py` — **deleted**.

Names follow the existing camelCase `pysrc/` convention (`newModule.py`,
`evalExpr.py`, `valueResolver.py`). `projectConfig.py` is used instead of
`config.py` to avoid visual collision with the `builder/base/config/` directory;
the **class name stays `config`** so import statements only change the module
path, not the symbol.

## `dirMacros` Refactor (eliminate the module global)

Today `dirMacros` is a `None`-initialized module global, mutated via
`global dirMacros` in `projectCreate.__init__` (line 2945/2970), in
`projectDirs()` (3059–3095), and in `projectOpen` (353–354), and read directly
by the helpers and by `newModule.py`. Carrying that global across a module
boundary is fragile (a bare `global` in a new module binds a fresh local and
leaves the helper reading `None`). Rather than relocate the hazard, this change
**removes the global**: the helpers become pure, and the live macro dict becomes
project instance state.

### Inspection facts that make this clean
- `projectOpen` never expands a path — it only *loads* `dirMacros` (in its
  loader, ≈line 353–354) so the `newModule.py` caller (which holds a `prj`) can
  expand paths. Every `expandDirMacros` / `expandNewModulePath` /
  `resolveFilePath` call site is inside `projectCreate` or `newModule.py`
  (verified: `resolveFilePath` in `__init__`; `expandDirMacros` in
  `configTemplates`, `postYamlExternalScript`, `getFileList`;
  `expandNewModulePath` in `saveIncludeFiles`; `newModule.__init__` and
  `newModule.create_from_template`).
- `dirMacros` is genuinely staged within `projectCreate`: seeded as
  `{"a2c": self.a2cRoot}` in `__init__`, consumed by `resolveFilePath` for the
  schema path before the full build, then fully populated in `projectDirs()`
  and persisted as config `DIRS`. Instance state models this staging naturally.

### Helper changes (minimal — thread `macros`, do not merge)
The only change to each helper is that the macro dict is **passed in as a
parameter** instead of read from the module global. Bodies are otherwise
unchanged; the two functions are **not** merged.

- `_expand_with_macros(path, macros)` — **unchanged**; it is already pure.
- `expandDirMacros(myFile, macros)` — drop `global dirMacros`; keep the body
  exactly:
  ```python
  def expandDirMacros(myFile, macros):
      if not macros:
          return myFile
      return _expand_with_macros(myFile, macros)
  ```
- `expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, macros, missingDirOk=False)`
  — body unchanged except `basePathAbs = macros[basePathKey]`. (`macros` is
  positional before the keyword-only-in-practice `missingDirOk`; both call sites
  pass `missingDirOk=True` by keyword, so this is safe.)
- `resolveFilePath(userDict, a2cDict, key, basePath, macros)` — body unchanged
  except `filePath = expandDirMacros(filePath, macros)`.

Keeping `expandDirMacros`'s `if not macros` guard makes its body identical to
today line-for-line (it is technically redundant with `_expand_with_macros`'s
own guard, but preserving it keeps the diff minimal and avoids relying on any
equivalence argument).

### State ownership
- **`projectCreate`**: add `self.dirMacros`. Seed
  `self.dirMacros = {"a2c": self.a2cRoot}` in `__init__` (replacing the
  `dirMacros = {...}` global write); `projectDirs()` builds onto
  `self.dirMacros` (replacing its local `dirMacros`) and persists it
  (`self.config.setConfig('DIRS', self.dirMacros)`); the call sites in
  `__init__` (`resolveFilePath`), `projectDirs` (`_expand_with_macros`),
  `configTemplates`, `postYamlExternalScript`, `getFileList`
  (`expandDirMacros`), and `saveIncludeFiles` (`expandNewModulePath`) all pass
  `self.dirMacros`. Both `global dirMacros` declarations are deleted.
- **`projectOpen`**: replace the loader's global write (≈line 353–354) with
  `self.dirMacros = self.config.getConfig('DIRS')`; delete the `global`.
- **`newModule.py`**: `prj` is in scope at every site (`__init__(self, prj, args)`
  and `create_from_template(..., prj, ...)`); switch `processYaml.dirMacros` →
  `prj.dirMacros`, `processYaml.expandDirMacros(x)` →
  `projectShared.expandDirMacros(x, prj.dirMacros)`, and
  `processYaml.expandNewModulePath(..., missingDirOk=True)` →
  `projectShared.expandNewModulePath(..., prj.dirMacros, missingDirOk=True)`.

### Why free functions + instance attribute (not a method or config method)
The two project classes share no base class; a one-line `expandDirMacros` method
would either duplicate across both or force a new base class (a structural change
the builder-base rules say to avoid). Pure functions in `projectShared` that take
`macros` explicitly keep `projectShared` side-effect-free and testable. The live
dict lives on the project instance because that is where its lifetime is owned.
Putting `expandPath` on the `config` object was considered and rejected: it would
push path-expansion domain logic into a generic key/value store and force `DIRS`
to be persisted in its partial `{"a2c": ...}` state earlier than today.

The final persisted `DIRS` value is identical to today, so the generated DB and
artifacts remain byte-identical.

## Import Wiring Between New Modules

- `projectConfig.py`: `g`, `printError`, `warningAndErrorReport`, `pickle`,
  `sqlite3`. No dependency on the other three.
- `projectShared.py`: `os`, `re`, `importlib`/`importlib.util`,
  `from typing import OrderedDict` (preserve the existing import exactly — it
  backs `generateHierarchy`), `YAML` from `yamlInclude`, `YAMLRAW`, the
  `arch2codeHelper` names actually used, `g`. No dependency on the classes.
- `projectOpen.py`: `import pysrc.projectShared as projectShared`,
  `from pysrc.projectConfig import config`, plus its current imports
  (`Schema`, `evalExpr`, `ValueResolver`, `merge_with_spec`, etc.). Replace
  every previously-module-local helper call with `projectShared.<helper>`.
- `projectCreate.py`: same shared/config imports as `projectOpen.py`, plus its
  current imports.

No cycles result: `projectShared` and `projectConfig` are leaves; the two class
modules depend only on those leaves and on unrelated modules (`Schema`,
`evalExpr`, …). `schema.py`'s imports of `config`/`projectCreate` stay lazy
(function-local), so the existing `Schema ↔ projectCreate` relationship is
unchanged.

## External Import Sites to Repoint

Code imports (must change):

| File:line | Current | New |
| :--- | :--- | :--- |
| `arch2code.py:11` | `from pysrc.processYaml import projectCreate, projectOpen` | `from pysrc.projectCreate import projectCreate` + `from pysrc.projectOpen import projectOpen` |
| `migrateYaml.py:48` | `from pysrc.processYaml import CURRENT_YAML_FORMAT` | `from pysrc.projectShared import CURRENT_YAML_FORMAT` |
| `config/postParseRegisterPorts.py:30` | `from pysrc.processYaml import camelCase, qualifiedKeyContext` | `from pysrc.projectShared import camelCase, qualifiedKeyContext` |
| `pysrc/newModule.py:3,56,62,144` | `import pysrc.processYaml as processYaml`; `processYaml.dirMacros`, `processYaml.expandDirMacros(x)`, `processYaml.expandNewModulePath(...)` | `import pysrc.projectShared as projectShared`; `prj.dirMacros`, `projectShared.expandDirMacros(x, prj.dirMacros)`, `projectShared.expandNewModulePath(..., prj.dirMacros)` (see dirMacros refactor) |
| `pysrc/schema.py:591,597` | `from pysrc.processYaml import config` | `from pysrc.projectConfig import config` |
| `pysrc/schema.py:637` | `from pysrc.processYaml import projectCreate` | `from pysrc.projectCreate import projectCreate` |
| `pysrc/systemcGen.py:2` | `from pysrc.processYaml import existsLoad` | `from pysrc.projectShared import existsLoad` |
| `pysrc/systemVerilogGenerator.py:2` | `from pysrc.processYaml import existsLoad` | `from pysrc.projectShared import existsLoad` |
| `templates/systemVerilog/moduleInterfacesInstances.py:2` | `from pysrc.processYaml import camelCase` | `from pysrc.projectShared import camelCase` |
| `templates/systemc/encoder.py:4` | `from pysrc.processYaml import camelCase` | `from pysrc.projectShared import camelCase` |
| `templates/systemc/testbench.py:4` | `from pysrc.processYaml import getPortChannelName` | `from pysrc.projectShared import getPortChannelName` |
| `pysrc/renderer.py:2` | `import pysrc.processYaml as processYaml` (**unused**) | **delete the line** |
| `pysrc/docgen.py:4` | `import pysrc.processYaml as processYaml` (**unused**) | **delete the line** |

Unittests (repoint the `from pysrc.processYaml import …` line to the owning
module; `projectOpen`→`projectOpen`, `projectCreate`→`projectCreate`,
`CURRENT_YAML_FORMAT`→`projectShared`):
`test_apb_validation.py`, `test_duplicate_interface.py`,
`test_data_by_parent_logic.py`, `test_boundary_signals.py`,
`test_mixed_project.py` (line 48, function-local), `test_interface_loading.py`,
`test_nested_loading.py`, `test_thunker_view.py`, `_addrctl_helpers.py`,
`test_parameter_variant_block_param_identity.py`, `test_foreign_key_lookup.py`,
`test_param_const_linkage.py`, `test_eval_canonical_view.py`,
`test_eval_sv_emit.py`, `test_eval_cpp_emit.py`,
`test_param_symbol_forwarding.py`, `test_migrate_yaml.py`.

Docstring/comment-only references to `processYaml.py::…` (no import) in several
`test_error_*` files, `intf_gen_utils.py`, `constructor.py`,
`test_implied_register_in_container_scope.py`,
`test_register_ports_independent_of_ports.py` — update the prose to name the new
owning module so the references stay accurate. These do not affect execution.

Docs: `builder/base/CLAUDE.md` and the project `CLAUDE.md` /
`builder-base-development` skill reference `pysrc/processYaml.py::projectCreate`
and `::projectOpen`. Update those path references to the new module names as a
final documentation pass.

## Execution Phases

1. **Create `projectShared.py`** — move the module helpers + the free
   `generateHierarchy` + the module constants (`continueOnError`,
   `CURRENT_YAML_FORMAT`, `yaml`). Apply the dirMacros refactor here: drop the
   `dirMacros = None` global and add the `macros` parameter to `expandDirMacros`,
   `expandNewModulePath`, and `resolveFilePath` (bodies otherwise unchanged;
   `_expand_with_macros` is untouched). Keep imports minimal.
2. **Create `projectConfig.py`** — move `class config` verbatim.
3. **Create `projectOpen.py`** — move `class projectOpen`; add shared/config
   imports; replace bare helper calls with `projectShared.<helper>` (including
   the `generateHierarchy` method body); convert the loader's global write to
   `self.dirMacros = self.config.getConfig('DIRS')`.
4. **Create `projectCreate.py`** — move `class projectCreate`; add shared/config
   imports; replace bare helper calls with `projectShared.<helper>` (including
   the `generateHierarchy` method body); introduce `self.dirMacros` (seed in
   `__init__`, build/persist in `projectDirs()`); pass `self.dirMacros` to the
   helper calls in `__init__`/`projectDirs`/`configTemplates`/
   `postYamlExternalScript`/`getFileList`/`saveIncludeFiles`; delete both
   `global dirMacros` declarations.
5. **Delete `processYaml.py`.**
6. **Repoint all code imports** per the table (including removing the two dead
   imports in `renderer.py`/`docgen.py` and the `newModule.py` reference
   renames).
7. **Repoint all unittest imports.**
8. **Update comments/docstrings and CLAUDE.md/skill path references.**

Do steps 1–5 in one pass, then 6–8, so the tree is never half-wired longer than
necessary.

## Verification

- `cd builder/base && python -c "import pysrc.projectCreate, pysrc.projectOpen, pysrc.projectConfig, pysrc.projectShared"`
  to catch import/cycle errors immediately.
- `grep -rn "processYaml" builder/` returns **zero** code references (only
  intentional historical mentions, if any, in plan files).
- `make clean && make gen` succeeds; diff the generated tree against a
  pre-refactor build — must be identical.
- `make run` passes.
- `cd builder/base && make unittest` (runs `unittest/run_all_tests.sh`) passes —
  this exercises the repointed test imports across `projectOpen`,
  `projectCreate`, `CURRENT_YAML_FORMAT`, and the eval/param suites.

## Risks & Notes

- **`dirMacros` refactor** is the only place touching logic rather than just
  moving it. Two checks guard correctness: (a) `self.dirMacros` must be seeded
  before `resolveFilePath` @2989 runs (it is, at @2970), and (b) the collapsed
  `expandDirMacros` must preserve the leading-`$`-only expansion semantics
  exactly. A `KeyError`/`None` here surfaces immediately as a bad schema or
  output path during `make gen`. The unit suite plus the DB diff cover it.
- **`config.data` is a class-level mutable dict** shared across instances. This
  is pre-existing behavior — move it verbatim, do not "fix" it in this refactor.
- **`generateHierarchy`'s `OrderedDict` import** comes from `typing` in the
  current file; preserve the exact import to avoid any behavior change.
- `builder/base` is a git submodule — per its CLAUDE.md, **do not stage or
  commit**; leave changes in the working tree for the user.
- Scope discipline: no method bodies, validation, or view logic change. If
  something looks improvable mid-move, leave it.
