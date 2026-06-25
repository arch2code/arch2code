# Socket Interface Design: pyuvm ↔ SystemC Transactional Bridge

## Overview

This document describes the design of a TCP socket bridge that allows a Python
process (targeting pyuvm) to participate in arch2code SystemC simulations at the
**transactional** level. The bridge replaces a native SystemC block with a thin
**shell block** whose SC_THREADs are templated functions defined in the
interface files. The rest of the simulation — channels, DUT, testbench
infrastructure — is completely unaware of the substitution.

The design follows the established **tandem block** pattern: just as a tandem
block wraps two sub-instances and uses `port_tee()` functions from the
interface files as SC_THREAD bodies, a socket shell block uses `port_socket()`
functions from the interface files as SC_THREAD bodies. The shell is registered
with `instanceFactory` using a `_socket` suffix (paralleling the `_tandem`
suffix), and selected via the testbench config or command line.

The proof-of-concept targets the `req_ack` interface type. The architecture is
designed to extend to all 13 arch2code interface types once the pattern is
proven.

## Motivation

The existing prototype in `examples/pySocket/` uses **four** separate TCP
sockets for a single `req_ack` channel (py2sc request, py2sc response, sc2py
request, sc2py response). The C++ side uses raw `read()`/`write()` on file
descriptors with manual `poll()` and a helper `SC_THREAD` to bridge between OS
I/O and SystemC events. This approach:

- Does not scale: each additional channel requires two more sockets and more
  glue threads.
- Is not integrated with the channel infrastructure: the bridge logic lives in
  application model code (`pySocket.cpp`) rather than as reusable components.
- Requires the Python side to manage multiple socket pairs manually.

## Design Principles

1. **Shell block, not proxy channel.** The bridge operates at the block level.
   The test block is a thin shell; the `req_ack_channel` (and all its
   infrastructure — interfaceBase, logging, tracking, tee, synchLock) remains
   in the loop untouched. This avoids reimplementing channel internals.

2. **Follows the tandem pattern.** The socket shell mirrors the structure of
   the generated tandem block:
   - Tandem: `SC_MODULE(blockTandem)` inherits `blockBase` + `blockBase`,
     registers as `"block_tandem"`, SC_THREADs call `port_tee()`.
   - Socket: `SC_MODULE(blockSocket)` inherits `blockBase` + `blockBase`,
     registers as `"block_socket"`, SC_THREADs call `port_socket()`.

   The socket shell is *simpler* than tandem — no sub-instances, no
   Inverted ports, no Channels objects. The shell's ports connect directly
   to the container's channels.

3. **`port_socket()` functions in the interface files.** Each interface type
   provides `port_socket()` overloads in a `*_port_socket.h` file, following
   the `*_port_tee.h` naming convention. These are templated free functions
   that serve as SC_THREAD bodies. The port direction (`req_ack_out` vs
   `req_ack_in`) determines the bridge role via overload resolution — exactly
   as `port_tee()` uses port direction to determine tee direction.

4. **Socket factory.** A `socketFactory` class (following the framework's
   `instanceFactory` / `testBenchConfigFactory` patterns) manages the
   lifecycle of all socket connections: registration, listen, accept, thread
   management, and shutdown.

5. **One bidirectional TCP socket per interface.** A single `SOCK_STREAM`
   connection carries both directions of an interface (e.g. request *and*
   acknowledgement for `req_ack`). A lightweight framing protocol
   distinguishes message types.

6. **Transfer raw unpacked C++ structs.** The bytes sent over the socket are
   `sizeof(StructType)` bytes copied directly from the C++ struct instance.
   These are the *unpacked* (natural-alignment, standard-layout) structs,
   **not** the bit-packed `_packedSt` representation. Python reconstructs them
   using `ctypes.Structure` with identical `_fields_` definitions.

7. **ThreadSafeEvent for cross-thread signaling.** The background receiver
   thread uses `ThreadSafeEvent` (`common/systemc/asyncEvent.h`) to safely
   inject events into the SystemC kernel. This is the only sanctioned
   mechanism for cross-thread event notification in SystemC.

8. **Layered Python architecture.** The Python side has three layers:
   - **Transport**: raw TCP socket read/write with framing.
   - **Transaction API**: typed methods mirroring the C++ channel interface.
   - **pyuvm adapter**: wraps the transaction API into pyuvm patterns.

## Architecture

### Tandem vs Socket: Structural Comparison

The tandem block pattern (A2C Pro) provides the structural template for the
socket shell. Both are thin SC_MODULEs that delegate each port to a templated
free function from the interface files:

```
                    Tandem                          Socket
                    ──────                          ──────
Registration    "block_tandem"                  "block_socket"
Inherits        blockBase + blockNameBase       blockBase + blockNameBase
Sub-instances   verif + model (via factory)     (none)
Extra ports     blockInverted × 2              (none)
Extra channels  blockChannels × 2              (none)
SC_THREADs      one per port: calls port_tee() one per port: calls port_socket()
Tee file        req_ack_port_tee.h             req_ack_port_socket.h
Function sig    port_tee(port, priPort, secPort) port_socket(port, ifcName)
Selection       --vlTandem + --vlInst          testbench config / --pySocket
```

The socket shell is simpler because there are no sub-instances to manage. The
shell's ports (inherited from `blockNameBase`) connect directly to the
container's channels via the normal generated `bind()` helpers.

### Block Topology

```
┌─────────────────────────────────────────────────────────┐
│  pySocket_tb (container)                                │
│                                                         │
│  ┌──────────────┐   req_ack_channel   ┌──────────────┐  │
│  │  pySocket    │◄═══════════════════►│     dut      │  │
│  │  (socket     │   test_req_ack      │  (SystemC)   │  │
│  │   shell)     │                     │              │  │
│  │              │   req_ack_channel   │              │  │
│  │              │◄═══════════════════►│              │  │
│  │              │   dut2Python        │              │  │
│  └──────┬───────┘                     └──────────────┘  │
│         │                                               │
│         │ SC_THREADs call port_socket()                  │
│         │ (from req_ack_port_socket.h)                   │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────┐                       │
│  │ socketFactory                │                       │
│  │  • manages socket fds       │                       │
│  │  • manages rx OS threads    │                       │
│  │  • listen / accept / close  │                       │
│  └──────────────┬───────────────┘                       │
│                 │                                       │
└─────────────────┼───────────────────────────────────────┘
                  │ TCP (localhost)
┌─────────────────┼───────────────────────────────────────┐
│  Python Process │                                       │
│                 │                                       │
│  ┌──────────────┴───────────────┐                       │
│  │ SocketTransport (asyncio)    │                       │
│  ├──────────────────────────────┤                       │
│  │ ReqAckTarget (transaction)   │                       │
│  ├──────────────────────────────┤                       │
│  │ ReqAckResponder (pyuvm)      │                       │
│  └──────────────────────────────┘                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Key insight: the **channels are untouched**. They are normal `req_ack_channel`
instances with full logging, tracking, and interfaceBase support. Only the test
block is replaced with a socket shell.

### Component Layers

```
Layer            Location                     Responsibility
─────            ────────                     ──────────────
port_socket()    interfaces/req_ack/          SC_THREAD body: bridge port ↔ socket
Socket factory   common/systemc/              Socket lifecycle, thread management
Wire protocol    common/systemc/              Header framing, send/recv helpers
Shell block      (generated or hand-written)  Thin SC_MODULE: ports + SC_THREAD wrappers
TB config        examples/pySocket/tb/        Factory setup, fork/exec Python
Python transport (python lib)                 asyncio framing
Python txn API   (python lib)                 Typed req/ack/reqReceive methods
pyuvm adapter    (python lib)                 UVM component wrappers
```

## `port_socket()` — Templated Interface Functions

### Location and Naming

```
interfaces/req_ack/req_ack_port_socket.h     (new file)
```

This follows the established naming convention:
- `req_ack_channel.h` — channel implementation
- `req_ack_bfm.h` — BFM (transactional ↔ signal-level bridge)
- `req_ack_port_tee.h` — tandem tee (fork/compare two sub-instances)
- `req_ack_port_socket.h` — socket bridge (transactional ↔ TCP bridge)

### Overloads by Port Direction

Just as `port_tee()` has two overloads based on port direction (one for
`req_ack_in` and one for `req_ack_out`), `port_socket()` has two overloads.
The port type determines the bridge role via overload resolution:

```cpp
// interfaces/req_ack/req_ack_port_socket.h

#ifndef REQ_ACK_PORT_SOCKET_H
#define REQ_ACK_PORT_SOCKET_H

#include "req_ack_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "asyncEvent.h"

// Overload 1: req_ack_out port — shell is initiator
// Python sends REQ → shell forwards via port->req() → sends ACK back to Python
template <class R, class A>
void port_socket(req_ack_out<R, A>& port, const std::string& interface_name)
{
    int fd = socketFactory::getFd(interface_name);

    auto req_event = ThreadSafeEventFactory::newEvent(
        (interface_name + "_req").c_str());

    R req_buf;
    std::atomic<bool> running{true};

    // Background OS thread: recv from Python, notify SC_THREAD
    std::thread rx_thread([&]() {
        uint8_t msg_type;
        uint16_t len;
        while (running.load()) {
            if (!socket_recv_msg(fd, msg_type, &req_buf, len))
                break;
            if (msg_type == MSG_SHUTDOWN)
                break;
            if (msg_type == MSG_REQ)
                req_event->notify();
        }
        running.store(false);
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    // SC_THREAD loop: wait for Python REQ → call port->req() → send ACK
    while (running.load()) {
        wait(req_event->default_event());
        if (!running.load()) break;

        R req_data = req_buf;
        A ack_data;
        port->req(req_data, ack_data);

        socket_send_msg(fd, MSG_ACK, &ack_data, sizeof(A));
    }
}

// Overload 2: req_ack_in port — shell is target
// DUT calls port->req() → shell receives via reqReceive() → sends REQ to Python
// Python sends ACK → shell calls port->ack()
template <class R, class A>
void port_socket(req_ack_in<R, A>& port, const std::string& interface_name)
{
    int fd = socketFactory::getFd(interface_name);

    auto ack_event = ThreadSafeEventFactory::newEvent(
        (interface_name + "_ack").c_str());

    A ack_buf;
    std::atomic<bool> running{true};

    // Background OS thread: recv from Python, notify SC_THREAD
    std::thread rx_thread([&]() {
        uint8_t msg_type;
        uint16_t len;
        while (running.load()) {
            if (!socket_recv_msg(fd, msg_type, &ack_buf, len))
                break;
            if (msg_type == MSG_SHUTDOWN)
                break;
            if (msg_type == MSG_ACK)
                ack_event->notify();
        }
        running.store(false);
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    // SC_THREAD loop: reqReceive() → send REQ to Python → wait ACK → ack()
    while (running.load()) {
        R req_data;
        port->reqReceive(req_data);

        socket_send_msg(fd, MSG_REQ, &req_data, sizeof(R));

        wait(ack_event->default_event());
        if (!running.load()) break;

        A ack_data = ack_buf;
        port->ack(ack_data);
    }
}

#endif // REQ_ACK_PORT_SOCKET_H
```

### Comparison with `port_tee()`

Side-by-side with `req_ack_port_tee.h` to show the structural parallel:

```
port_tee (tandem)                          port_socket (socket bridge)
─────────────────                          ──────────────────────────
void port_tee(                             void port_socket(
    req_ack_in<R,A>& in,                      req_ack_in<R,A>& port,
    req_ack_out<R,A>& outPri,                  const std::string& name)
    req_ack_out<R,A>& outSec)

  in->reqReceive(req);                       port->reqReceive(req);
  outPri->reqNonBlocking(req);               socket_send_msg(fd, MSG_REQ, ...);
  outSec->reqNonBlocking(req);               wait(ack_event);
  outPri->waitAck(ackPri);                   port->ack(ack_buf);
  outSec->waitAck(ackSec);
  ASSERT(ackPri == ackSec);
  in->ack(ackSec);
```

Both are templated free functions. Both are called from thin SC_THREAD
wrappers in the generated block. Both live in the interface directory. The
only difference is the target domain: `port_tee` forks to two internal
instances; `port_socket` bridges to an external TCP socket.

## Socket Shell Block

### Structure (Parallel to Tandem)

The socket shell follows the tandem block's structural pattern:

```cpp
// pySocketSocket.h (generated or hand-written)

#include "req_ack_port_socket.h"
#include "instanceFactory.h"
#include "pySocketBase.h"

SC_MODULE(pySocketSocket), public blockBase, public pySocketBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            instanceFactory::registerBlock("pySocket_socket",
                [](const char * blockName, const char * variant,
                   blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(
                        std::make_shared<pySocketSocket>(
                            blockName, variant, bbMode));
                }, "");
        }
    };
    static registerBlock registerBlock_;

public:
    pySocketSocket(sc_module_name blockName, const char * variant,
                   blockBaseMode bbMode);
    ~pySocketSocket() override = default;

private:
    void test_req_ackSocket(void);
    void test2Python_req_ackSocket(void);
    void dut2Python_req_ackSocket(void);
};
```

```cpp
// pySocketSocket.cpp

#include "pySocketSocket.h"

SC_HAS_PROCESS(pySocketSocket);

pySocketSocket::registerBlock pySocketSocket::registerBlock_;

void pySocketSocket::test_req_ackSocket(void) {
    port_socket(test_req_ack, "test_req_ack");
}

void pySocketSocket::test2Python_req_ackSocket(void) {
    port_socket(test2Python_req_ack, "test2Python_req_ack");
}

void pySocketSocket::dut2Python_req_ackSocket(void) {
    port_socket(dut2Python_req_ack, "dut2Python_req_ack");
}

pySocketSocket::pySocketSocket(sc_module_name blockName, const char * variant,
                               blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()),
                  LOG_IMPORTANT);
    SC_THREAD(test_req_ackSocket);
    SC_THREAD(test2Python_req_ackSocket);
    SC_THREAD(dut2Python_req_ackSocket);
}
```

### Comparison with Tandem Block

```
                        Tandem (preprocessTandem)        Socket (pySocketSocket)
                        ────────────────────────         ───────────────────────
Registration            "preprocess_tandem"              "pySocket_socket"
Inherits                blockBase + preprocessBase       blockBase + pySocketBase
Sub-instances           verif + model                    (none)
Inverted ports          verif_ports + model_ports        (none)
Internal channels       verif_channels + model_channels  (none)
bind() in constructor   verif_channels.bind(...)         (none — ports bound by container)
SC_THREAD body          port_tee(port, pri, sec)         port_socket(port, name)
Include                 req_ack_port_tee.h               req_ack_port_socket.h
Thread wrapper pattern  void portNameTee(void)           void portNameSocket(void)
```

The socket shell is a strict subset of the tandem pattern — same registration,
same inheritance, same SC_THREAD wrapper pattern, but without the sub-instance
and internal channel machinery.

### Instance Selection

Following the tandem precedent where `instanceFactory::registerInstance(path,
"tandem")` causes the factory to construct `"block_tandem"` instead of
`"block_model"`, the socket shell uses the same mechanism:

```cpp
// In testbench config or simController:
instanceFactory::registerInstance("u_pySocket", "socket");
// Now createInstance for u_pySocket resolves to "pySocket_socket"
// instead of "pySocket_model"
```

This could also be driven by a command-line flag (e.g. `--pySocket`) similar
to `--vlTandem`, or hardcoded in a socket-specific testbench config.

## Socket Factory

### Design

`socketFactory` is an all-static class following the framework's established
factory patterns (`instanceFactory`, `testBenchConfigFactory`): function-local
static maps to avoid the static initialization order fiasco, and a clean
registration/lookup API.

### Responsibilities

1. **Registration**: map an interface name to its socket configuration
   (role, port, fd, thread).
2. **Listen**: bind to `localhost:0`, record OS-assigned port.
3. **Accept**: block until the Python side connects. Must complete before
   `sc_start()`.
4. **Provide fds**: `port_socket()` functions retrieve their socket fd from
   the factory by interface name.
5. **Thread management**: track OS threads spawned by `port_socket()`
   functions; provide `shutdownAll()` that closes sockets and joins threads.
6. **Port reporting**: provide the list of (interface_name, port) pairs so the
   testbench config can pass them to the Python child process.

### Interface

```cpp
// common/systemc/socketFactory.h

class socketFactory {
public:
    // --- Setup phase (called from testbench config, before sc_start) ---

    // Register an interface. Creates a listening socket on localhost:0.
    // Returns the OS-assigned port for passing to the Python process.
    static uint16_t registerInterface(const std::string& name);

    // Accept the Python client on a registered interface.
    // Blocks until connection is established. Call after fork/exec.
    static void acceptConnection(const std::string& name);

    // Accept all registered interfaces (convenience).
    static void acceptAll();

    // Get assigned port for a registered interface (for env var plumbing).
    static uint16_t getPort(const std::string& name);

    // Get all registered (name, port) pairs.
    static std::vector<std::pair<std::string, uint16_t>> getAllPorts();

    // Formatted string for env var: "name1:port1,name2:port2"
    static std::string getPortString();

    // --- Runtime phase (called from port_socket() functions) ---

    // Get the connected socket fd for an interface.
    static int getFd(const std::string& name);

    // Register an OS thread associated with an interface (for lifecycle).
    static void registerThread(const std::string& name, std::thread&& t);

    // --- Shutdown phase (called from TB config final or end_of_simulation) ---

    // Send SHUTDOWN on all sockets, close fds, join all threads.
    static void shutdownAll();

private:
    struct SocketEntry {
        int         listen_fd  = -1;   // listening socket (closed after accept)
        int         conn_fd    = -1;   // connected socket
        uint16_t    port       = 0;    // OS-assigned port
        std::thread rx_thread;         // background receiver (from port_socket)
        bool        has_thread = false;
    };

    static std::map<std::string, SocketEntry>& getMap() {
        static std::map<std::string, SocketEntry> map;
        return map;
    }
};
```

### Usage Sequence

```
Testbench config (before sc_start):
  1. socketFactory::registerInterface("test_req_ack")       → port 54321
  2. socketFactory::registerInterface("test2Python_req_ack") → port 54322
  3. socketFactory::registerInterface("dut2Python_req_ack")  → port 54323
  4. setenv("PYSOCKET_PORTS", socketFactory::getPortString())
  5. fork/exec python3 pySocket.py
  6. socketFactory::acceptAll()   // blocks until Python connects all three

During sc_start (SC_THREADs run):
  7. Shell's test_req_ackSocket() calls:
       port_socket(test_req_ack, "test_req_ack")
     which calls socketFactory::getFd("test_req_ack"),
     spawns rx thread, registers it with socketFactory::registerThread(),
     enters bridge loop

  8. (same for the other two ports)

TB config final / end_of_simulation:
  9. socketFactory::shutdownAll()  // close sockets, join threads
```

## Wire Protocol

All messages on a single TCP connection share a common header followed by a
payload. Multi-byte fields are **little-endian** (matching x86-64 native
layout).

### Message Header

```
Offset  Size  Field       Description
──────  ────  ─────       ───────────
0       1     msg_type    Message type (see below)
1       1     reserved    Padding (zero)
2       2     payload_len Payload length in bytes (uint16_t LE)
──────  ────
4 bytes total header
```

### Message Types

For `req_ack<R, A>`:

| `msg_type` | Name          | Direction          | Payload            |
|------------|---------------|--------------------|--------------------|
| `0x01`     | `MSG_REQ`     | initiator → target | `sizeof(R)` bytes  |
| `0x02`     | `MSG_ACK`     | target → initiator | `sizeof(A)` bytes  |

Reserved for future interface types:

| `msg_type` | Name          | Interface type   | Payload            |
|------------|---------------|------------------|--------------------|
| `0x03`     | `MSG_PUSH`    | `push_ack`       | push data          |
| `0x04`     | `MSG_PUSH_ACK`| `push_ack`       | ack data           |
| `0x05`     | `MSG_VLD`     | `rdy_vld`        | valid data         |
| `0x06`     | `MSG_RDY`     | `rdy_vld`        | (empty / token)    |
| `0xFE`     | `MSG_SHUTDOWN`| control           | (empty)            |
| `0xFF`     | `MSG_ERROR`   | control           | error string       |

### Transport Helpers

```cpp
// common/systemc/socketTransport.h

struct SocketMsgHeader {
    uint8_t  msg_type;
    uint8_t  reserved;
    uint16_t payload_len;
};

// Send: header + payload. Returns false on error.
bool socket_send_msg(int fd, uint8_t msg_type,
                     const void* payload, uint16_t len);

// Recv: reads header, then payload. Returns false on EOF/error.
bool socket_recv_msg(int fd, uint8_t& msg_type,
                     void* payload, uint16_t& len);
```

### Payload

The payload is the raw bytes of the **unpacked** C++ struct, copied with
`memcpy(&buf, &struct_instance, sizeof(StructType))`. On the Python side,
an equivalent `ctypes.Structure` with matching `_fields_` and natural
alignment interprets the bytes directly.

Example for `p2s_message_st`:

```c++
// C++ (generated)
struct p2s_message_st {
    param_t param1;  // uint32_t
    param_t param2;  // uint32_t
};
// sizeof(p2s_message_st) == 8, no padding
```

```python
# Python (ctypes mirror)
class p2s_message_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("param1", ctypes.c_uint32),
        ("param2", ctypes.c_uint32),
    ]
# ctypes.sizeof(p2s_message_st) == 8
```

### Framing Guarantees

- TCP is a byte stream; the receiver must loop until `4 + payload_len` bytes
  are consumed for each message.
- `payload_len` is redundant for fixed-size struct payloads but allows the
  receiver to skip unknown message types and supports variable-length payloads
  in the future (e.g. error strings).

## Struct Binary Layout Rules

1. **Standard-layout C types only.** All struct members are fundamental types
   (`uint8_t`, `int8_t`, `uint16_t`, `uint32_t`, `uint64_t`, etc.). No
   virtual methods, no inheritance, no `#pragma pack`.

2. **Natural alignment.** The compiler (and `ctypes`) pad struct members to
   their natural alignment boundary. A `uint32_t` member is aligned to a
   4-byte boundary; `uint64_t` to 8-byte; etc.

3. **No endian conversion.** Both sides are assumed to be the same endianness
   (little-endian x86-64). The Python `ctypes.LittleEndianStructure` base
   class makes this explicit.

4. **`sizeof()` determines transfer size.** The `payload_len` in the wire
   header equals `sizeof(StructType)` on the C++ side and
   `ctypes.sizeof(struct_class)` on the Python side. These must match.

5. **Validation.** A debug-mode assertion can compare `sizeof(R)` (C++) with
   the Python-reported size during a handshake phase (future enhancement).

## Python Side

### Layer 1: Transport (`socket_transport.py`)

```python
class SocketTransport:
    """Raw TCP transport with message framing."""

    def __init__(self, host: str, port: int)
    async def connect(self)
    async def send_msg(self, msg_type: int, payload: bytes)
    async def recv_msg(self) -> tuple[int, bytes]
    async def close(self)
```

Uses `asyncio` streams (`open_connection`). Handles the 4-byte header
framing: pack/unpack `msg_type`, `reserved`, `payload_len`.

### Layer 2: Transaction API (`req_ack_transaction.py`)

```python
class ReqAckInitiator(Generic[R, A]):
    """Python-side initiator: sends REQ, receives ACK."""

    def __init__(self, transport: SocketTransport,
                 req_type: type[ctypes.Structure],
                 ack_type: type[ctypes.Structure])
    async def req(self, request: R) -> A

class ReqAckTarget(Generic[R, A]):
    """Python-side target: receives REQ, sends ACK."""

    def __init__(self, transport: SocketTransport,
                 req_type: type[ctypes.Structure],
                 ack_type: type[ctypes.Structure])
    async def req_receive(self) -> R
    async def ack(self, response: A)
```

These mirror the C++ `req_ack_out_if` / `req_ack_in_if` semantics exactly.
The `ctypes.Structure` subclass handles serialization/deserialization.

### Layer 3: pyuvm Adapter (`req_ack_uvm.py`)

```python
class ReqAckDriver(uvm_driver):
    """Drives req_ack from a UVM sequence."""

    async def run_phase(self):
        while True:
            seq_item = await self.seq_item_port.get_next_item()
            response = await self.initiator.req(seq_item.request)
            seq_item.response = response
            self.seq_item_port.item_done()

class ReqAckResponder(uvm_component):
    """Responds to req_ack requests from SystemC."""

    async def run_phase(self):
        while True:
            request = await self.target.req_receive()
            response = self.generate_response(request)
            await self.target.ack(response)
```

This layer is the final integration point. The PoC validates layers 1 and 2
first; the pyuvm adapter is implemented last.

## Testbench Config Integration

The testbench config orchestrates startup, following the same pattern as the
existing `pySocketConfig`:

```cpp
bool createTestBench(void) override
{
    // 1. Register instance to use socket shell instead of model
    instanceFactory::registerInstance("u_pySocket", "socket");

    // 2. Create hierarchy (factory resolves "pySocket_socket" for u_pySocket)
    auto tb = instanceFactory::createInstance("", "pySocket_tb", "pySocket_tb", "");

    // 3. Register interfaces with the socket factory
    socketFactory::registerInterface("test_req_ack");
    socketFactory::registerInterface("test2Python_req_ack");
    socketFactory::registerInterface("dut2Python_req_ack");

    // 4. Build port string for Python
    setenv("PYSOCKET_PORTS", socketFactory::getPortString().c_str(), 1);

    // 5. Fork/exec Python
    pid_t pid = fork();
    if (pid == 0) {
        execlp("python3", "python3", script_path.c_str(), NULL);
        _exit(127);
    }

    // 6. Accept all connections (blocks until Python connects)
    socketFactory::acceptAll();

    return true;
}

void final(void) override
{
    socketFactory::shutdownAll();
}
```

## Implementation Plan (PoC Steps)

### Step 1: Wire Protocol & Socket Transport

**C++ (`common/systemc/socketTransport.h/.cpp`)**:
- `socket_send_msg()` / `socket_recv_msg()` — framed send/recv helpers.
- `SocketMsgHeader` struct and message type constants.

**Python (`socket_transport.py`)**:
- `SocketTransport` class with `connect()`, `send_msg()`, `recv_msg()`,
  `close()`.

### Step 2: Socket Factory

**C++ (`common/systemc/socketFactory.h/.cpp`)**:
- `registerInterface()`, `acceptConnection()`, `acceptAll()`
- `getFd()`, `getPort()`, `getAllPorts()`, `getPortString()`
- `registerThread()`, `shutdownAll()`
- Function-local static map following framework conventions.

### Step 3: `port_socket()` Functions

**C++ (`interfaces/req_ack/req_ack_port_socket.h`)**:
- `port_socket(req_ack_out<R,A>&, name)` — initiator bridge.
- `port_socket(req_ack_in<R,A>&, name)` — target bridge.
- Background rx thread + ThreadSafeEvent integration.

### Step 4: Socket Shell Block & Testbench Config

- Shell block: `pySocketSocket.h/.cpp` — registers as `"pySocket_socket"`,
  one SC_THREAD per port calling `port_socket()`.
- Testbench config: uses `instanceFactory::registerInstance()` +
  `socketFactory` for socket lifecycle.
- Python: rewrite `pySocket.py` using `SocketTransport` + transaction API.
- Remove old 4-socket IPC code.

### Step 5: Python Transaction API & pyuvm Adapter

- `ReqAckInitiator` / `ReqAckTarget` classes.
- `ReqAckDriver` / `ReqAckResponder` pyuvm wrappers.

### Step 6: End-to-End Test

- Full simulation: SystemC (with socket shell) ↔ Python (with pyuvm).
- Both test paths work through the new architecture.

## File Inventory

```
New files:
  common/systemc/socketTransport.h          Wire protocol helpers
  common/systemc/socketTransport.cpp
  common/systemc/socketFactory.h            Socket lifecycle factory
  common/systemc/socketFactory.cpp
  interfaces/req_ack/req_ack_port_socket.h  port_socket() overloads for req_ack

New files (pySocket example):
  examples/pySocket/model/pySocketSocket.h   Socket shell block header
  examples/pySocket/model/pySocketSocket.cpp Socket shell block implementation

Modified files:
  examples/pySocket/tb/pySocket/pySocketConfig.cpp  Uses socketFactory + registerInstance
  examples/pySocket/pySocket.py                     Uses SocketTransport + transaction API

Removed files:
  examples/pySocket/tb/pySocket/pySocketIpc.h       Old 4-socket IPC
  examples/pySocket/tb/pySocket/pySocketIpc.cpp
```

## Open Questions

1. **Code generation**: The socket shell block and `port_socket()` wrapper
   methods follow a mechanical pattern identical to tandem. They should
   eventually be auto-generated using templates like `classDeclTandem.py` /
   `constructorTandem.py`. Out of scope for the PoC.

2. **`ctypes.Structure` generation**: The Python struct mirrors should be
   auto-generated from the same YAML that produces the C++ structs. Out of
   scope for the PoC.

3. **Multiple channels per process**: The current design is one socket per
   interface. A future optimization could multiplex multiple interfaces over a
   single socket using the `reserved` header byte as a channel ID.

4. **Timing**: The bridge introduces real-time latency (TCP round-trip). For
   functional verification this is acceptable. For timed models, a
   synchronization protocol extension may be needed.
