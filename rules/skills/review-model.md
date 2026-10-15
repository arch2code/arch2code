---
name: review-model
description: Checklist-driven review of SystemC model code for arch2code conventions, behavioral correctness, tandem readiness, model-RTL conformity, and code quality
---
# Skill: Review model

## Purpose
Review a SystemC model block against arch2code conventions, behavioral correctness, tandem readiness, light model-RTL conformity and code quality. Tandem proves functional equivalence with the RTL, so this review checks structure and standards.

## References
*   **systemc-core**: module layout, user slots, register and memory access, threads, logging.
*   **systemc-interfaces**: port calls for each family.
*   **systemc-synchronization**: shared events, `synchLock`, tandem-safe arbitration.
*   **systemc-patterns**: multi-cycle bursts.
*   **debug**: trackers, assertions, `statusPrint`.
*   **run-tandem** (A2C Pro): building and running tandem.

## Instructions

### 1. Arch2code conventions
*   **Generated regions.** Nothing is hand-edited between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` in `model/<block>.cppm`. A block model has `moduleScaffold --section=blockModuleHeader`, `moduleExport`, `classDecl` and `constructor --section=init` / `--section=body`. In a project with an `addressBlock:` router, a block that has children and owns registers or firmware-accessible memories also has a register handler model, whose regions are `blockRegs --section=header`, `--section=init` and `--section=body`. A leaf block's own model holds its `regHandler`.
*   **User slots.** Members follow the class region's end marker. Initializers, each starting with a comma, sit between the `init` end marker and the `body` begin marker. `SC_THREAD` registrations follow the `body` end marker. Imports and headers sit in the slots **systemc-core** describes.
*   **Class shape.** The class is a `template<typename Config>` class, with `using <block>Base<Config>::...` lines, only when the block declares its own `params:`. Otherwise it is a plain class, and its out-of-class definitions are `void blk::fn()`. Either shape is correct when it matches the YAML.
*   **Base files.** `*Base.cppm` files are unmodified.

### 2. Behavioral correctness
*   **Thread loops.** Every `SC_THREAD` loop blocks somewhere. A loop that blocks in a port call (`read()`, `receiveAddr()`, `request()`) needs no explicit `wait()`. FAIL only a loop of non-blocking calls with no `wait()`, because it spins.
*   **Loop exits.** A counted loop exits on a value its counter's type can hold. FAIL `for (i = 0; i < N; i++)` when `i` has a YAML type and N is one past its maximum, even if the C++ typedef happens to be wide enough, because the RTL loop with the same type never ends. The fix is the test-then-increment form in **systemc-core**, section 4.
*   **Shared state.** Threads that share data synchronize with an `sc_event` or a `synchLock`, not with cooperative scheduling order. A thread does not busy-poll a shared variable.
*   **Owned registers.** A register the block owns is an `hwRegister` member. It is read with `reg.read()`, and a thread reacting to firmware writes calls `reg.registerEvent(&ev)` once and loops on `wait(ev)`. It has no `->`, no `setExternalEvent` and no `readNonBlocking`.
*   **Register ports.** A `status` port is sampled with `readNonBlocking()`, or awaited with `read()`, which wakes on each firmware write, on the first `write()` and on each later `write()` that changes the value. It can return an unchanged value. On the dst side of an `external_reg` port, `read(v)` waits for a firmware write and `update_mirror(v)` publishes the read-back value. FAIL `reg_write` used to publish from a block that loops on `read()`, because it wakes that `read()`.
*   **`status` used for control.** FAIL a `status` port, or a project interface type built on the status channel, that tells another block when to act (design kernels 3, 6 and 9 in `design-architecture.md`). `status` keeps only the latest value, so writes in one delta merge and an unchanged write raises no event. Look for:
    *   A consumer that wakes on a change through `read()` or `setExternalEvent` and then grants, blocks, starts or completes something.
    *   A toggle or sequence bit in a status struct.
    *   A write held for a minimum time, or kept sticky until the next operation, so the reader sees it.
    *   A busy, done, valid, permission or count carried as a level.
    *   A custom interface type adopted because `status` lost a value.

    The fix is a transaction (`req_ack`, `notify_ack`, `push_ack` or `rdy_vld`). `design-architecture.md`, section "`status` carries state, never control", maps each case. Exempt a value where the consumer only needs the current value, never every change, such as configuration, mode, an enable, a lock, lifecycle state or a register mirror, even when it gates a decision. That includes a thread that wakes on its change to re-sample it. Also exempt a level that only rises until reset, such as a fatal alert, whose single rise one place turns into an event.
*   **Register handler.** The generator emits the handler (`regHandler`, `_a2cRegs.addRegister/addMemory`, `SC_THREAD(regHandler)`). FAIL any hand-written thread on the register bus port. The one allowed hand-written register thread serves a local `regType: memory` register on `<reg>_channel`.
*   **Owned memories.** A memory the block owns is an `hwMemory` member. Datapath code uses `read(i)`, `write(i, v)` and the RMW calls in **systemc-core**. FAIL `operator[]` on a datapath path, because it skips timing. It is fine for backdoor uses such as logging. FAIL any shadow copy of an `hwMemory`.
*   **Memory ports.** A memory reached through a `memory` port uses `port->request(isWrite, addr, data)`.

### 3. Tandem readiness
*   **Deterministic output.** Identical stimulus gives identical output transactions. Nothing depends on random seeds, wall-clock time or other uncontrolled state.
*   **No hidden state.** All state that affects output is visible at the interfaces or derivable from input stimulus.
*   **Arbitration.** A timing-dependent choice between ports goes through `synchLock::arb()`, and each `lock()` call site passes its own value. See **systemc-synchronization**.
*   **Trackers.** `alloc` and `dealloc` are balanced and pass `getTrackerRefCountDelta()`.
*   **Model/model first** (A2C Pro). The model passes model/model tandem before RTL/model tandem. The run needs `--vlInst <path> --vlType model --vlTandem`. Without `--vlInst`, tandem does not engage.

### 4. Model-RTL conformity
*   Open `rtl/<block>.sv` beside the model.
*   **Names.** Model variables are recognizable counterparts of RTL signals. RTL signal `<name>` is `<name>` in the model.
*   **Types.** If the RTL would have to declare a type for a value, the type comes from YAML and the model uses it, such as `<name>_t`, not `uint8_t`, `uint16_t`, `uint32_t`, `int` or `unsigned`. That covers signals, registers, counters, tags, indices, addresses, factors, pixels and struct fields, including values internal to the block. A state field uses a YAML enum. The model, the RTL and the firmware headers then share one definition, which stays in sync when the YAML changes and rules out width and sign mismatches (design kernel 11 in `design-architecture.md`). Native types are fine for loop iterators, container sizes, `bool` flags, temporaries with no RTL counterpart, the `int64_t` intermediates of bit-exact arithmetic (see **rtl-to-systemc**), and arguments an a2c API declares as native, such as a `synchLock<>` value. The value stored back to a hardware-visible variable uses the YAML type. Casts between YAML types are fine. FAIL a native type on a hardware-visible value, FAIL a redefinition of a type the YAML already defines, and FAIL a value with no YAML type, asking for one.
*   Algorithm, rounding and transaction-order equivalence belong to tandem. Do not re-verify them here.

### 5. Code quality
*   **Logging.** Output goes through `log_.logPrint` with `std::format`, not `printf`, `std::cout` or `std::cerr`.
*   **Lazy logging.** Costly debug formatting on a hot path (per pixel, per transaction, inside tight loops) uses the lambda form: `log_.logPrint([&]() { return std::format(...); }, LOG_DEBUG);`. Mark direct `std::format` in rare paths, such as configuration listeners, initialization, start-of-frame handlers and error branches, `[N/A]`, not `[WARN]`.
*   **Assertions.** Internal invariants (index bounds, queue capacity, state validity) use `Q_ASSERT(condition, "message")`.
*   **Status reporting.** A missing `statusPrint(void)` is `[WARN]`, not `[FAIL]`. When present, the constructor registers it with `logging::GetInstance().registerStatus(name(), ...)`, and it dumps the queues, counters and flags that help diagnose a hang.
*   **Magic numbers.** Numeric literals in expressions, comparisons, shift amounts, array sizes and loop bounds come from a YAML constant or a `constexpr`. A value the architecture defines, such as a count, size, opcode, field position or width, comes from YAML or is derived from it. FAIL a literal or a local `constexpr` that repeats such a value (design kernel 11 in `design-architecture.md`). A `constexpr` is fine for a value internal to the block. `0`, `1` and `-1` in simple increments and decrements, and `true`/`false`, are fine.
*   **Undefined behavior.** No out-of-bounds access, use-after-free or signed overflow in intermediate calculations.

### 6. Output format
Report each category as a checklist:

```
## <Category Name>
- [PASS] <item description>
- [FAIL] <item description> -- <explanation and suggested fix>
- [WARN] <item description> -- <note or recommendation>
- [N/A]  <item description> -- <reason not applicable>
```

End with a count: `X PASS, Y FAIL, Z WARN, W N/A`.

## Constraints
*   This review covers model code: `model/**/*.cppm`, plus any plain `.cpp` or `.h` beside them. Review RTL with **review-rtl**.
*   Do not modify generated regions or `*Base.cppm` files.
*   Do not verify algorithmic equivalence with the RTL. Tandem does that.
*   Use `[WARN]`, not `[FAIL]`, for a stylistic issue.
