---
name: verify-testbench
description: Guide for creating testbenches, configuring verification components, and using scoreboards in SystemC
---
# Skill: Verify testbench

## Create the testbench
1.  Set `hasTb: true` on the DUT block in the YAML.
2.  Run `make newmodule`, then `make gen`. `make newmodule` creates three files in `tb/<dut>/`, each seeded with `--block=<dut>`. When the DUT declares its own `params:`, each line also carries `--variant=<first declared variant>`, which selects the DUT's Config; edit it to test another declared variant. Without it `make gen` fails.
    *   `<dut>Testbench.cppm`, the testbench top. Its generated regions instantiate the DUT and the External and bind them, so you write no testbench top yourself.
    *   `<dut>External.cppm`, the test environment around the DUT.
    *   `<dut>Config.cpp`, the testbench configuration. It builds the hierarchy and declares the tests.
3.  To surround the DUT with other blocks, edit only the External's `GENERATED_CODE_PARAM` line, then run `make gen` again. See the next section.

The binary runs a testbench by its name: `build/run <dut> [options]`.

## The External and `--excludeInst`
The External is either the DUT's inverse alone or a test container's other instances.

*   **DUT inverse only.** Keep the seeded line, `--block=<dut>`. The External has no sub-instances, and all stimulus is hand-written in its user region. `examples/simple_ip/ip` and `examples/pySocket` work this way.
*   **Surrounding blocks.** Declare a test container block in the YAML that holds the DUT instance and the blocks around it: sources, sinks, a CPU, decoders. Retarget the External at it:

    ```cpp
    // GENERATED_CODE_PARAM --block=<container> --excludeInst=<dut instance> --mode=module
    ```

    The External then instantiates every instance of the container except the DUT. Each connection between the DUT and the other instances becomes an External port, which the Testbench binds. `--excludeInst` takes the DUT's instance name from the YAML `instances:` section. A name that matches no instance of the container is a generator error. Most testbenches with external interfaces use this form.

    `examples/mixed/arch/yaml/mixed.yaml` declares the container `mixed_tb`:

    ```yaml
    instances:
      u_mixed: { container: mixed_tb, instanceType: mixed, instGroup: top }
      uCPU:    { container: mixed_tb, instanceType: cpu,   instGroup: top }
    ```

    `mixedExternal.cppm` uses `--block=mixed_tb --excludeInst=u_mixed --mode=module`, so the External instantiates `uCPU` and the Testbench instantiates `u_mixed`.

The Testbench and Config keep `--block=<dut>`. For every marker option, see the "Code Generation Markers" section of `ARCH2CODE_AI_RULES.md`.

## Where to add your own `#include` or `import`
`<dut>External.cppm` and `<dut>Testbench.cppm` are C++20 module interface units with two user slots. Pick the slot by what the content must attach to. The wrong slot fails at link time, or gives a null `dynamic_pointer_cast` at run time.

| What you add | Slot | Why |
| :--- | :--- | :--- |
| A plain header that names no module type, such as `testController.h` or `q_assert.h` | `// user #includes here` (global module fragment) | Its declarations attach to the global module and match plain `.cpp` translation units, including any `.cpp` that defines the header's classes. |
| A module `import`, such as `import a2c.endOfTest;` | `// user imports here`, first | An import is legal only in the module preamble, never in the global module fragment. |
| A header that names a module's types or a `Config` type | `// user imports here`, after the imports | It must attach to this module and needs those imports visible. |

Inside the second slot, imports come first. The first `#include` closes the preamble, so an `import` after it is ill-formed, and a header that names a type imported only later fails with `declaration of '<type>' must be imported from module '<m>' before it is required`.

Give every header in either slot an include guard. A global-module-fragment header is often included twice in one translation unit, and only the guard keeps it attached to the global module.

Import a C++20 module unit such as `common/systemc/endOfTest.cppm`; never `#include` it. The compiler rejects the include, because the unit's `module;` line can only start a translation unit. Never copy its classes into a header either. A header copy included in a module purview attaches a private singleton and silently breaks end-of-test voting.

## `<dut>Config.cpp`
`<dut>Config.cpp` is a plain translation unit. Its one slot, `// user #includes and imports here`, takes `#include` and `import` in any order.

*   When the DUT block declares its own `params:`, the generated `prerequisites` region imports the DUT's Config module. A Config of any other block is your own import in the user slot.
*   A Config module is named `<project>.<block>.config`, or `<block>.config` when the block name equals the project name or starts with `<project>_`. Copy the name from the `export module` line of the generated `*VariantConfig.cppm` rather than build it.
*   To reach the External's members, cast the testbench top. `<dut>Testbench` is exported from the testbench module, so import that module too, copying its name from the `export module` line of `<dut>Testbench.cppm`:

    ```cpp
    // user #includes and imports here
    import xif_dut.testbench;

    // createTestBench
    std::shared_ptr<blockBase> tb = createTbTop();
    auto *tb_ptr = dynamic_cast<dutTestbench *>(tb.get());
    // tb_ptr->external.uSrc is the External's instance uSrc
    ```

## Run parameters
The `<dut>Config` class registers run-time parameters with `addParam`.

```cpp
// <dut>Config.cpp, user region of the Config class
void addProgramOptions(po::options_description &options) override
{
    addParam("num_packets", 100);   // default and maximum
}

// anywhere in the testbench
uint64_t numPackets = testBenchConfigBase::getParam("num_packets");
```

*   Register a key in `addProgramOptions` or `handleProgramOptions`. Both run before `--param` is applied. A key first registered from a module constructor is too late and is rejected as unknown.
*   The registered value is both the default and the upper bound. A command-line value from 0 up to that bound replaces the default. A key registered with 0 cannot be set from the command line.

## Run options
*   `--param key,value` sets a registered parameter for one run, for example `build/run myTb --param num_packets,50`. Repeat it for several keys. Each key may appear once, counting the command line and the config file together.
*   `--verbosity` sets the log level, `--instVerbosity` the level of the `--vlInst` instance, and the config-file `blockVerbosity` the level of one block. For the accepted values, see "Logging and errors" in `systemc-core`. A bad value stops the run with exit status 2.
*   `--scTimeLimit <us>` caps simulated time, in microseconds.
*   `--config <file>` reads options from a Boost config file, one `key=value` per line. The default is `<testbench>.cfg` in the run directory, used when it exists.
*   `--log` sends output to `<binary>.log`, or to the file it names.
*   `--listTests` and `--test` are described under test sequencing below.

These stop the run with exit status 2 and print what was expected:
*   a `--param` key the testbench did not register (the message lists the registered keys);
*   a `--param` value above the registered bound, missing, or not a non-negative integer (`5abc`, `-1`);
*   a `--param` key given twice.

## Ending a run and reporting failures
*   The framework owns simulation control. `sc_main` calls `sc_start`, and the run stops once every end-of-test voter has voted. Never call `sc_start` or `sc_stop` from a testbench.
*   A framework watchdog fails a run that has no end-of-test voter and no `--scTimeLimit`, and a run that stops making progress once the watchdog is enabled.
*   Report a check failure with `errorCode::fail(msg)`. It records the failure and sets the exit status, and the run continues. There is no `logError`. `Q_ASSERT` stops the run instead; see `debug`.

```cpp
// scoreboard check
void myScoreboard::check(const transaction &actual)
{
    transaction expected = expected_queue.front();
    expected_queue.pop();
    if (!(actual == expected)) {
        log_.logPrint(std::format("mismatch exp:{} act:{}", expected.prt(), actual.prt()), LOG_IMPORTANT);
        errorCode::fail("scoreboard mismatch");
    }
}
```

*   To follow tags and commands through the design, use trackers; see `debug`. For RTL against the model, see `verify-cosimulation`, and in A2C Pro, `run-tandem`.

## Test sequencing with `testController`
*   A testbench lists its tests, in run order, with `testController::GetInstance().set_test_names({...})` from `createTestBench` or `handleProgramOptions`. Call it before any block that uses `ADD_TEST` is built, so put it before `createTbTop()`. The scaffolded `final()` asserts `are_all_tests_complete()`, which fails until every listed test has completed.
*   **`ADD_TEST` is the recommended form.** A test is a member function of a block or the External. It takes no arguments and returns `void`. Its name is the test name and must match a listed name exactly. Register it in the constructor body, after the generated region, with `ADD_TEST(name);`, as `SC_THREAD(name);` registers a thread. The framework starts the function when its turn comes and completes the test when it returns, so the function never calls `register_test_name`, `wait_test` or `test_complete`. The macro needs `#include "testController.h"` in the `// user #includes here` slot. In the `// user imports here` slot the header would attach `testController` to this module, which then gets a second, empty singleton that the testbench's `set_test_names` never reaches.

```cpp
// <dut>Config.cpp, createTestBench
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

*   **Run order.** The `set_test_names` list sets the order across every block. The order of the `ADD_TEST` lines and of block construction does not matter. A test must not rely on an earlier one, because `--test` can run it alone. In `examples/mixed`, `--test test_mem_hier_cpu_read` fails for this reason: it reads memory that `test_mem_hier_blockd_write` writes.
*   **Start delay.** `ADD_TEST` takes no delay. When you convert a `wait_test` thread that passes a start delay, make `wait(...)` the first line of the `ADD_TEST` function. Leaving it out raises no error, but the test starts earlier and its timestamps change.
*   **One test in several blocks.** Functions with the same name in different blocks form one test, which completes when all of them have returned. Every instance of a block that adds the function adds one more. `examples/mixed` splits `test_reg_cpu_rwg` this way: `cpu` writes the register and `blockGLeaf` checks the value it receives.
*   **End-of-test voter.** Vote from one separate thread that waits on `wait_all_tests_complete()`, as above. Never put a voter inside an `ADD_TEST` function. It would register only when its test starts, so an earlier test could vote and end the run before later tests register their voters.
*   **Mixing the forms.** One testbench can run some tests with `ADD_TEST` and others with `wait_test` threads, so you can convert a testbench one block at a time. Each test uses one form. `examples/ip_test`'s `fwModelMain::startupInit` uses the `wait_test` form because it is one procedure, not one function per test. It runs two tests in a row and holds the end-of-test voter, so a `--test` run of that testbench never completes.
*   **Two functions in one block under one test name.** One class cannot hold two functions with the same name, so `ADD_TEST` cannot express this. `testController::GetInstance().add_test("name", [this]() { secondHalf(); });` registers a second function under the same name. Capture only `this`. A lambda that captures a constructor local by reference reads freed memory when the test runs.
*   **The `wait_test` form.** A test thread calls `register_test_name(name)`, then `wait_test(name)` to block until its turn, runs, and calls `test_complete(name)`. `wait_test` takes an optional start delay. Several threads may register the same name, and the test completes when all of them have called `test_complete`. A thread that ends the run waits on `wait_all_tests_complete()`.

```cpp
// a model or External thread
testController &controller = testController::GetInstance();
controller.register_test_name("test_req_ack");
controller.wait_test("test_req_ack");
// ... drive and check ...
controller.test_complete("test_req_ack");
```

*   **Errors.** A function whose name is not in the list stops construction with `ERROR: test name <name> is not valid`, exit status 1. A name run both ways, `ADD_TEST` before `set_test_names`, or `set_test_names` again after an `ADD_TEST` also exits with status 1, and the message names the mistake.
*   **Tests with no `ADD_TEST`.** Once any `ADD_TEST` has run, a warning before simulation names every listed test that has no `ADD_TEST`. A `wait_test` thread must run each one, or the run never completes it. A testbench that never uses `ADD_TEST` gets no warning.
*   **A test that never completes.** If `--scTimeLimit`, the watchdog or another voter ends the run, `final()` fails. If nothing ends it, the run hangs.
*   **`--listTests`** prints the declared names, one per line, and exits 0 without simulating. The names are the last lines of the output, after the run banner. With `--log`, the banner goes to the log file and the console shows the `Logging redirected to:` line, then the names.
*   **`--test <name>`** runs only the named tests. Repeat it for several. They run in the testbench's order, not the command-line order. A name the testbench did not declare stops the run with exit status 2 and prints the declared names.
    *   An `ADD_TEST` function of a test left out never starts.
    *   A `wait_test` thread of a test left out waits in `wait_test` forever. Any later test that thread would run, and any voter it holds, waits with it. If it holds a listed test, that test never completes.
    *   A thread that holds only the voter never votes, so the run never ends after the listed tests complete. If `--scTimeLimit` or the watchdog ends it, `final()` still fails.
    *   Tests that work with `--test` are `ADD_TEST` tests, and `wait_test` threads that run one test each and hold no voter, as in `examples/helloWorld`.
*   `--listTests` and `--test` stop the run with exit status 2 if the testbench has declared no tests by the time `createTestBench` returns. A testbench that narrows the list itself, from its own option, is filtered on the list it passed.
