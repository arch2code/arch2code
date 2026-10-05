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
    *   **Configuration:** The testbench `<tb>Config` class (a `testBenchConfigBase`) registers run-time parameters with `addParam`.
    *   **Top Level:** Define the testbench top module, instantiate the DUT, and connect interfaces.
    *   **Environment:** Initialize verification components (drivers, monitors, scoreboard).

    ```cpp
    // <tb>Config.cpp, user region of the Config class
    void addProgramOptions(po::options_description &options) override
    {
        addParam("num_packets", 100);   // default and maximum
    }

    // anywhere in the testbench
    uint64_t numPackets = testBenchConfigBase::getParam("num_packets");
    ```

    *   **`--param key,value`:** Sets a registered parameter for one run, for example `build/run myTb --param num_packets,50`. The registered value is both the default and the upper bound. A command-line value from 0 up to that bound replaces the default. A larger value stops the run with exit status 2, and a key registered with 0 cannot be set from the command line. Repeat `--param` for several keys. Each key may be given once, counting both the command line and the config file; a second occurrence stops the run with exit status 2.
    *   Register a key in `addProgramOptions` or `handleProgramOptions`. Both run before `--param` is applied. A key first registered from a module constructor is registered too late and is rejected as unknown.
    *   A key the testbench did not register stops the run with exit status 2 and prints the registered keys.
    *   A missing value, or a value that is not a non-negative integer (`5abc`, `-1`), also stops the run with exit status 2, naming the key and the value.
    *   `--verbosity`, `--instVerbosity` and config-file `blockVerbosity` take `low`/`0`, `med`/`medium`/`1`, `high`/`2` or `full`/`3`, case-insensitive. Any other value stops the run with exit status 2 and prints the accepted values.

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

    A `Config.cpp` commonly spells a DUT `Config` type, as any `dynamic_cast<<child><Cfg> *>(tb_ptr->external.<member>.get())` must. The `tbConfig --section=prerequisites` region imports the DUT block's own Config module for you (`import <project>.<block>.config;`). A Config of any other block, a parameterizable child included, is your import in the same slot, spelled the same way with that block's declaring project and name.

5.  **Simulation Control:**
    *   **Start/Stop:** Use `sc_start()` and `sc_stop()`.
    *   **Timeout:** Implement a watchdog timer to prevent infinite loops.

    ```cpp
    sc_start(100, SC_MS); // Run for 100ms
    if (sc_get_status() != SC_STOPPED) {
        log_.logError("Simulation timed out!");
    }
    ```

6.  **Test sequencing with `testController`:**
    *   A testbench lists its tests, in run order, by calling `testController::GetInstance().set_test_names({...})` from `createTestBench` or `handleProgramOptions`. The call must come before any block that uses `ADD_TEST` is built, so put it before `createTbTop()`. The scaffolded `final()` asserts `are_all_tests_complete()`, which fails until every listed test has completed.
    *   **`ADD_TEST` is the recommended form.** A test is a member function of a block or the External. It takes no arguments and returns `void`. Its name is the test name and must match a name in the list exactly. Register it in the constructor body, after the generated region, with `ADD_TEST(name);`, the same way `SC_THREAD(name);` registers a thread. The framework starts the function when its turn comes and completes the test when it returns, so the function never calls `register_test_name`, `wait_test` or `test_complete`. The macro needs `#include "testController.h"` in the `// user #includes here` slot, the global module fragment. In the `// user imports here` slot the header would attach `testController` to this module, which then gets a second, empty singleton that the testbench's `set_test_names` never reaches.

    ```cpp
    // <tb>Config.cpp, createTestBench
    testController::GetInstance().set_test_names({"test_rdy_vld", "test_req_ack"});

    // a model or External class
    void test_req_ack(void);
    void endOfTestVoter(void);

    // its constructor body, after the generated region
    ADD_TEST(test_req_ack);
    SC_THREAD(endOfTestVoter);

    void myBlock::test_req_ack(void)
    {
        wait(1, SC_NS);          // start delay, if the test needs one
        // ... drive and check ...
    }

    void myBlock::endOfTestVoter(void)
    {
        endOfTest eot(true);
        testController::GetInstance().wait_all_tests_complete();
        eot.setEndOfTest(true);
    }
    ```

    *   **Run order.** The `set_test_names` list sets the order, across every block. The order of the `ADD_TEST` lines and the order the blocks are built do not matter. A test must not rely on an earlier one, because `--test` can run it alone. In `examples/mixed`, `--test test_mem_hier_cpu_read` fails for this reason. It reads memory that `test_mem_hier_blockd_write` writes.
    *   **Start delay.** `ADD_TEST` takes no delay. Where an old-style test passed one to `wait_test`, write `wait(...)` as the first line of the function. Leaving it out raises no error, but the test starts earlier and its sim timestamps change.
    *   **One test in several blocks.** Functions with the same name in different blocks form one test, which completes when all of them have returned. Every instance of a block that adds the function adds one more. `examples/mixed` splits `test_reg_cpu_rwg` this way: `cpu` writes the register and `blockGLeaf` checks the value it receives.
    *   **End-of-test voter.** Vote from one separate thread that waits on `wait_all_tests_complete()`, as above. Never put a voter inside an `ADD_TEST` function. A voter there registers only when its test starts, so an earlier test can vote and end the run before later tests register their voters.
    *   **Mixing the forms.** One testbench can run some tests with `ADD_TEST` and others with old-style threads, so a testbench can move to `ADD_TEST` one block at a time. Each test uses one form. `examples/ip_test`'s `fwModelMain::startupInit` keeps the old form because it is one procedure, not one function per test. It runs two tests in a row and holds the end-of-test voter. For the same reason a `--test` run of that testbench never completes (see `--test` below).
    *   **Checks.** Once any `ADD_TEST` has run, a warning before simulation names every test that will run and has no `ADD_TEST`. An old-style thread must run each one. Otherwise the run never completes that test. If `--scTimeLimit`, a watchdog or another voter ends the run, `final()` fails. If none does, the run hangs. A testbench that never uses `ADD_TEST` gets no warning. A name run both ways stops the run with exit status 1, whether `register_test_name` or `ADD_TEST` comes first. A function whose name is not in the list stops construction with `ERROR: test name <name> is not valid`, exit status 1. Calling `ADD_TEST` before `set_test_names`, or `set_test_names` again after an `ADD_TEST`, also exits with status 1, and the message names the mistake.
    *   **Two functions in one block under one test name.** One class cannot hold two functions with the same name, so `ADD_TEST` cannot express this. `testController::GetInstance().add_test("name", [this]() { secondHalf(); });` registers a second function under the same name. Capture only `this`: a lambda that captures a constructor local by reference reads freed memory when the test runs.
    *   **The old form is still supported.** A test thread calls `register_test_name(name)`, then `wait_test(name)` to block until its turn, runs, and calls `test_complete(name)`. `wait_test` takes an optional start delay. Several threads may register the same name; the test completes when all of them have called `test_complete`. A thread that ends the run waits on `wait_all_tests_complete()`.

    ```cpp
    // a model or External thread
    testController &controller = testController::GetInstance();
    controller.register_test_name("test_req_ack");
    controller.wait_test("test_req_ack");
    // ... drive and check ...
    controller.test_complete("test_req_ack");
    ```

    *   **`--listTests`.** Prints the declared names, one per line, and exits 0 without simulating. The names follow the run banner, which shows the testbench name, build header, command line and seed. With `--log`, the banner goes to the log file, and the console shows the `Logging redirected to:` line and then the names.
    *   **`--test <name>`.** Runs only the named tests. Repeat it for several; they run in the testbench's order, not the command-line order. A name the testbench did not declare stops the run with exit status 2 and prints the declared names. An `ADD_TEST` function of a test left out never starts. An old-style thread of a test left out waits in `wait_test` and never runs. Any later test that thread would have run, and any voter it holds, waits with it, so an old-style thread that runs several tests in a row can stall the run. If that thread holds a listed test, the run never completes that test. If `--scTimeLimit`, a watchdog or another voter ends the run, `final()` fails. If none does, the run hangs.
    *   Both options stop the run with exit status 2 if the testbench has declared no tests with `set_test_names` by the time `createTestBench` returns. A testbench that narrows the list itself, from its own option, is filtered on the list it passed.
