---
name: review-model
description: Rules and checklist for writing, reviewing or converting SystemC models and their testbenches, covering arch2code conventions, transactional ordering, backpressure, tests, model-RTL conformity and code quality. Use when writing or reviewing a model, or converting a timing-based model to a transactional one.
---
# Skill: Review model

## Purpose
Write or review a SystemC model block against arch2code conventions, behavioral correctness, transactional ordering, light model-RTL conformity and code quality. The review checks structure, ordering and standards. It does not prove the algorithm matches the RTL.

A model orders its behavior by messages, never by time or by a level changing. Every ordering the model depends on must be a message, or a decision the model makes the way the RTL makes it. Section 3 gives the rules.

## References
*   **systemc-core**: module layout, user slots, register and memory access, threads, logging.
*   **systemc-interfaces**: port calls for each family.
*   **systemc-synchronization**: shared events and arbitration.
*   **systemc-patterns**: multi-cycle bursts.
*   **design-architecture**: design kernels, and the section "`status` carries state, never control".
*   **rtl-registers**: what the RTL sees of `rw` and `ext` registers, and `regBusErrorResponses`.
*   **debug**: trackers, assertions, `statusPrint`.
*   **review-model-tandem** (A2C Pro): the Tandem rules that extend this skill.

## Instructions

### 1. Arch2code conventions
*   **Generated regions.** Nothing is hand-edited between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` in `model/<block>.cppm`. A block model has `moduleScaffold --section=blockModuleHeader`, `moduleExport`, `classDecl` and `constructor --section=init` / `--section=body`. In a project with an `addressBlock:` router, a block that has children and owns registers or firmware-accessible memories also has a register handler model, whose regions are `blockRegs --section=header`, `--section=init` and `--section=body`. A leaf block's own model holds its `regHandler`.
*   **User slots.** Members follow the class region's end marker. Initializers, each starting with a comma, sit between the `init` end marker and the `body` begin marker. `SC_THREAD` registrations follow the `body` end marker. Imports and headers sit in the slots **systemc-core** describes.
*   **Class shape.** The class is a `template<typename Config>` class, with `using <block>Base<Config>::...` lines, only when the block declares its own `params:`. Otherwise it is a plain class, and its out-of-class definitions are `void blk::fn()`. Either shape is correct when it matches the YAML.
*   **Base files.** `*Base.cppm` files are unmodified.

### 2. Behavioral correctness
*   **Thread loops.** Every `SC_THREAD` loop waits on an event or a port call. A loop that blocks in a port call (`read()`, `receiveAddr()`, `request()`) needs no explicit `wait()`. FAIL a loop of non-blocking calls with no `wait()`, because it spins, and a loop that waits on time to poll (section 3).
*   **Loop exits.** A counted loop exits on a value its counter's type can hold. FAIL `for (i = 0; i < N; i++)` when `i` has a YAML type and N is one past its maximum, even if the C++ typedef happens to be wide enough, because the RTL loop with the same type never ends. The fix is the test-then-increment form in **systemc-core**, section 4.
*   **Owned registers.** A register the block owns is an `hwRegister` member, read with `reg.read()`. It has no `->`, no `setExternalEvent` and no `readNonBlocking`. Section 3 says how the block handles firmware writes.
*   **Register ports.** A `status` port is sampled with `readNonBlocking()`. Its `read()` wakes on each firmware write, on the first `write()` and on each later `write()` that changes the value, and it can return an unchanged value. On the dst side of an `external_reg` port, `read(v)` waits for a firmware write and `update_mirror(v)` publishes the read-back value. FAIL `reg_write` used to publish from a block that loops on `read()`, because it wakes that `read()`. FAIL an `external_reg` owner thread that returns to `read()` without publishing the write's read-back value, that serves two `external_reg` ports, or that waits on another port, on firmware or on time between two `read()` calls. The firmware write stays open until that thread is back in `read()`.
*   **Register handler.** The generator emits the handler (`regHandler`, `_a2cRegs.addRegister/addMemory`, `SC_THREAD(regHandler)`). FAIL any hand-written thread on the register bus port. The one allowed hand-written register thread serves a local `regType: memory` register on `<reg>_channel`.
*   **Owned memories.** A memory the block owns is an `hwMemory` member. Datapath code uses `read(i)`, `write(i, v)` and the RMW calls in **systemc-core**. FAIL `operator[]` on a datapath path, because it skips timing. It is fine for backdoor uses such as logging. FAIL any shadow copy of an `hwMemory`.
*   **Memory ports.** A memory reached through a `memory` port uses `port->request(isWrite, addr, data)`.
*   **Trackers.** `alloc` and `dealloc` are balanced and pass `getTrackerRefCountDelta()`.
*   **Deterministic output.** Identical stimulus gives identical output transactions. Nothing depends on random seeds, wall-clock time or other uncontrolled state, because regressions and scoreboards compare against a fixed expectation. FAIL a model that branches on how it is run, such as on `simController::vlType` or on whether RTL runs beside it. A run then checks a model that differs from the one that runs alone. Tandem adds its own cases (**review-model-tandem** section 4, A2C Pro).

### 3. Transactional ordering
Each item gives the reason, what to FAIL and the fix.

*   **Events are messages, and the result rides in the completion.** A level keeps only its latest value, so two changes in one delta merge and an unchanged write raises no event. FAIL a `status` port, or a project interface type built on the status channel, that tells another block when to act (design kernels 3, 6 and 9). Treat every other `status` port between two blocks as a warning sign too. Check which block changes it, when, and which blocks act on it. If it is not one of the cases `design-architecture.md` keeps, report a WARN and propose messages from the block that owns the value. If it is a kept case but its YAML has no comment naming the case, report a WARN and ask for the comment. A register's port needs no comment, because it is a register mirror. Look for:
    *   A thread that wakes on a level change through `read()` or `setExternalEvent`, including one that only re-samples or caches the value.
    *   A `prev` copy, rise detect, toggle or sequence bit, or other shadow of a level.
    *   A write held for a minimum time, or kept sticky until the next operation, so the reader sees it.
    *   A busy, done, valid or count carried as a level, or a permission that a transaction grants, such as a key usable after delivery, which belongs in that transaction's ack.
    *   A requester that reads a level after its ack to learn the outcome.
    *   A custom interface type adopted because `status` lost a value.
    *   A consumer that reads a value hardware changes on its own while requests run, such as a zeroize, fault or ready state, instead of keeping its own copy from the owner's messages. Also a consumer that asks the owner for a value the owner already holds. Asking until the answer changes is polling.

    The fix is a transaction (`req_ack`, `notify_ack`, `push_ack`, `pop_ack` or `rdy_vld`) that carries the cause or payload and returns the outcome in its ack. `design-architecture.md`, section "`status` carries state, never control", maps each case.

    A value the consumer needs only as it stands, such as configuration, mode, an enable, a lock, lifecycle state or a register mirror, stays `status` even when it gates a decision. The consumer reads it with `readNonBlocking()` inside the transaction it gates. A listener thread that caches a `status` level changes its copy at a point that depends on scheduling, so it is a FAIL too. A value that hardware changes on its own while requests are running is not `status` for a consumer that decides on it. The owner sends a message per change. The consumer changes its own copy only when it takes that message (`design-architecture.md`, section "`status` carries state, never control"). A level that crosses the hardware/firmware edge, such as an interrupt line, may also stay `status`. Its owner sends each modelled consumer, the testbench included, the level's current value whenever no message is out and the value differs from the last one sent. No model reads or waits on the level (`design-architecture.md`).

    Exactly one block may wake on a level change, and it turns the change into messages for the rest of the design. The level is either one that only rises until reset, such as a fatal alert, or an unclocked pin input whose source the model does not contain, such as GPIO. A serial link such as SPI is not a pin level. `design-architecture.md`, section "`status` carries state, never control", gives the conditions.

    ```cpp
    cmdAckSt ack;
    engine->req(cmd, ack);       // ack.status says done, refused or wiped
    if (ack.status != CMD_OK) { /* handle it here, read no level */ }
    ```
*   **A status output changes at a transaction.** Model and RTL write the same status outputs, so each output must change at the same point in the order of the block's transactions. Write it on receiving a request, or on taking the ack of a request the block issued, with no wait in between, never on completing a request it received. The RTL writes it in the cycle of that handshake or the next. FAIL a status write that ends internal work whose length differs between model and RTL, such as ready set after a discovery or init sequence. End that work with a request the block issues, and write the status on its ack. A consumer that decides on such a value while requests run keeps its own copy from the owner's messages instead (`design-architecture.md`, section "`status` carries state, never control"). When a received request runs a sequence of requests the block issues, write the status on the ack of the last request issued for it, including one that ends the sequence early, then send the response. The RTL sends the response no earlier than the cycle the status is visible. In A2C Pro, **review-model-tandem** section 3 says which handshakes Tandem aligns.
*   **Avoid backpressure between blocks.** Backpressure couples the timing of two blocks, stalls paths that have nothing to do with the busy one, and makes the order of events at their interfaces depend on scheduling. Control flow between blocks queues work at one end or the other. The consumer accepts each item at once into a queue sized for the worst case. Where the consumer's queue cannot hold the worst case, the consumer returns one credit per unit consumed and the producer sends only with a credit (design kernel 5). Set-like information, where merging repeats is correct, such as error bits on their way to a register block, may instead stay pending at the producer and coalesce. At the hardware/firmware edge, send the level instead (`design-architecture.md`, section "`status` carries state, never control"). This rule is about control flow. The `backpressure:` interface key is separate. It says whether a `rdy_vld` or `axi4_stream` stream may stall, and so whether `--delay` delays it. FAIL:
    *   A consumer that withholds ready or ack while it is busy.
    *   A register or request handler that blocks on a downstream ack. Firmware can write again before the consumer acks, and the stalled bus changes the order in which the block sees its other inputs. A bridge that only forwards each bus access to the block that owns the register, has no other inputs, and returns that block's answer, is not this case.
    *   Coalesced counted or ordered events. Design kernels 3 and 5 deliver them once per occurrence.

    Coalesce with a rule simple enough that RTL and model implement it identically, such as OR into one pending word.

    Three stalls are allowed. A register bridge, as above, waits for the owner's ack, because that ack is the bus access's own response. A data stream whose protocol defines flow control, such as `rdy_vld` or `axi4_stream` into a bounded FIFO, stalls by specification. This covers data, never a command path. A requester that waits in `req_ack` for the result it needs to continue stalls only itself, as long as no other work waits behind it. A terminal command such as zeroize is the requester case, because its completion is its result.
*   **A timing-dependent choice is explicit code.** The model must make the same ordering decisions the RTL makes. Where ports or threads compete, choose the winner where the RTL arbitrates, with plain code that models its policy, such as priority or round-robin, and branch on that result. Guard shared state with a busy flag or an `sc_event`. FAIL a choice left to thread scheduling order, and a mutex added to serialize threads for convenience. In A2C Pro each such decision also gets a `synchLock` site (**review-model-tandem**, A2C Pro).
*   **Register writes run in the bus thread.** A thread woken by `registerEvent` runs after the bus access has completed, so a later access can overtake it. Act on a firmware write in the register's `setWriteErrorHandler`, which the bus thread calls for each 32-bit word, with the word's byte offset, after storing the word. On an `ro` register the handler runs but nothing is stored. A `status_out` register is written where the value changes. FAIL `registerEvent` plus a thread that applies firmware writes, a thread that copies inputs into a status register, and a refusal tested in two places.

    The register type limits what a write handler may do, because the model must match what the RTL sees (**rtl-registers**):
    *   An `rw` register reaches the RTL as a stored value, with no write strobe and no error. A handler on it only derives state from the value.
    *   A refusal, keeping the old value, or any other per-write action needs `regType: ext`, whose RTL has the write strobe and `pslverr`. Decide a refusal once and derive everything it changes, such as the bus error and the kept value, from that one result. The handler's `true` return becomes a bus error only when the project sets `regBusErrorResponses`.

    ```cpp
    // constructor body. ctrl is regType: ext.
    ctrl.setWriteErrorHandler([this](uint64_t, uint32_t) {
        bool refused = !ctrlWriteAllowed();          // the one decision
        if (refused) {
            ctrl.write(ctrlKept);
        } else {
            ctrlKept = ctrl.read();
            applyCtrl();
        }
        return refused;
    });
    ```
*   **No time in control flow.** Judge a time wait by why it is there. In a model a time wait is allowed only in the first case below. A test may also use the test-only waits listed further down. The second case is never allowed, in a model or a test.
    *   **A wait that models an architectural behavior is allowed.** Such a wait models a time the hardware or its surroundings take. It is behavior, not control flow. One example is a modelled host's response time to a DMA read at the chip edge, which makes performance numbers come out right. Others are a latency, such as how long a device takes for an operation, a timeout beside the pins, and a rate, such as the gap a source leaves between beats.
    *   **Time added to fix ordering is never allowed.** A wait added so the design works, such as one that fixes an ordering problem or makes a failing test pass, is a hack, whatever its length. FAIL it. Ask what the wait is for, and wait on that message or event instead. Then read status once.

    `wait(SC_ZERO_TIME)` is always fine. It hands control back to the scheduler, and modelling needs it. A test may also wait on time in the cases listed below. Outside a test whose subject is elapsed time, the run must still pass with each modelled latency or gap set to zero or to any value the specification allows. A fault timeout is not such a latency. It stays longer than the device's time plus any `--delay`, as below. The model has no cycle timing, so a time-based sequence passes or fails by luck and changes under `--delay`. FAIL a time wait or time stamp in a model if the order of events or a control-flow decision depends on its length. A fault timeout beside the pins is the one exception, because it never fires on a working device. In a test, FAIL one that gives something time to happen before a check or stands in for a message the design sends or should send. That covers a settle delay, a polling loop, a busy-poll of a shared variable, a time limit on one call that turns a slow completion into a failure outside a test whose subject is elapsed time, and testbench bookkeeping keyed to when something was posted, such as dropping a latched message at the moment a clear is sent. Confirm each latched message against an ordered register read and discard it if stale. Threads that share data synchronize with a busy flag or an `sc_event`, never with scheduling order.

    If the design gives a consumer, the testbench included, no message to wait on, the fix is in the design. The block that owns the event sends a message per occurrence (design kernel 3). For a level that crosses the hardware/firmware edge, such as an interrupt line, its owner sends the level's value, as in the events item above. Do not poll for it.

    A delay that a specification sets, such as a power-up hold or an operation time, is modelled once, beside the pins or in a device model. A device model holds the time an operation takes. A controller that must wait, such as for a power-up hold, asks the block beside the pins for the wait. That block sets the time, and its reply ends the wait at a transaction the model and the RTL both see. If a controller drives its own pins, move the pin timing into a block below it. A poll bound is a count of requests, never a time. Between modelled blocks the device answers a poll only when the operation ends, in the model and the RTL alike, so both issue one poll and the count bounds only retries after an error. This is the requester case in the allowed stalls: the device's ack is the poll's result, and the controller queues other work rather than holding it behind the poll. A poll the physical device needs at a time interval sits below that interface, beside the pins, as for a serial link (`design-architecture.md`, section "`status` carries state, never control"). A timeout that only catches a fault sits beside the pins too, and its reply says timed out. It exceeds the device's specified time plus any `--delay`, so it never fires on a working device, and a test that makes it fire is an elapsed-time test. The delay ends in a response that carries the outcome, such as done or timed out, and blocks above it see the response, never the time. Do not just delete such a delay, because the model would then accept work the RTL refuses.

    Hand-written waits are allowed only in the places below. The list does not cover the delays the framework inserts, such as `hwMemory` access time and `--delay`. All other timing behavior belongs in all-RTL simulation.

    These model hardware time. They may sit in a model or a test:
    *   A specified delay or response time, such as a modelled host's DMA read response, or a timeout that only catches a fault, beside the pins or in a device or host model, as above.
    *   Stimulus pacing in a source, such as gaps between beats of a valid-only stream.

    These belong to tests and never sit in a model:
    *   One watchdog that bounds the whole run and fails it if it hangs.
    *   A start wait that only keeps a converted test's log time stamps (**verify-testbench**).
    *   A test whose subject is elapsed time, such as a timeout, stuck-work or throughput test. It says so, and stays out of runs that compare model and RTL, such as Tandem (A2C Pro).
    *   A wait that sets up a case. A test may space or hold its own stimulus and responses so the design reaches the state the case needs, such as competing requests all pending at an arbiter at once. It never waits for the design to finish something, because that is a message. A comment says what the wait sets up. The setup works at every modelled latency the specification allows, from zero up, and under `--delay`. A hold outlasts any `--delay`, as a fault timeout does. The test still waits on a message for the result it checks.

    A model or test never waits for reset release. The model has no reset (**systemc-core**). FAIL a time wait added to get past reset. A BFM (**verify-cosimulation**) that drops or drives a transaction before its reset releases is a framework defect. Report it. Do not work around it in the model. A test that must wait for such a BFM until it is fixed names the BFM in a comment.
*   **Accept work exactly when the RTL does.** A model that accepts earlier or later than the RTL orders its work differently, and nothing in a model-only run reports it. If the RTL stops accepting while a command is pending, the model stops too, drains in-flight and queued work, then acts. This includes internal work such as a clock change or a calibration. Model it as a request the block issues to the block that performs it, and write any status on that ack. Where the RTL queues new work from issue until that ack, the model queues it too. Where the RTL refuses, the model refuses. Prefer queueing to refusing in the design, because a refusal window makes the outcome depend on arrival time. Change state and hand over a phase only on an accepted handshake, valid and ready together. FAIL a model that takes at once a command the RTL takes only when idle, and a sub-block handed a command or phase on valid alone. Whether the RTL should stall at all is the backpressure item.
*   **State that spans a wait stays in one ordering window.** Any blocking call lets another transaction, such as a wipe, land between the two halves. FAIL a lookup then a store, or a read-modify-write, with a port call or `wait` between them and nothing held. Hold a busy flag across both halves, or move the wait outside them.
*   **Workarounds are debt.** Polling, an extra lock or an ack-hold flop added to make a failing run pass hides a level or a decision the model does not make explicitly, and the failure comes back. FAIL a change whose only reason is that the run passes now. Find the level or the decision behind it and fix that.

### 4. Tests
*   **Tests can fail.** A check that cannot fail hides the bug it was written for. A missing completion is a failure, not a log line. After an ordering read, check that nothing stray arrived on another channel. FAIL a race whose beats were all refused before it began, a "refused" check that an earlier layer would refuse anyway, and an absence check after a time wait, outside a test whose subject is elapsed time. Prove each new check with a negative control. Break the design, watch the test fail, then restore it.
*   **Arbiter tests check the policy.** A test of an arbiter makes the competing requests pending together, with a time wait where no message shows they are, then checks the exact order the policy gives. A test that only issues the requests together and accepts every order passes an arbiter that starves one requester, so it does not check the policy. Prove the check with a negative control, such as fixed priority in place of round robin. Tandem (A2C Pro) does not compare the two picks. The model replays the RTL's pick and drops its own. A run of the model alone checks the model's policy, and a run with the RTL substituted checks the RTL's (**run-tandem**).

### 5. Model-RTL conformity
*   Open `rtl/<block>.sv` beside the model.
*   **Names.** Model variables are recognizable counterparts of RTL signals. RTL signal `<name>` is `<name>` in the model.
*   **Types.** If the RTL would have to declare a type for a value, the type comes from YAML and the model uses it, such as `<name>_t`, not `uint8_t`, `uint16_t`, `uint32_t`, `int` or `unsigned`. That covers signals, registers, counters, tags, indices, addresses, factors, pixels and struct fields, including values internal to the block. A state field uses a YAML enum. The model, the RTL and the firmware headers then share one definition, which stays in sync when the YAML changes and rules out width and sign mismatches (design kernel 11 in `design-architecture.md`). Native types are fine for loop iterators, container sizes, `bool` flags, temporaries with no RTL counterpart, the `int64_t` intermediates of bit-exact arithmetic (see **rtl-to-systemc**), and arguments an a2c API declares as native. The value stored back to a hardware-visible variable uses the YAML type. Casts between YAML types are fine. FAIL a native type on a hardware-visible value, FAIL a redefinition of a type the YAML already defines, and FAIL a value with no YAML type, asking for one.
*   Algorithm and rounding equivalence belong to simulation against the RTL (**verify-cosimulation**). Do not re-verify them here.

### 6. Code quality
*   **Logging.** Output goes through `log_.logPrint` with `std::format`, not `printf`, `std::cout` or `std::cerr`.
*   **Lazy logging.** Costly debug formatting on a hot path (per pixel, per transaction, inside tight loops) uses the lambda form: `log_.logPrint([&]() { return std::format(...); }, LOG_DEBUG);`. Mark direct `std::format` in rare paths, such as write handlers, initialization, start-of-frame handlers and error branches, `[N/A]`, not `[WARN]`.
*   **Assertions.** Internal invariants (index bounds, queue capacity, state validity) use `Q_ASSERT(condition, "message")`.
*   **Status reporting.** A missing `statusPrint(void)` is `[WARN]`, not `[FAIL]`. When present, the constructor registers it with `logging::GetInstance().registerStatus(name(), ...)`, and it dumps the queues, counters and flags that help diagnose a hang.
*   **Magic numbers.** Numeric literals in expressions, comparisons, shift amounts, array sizes and loop bounds come from a YAML constant or a `constexpr`. A value the architecture defines, such as a count, size, opcode, field position or width, comes from YAML or is derived from it. FAIL a literal or a local `constexpr` that repeats such a value (design kernel 11 in `design-architecture.md`). A `constexpr` is fine for a value internal to the block. `0`, `1` and `-1` in simple increments and decrements, and `true`/`false`, are fine.
*   **Undefined behavior.** No out-of-bounds access, use-after-free or signed overflow in intermediate calculations.

### 7. Output format
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
*   Sections 2 to 5 are also the rules for writing a model.
*   A review covers model code, `model/**/*.cppm` plus any plain `.cpp` or `.h` beside them, and the testbench for the items in sections 3 and 4 that name tests. Review RTL with **review-rtl**.
*   Do not modify generated regions or `*Base.cppm` files.
*   Do not verify algorithmic equivalence with the RTL. Simulation against the RTL does that.
*   Use `[WARN]`, not `[FAIL]`, for a stylistic issue.
