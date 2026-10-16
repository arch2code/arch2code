---
name: manage-address-space
description: Guide for configuring the project.yaml address-policy sections (instanceGroups, addressObjects placement and alignment) and firmware header generation (includeFW, regAddresses)
---
# Skill: manage address space

## Purpose
This skill covers the two address-policy sections of the top-level
`project.yaml`, `instanceGroups:` and `addressObjects:`, and firmware header
generation.

Use `design-register-decode.md` for everything about decode: where registers
and memories live, `regAccess`, routers (`addressBlock:`), `registerPorts:`,
address-group naming, and worst-case sizing of parameterizable registers and
memories. A project that has an `addressControl.yaml` must be converted
first: run `make migrate` (see `migrate-project.md`).

## 1. `addressObjects:`

`addressObjects:` places each block's registers and firmware-accessible
memories at offsets inside the block's address space. A project with any
register or `regAccess` memory needs it. Without it every object keeps offset
0, and the model asserts on the overlap.

```yaml
# In project.yaml
addressObjects:
  memories:
    alignment: memsize
    sizeRoundUpPowerOf2: true
    sortDescending: true
  registers:
    alignment: 8
    sortDescending: true
```

*   **Keys.** `memories` places `regAccess` memories. `registers` places
    registers. A `regType: memory` register is placed with the `registers`
    key but takes its alignment and rounding from the `memories` row, so a
    project with one needs both rows.
*   **Key order sets placement.** Within each block, offsets start at 0 and the
    first key's objects take the low offsets. The example puts memories below
    registers.
*   **`alignment`.** An integer aligns each object to that many bytes.
    `memsize`, for memories, aligns each memory to its own size, which keeps
    the decode simple. Pair it with `sizeRoundUpPowerOf2: true`.
*   **`sizeRoundUpPowerOf2`.** Rounds a memory's size up to a power of two, at
    least 4 bytes.
*   **`sortDescending`.** Places the largest objects first within each block.
    Without it, objects keep their declaration order, so offsets change only
    when you change the YAML.

Parameterizable registers and memories are placed at their worst-case size.
A row's width comes from its structure's `maxBitwidth`. A memory whose
`wordLines` names a block parameter reserves the `maxValue` of the
`ipParameters:` constant backing that parameter, and `make db` rejects a
variant that binds the parameter above that `maxValue`.
`design-register-decode.md` §5 has the full rule.

## 2. `instanceGroups:`

`instanceGroups:` declares the names an instance's `instGroup:` may use. An
`instGroup:` naming a group that is not declared fails `make db`. Its
`varType:` and `enumPrefix:` keys have no effect.

```yaml
# In project.yaml
instanceGroups:
  top: {}
```

```yaml
# In a design file
instances:
  uIp: { container: top, instanceType: ip, instGroup: top }
```

## 3. Firmware headers (`includeFW`)

Firmware headers are on when `project.yaml` declares an `includeFW` entry under
`fileGeneration.fileMap`. A project created with `--newproject` and firmware
enabled already has it:

```yaml
# In project.yaml
fileGeneration:
  fileMap:
    includeFW: {name: "IncludesFW", ext: {hdr: "h", src: "cpp"}, cond: {smartInclude: true}, mode: context, basePath: fwInc, langDomain: fw, desc: "yaml based fw include file"}
```

*   `mode: context` writes one `<context>IncludesFW.{h,cpp}` pair per YAML file.
*   `cond: {smartInclude: true}` writes a context's files only when it has
    types, structures or constants. These come from `types:` (or its alias
    `enums:`), `structures:`, `constants:`, `encoders:`, and the address enum of
    a router's `addressBlock:`, which lands in the router block's own file. A
    context holding only registers, memories or `ipParameters:` gets no file.
*   `basePath:` names the `dirs:` segment to write into.
*   `langDomain: fw` applies `fwFilePrefix` to the file names.

## 4. Project-wide address header (`regAddresses`)

`regAddresses` writes one header for the whole project with the instance and
register address defines. It is opt-in. A firmware project from `--newproject`
carries the entry commented out after `includeFW`. Uncomment it or add it:

```yaml
# In project.yaml, under fileGeneration.fileMap
regAddresses: {name: "regAddresses", ext: {hdr: "h"}, mode: project, basePath: fwInc, langDomain: fw, desc: "Per-project instance and register address defines"}
```

*   `name:` is the file's basename, used verbatim. A project-mode file takes
    neither the project name nor a filename prefix, so a project usually
    spells its own name, such as `axi4sRegAddresses`.
*   `basePath:` picks the segment, commonly `fwInc` or `model`.
*   Run `make newmodule` to create the file, then `make gen` to fill it.

To keep the file project-owned instead, leave the entry out. Write the file
with a `GENERATED_CODE_PARAM --project=<projectName>` line and the `includes`
template's `addresses` and `regAddresses` regions, then list it on
`EXTRA_SC_GEN_FILES` in `include/make/shared.mk`. See `manage-build.md`.

## References
*   Decode hierarchy, `regAccess`, group naming and parameterizable sizing:
    `design-register-decode.md`
*   Build and scaffold targets: `manage-build.md`
*   Converting `addressControl.yaml`: `address-migration.md`
