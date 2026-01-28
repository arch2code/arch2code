# SystemC Shared Rules

These rules apply to **both** `model/` and `tb/` directories.

## Generated Code Protection

### Never Edit These Files
- `*Base.h` files - Pure virtual base classes (fully regenerated)
- `*Includes.h/cpp` files - Type definitions
- Code between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` markers

### Safe to Edit
- `*.cpp` implementation files (outside generated markers)
- Your `SC_THREAD` and `SC_METHOD` implementations

## Module Logging

Every module has a `log_` member for hierarchical logging:

```cpp
// Basic logging
log_.logPrint("Starting transaction");

// With log level
log_.logPrint("Debug info", LOG_DEBUG);
log_.logPrint("Important event", LOG_IMPORTANT);

// Lazy evaluation for expensive formatting
log_.logPrint([&]() { 
    return std::format("Complex: {}", expensive()); 
}, LOG_DEBUG);
```

**Log Levels:** `LOG_ALWAYS` > `LOG_IMPORTANT` > `LOG_NORMAL` > `LOG_DEBUG`

## Register Access

### Unclocked Access (Preferred for functional models)
```cpp
// Direct value access
regSt value = myRegister.m_val;

// Field access
uint32_t field = myRegister.m_val.fieldName;
myRegister.m_val.fieldName = newValue;
```

### Clocked Access (Timing-accurate)
```cpp
regSt value = myRegister.read();   // With timing delay
myRegister.write(newValue);        // With timing delay
```

## Memory Access

```cpp
// Timed access (preferred)
aMemSt data = myMemory.read(index);
myMemory.write(index, data);

// No delay (for streaming with clocked interfaces)
myMemory.writeNoDelay(index, data);

// Backdoor (test initialization ONLY - bypasses locking)
myMemory[index] = data;  // Use sparingly!
```

### Atomic Read-Modify-Write
```cpp
const uint64_t MAGIC = 0x12345;
aMemSt data = myMemory.readRMW(index, MAGIC);  // Lock
data.field += 1;
myMemory.writeRMW(index, data);  // Write and unlock
// OR: myMemory.releaseRMW(index);  // Unlock without write
```

## Channel Patterns

### rdy_vld (Ready/Valid)
```cpp
// Source side
data_st data;
myPort->write(data);  // Blocks until sink ready

// Sink side - calling read() signals ready
myPort->read(data);   // Blocks until data available
```

### APB
```cpp
// Master side
apbAddrSt addr;
apbDataSt data;
addr._setAddress(0x100);
data._setData(0xDEADBEEF);
apbPort->request(true, addr, data);   // Write
apbPort->request(false, addr, data);  // Read, data returned

// Slave side
apbPort->reqReceive(isWrite, addr, data);
if (!isWrite) {
    data._setData(readValue);
    apbPort->complete(data);
}
```

### req_ack (Request/Acknowledge)
```cpp
// Initiator
reqData_st req;
ackData_st ack;
myPort->req(req, ack);  // Blocking request/response

// Target
myPort->reqReceive(req);
myPort->ack(ack);
```

## Thread Structure

```cpp
void myModule::myThread() {
    // Initial synchronization (REQUIRED)
    wait(SC_ZERO_TIME);
    
    // Main loop
    while (true) {
        data_st data;
        inputPort->read(data);   // Blocks
        processData(data);
        outputPort->write(data); // Blocks
    }
}
```

## Reference
For complete API documentation: `builder/base/SYSTEMC_API_USER_REFERENCE.md`
