# Plan #134 — arbitration API (`setExternalEvent` / `isActive` / `isNotActive`) on all receive-side interfaces

- **Status:** PLANNED (2026-09-08). No code written.
- **Branch:** `feature/134-add-arbitration-features-to-all-interfaces` (base and pro).
- **Source:** Keystone `axi_fabric` design work; documentation defect D3 (skills
  document the pattern as universal while 7 of 14 channel families lack it).
- **Components touched:** `interfaces/rdy_vld/rdy_vld_channel.h`;
  `interfaces/axi_read/axi_read_channel.h`; `interfaces/axi_write/axi_write_channel.h`;
  `interfaces/axi4_stream/axi4_stream_channel.h`; `interfaces/apb/apb_channel.h`;
  `interfaces/memory/memory_channel.h`; `unittest/`; `rules/skills/systemc-synchronization.md`;
  `rules/skills/systemc-patterns.md`. Companion change in pro: `interfaces/lmmi`.

---

## 1. Problem

The multi-interface arbitration pattern — one thread servicing several input
ports via a shared `sc_event`, an `isActive()` scan, and a blocking receive only
after activity is confirmed — is documented in `systemc-synchronization.md` §1
and `systemc-patterns.md` §3 as if it applied to any port. It applies to four
channel families and is absent from the rest:

| Has the trio | Missing it | Partial (`setExternalEvent` only, no `isActive`/`isNotActive`) |
| :--- | :--- | :--- |
| `notify_ack`, `pop_ack`, `push_ack`, `req_ack` | `apb`, `axi4_stream`, `axi_read`, `axi_write`, `memory`, `rdy_vld` (base); `lmmi` (pro) | `external_reg`, `raw`, `status` |

The partial families are out of scope for this change: adopting the full
trio there is a separate issue if a consumer appears.

The gap bites hardest on AXI: the receive API is blocking-only (`receiveAddr`,
`receiveData`, `receiveDataCycle` — no peek, no non-blocking variant), and both
AXI channels override `setMultiDriver` with an unconditional failure. A model
that must arbitrate across N AXI ports therefore cannot follow the documented
pattern at all; the only workaround is one thread per port plus explicit
`synchLock` mutexes, which distributes what should be a single arbitration
decision across N threads.

Motivating consumer: Keystone `axi_fabric` — 4 AXI managers (read + write, so
8 dst ports) routing into 6 subordinate apertures, designed as a single
arbitration thread per the skill.

## 2. Design

### 2.1 One implementation, at the `rdy_vld` layer

`rdy_vld_channel` is both a user-facing channel and the composition base for
`axi_read`, `axi_write` and `axi4_stream` (e.g. `axi_read_channel` composes
`m_addr_channel` and `m_data_channel`, both `rdy_vld_channel` instances).
Implement the trio once on the `rdy_vld` receive side, mirroring the existing
`push_ack` implementation (`push_ack_channel.h:103-109`):

- `m_active` — true from the moment a value is available to receive until it
  has been consumed.
- `setExternalEvent(sc_event*)` — stores the event pointer and sets
  `m_external_arb`.
- Send path: when an external event is bound, notify it (in addition to, not
  instead of, the internal machinery — the API must be purely additive; an
  unbound channel behaves exactly as today).

### 2.2 Composed protocols forward; leaf protocols implement directly

- `axi_read` / `axi_write` **dst modport**: `setExternalEvent` binds the
  *address* sub-channel; `isActive()` = address pending. Rationale: the
  arbitration decision in an interconnect or multi-port subordinate is made at
  the address phase; once a thread commits to a transaction, gathering write
  beats or returning read data uses the normal blocking API.
- `axi_read` / `axi_write` **src modport**: `setExternalEvent` binds the
  response sub-channel (`rdata` for read, `bresp` for write); `isActive()` =
  response pending. This serves the mirror use case, a manager model
  multiplexing responses from several ports.
- `axi4_stream`: binds its single data channel — direct forward.
- `apb`, `memory`: direct implementations on their channels, same three
  methods, same semantics (request pending on the subordinate side).
- `lmmi` (pro repo): same as `apb`; separate commit on the pro branch.

One event binding per port object, one meaning per modport. No per-sub-channel
API surface: a consumer that needs finer granularity than "this port has work"
has not been seen, and the simplicity rules in `builder/base/CLAUDE.md` say not
to build it until one exists.

### 2.3 Semantics that must hold

- **Additive only.** A model that never calls `setExternalEvent` compiles and
  behaves bit-identically to today. No change to any existing example, BFM,
  thunker, or tandem flow is required for the feature to merge.
- **No lost wakeups.** The scan-then-wait idiom in the skill
  (`while (all isNotActive()) wait(event);`) must be race-free: `m_active`
  must be set before the event is notified, and a value arriving between the
  scan and the `wait` must still wake the thread (SystemC delta semantics make
  this safe when notification follows state update in the same call).
- **`isActive` stays true until consumed**, so a thread that arbitrates among
  several active ports and services one can rescan and still see the others.
- **Tandem:** the trio is model-side state; `setTandem` paths are untouched.
  Verify by running an existing tandem example unchanged.
- **Sockets out of scope:** the `*_port_socket.h` flavor added by #131 is a
  different transport; extending the trio to sockets is a separate issue if a
  consumer appears.

## 3. Steps

1. `rdy_vld_channel.h`: add `m_active`, the trio, and external-event
   notification on the send path, following `push_ack_channel.h` exactly.
2. `axi_read_channel.h` / `axi_write_channel.h`: forward per §2.2 on both
   modport interface classes.
3. `axi4_stream_channel.h`: forward to the data channel.
4. `apb_channel.h`, `memory_channel.h`: direct implementations.
5. Unit tests (see §4).
6. Skill/doc updates: `systemc-synchronization.md` §1 and `systemc-patterns.md`
   §3 gain a per-family support table (now "all"); remove the D3 caveat once
   true. Update `SYSTEMC_API_USER_REFERENCE.md` if it enumerates the API per
   interface.
7. Pro repo: `lmmi` channel, same shape, own commit.

## 4. Tests

- **Compile-contract test:** a unittest that instantiates every channel family
  and calls the trio, so a future family cannot ship without it (discover the
  families rather than list them, per the unittest conventions).
- **Behavioral test, rdy_vld:** two producers, one consumer thread using the
  documented pattern; assert both values arrive, no deadlock, no lost wakeup
  under simultaneous (same-delta) sends.
- **Behavioral test, AXI:** one consumer thread servicing two `axi_read` dst
  ports via one event — the `axi_fabric` shape in miniature. Assert
  transaction interleaving is serviced and responses route to the correct
  initiating port.
- **Regression:** existing examples (`axiDemo`, tandem examples) pass
  unchanged, demonstrating the additive property.

## 5. Acceptance

- A single `SC_THREAD` can service N AXI dst ports via one shared event.
- The pattern in `systemc-synchronization.md` §1 works as written on every
  channel family; documentation defect D3 is closed by code, not by caveat.
- All existing unit tests and examples pass with no modification.

## 6. Consumer validation

Keystone `axi_fabric` will be built against this branch as the first real
consumer (single arbitration thread, 8 dst ports, decode table from YAML
constants) and serves as the integration proof before merge.
