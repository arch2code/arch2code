# SystemC API Reference for arch2code

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
   - [raw_channel](#49-raw_channel---last-resort-handshake-less-boundary)
   - [axi_read_channel](#410-axi_read_channel---axi-read)
   - [axi_write_channel](#411-axi_write_channel---axi-write)
   - [axi4_stream_channel](#412-axi4_stream_channel---axi4-stream)
   - [external_reg_channel](#413-external_reg_channel---register-owned-by-another-block)
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

This document is the reference for **user-facing SystemC APIs** in the arch2code toolchain. It focuses on the APIs that C++ developers use to implement hardware module behavior in `model/<block>.cppm` files.

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
- `base/<block>Base.cppm` - The block's base class with its port declarations
- `model/<includeName>Includes.cppm` - The constants, types and structures of one YAML context
- Code between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` markers

**User Implementation Files (YOUR CODE):**
- `model/<block>.cppm` - One C++20 module file per block. Your code goes outside the generated markers.
- Your `SC_THREAD` and `SC_METHOD` implementations
- Business logic, algorithms, protocols

### Key Concepts

**Blocks:** SystemC modules (`sc_module`) that represent hardware components
**Ports:** Connection points between blocks (declared in Base classes)
**Channels:** Communication infrastructure connecting ports
**Registers:** CPU-accessible storage with structure types
**Memories:** Arrays of structured data with optional CPU access
**Trackers:** Transaction tracking system for debug

### HW Dimensions vs. C++ Dimensions

Every generated structure carries two separate notions of size:

| Member | Represents | Used For |
|--------|-----------|----------|
| `_bitWidth` | **HW bit width**, the sum of all field widths as defined in YAML | `sc_bv<>` sizing, pack/unpack serialization, address-map calculations |
| `_byteWidth` | **HW byte width**, `(_bitWidth + 7) >> 3` | Register/memory byte footprint in address maps, `addMemory()` calls. A parameterizable structure's footprint is its widest variant's, not this |
| `sizeof(T)` | **C++ storage size**, the actual memory footprint of the C++ struct | Multi-cycle burst sizing, `memcpy`, array allocation |

These are **deliberately different**. C++ storage types are typically wider than the hardware reality they model. For example, a 1-bit `eol_t` field is stored in a `uint8_t` (8× wider), and a 3-field struct of single-bit types has `_byteWidth = 1` but `sizeof = 3`.

**Concrete example:**

```cpp
struct video_frame_t {
    eof_t eof;   // 1 HW bit, stored in uint8_t
    sof_t sof;   // 1 HW bit, stored in uint8_t
    eol_t eol;   // 1 HW bit, stored in uint8_t

    static constexpr uint16_t _bitWidth  = 1 + 1 + 1;       // 3 HW bits
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3; // 1 HW byte
    typedef uint8_t _packedSt;
    // ...
};
// sizeof(video_frame_t) == 3  (three uint8_t members in C++)
// _byteWidth            == 1  (3 HW bits → 1 byte on the wire)
```

**`_packedSt`** is the C++ integer type (or array of `uint64_t` for wide structs) chosen to hold the bit-packed HW representation. `pack()` serializes the C++ struct fields into `_packedSt` using HW-accurate bit positions; `unpack()` does the reverse.

**When each size matters:**

- Use **`_bitWidth` / `_byteWidth`** when reasoning about the hardware: register byte widths, address-space allocation, `sc_bv` template parameters, and pack/unpack operations.
- Use **`sizeof`** when reasoning about C++ memory: multi-cycle channel burst lengths, buffer allocation, `memcpy` sizes, and pointer arithmetic.
- Never assume `sizeof(T)` equals `_byteWidth`. They are independent by design.

### Understanding Code Markers

An abridged `model/myBlock.cppm` for a block without its own `params:` in project `proj`. The `moduleScaffold` and `moduleExport` regions above the class are omitted. The `systemc-core` skill (`rules/skills/systemc-core.md`, sections 1 and 2) shows the whole file and every user slot.

```cpp
// GENERATED_CODE_BEGIN --template=classDecl
using namespace proj_ns;
export SC_MODULE(myBlock), public blockBase, public myBlockBase
{
    // ... generated register and memory members ...
    myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    // GENERATED_CODE_END
    // block implementation members
    uint32_t myUserVariable;
    void myThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(myBlock);
// ... factory registration ...
myBlock::myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("myBlock", name(), bbMode)
        ,myBlockBase(name(), variant)
// GENERATED_CODE_END
        ,myUserVariable(0)
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // ... generated body: register and memory registration, SC_THREAD(regHandler) ...
    // GENERATED_CODE_END
    SC_THREAD(myThread);
}

void myBlock::myThread(void)
{
    // your implementation
}
```

**Important Notes:**
- **Base files (`base/<block>Base.cppm`)** and **Include files (`model/<includeName>Includes.cppm`)** contain only generated code between markers
- These files are **NOT regenerated** from scratch - they use in-place generation
- The markers allow selective regeneration of sections while preserving the file
- **Model files (`model/<block>.cppm`)** allow user code outside markers

**Rules:**
- Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`
- Add your member initializers between the `constructor --section=init` end marker and the `--section=body` begin marker, each starting with a comma
- Implement your logic outside these markers
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

The run's `--verbosity` decides which levels print. Each verbosity adds one level: `low` prints `LOG_ALWAYS`, `medium` adds `LOG_IMPORTANT`, `high` adds `LOG_NORMAL`, and `full` adds `LOG_DEBUG`. The default is `medium`, so `logPrint(msg)` with no level (`LOG_NORMAL`) prints only with `--verbosity high` or above.

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

**Do:**
- Use appropriate log levels
- Include context in log messages
- Log at transaction boundaries
- Use lazy evaluation for expensive formatting

**Don't:**
- Log every cycle in tight loops
- Include sensitive data without filtering
- Use `std::cout` directly (breaks logging hierarchy)

---

## 3. Hardware Objects (USER API)

### 3.1 Direct Register Access

A register the block owns is an `hwRegister` member that the generator declares in the block's `classDecl` region. Its accessors take no simulation time.

**API:**
- `myRegister.read()` - Returns the current value
- `myRegister.write(value)` - Sets the value and notifies the event passed to `registerEvent()`
- `myRegister.registerEvent(&ev)` - Hooks an `sc_event` that fires on each firmware write and on each `write()`. The register holds one event, so a second call replaces the first
- `myRegister.m_val` - The stored value. Assigning to it directly notifies no event

An `hwRegister` has no `->`, no `setExternalEvent` and no `readNonBlocking`.

**Example - React to firmware writes:**

```cpp
void myBlock::controlThread(void)
{
    sc_event ctrlEvent;
    controlReg.registerEvent(&ctrlEvent);
    while (true) {
        wait(ctrlEvent);
        controlRegSt ctrl = controlReg.read();
        // act on ctrl
    }
}
```

Firmware writes a register wider than 32 bits one word at a time, and each word write notifies the event. A thread woken by the low-word write still sees the old high word. A read-only register ignores firmware writes.

### 3.2 Direct Memory Access

**IMPORTANT:** Always use memory APIs, not direct member access.

#### Basic Access

**API:**
- `myMemory.read(index)` - Timed read with delay (preferred for functional code)
- `myMemory.write(index, value)` - Timed write with delay (preferred for functional code)
- `myMemory.writeNoDelay(index, value)` - Write without timing delay (for streaming data with clocked interfaces)
- `myMemory[index]` - **Backdoor access** that skips timing and locking. Use it only for backdoor work such as logging and test initialization

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

**Important - Backdoor Access (`[]`):**
- **Bypasses:** Locking, synchronization, timing delays
- **Use ONLY for:** Logging, test initialization, verification backdoor reads
- **DO NOT use for:** Functional module behavior
- **Functional code:** Always use `read()`, `write()`, or `writeNoDelay()`

#### Atomic Read-Modify-Write

For thread-safe modifications when multiple threads or instances access the same memory.

**API:**
- `myMemory.readRMW(index, magicNumber)` - Start atomic RMW, returns value
- `myMemory.writeRMW(index, value)` - Complete atomic RMW
- `myMemory.releaseRMW(index)` - Release RMW lock without write
- `myMemory.lock(index, magicNumber)` - Acquire lock only
- `myMemory.configureSynch(getAltName(), nullptr)` - Sets the memory up for row locking. Call it once in the constructor body. `readRMW`, `writeRMW`, `releaseRMW` and `lock` assert without it

**Magic Number:** The tandem match key, as for `synchLock::lock` (see section 7.2). In tandem, the memory records each (magic number, row) pair the first copy locks, and the second copy waits until the next recorded pair equals its own. Give each call site its own value.

**Example:**

```cpp
// constructor body, after the generated region:
//     myMemory.configureSynch(getAltName(), nullptr);

void myModule::atomicUpdate() {
    // Match key for this call site (important for tandem mode)
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
- Tandem mode: both copies of the block take the row locks in the same order
- Coordinated access across module instances

### Memory Access Summary

| Method | Timing | Thread-Safe | Use Case |
|--------|--------|-------------|----------|
| `[index]` | None | No | Backdoor (logging, test init, verification) |
| `read(index)` | Yes | No | Timed single-thread |
| `write(index, value)` | Yes | No | Timed single-thread |
| `writeNoDelay(index, value)` | None | No | Interface already provides the timing |
| `readRMW()` | Yes | Yes, after `configureSynch` | Multi-threaded access |
| `writeRMW()` | Yes | Yes, after `configureSynch` | Complete atomic update |

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
| `raw` | Handshake-less data (**last resort**) | External boundary pinouts only |
| `axi_read` | AXI read | Burst read transactions |
| `axi_write` | AXI write | Burst write transactions |
| `axi4_stream` | AXI4-Stream | High-speed streaming |
| `external_reg` | Firmware register owned by another block | Register whose storage lives outside the register handler |

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
- `myPort->isActive()` / `myPort->isNotActive()` - Check whether a value is pending
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration (see `rules/skills/systemc-synchronization.md` Section 1)

**Important - Ready Signaling:**
- Calling `read()` on a destination (sink) interface **signals the module is ready**
- The `read()` function asserts the ready signal and waits for valid data
- This is the standard way to indicate readiness - manual ready control is not needed

**Example - Basic Read:**

```cpp
void consumer::consumerInRdyVld(void)
{
    data_st data;
    
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
- `myPort->requestNonBlocking(isWrite, addr, data)` - Non-blocking request, for tee use only
- `myPort->waitComplete(data)` - Wait for the non-blocking read to complete, for tee use only

**Example - APB Master:**

```cpp
void myModule::apbMaster() {
    apbAddrSt addr;
    apbDataSt data;
    
    // Write transaction
    addr.address = 0x100;
    data._setData(0xDEADBEEF);
    apbPort->request(true, addr, data);  // Blocking write
    
    // Read transaction
    addr.address = 0x100;
    apbPort->request(false, addr, data);  // Blocking read, data returned
    
    log_.logPrint(std::format("Read value: 0x{:x}", data._getData()));
}
```

#### Completer Side (Responding to Requests)

**API:**
- `myPort->reqReceive(isWrite, addr, data)` - Wait for and receive request
  - Returns `isWrite` flag and request data
- `myPort->complete(data)` - Send read response data
- `myPort->isActive()` / `myPort->isNotActive()` - Check whether a request is pending
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration (see `rules/skills/systemc-synchronization.md` Section 1)

**Register bus ports:** When a block's `apb` port is its register bus, the generator writes the handler (`regHandler`, which calls `registerHandler(_a2cRegs, ...)`, and `SC_THREAD(regHandler)`). Never add a thread on the register bus port. See section 8.5.

### 4.3 memory_channel - Memory Access Protocol

1-cycle latency memory interface. Same API as APB but optimized for memory timing.

**API:** Same as `apb_channel`
- `request()` on requester side (`requestNonBlocking()` and `waitComplete()` are for tee use only)
- `reqReceive()`, `complete()`, `isActive()`/`isNotActive()`, `setExternalEvent(event)` on completer side

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
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration

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
- `myPort->isActive()` / `myPort->isNotActive()` - Check whether a push is pending
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration

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
- `myPort->isActive()` / `myPort->isNotActive()` - Check whether a pop is pending
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration

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
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration

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
- `myPort->write(value)` - Update status (non-blocking). A `write()` that repeats the current value raises no event, except the first `write()`, which always does

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
- `myPort->read(value)` - Blocks until the next event, then returns the current value
- `myPort->readNonBlocking(value)` - Samples the current value (non-blocking)
- `myPort->setExternalEvent(event)` - Replaces the port's own event, so `read()` also returns when another port fires it. There is no `isActive()`

`read()` wakes on each firmware write, on the first `write()`, and on each later `write()` that changes the value. The initial value raises no event, so a thread that needs it at start-up samples it with `readNonBlocking()` first. `read()` can return the value it returned last time, so compare with the last value seen.

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

### 4.9 raw_channel - Last Resort Handshake-Less Boundary

**`raw` is supported but is an interface of last resort.** Prefer `rdy_vld`,
`push_ack`/`pop_ack`, or `axi4_stream` for new interconnect. Use `raw` only at
design **boundaries** when adapting to **external IP** whose pinout is
a free-running data bus with **no ready/valid/ack wires** (validity usually
encoded in the payload). Do **not** use `raw` for new internal pipeline links
between arch2code blocks.

RTL exposes only `data`. SystemC provides a blocking `write()` / `read()`
rendezvous so threads stay in lockstep in simulation. That rendezvous is **not**
expressed on the wire, and timed/tandem runs can diverge if delay is enabled.

**Do not confuse with `status`:** same wire shape; `status` is publish/sample
(non-blocking write), `raw` is a one-shot transfer that blocks both sides until
the beat is consumed.

**Note:** `raw_channel` signals both "value written" and "value taken" on one
`sc_event` unless the reader passes its own event to `setExternalEvent()`. On
that single-event path each side gets a spurious wake-up per beat. Prefer a
handshaked protocol whenever possible.

#### Source Side

**API:**
- `myPort->write(data)` - Blocking write; waits until the sink consumes the value

```cpp
void producer::driveExternalBoundary(void)
{
    video_csi_t beat;
    // ... fill beat (validity may live in payload fields) ...
    csi_video_in->write(beat);
}
```

#### Sink Side

**API:**
- `myPort->read(data)` - Blocking read; waits until a value is written
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*`. `raw` has no `isActive()`

```cpp
void consumer::sampleExternalBoundary(void)
{
    video_csi_t beat;
    csi_video_in->read(beat);
    // Convert to rdy_vld (or similar) at the first internal hop
}
```

### 4.10 axi_read_channel - AXI read

AXI read with an address channel (`axiReadAddressSt`: `arid`, `araddr`, `arlen`, `arsize`, `arburst`) and a read data channel (`axiReadRespSt`: `rid`, `rdata`, `rresp`, `rlast`). Responses are matched to requests by ID. The burst buffer calls (`push_burst`, `getReadPtr`, `getWritePtr`, `sendData(first, beats)`) and the per-beat calls need the interface's YAML entry to set `multiCycleMode` and `maxTransferSize`.

#### Source side (manager)

**API:**
- `myPort->sendAddr(addr)` - Send a read request
- `myPort->receiveData(resp)` - Blocking read of the response
- `myPort->push_burst(beats)` - Before `sendAddr`, size the receive buffer for a burst of `beats` responses
- `myPort->getReadPtr()` - After `receiveData`, a pointer to the received burst buffer
- `myPort->receiveDataCycle(resp)` - Receive one beat. Needs the interface's `multiCycleMode` and `setCycleTransaction(PORTTYPE_OUT)` on this port

```cpp
axiReadAddressSt<axiAddrSt> addr;
addr.arid = 0x1;
addr.arlen = 255;               // 256 beats
addr.arsize = 0x2;              // 4 bytes per beat
addr.arburst = AXIBURST_INCR;
axiReadRespSt<axiDataSt> data;
axiRd0->push_burst(256);
axiRd0->sendAddr(addr);
axiRd0->receiveData(data);
auto *buff = reinterpret_cast<axiReadRespSt<axiDataSt> *>(axiRd0->getReadPtr());
```

#### Sink side (subordinate)

**API:**
- `myPort->receiveAddr(addr)` - Blocking wait for a read request
- `myPort->sendData(resp)` - Send one response
- `myPort->sendData(first, beats)` - Send `beats` responses from the buffer that `getWritePtr()` returns. `first` is its first element
- `myPort->getWritePtr()` - The send buffer, to fill before `sendData(first, beats)`
- `myPort->sendDataCycle(resp)` - Send one beat. Needs `multiCycleMode` and `setCycleTransaction(PORTTYPE_IN)` on this port
- `myPort->isActive()` / `myPort->isNotActive()` - Whether a read request is pending on the address channel
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` to the address channel

```cpp
axiReadAddressSt<axiAddrSt> addr;
auto *resp = reinterpret_cast<axiReadRespSt<axiDataSt> *>(axiRd0->getWritePtr());
axiRd0->receiveAddr(addr);
int beats = addr.arlen + 1;
for (int i = 0; i < beats; i++) {
    resp[i].rid = addr.arid;
    resp[i].rresp = AXIRESP_OKAY;
    resp[i].rdata.data = i;
}
axiRd0->sendData(*resp, beats);
```

### 4.11 axi_write_channel - AXI write

AXI write with an address channel (`axiWriteAddressSt`: `awid`, `awaddr`, `awlen`, `awsize`, `awburst`), a write data channel (`axiWriteDataSt`: `wid`, `wdata`, `wstrb`, `wlast`) and a response channel (`axiWriteRespSt`: `bid`, `bresp`). As for `axi_read`, the burst buffer calls and the per-beat calls need `multiCycleMode` and `maxTransferSize` on the interface.

#### Source side (manager)

**API:**
- `myPort->sendAddr(addr)` - Send a write request
- `myPort->sendData(data)` - Send one data beat
- `myPort->sendData(first, beats)` - Send `beats` data beats from the buffer that `getSendDataPtr()` returns. `first` is its first element
- `myPort->getSendDataPtr()` - The send buffer, to fill before `sendData(first, beats)`
- `myPort->receiveResp(resp)` - Blocking read of the write response
- `myPort->sendDataCycle(data)` - Send one beat. Needs `multiCycleMode` and `setCycleTransaction(PORTTYPE_OUT)` on this port

```cpp
axiWr0->sendAddr(addr);
auto *buff = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr0->getSendDataPtr());
for (int i = 0; i < 256; i++) {
    buff[i].wid = addr.awid;
    buff[i].wdata.data = i;
    buff[i].wstrb.strobe = 0xF;
    buff[i].wlast = (i == 255);
}
axiWr0->sendData(*buff, 256);
axiWriteRespSt<> resp;
axiWr0->receiveResp(resp);   // often in a separate thread
```

#### Sink side (subordinate)

**API:**
- `myPort->receiveAddr(addr)` - Blocking wait for a write request
- `myPort->receiveData(data)` - Blocking read of the data
- `myPort->getReceiveDataPtr()` / `myPort->getReceiveBeatCount()` - After `receiveData`, the received burst buffer and its beat count
- `myPort->sendResp(resp)` - Send the write response
- `myPort->receiveDataCycle(data)` - Receive one beat. Needs `multiCycleMode` and `setCycleTransaction(PORTTYPE_IN)` on this port
- `myPort->isActive()` / `myPort->isNotActive()` - Whether a write request is pending on the address channel
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` to the address channel

```cpp
axiWriteAddressSt<axiAddrSt> addr;
axiWriteDataSt<axiDataSt, axiStrobeSt> first;
axiWr0->receiveAddr(addr);
axiWr0->receiveData(first);
auto *data = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr0->getReceiveDataPtr());
// check data[0 .. addr.awlen]
axiWriteRespSt<> resp;
resp.bid = addr.awid;
resp.bresp = AXIRESP_OKAY;
axiWr0->sendResp(resp);
```

### 4.12 axi4_stream_channel - AXI4-Stream

One data channel carrying `axi4StreamInfoSt` (`tdata`, `tstrb`, `tkeep`, `tid`, `tlast`, `tdest`, and `tuser` when the interface has one). `tstrb` and `tkeep` hold one qualifier per byte, indexed with `[]` and set to `Q_TRUE` or `Q_FALSE`.

#### Source side

**API:**
- `myPort->sendInfo(info)` - Blocking send of one transfer

#### Sink side

**API:**
- `myPort->receiveInfo(info)` - Blocking receive of one transfer
- `myPort->isActive()` / `myPort->isNotActive()` - Whether a transfer is pending
- `myPort->setExternalEvent(event)` - Bind an external `sc_event*` for multi-interface arbitration

```cpp
void myBlock::streamThread(void)
{
    while (true) {
        // the port's template arguments, as declared in the base class
        axi4StreamInfoSt<data_t, tid_t, tdest_t, tuser_t> info;
        axisIn->receiveInfo(info);
        // ...
        axisOut->sendInfo(info);
    }
}
```

### 4.13 external_reg_channel - Register owned by another block

A firmware register whose storage lives in the block that owns it, not in the register handler. The src side is normally the generated register handler. The dst side is the owning block.

#### Source side (register handler)

**API:**
- `myPort->reg_write_cmd(value)` - Issues a firmware write. It wakes the owner's `read()` and leaves the readback value unchanged. A test driver that emulates firmware uses this call too
- `myPort->readNonBlocking(value)` - The readback value the owner last published
- `myPort->write(value)` - Never wakes the owner's `read()`. Do not use it to drive the owner

#### Sink side (owning block)

**API:**
- `myPort->read(value)` - Blocks until firmware writes and returns the written value
- `myPort->update_mirror(value)` - Publishes the value firmware reads back, without waking `read()`
- `myPort->reg_write(value)` - Publishes the readback value and also wakes `read()`, so do not use it from a block that loops on `read()`
- `myPort->setExternalEvent(event)` - Hooks a shared event. It fires only on `write()`, never on a firmware write. There is no `isActive()`

```cpp
void myBlock::ctrlThread(void)
{
    ctrlRegSt ctrl;
    while (true) {
        ctrlReg->read(ctrl);          // wait for a firmware write
        // apply ctrl, then publish the readback value
        ctrlReg->update_mirror(ctrl);
    }
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
| Firmware register stored in the block that owns it | `external_reg` |
| External handshake-less boundary only | `raw` (**last resort**) |

---

## 5. Transaction Tracking (USER API)

Trackers follow transactions and resources as they flow through your design.

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
- User code allocates a tag, such as a command ID, when a transaction enters the system
- Tag carries an info object of the tracker's type `T` (source, destination, size, type)
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

The testbench registers each tracker by name in `<dut>Config::createTestBench()`, before `createTbTop()`. The `debug` skill (`rules/skills/debug.md`) shows how. `getTracker` asserts `Tracker not found` for a name not yet registered.

**By Name:** `alloc`, `dealloc` and `info` belong to `tracker<T>`, so cast the `trackerBase` pointer:
```cpp
// member, initialized in the constructor
std::shared_ptr<tracker<tagInfo>> cmdTracker;
,cmdTracker(std::static_pointer_cast<tracker<tagInfo>>(trackerCollection::GetInstance().getTracker("cmd")))
```

**From Ports:** `myPort->getTracker()` returns the `trackerBase` bound to the port, which offers the printing and backdoor calls below.

### User API Reference

#### `tracker->alloc(tag, info, getTrackerRefCountDelta())`
Allocate `tag` and attach the info object `info` (a `std::shared_ptr<T>`).

**Use Case:** Call when a transaction enters your system or when allocating a resource. The tag must be allocated before the first transfer that carries it.

**Example:**
```cpp
void myModule::newCommand(uint32_t tag, uint32_t cmdId) {
    auto info = std::make_shared<tagInfo>();
    info->cmdId = cmdId;
    cmdTracker->alloc(tag, info, getTrackerRefCountDelta());
    log_.logPrint(cmdTracker->prt(tag, "Command allocated"), LOG_NORMAL);
}
```

#### `tracker->dealloc(tag, getTrackerRefCountDelta())`
Deallocate a tag when the transaction completes.

**Use Case:** Call when transaction finishes or resource is released. `getTrackerRefCountDelta()` halves the reference count step in tandem, where both copies allocate and release the same tag, so pass it to both `alloc` and `dealloc`.

**Example:**
```cpp
void myModule::commandComplete(uint32_t tag) {
    log_.logPrint(cmdTracker->prt(tag, "Command complete"), LOG_NORMAL);
    cmdTracker->dealloc(tag, getTrackerRefCountDelta());
}
```

#### `tracker->prt(tag)`
Print tag information as a formatted string.

**Returns:** String with tracker prefix, sequence number, and transaction data

**Example:**
```cpp
void myModule::logTransaction(uint32_t tag) {
    auto tracker = myPort->getTracker();
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
Get the info object attached at `alloc`. Only `tracker<T>` has it.

**Returns:** `std::shared_ptr<T>`

**Example:**
```cpp
auto info = cmdTracker->info(tag);
// Access fields from info structure
log_.logPrint(std::format("Command: {}", info->cmdId));
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

A DMA block takes a free buffer for each command and uses the buffer number as the tag. Every stage logs through the tag, and the last stage releases it. `cmdTracker` is a `std::shared_ptr<tracker<dmaInfo>>` member initialized as in "Accessing Trackers". `dmaInfo` is an info type like the `debug` skill's `tagInfo`: a `cmdId` member, a default constructor, a constructor that takes a `std::string`, and a `std::string prt()` method.

```cpp
void dmaController::commandReceive(void)
{
    while (true) {
        dma_cmd_t cmd;
        cmdIn->read(cmd);
        uint32_t bufferId = takeFreeBuffer();
        auto info = std::make_shared<dmaInfo>();
        info->cmdId = cmd.cmdId;
        cmdTracker->alloc(bufferId, info, getTrackerRefCountDelta());
        cmd.bufferId = bufferId;
        log_.logPrint(cmdTracker->prt(bufferId, "DMA cmd accepted"), LOG_NORMAL);
        moveOut->write(cmd);
    }
}

void dmaController::dataMove(void)
{
    while (true) {
        dma_cmd_t cmd;
        moveIn->read(cmd);
        log_.logPrint(cmdTracker->prt(cmd.bufferId, std::format("Moving {} bytes", cmd.length)), LOG_NORMAL);
        performTransfer(cmd);
        log_.logPrint(cmdTracker->prt(cmd.bufferId, "DMA complete"), LOG_NORMAL);
        cmdTracker->dealloc(cmd.bufferId, getTrackerRefCountDelta());
        releaseBuffer(cmd.bufferId);
    }
}
```

**Output Example** (prefix `C#`, sequence number in hex, then the info object's `prt()`):
```
DMA cmd accepted C#1{cmd:7}
Moving 4096 bytes C#1{cmd:7}
DMA complete C#1{cmd:7}
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
- A channel that carries a tracker field logs every transfer through the tracker. A transfer whose tag is not allocated fails the run with `Invalid tracker interface data`

**Tag Validity:**
- Tags are valid only between `alloc` and `dealloc`
- `prt`, `info`, `getLen` and the other per-tag calls assert on a tag that is out of range or not allocated

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
- `addMemory(address, size, name, ptr)` - Register a memory. A memory with a parameterizable structure is registered this way, with `size` the row stride times the row count
- `addMemory(address, structByteWidth, wordLines, name, ptr)` - Register memory with dimensions
- `cpu_read(address)` - Read from address space
- `cpu_write(address, value)` - Write to address space
- `registerHandler<ADDR, DATA>(regs, apbPort, addressMask)` - Template helper the generated `regHandler` thread calls

**Where Used:** Generated register handler initialization. The generator emits the `_a2cRegs` member, every `addRegister`/`addMemory` call, `regHandler` and `SC_THREAD(regHandler)`. Never hand-write them.

**Example (generated code):**
```cpp
// In generated constructor body:
_a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLELOCAL, aRegSt::_byteWidth, BSIZE,
               std::string(this->name()) + ".blockATableLocal", &blockATableLocal_adapter);
_a2cRegs.addRegister( REG_ADDR_BLOCKA_ROA, 1, "roA", &roA );
```

**User Access:** Access registers/memories via direct APIs (Section 3)

### 6.5 instanceFactory (Framework)

**Purpose:** Factory for creating module instances dynamically.

**Framework APIs:**
- `registerBlock(blockType, factory, variant, projectName)` - Register a constructor under the key `(blockType, variant, projectName)`. `blockType` is `<block>_model`, `<block>_verif`, `<block>_socket` or `<block>_tandem`. The first registration under a key wins; a later one is ignored.
- `createInstance(hierarchy, instanceName, blockType, variant, projectName)` - Create a module instance from the registration under that key, falling back to the empty variant.
- `createInstance<Impl>(hierarchy, instanceName, blockType, variant, projectName)` - Same lookup, but when the exact key has no registration and the request is for the model, construct `Impl`. Generated code uses this form for a child whose Config comes from its container.
- `createInstance(hierarchy, instanceName, blockType, variant, projectName, containerSuppliedFactory)` - The non-template form behind `createInstance<Impl>`. The factory answers model requests only.

The fifth argument is a factory domain, not always a bare project name. At a site whose child declares its own `params:` (every variant site) it is the dotted registration key `<owner>.<parentModule>.<childModule>`. For any other child it is the child's owning project.

**Where Used:** Generated constructors, testbenches and registrar files

**Example (generated code):**
```cpp
uBlockD(std::dynamic_pointer_cast<blockDBase>(
    instanceFactory::createInstance(name(), "uBlockD", "blockD", "", "mixed")
))
uLeafA(std::dynamic_pointer_cast<xpInhLeafBase<Config>>(
    instanceFactory::createInstance<xpInhLeaf<Config>>(name(), "uLeafA", "xpInhLeaf", variant,
        "xpInhVar.xpInhVar_xpInhCont.xpInhVar_xpInhLeaf")
))
```

**User Access:** Instances created automatically, users just use them. The key, lookup order and registrar files are specified in `specs/spec-block-registration.md`.

### 6.6 hwRegister/hwMemory Constructors (Framework)

**Purpose:** Construct register and memory objects.

**Framework APIs:**
- `hwRegister<REG_DATA, N, RO>(initialValue)` - Construct register. `N` is the register size in bytes (default 4) and `RO` is `true` for a read-only register
- `hwMemory<MEM_DATA, ROW_BYTES>(hierarchicalName, memName, memories, rows, type, fwAccess)` - Construct memory. `fwAccess` is `HWMEMORYFWACCESS_RW` (default), `_RO` or `_WO`, from the memory's `regAccess`
- `hwMemoryPort<ADDR, DATA, ROW_BYTES>(port, fwAccess, name)` - Firmware adapter a register handler uses to reach a memory over its channel; `fwAccess` and `name` default to rw and empty
- `bindPort()` - Bind memory to channel port

`ROW_BYTES` is the address stride between rows. It defaults to the structure's byte width rounded up to a power of two, at least 4. A value that is not a power of two, or is smaller than that default, fails to compile. For a parameterizable structure the generated code passes the address map's stride, sized for the widest variant, so row N sits at the same address in every variant. Bytes of a row past the bound variant's width read 0 and drop writes, as in the RTL.

Firmware access goes through `cpu_read`/`cpu_write`. On an `ro` memory `cpu_write` drops the write, and on a `wo` memory `cpu_read` returns 0; each logs at `LOG_ALWAYS`, so it prints at every verbosity, naming the memory and the offset. Block-side `read`/`write` ignore the mode.

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

A mutex that also records decisions so tandem can replay them. The `systemc-synchronization` skill (`rules/skills/systemc-synchronization.md`, section 2) has the full rules.

**Purpose:** Guard state shared between threads, and record timing-dependent arbitration choices.

**Note:** Memory RMW operations use a row lock internally (see section 3.2).

**API:**
- `synchLockFactory<T>::getInstance().newLock(getAltName(), lockName)` - Create a lock. `T` defaults to `uint64_t`. `getAltName()` gives both tandem copies the same key. Lock names must be unique within a block instance
- `lock->lock(value)` - Take the mutex. `value` is the tandem match key, so give each call site its own value
- `lock->unlock()` - Release it. There is no RAII guard, so unlock on every path out
- `lock->arb(value)` - Record the winner your code chose. Outside tandem it returns `value`. In tandem the second copy returns the first copy's value. Keep `arb()` and `lock()` on separate locks

**Example - Guard shared state:**

```cpp
// block implementation members
std::shared_ptr<synchLock<>> stateLock;

// constructor initializers
        ,stateLock(synchLockFactory<>::getInstance().newLock(getAltName(), "stateLock"))

void myModule::thread1(void)
{
    stateLock->lock(LOCK_SITE_THREAD1);   // a constant the block defines, one per call site
    accessSharedResource();
    stateLock->unlock();
}
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
    
    auto tracker = myPort->getTracker();
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
- Use for performance-critical paths
- Use when standard APIs insufficient
- Requires careful testing
- Can bypass safety checks

---

## 8. Common Implementation Patterns

Complete examples of common module implementation patterns.

### 8.1 Basic Module Structure

The file layout, generated regions and user slots of `model/<block>.cppm` are in section 1, "Understanding Code Markers". Register the thread with `SC_THREAD(mainThread);` after the `constructor --section=body` end marker, and declare it in the class after the `classDecl` region.

```cpp
void myModule::mainThread(void)
{
    while (true) {
        data_st data;
        inputPort->read(data);   // blocks, so the loop needs no wait()

        log_.logPrint(std::format("Received: 0x{:x}", data.value));

        result_st result = processData(data);
        outputPort->write(result);
    }
}
```

### 8.2 Producer Pattern (rdy_vld source)

```cpp
void producer::dataGenerator() {
    data_st data;
    uint32_t counter = 0;
    
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
    while (true) {
        apbAddrSt addr;
        apbDataSt data;
        
        // Write transaction
        addr.address = 0x1000;
        data._setData(0xDEADBEEF);
        
        log_.logPrint(std::format("APB Write addr:0x{:x} data:0x{:x}", 
                                  addr._getAddress(), data._getData()));
        
        apbPort->request(true, addr, data);
        
        // Read transaction
        addr.address = 0x1000;
        apbPort->request(false, addr, data);
        
        log_.logPrint(std::format("APB Read addr:0x{:x} data:0x{:x}",
                                  addr._getAddress(), data._getData()));
        
        wait(100, SC_NS);
    }
}
```

### 8.5 APB Slave / Register Handler Pattern

The generator writes the register handler: `regHandler`, its `registerHandler(_a2cRegs, ...)` call, `SC_THREAD(regHandler)`, and the `_a2cRegs.addRegister`/`addMemory` calls. Never add a thread on the register bus port.

The one hand-written register thread serves a local `regType: memory` register. It answers on `<reg>_channel` with `reqReceive` and `complete`, against storage the block declares:

```cpp
void blockA::blockATableLocalModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        aRegSt data;
        blockATableLocal_channel.reqReceive(isWrite, addr, data);
        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockATableLocal_shadow_.size()) {
            log_.logPrint(std::format("blockATableLocalModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockATableLocal_channel.complete(aRegSt());
            }
            continue;
        }
        if (isWrite) {
            blockATableLocal_shadow_[idx] = data;
        } else {
            blockATableLocal_channel.complete(blockATableLocal_shadow_[idx]);
        }
    }
}
```

### 8.6 Multi-Cycle Burst Pattern

The interface's YAML entry must set `multiCycleMode`, plus `maxTransferSize` where the mode needs it. Without it, `writeClocked` sends each beat as a full transaction. Do not mix beat calls and whole-transaction calls on one interface.

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
        burstPort->writeClocked(burstData[i]);  // blocks per beat
    }
}

void myModule::burstRead() {
    const int BURST_LEN = 256;
    data_st burstData[BURST_LEN];
    
    // Receive burst cycle-by-cycle
    for (int i = 0; i < BURST_LEN; i++) {
        burstPort->readClocked(burstData[i]);  // blocks per beat
    }
    
    // Process received burst
    processBurst(burstData, BURST_LEN);
}
```

### 8.7 Register/Memory Access Pattern

```cpp
void myModule::registerAccess() {
    // Register access takes no simulation time
    controlRegSt ctrl = controlReg.read();
    ctrl.enable = 1;
    ctrl.mode = 3;
    controlReg.write(ctrl);  // also notifies the registerEvent() event
}

void myModule::memoryAccess() {
    // Timed memory access
    aMemSt data = myMemory.read(0x100);
    data.field += 1;
    myMemory.write(0x100, data);
    
    // Backdoor read for logging only (no timing)
    log_.logPrint(myMemory[0x100].prt(), LOG_DEBUG);
}

// needs myMemory.configureSynch(getAltName(), nullptr) in the constructor body
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

#### Add an initial wait(SC_ZERO_TIME) only when the thread needs other threads to start first

A thread that blocks in a port call needs no initial wait. Add one only when the thread's first action reads state that another thread sets when it starts. The wait gives the other threads their first delta cycle.

```cpp
void myModule::myThread() {
    wait(SC_ZERO_TIME);   // let the other threads run their first delta cycle
    while (true) {
        // ...
    }
}
```

#### Use while(true) for Continuous Operation

```cpp
// Good: Continuous processing
void myModule::processor() {
    while (true) {
        data_st data;
        inputPort->read(data);   // blocks, so the loop needs no wait()
        processData(data);
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
```

#### Let Channels Handle Handshaking

```cpp
// Good: Channel handles ready/valid
void myModule::autoHandshake() {
    data_st data;
    outputPort->write(data);  // Channel manages handshake
}

// Only for advanced cases, on an rdy_vld sink port:
void myModule::manualHandshake() {
    inputPort->enable_user_ready_control();
    inputPort->set_rdy(true);
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
log_.logPrint(std::format("State: {} -> {}", oldState, newState), LOG_DEBUG);

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

### 9.5 Performance

#### Skip the memory delay only where an interface already times the access

```cpp
// Timed access in datapath code
value = myMemory.read(index);

// The clocked interface already provided the timing
inputPort->readClocked(beat);
myMemory.writeNoDelay(index, beat);
```

`myMemory[index]` skips timing too, but it is only for backdoor uses such as logging.

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
| Threads | Use `SC_THREAD` and `while(true)` | End threads prematurely |
| Channels | Use blocking calls | Over-complicate with non-blocking |
| Logging | Use levels, include context | Log in tight loops |
| Errors | Check assertions, handle failures | Ignore error conditions |
| Performance | Use zero-copy buffer pointers | Copy unnecessarily, or use `[]` in datapath code |
| Debug | Use trackers, prt() methods | Ignore available tools |

---

## Conclusion

This reference covers the essential SystemC APIs for implementing hardware blocks in arch2code. Remember:

- **User APIs** (Sections 2-5): Your primary tools
- **Framework Reference** (Section 6): Understanding generated code
- **Advanced Topics** (Section 7): Specialized features
- **Patterns** (Section 8): Proven implementation approaches
- **Best Practices** (Section 9): Thread, channel, logging, error-handling, performance and debug guidelines

For code generation workflow and YAML architecture, see `ARCH2CODE_AI_RULES.md`.

