# Plan: Template Identity Contract Cleanup

## Status

- **Direction:** complete. WI6, the last residual, is closed (descoped) as of
  2026-06-23 with a one-line sanitization alignment in `config.py`.
- **Status taxonomy:** **implemented in working tree** (commit `1c09e53`,
  2026-06-22; plus the 2026-06-23 `config.py` normalization alignment);
  not independently re-verified with `make gen` in this update.
- **Current state:** the core intent is implemented. The trigger helpers
  `module_name_from_include()` / `namespace_name_from_include()` are
  **removed** from `pysrc/intf_gen_utils.py`. Module / namespace / package
  identity is now spelled from the project-owned include identity
  `prj.includeName[context]` (via `cpp_module_name()` /
  `cpp_namespace_name()`) and from the `getContextData` view fields
  `contextIncludeName` and `contextStem`, rather than by splitting rendered
  filenames. `moduleScaffold.py` emits `export module` from
  `data["contextIncludeName"]`; `headers.py`, `classDecl.py`, and
  `baseClassDecl.py` spell imports/usings from `prj.includeName[context]`;
  the SV package name is `prj.includeName[context] + '_package'` in both
  `systemVerilogGeneratorHelper.py` and `package.py`; the SV
  filename/block consistency check moved out of the render path into the
  SystemVerilog generator.
- **Residual / deviations from the original work items:**
  - **WI1 alternative.** Module/namespace identity was routed through
    `getContextData` (`contextIncludeName`) and `prj.includeName[context]`
    rather than by persisting `moduleName` / `namespaceName` into
    `INCLUDEFILES`. This satisfies the goal (no filename-shape inference)
    by a different mechanism than the "Target Shape" sketch.
  - **WI6 closed (descoped, 2026-06-23).** `templates/systemc/config.py`
    continues to derive the legacy `<context>DefaultConfig` name from the
    `contextStem` view field rather than consuming the persisted
    `blocks.defaultConfig` column, and that is now the accepted final shape.
    Investigation showed the column cannot be cleanly consumed per render:
    `calcBlockConfigInfo()` derives `blocks.defaultConfig` from a block's
    `contexts[0]` (the context of the first parameterizing structure), not
    from the block's own `_context`, and that primary context is not
    persisted per block; constant-only config contexts (real, per
    `_configHeaderContexts()`) have parameterizable constants but no primary
    block, so there is no column value to read. The per-context struct name
    is fundamentally `<context-stem>DefaultConfig`. The only real defect —
    the template's incomplete sanitization (`-` only) versus the persisted
    rule (`-` and `.`) — is fixed: `config.py` now mirrors
    `calcBlockConfigInfo()`'s `.replace('-', '_').replace('.', '_')`, so the
    emitted name can no longer drift from `blocks.defaultConfig`. No
    `getContextData()`/contract change was made.
- **Goal:** remove fragile generated-identity derivation from filename and path
  strings in templates and template utilities.
- **Trigger (historical):** `pysrc/intf_gen_utils.py::module_name_from_include()`
  and `namespace_name_from_include()` stripped `.cppm` and `Includes` suffixes
  from `baseName`, then sanitized the result. Those helpers are now removed.

## Problem

SystemC module-mode rendering currently reconstructs C++20 module names and
exported namespace names from generated filenames:

- `templates/systemc/moduleScaffold.py` emits `export module ...` from
  `data["fileNameBase"]`.
- `templates/systemc/headers.py`, `classDecl.py`, and `baseClassDecl.py` emit
  `import ...` and `using namespace ...` from
  `data["includeFiles"][...][context]["baseName"]`.
- `pysrc/intf_gen_utils.py::wrap_module_namespace()` emits `export namespace`
  from `data["fileNameBase"]`.

This violates the builder/base ownership split. Template utilities should spell
syntax from already supplied fields; they should not infer semantic identity by
splitting filename strings. The durable upstream contract already exists in
`projectCreate.saveIncludeFiles()`, which persists `INCLUDEFILES`, but the
contract only stores `baseName` and `fileName`.

There is a related cleanup in `templates/systemc/headers.py`: when
`include_hdr` is absent, it derives a sibling header name from `include_cppm`
with `.removesuffix(".cppm") + ".h"`. That is also filename-shape inference and
should be replaced by an explicit contract or removed when the legacy path is no
longer required.

The same pattern appears in other templates:

- `templates/systemc/config.py` derives the legacy `<context>DefaultConfig`
  struct name from the `contextStem` view field. (Closed/descoped 2026-06-23:
  the per-context name is a pure function of the context stem and is not
  cleanly sourceable from the `blocks.defaultConfig` column, which is keyed off
  a block's unpersisted `contexts[0]`; constant-only config contexts have no
  block at all. The template's sanitization is aligned to
  `calcBlockConfigInfo()` so the emitted name cannot drift from the persisted
  one. See WI6.)
- `templates/systemc/structures.py` derives the generated
  `test_<context>_structs` C++ class name from the context path basename.
- `pysrc/systemVerilogGeneratorHelper.py` derives SystemVerilog package import
  names from `includeFiles[*][context]["baseName"]` via `Path(...).stem`, while
  `templates/systemVerilog/package.py` emits the package declaration from
  `prj.includeName[context] + "_package"`.
- `templates/systemVerilog/apbDecodeModule.py` and
  `templates/systemVerilog/moduleInterfacesInstances.py` compare the current
  output file stem to `blockName` inside the template path. The emitted module
  name still comes from `blockName`, but filename/block consistency checking is
  validation, not rendering.
- `templates/fileGen/fileGen.py` derives sibling header names for
  `include_src` and `includeFW_src` with
  `data["headerName"].replace(".cpp", ".h")`.

## Target Shape

`projectCreate.saveIncludeFiles()` should persist the module-facing identity for
context include artifacts. For `include_cppm` entries, `INCLUDEFILES` should
carry explicit fields such as:

```python
{
    "baseName": "ipIncludes.cppm",
    "fileName": ".../ipIncludes.cppm",
    "moduleName": "ip",
    "namespaceName": "ip_ns",
}
```

The exact names should be derived from project-owned include identity, not from
the final rendered filename. The most likely source is the existing
`includeName[context]` value available in `saveIncludeFiles()`, with a single
sanitization rule owned by project creation.

Rendering should then consume those fields directly:

- Imports use `includeFiles["include_cppm"][context]["moduleName"]`.
- Namespace directives use
  `includeFiles["include_cppm"][context]["namespaceName"]`.
- The current `.cppm` file's `export module` and `export namespace` use a
  current-context module identity supplied in the context data view, not
  `fileNameBase`.

The same rule should apply to related generated identities:

- Context Config default names come from `getContextData()`.
- Structure-test class names come from `getContextData()`.
- SystemVerilog package declarations and imports use one package-name contract.
- Generated source/header sibling relationships come from `INCLUDEFILES` or a
  file-generation view, not suffix replacement in templates.
- Filename/block consistency checks run before rendering or consume an explicit
  validation result; templates do not inspect output file stems.

## Work Items

1. Add explicit module identity fields to the persisted `INCLUDEFILES` contract
   for `include_cppm` entries in `projectCreate.saveIncludeFiles()`.

2. Add a narrow `projectOpen` view field for the current context module identity
   used by `.cppm` context rendering. This should be populated by
   `getContextData()` from DB/config data, not by reparsing the current output
   filename in templates.

3. Update SystemC module-mode templates to read the new fields directly:
   `moduleScaffold.py`, `headers.py`, `classDecl.py`, `baseClassDecl.py`, and
   any helper paths that call `wrap_module_namespace()`.

4. Remove `module_name_from_include()` and `namespace_name_from_include()` once
   the templates no longer need filename-derived names.

5. Replace or delete the `headers.py` fallback that synthesizes `.h` names from
   `.cppm` names. If header-mode compatibility is still required, represent the
   header artifact explicitly in `INCLUDEFILES`; do not infer it in the
   template.

6. ~~Stop recomputing the legacy default Config name in
   `templates/systemc/config.py`.~~ **Closed (descoped, 2026-06-23.)** The
   per-context `<context>DefaultConfig` struct name is a pure function of the
   context stem and cannot be sourced cleanly from the `blocks.defaultConfig`
   column: that column is keyed off a block's `contexts[0]` (not its
   `_context`, and not persisted), and constant-only config contexts have no
   block to read from. The actionable defect — the template's incomplete
   sanitization relative to the persisted rule — is fixed by aligning
   `config.py` to `calcBlockConfigInfo()`'s
   `.replace('-', '_').replace('.', '_')`. No view field was added.

7. Move the structure-test class name currently derived in
   `templates/systemc/structures.py` into `getContextData()`. The template
   should consume the precomputed class name and display string directly.

8. Add an explicit SystemVerilog package-name field for `package_sv` entries, or
   an equivalent context-view package-name field, and update
   `pysrc/systemVerilogGeneratorHelper.py` and
   `templates/systemVerilog/package.py` to consume the same contract.

9. Move the filename/block consistency check used by
   `templates/systemVerilog/apbDecodeModule.py` and
   `templates/systemVerilog/moduleInterfacesInstances.py` out of the template
   render path. The templates should emit module declarations from `blockName`
   without inspecting `data["fileName"]`.

10. Replace `templates/fileGen/fileGen.py` source-to-header substitutions for
    `include_src` and `includeFW_src` with an explicit sibling header field from
    `INCLUDEFILES` or a file-generation view.

11. Regenerate and verify with the normal make flow. At minimum, run `make gen`
   for `examples/ip_test`; if YAML or persisted config behavior changes, rebuild
   the DB first with `make clean` or the project-standard database target.

## Non-Goals

- Do not change user-authored YAML syntax unless a later review determines the
  module-name contract must be user configurable.
- Do not add template-side compatibility fallbacks for old `INCLUDEFILES`
  shapes. The compatibility boundary is user YAML accepted by `projectCreate`,
  not intermediate Python dictionaries.
- Do not broaden this into a general C++ module build-system cleanup.
- Do not chase local emitted-code punctuation edits such as trimming trailing
  commas, indentation slicing, enum last-element handling, or local `<Config>`
  spelling substitutions. Those are formatting/spelling concerns, not
  generated-identity lookup.

## Open Questions

- Should `moduleName` be the sanitized `includeName[context]` value with the
  configured context include suffix removed before persistence, or should
  `saveIncludeFiles()` persist a separate suffix-free context stem before file
  expansion?
- Is the `headers.py` `include_hdr` fallback still needed after the hard
  replacement to `.cppm`, or can the fallback be removed outright?
- ~~Should legacy context default Config naming continue to follow the context
  basename, or should it be reconciled with `blocks.defaultConfig` and the
  per-variant `configName` descriptors?~~ **Resolved (2026-06-23):** it
  continues to follow the context basename. `blocks.defaultConfig` is keyed off
  a block's unpersisted `contexts[0]` and constant-only contexts have no block,
  so the column is not cleanly per-context-keyed; the two are kept consistent by
  using one sanitization rule (`.replace('-', '_').replace('.', '_')`) in both
  `config.py` and `calcBlockConfigInfo()`.
- Should generated structure-test class names be persisted as part of context
  data, or should they be owned by a narrower test-structure view?
