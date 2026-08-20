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

    **When you don't need it:** When the External is to be the DUT's inverse test surface only, with all stimulus hand-written in its user region. Then `--block` names the **DUT block itself** — not a `_tb` container — and `--excludeInst` is omitted. In that case the External has no sub-instances to manage (the DUT still instantiates its own children, in the DUT's own generated region) and `--excludeInst` is not required. There need not be a `_tb` container at all: `examples/simple_ip/ip` and `examples/ip_test/ip` have none. Where one does exist it can be bypassed deliberately — `pySocket_tb` holds a peer (`u_dut`), yet `examples/pySocket` still uses `--block=pySocket` with hand-written stimulus. In practice most real testbenches need surrounding blocks, so `--excludeInst` is the common case.

    **Usage:** `*External.cppm` carries the param line:

    ```cpp
    // GENERATED_CODE_PARAM --block=<tb_block> --excludeInst=<dut_instance> --mode=module
    ```

    *   `--block` is the `_tb` wrapper block name from the YAML.
    *   `--excludeInst` is the DUT instance name as it appears in the YAML `instances:` section.
    *   If the instance name doesn't match any instance in the block, the generator produces an error.

    **Example** — `examples/mixed/arch/yaml/mixed.yaml` defines the `mixed_tb` container:

    ```yaml
    instances:
      u_mixed: { container: mixed_tb, instanceType: mixed, instGroup: top }
      uCPU:    { container: mixed_tb, instanceType: cpu,   instGroup: top }
    ```

    The DUT is `u_mixed`. The External uses:

    ```cpp
    // GENERATED_CODE_PARAM --block=mixed_tb --excludeInst=u_mixed --mode=module
    ```

    This makes the External instantiate the surrounding blocks (here `uCPU`), while the Testbench instantiates `u_mixed` and binds it to the External.

4.  **Where to add your own `#include` / `import`:**

    `<block>External.cppm` and `<block>Testbench.cppm` are C++20 module interface units. They seed two user slots, and they are not interchangeable — the slot is chosen by what the content attaches to, not by convenience. Putting content in the wrong slot fails at link time or, worse, produces a null `dynamic_pointer_cast` at run time rather than a compile error.

    | What you are adding | Slot | Why |
    | :--- | :--- | :--- |
    | Header whose definitions live in a plain `.cpp` (a pimpl boundary, e.g. `model/b2p_deb_conv_impl.h`, `model/rgb_img_writer_impl.h` in `debayer`) | `// user #includes here` (global module fragment) | Its class must attach to the **global module** so it matches those `.cpp` definitions at link time. |
    | Header naming no module and no `Config` type (a plain helper class, e.g. `model/rgb_video_sink_config.h`) | `// user #includes here` (global module fragment) | Nothing forces module attachment; the GMF keeps it shared with plain translation units. |
    | A module `import` (e.g. `import a2c.endOfTest;`) | `// user imports here`, **first** | Imports are illegal in the global module fragment and legal only in the module preamble. |
    | Header that *names* module or `Config` types (a template wrapper, e.g. `model/b2p_deb_conv.h`, `model/rgb_img_writer.h`) | `// user imports here`, **after the imports** | It must attach to **this** module, and it needs the preceding imports already visible. |

    **Imports before includes, inside that second slot.** A `#include` is a non-import declaration, so the first one closes the preamble; anything the header then names must already have been imported above it, and an `import` placed after it is ill-formed. Ordering the slot the other way fails with `declaration of '<type>' must be imported from module '<m>' before it is required`.

    Give any header you put in a zone-sensitive slot an include guard: a GMF header is often included a second time in the same translation unit, and only the guard keeps it attached to the global module.

    Never reintroduce a textual `#include` of something that is now a module — `common/systemc/endOfTest.cppm` carries its own warning about this: including it in a module purview would attach a private per-module singleton and silently break end-of-test voting.

    **`<block>Config.cpp` has no zone rules.** It is a plain translation unit, not a module unit, so its single `// user #includes and imports here` slot accepts `#include` and `import` interleaved in any order.

    A `Config.cpp` commonly spells a DUT `Config` type — as any `dynamic_cast<<child><Cfg>> *>(tb_ptr->external.<member>.get())` must — and `import <block>.testbench;` does not supply it: the Config structs live in the *global module fragment* of the testbench modules, so an importer finds them reachable but **not visible**. The `tbConfig --section=prerequisites` region therefore emits `#include "<context>VariantConfig.h"` for you, one per config context the DUT block's view names (its own, plus each parameterizable child's). Do not delete it because the generated lines around it do not name a Config type — the code that needs it is yours.

    That covers the usual case, including a `tb_ptr->external.<member>` sibling whose Config is declared in the same context as the DUT's, because the header is per *context* rather than per block. A Config declared in some *other* context is not in that set and is still your include, in the same slot. Symptom either way: `fatal error: missing '#include "<context>VariantConfig.h"'; '<child>DefaultConfig' must be declared before it is used`.

5.  **Simulation Control:**
    *   **Start/Stop:** Use `sc_start()` and `sc_stop()`.
    *   **Timeout:** Implement a watchdog timer to prevent infinite loops.

    ```cpp
    sc_start(100, SC_MS); // Run for 100ms
    if (sc_get_status() != SC_STOPPED) {
        log_.logError("Simulation timed out!");
    }
    ```
