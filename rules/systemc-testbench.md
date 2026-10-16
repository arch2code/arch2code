---
description: SystemC testbench conventions for files in tb/ directory
globs: "tb/**/*.cpp, tb/**/*.cppm, tb/**/*.h"
alwaysApply: false
---
# SystemC testbench rules

These rules apply to files in `tb/`. Also read `systemc-shared.md`.

*   After `hasTb: true`, `make newmodule` creates `tb/<dut>/<dut>Testbench.cppm`, `<dut>External.cppm` and `<dut>Config.cpp`. The Testbench class is generated. Stimulus and checks go in the External's user region or in the models of the blocks around the DUT.
*   `verify-testbench` covers the External and `--excludeInst`, where an `#include` or `import` goes, `ADD_TEST`, run options, `errorCode::fail` and the end-of-test voter.
*   RTL against the model: `verify-cosimulation`. Tandem, an A2C Pro feature: `run-tandem`.
