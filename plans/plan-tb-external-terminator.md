# Plan: make testbench termination and checking independent of the DUT model (F5)

- **Status:** CLOSED. W0, W0b, W2 and W4 are implemented and verified; W1 and
  W3 are deferred by user decision (2026-09-08, §5), and nothing in this plan
  is left open. Revised once after adversarial review, which inverted the
  priority — §4 no longer resembles the first draft.
- **Landed last: W2, as the watchdog fallback.** `watchDogHandler`
  (`common/systemc/watchDog.cpp`) arms a second wall-clock-bounded path on
  exactly the pair "no end-of-test voter registered and no `--scTimeLimit`",
  disarmed by a latched end-of-test, and fails the run naming the cause. Tickles
  do not reset it, because having no terminator is a property of the
  configuration rather than of progress. `unittest/test_watchdog_no_terminator.py`
  builds and runs the shipped watchdog and pins six rules, including that the
  stall path is unchanged and that the bound is load-bearing. The user confirmed
  the watchdog mechanism over a startup warning after it landed.
- **Landed since scoping:** the `m_total_tests == 0` guard
  (`testController.h:88-90`), scaffold seeding plus the completion assert
  (`fileGen.py`), three corrected false comments, unit suite 75 pinning both
  rules, and `hasVl: true` on `simple`'s leaves with bidirectional mutation
  proof. §1.2 below describes the code **as it was before W0** and is retained
  because it is the reasoning that justified the change.
- **Source:** review during the multi-clock work (issue #129), from the
  `simple`/`axiDemo` cosim hang diagnosis.
- **Goal:** a testbench terminates *and reports* on its own, so replacing the DUT
  model with RTL cannot remove the only thing that ends the run or the only
  thing that checks it.

## 1. What the code actually does

1. **End-of-test is AND, not OR.** `common/systemc/endOfTest.cppm:84` latches on
   `voteCast && endOfTestCounter >= voters`; `registerVoter()` is `voters++`
   (`:89-92`). Adding a voter can only delay end-of-test, never truncate it.
   This holds by convention, not construction: `endOfTest()` (`:106`) is a
   non-registering constructor and `setEndOfTest` is public on it, so an
   unregistered instance's vote can satisfy another voter's threshold. Every
   voting instance in the tree does register today. There is also no unregister
   on destruction.
2. **The scaffold's only end-of-run check is `isEndOfTest()`.**
   `templates/fileGen/fileGen.py:484-489` emits exactly
   `Q_ASSERT_CTX(...isEndOfTest()...)` then `errorCode::pass()`. It does **not**
   emit `set_test_names` or `are_all_tests_complete()`. And
   `common/systemc/testController.h:88-89` is
   `return m_test_number >= m_total_tests;` with both members initialised to `0`
   (`:98-99`) — trivially true when nothing is seeded, with no `m_total_tests == 0`
   guard anywhere.
   **Therefore a vote is sufficient to pass a scaffolded project.**
3. **A run with no voter hangs without bound.** `scTimeLimit` defaults to `0.0`
   (`simController.cpp:100`) and `main.cpp:312` treats zero as no limit. SystemC
   event starvation does not rescue it: `main.cpp:273` spawns `watchDogHandler()`
   unconditionally for every project and its periodic wake keeps events in the
   queue — stated outright at `watchDog.cpp:41-42`. The watchdog stays silent
   only because `enabled` is gated on registered enablers (`watchDog.cpp:23`).
   Note `endOfTest.cppm:78-79` claims such a project "terminates by `scTimeLimit`
   or event starvation instead"; the starvation half is unreachable.

## 2. The defect, stated precisely

For a DUT whose voter and checks are internal, `--vlInst <top>` removes both in
one step. What remains hangs per §1.3.

Two corrections to the first draft, both from review:

- **It does not then "pass vacuously" — for `simple` it fails.**
  `simpleConfig.cpp:42-45` seeds two test names and `:56` asserts
  `are_all_tests_complete()`; with `u_simple` verilated nothing registers, so
  `0 >= 2` is false and the assert fires. That safety comes from hand-written
  user-region code in one example, not from the framework.
- **The vacuous-pass risk lives in the scaffold, not in `simple`.** Per §1.2 a
  newly scaffolded project has no such assert, so any vote at all passes it.

Census of the 16 shipped Externals (independently recounted; the first draft
said 17 and 11, both wrong):

- **6 of 16 are fully inert** — no stimulus, no vote, no check: `axiDemo`,
  `helloWorld`, `bridgeStdTop`, `nested`, `pySocket`, `simple`.
- **0 of 16 contain any `Q_ASSERT` directly**, but 3 delegate checking to
  External-owned children (§3).
- **3 register a voter directly:** `twoClkExternal.h:46`,
  `ip_test/ip/tb/ip/ipExternal.h:42`, `simple_ip/ip/tb/ip/ipExternal.h:42`.
- **9 of 16 Configs assert `are_all_tests_complete()`; 7 assert
  `isEndOfTest()` only.**

## 3. The house pattern the first draft missed

The first draft claimed no external checker is constructible for a port-less
DUT and generalised that into W4. **That is wrong as a general claim.** The
framework already has an External-owned sibling BFM that checks *and* votes,
outside the DUT and therefore surviving `--vlInst <dut>`:

`axi4sDemoExternal.cpp:17-18` creates `u_axi4s_m_drv`/`u_axi4s_s_drv` under the
External's own `name()`, sibling to the excluded `u_axi4sDemo` (`:5`), and
`axi4s_s_drv.cppm:74` registers a voter, `:79`/`:84` assert parity and frame
length, `:90` votes. `hierVlDemo` is identical; `apbDecode` does the same with
`uCPU` (`someRapperExternal.cpp:16`, `cpu.cppm:78-80`).

**This is the recommended remedy for any DUT with boundary ports**, and it is
strictly better than a timer.

What survives of the original constraint, narrowed to what the code supports:

- The sibling BFM binds to boundary channels (`axi4sDemoExternal.cpp:23-24`).
  `simple`, `axiDemo` and `twoClk` have empty `<name>Inverted` classes
  (`simpleBase.cppm:32-46`, `axiDemoBase.cppm:34-48`, `twoClkBase.cppm:32-46`),
  so for **those** there is nothing to bind and the pattern is unavailable.
- "No boundary ports" is still not "nothing observable" in general —
  `instanceFactory::getInstance(qualifiedName)` and `trackerCollection::getTracker`
  are global lookups, and `are_all_tests_complete()` is itself a port-free check
  on DUT progress. It is unavailable for `simple`/`axiDemo` specifically because
  they declare no registers, memories or address space.
- **Do not group the three port-less examples.** `twoClk`'s sub-blocks are
  `hasVl: true` (`twoClk.yaml:23,29`), so `--vlInst twoClk.uSink` is a real
  RTL↔model check with the surviving model block as checker. `simple`
  (`simple.yaml:34,40`) and `axiDemo` (`axiDemo.yaml:73,79`) have `hasVl: false`
  sub-blocks and cannot do partial cosim at all.

## 4. Scoped work items, in priority order

**W0 — close the vacuous-pass class. Small; no semantic decision. Do first.**
Guard `testController::are_all_tests_complete()` against `m_total_tests == 0`
(`testController.h:88-89`), and scaffold `set_test_names` plus the
`are_all_tests_complete()` assert into `fileGen.py:484-489`. This is the item
that makes a scaffolded pass mean something, and **W1 is unsafe until it lands**
(§5).

**W0b — correct three false comments already shipped. Trivial; no decision.**
`fileGen.py:562` and `:597-598` both tell the user that a test which never votes
"aborts in `final()`". Per §1.3 it never reaches `final()` — it hangs.
`endOfTest.cppm:78-79` claims a starvation exit that `main.cpp:273` makes
unreachable.

**W2 — terminate the hang with a diagnosis. LANDED as the watchdog fallback.**
Priority was raised by a live finding: `examples/mixed` hung under
`--vlInst mixed`, spinning in `sc_simcontext::crunch`. Its only voter is
DUT-internal (`blockB.cppm:196`), so verilating removes it — and the
unconditional watchdog spawn keeps events queued, so the run no longer ended on
starvation as it once would have. W2 therefore restores an exit that the
watchdog work removed, rather than merely improving a diagnostic. The same
applied to `--vlInst simple`.
The first draft proposed a one-shot warning at `setStartupComplete()` when
`voters == 0`. Review's counter was taken: the watchdog is *already* spawned for
every project and *already* wall-clock bounded (1 s), and it is the only
always-on bounded exit that exists. `watchDogHandler` now arms a second path on
`registeredVoters() == 0 && maxRuntimeUS == 0 && !isEndOfTest()`, waits out the
same wall-clock bound so lazily registered firmware and host-thread voters are
not mistaken for none, and fails the run with `No end-of-test voter is registered
and no --scTimeLimit is set, so this run can never terminate`. The condition can
only go true-to-false, so the timer is never rearmed, and tickles do not reset it.
Logging stays in `watchDog.cpp`, which imports `a2c.endOfTest` rather than
including a header, so the module purview warning in `endOfTest.cppm` is
respected. Such a run now ends after about one second of wall clock with a
named cause instead of hanging; that is a failure, which is the honest result
for a configuration nothing can end. The watchdog constraint the user had
previously stated was about wiring it into interfaces, which this is not, and the
mechanism was confirmed by the user on 2026-09-08.

**W3 — pin the invariant in the unit suite. DEFERRED by user decision
(2026-09-08).** What did land is narrower: `test_watchdog_no_terminator.py` pins
the runtime behaviour when the invariant is violated, not the invariant itself.
The invariant "every example's testbench has a DUT-independent terminator"
**fails today** for about seven examples whose only voter is DUT-internal
(`simple`, `axiDemo`, `helloWorld`, `mixed`, `nested`, `xif`, `bridgeStdTop`).
Since §6 rules out retrofitting them, W3 needs a waiver mechanism, and
`builder/base/CLAUDE.md` requires such tests to discover rather than list. No
existing test touches Externals, `endOfTest` or voters, so this is greenfield and
must discover Externals across nested sub-projects at inconsistent depths.

**W4 — enable partial cosim for `simple`. Small YAML change; genuine value.**
Set `hasVl: true` on `simple`'s producer/consumer leaf blocks
(`simple.yaml:34,40`). That puts the `push_ack` handshake across the SC/RTL
boundary and yields real model-versus-RTL checking, replacing an
elaborate/clock/run smoke test with an actual comparison. Reached independently
by both the RTL implementation and the adversarial review.

**W1 — scaffold a live voter and run window. DEFERRED by user decision
(2026-09-08), W0 having landed.** The remaining reason is the second one below:
a configuration with no checker should report a skip, and no such outcome exists.
`fileGen.py:560-569` and `:591-607` ship `stimulusThread` and
`endOfTest eot_{true}` commented out. Making them live would fix the cosim hang
(the External becomes the sole voter), but on top of today's scaffold `final()`
it manufactures an unconditional pass: timer elapses, vote latches,
`isEndOfTest()` true, `errorCode::pass()`. `twoClk` already demonstrates this
shape — `twoClkConfig.cpp:48-49` asserts `isEndOfTest()` only and never seeds
test names, so `--vlInst twoClk` reports a pass because 200 ns elapsed.
W1 would replicate that into every future project.

## 5. The decisions — all taken (2026-09-08)

1. **W2's mechanism** — watchdog fallback (terminates with a cause) versus a
   startup warning (prints, then still hangs). **Decided: the watchdog.** Landed;
   see §4.
2. **W1, only after W0** — should a scaffolded External always be a voter? Once
   W0 lands, a vote alone no longer passes, and the honest answer for a
   configuration with no checker is a *skip*, not a pass. That distinction does
   not exist in the framework today and is the real question behind W1.
   **Decided: deferred.** The scaffold keeps its stimulus thread and voter
   commented out; a skip outcome is a framework feature to be designed on its own
   when a project needs it.
3. **The run window's duration** — `twoClk` hard-codes `wait(200, SC_NS)` against
   the 100 ns `startupDelay`. Tolerable in one hand-authored example, not in a
   scaffold shipped to every project; it needs project config. **Moot while W1 is
   deferred.**
4. **W3's waiver mechanism** — **Decided: deferred.** The runtime consequence of
   a violation is pinned instead (`test_watchdog_no_terminator.py`).

Order as executed: W0 and W0b first, then W4, then W2 with the watchdog confirmed
after the fact. W1 and W3 are not scheduled.

## 6. Out of scope

- Retrofitting the 6 inert Externals. User-region files; per-example judgement.
- Enforcing "voting requires registering" (§1.1). Not live today; worth an
  assert eventually, not now.

