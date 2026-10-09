---
description: Core arch2code project conventions, naming rules, design checklist, and critical constraints
globs: "**/*.yaml, **/*.sv, **/*.svh, **/*.cppm, **/*.cpp, **/*.h"
alwaysApply: false
---
# Project conventions

## Project context
- **Toolchain**: arch2code (Python-based generator).
- **Languages**: YAML (Architecture), SystemVerilog (RTL), SystemC (Model), Python (Tooling).
- **Philosophy**: YAML is the Single Source of Truth (SSoT). Never modify generated code between the markers.

## Critical constraints
1.  **Command execution**:
    -   NEVER run `python arch2code.py` directly. The one exception is `arch2code.py --newproject`, which creates a project before any makefile exists.
    -   ALWAYS use the `make` targets in `manage-build` (`db`, `gen`, `newmodule`, `clean`, `run`, `lint`). It says which directory each runs in.
2.  **File creation**:
    -   Before creating any implementation file (`.sv`, `.cppm`, `.cpp`, `.h`) or enabling a missing generated artifact with `hasRtl`, `hasMdl`, `hasVl`, or `hasTb`, load the `manage-build` skill.
    -   ALWAYS use `make newmodule` first for arch2code-scaffolded files, even when the block already exists.
    -   Example: changing an existing block from `hasRtl: false` to `hasRtl: true` requires `make newmodule` to scaffold the RTL file, followed by `make gen`.
    -   Only create files manually when they are genuinely user-owned and not scaffolded by arch2code.
3.  **Code editing**:
    -   NEVER edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` markers.
    -   If this code needs changing, rerun the generators.
    -   Only edit outside of these regions.
4.  **Deleting implementation files (.sv, .cppm, .cpp, .h)**
    - Do not delete implementation files unless the user asks. `make gen` does not recreate a deleted file. `make newmodule` recreates it only as a fresh scaffold, so the hand-written code is lost.

## Architecture rules (YAML)
Before suggesting YAML changes, verify against `builder/base/config/schema.yaml` and `ARCH2CODE_AI_RULES.md`.

### Naming conventions
-   **Constants**: `UPPER_SNAKE_CASE` (e.g., `BUFFER_SIZE`)
-   **Types/structures**: `snake_case_t` (e.g., `packet_t`)
-   **Blocks/Interfaces**: `snake_case` (e.g., `dma_controller`)
-   **Instances**: `u_snake_case` (e.g., `u_dma_controller`)
-   **Enums**: `UPPER_SNAKE_CASE` (e.g., `STATUS_IDLE`)

### Design checklist
-   [ ] **Widths**: Give each non-enum type exactly one of `width`, `widthLog2` or `widthLog2minus1`.
-   [ ] **Decoders**: The register-bus router is a **generated** block. Declare it with a populated `addressBlock:` and instance it in the container of the leaves it serves. Its RTL comes from `apbDecodeModule`, which `make newmodule` selects. NEVER hand-author a top-level decoder. See `design-register-decode.md`.
-   [ ] **Reg handlers**: NEVER create a register handler block (`<block>` plus `fileGeneration.regBlockNaming.blockSuffix`). The generator creates it.
-   [ ] **Connections**: Connections are for the SAME container. Use `connectionMaps` for hierarchy.
-   [ ] **References**: Verify all types, structures, and instances exist before using them.

## Implementation guidelines
-   **SystemVerilog**: Use `logic`. Write flops with the DFF macros. See `rtl-core`.
-   **SystemC**: Never edit `base/<block>Base.cppm`. Write the model in the user slots of `model/<block>.cppm`. See `systemc-core`.
