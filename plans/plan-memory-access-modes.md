# Implementation plan: memory port access modes

Implements `plans/spec-memory-access-modes.md`. Source of the RTL change is
uvc_rd pull request 6, merged as `7a38aac`.

## How the work runs

- The work is split into four passes. Each pass goes to `implementer`, then
  `reviewer`, then `test-debug` for the gate. Review findings go back to
  `implementer` and get a second review before the gate runs.
- The reviewer loads `review-python-code` for Python under `builder/base` and
  `review-rtl` for SystemVerilog. The implementer loads
  `builder-base-development`.
- Edits inside `projectCreate.processSimple` in `pysrc/processYaml.py` are made
  by the main session, not the implementer. Pass 3 is the only pass that may
  need one.
- Every validator and every fix of existing behaviour lands with a fixture that
  fails before the change. `test-debug` confirms the failure on the unchanged
  tree before it confirms the pass.
- Nothing is committed until the user asks.

### Gate rules for every pass

- Run `make clean` in each example before regenerating, since schema, pysrc and
  template edits leave stale output otherwise.
- The unit suite and the example builds never run at the same time.
- Scratch builds use `make -C <absolute path>`.
- Timed Verilator builds in temp directories run with `CCACHE_DISABLE=1`.
- The churn gate compares regenerated example output against the tree before
  the pass. Every diff must be one the pass predicts. Anything else fails the
  gate.

## Pass 1: dual-clock primitive and memory types

No change in behaviour yet. The bridge stays, and both memory clocks bind to the
memory's current `domainClock`.

1. Replace `common/systemVerilog/memory_dp.sv` with the uvc_rd version. Keep
   `clkA`, `clkB`, `PORTA_READ_ONLY` and `PORTB_WRITE_ONLY` exactly as named
   there. Leave out the `syn_ramstyle` comment.
2. Give `common/systemVerilog/memory_dp_ext.sv` the same clocks and parameters,
   keeping its `mem` output. `memory_sp` and `memory_sp_ext` do not change.
3. Add `portRportRW`, `portRWportW` and `portRportW` to `memoryType` in
   `config/schema.yaml`.
4. Add one helper that takes a memory's `memoryType` and access mode and
   returns the register port, `A`, `B` or none, and the capability of each
   port. It follows the spec's selection rule. Every consumer calls it, so the
   rule lives in one place. Until pass 3 the only mode is `rw`, which is what
   `true` means.
5. Rework `templates/systemVerilog/moduleInterfacesInstances.py:73-155`.
   - Replace the three `memoryType == 'dualPort'` tests at lines 87, 140 and
     148 with a dual-port test that covers all four dual-port types.
   - Put the `_reg` interface on the port the helper picks. Block ports fill
     the remaining ports in `ports:` order.
   - Emit both parameters on every `memory_dp` and `memory_dp_ext` instance.
   - Bind `.clkA` and `.clkB` to `domainClock` for now.
6. Add two validators, with diagnostics that name the memory.
   - A register access mode that no port supports, for example `portRportW`
     with `regAccess: true`.
   - A dual-port memory with `regAccess` and two entries in `ports:`. Today
     line 94 overwrites the second block port without warning.
7. Find hand-written `memory_dp` instances outside generated regions in
   `examples/` and rename `.clk`.

Tests:

- A Verilator simulation of `memory_dp` with independent clocks, in the pattern
  of `unittest/test_memory_reg_bridge_sim.py`. Port the uvc_rd
  `memory_dp_ports_tb.sv` as the fixture. Add `portRWportW` to it, which the
  uvc_rd bench does not cover. Register the test in
  `unittest/run_all_tests.sh`.
- Generation checks for each memory type, with and without `regAccess`. They
  cover the instance parameters, which port gets `_reg`, and the port order.
- Rejection fixtures for the two validators. The two-block-port fixture must
  fail on the unchanged tree.

Predicted churn: every generated `memory_dp` instance gains the two parameters
and changes `.clk` to `.clkA`/`.clkB`, all bound to the same signal. Nothing
else changes.

## Pass 2: remove the bridge

1. Delete `common/systemVerilog/memory_reg_bridge.sv`,
   `unittest/test_memory_reg_bridge_sim.py` and
   `unittest/fixtures/memory_reg_bridge_tb.sv`. Remove the suite from
   `unittest/run_all_tests.sh:591-594`.
2. `pysrc/clockTree.py`
   - Remove the bridge reset checks at 1791-1834. Put one check in their
     place. A `singlePort` memory with `regAccess` on a clock other than the
     block's register clock is an error.
   - Remove the bridged clock and reset ports that `_resolveRegisterHandlerBinds`
     adds to the handler, 2348-2376. The handler keeps only its bus clock and
     reset.
   - Remove the memory reset from `MemoryDomain`, the resolution at 440-447 and
     the `memoryClocks` row at 533.
3. `pysrc/processYaml.py`
   - Remove `bridged` at 1599-1603.
   - Remove `domainReset` at 2338-2340 and the reset column that
     `getBDMemoryClock` returns at 1619-1626.
   - Give each memory the clock its register port runs on, taken from the
     owning block's `registerClock`.
4. `config/schema.yaml`: remove `reset` and `blockReset` from `memories`. A
   memory that still sets `reset:` must fail with a diagnostic that names the
   field.
5. `templates/systemVerilog/moduleRegs.py`
   - Remove every bridged branch: 98-128 `has_bridge`, 199-224, 664-667,
     687-690, the bridged arms of 751-788 and 805-823, the `slverr` template
     lines 960-1030, and `section_01_mem_bridge_j2_template` at 1064-1089.
   - `pslverr` goes back to the unmapped-address error only.
6. `moduleInterfacesInstances.py`: bind the register port's clock to the
   register clock and the block port's clock to `domainClock`.
7. `examples/twoClk`: change `tbl` to `portRportRW`, with the block's read-only port A on
   `clkSlow`. Tie off the block-side port in `twoClkTable`'s hand-written code,
   outside the generated regions. Update the YAML comment at line 18. Check
   whether `TWO_CLK_RESET_SETTLE_NS` still has a purpose and keep it if the
   testbench depends on it.
8. Tests
   - `test_clock_domains.py`: remove the three bridge tests at 4160-4171,
     4412-4479 and 4484-4537 and their group at 8235-8237. Add the single-port
     clock rejection and a test that a dual-port `regAccess` memory on another
     clock builds with `clkB` on the register clock.
   - `test_clock_reset_emission.py`: remove the bridge checks at 1909-1937 and
     2233-2402 and their entries at 2710-2711 and 2819-2831. Add a check that
     the handler for a memory on another clock has one clock and one reset and
     lints clean.
   - Check `test_param_const_linkage.py`, `test_register_decode_clock.py` and
     `test_transit_surface_classification.py` for bridge cases and update
     them.
   - Add a rejection fixture for `reset:` on a memory.

Predicted churn: `twoClk` regenerates without the bridge, and the handler
loses its `clkSlow` ports. In any other example, a `regAccess` memory on the
register clock sees no change. Any other diff fails the gate.

## Pass 3: firmware access modes

1. `regAccess` in `config/schema.yaml` accepts `true`, `false`, `rw`, `ro` and
   `wo`. First find out, with a fixture, whether the existing `_validate:
   values:` check in `processSimple` (processYaml.py:8667) accepts a list that
   mixes booleans and strings. If it needs a code change, the main session
   makes it.
2. Normalise `true` to `rw` once, when the memory is parsed. After that, a
   memory's `regAccess` is `False`, `rw`, `ro` or `wo`. The boolean tests in
   `processYaml.py:2341,2454`, `intf_gen_utils.py:1304`,
   `config/postParseRegisterPorts.py:62,697`, `templates/systemc/includes.py:233`
   and the doc templates keep working as they are. The SQL at
   `processYaml.py:5813` tests `a.regAccess = 1` and must change. Drop the
   `bool` annotation on `MemoryDomain.regAccess` if it survived pass 2.
3. Pass the mode into the port helper from pass 1. `ro` and `wo` now reach the
   A-side choices, for example `portRportW` with `ro` puts `_reg` on port A.
4. `templates/systemVerilog/moduleRegs.py`
   - `ro`: the write case still decodes the memory's range and completes the
     transfer with no `pslverr`. It drives no write strobe and no write
     enable to the memory.
   - `wo`: the read case completes at once with zero. It has no
     `rd_enable`/`rd_capture` pipeline and does not access the memory.
   - The fixed-width paths (`section_01_memregs`, `section_02b_memregs`,
     `section_03b_mems`) and the parameterised paths (`section_01_mem_param`,
     `section_02b_mem_param` at 593, `section_03b_mem_param` at 751) all need
     this.
5. SystemC model
   - `common/systemc/hwMemory.h`: add a firmware access mode, `rw` by
     default. `cpu_write` on an `ro` memory drops the write. `cpu_read` on a
     `wo` memory returns zero. Both log at `LOG_IMPORTANT` through
     `log()` in `common/systemc/log.h`, naming the memory and the address.
   - `templates/systemc/constructor.py:246-251`: pass the mode when it
     constructs the `hwMemory`.
6. Tests
   - Handler generation checks for `ro` and `wo`, fixed and parameterised,
     including a lint of each handler.
   - Port choice for every cell of the spec's selection table.
   - A rejection fixture for an unknown `regAccess` value.
   - Existing YAML with `true` produces the same output as before.

Predicted churn: none in existing examples, since they use only `true` and
`false`.

## Pass 4: example coverage, documentation, acceptance

1. Add two memories to `examples/twoClk`, since it already has a register clock
   and a second clock.
   - A `portRportW` table with `regAccess: wo`, which firmware loads and the
     block reads on `clkSlow`.
   - A `portRportW` buffer with `regAccess: ro`, which the block fills on
     `clkSlow` and firmware reads.
   - The testbench or firmware test loads and checks both. It also makes one
     wrong-direction access of each kind and checks for no `pslverr`, the
     unchanged contents and the zero read. In model mode it checks for the
     log message.
   - Run tandem for the leaf if `twoClk` supports it.
2. Documentation
   - `rules/skills/design-architecture.md`: the memory fields at 179-183 and
     the crossing note at 140.
   - `rules/skills/design-register-decode.md`: replace the bridge section at
     184-194, the error rows at 440-450 and the `regAccess` passages.
   - `rules/skills/manage-address-space.md:36-37` and
     `rules/skills/rtl-registers.md`.
   - Search `ARCH2CODE_AI_RULES.md` and `GENERATOR_ARCHITECTURE.md` for the
     memory field catalog and the bridge.
   - Leave `plans/plan-register-handler-bridge.md` as the record of the old
     design.
   - Run `make agent-dev-setup` so the installed copies match.
3. Acceptance against uvc_rd. Regenerate the debayer `lsc` block with
   `portRportW` and `regAccess: wo`, and compare its memory instances and
   `cfg_clk` wiring with the hand-edited `lsc.sv`. If the debayer project is
   not available, a unit fixture copies the `lsc` memory YAML and checks the
   generated instance text.
4. Final gate: the full unit suite, then every example serially, including
   lint. Then the comment sweep over the whole branch diff.

## Not in scope

- The `syn_ramstyle` attribute.
- A read-only port B or write-only port A type. The spec's `ro` case uses
  `portRportW` with the register port on A.
- Showing the access mode in the generated documents and firmware headers.
  They keep showing that the memory is accessible.
- `memoryConnections:` clock rules. A block-side port still runs on the
  memory's `clock:`.

## Pending RTL decision

Verilator raises `MULTIDRIVEN` on `mem` when both ports can write and `clkA`
and `clkB` are different nets, which fails `make lint`. The RTL engineer will
choose between a scoped `lint_off MULTIDRIVEN` in `memory_dp` and
`memory_dp_ext`, and a generator error for two writers on two clocks. The
passes above do not depend on the answer: `twoClk` uses `portRportRW`, and the
lint test leaves the two-writer, two-clock case out until it is decided. The
answer lands as a small follow-up pass with its own review and gate.
