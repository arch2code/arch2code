# Skill: Run Tandem Mode

## Purpose
Guide the user on building and running tandem verification for leaf blocks, covering both RTL/model and model/model configurations.
Tandem mode enables checking that RTL and Model implementations match. Ensure model/model works before RTL/model

## References
*   **Co-Simulation:** `verify-cosimulation.md` (Verilator wrapper setup, `hasVl` flag)
*   **Build:** `manage-build.md` (`make` targets)

## Instructions

1.  **Prerequisites:**
    *   The block must be a **leaf block** (no sub-instances). Tandem mode does not apply to hierarchical blocks.
    *   *_Reg blocks do not support tandem
    *   The block's YAML definition must have `hasVl: true`, `hasRtl: true`, and `hasMdl: true`.
    *   Generated tandem files must exist (`*Tandem.h/.cpp` in `base/`). Run `make gen` if missing.
    *   A2C Pro must be enabled (tandem is gated by `#ifdef A2CPRO` in `simController.cpp`).

    ```yaml
    blocks:
      gain_calculation:
        desc: "Digital gain calculation block"
        hasVl: true
        hasRtl: true
        hasMdl: true
    instances:
        u_gain_calculation: { container: gain, instanceType: gain_calculation, instGroup: top }
    ```

2.  **Two Tandem Configurations:**

    **Model/Model** -- run two SystemC model instances in parallel:
    *   Both sides instantiate `<block>_model` (SystemC model).
    *   Does NOT require Verilator. Standard build is sufficient.
    *   Run with `--vlType model`.
    *   Useful for: Validating that the model is tandem safe and that synchronization is working correctly. When errors occus consult systemc-synchronization skill
    *   Model must be running clean before attempting to debug RTL/Model
    *   Optional use `--delay` and `--delayMode` to check model works eg `--delay 10` will cause the primary to run with delays 

    **RTL/Model** -- compare RTL (via Verilator) against the SystemC golden model:
    *   Primary side instantiates `<block>_verif` (Verilator `_hdl_sc_wrapper`).
    *   Secondary side instantiates `<block>_model` (SystemC model).
    *   Requires building with `VL_DUT=1` and running with `--vlType verif`.

3.  **Build:**

    **Model/model (no Verilator needed):**

    ```text
    cd rundir
    make
    ```

    **RTL/model (Verilator required):**

    ```text
    cd rundir
    make VL_DUT=1
    ```

4.  **Run:**

    Command-line flags (defined in `simController.cpp`):
    *   `--vlInst <hierarchy>` -- dot-separated instance path to the leaf block (the framework prepends `tb.` automatically).
    *   `--vlType verif|model` -- selects the primary instance type.
    *   `--vlTandem` -- enables tandem mode.
    *   `--vlTrace` -- (optional) enables VCD waveform dump.

    **Example:** tandem on `gain_calculation` (instance path: `gain.u_gain_calculation`):

    ```text
    # Model/model tandem
    ./build/run gain --vlInst gain.u_gain_calculation --vlType model --vlTandem

    # RTL/model tandem
    ./build/run gain --vlInst gain.u_gain_calculation --vlType verif --vlTandem

    # RTL/model tandem with VCD tracing
    ./build/run gain --vlInst gain.u_gain_calculation --vlType verif --vlTandem --vlTrace
    ```

5.  **How It Works:**
    *   `instanceFactory` replaces the named instance with a `*Tandem` wrapper (e.g., `gain_calculationTandem`).
    *   The wrapper creates two sub-instances: `verif` (PRIMARY) and `model` (SECONDARY).
    *   Port tee threads fork all interface transactions to both instances.
    *   Both instances process the same stimulus independently.

6.  **Determining the `--vlInst` Path:**
    *   Identify the leaf block's instance name in the YAML `instances:` section.
    *   Build the dot-separated path from the testbench top down to that instance, excluding the `tb` prefix.
    *   Example: if the testbench creates `gain`, which contains `u_gain_calculation`, the path is `gain.u_gain_calculation`.

## Constraints
*   Tandem mode only works on **leaf blocks** -- blocks that do not contain sub-instances.
*   Requires A2C Pro build (`-DA2CPRO`).
*   The `--vlInst` path must exactly match the instance hierarchy in the testbench.
*   For RTL/model, the Verilator wrapper library must be built first (`make VL_DUT=1`).
