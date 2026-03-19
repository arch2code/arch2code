---
name: design-yaml-includes
description: Guide for using YAML include directives and managing multi-file architecture definitions in arch2code
globs: arch/yaml/**/*.yaml
alwaysApply: false
---
# Skill: YAML Include & Multi-File Management

## Purpose
Guide the user on splitting architecture definitions across multiple YAML files using `include:` directives and `projectFiles` in `project.yaml`.

## Two Mechanisms

### 1. `projectFiles` in `project.yaml`

Lists the top-level YAML files that define the architecture. These are the entry points the toolchain loads.

```yaml
# project.yaml
projectName: my_chip
topInstance: top_tb

projectFiles:
  - top.yaml
  - subsystem_a/subsystem_a.yaml
  - subsystem_b/subsystem_b.yaml
  - shared/shared_types.yaml
```

Paths are relative to the directory containing `project.yaml`.

### 2. `include:` Directive in YAML Files

Any YAML file can include other files. Included files are parsed as if their content were inlined at the include point.

```yaml
# subsystem_a/subsystem_a.yaml
include:
  - ../shared/shared_types.yaml
  - local_types.yaml

blocks:
  subsystem_a:
    desc: "Subsystem A"
```

**Path rules:**
*   Paths are **relative to the including file**, not the project root.
*   Use `../` to navigate up directories.
*   **Never** use absolute paths.

## Best Practices

### 1. Organize by Subsystem

```
arch/yaml/
  project.yaml
  config/
    addressControl.yaml
  shared/
    shared_types.yaml        # Common types and constants
    shared_interfaces.yaml   # Common interfaces
  subsystem_a/
    subsystem_a.yaml         # Blocks, instances, connections for subsystem A
  subsystem_b/
    subsystem_b.yaml         # Blocks, instances, connections for subsystem B
  top.yaml                   # Top-level instances and connections
```

### 2. Shared Types First

Put commonly referenced types, constants, and structures in a shared file. Include it from subsystem files that need those definitions.

```yaml
# shared/shared_types.yaml
constants:
  DATA_WIDTH: {value: 64, desc: "Common data width"}

types:
  datapath_t: {width: DATA_WIDTH, desc: "Datapath type"}

structures:
  data_st:
    data: {varType: datapath_t, desc: "Data payload"}
```

```yaml
# subsystem_a/subsystem_a.yaml
include:
  - ../shared/shared_types.yaml

interfaces:
  my_data_if:
    interfaceType: rdy_vld
    desc: "Uses shared type"
    structures:
      - {structure: data_st, structureType: data_t}
```

### 3. Avoid Circular Includes

File A should not include File B if File B also includes File A. Structure your includes as a DAG (directed acyclic graph).

### 4. Include Order Matters

Elements must be defined before they are referenced. If File B uses a type from File A, File A must be included (directly or transitively) before File B defines structures using that type.

## Common Pitfalls

```yaml
# BAD - absolute path
include:
  - /home/user/project/arch/yaml/shared.yaml

# BAD - wrong relative path (common in nested directories)
include:
  - shared_types.yaml  # Won't find it if file is in a subdirectory

# GOOD - relative to current file
include:
  - ../shared/shared_types.yaml
  - common/interfaces.yaml
```

## Validation
*   Run `make db` to verify all includes resolve correctly.
*   Missing includes produce clear error messages with the expected path.
