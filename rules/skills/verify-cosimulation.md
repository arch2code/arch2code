# Skill: Verify Co-Simulation

## Purpose
Guide the user on performing co-simulation of RTL and SystemC models using Verilator. This allows verifying the RTL implementation against the SystemC reference model (Tandem Verification) or running RTL within a SystemC testbench.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Blocks & Instances" section for `hasVl` flag)

## Instructions

1.  **Enabling Verilator Generation:**
    *   In your YAML block definition, set `hasVl: true`.
    *   This triggers the generation of:
        *   `_hdl_sv_wrapper.sv`: SystemVerilog wrapper for the RTL.
        *   `_hdl_sc_wrapper.h`: SystemC wrapper class for the Verilator model.

    ```yaml
    blocks:
      dma_controller:
        desc: "DMA Controller"
        hasRtl: true
        hasMdl: true
        hasVl: true  # Enables Verilator wrapper generation
    ```

2.  **Using the Wrapper in SystemC:**
    *   Include the generated wrapper header.
    *   Instantiate the wrapper instead of (or alongside) the SystemC model.
    *   The wrapper exposes standard SystemC ports that match your block's interface.

    ```cpp
    #include "dma_controller_hdl_sc_wrapper.h"

    class myTestbench : public sc_module {
        // ...
        // Instantiate Verilator wrapper
        dma_controller_hdl_sc_wrapper* dut;
        
        void build() {
            dut = new dma_controller_hdl_sc_wrapper("dut");
            // Connect ports just like a normal SystemC module
            dut->clk(clk);
            dut->rst_n(rst_n);
            dut->apb_s->bind(*apb_channel);
        }
    };
    ```

3.  **Tandem Verification:**
    *   **Concept:** Run both the SystemC model (Golden Reference) and the RTL (via Verilator) in parallel.
    *   **Mechanism:** Compare state and transactions at key boundaries (interfaces, registers).
    *   **Setup:**
        *   Instantiate both models.
        *   Feed same stimulus to both.
        *   Use a scoreboard or "Tandem" mode in the framework to compare outputs.

4.  **Tracing:**
    *   Verilator supports waveform tracing (VCD/FST).
    *   Enable tracing in the wrapper or testbench configuration (typically via `vl_trace()` or makefile arguments).

5.  **Compilation:**
    *   Use `make gen` to generate the wrappers.
    *   Ensure your `Makefile` or build system compiles the generated Verilator C++ sources.

6.  **Troubleshooting:**
    *   **Signal Mismatches:** Ensure RTL port types match SystemC interface types.
    *   **Clocking:** Verilator models require explicit clocking. The wrapper usually handles pin connections, but ensure your testbench drives `clk`.
    *   **Build Errors:** Check `hasVl: true` is set and `make gen` ran successfully.
