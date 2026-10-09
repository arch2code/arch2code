---
name: design-yaml-includes
description: Guide for splitting arch2code architecture across YAML files. Covers include visibility, projectFiles, using another project's files, and the C++ module, namespace and SV package each file generates, named from includeName. Use when adding a YAML file, an include, or a child project.
---
# Skill: YAML includes and multi-file designs

## Purpose
Split an architecture across YAML files with `projectFiles:` and `include:`, predict what each file generates, and use names from another project. For where YAML files and generated files sit on disk, see `setup-project.md`.

## How files load

*   The project file's `projectFiles:` lists the entry files, with paths relative to the project file.
*   A design file's `include:` lists the files whose names it uses, with paths relative to the including file.
*   Every file reached through either list is loaded. A file reached only through `include:` does not need a `projectFiles:` entry.
*   `projectFiles:` adds no visibility. Listing a file there does not make its names visible to any other file.

```yaml
# prj/yaml/my_chipProject.yaml
projectFiles:
  - ../../yaml/my_chip.yaml

# yaml/my_chip.yaml
include:
  - ../shared/yaml/shared_types.yaml
  - ../subsystem_a/yaml/subsystem_a.yaml
```

## Each file is its own context

Each YAML file is its own context, and `include:` only makes names visible. Nothing is inlined. A file sees itself, the files it includes, and the files those include. Nothing deeper is visible.

If `a.yaml` includes `b.yaml`, `b.yaml` includes `c.yaml`, and `c.yaml` includes `d.yaml`, then `a.yaml` sees the names in `b.yaml` and `c.yaml` but not `d.yaml`. To use a name from `d.yaml` in `a.yaml`, add `d.yaml` to the `include:` of `a.yaml`. List every file whose names you use rather than relying on a chain.

*   The order of the `include:` list does not matter. A file is processed after every file it includes.
*   Inside one file, declare a name in an earlier section than its use, for example `types:` before `structures:`.
*   A circular include stops `make db` with "Circular include dependancy detected".
*   A name used outside its scope fails `make db` with "value ... was not valid in context ...". When another loaded file declares it, the message names that file and says to add it to the `include:` chain.

## What each file generates

A file generates context files only when it declares `constants:`, `types:`, `enums:` or `structures:`. A file that declares only other sections, such as `interfaces:`, `ipParameters:`, `blocks:`, `instances:` or connections, produces no context file, and no generated code imports it. Entries inside `ipParameters:` do not count.

| Artifact | Location | Name |
| :--- | :--- | :--- |
| C++ module | `model/` | `<includeName>Includes.cppm` |
| SystemVerilog package | `rtl/` | `<includeName>_package.sv`, package `<includeName>_package` |
| Firmware header | `fw/` (`fw/include/` in the functional layout) | `<includeName>IncludesFW.h` and `.cpp`, only when the project's `fileMap` declares `includeFW` |

*   `includeName` is the file stem unless the file sets a top-level `includeName:`.
*   File names, and the SV package name, take the owning project's `scFilePrefix`, `svFilePrefix` or `fwFilePrefix` when it sets one.
*   The C++ module is `<project>_<includeName>`, where `<project>` is the project that owns the file. An `includeName` that equals the project name, or already starts with `<project>_`, is used unchanged. The namespace is the module name plus `_ns`.
*   Copy a module name from the generated file's `export module` line rather than building it by hand.
*   Two files that give the same C++ module name fail `make db`, even when neither generates a context file. Two files whose generated SV packages share a name also fail. Two projects with no `svFilePrefix` hit this when each has a file of the same stem. Set `includeName:` in one of them.
*   A package name that matches a block's SV module name fails the same way. Set `includeName:` in one file, or give one project a distinct `svFilePrefix`.

For example, `common/yaml/shared_types.yaml` in project `common` generates `common/model/shared_typesIncludes.cppm` with `export module common_shared_types;` and namespace `common_shared_types_ns`, and `common/rtl/shared_types_package.sv`. A file `ip.yaml` in project `ip` gives module `ip`.

## Using another project's files

*   A child project opens only through the parent's `projectFiles:`, by listing the child's project file.
*   Naming a project file in `include:` stops `make db`. To use a child's names, include the child's design YAML file that declares them.
*   The child owns its files. Their generated files sit in the child's tree, placed by the child's layout, and their module names use the child's project name.
*   Reach a child's design file by its real path, the same one the child's own project file resolves to. A path through a symlinked copy names a second context.

```yaml
# prj/yaml/ip_testProject.yaml (parent)
projectFiles:
  - ../../common/prj/yaml/commonProject.yaml   # opens child project common
  - ../../top/yaml/ip_top.yaml

# top/yaml/ip_top.yaml
include:
  - ../../common/yaml/shared_types.yaml        # names owned by project common
```

Code in `ip_top`'s blocks then uses module `common_shared_types` and namespace `common_shared_types_ns`.

## Composing projects

*   One physical file provides each `projectName`. Two paths that open the same `projectName`, such as a vendored symlink and the real tree, stop `make db` until an ancestor project file selects one with `projectOverrides: { <projectName>: <path to its project file> }`. The highest ancestor's choice wins, so each level keeps the overrides its own standalone build needs.
*   A file belongs to the project that lists it directly in `projectFiles:`. Otherwise it belongs to the project that reaches it at the greatest depth from the root. When two projects reach it at the same depth, `make db` names the file and both projects. List the file in the owner's `projectFiles:`.
*   Only the root project's `topInstance` is built. A child's own testbench top, its `cpu` and its connections are parsed, but they get no address, no router slot, no `rtl.f` entry and no compiled RTL.
*   Generate each child before its parent. A parent compiles child files but never regenerates them. Migrate bottom-up: run `make migrate` in each child's `rundir/` first, again after every builder update, then in the parent.

The rules are in `builder/base/specs/spec-project-composition.md`.

## Path rules

*   Write paths relative to the including file, with `../` to go up. Absolute paths tie the project to one checkout.
*   An entry with no directory part, such as `types.yaml`, resolves to the project file's directory instead when that directory's `types.yaml` is already loaded. Write `./types.yaml` for a file beside the including file.

## Validation
Run `make db`. It reports a missing file, a circular include, a project file named in `include:`, a name outside a file's scope, and a module or package name two files share.
