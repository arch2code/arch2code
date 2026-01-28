# SystemC Model Rules

These rules apply specifically to files in `model/` directory.

**Also read:** `builder/base/rules/systemc-shared.md` for common patterns.

## File Structure

```
model/
  <module>.h          # Your header (edit allowed)
  <module>.cpp        # Your implementation (edit allowed)
  <module>Includes.h  # Generated types (DO NOT EDIT)
  <module>Includes.cpp
```

## Implementation Pattern

```cpp
// In <module>.cpp
#include "<module>.h"

// Constructor - add your SC_THREADs after generated code
// GENERATED_CODE_BEGIN
<module>::<module>(sc_module_name name, ...)
    : sc_module(name),
      blockBase("<module>", name(), bbMode),
      <module>Base(name(), variant)
{
    // GENERATED_CODE_END
    
    // YOUR CODE:
    SC_THREAD(mainProcess);
    SC_THREAD(regHandler);
}

void <module>::mainProcess() {
    wait(SC_ZERO_TIME);
    while (true) {
        // Implementation
    }
}
```

## Register Decode Handler

Is automatically handled by the generators

## Memory Access Patterns

### Functional Read/Write (with timing)
```cpp
void myBlock::processData() {
    // Timed memory access
    aMemSt data = myMemory.read(0x100);
    data.field = processValue(data.field);
    myMemory.write(0x100, data);
}
```

### Streaming to Memory (no extra delay)
```cpp
void myBlock::streamToMemory() {
    uint32_t index = 0;
    while (true) {
        data_st data;
        inputPort->readClocked(data);  // Timing from interface
        myMemory.writeNoDelay(index++, data);  // No additional delay
    }
}
```

## Producer Pattern
```cpp
void producer::generateData() {
    wait(SC_ZERO_TIME);
    uint32_t count = 0;
    
    while (true) {
        data_st data;
        data.value = count++;
        
        log_.logPrint(std::format("Producing: {}", count));
        outputPort->write(data);  // Blocks until consumer ready
    }
}
```

## Consumer Pattern
```cpp
void consumer::processData() {
    wait(SC_ZERO_TIME);
    
    while (true) {
        data_st data;
        inputPort->read(data);  // Blocks until data available
        
        log_.logPrint(std::format("Consuming: {}", data.value));
        process(data);
    }
}
```

## Best Practices

1. **Always start threads with `wait(SC_ZERO_TIME)`**
2. **Use `while(true)` for continuous operation**
3. **Prefer blocking channel calls** - let channels handle flow control
4. **Log at transaction boundaries**, not in tight loops
5. **Use `m_val` for register access** unless timing accuracy required
