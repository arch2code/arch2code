# Skill: Verify Testbench

## Purpose
Guide the user on creating testbenches, configuring verification components, and using scoreboards.

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

3.  **Simulation Control:**
    *   **Start/Stop:** Use `sc_start()` and `sc_stop()`.
    *   **Timeout:** Implement a watchdog timer to prevent infinite loops.

    ```cpp
    sc_start(100, SC_MS); // Run for 100ms
    if (sc_get_status() != SC_STOPPED) {
        log_.logError("Simulation timed out!");
    }
    ```
