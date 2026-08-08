# Investigation: Status-Port Comparison Under Tandem

Status: **OPEN — design not settled. Study and prototyping required before any
implementation.** Held by the architect 2026-08-04.
**Interim release mitigation (2026-08-05):** `status_tee_2in_1out` logs a
`LOG_IMPORTANT` warning on per-notification mismatch and does **not**
`Q_ASSERT`. This is not the design resolution; it unblocks tandem runs that
hit false positives until change-based (or other) semantics land.
Category: verification-harness design. This is deliberately **not** filed in
[`bugs-116.md`](./bugs-116.md), which registers defects with known fixes; this one
needs a design decision and probably a prototype first.
Originating report: BUG 9 in `~/isp-parameterization-bug-report.md`, full write-up
in `~/bug-status-port-cycle-tandem-compare.md`.
Owner of the code under discussion: `builder/pro`
(`common/systemc/status_port_tee.h`).

## Why this is a different category

Every other item raised by the ISP parameterization work was a defect with a
determinate fix: a branch that dropped a field, a template that discarded a reset
value, a missing include directory, a stale artifact. This one is not. The tee code
does exactly what it was written to do; what is wrong is the **premise** that a
status port presents a comparable sequence of events at all. Fixing it therefore
means deciding what "model and RTL agree on a state signal" *means*, and only then
writing code.

Three properties make it resist the pattern used for the other fixes:

1. **There is no in-tree harness, at all.** `status_port_tee.h` is instantiated by
   **zero** examples in the repository. Tandem is pro-only, and the single tandem
   example (`lmmiDemo`) tees an `lmmi_if` port. No example declares
   `interfaceType: status`; status channels arise only through the `reg_ro` /
   `reg_rw` mapping (`interfaces/status/status_if.yaml:20`), and the only base
   example with any is `mixed`, whose value is written once. So there is nothing to
   reproduce against and nothing to regress against — a fixture must be built
   before a fix can be evaluated, not after.
2. **The failure is configuration-dependent and asymmetric**, arising from the
   interaction of a non-queued channel, a blocking tee loop, and an injected
   per-side delay. It is not reproducible by inspection of a single code path.
3. **Any fix trades coverage against false positives**, and the trade is a
   judgement call rather than a correctness question. That is precisely the kind of
   decision that should be prototyped and measured, not argued.

## Rejected direction, recorded so it is not revisited

An early recommendation was to demote the per-notification comparison to the
already-existing settled comparison at `status_port_tee.h:65-73`, which only logs.
**Rejected by the architect:** tandem exists to *detect* model-versus-RTL
divergence, and a warning is useless for that. Two further objections confirm the
rejection on independent grounds: the settled comparison is vacuous for a register
cleared during the test, and it cannot even assert where it currently lives,
because `logging::statusPrint()` is shared with three diagnostic dump paths
(`q_assert.cpp:36`, `watchDog.cpp:114`, `main.cpp:39`), so an assertion there would
fire during unrelated failures and turn a diagnostic into a second, misleading
failure.

## Questions to settle before implementing

1. **What is the comparison point?** The leading proposal is the settled
   change-of-state (below). The alternative anchors are transaction quiescence
   across the block's teed ports, and comparison at the point of observation (a
   firmware register read, or a downstream handshaked consumer) where a sound
   comparison already exists.
2. **How is "settled" defined in a spawned tee thread that has no clock?** Can the
   window be derived from the configured tandem `--delay`, which is the injected
   skew the window must cover, rather than hand-tuned per port?
3. **Is the accepted limitation acceptable?** A transient wrong value that
   converges would not be caught. The argument that this is correct — a status
   signal carries no valid qualifier, so an implementation may legitimately pass
   through intermediate states the other does not model — needs the architect's
   agreement, because it defines the coverage the feature claims.
4. **Does the event loss have to be fixed regardless?** The tee blocking at
   `status_port_tee.h:58` drops state changes asymmetrically. Any approach that
   keys off state changes depends on not losing them.
5. **What does the fixture look like?** Model/model with `--delay` appears
   sufficient to reproduce, which would avoid needing Verilator in the loop. That
   prediction is code-derived and unproven.

## Prototyping plan (proposed, not started)

1. Build the fixture first, and prove it reproduces the failure on today's
   unmodified tee. Until that exists, any fix is unfalsifiable. Minimum shape: a
   tandem-enabled pro leaf with one `regType: ro` register whose model writes a
   monotonically changing value on every transaction, run model/model with
   `--delay`.
2. Only then implement the chosen comparison, and require the fixture to fail
   before and pass after — the same gate applied to the BUG 10 fix.
3. Add a negative case that a genuinely divergent implementation is still caught,
   so the fix cannot be a silent relaxation. This is the case that the rejected
   log-only direction failed.

## Analysis carried forward

The material below was reviewed against the code on 2026-08-04 and is the factual
basis for the questions above.


**Verdict: CONFIRMED as a verification-harness defect. Not fixed; design not yet
settled. Owner: `builder/pro` tee.** Source:
`~/bug-status-port-cycle-tandem-compare.md`.

recorded as BUG 9 in the ISP parameterization bug report. A read-only status
register that changes more than once per test is compared per notification by
`status_tee_2in_1out` (`builder/pro/common/systemc/status_port_tee.h:39-64`)
and reports a data mismatch even though both sides settle to the same value.
A read-only investigation settled the three questions and corrected the
report's own mechanism:
- **No test harness exists.** `status_port_tee.h` has **zero in-tree
  coverage** — no example instantiates it. Tandem is pro-only, and the sole
  tandem example (`lmmiDemo`) tees only an `lmmi_if` port. No example declares
  `interfaceType: status` at all; status channels arise only through the
  `reg_ro`/`reg_rw` mapping (`interfaces/status/status_if.yaml:20`), and the
  only base example with any is `mixed`, whose value is written once and so
  would exercise the tee without reproducing the failure. A **new pro fixture**
  is required: a tandem-enabled leaf with one `regType: ro` register whose
  model writes a monotonically changing value on every transaction, run
  model/model with `--delay`. No configuration-only reproduction exists.
- **The mechanism is sample loss, not latency shift.** `status_channel::write`
  coalesces identical consecutive values (`status_channel.h:205-207`), so a
  pure shift would still pair the Nth distinct value against the Nth distinct
  value and compare equal. The real cause is that `status_channel` is a
  non-queued state channel while the tee assumes a lossless stream: after one
  side reads, it blocks in `wait(m_tee_sync)` with no process on the channel
  event, so writes in that window are discarded asymmetrically and every
  later pairing is off by one. `status` is the only teed interface whose
  channel can silently drop values; every other tee sits on a back-pressured
  transaction.
- **A `synchLock` fix in the application is not viable**, on three independent
  grounds: the verified side's notification rate is set by the clock, not the
  model (`interfaces/status/status_bfm.h:31-38` samples the wire every
  `clk.posedge_event()`), so no model-side deferral can align the counts; the
  failure reproduces model/model with identical source on both sides, because
  `--delay` is injected below the model in the primary side's channel
  (`instanceFactory.cpp:146-159`); and no sanctioned pattern exists —
  `systemc-synchronization.md` provides arbitration and mutual exclusion, not
  deferred publication.
- **The report's Option 2 is not implementable as written:**
  `portBase::setCycleTransaction` is an empty virtual
  (`common/systemc/portBase.h:24`) that `status_channel` does not override, so
  the `out->setCycleTransaction()` call at `status_port_tee.h:35` is dead and
  there is no per-cycle flag to key a relaxation on.
- **REJECTED (2026-08-04, architect): "make the existing settled comparison
  authoritative".** The settled comparison at `status_port_tee.h:65-73` only
  logs, and demoting a mismatch to a log defeats the purpose of tandem, which
  exists to *detect* model-versus-RTL divergence. It also fails on two further
  counts: it is vacuous for a register cleared during the test, and it cannot
  even assert where it lives, because `statusPrint()` is shared with three
  diagnostic dump paths (`q_assert.cpp:36`, `watchDog.cpp:114`,
  `main.cpp:39`). Any acceptable fix must produce a hard failure on real
  divergence, during the run.
- **Why no per-update compare can work at any tolerance.** Every other teed
  interface is transaction-based, and that is precisely why its tee is sound:
  `memory_port_tee.h:52-74` blocks on `reqReceive` from *both* sides before
  comparing, so the handshake guarantees exactly one comparable item per side
  per transaction. `status` has no transaction on either side. The
  SystemVerilog side is a bare always-valid wire; the SystemC side coalesces
  identical consecutive writes (`status_channel.h:203-205`) and its `read()`
  snapshots current state after a `wait` (`:187-191`), so writes are dropped
  by design; and the verified side's sample count is set by the clock, not the
  design (`status_bfm.h:31-38` samples every `clk.posedge_event()`). The two
  sides therefore never produce comparable *sequences*. This is not a skew
  problem to be tuned — there is no common event to pair on — so the fix must
  change *what* is compared, not how strictly.
- **The two sound anchors, both transactional.** (a) **Compare where the value
  is observed.** A status value matters only where something reads it, and
  every reader is transactional: firmware reads it as a `ro` register over
  APB or `external_reg`, and a downstream block consumes it through a
  handshaked port. Those interfaces are already teed and already compared at a
  handshake, so the observable consequence of a status divergence is covered —
  provided the test actually performs the read. This makes register readback a
  test-methodology requirement rather than new machinery. (b) **Compare state
  at transaction quiescence.** Status is a function of the transaction
  history, so once both sides have consumed the identical transaction sequence
  and drained, their derived state must be equal — no tolerance on the value,
  only a bounded settling allowance in time, with failure to converge inside
  that bound a hard error. This preserves repeated in-run detection.
  **Feasibility caveat:** `interfaceBase::teeBusy_` is not the ready-made
  primitive an earlier draft of this item implied. It has no getter, it is
  per-interface with no aggregate, and `interfaceBase::teeStatus()`
  (`interfaceBase.h:117-123`) consumes it only to print "has one side, waiting
  for other" in a diagnostic dump. A per-block quiescence signal across all of
  a block's teed ports, plus a drain allowance, would be new machinery.
- **CORRECTION (architect insight, 2026-08-04): the only event a status port
  has is change of state, and both sides already emit exactly that.** An
  earlier draft of this item recorded that "the verified side's notification
  rate is set by the clock, not the model". That is wrong at the level that
  matters. `status_src_bfm::bfm_driver_thread` (`status_bfm.h:31-38`) does
  write unconditionally on every `clk.posedge_event()`, but
  `status_channel::write()` discards a write whose value equals the current
  state (`status_channel.h:203-205`), so the per-clock sampling collapses and
  the channel's notification stream is a **change-of-state stream on both
  sides**. The two sides therefore do share one comparable event after all,
  which reopens per-change comparison as sound in principle. Three distinct
  causes of mismatch remain, and only the first is a defect: (i) the tee
  destroys its own stream — the channel is non-queued and the tee blocks in
  `wait(m_tee_sync)` (`status_port_tee.h:58`) with no process on the channel
  event, so changes in that window are dropped asymmetrically; (ii) one side
  may legitimately emit a finer sequence than the other, where the RTL updates
  per pixel and the model updates per word, so one stream is a refinement of
  the other rather than unequal to it; and (iii) plain skew, the same sequence
  at different times.
- **Leading proposal (supersedes (a) and (b) above; needs architect
  confirmation): compare on settled change of state, and fail hard.** Take the
  change of state as the trigger, since it is the interface's only event: on
  any change on either side, arm a comparison rather than comparing
  immediately; when both sides have been stable for a bounded settling window,
  compare and `Q_ASSERT` on inequality. This keeps detection in-run and
  repeated, keeps the failure hard, tolerates skew and refinement because only
  settled values are compared, and needs no cross-port quiescence machinery.
  The settling window should key off the configured tandem `--delay`, since
  that injected skew (`instanceFactory.cpp:146-159`) is what the window must
  cover. Prerequisite: fix the event loss at `status_port_tee.h:58`, otherwise
  the arming is itself unreliable. **Accepted limitation:** a transient wrong
  value that converges is not caught. That is the correct price — a status
  signal carries no valid qualifier, so an implementation is free to pass
  through intermediate states the other does not model; catching transients
  would require adding a qualifier to the interface contract.
- **A documentation gap exists regardless of the code fix:** nothing in
  `systemc-interfaces.md`, `rtl-interfaces.md`, `run-tandem.md`, or
  `verify-testbench.md` states what a status port's tandem compare semantics
  are, and `run-tandem.md:41` currently misdirects a model/model status
  mismatch to the synchronization skill.
This work is out of scope for `spec-tandem-parameterized-types.md`, which
excludes the tee and port-tee helpers at line 446, and it has no dedicated
plan file yet.

The old `mixed` registrar-orphan deferral is closed. The earlier C2/L2b, C5/L5,
registrar S5, cross-project clangd, composed VL, and wrapper P2 items are also
closed and must not be carried forward as open work.

