---
name: review-model
description: Checklist-driven review of SystemC model code for arch2code conventions, behavioral correctness, tandem readiness, model-RTL conformity, and code quality
globs: "model/**/*.cpp, model/**/*.h"
alwaysApply: false
---
# Skill: Review Model

## Purpose
Perform a structured code review of a SystemC model module within the arch2code framework. The review covers framework conventions, behavioral correctness, tandem verification readiness, lightweight model-RTL conformity checks, and code quality. Functional equivalence between model and RTL is ultimately proven by tandem mode; this review focuses on structural correctness and adherence to standards.

## References
*   **SystemC Core:** `systemc-core.md` (Module structure, threading, logging)
*   **SystemC Patterns:** `systemc-patterns.md` (Producer-Consumer, Register Handler, Multi-Cycle)
*   **SystemC Sync:** `systemc-synchronization.md` (Locking, arbitration, events)
*   **SystemC Interfaces:** `systemc-interfaces.md` (AXI, Rdy/Vld, Push/Ack)
*   **Debugging:** `debug.md` (Trackers, assertions, status reporting)
*   **Tandem:** `run-tandem.md` (Build/run tandem verification)
*   **RTL->SC Conversion:** `rtl-to-systemc.md` (Conversion patterns)

## Instructions

### 1. Arch2code Convention Checks

*   **Generated Code Zones:** Verify no manual edits exist between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers in both `.h` and `.cpp` files.
*   **Header (.h) Layout:** Manual member variables and function declarations are placed **after** `// GENERATED_CODE_END` in the class definition.
*   **Constructor Initializers:** Manual member initializers (starting with `,`) are placed **between** the first `// GENERATED_CODE_END` and the next `// GENERATED_CODE_BEGIN` in the constructor.
*   **Constructor Body:** `SC_THREAD` registrations and other manual logic are placed **after** the final `// GENERATED_CODE_END` in the constructor.
*   **Types -- Arch2code Typedefs Only:** All variables representing hardware signals, registers, counters, factors, addresses, or pixel data **must** use the arch2code-generated typedefs from `*Includes.h` (e.g., `lsc_factor_t`, `pixel_t`, `x_pos_t`), **not** raw C++ integer types (`int32_t`, `uint8_t`, etc.). The generator maps YAML-defined bit-widths to the smallest C++ type that fits (e.g., a 6-bit field becomes `uint8_t`), and the typedef carries the semantic meaning and RTL correspondence. Using raw types loses that traceability and risks width mismatches if the YAML changes. Native C++ types are acceptable **only** for loop iterators, boolean flags (`bool`), and temporaries that have no RTL counterpart. Do not redefine types that exist in the package.
*   **Base Files:** Never modify `*Base.h` files.

### 2. Behavioral Correctness Checks

*   **Thread Safety:** Every `SC_THREAD` `while(true)` loop contains at least one `wait()` call. No infinite spin loops.
*   **Event Synchronization:** Inter-thread communication uses `sc_event` and `wait(event)`. No busy-wait polling of shared variables.
*   **Register Listener Pattern:** Register access uses a dedicated listener thread with `setExternalEvent` + `readNonBlocking` + `wait(event)`. Derived values are cached as class members for use by the main processing thread.
*   **Memory Access:** Memory reads/writes use the `mem->request(isWrite, addr, data)` API. No direct memory manipulation.
*   **No Shared Mutable State Without Events:** If multiple threads access the same data, synchronization is enforced via `sc_event`, not by relying on SystemC cooperative scheduling order.
*   **Blocking vs Non-Blocking:** `port->read()` / `port->write()` for streaming interfaces (blocking). `reg->readNonBlocking()` for registers (non-blocking, in listener threads).

### 3. Tandem / RTL Equivalence Readiness

*   **Deterministic Output:** For identical input stimulus, the model produces identical output transactions. No dependence on uncontrolled state (e.g., random seeds, wall-clock time).
*   **No Hidden State:** All state that affects output transactions is either visible at interface boundaries or is derivable from input stimulus. No internal-only state that could diverge from RTL.
*   **Tracker Lifecycle:** `tracker->alloc()` and `tracker->dealloc()` calls are balanced. Every allocated tag is eventually deallocated.
*   **Tandem Ref Counting:** `getTrackerRefCountDelta()` is used when calling `alloc`/`dealloc` to ensure correct reference counting in tandem mode.
*   **Model/Model First:** The model should pass model/model tandem (`--vlType model --vlTandem`) before attempting RTL/model tandem. This validates that the model itself is tandem-safe.

### 4. Model-RTL Conformity Checks

*   **Read the RTL:** Open the corresponding `rtl/<block>.sv` alongside the model.
*   **Naming Consistency:** Model variable names should be recognizable counterparts of RTL signal names (e.g., RTL `pos_x` maps to model `pos_x`, RTL `gain_factor` maps to model `gain_factor`).
*   **Type/Width Alignment via Typedefs:** Verify that model variables use the **same arch2code typedef** as the corresponding RTL signal's type. For example, if the RTL declares `lsc_factor_t`, the model variable must also be `lsc_factor_t` -- not a raw `int32_t` that happens to be wide enough. This ensures that if the YAML-defined bit-width changes, both model and RTL update automatically via regeneration. Flag any variable representing a hardware-visible value that uses a raw C++ type (`int32_t`, `uint16_t`, etc.) instead of its arch2code typedef as `[FAIL]`.
*   **No Native C++ Types for Signals:** Scan the model `.cpp` and `.h` files for raw C++ integer types (`int8_t`, `uint8_t`, `int16_t`, `uint16_t`, `int32_t`, `uint32_t`, `int64_t`, `uint64_t`). Each occurrence must be justified: loop iterators and non-signal temporaries are acceptable; variables that correspond to RTL signals, struct fields, or intermediate pipeline values must use arch2code typedefs. Cast expressions (e.g., `(lsc_pixel_m_factor_t)value`) are acceptable when converting between types.
*   **Scope:** Functional equivalence (algorithm correctness, rounding behavior, transaction ordering) is proven by tandem mode. Do not duplicate that verification here.

### 5. Code Quality Checks

*   **Logging:** Use `log_.logPrint` with `std::format` for all output. No `printf`, `std::cout`, or `std::cerr`.
*   **Lazy Logging:** Use lambda form for expensive debug formatting: `log_.logPrint([&]() { return std::format(...); }, LOG_DEBUG);`.
*   **Assertions:** Use `Q_ASSERT(condition, "message")` for internal invariants (index bounds, queue capacity, state validity).
*   **Status Reporting:** `statusPrint(void)` is recommended and should be flagged as `[WARN]` (not `[FAIL]`) if missing. When present, it should be registered via `logging::GetInstance().registerStatus(name(), ...)` in the constructor and dump internal state (queues, counters, flags) useful for diagnosing simulation hangs.
*   **No C++ Undefined Behavior:** No out-of-bounds array access, no use-after-free, no signed integer overflow in intermediate calculations.
*   **Tracker Info Struct:** If trackers are used, the info struct has a `prt()` method for human-readable output.

### 6. Review Output Format

Present findings as a checklist. For each category, report:

```
## <Category Name>
- [PASS] <item description>
- [FAIL] <item description> -- <explanation and suggested fix>
- [WARN] <item description> -- <note or recommendation>
- [N/A]  <item description> -- <reason not applicable>
```

Summarize with a count: `X PASS, Y FAIL, Z WARN, W N/A`.

## Constraints
*   This review is for **model code only** (`model/**/*.cpp`, `model/**/*.h`). For RTL code, use the **review-rtl** skill.
*   Do not modify generated code zones or `*Base.h` files.
*   Do not attempt to verify algorithmic equivalence with the RTL -- that is the role of tandem verification.
*   Flag items as `[WARN]` rather than `[FAIL]` when the issue is stylistic rather than functional.
