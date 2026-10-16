---
description: SystemVerilog RTL conventions and skill references for rtl/ directory
globs: "rtl/**/*.sv, rtl/**/*.svh"
alwaysApply: false
---
# SystemVerilog RTL Rules

These rules apply to files in `rtl/` directory.

For comprehensive guidance, refer to the skill files:

*   **`rtl-core.md`** -- Module structure, FSMs, reset logic, DFF macros, clock domains, naming conventions, coding idioms
*   **`rtl-interfaces.md`** -- Interface protocols and their `src`/`dst` modports (`rdy_vld`, `status`, `memory`, `external_reg`, AXI and the rest)
*   **`rtl-patterns.md`** -- Pipelines, interpolation, saturation, resource sharing, memory FSMs
*   **`rtl-registers.md`** -- Hand-written logic behind a block's registers: `ro`, `rw` and `ext` registers, the register clock domain, wide registers. The decoder and register handler are generated.
*   **`rtl-datapath.md`** -- A2C Pro datapath modules: `rdyVldFifo`, `inPlaceList`, `rdyVldCapture`, `incDec`
*   **`rtl-arbitration.md`** -- A2C Pro arbitration modules: `memArb`, `vldAckArb`, `lockLocation`, `rrArb`
*   **`systemc-to-rtl.md`** -- Converting SystemC models to RTL
*   **`rtl-to-systemc.md`** -- Converting RTL to SystemC models
