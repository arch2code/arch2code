# Skill: SystemC Patterns

## Purpose
Reference common SystemC implementation patterns to solve frequent design problems efficiently and consistently.

## References
*   **API Reference:** `SYSTEMC_API_USER_REFERENCE.md` (See "Common Implementation Patterns" section)

## 1. Producer-Consumer
Basic data movement model.
*   **Producer:** Generates data, calls `port->write(data)`.
*   **Consumer:** Processes data, calls `port->read(data)`.
*   **Ref:** `systemc-interfaces.md`

## 2. Register Handler
Handling CPU register access.
*   **Pattern:** Use `registerHandler` template or implement a thread waiting on `apbPort->reqReceive`.
*   **Logic:** Decode address -> Read/Write internal storage -> Respond.
*   **Ref:** `systemc-interfaces.md` (Section 8.5)

## 3. Multi-Interface Handling
Thread servicing multiple inputs.
*   **Mechanism:** `setExternalEvent` + `wait(event)` + `isActive()`.
*   **Flow:** Wait for shared event -> Check all ports for activity -> Process active ones (Arbitrate if needed).
*   **Ref:** `systemc-synchronization.md`

## 4. Multi-Cycle Burst
Transferring large data structures over narrow interfaces.
*   **Writer:** Loop `writeClocked(beat)`.
*   **Reader:** Loop `readClocked(beat)`.
*   **Optimization:** Use `getReadPtr()`/`getWritePtr()` for zero-copy buffer access.
*   **Ref:** `systemc-interfaces.md` (Section 8.6)

## 5. Resource Tracking
Debugging complex flows.
*   **Pattern:** Alloc tracker tag at entry -> Pass tag with data -> Log progress with `prt(tag)` -> Dealloc at exit.
*   **Ref:** `debug.md`
