---
description: SystemC model conventions for files in model/ directory
globs: "model/**/*.cppm, model/**/*.cpp, model/**/*.h"
alwaysApply: false
---
# SystemC model rules

These rules apply to files in `model/`. Also read `systemc-shared.md`.

*   `systemc-core`: the `model/<block>.cppm` layout and user slots, registers and memories, threads, logging.
*   `systemc-interfaces`: the call for each port family.
*   `systemc-patterns`: producer-consumer, one thread on several ports, multi-cycle bursts, trackers.
*   `systemc-synchronization`: shared events, `synchLock` and tandem-safe `arb()`.
*   `rtl-to-systemc`: writing a model from RTL.
