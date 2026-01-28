# SystemC Testbench Rules

These rules apply specifically to files in `tb/` directory.

**Also read:** `builder/base/rules/systemc-shared.md` for common patterns.

## File Structure

```
tb/
  <testbench>/
    <testbench>Testbench.h    # Main testbench class
    <testbench>Testbench.cpp  # Testbench implementation
    <testbench>Config.cpp     # Test configuration
    <testbench>TestConfigs.h  # Test case definitions
    <testbench>External.h     # External interfaces (optional)
    <testbench>External.cpp
```
Note that these files will be created when you specify a block hasTb: True in the yaml
## Testbench Structure

```cpp
// <testbench>Testbench.h
class myTestbench : public myTestbenchBase {
public:
    SC_HAS_PROCESS(myTestbench);
    
    myTestbench(sc_module_name name, const char* variant, blockBaseMode bbMode);
    
    void runTest();
    void checkResults();
    
private:
    // Test state
    uint32_t errorCount;
    uint32_t testCount;
};
```

## Test Configuration Pattern

```cpp
// <testbench>Config.cpp
void myTestbench::configure() {
    // Set up test parameters
    testConfig.iterations = 100;
    testConfig.randomSeed = 12345;
    
    // Initialize DUT registers
    configReg.m_val.enable = 1;
    configReg.m_val.mode = TEST_MODE_NORMAL;
}
```

## Stimulus Generation

### Sequential Stimulus
```cpp
void myTestbench::generateStimulus() {
    wait(SC_ZERO_TIME);
    
    for (int i = 0; i < testConfig.iterations; i++) {
        data_st stimulus;
        stimulus.value = generateTestValue(i);
        
        log_.logPrint(std::format("Stimulus {}: 0x{:x}", i, stimulus.value));
        stimPort->write(stimulus);
        
        wait(10, SC_NS);  // Inter-stimulus delay
    }
    
    log_.logPrint("Stimulus generation complete", LOG_IMPORTANT);
}
```

### Random Stimulus
```cpp
void myTestbench::generateRandomStimulus() {
    wait(SC_ZERO_TIME);
    std::mt19937 rng(testConfig.randomSeed);
    
    for (int i = 0; i < testConfig.iterations; i++) {
        data_st stimulus;
        stimulus.value = rng();
        stimulus.addr = rng() & 0xFFFF;
        
        stimPort->write(stimulus);
    }
}
```

## Checking and Scoreboarding

### Simple Checker
```cpp
void myTestbench::checkOutput() {
    wait(SC_ZERO_TIME);
    
    while (true) {
        result_st actual;
        resultPort->read(actual);
        
        result_st expected = computeExpected();
        
        if (actual.value != expected.value) {
            log_.logPrint(std::format("MISMATCH: got 0x{:x}, expected 0x{:x}",
                actual.value, expected.value), LOG_ALWAYS);
            errorCount++;
        } else {
            log_.logPrint("CHECK PASSED", LOG_DEBUG);
        }
        testCount++;
    }
}
```

### Scoreboard Pattern
```cpp
class Scoreboard {
    std::queue<expected_st> expectedQueue;
    
public:
    void addExpected(const expected_st& exp) {
        expectedQueue.push(exp);
    }
    
    bool checkActual(const actual_st& act) {
        if (expectedQueue.empty()) {
            log_.logPrint("ERROR: Unexpected output", LOG_ALWAYS);
            return false;
        }
        expected_st exp = expectedQueue.front();
        expectedQueue.pop();
        return (act.value == exp.value);
    }
};
```

## Test Control Flow

```cpp
void myTestbench::runTest() {
    log_.logPrint("=== Test Starting ===", LOG_IMPORTANT);
    
    // Reset DUT
    resetDUT();
    wait(100, SC_NS);
    
    // Configure
    configure();
    wait(10, SC_NS);
    
    // Start parallel threads
    SC_THREAD(generateStimulus);
    SC_THREAD(checkOutput);
    
    // Wait for completion
    wait(testComplete);
    
    // Report results
    reportResults();
}

void myTestbench::reportResults() {
    log_.logPrint("=== Test Complete ===", LOG_IMPORTANT);
    log_.logPrint(std::format("Tests: {}, Errors: {}", testCount, errorCount), 
                  LOG_ALWAYS);
    
    if (errorCount == 0) {
        log_.logPrint("*** TEST PASSED ***", LOG_ALWAYS);
    } else {
        log_.logPrint("*** TEST FAILED ***", LOG_ALWAYS);
    }
}
```

## Best Practices

1. **Separate stimulus generation from checking** - easier to debug
2. **Use scoreboards** for out-of-order completion
3. **Log at appropriate levels** - important events at `LOG_IMPORTANT`
4. **Report pass/fail clearly** at `LOG_ALWAYS`
5. **Use random seeds** for reproducibility
6. **Initialize all DUT state** before starting stimulus
