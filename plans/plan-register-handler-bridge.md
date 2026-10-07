# Plan: register handler bridge (R20)

- **Status:** DONE (2026-09-21). Landed: `common/systemVerilog/memory_reg_bridge.sv`;
  the V19 checks and handler clock/reset rows in `clockTree.py`; the bridged
  emission with `pslverr` in `moduleRegs.py`; the `examples/twoClk`
  cpu/decode/table trio; and the skill and plan updates.
- **Specification:** [`spec-clock-reset-requirements.md`](./spec-clock-reset-requirements.md),
  R19, R20, R25, V19, V24, §4.3 "Memories", §4.4 selected reset, §4.9.
  Where this plan and the specification disagree, the specification is
  right and this plan is stale.
- **Parent plan:** [`plan-clock-container-model.md`](./plan-clock-container-model.md)
  §7 item 6. Phases 1 to 5 and 7 of that plan are in the tree; this plan is
  its phase 6.
- **Source:** issue #129.
- **Baseline:** `feature/129-clock-followup` at ab9c341. Today a `regAccess`
  memory declared on a clock other than its block's register bus clock is
  rejected at build (V24, `pysrc/clockTree.py`, `unittest/test_clock_domains.py`).

---

## 1. What changes, in one page

A routed leaf's generated `<block>_regs` handler runs on the register bus
clock (R25). Its `regAccess` memories run on whatever block clock their
declaration names (R19). Today those two clocks must be the same clock, and
the handler drives the memory port from bus-domain flops and captures read
data one bus cycle after the enable.

After this plan, a memory whose clock differs from the bus clock is served
through a handshake bridge. The bus side of the bridge is in the handler's
bus domain; the memory side is clocked by the memory's `clock:` and reset by
its `reset:` (the selected reset of that clock when unstated). One access is
outstanding per memory at a time. The bus is stalled until the response is
back in the bus domain. A memory-side reset during or before an access
completes the access with `pslverr`, and the memory is never touched by a
request the bus has already failed. Every generated router forwards
`pslverr` to the bus master; the router template already does this one
level, and the plan verifies the chain rather than rewriting it.

A memory on the bus clock keeps today's emission unchanged, byte for byte.
The bridge is emitted only where the domains differ, so no existing example
changes output.

The handler gains one clock port and one reset port per memory domain it
bridges, named by the leaf's own clock and reset names, so the leaf's
generated instantiation binds them by name exactly as it binds the bus pair.

Nothing changes on the SystemC side. The model carries no clocks (R26,
§4.11), `hwMemory` is untimed, and the handler model template is untouched.

Schema: no change. `memories[].clock` and `memories[].reset` already exist
(`config/schema.yaml`, "The owning block's clock this memory is on").

---

## 2. Decisions for the user

Each option carries a recommendation. Nothing below is implemented until the
user has chosen.

### D1. Where the bridge logic lives

**Option A (recommended): a shared parameterised module under
`common/systemVerilog/`**, next to `memory_sp.sv`, instantiated once per
bridged memory by `moduleRegs.py`. Shape:

```systemverilog
module memory_reg_bridge #(parameter type data_t = logic, parameter type addr_t = logic) (
    input  bus_clk,  input bus_rst_n,
    input  mem_clk,  input mem_rst_n,
    // bus domain: one request at a time, held until done
    input  req, input wr, input addr_t addr, input data_t wdata,
    output done, output err, output data_t rdata,
    // memory domain
    memory_if.src mem_port
);
```

The handler keeps decode, per-segment write accumulation, the bus stall,
the read slice and the `pslverr` merge, all in the bus domain as today. The
module carries the two FSMs, the synchronisers and the held read data.

Why: the protocol in §4 is about forty lines of state machine plus
synchronisers, and it has reset corner cases that deserve to be read and
linted as one unit rather than reassembled from template fragments per
memory. A shared module lints once under all three reset styles (§4.9) and
gets a unit test of its own. `common/systemVerilog/a2c.f` already picks up
every `.sv` in that directory (`-y .` with `+libext+.sv`), so no file list
changes. Variant-width memories work through the `type` parameters, the same
way `memory_if` and `memory_sp` already take them.

Cost: one more file the downstream fork carries (memory: the fork replaces
`flops.sv`; a new file is an addition there, not a conflict).

**Option B: inline in the generated handler.** Everything in
`moduleRegs.py`, one copy of the FSMs per bridged memory in the emitted
module. No new shared file, but the template grows by the whole protocol,
the per-memory signal naming multiplies, and the reset corner cases are
proved only through generated fixtures rather than once on the module.

### D2. Where the memory read latency comes from

**Option A (recommended): fixed at one cycle.** Every shipped primitive
(`memory_sp`, `memory_dp`, and their `_ext` forms) registers `read_data`
once, so a read is valid one memory cycle after `enable`. The handler
already hard-codes that (`rd_enable` then `rd_capture`). The bridge's memory
side waits one cycle after the access before capturing.

**Option B: a per-memory `readLatency:` attribute.** A schema addition
(data contract sign-off, `config/SCHEMA_SPECIFICATION.md`), a view field,
and a parameter on the bridge. No primitive in the tree needs any value but
one, and a designer swapping in a different memory macro today already has
to match the one-cycle contract for the same-domain handler. I would not add
a knob with no consumer; if a second latency ever arrives, it should land on
both handler paths at once.

### D3. Which fixture proves it

**Option A (recommended): extend `examples/twoClk`.** It already declares
`clk` and `clkSlow` with a reset each, runs the model, the whole-DUT
verilated build and per-leaf verilated runs, and lints under both
non-default reset styles (`Makefile` target `two-clk`). It is also the
fixture every phase of the parent plan gated on. Additions, all on the
assembler side so the composition purpose of the fixture is untouched:

- a register bus: constants, address and data structures, an `apb`
  interface `twoClkReg`;
- `twoClkCpu`, model only (as `apbDecode`'s `cpu`), driving writes and
  reads of the table and comparing, the same traffic shape as
  `examples/apbDecode/model/cpu.cppm`;
- `twoClkDecode`, a router (`addressBlock:`) on `clk`;
- `twoClkTable`, a top-down leaf declaring `clk` (default) and `clkSlow`
  with their resets, owning `tbl` with `regAccess: true`,
  `clock: clkSlow`, `memoryType: singlePort` (the handler takes the only
  port, R20). Its model holds an `hwMemory` registered through
  `addMemory`, as `examples/apbDecode/model/blockA.cppm` does;
- instances in `twoClk` with explicit maps; the `twoClkReg` connection
  `uCpu -> uDecode` needs no `connectionMap` since both sit in `twoClk`;
- `rundir/Makefile`: a `run-vl-table` leaf run added to `run-vl`.

The whole-DUT verilated run is the proof: the model cpu drives APB through
the BFM into RTL router, handler, bridge and memory, and the read-back
compare fails if any word is lost or duplicated.

**Option B: a new example.** Cleaner separation of purpose, but a whole
project skeleton, a new `Makefile` target, a `pipeline-test` entry, and one
more serialised build in every sweep, for a fixture that would need the same
two clocks `twoClk` already has.

**Not recommended: extend `examples/apbDecode`.** It has the cpu traffic and
the memories already, but it is the canonical single-router teaching example
(skill `design-register-decode` §6, `apbDecode.adoc`), and its `Makefile`
target does not run the verilated build.

---

## 3. Design points resolved on recommendation

These change internal shape or generated RTL. They are listed so the user
can object; they are not questions.

1. **The handler's clock ports carry the leaf's names in the clock tree
   model, not only at emission.** Today the synthesised handler keeps the
   implicit `clk`/`rst_n` pair inside `clockTree.BlockDomains` and
   `intf_gen_utils.bus_clock_reset_port_data` renames it to the bus clock
   when the port list is emitted. That cannot host a second domain. A leaf
   with `clk` (default) and `clkPix`, its bus on `clkPix` (spec §8.4) and a
   memory on `clk`, would give the handler an implicit `clk` emitted as
   `clkPix` and a bridged port also named `clk`. So
   `_resolveRegisterHandlerBinds` renames the handler's pair to
   `leafDomain.registerClock`/`registerReset` when it resolves them, and
   appends one `ClockDecl`/`ResetDecl` per bridged memory domain under the
   leaf's names, in the leaf's declaration order. `busClockPort`/
   `busResetPort` then equal `registerClock`/`registerReset` for a handler
   and `bus_clock_reset_port_data` becomes an identity there (it stays as
   is for routers). The existing rows persist the extra entries; the leaf's
   generated instantiation binds them through the same
   `instanceClockResetBinds` rows as the bus pair. The existing emission
   check `check_regs_handler_non_default_domain` (`input clkSlow, input
   rstBus_n`) stays green and pins that the rename is invisible where there
   is no bridge.
2. **V24 is replaced by a V19 check.** A `regAccess` memory whose clock
   differs from the bus clock and whose clock has no selected reset is
   rejected with a V19 diagnostic naming the memory, the clock, and the fix
   (declare a reset on that clock or name `reset:`). The V24 diagnostic and
   its test go.
3. **Same-domain emission is unchanged.** The bridge path is taken only
   when the memory's resolved clock differs from `registerClock`. The gate is
   `git diff --stat examples/` empty after the full sweep.
4. **The handler generates `pslverr` only from the bridge.** Unmapped reads
   still return zero with no error, unmapped writes are still acknowledged,
   exactly as the template comment states today. Only a bridged access
   that the memory side failed raises `pslverr`, in the same cycle as
   `pready`.
5. **Writes to a bridged memory stall too.** Today a write completes in the
   cycle it is decoded. A write to a bridged memory holds `pready` low until
   the memory side has acknowledged (R20: "the bus stalls the access until
   the response is in the bus domain"). Same-domain writes are unchanged.
6. **The read data hold register on the memory side is not reset.** It is
   written before the acknowledge is raised and held until the request
   drops, so a memory-side reset between the acknowledge and the bus
   sampling it cannot zero data the bus is about to accept as valid. The
   error flag travelling with it is likewise unreset. Both are plain
   `always_ff` without reset, or `DFFNR_DOM`, not a synthesis attribute.
7. **Router and passthrough are verified, not changed.**
   `apbDecodeModule.py` registers `pready`, `prdata` and `pslverr` from the
   selected child together, so alignment holds through any nesting depth.
   A passthrough container carries the whole `apb_if` through its boundary
   map, so `pslverr` rides along. Both get emission checks (§6.2); neither
   template is edited unless a check fails.
8. **Synchroniser flops carry keep attributes, not synthesis constraints.**
   The keep attributes sit on every stage declared with the macro, ten
   crossing flops in all (`req_sync_meta`/`req_sync_stable`,
   `alive_sync_meta`/`alive_sync_stable`, `ack_sync_meta`/`ack_sync_stable`,
   `bus_alive_sync_meta`/`bus_alive_sync_mid1`/`bus_alive_sync_mid2`/
   `bus_alive_sync_stable`) use `DFF_KEEP_INST_DOM` or `DFFR_KEEP_INST_DOM`,
   which stops synthesis merging or sharing a stage with an apparently
   equivalent register; `bus_alive` itself stays on the plain `_DOM` macro.
   `ASYNC_REG` or an equivalent vendor placement attribute is still the
   flow's, since `flops.sv` carries none, and so is a
   shift-register-mapping attribute on this chain (§8).

---

## 4. The bridge protocol

Four-phase level handshake, one request outstanding per memory. Signals in
the bus domain: `req`, `wr`, `addr`, `wdata` (held stable from `req` rising
until it falls), `done`, `err`, `rdata`, `bus_alive`, `req_taken`. Signals in
the memory domain: `ack`, `err_hold`, `rdata_hold`, `alive`. Four crossings
link the domains: `req_latch` crosses into the memory domain as `req_sync`
(two stages, reset 0), `bus_alive` crosses into the memory domain as
`bus_alive_sync` (four stages, reset 0), and `alive` and `ack` cross into the
bus domain as `alive_sync` and `ack_sync` (two stages each, reset 1). Every
crossing stage is built with `DFF_KEEP_INST_DOM` or `DFFR_KEEP_INST_DOM`
(`common/systemVerilog/flops.sv`), which adds `syn_keep` and `syn_preserve` to
the pair's registered flop so synthesis cannot merge or share a stage with an
apparently equivalent register. Neither attribute stops
synthesis inferring a shift register out of the four-stage `bus_alive_sync`
chain; a `syn_srlstyle`-equivalent attribute for that is an open
recommendation, not yet applied (§8). Under `A2C_CDC_JITTER`, each crossing
also gets a `<x>_release_credit` flop (§4.2.1) that lets its first transition
after a reset hold twice instead of once.

### 4.1 Memory side (memory clock, memory reset)

- `alive`: reset to 0, sets on the first `MEM_IDLE` entry after a reset and
  holds until the memory FSM is forced back to `MEM_ARM`. Its synchronised
  copy tells the bus side whether the memory domain is live and has not been
  forced back to `MEM_ARM` by a bus reset it has not yet answered.
- `req_sync_meta` and `req_sync_stable` reset to 0. `MEM_ARM` has to act on a
  held request either way, sending it to `MEM_ACKED` with `err_hold` set or
  an absent one to `MEM_IDLE`, so no reset value on this chain can make both
  answers safe; structure protects it instead. `bus_alive_sync` carries four
  stages against `req_sync`'s two, so whenever `bus_alive_sync_stable` first
  reads a real 1 after a memory reset, `req_sync_stable` has already had two
  full edges beyond its own two-stage reset window to become a real sample,
  not one. The extra edges are what let the module tolerate one late-resolving
  synchroniser stage and a one-edge difference in when the bus-side and
  memory-side resets deassert, at the same time, rather than either
  condition alone. `A2C_CDC_JITTER`'s release-credit mechanism (§4.2.1)
  models exactly that combination on a crossing's first transition after
  reset; outside that first transition, the protocol still only assumes one
  cycle of ordinary synchroniser skew between any two crossings.
- `bus_alive_sync_stable` falling forces the next state to `MEM_ARM` from any
  state, ahead of that state's own transition, and clears `alive` and `ack`
  with it. This is how a bus reset tells the memory side to stop trusting the
  request it is holding.
- States: `MEM_ARM` (reset state), `MEM_IDLE`, `MEM_ACCESS`, `MEM_WAIT_RD`,
  `MEM_ACKED`.
  - `MEM_ARM`: wait for `bus_alive_sync_stable` high, then check
    `req_sync_stable`. If it is low, go to `MEM_IDLE`. If it is high, that is
    a request the bus raised before this side was reset, or one it abandoned
    during a bus reset; raise `ack` with `err_hold` set and do not touch the
    memory, then wait in `MEM_ACKED` for `req_sync_stable` to fall, then
    `MEM_IDLE`. This is what makes a reset mid-access end in `pslverr` on the
    bus and never in a duplicated write (R20), and it needs no minimum reset
    pulse width.
  - `MEM_IDLE`: on `req_sync_stable` high, drive `mem_port.enable`, `wr_en`,
    `addr`, `write_data` for one cycle; go to `MEM_WAIT_RD` for a read (one
    cycle, D2) or straight to `MEM_ACKED` for a write.
  - `MEM_WAIT_RD`: capture `mem_port.read_data` into `rdata_hold`, clear
    `err_hold`, go to `MEM_ACKED`.
  - `MEM_ACKED`: `ack` high until `req_sync_stable` falls, then `MEM_IDLE`.

### 4.2 Bus side (bus clock, bus reset)

- `alive_sync_meta`/`alive_sync_stable` and `ack_sync_meta`/`ack_sync_stable`
  reset to 1. `BUS_ARM` and `BUS_IDLE` only ever wait for a real 0 from these
  chains, so a reset value can only lengthen that wait; it is never read as
  permission to proceed. `BUS_WAIT_ACK` and `BUS_DRAIN` wait for
  `ack_sync_stable` high, but its reset value cannot reach either state.
  `BUS_ARM` consumes it first, since a request cannot reach `BUS_WAIT_ACK` or
  `BUS_DRAIN` without first passing through a real `alive_sync_stable` low in
  `BUS_ARM`, by which point `ack_sync_stable` has had the same margin to
  settle. Under jitter, though, `BUS_ARM` is not the only state that can see
  that reset value. `ack_sync`'s 1 can last up to four bus edges and
  `BUS_ARM` exits after three, so `BUS_CONNECT` can be the active state
  while it lasts. That is safe because `BUS_CONNECT` does not read
  `ack_sync`, and every later state is reached only after `BUS_ARM` has seen
  a real 0 on `alive_sync`. Neither chain needs a flush chain of its own.
- `req_taken` records whether the current level of `req` has been acted on,
  so a caller that leaves `req` high past `done` is not read as a second
  access.
- `BUS_ARM` (reset state): wait for `alive_sync_stable` low, proof nothing
  this bus incarnation starts can be mistaken for a request from before the
  reset. Then raise `bus_alive`, go to `BUS_CONNECT`. A request arriving here
  completes at once with `pslverr`, `bus_alive` stays 0, `req_latch` is never
  raised.
- `BUS_CONNECT`: wait for `alive_sync_stable` to rise again. That rise is not
  proof the memory side has left `MEM_ARM` for good. `alive` can pulse for
  two memory cycles and fall again, from either of two sources, both the
  stage-count difference between `bus_alive_sync` (four stages) and
  `req_sync` (two). First, `MEM_ACKED`, answering a request pending from
  before the reset, drains into `MEM_IDLE` on an edge where
  `bus_alive_sync_stable` still reads its old value of 1 (§4.1). Second,
  `MEM_ARM` exits to `MEM_IDLE` on a stale `bus_alive_sync_stable` of 1 while
  `req_sync_stable` already reads 0, the memory just out of its own reset
  with the bus already in `BUS_ARM`; same width, same harmless outcome.
  `BUS_CONNECT` may therefore exit on such a pulse rather than on the memory
  side's real reconnection; this is harmless, since `req_latch` fell at the
  reset and an access accepted inside such a pulse is abandoned into
  `BUS_DRAIN` once `alive_sync_stable` falls again, answered with `pslverr`
  there. A request arriving in `BUS_CONNECT` itself completes at once with
  `pslverr`, same as `BUS_ARM`.
- `BUS_IDLE`: on a decoded access to a bridged memory word, with
  `ack_sync_stable` low. If `alive_sync_stable` is 0, complete at once with
  `pready` and `pslverr`, never raise `req_latch` (R20: a request while the
  memory side is held in reset completes with the error without touching the
  memory). Else latch `wr`, `addr`, `wdata`, raise `req_latch`, go to
  `BUS_WAIT_ACK`. Hold `pready` low. The `ack_sync_stable` term here is an
  interlock, not a margin requirement. `alive_sync_stable` and `req_taken`
  already gate what `BUS_IDLE` will accept, but the term keeps "no access
  starts against a raised ack" a property of one line instead of an
  inference from the rest of the FSM. Under the two-hold jitter model it
  also closes a one-edge window. Take a bus reset that lands while the
  memory sits in `MEM_ACKED` reached from `MEM_ARM` (`alive` 0, `ack` 1).
  The memory sees `req_latch` fall and moves to `MEM_IDLE`, so `alive`
  rises and `ack` falls on the same edge. The `alive` rise crosses unheld.
  The `ack` fall is `ack_sync`'s first transition after the bus reset, so it
  can be held twice. Without the term, `BUS_IDLE` would accept a request on
  the edge `ack_sync_stable` falls, and `BUS_WAIT_ACK` would read `ack` low
  for one more edge before the real completion.
- `BUS_WAIT_ACK`: if `alive_sync_stable` falls (a memory-side reset),
  complete at once with `pslverr`, but keep `req_latch` raised and go to
  `BUS_DRAIN`; the memory side still owes that request an answer. Usually
  that answer is `MEM_ARM`'s err. But a request raised on a stale `alive`
  reading can reach the memory only after `MEM_ARM` has already moved on to
  `MEM_IDLE`, and then the memory performs the access for real. `BUS_DRAIN`
  waits for that answer before dropping `req_latch`, so a late ack is never
  taken for the next access. An access reported with err after a memory
  reset may therefore have executed. The caller must retry on err, which is
  why a register table write has to be idempotent. If
  `ack_sync_stable` rises, take `rdata_hold` and `err_hold`, complete with
  `pready` and `pslverr = err`, drop `req_latch`, go to `BUS_WAIT_ACK_LOW`.
- `BUS_WAIT_ACK_LOW`: when `ack_sync_stable` is 0, go to `BUS_IDLE`.
- `BUS_DRAIN`: the only recovery state; every reset a request can land in
  mid-access drains through here before `BUS_IDLE` accepts another one. When
  `ack_sync_stable` rises, drop `req_latch`, go to `BUS_WAIT_ACK_LOW`. A new
  request arriving here completes at once with `pslverr` only while
  `alive_sync_stable` is still 0, same rule as `BUS_IDLE`; while
  `alive_sync_stable` is 1 it simply waits, since `BUS_IDLE` will pick it up
  once `BUS_WAIT_ACK_LOW` drains.
- Bus-side reset drops `req_latch` and `bus_alive` at once, since the reset
  state is `BUS_ARM` and neither register carries a reset value other than
  0. The memory side sees `bus_alive_sync_stable` fall and is forced to
  `MEM_ARM` from whatever state it was in, ahead of that state's own
  transition. A write already presented to the memory that same cycle still
  executes under this internal force, since it is a synchronous next-state
  decision and the memory port reads only the current state, not the forced
  next one, whatever the reset style. That guarantee does not extend to
  `mem_rst_n` itself arriving asynchronously mid-cycle under
  `A2C_RESET_ASYNC`: an async reset can clear `mem_state`, and with it
  `mem_port.enable`, before a write in progress finishes, the same as it
  would next to any memory.
- A request whose memory clock is not running stalls the bus.
  `alive_sync_stable` stays whatever it last was, and if it is 1 the bus
  waits for an acknowledge that never comes. The specification places this
  on firmware (R20: no timeout is specified).
- Two requirements on the environment follow from the margin above. Each
  domain's reset must deassert synchronously to that domain's clock, within
  the one-edge tolerance §4.1 states. The memory clock must run, or the
  memory domain must be held in reset, whenever the bus domain is out of
  reset, since a stopped memory clock leaves the caller waiting for `done`
  with no timeout in this module (previous bullet).

### 4.2.1 Checkers and the jitter model

- The following invariants are also checked at run time, in two
  `` `ifndef SYNTHESIS `` blocks, one per domain, each an `always_ff` gated on
  its own domain's reset so a flop's post-reset default cannot trip a check
  before the design has had a chance to run. Most of these assertions restate
  the `always_comb` that drives the signal they check, so they catch a later
  edit or a synthesis mismatch rather than proving the protocol itself; the
  protocol check is the testbench monitor (§6.2). The bus-domain block checks
  that a non-error completion only ever follows `BUS_WAIT_ACK` with
  `ack_sync_stable` high, that a new access never starts while `req_latch` is
  still set, that `bus_alive` is 0 only in `BUS_ARM`, and that `req_latch` is
  never high outside `BUS_WAIT_ACK`/`BUS_DRAIN`. The memory-domain block
  checks that `mem_port.enable` only asserts in `MEM_ACCESS`, that
  `MEM_ACCESS` is only entered from `MEM_IDLE`, that `ack` only asserts in
  `MEM_ACKED`, that `ack` never rises on the same edge `alive` falls, that
  `ack` falling and `alive` rising together only happens on `MEM_ACKED`
  exiting to the first `MEM_IDLE` after a reset, and that `alive` is never
  set in `MEM_ARM`. The two `ack`/`alive` edge properties are why
  `alive_sync` and `ack_sync` need no stage margin, unlike `req_sync`
  (§4.1). Both chains are pure waits on the bus side. `BUS_WAIT_ACK_LOW`
  reads only `ack_sync_stable`, and `BUS_IDLE` answers with err until
  `alive_sync_stable` reads high, so either arrival order of the pair ends
  in a wait or an err, whatever the stage count. None of these blocks
  synthesise. Both read `bus_rst_n`/`mem_rst_n` as data on purpose, which
  `-Wall` reports as
  `SYNCASYNCNET` once `A2C_RESET_ASYNC` puts the same net on an async
  sensitivity list elsewhere in the module; both blocks are bracketed in
  `/* verilator lint_off SYNCASYNCNET */`/`lint_on`.
- `A2C_CDC_JITTER` is a compile-time define that models a synchroniser stage
  resolving one cycle late, so the default build, which never defines it, is
  unaffected. Under the define, each crossing's first stage gains a
  testbench-driven `jit_*` control and an in-module `_seen` flop that samples
  the crossing's source every receiving cycle, except that it freezes instead
  while a hold is spending the release credit below. The first stage holds its
  current value for one cycle, instead of taking the source's new value,
  only on the edge where the source has just changed from what `_seen` last
  saw; reset release counts as a change, since `_seen` resets to the same
  value as the stage it feeds. One hold per transition is the model for
  every transition but one. A stage may resolve a cycle late, but it cannot
  stall for several cycles against a source that has stopped moving, since
  that models nothing physical and would defeat any finite margin. Each
  crossing also gets a `<x>_release_credit` flop, reset 1 and spent the
  first time a hold fires after a reset; with the credit still set, `_seen`
  freezes instead of catching up to the source, so the very next edge can
  hold again too, modelling reset-removal skew and an ordinary
  late-resolving stage landing on the same transition together. Once spent,
  a crossing gets only its ordinary single-cycle hold, on this or any later
  transition, until the next reset restores the credit. The testbench drives
  all four `jit_*` controls from a random process of its own; the design has
  to tolerate any pattern of such holds, one per transition and up to two on
  a crossing's first transition after reset, across the four crossings.

### 4.3 Cost

B is a bus cycle, M a memory cycle. Each step is a crossing's stage count
plus one FSM reaction edge, the same reasoning behind the module header's
connect-cost figure, measured from a reset release at 6 bus edges plus 5
memory edges. From the decode cycle:

| Step | Delay |
| :--- | :--- |
| `req` raised, seen by the memory side | 1 B + 2 M |
| memory access, plus read wait | 1 M, plus 1 M for a read |
| `ack` seen by the bus side, access completes | 2 B |
| `req` dropped, seen by the memory side | 2 M |
| `ack` dropped, seen by the bus side, next access may start | 2 B |

An access holds the bus roughly 3 B + 4 M; the next one can start about
2 B + 2 M later. The APB master BFM (`interfaces/apb/apb_bfm.h`) already
loops on `pready`, and the generated router holds `trans_active` until the
child's `pready`, so no consumer changes.

---

## 5. Changes by owner

### 5.1 `common/systemVerilog/` (D1 option A)

- New `memory_reg_bridge.sv` as sketched in §2 D1, flops through
  `DFF_DOM`/`DFFR_DOM`/`DFFNR_DOM` so it follows the selected reset style
  (`flops.sv`). Header comment states the protocol of §4 and the two
  unreset registers (`rdata_hold`/`err_hold` on the memory side,
  `latched_wr`/`latched_addr`/`latched_wdata` on the bus side) with their
  reason.
- No change to `a2c.f`.

### 5.2 `projectCreate`: `pysrc/clockTree.py`

- `_resolveRegisterHandlerBinds`: after `resolveBlock(leafBlockKey)`,
  rename the handler's implicit pair to the leaf's `registerClock`/
  `registerReset` (keys of `handlerDomain.clocks`/`resets`, the
  `selectedReset` map, `busClockPort`/`busResetPort`), rebind the two
  consumers under the new port names, then for each `regAccess` memory of
  the leaf whose `clock` differs from `registerClock`, append a clock and a
  reset entry under the memory's clock and reset names and add a consumer
  bind for each on the leaf container's nets (binding kind `'register'`, or
  a new `'memory'` kind if a diagnostic ever needs to tell them apart; the
  plan takes `'register'` unless one does).
- Replace the V24 block with the V19 check of §3 item 2. The `MemoryDomain`
  docstring loses its "not implemented yet" sentence.
- `rows()` needs no change. The handler's extra entries persist through the
  existing `blockClocksResets` and `instanceClockResetBinds` rows.

### 5.3 `projectOpen` views: `pysrc/processYaml.py`

- A handler-only view helper (name to the implementer, sited with
  `getBDBusClockReset`) that stamps each entry of `ret['memoriesParent']`
  with `clock`, `reset` (the handler's own port names, read from
  `getBDMemoryClock`) and `bridged` (`clock != ret['registerClock']`). The
  template reads the flag; it never compares clocks itself.
- `getBDMemoryClock`'s comment loses its "may be None" hedge for the bridged
  case, since V19 now guarantees the reset where a bridge exists.

### 5.4 Templates

- `templates/systemVerilog/moduleRegs.py`: for a memory with `bridged`
  true, `section_01` emits the bridge instance and its bus-side request
  latch instead of the four `DFF_DOM` access flops; `section_02b` and
  `section_03b` for that memory raise `req` and hold `nxt_*_ready` low
  until `done`, then return the read slice and `err`. `pslverr` becomes a
  registered OR of the bridged memories' `err` terms, `1'b0` when none.
  Per-segment write accumulation (`<mem>_data` flops, `_update_n`) stays in
  the bus domain and feeds the bridge's `wdata` as the whole row; each
  segment read is one bridged access, as each is one access today. The
  parameterizable path (`section_01_mem_param`) gets the same treatment.
  The header comment "slave error is never asserted" changes to say when it
  is.
- `templates/systemVerilog/apbDecodeModule.py`,
  `templates/systemVerilog/moduleInterfacesInstances.py`: no change
  expected (§3 item 7; the memory primitive is already clocked by
  `domainClock`).
- `templates/systemc/*`: no change.

### 5.5 Schema and configuration

None. The `clock:`/`reset:` fields and their `blockClock`/`blockReset`
combo keys exist.

---

## 6. Fixtures, tests, documentation

### 6.1 Fixture (D3 option A)

`examples/twoClk` as listed in §2 D3. Model traffic: the cpu writes every
word of `tbl`, reads them back, compares, and logs one success line; a
mismatch is a `Q_ASSERT`. End-of-test voting stays with the existing sinks;
the cpu must not hold the run open (check the testbench's vote mechanism
when wiring it in). Both existing lint variants and `run-vl` cover the new
blocks with no `Makefile` change at the top level.

### 6.2 Unit tests (`unittest/`, registered in `run_all_tests.sh`)

- `test_clock_reset_emission.py`: a second register-handler case with the
  memories declared on a clock other than the feed (the `{memClock}` slot
  already exists in `REGS_DESIGN`) asserting the handler's port list is
  bus pair then memory pair, that a `memory_reg_bridge` instance is bound
  to those ports, that the leaf binds the handler's four ports by name,
  that `pslverr` is driven from the bridge, and that the same-domain case
  still emits no bridge and `assign <port>.pslverr = 1'b0`. The comment at
  the `memClock` assignment ("needs the R20 bridge, not yet implemented")
  goes.
- `test_clock_domains.py`: the V24 case becomes the V19 case (memory on a
  clock with no reset is rejected; memory on a clock with a reset builds).
- A router emission check pinning the `pslverr` register and forward, and a
  passthrough check that the boundary map passes the interface whole. No
  test covers `pslverr` today.
- A bridge module check: discover `common/systemVerilog/memory_reg_bridge.sv`
  and lint it with Verilator under `A2C_RESET_NONE`, `A2C_RESET_ASYNC` and
  the default, in the style of `check_flops_*` in
  `test_clock_reset_emission.py`, with the reason in the failure message.
- `test_memory_reg_bridge_sim.py`: builds `unittest/fixtures/memory_reg_bridge_tb.sv`
  with Verilator `--binary --timing -j 4` (the co-simulation flow's build
  parallelism, with a 600 s timeout on the build subprocess) and runs it
  under twenty configurations: the default, `A2C_RESET_ASYNC` and
  `A2C_RESET_NONE` reset styles, each at bus/memory clock ratios of 1/3, 2/2
  and 3/1 (nine configurations); the default and `A2C_RESET_ASYNC` styles
  again at the 2/2 ratio with the memory clock's first edge phase-shifted by
  one time unit (two more); the default style at the non-integer ratios 3/7
  and 7/3, also phase-shifted (two more); and seven jitter configurations
  that build under `A2C_CDC_JITTER`, one each at the default style's three
  integer ratios, one at `A2C_RESET_ASYNC` 2/2, one at the default style's
  3/7 ratio, and one each at the default style's 1/5 and 5/1 ratios
  (phase-shifted, the two most lopsided integer ratios the suite builds).
  `RESET_STYLES` is a `namedtuple` looked up by label, so the non-integer and
  jitter lists pick a style's defines by name instead of repeating the
  literals, and each configuration is itself a `namedtuple` rather than a
  positional 7-tuple. `--assert` is passed on every build; it is a no-op on
  the Verilator release this suite targets, since assertions default on
  there, but it keeps the checkers on should an older release change that
  default. `A2C_RESET_NONE` runs under `+no_reset_tests` since it has no
  reset to recover from. Every run is seeded through the fixture's `+seed=`
  plusarg, one value per configuration by default (`index + 1`), or a single
  value applied to every configuration through this script's own `--seed`
  override, for a targeted stress sweep. Both `bus_rst_n` and `mem_rst_n`
  start low at time 0, before either clock has toggled, so a four-state
  simulator never evaluates a checker against X; the normal reset tasks
  release them from there. After the startup reset, the run retries the
  first access under the normal retry rule and reports the attempt count,
  then times one plain read to calibrate `done_cycles`, the number of bus
  cycles a read takes to `done` at that ratio, which sizes the sweep
  scenarios below and, from it, `max_retries`, the retry rule's cap on
  attempts before it fatals. A bus-reset recovery's reconnect handshake can
  cost several times `done_cycles` worth of bus cycles at the widest clock
  ratios, so a fixed cap picked for the ratios that existed before the 1/5
  and 5/1 configurations is not enough at those two. A read retry rotates to
  a different row on each attempt, so a stale ack cannot be mistaken for a
  correct one by landing back on the row it already read. The fixture then
  runs thirteen scenarios, each its own task. The first is a write and read of
  every row. The second is a held `req` past `done` that does not start a
  second access. The third is back-to-back accesses at the minimum req gap.
  The header contract requires `req` to drop for at least one bus cycle
  between accesses; `access()` and `soft_access()` drop `req` at the negedge
  after `done`, and the next access may raise it at the very next negedge,
  so the minimum gap this scenario (and `scenario_random_traffic`) issues is
  exactly one bus cycle of `req` low.
  The fourth is a request issued while the memory side is held in reset; it
  fails with `err`. The fifth sweeps a memory reset across an in-flight
  read's request window; the swept variable is `offset_ns`, in time units
  up to `(done_cycles + 4)` bus periods, stepped by the faster clock's
  period, crossed with a reset width from 1 to 6 memory cycles, and it
  checks the recovery accesses after the reset. The sixth sweeps a bus
  reset across an in-flight write's request window over the same range and
  checks that the memory lands on the old or new value only. The seventh
  sweeps a bus reset across an in-flight read's request window, with
  `offset_ns` and a reset width from 1 to 6 bus cycles both swept, and
  checks the recovery accesses after it. The eighth overlaps both resets
  mid-access and checks the recovery accesses after it. The ninth is a
  memory reset between accesses with no request in flight. The tenth is a
  memory reset with the bus idle, followed by a request inside a short
  window afterward while the bus still reads the memory as alive; it sweeps
  reset width and a short assertion-to-request offset stepped by the faster
  clock's period, and checks that the next two reads are not completed by a
  stale answer. The eleventh, `scenario_bus_reset_during_drain`, sizes a
  memory reset in bus periods rather than the fixed 1-to-6-memory-cycle
  width the other reset sweeps use, because a shorter pulse is not
  guaranteed to be observed by the bus domain's synchronisers at the widest
  clock ratios; the formula gives, for example, a width of 6 memory cycles
  at bus/memory ratio 2/2 and 3 memory cycles at ratio 1/3. It lands while a
  read is outstanding, so the bus answers `err` from `BUS_WAIT_ACK` and
  enters `BUS_DRAIN` with `req_latch` still owed an answer. A one-bus-cycle
  `bus_rst_n` pulse then sweeps across the `done_cycles` bus cycles after
  that `err`, the sequence that produces the one-cycle `alive` pulse §4.2
  describes, checking the recovery accesses after it at every offset.
  Unlike the other scenarios, which reset and report `stale_starts` once
  for the whole scenario, this one resets and reports it once per offset.
  It also checks `bus_alive`, `alive_sync_stable`, `ack_sync_stable` and
  `req_latch` rather than `bus_state` itself, because an XMR to a
  `bus_state_t` enum item, declared inside the DUT module rather than a
  package, crashes this Verilator release with an internal error. The
  twelfth is 1500 accesses of
  random traffic concurrent with independent memory- and bus-side reset
  pulsers of random width and gap. Random traffic checks
  against a per-row candidate set (`row_cand`, one queue of still-possible
  values per row) instead of a single expected value, since a reset can
  leave a write's outcome ambiguous: a write that completes clean collapses
  its row's candidates to the one value written; a write that completes with
  `err` appends the written value to the candidates without discarding the
  old ones, since the write may have executed anyway; a read that completes
  clean is fatal unless its value is among the row's current candidates,
  then collapses the row to that one value. The thirteenth,
  `scenario_connect_latency`, runs last, after random traffic, so the
  random stream random traffic draws from is unchanged from before this
  scenario existed; it can no longer rely on `scenario_back_to_back`'s row
  0 value surviving random traffic, so it first writes a known value to
  row 0 with `retry_access` and reads it back once. It then drives its own
  joint reset release: `bus_reset` held for `MEM_HALF_PERIOD` bus cycles,
  `mem_reset_pulse` held for `BUS_HALF_PERIOD` memory cycles, so the two
  releases land at the same simulation time, as close together as two
  different-period clocks allow, and measures the connect handshake as
  three legs instead of one bus-cycle total, so a fast memory clock cannot
  shrink the total below a workable tolerance and a slow one cannot inflate
  it past a reasonable retry bound. Each leg pairs a free-running edge
  counter, in the leg's own clock domain, against a guarded wait on the
  target signal's own positive-edge event, racing them in a fork with
  `join_any` and `disable fork`; the guard skips the wait when the signal
  already reads 1, which is what keeps a leg at 0 under `+no_reset_tests`,
  where `bus_alive` and `alive` sit at their post-power-on values and never
  see a rising edge. L1 counts bus edges from the `bus_rst_n` rise, watched
  from a fork branch armed before either reset task runs, until
  `dut.bus_alive` reads 1: expected 3 exactly (two `alive_sync` stages
  capturing the memory's `alive` of 0, then `BUS_ARM`'s own reaction edge),
  tolerance 0, at most 5 under `A2C_CDC_JITTER`. L2 counts memory edges
  strictly after the bus edge L1 ends on until `dut.alive` reads 1:
  expected 5 (four `bus_alive_sync` stages plus `MEM_ARM`'s reaction edge),
  tolerance 1, at most 7 under jitter. L3 counts bus edges strictly after
  the memory edge L2 ends on until `dut.start_access` pulses: expected 4
  (two `alive_sync` stages, `BUS_CONNECT`'s reaction edge, `BUS_IDLE`'s
  accept edge), tolerance 2, at most 8 under jitter. The retry loop
  (`soft_access` at the minimum req gap) that gives `BUS_IDLE` something to
  accept runs as a fourth branch of the same fork as the two reset tasks
  and the leg counters, since it has to stay active through all three legs
  for `dut.start_access` to ever pulse. All three legs and the total bus
  cycles from the `bus_rst_n` rise to the first clean completion
  (informational only) print in every configuration. The fatal checks are
  skipped, with a printed line, under `+no_reset_tests`, for the reason
  above. Every scenario also runs under
  an always-on end-to-end monitor, independent of which scenario is active:
  it latches the request recorded at `start_access` and is fatal if a
  non-error completion had no execution behind it, if the memory executed a
  request that does not match the one latched, or if one request executed
  against the memory more than once. Every `bus_rst_n`/`mem_rst_n` assert and
  release in the fixture, including inside the random-traffic reset
  pulsers, sits on a negedge of that reset's own domain clock, with a plain
  blocking assignment, so every posedge between them samples reset low
  unambiguously regardless of process scheduling order; a pulse as narrow as
  one cycle is as unambiguous as any wider one. An informational
  `stale_starts` counter, reset and reported once
  per scenario, counts bus edges where the bridge starts an access while the
  memory side is not alive. A `--rtl` option points the same driver at a
  copy of the module for a fail-before comparison.

  Every `drv_req`, `drv_wr`, `drv_addr` and `drv_wdata` write, and every
  driver read of `done`, `err` or `rdata`, sits on a negedge of `bus_clk`
  with a blocking assignment, the same discipline the reset tasks use, so
  the bench does not depend on any particular same-edge ordering of task
  writes relative to the clock and runs the same under full IEEE
  four-region scheduling as under this simulator's own. `retry_access`
  fatals if a call's attempts exceed a checked bound, `max_retries`,
  computed once from three parts. `connect_cost_cycles` is the connect
  handshake's cost in bus cycles after a bus-only reset, `6 +
  ceil(12*MEM_HALF_PERIOD/BUS_HALF_PERIOD)`, margined over attempts measured
  directly with the tb across the suite's clock ratios under
  `A2C_CDC_JITTER` rather than a literal restatement of the module header's
  connect-cost figure (a bus-only reset costs two synchroniser-crossing
  transitions in `BUS_ARM` and `BUS_CONNECT`, not the header's one
  release-to-connect pass). `jitter_allowance_cycles` is 6 under
  `A2C_CDC_JITTER`, 0 otherwise. `reset_width_cycles` is the widest reset a
  `retry_access` caller can still be holding concurrently with the call, up
  to 6 memory cycles converted to bus cycles and rounded up
  (`scenario_mem_reset_then_request_sweep`'s own reset). `startup_retries`,
  checked before `done_cycles` is known, uses `connect_cost_cycles +
  jitter_allowance_cycles` alone. `scenario_random_traffic` keeps its own
  loop and is not bounded by this, since random resets make its attempt
  count arbitrary. After `scenario_random_traffic`'s `join_any; disable
  fork;`, both `bus_rst_n` and `mem_rst_n` are driven high at their own
  domain's negedge, since a pulser killed mid-pulse by `disable fork` can
  leave its reset asserted for whatever scenario runs next. Under
  `+no_reset_tests`, every scenario that exercises a reset is skipped
  (`scenario_mem_in_reset_at_request` through `scenario_mem_reset_then_
  request_sweep`), including the two, `scenario_mem_reset_between_accesses`
  and `scenario_mem_reset_then_request_sweep`, that assert only `mem_rst_n`,
  since no bridge flop responds to `mem_rst_n` in `A2C_RESET_NONE`, the
  style `+no_reset_tests` selects.

### 6.3 Documentation and skills (`rules/skills/`, the deployed source)

- `design-register-decode.md`: a short paragraph under §1 or §4: a
  `regAccess` memory may sit on a block clock other than the bus clock; the
  handler bridges; cost per access from §4.3; the memory's clock needs a
  reset (V19).
- `design-architecture.md`: line 125 says "A memory reached by more than
  one clock ... [is] rejected". That stays true for `memoryConnections:`
  accessors (V8) and gains the exception: firmware access through the
  handler may come from another domain, the handler bridges it.
- `rtl-registers.md`: one sentence in the Domain note.
- `plan-clock-container-model.md`: §7 item 6 points here; its status line
  is unchanged (it already excludes phase 6).
- The specification is not edited. V24 reads "when the generator does not
  implement the R20 bridge" and becomes vacuous rather than wrong.

---

## 7. Phasing and verification

Each phase ends, from `/work/ws/test/builder/base`, with `make clean`,
removal of every `__pycache__`, `make -j8 unittest`, then `make -j8 two-clk`,
never concurrently (memories: `a2c-build-serialization`,
`a2c-make-clean-after-infra-change`, `a2c-pycache-race`). The last phase
runs the full nineteen-target sweep one target at a time and requires
`git status --short examples/` and `git diff --stat examples/` empty.

1. **Bridge module.** `memory_reg_bridge.sv` and its lint check. No
   generator change yet; the unit suite grows by one check.
2. **Clock tree.** §5.2 rename, bridged ports, V19 in place of V24. The
   handler port list of every example is byte-identical afterwards (no
   example bridges anything yet), which is the proof the rename is
   invisible.
3. **Views and handler template.** §5.3 and §5.4. New emission case, the
   router and passthrough `pslverr` checks. Sweep gate: examples unchanged.
4. **Fixture.** §6.1. `two-clk` green including `run-vl` and both lint
   variants. Read the emitted `twoClkTable_regs.sv` and the run log; a
   subagent's report is not proof (`principle-prove-it-works`).
5. **Documentation and sweep.** §6.3, the comment sweep of §5.2 and §5.3,
   `grep -rn "V24\|not implemented" pysrc templates unittest config` returns
   only the V19 diagnostic and durable references. Known hit to clear:
   `config/postParseRegisterPorts.py:670` names "the misleading V24 clock-port
   compare", which is now the V19 check. Full nineteen-target sweep.

Supervisor pattern throughout (`~/.claude/CLAUDE.md`): `code-search` for
lookups, `implementer` for edits, `test-debug` for builds, `reviewer` on
each phase's diff before it goes to the user for commit. The user stages and
commits.

---

## 8. Risks and limits

- **The error path is not observable in co-simulation.** The model-side APB
  `request()` API has no error return, so a model master cannot observe
  `pslverr`; the bus functional model in `interfaces/apb/apb_bfm.h` captures
  it and drops it ("PSLVERR is legal for unmapped APB; do not fatal"). A
  bridged access issued while the memory domain is still in reset is
  therefore silently lost in model-driven RTL runs; the `twoClk` cpu waits
  100 ns after start before its first access for that reason. Neither the
  reset-mid-access path nor the held-in-reset path runs in `run-vl`; both are
  simulated instead by `unittest/test_memory_reg_bridge_sim.py` and the
  bridge testbench it builds (§6.2). Carrying `pslverr` into the model's
  `apb` channel would change an interface contract and is a separate piece
  of work.
- **A stopped memory clock stalls the bus forever.** By specification.
- **Keep attributes are emitted on the ten synchroniser stages; no
  ASYNC_REG or vendor placement attribute exists in `flops.sv`, and none was
  added there because that library is forked downstream.**
- **`memoryType: register`** is instantiated as `memory_sp` by the container
  template today and is treated by the bridge exactly as `singlePort`. No
  example uses it.
- **`count:` on a memory** is one decode range in the handler today; the
  bridge follows the handler's existing addressing and adds no per-element
  state. Verified by reading the emitted handler for a counted memory if the
  fixture or an example has one (`examples/mixed` has, on the bus clock, so
  the same-domain gate covers it).
- A memory whose clock's only reset is a local net inside the leaf (a
  synchroniser output the leaf does not declare) is rejected by V19 with the
  no-selected-reset message; declaring that reset as an `output` reset of the
  leaf is the remedy.
- **Stale-ack defect found in review, now fixed.** `alive` used to be
  free-running (reset to 0, then set every memory cycle regardless of FSM
  state), so it could read 1 on the bus side before a pre-reset stale ack
  had finished draining through its own synchroniser, letting `BUS_RECOVER`
  exit early and a new request complete on that stale ack. `alive` now sets
  only on the memory FSM's first `MEM_IDLE` entry after a reset and holds
  until the next one, which keeps it behind any stale ack still in flight.
- **Second stale-completion defect found in the wide clock-ratio sweep, now
  fixed.** The bus accepted a request on a stale `alive_sync_stable` reading
  after a memory reset. It abandoned that request, dropping `req_latch`
  while the request's rise was already inside the `req_sync` chain.
  `MEM_ARM` had already sampled `req_sync_stable` before that rise arrived,
  so it passed to `MEM_IDLE` on a pre-rise sample. `MEM_IDLE` then saw the
  rise, performed the access for real, and acked later. By then
  `BUS_RECOVER` had already exited on `alive_sync_stable` high with
  `ack_sync_stable` still low, so that ack completed the next request
  instead, with the earlier request's data and `err=0`. Reproduced at
  simulation time 3858 to 3862 in `unittest/test_memory_reg_bridge_sim.py`'s
  bus=2/mem=2 clock ratio, in both the default and `A2C_RESET_ASYNC` reset
  styles: a row 2 recovery read returned row 1's data with no error.
  `BUS_DRAIN` closes the memory-reset path. Once the bus abandons a request
  on a memory reset, it holds `req_latch` high until the memory side
  actually answers, so a late ack can never land on the next request.
  `bus_alive` with the `BUS_ARM`/`BUS_CONNECT` handshake closes the
  symmetric bus-reset path, in which the bus, right after its own reset,
  could accept a request before the memory side had noticed the reset,
  letting an old access's ack complete the new request. The bus-reset path
  was never exercised before this testbench; its sweep scenarios are new
  alongside the fix. See §4 for the full protocol.
- **A drain-mutant coverage gap remains in the testbench.** A mutant that
  drops `req_latch` in `BUS_WAIT_ACK` on `alive` falling, instead of
  entering `BUS_DRAIN`, is caught at the 2:2 clock ratio in both reset
  styles but survives at 1:3 and 3:1. At 1:3 the hazard does not exist,
  since the abandoned `req_latch` pulse is shorter than one memory cycle
  and the memory synchroniser is still in reset for its whole length. At
  3:1 the sweeps do reach the stale-alive window, the `stale_starts`
  counter reports tens of hits there, but not the further alignment where
  the memory's late ack lands on the bus between the next acceptance and
  its first ack sample. The `rdata_hold` reset mutant is caught in every
  reset-capable configuration except the synchronous style at 1:3, where a
  synchronous memory reset cannot clear the hold before the bus, two fast
  cycles later, has already sampled the ack.
- **Double-execution defect found under jitter, fixed by a reset-value
  change that introduced the next finding below.** Wiring the jitter model
  into the end-to-end monitor exposed a real double execution. `req_sync`
  and `bus_alive_sync` were the same two-flop depth on the same clock and
  reset, and the header argued from that equal depth that they always leave
  a memory reset's reset window on the same edge. Jitter breaks that: at a
  memory reset landing on a shared clock edge, `bus_alive_sync_stable` could
  resynchronise one edge ahead of `req_sync_stable`. `MEM_ARM` read
  `req_sync_stable`'s reset value 0 while `bus_alive_sync_stable` already
  showed a real 1, moved to `MEM_IDLE`, and then executed the late-arriving
  real rise of a request the bus had already completed. Reproduced under
  `A2C_CDC_JITTER` in a memory-reset sweep scenario and traced with a VCD.
- **Phantom-acknowledge defect found under jitter, superseded by the
  structural-margin fix below.** The first attempt at a fix made `req_sync`,
  `alive_sync` and `ack_sync` all reset to 1 and removed the `bus_flushed`
  chain. Under jitter, a memory reset landing while a request was in flight
  then made `MEM_ARM` read `req_sync_stable`'s reset value 1 as a pending
  request and raise a phantom `ack` before the real request's own sample had
  landed. That phantom ack crossed to the bus side and was consumed by
  `BUS_DRAIN` as the answer owed to the request the bus had already
  abandoned with err, dropping `req_latch` before the memory had done
  anything for it. The memory then executed that request for real and
  raised a second, genuine ack, which the bus, by then serving an unrelated
  later transaction, attributed to that later transaction instead: a
  completion reported clean for a transaction the memory never touched.
  Reproduced under jitter at ratio bus=2/mem=2, caught by the end-to-end
  monitor, traced with a VCD.
- **Design conclusion: `MEM_ARM` must act on a held request either way, so
  structure, not a reset value, protects it.** The two findings above show
  that neither reset value for `req_sync` is safe by itself: reset 0 turns
  the reset window into a late execution, reset 1 turns it into a phantom
  acknowledge that `BUS_DRAIN` can consume for the wrong request. `req_sync`
  resets to 0 and `bus_alive_sync` gains a third stage against `req_sync`'s
  two, so `bus_alive_sync_stable` cannot read a real 1 until `req_sync_stable`
  has already cleared its own two-stage reset window by one full edge. That
  one-cycle synchroniser margin was round6's fix. Round7 later widened
  `bus_alive_sync` to a fourth stage against the same two, doubling the
  margin (below, and stated explicitly in §4); that four-stage version is
  what the RTL carries. The jitter model was corrected at the same time as
  round6's fix to hold a stage for at most one cycle, on the edge its source
  changes; holding longer against a stable input models nothing physical
  and would defeat any finite margin.
- **Seed 41 testbench race, resolved by a negedge reset-drive discipline.**
  A five-seed stress sweep (5, 17, 23, 41, 100) of the structural-margin fix
  found one failure: seed 41, ratio bus=3/mem=1, jitter on, inside
  `scenario_bus_reset_mid_access_sweep` at offset=20/width=1. Traced with a
  VCD: the scenario's width=1 `bus_rst_n` pulse asserted at an arbitrary,
  non-clock-aligned time and released on the same edge the pulse needed
  sampled low, so no edge in the pulse was unambiguously low going into a
  sample without also being the edge it was released on; different seeds
  changed how the jitter model's random process interleaved with other
  testbench processes, enough to flip which side of that race won. This was
  a testbench stimulus defect, not an RTL defect; the RTL's synchronous
  reset samples exactly what it is given. The first attempt at a fix drove
  every `bus_rst_n`/`mem_rst_n` release with a nonblocking assignment, on
  the standard assumption that NBA lands after the sampling flops have read
  the edge. Re-verified against the same seed and configuration, the
  failure persisted identically, at the same simulation time and with the
  same values. Inspection of the Verilator release this suite targets,
  built with `--binary --timing`, showed why: a nonblocking write to a
  plain variable driven from testbench task code compiles to the same
  direct, immediate write as a blocking assignment, with no deferred
  commit. This simulator's `--timing` scheduler does not defer such writes
  the way full IEEE four-region NBA semantics would, so the NBA form does
  not remove the race under this tool. The fix that does work does not
  depend on assignment timing at all: every reset assert and release now
  sits on a negedge of that reset's own domain clock (plain blocking
  assignment), so every posedge in between samples reset low
  unambiguously, whatever order the simulator runs processes in. A width=1
  pulse is then exactly as unambiguous as any wider one, since the negedge
  before it and the negedge after it are never the same edge as a posedge
  sample. Re-run at all five seeds plus the default set: all 18
  configurations pass at every seed, including seed 41 at bus=3/mem=1 with
  jitter.
- **Mutant table, re-run against the twenty-configuration suite after the
  review-fixes round, with one surviving mutant left as a decision for the
  user.** Supersedes the eighteen-configuration table this bullet used to
  hold; `mut_3stage` is new, testing the round6 margin (three stages) against
  the round7 fix (four).

  | Mutant | Change | Result |
  | :--- | :--- | :--- |
  | `mut_3stage` | `bus_alive_sync` back to three stages (the round6 margin) | 7 of 20 configurations fail, all `A2C_CDC_JITTER` |
  | `mut_2stage` | `bus_alive_sync` back to two stages | 7 of 20 fail, all `A2C_CDC_JITTER` |
  | `mut_aliverst0` | `alive_sync` reset back to 0 | 12 of 20 fail |
  | `mut_ackrst0` | `ack_sync` reset back to 0 | survives all 20 |
  | `mut_nodrain2` | `BUS_WAIT_ACK` drops `req_latch` instead of entering `BUS_DRAIN` on a memory reset | 17 of 20 fail |
  | `mut_rdatarst2` | `rdata_hold` given a reset | 15 of 20 fail |
  | `mut_noforce2` | `MEM_ARM`'s force on `!bus_alive_sync_stable` removed | 17 of 20 fail |
  | `mut_noackgate2` | `BUS_IDLE`'s `!ack_sync_stable` gate removed | 2 of 20 fail, both `A2C_CDC_JITTER` |

  Rerun with the restating checker's own `!ack_sync_stable` term also removed
  (`mut_noackgate2_nochk`): fails at the default seed in the default sync
  style, clock ratio bus=5/mem=1, MEM_PHASE=1, `A2C_CDC_JITTER`, with a
  scoreboard data mismatch, not a monitor or timeout fatal: `random_traffic:
  access 1243: row 1 read 6d70c9b5f1aa, not among 3 still-possible value(s)`.
  It survives all 20 configurations at seeds 5, 17 and 41. The gate closes a
  real window under the two-hold jitter model. A 200-seed sweep against the
  calibration change above finds 1 kill in 200 at bus=5/mem=1
  `MEM_PHASE=1` jitter (seed 32, random-traffic scoreboard) and 1 kill in
  200 at bus=3/mem=1 jitter (seed 73, random-traffic scoreboard); both
  default-seed kills moved seed because the calibration change shifts how
  far the testbench runs ahead of random traffic, and the jitter driver
  draws from the same random stream on every clock edge regardless of
  which scenario is running. The default seeds are kept as they are; the
  RTL's own checker restates the gate `mut_noackgate2_nochk` removes, so
  removing the gate alone still fails every configuration at once, the
  defense-in-depth `mut_noackgate2` already demonstrates.
- **The retry bound is a coarse net; a new scenario is the exact check.**
  Mutant `mut_slowconnect` (`bus_alive_sync` with eight stages instead of
  four) passes all 20 configurations at the default seed. At bus 2/mem 2
  default style the tb printed `max_retries=24 attempts, largest attempt
  count any retry_access call actually used=21`. `max_retries` is margined
  for attempts under jitter and reset-width slack, not sized against the
  header's connect-cost figure, so it absorbs a slower reconnect without
  ever timing out. `scenario_connect_latency` closes that gap: it drives its
  own joint reset release (`bus_reset` held for `MEM_HALF_PERIOD` bus
  cycles, `mem_reset_pulse` held for `BUS_HALF_PERIOD` memory cycles, so the
  two releases land at the same simulation time), then reissues a read of a
  known row at the minimum req gap until one clears with `err=0`, counting
  bus cycles from the release to that completion. The count is checked
  against `6 + ceil(5 * MEM_HALF_PERIOD / BUS_HALF_PERIOD) + done_cycles`,
  the header's connect-cost figure converted to bus cycles plus the read's
  own latency, with a tolerance of `ceil(MEM_HALF_PERIOD / BUS_HALF_PERIOD)
  + 2` for release-phase slack and the cycle-counting fork's own edge
  granularity. It is skipped, with a printed line, under `A2C_CDC_JITTER`
  (a held synchroniser stage adds cycles the tolerance does not cover) and
  under `+no_reset_tests` (`A2C_RESET_NONE` has no live reset past time 0,
  so the release is a no-op and there is nothing to measure). It loses
  precision as the memory clock grows faster than the bus, since the extra
  memory-side stages a slow reconnect would add then convert to less than
  one bus cycle there, so it is sharpest when the memory clock is the
  slower of the two.
- **The connect-latency check now measures each leg of the handshake in its
  own clock domain, resolved.** The single bus-cycle total the check used to
  keep could shrink below a workable tolerance once the memory clock ran
  faster than the bus (the total is denominated in bus cycles, but the
  handshake's own cost is a fixed number of synchroniser-crossing edges in
  whichever domain each crossing lives in), and could not localise a failure
  to one crossing when it did trip. `scenario_connect_latency` now counts
  three legs instead: L1, bus edges from the joint reset release until
  `dut.bus_alive` reads 1 (expected 3 exactly, two `alive_sync` stages plus
  `BUS_ARM`'s reaction edge); L2, memory edges from there until `dut.alive`
  reads 1 (expected 5, four `bus_alive_sync` stages plus `MEM_ARM`'s
  reaction edge, tolerance 1); L3, bus edges from there until
  `dut.start_access` pulses (expected 4, two `alive_sync` stages plus
  `BUS_CONNECT`'s and `BUS_IDLE`'s reaction edges, tolerance 2). Each leg is
  counted in the domain the crossing it measures actually lives in, so an
  extra synchroniser stage at any clock ratio, including a memory clock
  faster than the bus, changes that leg's own count rather than hiding
  inside a total. Under `A2C_CDC_JITTER` each leg checks an upper bound only
  (5, 7 and 8), since a held synchroniser stage adds cycles a two-sided
  tolerance would then have to cover on the low side too. The scenario now
  runs last, after `scenario_random_traffic`, so the random stream random
  traffic draws from is unchanged from before this scenario existed; it can
  no longer rely on `scenario_back_to_back`'s row 0 value surviving random
  traffic, so it first writes a known value to row 0 with `retry_access` and
  reads it back once. `calibrate_done_cycles`, which this scenario's
  tolerance budget does not depend on but the sweep scenarios earlier in the
  run do, is corrected separately: it used to drive `req` from a `posedge
  bus_clk`-timed, non-blocking-assignment task immediately after the startup
  retry, a different sampling edge and assignment discipline than every other
  driver task (`access`, `soft_access`, all negedge-timed with blocking
  assignments); rebuilding that original task body verbatim (recovered from
  the pre-session baseline) to compare against the fix instead surfaces the
  mismatch directly: at bus=1/mem=3 it measures `done_cycles=0`, because its
  first, unguarded settle check finds `drv_done` already true, left over
  from the negedge-timed startup retry that runs immediately before it on
  the wrong edge relationship. This confirms the original calibration was
  unreliable by construction rather than simply measuring a window that
  included leftover connect-handshake state, so no clean old-vs-new number
  is available at every ratio; the fixed task instead runs a complete,
  untimed `access()`, then four idle negedges, then times a fresh read from
  a genuinely idle bus, matching every other driver task's own sampling
  discipline. Measured `done_cycles` after the fix, by configuration: 26 at
  bus=1/mem=3 (default, `A2C_RESET_ASYNC` and `A2C_RESET_NONE`); 11 at
  bus=2/mem=2 (same three styles); 5 at bus=3/mem=1 (same three styles); 9 at
  bus=2/mem=2 `MEM_PHASE=1` (default and `A2C_RESET_ASYNC`); 17 at bus=3/mem=7
  `MEM_PHASE=1`; 5 at bus=7/mem=3 `MEM_PHASE=1`. The sweep scenarios that use
  `done_cycles + 4` as their offset ceiling still cover the whole access
  they sweep regardless of which of these numbers is the true pure-idle
  figure, since a larger `done_cycles` only widens the swept range; all
  thirteen scenarios pass at every one of these values (§7 re-run).
- **`done_cycles` split into `drain_cycles` and `done_cycles`, testbench
  calibration change.** The single `done_cycles` figure conflated two
  different windows: the drain after an access completes (the acknowledge
  falling through `req_sync`, `MEM_ACKED`, and `ack_sync`) and a pure idle
  read's own latency measured from there. Measured at four ratios:
  bus=1/mem=3, drain_cycles=12, done_cycles=18 (was 26); bus=2/mem=2,
  drain_cycles=6, done_cycles=9 (was 11); bus=3/mem=1, drain_cycles=4,
  done_cycles=5 (was 5); bus=3/mem=7 `MEM_PHASE=1`, drain_cycles=7,
  done_cycles=14 (was 17). `calibrate_done_cycles` now counts bus negedges
  from the first untimed access until `dut.bus_alive &&
  dut.alive_sync_stable && !dut.ack_sync_stable && !dut.req_latch` holds,
  the new `drain_cycles`, then raises the timed read at that same negedge
  and counts to done, `done_cycles`, a pure idle read latency with no drain
  folded in at any ratio. `scenario_mem_reset_mid_access_sweep`,
  `scenario_bus_reset_mid_access`, and `scenario_bus_reset_mid_access_sweep`,
  whose offset ceiling used to be `done_cycles + 4`, now use `done_cycles +
  drain_cycles + 4`, so the ceiling explicitly covers the drain after the
  swept access at every ratio, rather than depending on how much of the
  drain the old, sometimes-inflated `done_cycles` happened to overlap by
  accident. `scenario_bus_reset_during_drain`'s offset range, `0` to
  `done_cycles`, is unchanged, since it means to land inside the drain
  itself rather than past it.
- **Per-leg jitter upper-bound discrepancy, found while re-running the
  per-leg check, now resolved as a testbench defect.** The one-cycle
  overage seen at `--seed 41` (default sync style, bus=3/mem=1 with
  jitter, `leg L1 measured 6 bus edges, expected at most 5`), at `--seed 5`
  and `--seed 100` (bus=1/mem=5 `MEM_PHASE=1` with jitter, both times on
  L1), and at a direct build outside the suite's own seed assignment
  (bus=3/mem=1 with jitter, seed 1, on L3) traced to
  `scenario_connect_latency`'s own joint reset release, not the RTL.
  `bus_reset` and `mem_reset_pulse` ran as independent fork branches,
  releasing on their own clock's negedge with only their real-time hold
  widths matched, so the memory reset's release could land before the bus
  reset's own first clock edge had cleared `bus_alive`. The memory's
  `bus_alive_sync` chain then sampled that stale 1, `MEM_ARM` exited to
  `MEM_IDLE` on it, and `alive` pulsed for two memory cycles after the bus
  had already released, so L1 measured the pulse rather than the
  handshake, and one jitter hold on `alive_sync` added the sixth edge. The
  fix replaces the two independent reset tasks with one explicit sequence:
  `bus_rst_n` asserts at a bus negedge and the scenario waits for the
  following bus posedge, the edge that clears `bus_alive`, before
  `mem_rst_n` asserts at a memory negedge; `mem_rst_n` then releases before
  `bus_rst_n` does, since the memory's `bus_alive_sync` chain holds zeros
  through the wait regardless of which side releases first. The per-leg
  bounds themselves were not widened; all twenty configurations pass at
  the default seed and at `--seed 5, 17, 23, 41, 100` against the fixed
  scenario.
- **Alive-pulse defect in the header found in review, now fixed.** `alive`
  can be high for one memory cycle in the middle of a bus reset, if
  `MEM_ACKED`, answering a request pending from before the reset, drains
  into `MEM_IDLE` on an edge where `bus_alive_sync_stable` still reads its
  old value of 1. `BUS_CONNECT` can exit on that pulse rather than on the
  memory side's real reconnection. The header used to claim the opposite,
  that a `BUS_CONNECT` exit proves the memory side has left `MEM_ARM` for
  good; it does not. The outcome is a spurious `err`, not wrong data: an
  access accepted inside such a pulse is abandoned into `BUS_DRAIN` once
  `alive_sync_stable` falls again, and `BUS_IDLE` answers any request with
  `err` while `alive_sync_stable` reads low. `scenario_bus_reset_during_drain`
  (§6.2) reproduces the sequence.
- **Async reset and the memory enable, found in review.** The claim that a
  write already presented to the memory completes the cycle a `MEM_ARM`
  force lands in holds only for that internal, synchronous force. Under
  `A2C_RESET_ASYNC`, `mem_rst_n` itself can arrive mid-cycle and clear
  `mem_state`, and with it `mem_port.enable`, before a write in progress
  finishes, the same as it would next to any memory. Not a defect; the
  header now says so.
- **`BUS_IDLE`'s `ack_sync_stable` gate reframed as an interlock, not a
  margin necessity, found in review.** `alive_sync_stable` and `req_taken`
  already gate what `BUS_IDLE` will accept; the `ack_sync_stable` term is
  kept so that "no access starts against a raised ack" is a property of one
  line rather than an inference from the rest of the FSM, the same defense
  in depth the mutant table above describes for `mut_noackgate2`, which the
  wider twenty-configuration sweep now does observe killing (mutant table
  above). RTL unchanged; only the comment moved from arguing a margin to
  naming an interlock.
- **A `syn_srlstyle`-equivalent attribute on the crossing chains, found in
  review, recommended but not applied.** `syn_keep` and `syn_preserve` stop
  synthesis merging, sharing or retiming a crossing stage with an apparently
  equivalent register, but neither stops it inferring a shift-register
  primitive out of the four-stage `bus_alive_sync` chain. Adding
  `syn_srlstyle = "registers"` to `DFF_KEEP_INST_DOM` and
  `DFFR_KEEP_INST_DOM` (`common/systemVerilog/flops.sv`) was tried and then
  reverted: the file's own `check_flops_default_matches_fork` test
  (`unittest/test_clock_reset_emission.py`) is a drop-in-compatibility
  contract against a downstream fork fixture that does not carry the
  attribute, and its Synplify validity was not confirmed against the user's
  release either. Left as an open recommendation for the user to verify and
  apply, together with the fork fixture, rather than applied unilaterally.
- **Retry-cap scaling defect in the testbench, found while adding the 1/5
  and 5/1 clock ratios, now fixed.** `retry_access`'s cap was a fixed 20
  attempts, sized against the ratios the suite built when it was picked. At
  bus=1/mem=5 with jitter, `scenario_bus_reset_mid_access` hit that cap
  while a bus-reset recovery's reconnect handshake was still legitimately in
  progress (`bus_state` still `BUS_ARM`/`BUS_CONNECT`, converging normally),
  not hung: the handshake at this ratio can cost several times
  `done_cycles` worth of bus cycles, more than 20 cheap retry attempts cover.
  Traced with per-attempt `$display` tracing (a VCD would show the same
  thing): raising the cap to 200 let the same seed finish in 22 attempts and
  the whole run reach `TB_PASS`. The fix scales the cap from the calibrated
  `done_cycles` instead of a fixed count (`unittest/fixtures/memory_reg_bridge_tb.sv`,
  `max_retries`).
- **Reset-pulse-width defect in `scenario_bus_reset_during_drain`, found
  while running the new scenario at bus=5/mem=1, now fixed.** The scenario's
  memory-reset pulse was the same fixed 2 memory cycles the other reset
  sweeps use, but those sweeps do not assert which state the FSM lands in
  afterward, while this one asserts `BUS_DRAIN` specifically. Traced with
  `$display` tracing at the failing seed: a crossing only guarantees the
  receiving domain observes a pulse if the source holds it for at least one
  receiving-domain period, and 2 memory cycles is far short of one bus
  period when the memory clock is the faster of the two by 5:1. The reset
  and the stale-request answer it forces both resolved before the bus ever
  sampled `alive` low, so the access completed straight out of
  `BUS_WAIT_ACK` on the answering `ack` alone, never visiting `BUS_DRAIN` at
  all; the RTL's completion was correct, only not the state path this
  scenario meant to exercise. The fix sizes the pulse in bus periods
  (`mem_reset_width` in `scenario_bus_reset_during_drain`) instead of a fixed
  memory-cycle count. It is two bus periods converted to memory cycles, plus
  a floor of 2 memory cycles so the bus is sure to see `alive` fall.

### Incidental fix

- `templates/systemVerilog/apbDecodeModule.py` emitted a constant `apb_addr
  >= 0` compare for a router with a single slot at offset 0, which
  Verilator's UNSIGNED lint rejects; it now emits a bare begin block. This
  regenerates three routers by one line each: `examples/simple_ip/rtl/apbDecode.sv`,
  `examples/simple_ip/ip/rtl/ipStdDecode.sv` and
  `examples/ip_test/ip/rtl/ipStdDecode.sv`.
- **Second review's findings, applied to the header comments and the
  fixture.** The module header's connect-cost and alive-pulse-width figures
  were corrected against a trace (§4, §4.3); `retry_access`'s attempts are
  now checked against a derived bound instead of tolerating an unbounded
  count up to a large fixed cap (§6.2); every `drv_*` write and driver
  sampling read moved to a negedge of `bus_clk`, the same discipline the
  reset tasks already used (§6.2); and `BUS_IDLE`'s `!ack_sync_stable`
  interlock is kept for a one-edge window it closes under the two-hold
  jitter model, not dropped as redundant with the margin argument (§4.2).

---

## 9. Out of scope, by user decision

- Router-owned registers: not validated, not built.
- Multi-clock routers: rejected, unchanged.
- A nested router hosted through a router-less passthrough container: the
  rejection from ab9c341 stays.
- Any crossing other than the handler's memory access (R17).
