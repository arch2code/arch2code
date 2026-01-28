# SystemC API Reference for arch2code

**Version:** 1.0  
**Audience:** C++ developers implementing hardware blocks  
**Scope:** User-facing SystemC APIs for module implementation

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Module Logging](#2-module-logging-user-api)
3. [Hardware Objects](#3-hardware-objects-user-api)
   - [Register Access](#31-direct-register-access)
   - [Memory Access](#32-direct-memory-access)
4. [Communication Channels](#4-communication-channels-user-api)
   - [rdy_vld_channel](#41-rdy_vld_channel---readyvalid-handshake)
   - [apb_channel](#42-apb_channel---apb-bus-protocol)
   - [memory_channel](#43-memory_channel---memory-access-protocol)
   - [req_ack_channel](#44-req_ack_channel---requestacknowledge-protocol)
   - [push_ack_channel](#45-push_ack_channel---push-with-acknowledge)
   - [pop_ack_channel](#46-pop_ack_channel---pop-with-acknowledge)
   - [notify_ack_channel](#47-notify_ack_channel---notify-with-acknowledge)
   - [status_channel](#48-status_channel---status-monitoring)
5. [Transaction Tracking](#5-transaction-tracking-user-api)
6. [Framework Reference](#6-framework-reference-minimal-documentation)
7. [Advanced Topics](#7-advanced-topics-power-users)
   - [Multi-Cycle Channel Patterns](#71-multi-cycle-channel-patterns)
   - [Synchronization](#72-synchronization-synchlock)
   - [Tag Encoding](#73-tag-encoding-encoderbase)
   - [External Thread Integration](#74-external-thread-integration-threadsafeevent)
   - [Backdoor Access](#75-backdoor-access)
8. [Common Implementation Patterns](#8-common-implementation-patterns)
9. [Best Practices](#9-best-practices)

---

## 1. Introduction

### Purpose and Scope

This document provides a comprehensive reference for **user-facing SystemC APIs** in the arch2code toolchain. It focuses on the APIs that C++ developers use to implement hardware module behavior in `.cpp` files.

**What You'll Learn:**
- How to access registers and memories
- How to use communication channels for data transfer
- How to implement common hardware patterns
- How to debug and track transactions
- Best practices for SystemC implementation

**What's NOT Covered:**
- Code generation workflow (see `ARCH2CODE_AI_RULES.md`)
- YAML architecture definition
- SystemVerilog/RTL implementation

### Generated vs. User Code

arch2code generates two types of files:

**Generated Files (DO NOT EDIT):**
- `*Base.h` - Pure virtual base classes with port declarations
- `*Includes.h/cpp` - Type definitions and structures
- Code between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` markers

**User Implementation Files (YOUR CODE):**
- `*.cpp` - Module implementation outside generated markers
- Your `SC_THREAD` and `SC_METHOD` implementations
- Business logic, algorithms, protocols

### Key Concepts

**Blocks:** SystemC modules (`sc_module`) that represent hardware components
**Ports:** Connection points between blocks (declared in Base classes)
**Channels:** Communication infrastructure connecting ports
**Registers:** CPU-accessible storage with structure types
**Memories:** Arrays of structured data with optional CPU access
**Trackers:** Transaction tracking system for debug

### Understanding Code Markers

```cpp
// GENERATED_CODE_PARAM --block=myBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "myBlock.h"
SC_HAS_PROCESS(myBlock);

myBlock::myBlock(sc_module_name blockName, const char* variant, blockBaseMode bbMode)
    : sc_module(blockName)
    ,blockBase("myBlock", name(), bbMode)
    ,myBlockBase(name(), variant)
    ,controlReg()  // Generated register initialization
    ,dataMemory(name(), "dataMemory", mems, 1024)  // Generated memory
    // User can add initialization here:
    ,myUserVariable(0)  // USER: Custom initialization
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // ... FRAMEWORK CODE - DO NOT EDIT ...
    regs.addRegister(0x100, 4, "controlReg", &controlReg);
    SC_THREAD(regHandler);
    // GENERATED_CODE_END
    
    // YOUR USER CODE STARTS HERE
    SC_THREAD(myThread);
}

void myBlock::myThread() {
    // ALL YOUR IMPLEMENTATION CODE
}
```

**Important Notes:**
- **Base files (`*Base.h`)** and **Include files (`*Includes.h/cpp`)** contain ONLY generated code between markers
- These files are **NOT regenerated** from scratch - they use in-place generation
- The markers allow selective regeneration of sections while preserving the file
- **Implementation files (`*.cpp`, `*.h`)** allow user code outside markers

**Rules:**
- Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`
- In constructor init sections, you can add user member initializations after generated ones
- Implement your logic outside these markers in implementation files
- Re-running generators preserves your user code

---

## 2. Module Logging (USER API)

Every module inherits a `log_` member for hierarchical logging.

### API Reference

#### `log_.logPrint(message)`
Log a message at `LOG_NORMAL` level.

```cpp
log_.logPrint("Starting transaction");
```

#### `log_.logPrint(message, loglevel)`
Log a message at specific level.

```cpp
log_.logPrint("Debug info", LOG_DEBUG);
log_.logPrint("Important event", LOG_IMPORTANT);
```

#### Log Levels

| Level | Value | Use Case |
|-------|-------|----------|
| `LOG_ALWAYS` | Highest | Critical errors, test results |
| `LOG_IMPORTANT` | High | Major events, initialization |
| `LOG_NORMAL` | Medium | Regular transactions |
| `LOG_DEBUG` | Low | Detailed debug information |

### Usage Examples

#### Basic Logging

```cpp
void myModule::processData() {
    log_.logPrint("Process started", LOG_IMPORTANT);
    
    // Process data
    data_st data;
    inputPort->read(data);
    
    log_.logPrint(std::format("Received data: 0x{:x}", data.value), LOG_NORMAL);
    
    // More processing...
    
    log_.logPrint("Process complete", LOG_IMPORTANT);
}
```

#### Conditional Logging

```cpp
void myModule::debugTransaction() {
    if (log_.isMatch(LOG_DEBUG)) {
        // Only compute expensive debug string if debug logging enabled
        std::string debugInfo = computeExpensiveDebugInfo();
        log_.logPrint(debugInfo, LOG_DEBUG);
    }
}
```

#### Using Lambda for Lazy Evaluation

```cpp
void myModule::efficientLogging() {
    // Lambda only executed if log level matches
    log_.logPrint([&]() { 
        return std::format("Complex: {} + {}", expensive1(), expensive2()); 
    }, LOG_DEBUG);
}
```

### Best Practices

✅ **DO:**
- Use appropriate log levels
- Include context in log messages
- Log at transaction boundaries
- Use lazy evaluation for expensive formatting

❌ **DON'T:**
- Log every cycle in tight loops
- Include sensitive data without filtering
- Use `std::cout` directly (breaks logging hierarchy)

---

## 3. Hardware Objects (USER API)

### 3.1 Direct Register Access

Registers are declared in generated Base classes and can be accessed directly from user code.

#### Unclocked Access (Preferred)

Direct access to register value without timing delay.

**API:**
- `myRegister.m_val` - Direct member access to register value
- `myRegister.m_val.field` - Access structure fields

**Example:**

```cpp
void blockA::LocalRegAccess() {
    // Direct register access
    un0ARegSt arw;
    
    // Read register value
    arw = rwUn0A.m_val;
    
    // Write register value
    arw.fa = 'a';
    arw.fb = 0xfefe1234;
    arw.fc = 'c';
    extA.m_val = arw;
    
    // Field access
    uint32_t fieldValue = rwUn0A.m_val.fb;
    rwUn0A.m_val.fa = 'x';
}
```

#### Clocked Access

Access with configured timing delays (for timing-accurate models).

**API:**
- `myRegister.read()` - Get register value with timing
- `myRegister.write(value)` - Set register value with timing

**Example:**

```cpp
void myModule::timedAccess() {
    // Clocked register read (includes timing delay)
    regSt value = myRegister.read();
    
    // Process value
    value.field += 1;
    
    // Clocked register write (includes timing delay)
    myRegister.write(value);
}
```

### When to Use Each

| Access Type | Use Case | Timing |
|-------------|----------|--------|
| `m_val` | Functional models, fast simulation | No delay |
| `read()`/`write()` | Timing-accurate models | Configured delay |

### 3.2 Direct Memory Access

**IMPORTANT:** Always use memory APIs, not direct member access.

#### Basic Access

**API:**
- `myMemory.read(index)` - Timed read with delay (preferred for functional code)
- `myMemory.write(index, value)` - Timed write with delay (preferred for functional code)
- `myMemory.writeNoDelay(index, value)` - Write without timing delay (for streaming data with clocked interfaces)
- `myMemory[index]` - **Backdoor access** (bypasses locking/synchronization, test initialization only)

**Example - Functional Access:**

```cpp
void myModule::functionalMemoryAccess() {
    // Timed memory read (includes configured delay)
    aMemSt data = myMemory.read(0x100);
    
    // Process data
    data.field += 1;
    
    // Timed memory write (includes configured delay)
    myMemory.write(0x100, data);
}
```

**Example - Streaming Data (No Delay):**

```cpp
void myModule::streamToMemory() {
    data_st data;
    
    while (true) {
        // Receive data on clocked interface
        inputPort->readClocked(data);
        
        // Write to memory without additional delay
        // (timing already provided by clocked interface)
        myMemory.writeNoDelay(index++, data);
    }
}
```

**Example - Test Initialization (Backdoor):**

```cpp
void myModule::initializeMemory() {
    // ONLY for test initialization - bypasses all locking/synchronization
    for (uint32_t i = 0; i < 256; i++) {
        myMemory[i].data = i * 0x100;  // Direct backdoor access
    }
}
```

**⚠️ Important - Backdoor Access (`[]`):**
- **Bypasses:** Locking, synchronization, timing delays
- **Use ONLY for:** Test initialization, verification backdoor reads
- **DO NOT use for:** Functional module behavior
- **Functional code:** Always use `read()`, `write()`, or `writeNoDelay()`

#### Atomic Read-Modify-Write

For thread-safe modifications when multiple threads or instances access the same memory.

**API:**
- `myMemory.readRMW(index, magicNumber)` - Start atomic RMW, returns value
- `myMemory.writeRMW(index, value)` - Complete atomic RMW
- `myMemory.releaseRMW(index)` - Release RMW lock without write
- `myMemory.lock(index, magicNumber)` - Acquire lock only

**Magic Number:** Used for synchronization between multiple instances accessing shared memory, particularly in tandem mode (RTL + SystemC co-simulation) where the magic value coordinates access through synchLock.

**Example:**

```cpp
void myModule::atomicUpdate() {
    // Magic value for synchronization (important for tandem mode)
    const uint64_t MAGIC = 0x12345;
    
    // Start atomic RMW (locks the row)
    aMemSt data = myMemory.readRMW(0x50, MAGIC);
    
    // Modify data (exclusive access)
    data.counter += 1;
    
    if (data.counter > 100) {
        // Write modified data and release lock
        myMemory.writeRMW(0x50, data);
    } else {
        // Release lock without writing
        myMemory.releaseRMW(0x50);
    }
}
```

**Use Cases:**
- Multiple SystemC threads accessing same memory
- Tandem mode: RTL and SystemC model accessing shared memory
- Coordinated access across module instances

### Memory Access Summary

| Method | Timing | Thread-Safe | Use Case |
|--------|--------|-------------|----------|
| `[index]` | None | ⚠️ No | Backdoor (test init / verification only) |
| `read(index)` | Yes | ⚠️ No | Timed single-thread |
| `write(index, value)` | Yes | ⚠️ No | Timed single-thread |
| `readRMW()` | Yes | ✅ Yes | Multi-threaded access |
| `writeRMW()` | Yes | ✅ Yes | Complete atomic update |

---

## 4. Communication Channels (USER API)

All channels are created and connected in generated code. Users call methods on port objects to send and receive data.

### Channel Overview

| Channel Type | Protocol | Use Case |
|--------------|----------|----------|
| `rdy_vld` | Ready/Valid handshake | Streaming data, FIFOs, pipelines |
| `apb` | APB bus protocol | Register access, control |
| `memory` | Memory access | Memory-mapped access |
| `req_ack` | Request/Acknowledge | Command/response protocols |
| `push_ack` | Push with ack | Data streaming with backpressure |
| `pop_ack` | Pop with ack | FIFO-like pull interfaces |
| `notify_ack` | Notify with ack | Event signaling |
| `status` | Status monitoring | Read-only state sharing |
| `axi_read` | AXI read | Burst read transactions |
| `axi_write` | AXI write | Burst write transactions |
| `axi4_stream` | AXI4-Stream | High-speed streaming |

### 4.1 rdy_vld_channel - Ready/Valid Handshake

Simple streaming protocol with ready/valid handshaking. Most commonly used for data pipelines.

#### Source Side (Writing Data)

**API:**
- `myPort->write(data)` - Blocking write, waits for ready
- `myPort->writeClocked(data)` - Multi-cycle burst write (one beat per call)
- `myPort->write(data, size)` - Transactional write with size/tag
- `myPort->getWritePtr()` - Get buffer pointer for multi-cycle writes
- `myPort->get_rdy()` - Check if sink is ready (non-blocking)

**Example - Basic Write:**

```cpp
void producer::producerOutRdyVld(void)
{
    data_st data;
    data.b = 0;
    wait(SC_ZERO_TIME);
    
    log_.logPrint("RV1");
    test_rdy_vld->write(data);  // Blocks until sink ready
    
    log_.logPrint("RV2");
    data.b = 1;
    test_rdy_vld->write(data);  // Next write
}
```

#### Sink Side (Reading Data)

**API:**
- `myPort->read(data)` - Blocking read, calling this signals module is ready to receive
- `myPort->readClocked(data)` - Multi-cycle burst read (one beat per call)
- `myPort->push_context(size)` - Set transaction size for multi-cycle
- `myPort->getReadPtr()` - Get buffer pointer for multi-cycle reads

**Important - Ready Signaling:**
- Calling `read()` on a destination (sink) interface **signals the module is ready**
- The `read()` function asserts the ready signal and waits for valid data
- This is the standard way to indicate readiness - manual ready control is not needed

**Example - Basic Read:**

```cpp
void consumer::consumerInRdyVld(void)
{
    data_st data;
    wait(SC_ZERO_TIME);
    
    log_.logPrint("RV1");
    // Calling read() signals ready and waits for data
    test_rdy_vld->read(data);  // Blocks until data available
    
    log_.logPrint("RV2");
    test_rdy_vld->read(data);  // Next read - ready signaled again
}
```

### 4.2 apb_channel - APB Bus Protocol

Request/response protocol for register and memory access. Supports single outstanding transaction.

#### Requester Side (Initiating Transactions)

**API:**
- `myPort->request(isWrite, addr, data)` - Blocking request (write or read)
  - For writes: `data` contains write data
  - For reads: `data` receives read data on return
- `myPort->requestNonBlocking(isWrite, addr, data)` - Non-blocking request
- `myPort->waitComplete(data)` - Wait for non-blocking read completion

**Example - APB Master:**

```cpp
void myModule::apbMaster() {
    apbAddrSt addr;
    apbDataSt data;
    
    // Write transaction
    addr._setAddress(0x100);
    data._setData(0xDEADBEEF);
    apbPort->request(true, addr, data);  // Blocking write
    
    // Read transaction
    addr._setAddress(0x100);
    apbPort->request(false, addr, data);  // Blocking read, data returned
    
    log_.logPrint(std::format("Read value: 0x{:x}", data._getData()));
}
```

#### Completer Side (Responding to Requests)

**API:**
- `myPort->reqReceive(isWrite, addr, data)` - Wait for and receive request
  - Returns `isWrite` flag and request data
- `myPort->complete(data)` - Send read response data

**Example - APB Slave / Register Handler:**

```cpp
void blockA::regHandler(void) {
    // Uses template helper function
    registerHandler<apbAddrSt, apbDataSt>(regs, apbReg, (1<<10)-1);
}

// Or custom handler:
void myModule::customHandler() {
    while (true) {
        bool isWrite;
        apbAddrSt addr;
        apbDataSt data;
        
        // Wait for request
        apbPort->reqReceive(isWrite, addr, data);
        
        uint64_t address = addr._getAddress();
        
        if (isWrite) {
            // Handle write
            myMemory.write(address, data._getData());
        } else {
            // Handle read
            data._setData(myMemory.read(address));
            apbPort->complete(data);
        }
    }
}
```

### 4.3 memory_channel - Memory Access Protocol

1-cycle latency memory interface. Same API as APB but optimized for memory timing.

**API:** Same as `apb_channel`
- `request()`, `requestNonBlocking()`, `waitComplete()` on requester side
- `reqReceive()`, `complete()` on completer side

**Example:**

```cpp
void myModule::memoryAccess() {
    bSizeSt addr;
    aRegSt data;
    
    // Memory write
    addr.index = 0x50;
    data.a = 0x12345678;
    memPort->request(true, addr, data);
    
    // Memory read
    addr.index = 0x50;
    memPort->request(false, addr, data);
    
    Q_ASSERT(data.a == 0x12345678, "Memory readback failed");
}
```

### 4.4 req_ack_channel - Request/Acknowledge Protocol

General-purpose request/response with separate request and acknowledgement data types.

#### Initiator Side

**API:**
- `myPort->req(request, ack)` - Send request, wait for ack (blocking)
- `myPort->reqNonBlocking(request)` - Send request (non-blocking)
- `myPort->waitAck(ack)` - Wait for acknowledgement

**Example:**

```cpp
void producer::producerOutReqAck(void)
{
    data_st reqData;
    data_st ackData;
    
    reqData.b = 0;
    log_.logPrint("RQA1");
    test_req_ack->req(reqData, ackData);  // Blocking req/ack
    
    log_.logPrint(std::format("Received ack: {}", ackData.b));
}
```

#### Target Side

**API:**
- `myPort->reqReceive(request)` - Wait for and receive request
- `myPort->ack(ack)` - Send acknowledgement
- `myPort->isActive()` / `myPort->isNotActive()` - Check request status

**Example:**

```cpp
void consumer::consumerInReqAck(void)
{
    data_st reqData;
    data_st ackData;
    
    // Wait for request
    test_req_ack->reqReceive(reqData);
    
    // Process and create ack
    ackData = reqData;
    ackData.b += 1;
    
    // Send acknowledgement
    test_req_ack->ack(ackData);
}
```

### 4.5 push_ack_channel - Push with Acknowledge

Source pushes data, sink acknowledges receipt. Good for streaming with explicit flow control.

#### Source Side

**API:**
- `myPort->push(data)` - Push data (blocking until ack)

**Example:**

```cpp
void producer::producerOutPushAck(void)
{
    data_st data;
    data.b = 0;
    
    log_.logPrint("VA1");
    test_push_ack->push(data);  // Push and wait for ack
    
    log_.logPrint("VA2");
}
```

#### Sink Side

**API:**
- `myPort->pushReceive(data)` - Receive pushed data
- `myPort->ack()` - Acknowledge receipt

**Example:**

```cpp
void consumer::consumerInPushAck(void)
{
    data_st data;
    
    // Receive push
    test_push_ack->pushReceive(data);
    
    // Process data
    processData(data);
    
    // Acknowledge
    test_push_ack->ack();
}
```

### 4.6 pop_ack_channel - Pop with Acknowledge

Requester pops data, provider acknowledges with data. Pull-based interface.

#### Requester Side

**API:**
- `myPort->pop(data)` - Request data (blocking until available)

**Example:**

```cpp
void producer::producerOutPopAck(void)
{
    data_st ackData;
    
    log_.logPrint("RDA1");
    test_pop_ack->pop(ackData);  // Pop request, receive data
    
    log_.logPrint(std::format("Popped: {}", ackData.b));
}
```

#### Provider Side

**API:**
- `myPort->popReceive()` - Wait for pop request
- `myPort->ack(data)` - Provide data

**Example:**

```cpp
void consumer::consumerInPopAck(void)
{
    data_st ackData;
    
    // Wait for pop request
    test_pop_ack->popReceive();
    
    // Prepare data
    ackData.b = getData();
    
    // Send data
    test_pop_ack->ack(ackData);
}
```

### 4.7 notify_ack_channel - Notify with Acknowledge

Simple event notification with acknowledgement. No data transfer.

#### Notifier Side

**API:**
- `myPort->notify()` - Send notification (blocking until ack)
- `myPort->notifyNonBlocking()` - Send notification (non-blocking)
- `myPort->waitAck()` - Wait for acknowledgement

**Example:**

```cpp
void myModule::sendNotification() {
    // Blocking notify
    startDone->notify();
    
    // Non-blocking notify
    event->notifyNonBlocking();
    event->waitAck();  // Wait separately
}
```

#### Receiver Side

**API:**
- `myPort->waitNotify()` - Wait for notification
- `myPort->ack()` - Acknowledge notification
- `myPort->isActive()` / `myPort->isNotActive()` - Check notification status

**Example:**

```cpp
void myModule::waitForEvent() {
    // Wait for notification
    startDone->waitNotify();
    
    // Process event
    handleEvent();
    
    // Acknowledge
    startDone->ack();
}
```

### 4.8 status_channel - Status Monitoring

Broadcast read-only status information. Writer updates status, readers can poll.

#### Writer Side

**API:**
- `myPort->write(value)` - Update status (non-blocking)

**Example:**

```cpp
void myModule::updateStatus() {
    bSizeRegSt status;
    status.index = currentState;
    
    // Update status (non-blocking)
    statusPort->write(status);
}
```

#### Reader Side

**API:**
- `myPort->read(value)` - Read current status (blocking, waits for update)
- `myPort->readNonBlocking(value)` - Read current status (non-blocking)

**Example:**

```cpp
void myModule::monitorStatus() {
    bSizeRegSt status;
    
    // Blocking read (waits for next update)
    statusPort->read(status);
    
    // Non-blocking read (gets current value)
    statusPort->readNonBlocking(status);
}
```

### Channel Selection Guide

| Need | Use Channel |
|------|-------------|
| Simple data streaming | `rdy_vld` |
| Register/control access | `apb` |
| Memory access | `memory` |
| Command/response | `req_ack` |
| Push with backpressure | `push_ack` |
| Pull-based transfer | `pop_ack` |
| Event notification | `notify_ack` |
| Status broadcasting | `status` |
| Burst read/write | `axi_read`/`axi_write` |
| High-speed streaming | `axi4_stream` |

---

## 5. Transaction Tracking (USER API)

Trackers provide a powerful mechanism for tracking transactions and resources as they flow through your design.

### Overview

**Purpose:** Track transactions, commands, and shared resources with unique identifiers through complex data flows.

**What Are Trackers?**
- **Tag Management System:** Allocate unique IDs (tags) to track transactions
- **Resource Tracking:** Monitor commands using shared resources (buffers, channels, queues)
- **Debug Visibility:** See transaction flow through the system with unique sequence numbers
- **Multi-Cycle Support:** Track data across multi-cycle transfers with buffer pointers

**Why Use Trackers?**
- **Debug Complex Flows:** Follow a specific command through multiple processing stages
- **Resource Management:** Track which command is using which buffer/resource
- **Verification:** Ensure transactions complete correctly without loss or duplication
- **Performance Analysis:** Measure transaction latency through the system
- **Correlation:** Match requests with responses in command/response protocols

**How They Work:**
- User code allocates a tag when a transaction enters the system
- Tag carries transaction metadata (source, destination, size, type)
- Tag flows with the transaction through channels and modules
- Each tag gets a unique sequence number for identification
- User code deallocates the tag when transaction completes

**Common Use Case Example:**
A DMA command enters your system and needs to:
1. Allocate a buffer for data transfer
2. Flow through command decode → address translation → data movement
3. Track which buffer is associated with this specific command
4. Release the buffer when transfer completes

The tracker tag stays with the command throughout, linking it to its allocated buffer.

### Accessing Trackers

**From Channels:**
```cpp
std::shared_ptr<trackerBase> tracker = myChannel->getTracker();
```

**By Name:**
```cpp
auto& trackers = trackerCollection::GetInstance();
std::shared_ptr<trackerBase> tracker = trackers.getTracker("tracker_name");
```

### User API Reference

#### `tracker->alloc()`
Allocate a new tag for tracking a transaction.

**Returns:** Unique tag ID

**Use Case:** Call when a transaction enters your system or when allocating a resource.

**Example:**
```cpp
void myModule::newCommand() {
    auto tracker = cmdTracker->getTracker();
    
    // Allocate tag for new command
    uint32_t tag = tracker->alloc();
    
    // Associate with command
    cmd.tag = tag;
    
    log_.logPrint(tracker->prt(tag, "Command allocated"), LOG_NORMAL);
}
```

#### `tracker->dealloc(tag)`
Deallocate a tag when transaction completes.

**Use Case:** Call when transaction finishes or resource is released.

**Example:**
```cpp
void myModule::commandComplete() {
    auto tracker = cmdTracker->getTracker();
    
    log_.logPrint(tracker->prt(tag, "Command complete"), LOG_NORMAL);
    
    // Release the tag
    tracker->dealloc(tag);
}
```

#### `tracker->prt(tag)`
Print tag information as a formatted string.

**Returns:** String with tracker prefix, sequence number, and transaction data

**Example:**
```cpp
void myModule::logTransaction(uint32_t tag) {
    auto tracker = myChannel->getTracker();
    log_.logPrint(tracker->prt(tag), LOG_NORMAL);
    // Output: "PKT#3a{src:0x10 dst:0x20 len:256}"
}
```

#### `tracker->prt(tag, message)`
Print tag with additional message.

**Example:**
```cpp
tracker->prt(tag, "Processing packet");
// Output: "Processing packet PKT#3a{...}"
```

#### `tracker->getString(tag)`
Get parseable tag string (uses `[]` instead of `{}`).

**Example:**
```cpp
std::string tagStr = tracker->getString(tag);
// Output: "PKT#3a[src:0x10 dst:0x20 len:256]"
```

#### `tracker->info(tag)`
Get transaction info object (type-specific).

**Returns:** Shared pointer to transaction metadata structure

**Example:**
```cpp
auto tracker = myChannel->getTracker();
auto info = tracker->info(tag);
// Access fields from info structure
log_.logPrint(std::format("Source: 0x{:x}", info->source));
```

#### `tracker->getBackdoorPtr(tag)`
Get data buffer pointer for multi-cycle transfers.

**Returns:** `uint8_t*` pointer to transaction buffer

**Use Case:** Zero-copy data access in multi-cycle channels

**Example:**
```cpp
void myModule::processMultiCycle() {
    axiReadRespSt<axiDataSt> *buff = 
        reinterpret_cast<axiReadRespSt<axiDataSt>*>(
            axiRd0->getTracker()->getBackdoorPtr(tag)
        );
    
    // Direct access to buffer
    for (int i = 0; i < 256; i++) {
        processData(buff[i]);
    }
}
```

#### `tracker->getLen(tag)`
Get transaction length/size.

**Returns:** `uint64_t` length in bytes

**Example:**
```cpp
uint64_t packetSize = tracker->getLen(tag);
log_.logPrint(std::format("Packet size: {} bytes", packetSize));
```

### Usage Patterns

#### Complete Example: Command Flow with Resource Tracking

This example shows a command flowing through a DMA controller that allocates a buffer, processes the transfer, and releases the buffer. The tracker links the command to its buffer throughout the flow.

```cpp
class dmaController : public dmaControllerBase {
private:
    std::shared_ptr<trackerBase> cmdTracker;
    std::array<uint8_t*, 16> buffers;  // 16 data buffers
    
public:
    void commandReceive() {
        cmdTracker = cmdChannel->getTracker();
        
        while (true) {
            dma_cmd_t cmd;
            
            // Receive DMA command
            cmdPort->read(cmd);
            
            // Allocate tracker tag for this command
            uint32_t tag = cmdTracker->alloc();
            
            // Find free buffer (example uses tag as buffer ID)
            uint32_t bufferId = tag % 16;
            
            // Log command entry
            log_.logPrint(cmdTracker->prt(tag, 
                std::format("DMA cmd allocated buffer {}", bufferId)), 
                LOG_NORMAL);
            
            // Store command with tag
            cmd.tag = tag;
            cmd.bufferId = bufferId;
            
            // Forward to address decoder
            addrDecodePort->write(cmd);
        }
    }
    
    void addressDecode() {
        cmdTracker = cmdChannel->getTracker();
        
        while (true) {
            dma_cmd_t cmd;
            addrDecodePort->read(cmd);
            
            // Process address translation
            uint64_t physAddr = translateAddress(cmd.address);
            cmd.physAddr = physAddr;
            
            // Log progress (tag flows with command)
            log_.logPrint(cmdTracker->prt(cmd.tag, 
                std::format("Address translated: 0x{:x} -> 0x{:x}", 
                    cmd.address, physAddr)), 
                LOG_DEBUG);
            
            // Forward to data mover
            dataMovePort->write(cmd);
        }
    }
    
    void dataMove() {
        cmdTracker = cmdChannel->getTracker();
        
        while (true) {
            dma_cmd_t cmd;
            dataMovePort->read(cmd);
            
            // Get buffer associated with this command
            uint8_t* buffer = buffers[cmd.bufferId];
            
            log_.logPrint(cmdTracker->prt(cmd.tag, 
                std::format("Moving {} bytes using buffer {}", 
                    cmd.length, cmd.bufferId)), 
                LOG_NORMAL);
            
            // Perform data transfer
            performTransfer(cmd.physAddr, buffer, cmd.length);
            
            // Send completion
            dma_complete_t complete;
            complete.tag = cmd.tag;
            complete.status = DMA_SUCCESS;
            completePort->write(complete);
        }
    }
    
    void commandComplete() {
        cmdTracker = cmdChannel->getTracker();
        
        while (true) {
            dma_complete_t complete;
            completePort->read(complete);
            
            // Log completion
            log_.logPrint(cmdTracker->prt(complete.tag, "DMA complete"), 
                LOG_NORMAL);
            
            // Deallocate tag - transaction finished
            cmdTracker->dealloc(complete.tag);
            
            // Buffer now free for reuse
        }
    }
};
```

**Key Points in Example:**
- **Allocate** when command enters system
- **Tag flows** through all processing stages
- **Links command** to allocated buffer throughout flow
- **Tracks progress** at each stage with meaningful log messages
- **Deallocate** when transaction completes
- **Buffer management** tied to tag lifecycle

**Output Example:**
```
CMD#01[DMA cmd allocated buffer 5]
CMD#01[Address translated: 0x80000000 -> 0x40000000]
CMD#01[Moving 4096 bytes using buffer 5]
CMD#01[DMA complete]
```

#### Basic Transaction Logging

```cpp
void myModule::processWithLogging() {
    data_st data;
    myPort->read(data);
    
    // Tag embedded in data structure
    uint32_t tag = data.getStructValue();
    
    // Log transaction
    auto tracker = myPort->getTracker();
    log_.logPrint(tracker->prt(tag, "Received"), LOG_NORMAL);
    
    // Process
    processData(data);
    
    log_.logPrint(tracker->prt(tag, "Processed"), LOG_NORMAL);
}
```

#### Multi-Cycle with Tracker

```cpp
void producer::outAXI0Rd(void) {
    for(int loop = 0; loop < LOOPCOUNT; loop++) {
        axiReadAddressSt<axiAddrSt> addr;
        addr.araddr.addr = loop;
        addr.arlen = 255;  // 256 transfers
        
        axiReadRespSt<axiDataSt> data;
        axiRd0->push_burst(256);
        axiRd0->sendAddr(addr);
        axiRd0->receiveData(data);
        
        // Use backdoor pointer for efficient access
        axiReadRespSt<axiDataSt> *buff = 
            reinterpret_cast<axiReadRespSt<axiDataSt>*>(
                axiRd0->getReadPtr()
            );
        
        // Direct buffer access
        for (int i = 0; i < 256; i++) {
            Q_ASSERT(buff[i].rdata.data == i * 0x01010101, "Data mismatch");
        }
    }
}
```

### Important Notes

**User-Managed Allocation:**
- `alloc()` and `dealloc()` are **commonly used in user code** for resource tracking
- Allocate when transaction enters system or resource acquired
- Deallocate when transaction completes or resource released
- Automatic alloc/dealloc by channels often doesn't work well and may be deprecated

**Tag Validity:**
- Always check if tag is valid before accessing
- Invalid tags will trigger assertions
- Tags only valid between alloc/dealloc

**Performance:**
- `prt()` creates formatted strings - avoid in performance-critical loops
- Use backdoor pointers for zero-copy access
- Logging is conditional on verbosity level

**Best Practices:**
- Allocate at system entry points (command receive, request decode)
- Flow tag with transaction through all stages
- Use `prt()` with meaningful messages at key stages
- Deallocate at completion points (response sent, transaction done)
- Consider tag as a "handle" linking command to resources (buffers, queues, etc.)

---

## 6. Framework Reference (Minimal Documentation)

These APIs are used in generated code. Users rarely need to call them directly. This section provides brief reference for understanding generated code only.

### 6.1 blockBase (Framework)

**Purpose:** Base class for all SystemC modules, provides logging and infrastructure.

**Framework APIs (in generated code):**
- Constructor: `blockBase(loggingName, hierarchyName, mode)`
- Tandem mode: `isTandem()`, `getAltName()`, `getAltNameSafe()`
- Verilator tracing: `vl_trace()`

**User-Accessible:**
- `log_` member (documented in Section 2)

**Where Used:** Generated constructor initialization lists

### 6.2 interfaceBase (Framework)

**Purpose:** Base functionality for all channel interfaces.

**Framework APIs:**
- `setTracker()` - Attach tracker to interface
- `setTimed()` - Configure timing delays
- `setLogging()` - Set logging verbosity
- `setMultiDriver()` - Enable multi-driver synchronization
- `setTandem()` - Configure tandem mode
- Auto-allocation modes: `INTERFACE_AUTO_OFF`, `INTERFACE_AUTO_ALLOC`, `INTERFACE_AUTO_DEALLOC`

**Where Used:** Channel constructors and configuration

**User Access:** Via channel methods, not direct calls

### 6.3 portBase (Framework)

**Purpose:** Common interface for all port types.

**Framework APIs:**
- `getTracker()` - Get attached tracker
- `getChannel()` - Get underlying channel
- `setTeeBusy()` - Set tee busy status
- `setTandem()` - Configure tandem mode
- `setLogging()` - Set logging level
- `setTimed()` - Configure timing
- `setMultiDriver()` - Enable multi-driver

**Where Used:** Port configuration and management

**User Access:** Call channel-specific methods instead

### 6.4 addressMap (Framework)

**Purpose:** Address space management for register and memory access.

**Framework APIs:**
- `addRegister(address, size, name, ptr)` - Register a register
- `addMemory(address, size, name, ptr)` - Register a memory
- `addMemory(address, structByteWidth, wordLines, name, ptr)` - Register memory with dimensions
- `cpu_read(address)` - Read from address space
- `cpu_write(address, value)` - Write to address space
- `registerHandler()` - Template helper for register threads

**Where Used:** Generated register handler initialization

**Example (generated code):**
```cpp
// In generated constructor body:
regs.addMemory(0x0, aMemSt::_byteWidth, MEMORYA_WORDS, 
               std::string(this->name()) + ".blockATable0", &blockATable0);
regs.addRegister(0x200, 5, "roA", &roA);
```

**User Access:** Access registers/memories via direct APIs (Section 3)

### 6.5 instanceFactory (Framework)

**Purpose:** Factory for creating module instances dynamically.

**Framework APIs:**
- `createInstance(parent, name, blockType, variant)` - Create module instance

**Where Used:** Generated constructors for hierarchical designs

**Example (generated code):**
```cpp
uBlockD(std::dynamic_pointer_cast<blockDBase>(
    instanceFactory::createInstance(name(), "uBlockD", "blockD", "")
))
```

**User Access:** Instances created automatically, users just use them

### 6.6 hwRegister/hwMemory Constructors (Framework)

**Purpose:** Construct register and memory objects.

**Framework APIs:**
- `hwRegister<REG_DATA, N>(initialValue)` - Construct register
- `hwMemory<MEM_DATA>(hierarchicalName, memName, memories, rows, type)` - Construct memory
- `bindPort()` - Bind memory to channel port

**Where Used:** Generated initialization lists and constructor body

**Example (generated code):**
```cpp
// Registers in init list:
rwUn0A(un0ARegSt::_packedSt(0x1234abcdef))

// Memories in init list:
blockATable0(name(), "blockATable0", mems, MEMORYA_WORDS)

// Memory binding in body:
blockBTable1.bindPort(blockBTable1_port1);
```

**User Access:** Use direct access APIs (Section 3)

### Framework Summary

| Component | Purpose | User Action |
|-----------|---------|-------------|
| blockBase | Module base | Use `log_` member |
| interfaceBase | Channel base | Use channel methods |
| portBase | Port interface | Use channel methods |
| addressMap | Register/memory map | Use direct access |
| instanceFactory | Module creation | Use created instances |
| hwRegister/hwMemory | Hardware objects | Use access APIs |

**Key Principle:** Framework APIs are called in generated code. Users interact with the system through high-level APIs documented in Sections 2-5.

---

## 7. Advanced Topics (Power Users)

These APIs are for specialized use cases. Most designs won't need them.

### 7.1 Multi-Cycle Channel Patterns

Transfer data larger than channel width over multiple cycles.

#### Fixed-Size Bursts

Use `readClocked()` / `writeClocked()` for burst transfers with known size.

**API:**
- `myPort->writeClocked(data)` - Write one beat of burst
- `myPort->readClocked(data)` - Read one beat of burst
- Call once per cycle/beat
- Channel handles buffering automatically

**Example - Cycle-by-Cycle Transfer:**

```cpp
void producer::outAXI1Rd(void) {
    axiRd1->setCycleTransaction(PORTTYPE_OUT);
    
    for(int loop = 0; loop < LOOPCOUNT; loop++) {
        axiReadAddressSt<axiAddrSt> addr;
        addr.arlen = 255;  // 256 transfers
        axiRd1->sendAddr(addr);
        
        // Read 256 beats, one per call
        for (int i = 0; i < 256; i++) {
            axiReadRespSt<axiDataSt> cycleData;
            axiRd1->receiveDataCycle(cycleData);
            
            // Process beat
            processData(cycleData);
        }
    }
}
```

#### Variable-Size Transactions

Use size/tag parameter to specify transaction length dynamically.

**Source Side:**
- Use `write(data, size)` with size or tag parameter
- Size determines transfer length

**Sink Side:**
- Use `push_context(size)` before reading to set expected size
- Supports tracker-based or list-based size management

**Example - Variable Size:**

```cpp
void myModule::variableSizeTransfer() {
    data_st data;
    uint32_t packetSize = computePacketSize();
    
    // Write with size/tag
    myPort->write(data, packetSize);
}

void myModule::variableSizeReceive() {
    data_st data;
    uint32_t expectedSize = getExpectedSize();
    
    // Set context before read
    myPort->push_context(expectedSize);
    myPort->read(data);
}
```

#### Buffer Pointer Access (Zero-Copy)

Direct buffer access for maximum performance.

**API:**
- `myPort->getReadPtr()` - Get read buffer pointer
- `myPort->getWritePtr()` - Get write buffer pointer
- Use with `readClocked()` / `writeClocked()` or standalone

**Example - Zero-Copy Read:**

```cpp
void producer::outAXI0Rd(void) {
    axiReadRespSt<axiDataSt> data;
    axiRd0->push_burst(256);
    axiRd0->sendAddr(addr);
    axiRd0->receiveData(data);
    
    // Get direct pointer to buffer
    axiReadRespSt<axiDataSt> *buff = 
        reinterpret_cast<axiReadRespSt<axiDataSt>*>(
            axiRd0->getReadPtr()
        );
    
    // Direct access - no copying
    for (int i = 0; i < 256; i++) {
        if (buff[i].rdata.data != i * 0x01010101) {
            Q_ASSERT(false, "Data mismatch");
        }
    }
}
```

### 7.2 Synchronization (synchLock)

Thread-safe access to shared resources.

**Purpose:** Coordinate multiple threads accessing shared data.

**Note:** Memory RMW operations use synchLock internally. Rarely needed in user code.

**API:**
- `synchLock<T>::lock(value)` - Acquire lock with value
- `synchLock<T>::unlock()` - Release lock
- `synchLockFactory::newLock(name)` - Create lock

**Example - Custom Arbitration:**

```cpp
class myModule : public myModuleBase {
    std::shared_ptr<synchLock<uint32_t>> arbLock;
    
public:
    myModule(...) {
        arbLock = synchLockFactory<uint32_t>::getInstance()
                    .newLock(name(), "arbitration");
    }
    
    void thread1() {
        uint32_t requestId = 0x1;
        arbLock->lock(requestId);
        
        // Critical section
        accessSharedResource();
        
        arbLock->unlock();
    }
};
```

### 7.3 Tag Encoding (encoderBase)

Multiplexing multiple tag spaces into a single field.

**Purpose:** Encode different tag types into one tag value.

**API:**
- `encode(tag, type)` - Encode tag with type
- `decode(encodedTag)` - Extract tag and type
- `prt(encodedTag)` - Pretty print
- `getName(type)` - Get type name

**Example - Multiple Tag Types:**

```cpp
enum TransactionType {
    TYPE_READ = 0,
    TYPE_WRITE = 1,
    TYPE_CONTROL = 2
};

class myEncoder : public encoderBase<uint32_t, TransactionType> {
public:
    myEncoder() : encoderBase<uint32_t, TransactionType>(
        {
            // encVal  encMask    max      hexW  name            var
            {0x0000, 0xE000, 0x1FFF, 4, "TYPE_READ",    "rd"},
            {0x2000, 0xE000, 0x1FFF, 4, "TYPE_WRITE",   "wr"},
            {0x4000, 0xE000, 0x0FFF, 3, "TYPE_CONTROL", "ctl"}
        }, 16, 0xFFFF, true) {}
};

void myModule::useEncoder() {
    myEncoder encoder;
    
    // Encode
    uint32_t encodedTag = encoder.encode(0x123, TYPE_READ);
    
    // Decode
    auto [tag, type] = encoder.decode(encodedTag);
    
    // Print
    log_.logPrint(encoder.prt(encodedTag));
    // Output: "rd:0x0123"
}
```

### 7.4 External Thread Integration (ThreadSafeEvent)

Signal SystemC from external threads.

**Purpose:** External C++ threads can trigger SystemC events safely.

**API:**
- `ThreadSafeEventFactory::newEvent(name)` - Create thread-safe event
- `ThreadSafeEventFactory::getEvent(name)` - Get existing event
- `event->notify(delay)` - Signal from any thread (thread-safe)
- `event->default_event()` - Get sc_event for waiting

**Example - External Stimulus:**

```cpp
// In SystemC thread:
void myModule::waitForExternal() {
    auto event = ThreadSafeEventFactory::newEvent("external_trigger");
    
    while (true) {
        // Wait for external event
        wait(event->default_event());
        
        // Handle trigger
        handleExternalEvent();
    }
}

// In external C++ thread:
void externalThread() {
    auto event = ThreadSafeEventFactory::getEvent("external_trigger");
    
    // Do work in external thread
    performExternalWork();
    
    // Signal SystemC (thread-safe)
    event->notify();
}
```

### 7.5 Backdoor Access

Zero-copy data transfer via pointers.

**Purpose:** Direct memory access without copying for large data transfers.

**API (via Tracker):**
- `tracker->getBackdoorPtr(tag)` - Get data buffer pointer
- `tracker->setBackdoorPtr(tag, ptr)` - Set custom buffer
- `tracker->setLen(tag, length)` - Set buffer length
- `tracker->getLen(tag)` - Get buffer length

**Example - DMA-Like Transfer:**

```cpp
void myModule::dmaTransfer() {
    const uint32_t BUFFER_SIZE = 4096;
    uint8_t *externalBuffer = allocateExternal(BUFFER_SIZE);
    
    auto tracker = myChannel->getTracker();
    uint32_t tag = allocateTag();
    
    // Point tracker to external buffer
    tracker->setBackdoorPtr(tag, externalBuffer);
    tracker->setLen(tag, BUFFER_SIZE);
    
    // Transfer uses backdoor pointer (no copy)
    performTransfer(tag);
    
    // Access data directly
    uint8_t *data = tracker->getBackdoorPtr(tag);
    processData(data, BUFFER_SIZE);
}
```

**Example - Memory Backdoor:**

```cpp
void myModule::memoryBackdoor() {
    // Access memory data pointer directly
    aMemSt *memData = myMemory.data();
    
    // Direct manipulation (use with caution)
    for (uint32_t i = 0; i < rows; i++) {
        memData[i].field = initialValue;
    }
}
```

### Advanced Topics Summary

| Feature | Use Case | Complexity |
|---------|----------|------------|
| Multi-cycle bursts | Large data transfers | Medium |
| Buffer pointers | Zero-copy, performance | Medium |
| synchLock | Multi-threading | High |
| encoderBase | Tag multiplexing | Medium |
| ThreadSafeEvent | External integration | High |
| Backdoor access | DMA, external memory | High |

**When to Use:**
- ✅ Use for performance-critical paths
- ✅ Use when standard APIs insufficient
- ⚠️ Requires careful testing
- ⚠️ Can bypass safety checks

---

## 8. Common Implementation Patterns

Complete examples of common module implementation patterns.

### 8.1 Basic Module Structure

```cpp
// GENERATED_CODE sections omitted for clarity

class myModule : public myModuleBase {
public:
    myModule(sc_module_name blockName, const char* variant, blockBaseMode bbMode)
        : sc_module(blockName),
          blockBase("myModule", name(), bbMode),
          myModuleBase(name(), variant)
    {
        // Generated code here
        // YOUR CODE:
        SC_THREAD(mainThread);
    }
    
    void mainThread() {
        // Initialization
        wait(SC_ZERO_TIME);
        
        // Main loop
        while (true) {
            // Read input
            data_st data;
            inputPort->read(data);
            
            log_.logPrint(std::format("Received: 0x{:x}", data.value));
            
            // Process
            result_st result = processData(data);
            
            // Write output
            outputPort->write(result);
        }
    }
    
private:
    result_st processData(const data_st& data) {
        result_st result;
        // Processing logic
        return result;
    }
};
```

### 8.2 Producer Pattern (rdy_vld source)

```cpp
void producer::dataGenerator() {
    data_st data;
    uint32_t counter = 0;
    
    wait(SC_ZERO_TIME);  // Initial synchronization
    
    while (true) {
        // Generate data
        data.value = counter++;
        data.timestamp = sc_time_stamp().value();
        
        log_.logPrint(std::format("Producing: 0x{:x}", data.value));
        
        // Send (blocks if sink not ready)
        outputPort->write(data);
        
        // Optional: Add timing
        wait(10, SC_NS);
    }
}
```

### 8.3 Consumer Pattern (rdy_vld sink)

```cpp
void consumer::dataProcessor() {
    data_st data;
    
    wait(SC_ZERO_TIME);  // Initial synchronization
    
    while (true) {
        // Receive (blocks until data available)
        inputPort->read(data);
        
        log_.logPrint(std::format("Consuming: 0x{:x}", data.value));
        
        // Process data
        processData(data);
        
        // Optional: Processing delay
        wait(5, SC_NS);
    }
}
```

### 8.4 APB Master Pattern

```cpp
void myModule::apbMasterThread() {
    wait(SC_ZERO_TIME);
    
    while (true) {
        apbAddrSt addr;
        apbDataSt data;
        
        // Write transaction
        addr._setAddress(0x1000);
        data._setData(0xDEADBEEF);
        
        log_.logPrint(std::format("APB Write addr:0x{:x} data:0x{:x}", 
                                  addr._getAddress(), data._getData()));
        
        apbPort->request(true, addr, data);
        
        // Read transaction
        addr._setAddress(0x1000);
        apbPort->request(false, addr, data);
        
        log_.logPrint(std::format("APB Read addr:0x{:x} data:0x{:x}",
                                  addr._getAddress(), data._getData()));
        
        wait(100, SC_NS);
    }
}
```

### 8.5 APB Slave / Register Handler Pattern

```cpp
void blockA::regHandler(void) {
    // Template helper handles register decode
    registerHandler<apbAddrSt, apbDataSt>(regs, apbReg, (1<<10)-1);
}

// Or custom register handler:
void myModule::customRegHandler() {
    while (true) {
        bool isWrite;
        apbAddrSt addr;
        apbDataSt data;
        
        // Wait for APB request
        apbPort->reqReceive(isWrite, addr, data);
        
        uint64_t address = addr._getAddress();
        
        if (isWrite) {
            // Decode and handle write
            if (address == 0x100) {
                controlReg.m_val.field = data._getData();
                log_.logPrint("Control register written");
            } else if (address >= 0x1000 && address < 0x2000) {
                uint32_t index = (address - 0x1000) / 4;
                myMemory.write(index, data._getData());
            }
        } else {
            // Decode and handle read
            if (address == 0x100) {
                data._setData(controlReg.m_val.field);
            } else if (address >= 0x1000 && address < 0x2000) {
                uint32_t index = (address - 0x1000) / 4;
                data._setData(myMemory.read(index));
            }
            
            // Send read response
            apbPort->complete(data);
        }
    }
}
```

### 8.6 Multi-Cycle Burst Pattern

```cpp
void myModule::burstWrite() {
    const int BURST_LEN = 256;
    
    // Prepare burst data
    data_st burstData[BURST_LEN];
    for (int i = 0; i < BURST_LEN; i++) {
        burstData[i].value = i;
    }
    
    // Send burst cycle-by-cycle
    for (int i = 0; i < BURST_LEN; i++) {
        burstPort->writeClocked(burstData[i]);
        wait(SC_ZERO_TIME);  // One cycle per beat
    }
}

void myModule::burstRead() {
    const int BURST_LEN = 256;
    data_st burstData[BURST_LEN];
    
    // Receive burst cycle-by-cycle
    for (int i = 0; i < BURST_LEN; i++) {
        burstPort->readClocked(burstData[i]);
        wait(SC_ZERO_TIME);  // One cycle per beat
    }
    
    // Process received burst
    processBurst(burstData, BURST_LEN);
}
```

### 8.7 Register/Memory Access Pattern

```cpp
void myModule::registerAccess() {
    // Unclocked register access (preferred)
    controlRegSt ctrl = controlReg.m_val;
    ctrl.enable = 1;
    ctrl.mode = 3;
    controlReg.m_val = ctrl;
    
    // Field access
    uint32_t currentMode = controlReg.m_val.mode;
    controlReg.m_val.enable = 0;
}

void myModule::memoryAccess() {
    // Timed memory access (preferred)
    aMemSt data = myMemory.read(0x100);
    data.field += 1;
    myMemory.write(0x100, data);
    
    // Fast access (no timing)
    myMemory[0x100] = data;
    data = myMemory[0x100];
}

void myModule::atomicMemoryUpdate() {
    const uint64_t MAGIC = 0x1234;
    
    // Atomic read-modify-write
    aMemSt data = myMemory.readRMW(0x50, MAGIC);
    data.counter += 1;
    
    if (data.counter < 100) {
        myMemory.writeRMW(0x50, data);
    } else {
        myMemory.releaseRMW(0x50);
    }
}
```

### 8.8 Pipeline Stage Pattern

```cpp
void myModule::pipelineStage() {
    wait(SC_ZERO_TIME);
    
    while (true) {
        data_st input;
        
        // Read from previous stage
        inputPort->read(input);
        
        // Process
        result_st output = stageProcess(input);
        
        // Forward to next stage
        outputPort->write(output);
    }
}
```

---

## 9. Best Practices

### 9.1 Thread Design

#### Use SC_THREAD for Most Communication

```cpp
// Good: SC_THREAD for blocking I/O
SC_THREAD(communicationThread);

void myModule::communicationThread() {
    while (true) {
        data_st data;
        inputPort->read(data);  // Blocking
        processData(data);
        outputPort->write(data);  // Blocking
    }
}
```

#### Always Include Initial wait(SC_ZERO_TIME)

```cpp
void myModule::myThread() {
    // Initial synchronization
    wait(SC_ZERO_TIME);
    
    // Main loop
    while (true) {
        // ...
    }
}
```

#### Use while(true) for Continuous Operation

```cpp
// Good: Continuous processing
void myModule::processor() {
    wait(SC_ZERO_TIME);
    while (true) {
        processData();
    }
}

// Bad: Thread ends prematurely
void myModule::badProcessor() {
    processData();  // Only runs once!
}
```

### 9.2 Channel Usage

#### Prefer Blocking Calls

```cpp
// Good: Simple and clear
void myModule::simpleIO() {
    data_st data;
    inputPort->read(data);   // Blocks until available
    outputPort->write(data);  // Blocks until accepted
}

// Avoid: Complex non-blocking unless necessary
void myModule::complexIO() {
    data_st data;
    inputPort->readNonBlocking(data);
    // Complex state management needed...
}
```

#### Let Channels Handle Handshaking

```cpp
// Good: Channel handles ready/valid
void myModule::autoHandshake() {
    dataPort->write(data);  // Channel manages handshake
}

// Only for advanced cases:
void myModule::manualHandshake() {
    dataPort->enable_user_ready_control();
    dataPort->set_rdy(true);
    // Manual control...
}
```

### 9.3 Logging

#### Use Appropriate Log Levels

```cpp
// Initialization and major events
log_.logPrint("Module initialized", LOG_IMPORTANT);

// Regular transactions
log_.logPrint(std::format("Processing packet {}", id), LOG_NORMAL);

// Detailed debug
log_.logPrint(std::format("State: {} -> {}", old, new), LOG_DEBUG);

// Critical errors
log_.logPrint("Fatal error detected!", LOG_ALWAYS);
```

#### Include Context in Messages

```cpp
// Good: Clear context
log_.logPrint(std::format("DMA transfer addr:0x{:x} len:{} bytes", 
                          addr, len), LOG_NORMAL);

// Bad: Vague
log_.logPrint("Transfer done", LOG_NORMAL);
```

#### Use Lazy Evaluation for Expensive Formatting

```cpp
// Good: Only formats if debug enabled
log_.logPrint([&]() {
    return std::format("Complex: {}", expensiveComputation());
}, LOG_DEBUG);

// Bad: Always computes even if not logged
log_.logPrint(std::format("Complex: {}", expensiveComputation()), LOG_DEBUG);
```

### 9.4 Error Handling

#### Use Q_ASSERT for Internal Consistency

```cpp
void myModule::processData(uint32_t index) {
    Q_ASSERT(index < MAX_SIZE, "Index out of range");
    
    data_st data = dataArray[index];
    // ...
}
```

#### Check Return Values

```cpp
void myModule::safeRead() {
    data_st data;
    bool success = tryRead(data);
    
    if (!success) {
        log_.logPrint("Read failed, using default", LOG_IMPORTANT);
        data = getDefaultData();
    }
}
```

### 9.5 Performance

#### Use Direct Access When Timing Not Critical

```cpp
// Fast functional access
value = myMemory[index];

// Timed access when accuracy matters
value = myMemory.read(index);
```

#### Use Backdoor Pointers for Large Transfers

```cpp
// Efficient: Zero-copy
uint8_t *buff = tracker->getBackdoorPtr(tag);
processLargeBuffer(buff, size);

// Inefficient: Multiple copies
for (int i = 0; i < size; i++) {
    data[i] = readByte(i);
}
```

#### Avoid Logging in Tight Loops

```cpp
// Good: Log at transaction boundaries
log_.logPrint(std::format("Processing {} items", count));
for (int i = 0; i < count; i++) {
    processItem(i);  // No logging
}
log_.logPrint("Processing complete");

// Bad: Spam log
for (int i = 0; i < count; i++) {
    log_.logPrint(std::format("Item {}", i));  // Too much!
}
```

### 9.6 Debugging

#### Enable Tracker Logging

```cpp
void myModule::debugTransaction() {
    auto tracker = myPort->getTracker();
    uint32_t tag = data.getStructValue();
    
    log_.logPrint(tracker->prt(tag, "Start processing"));
    processData(data);
    log_.logPrint(tracker->prt(tag, "Complete"));
}
```

#### Use prt() Methods on Data Structures

```cpp
// Good: Use built-in prt() methods
log_.logPrint(std::format("Data: {}", data.prt()), LOG_DEBUG);

// Tedious: Manual formatting
log_.logPrint(std::format("Data: a:{} b:{} c:{}", 
                          data.a, data.b, data.c), LOG_DEBUG);
```

#### Check Interface Status

```cpp
// If data seems stuck, check channel status
if (timeout) {
    log_.logPrint("Checking interface status:", LOG_IMPORTANT);
    logging::GetInstance().interfaceStatus();
}
```

#### Add Strategic Log Points

```cpp
void myModule::complexProcess() {
    log_.logPrint("=== Starting complex process ===", LOG_NORMAL);
    
    step1();
    log_.logPrint("Step 1 complete", LOG_DEBUG);
    
    step2();
    log_.logPrint("Step 2 complete", LOG_DEBUG);
    
    step3();
    log_.logPrint("=== Complex process complete ===", LOG_NORMAL);
}
```

### Best Practices Summary

| Category | Do | Don't |
|----------|-----|-------|
| Threads | Use `SC_THREAD`, `wait(SC_ZERO_TIME)`, `while(true)` | End threads prematurely |
| Channels | Use blocking calls | Over-complicate with non-blocking |
| Logging | Use levels, include context | Log in tight loops |
| Errors | Check assertions, handle failures | Ignore error conditions |
| Performance | Use direct access when safe | Copy unnecessarily |
| Debug | Use trackers, prt() methods | Ignore available tools |

---

## Conclusion

This reference covers the essential SystemC APIs for implementing hardware blocks in arch2code. Remember:

- **User APIs** (Sections 2-5): Your primary tools
- **Framework Reference** (Section 6): Understanding generated code
- **Advanced Topics** (Section 7): Specialized features
- **Patterns** (Section 8): Proven implementation approaches
- **Best Practices** (Section 9): Guidelines for quality code

For code generation workflow and YAML architecture, see `ARCH2CODE_AI_RULES.md`.

**Happy coding!**

