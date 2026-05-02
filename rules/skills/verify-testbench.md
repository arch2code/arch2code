---
name: verify-testbench
description: Guide for creating testbenches, configuring verification components, and using scoreboards in SystemC
---
# Skill: Verify Testbench

## Purpose
Guide the user on creating testbenches, configuring verification components, and using scoreboards.

## References
*   **Code Generation Markers:** `ARCH2CODE_AI_RULES.md` (Section 9 — "Code Generation Markers — Comprehensive Reference") for all `GENERATED_CODE_PARAM` and `GENERATED_CODE_BEGIN` options including `--excludeInst`, with architecture diagrams.

## Instructions

1.  **Testbench Structure:**
    *   **Configuration Factory:** Use `testBenchConfigFactory` to manage test parameters.
    *   **Top Level:** Define the testbench top module, instantiate the DUT, and connect interfaces.
    *   **Environment:** Initialize verification components (drivers, monitors, scoreboard).

    ```cpp
    // Example from verification/testbench.cpp
    class myTestBench : public testBenchBase {
    public:
        myTestBench() {
            // Register test parameters
            testBenchConfigFactory::registerParam("num_packets", 100);
            // ...
        }
        void run() override {
            // Main test sequence
            // ...
        }
    };
    ```

2.  **Trackers & Scoreboarding:**
    *   **Trackers:** See the **Debug** skill for details on using `tracker<T>`.
    *   **Scoreboard:** Compare expected vs. actual transactions.
    *   **Tandem Verification:** If enabled, use tandem DPI calls to compare RTL state with SystemC model state.

    ```cpp
    // Scoreboard Example
    class myScoreboard : public sc_module {
        void check(const transaction& actual) {
            transaction expected = expected_queue.pop();
            if (actual != expected) {
                log_.logError("Mismatch!");
            }
        }
    };
    ```

3.  **External Module & `--excludeInst`:**

    The testbench framework splits into two generated pieces: the **Testbench** module (instantiates the DUT and the External) and the **External** module (provides the test environment around the DUT). The `_tb` block in YAML defines the complete test container — it holds the DUT instance alongside all the surrounding blocks (stimulus sources, sinks, CPU, decoders, etc.).

    The `--excludeInst` option in `GENERATED_CODE_PARAM` tells the generator which instance inside the `_tb` block is the DUT. The generator then:
    *   Puts the DUT in the Testbench module.
    *   Puts everything else (the surrounding blocks) in the External module.
    *   Turns connections that cross between the DUT and the surrounding blocks into the External's ports, which the Testbench binds.

    **When to use `--excludeInst`:** When the DUT is a complex block with multiple surrounding test blocks (sources, sinks, CPU, decoders) that all live together in the `_tb` container. This is the standard pattern for any DUT that has external interfaces needing drivers/monitors.

    **When you don't need it:** A simple leaf block with no surrounding blocks — where the `_tb` container holds only the DUT instance. In that case the External has no sub-instances to manage and `--excludeInst` is not required. In practice most real testbenches need surrounding blocks, so `--excludeInst` is the common case.

    **Usage:** Both the `*External.h` and `*External.cpp` must have the same param line:

    ```cpp
    // GENERATED_CODE_PARAM --block=<tb_block> --excludeInst=<dut_instance>
    ```

    *   `--block` is the `_tb` wrapper block name from the YAML.
    *   `--excludeInst` is the DUT instance name as it appears in the YAML `instances:` section.
    *   If the instance name doesn't match any instance in the block, the generator produces an error.

    **Example** — `debayer_tb.yaml` defines:

    ```yaml
    instances:
      debayer_tb:   { container: debayer_tb, instanceType: debayer_tb,     instGroup: top }
      u_raw_src:    { container: debayer_tb, instanceType: raw_video_src,  instGroup: top }
      u_debayer:    { container: debayer_tb, instanceType: debayer,        instGroup: top }
      u_rgb_sink:   { container: debayer_tb, instanceType: rgb_video_sink, instGroup: top }
      u_apb_decode: { container: debayer_tb, instanceType: apb_decode,     instGroup: top }
      u_cpu:        { container: debayer_tb, instanceType: cpu,            instGroup: top }
    ```

    The DUT is `u_debayer`. The External files use:

    ```cpp
    // GENERATED_CODE_PARAM --block=debayer_tb --excludeInst=u_debayer
    ```

    This makes the External instantiate `u_raw_src`, `u_rgb_sink`, `u_apb_decode`, and `u_cpu`, while the Testbench instantiates `u_debayer` and binds it to the External.

4.  **Simulation Control:**
    *   **Start/Stop:** Use `sc_start()` and `sc_stop()`.
    *   **Timeout:** Implement a watchdog timer to prevent infinite loops.

    ```cpp
    sc_start(100, SC_MS); // Run for 100ms
    if (sc_get_status() != SC_STOPPED) {
        log_.logError("Simulation timed out!");
    }
    ```
