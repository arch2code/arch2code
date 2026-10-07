---
name: verify-cosimulation
description: Guide for running Verilated RTL in place of a SystemC model instance (co-simulation) with VL_DUT and --vlInst, including wrapper generation, clocks and resets, and tracing
---
# Skill: Verify co-simulation

Co-simulation runs the RTL of one block instance, verilated, in place of its SystemC model inside the normal testbench. The rest of the design stays as models.

## Enable the wrapper
1.  Set `hasVl: true` on the block. `hasRtl` and `hasMdl` default to true.

    ```yaml
    blocks:
      dma_controller:
        desc: "DMA Controller"
        hasVl: true
    ```

2.  Run `make newmodule`, then `make gen`. `make newmodule` creates these files, and `make gen` fills them:
    *   `<block>_hdl_sv_wrapper.sv`, the SystemVerilog top Verilator compiles. A block with its own `params:` instead gets one `<block>_<variant>_hdl_sv_wrapper.sv` per variant, plus a shared `<block>_hdl_sv_wrapper.svh` body. A variant that another project declares for the block gets `<project>_<block>_<variant>_hdl_sv_wrapper.sv` in that project's `vl_wrap` directory, for example `examples/ip_test/bridge/verif/ipBridge_ip_variant1_hdl_sv_wrapper.sv`.
    *   `<block>_hdl_sc_wrapper.h`, the SystemC class around the verilated model. Its `end_ctor_init()` body is yours.
    *   `<block>VlRegistrar.cpp`, which registers the wrapper with the instance factory as `<block>_verif`.

    The wrappers go in the `vl_wrap` directory and the registrar in the `registrar` directory of the project's `dirs:` layout, for example `verif/vl_wrap/` and `registrar/`.

You never instantiate the wrapper yourself. The testbench keeps building the model hierarchy, and the instance factory swaps in the wrapper at run time.

## Build and run
From `rundir/`:

```text
make VL_DUT=1
build/run <testbench> --vlInst <instance path>
```

*   `make VL_DUT=1` verilates every `hasVl` block and links the result into `build/run`. See `manage-build`.
*   `--vlInst` names the instance to replace. The path is dot-separated and starts at the DUT, which the testbench names after the DUT block, so `--vlInst clkGen.uDivider` in `examples/clkGen` replaces child `uDivider` of DUT `clkGen`. A leading `tb.` is optional. A path that matches no instance fails the run with `Unknown instance <path>`.
*   `make run VL_DUT=1` runs with `--vlInst $(HDL_TOP_MODULE)`, which replaces the DUT top. Projects that verify every RTL instance add their own targets, such as `run-vl` in `examples/clkGen/rundir/Makefile`.
*   The named instance and everything below it run as RTL. The rest stays as models, so to check each block against model neighbours, run once per instance.

## Clocks and resets
The SC wrapper drives the RTL's input clocks and resets itself. It toggles each clock at the period declared in the YAML, holds each reset for that reset's `releaseCycles` edges of its own clock, then releases it. A clock or reset the RTL drives out is observed, not generated. The testbench drives none of them.

## Tracing
Add `--vlTrace` to the run command. It writes a VCD of the verilated instance to `simx.vcd` in the run directory. FST is not supported, and no make variable turns tracing on.

## Tandem
Tandem runs the RTL and the model side by side on the same stimulus and compares their outputs. It adds `--vlTandem` to `--vlInst`, works on leaf blocks only, and needs A2C Pro. A base build fails the run with `Tandem mode not supported`. In A2C Pro, see `run-tandem`.

## Troubleshooting
*   **`Attempted to create an instance <name> of an unregistered block type <block>_verif`.** Rebuild with `make VL_DUT=1`, because a plain `make` binary has no verilated wrappers. If that fails too, check `hasVl: true` on the block, then rerun `make newmodule` and `make gen` so the VlRegistrar exists.
*   **Port type mismatch.** The RTL port types must match the SystemC interface types the YAML declares.
