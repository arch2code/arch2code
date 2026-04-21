---
description: SystemVerilog RTL conventions and skill references for rtl/ directory
globs: "rtl/**/*.sv, rtl/**/*.svh"
alwaysApply: false
---
# SystemVerilog RTL Rules

These rules apply to files in `rtl/` directory.

For comprehensive guidance, refer to the skill files:

*   **`rtl-core.md`** -- Module structure, FSMs, DFF macros, naming conventions, coding idioms
*   **`rtl-interfaces.md`** -- Interface protocols (`rdy_vld`, `status_if`, `memory_if`, `external_reg_if`, AXI)
*   **`rtl-patterns.md`** -- Pipelines, interpolation, saturation, resource sharing, memory FSMs
*   **`rtl-registers.md`** -- Register decoder architecture, external registers
*   **`rtl-datapath.md`** -- FIFOs, `inPlaceList`, `rdyVldCapture`, counters
*   **`rtl-arbitration.md`** -- `memArb`, `vldAckArb`, `lockLocation`
*   **`systemc-to-rtl.md`** -- Converting SystemC models to RTL
*   **`rtl-to-systemc.md`** -- Converting RTL to SystemC models
