# Clock and reset branch PR review

## Status

Branch `feature/129-clock-followup`, at `5eca0d20`, compared with `origin/main` at `d7897c62`. The branch's merge base is `origin/main` itself.

This record consolidates three reviews:

- the original review at `b828652b` (findings 1-9);
- the rereview at `1ce776d3` (R1-R6);
- the full-branch review at `1ce776d3` (R7-R12).

Fixes landed in `1ce776d3`, `3028732b`, `1d3a0b7d`, `8d92719a`, `6d81a15d` and `5eca0d20`.

Each Fixed or Fixed by restriction disposition below rests on two things:

- the code at `5eca0d20`;
- a regression case that passes in the unit suite, except R12, which the `clkGen` example in `make pipeline-test` covers.

R5 and R6 are unfixed.

The original reproduction fixtures were temporary and have not been rerun.

- Source paths are relative to `builder/base`.
- Line numbers refer to `5eca0d20`.

## Findings

| ID | Sev | Finding | Disposition | Resolved | Regression coverage |
| --- | --- | --- | --- | --- | --- |
| 1 | P1 | A router whose clk/rst_n are renamed gets wrapper pins it does not have | Fixed | `1ce776d3` | `test_clock_reset_emission.py` `check_router_keeps_declared_ports` |
| 2 | P1 | Gated lockstep silently changes sub-nanosecond clock frequencies | Fixed by restriction | `1ce776d3` | `test_clock_reset_emission.py` `check_gated_clock_rejects_off_step_half_period` |
| 3 | P2 | Reused containers overwrite descendant clock and reset resolutions | Fixed | `1ce776d3` | `test_clock_domains.py` `run_reused_container_period_cases` |
| 4 | P2 | One inferred port takes conflicting clocks across instances | Fixed | `1ce776d3`, `3028732b` (R2) | `test_clock_domains.py` `run_topdown_port_conflicting_block_clocks_cases` |
| 5 | P2 | Reset fan-in emits duplicate router reset pins | Fixed | `1ce776d3` | `test_clock_reset_emission.py` `check_router_two_resets_on_one_net` |
| 6 | P2 | Temporary handler binding rejects a valid resetless datapath | Fixed | `1ce776d3`, `3028732b` (R1) | `test_clock_domains.py` `run_register_bus_on_leaf_non_default_clock_cases` |
| 7 | P2 | Memory-derived BFM ports bypass reset validation | Fixed | `1ce776d3` | `test_clock_domains.py` `run_hasvl_memory_connection_port_rejected`, `run_hasvl_register_connection_port_rejected` |
| 8 | P2 | A reused passthrough gets inconsistent register-bus boundaries | Fixed | `1ce776d3` | `test_register_decode_clock.py` `run_passthrough_reused_under_disagreeing_routers_takes_interface_name` |
| 9 | P2 | Passthrough inference ignores an authored child-local interface | Fixed | `1ce776d3`, `3028732b` | `test_register_decode_clock.py` `run_passthrough_authored_boundary_inner_leaf_cross_file`; `test_addrctl_passthrough_single_consumer.py` `_run_authored_boundary_keeps_its_interface` |
| R1 | P2 | Handler reset deferral misses a reset named `rst_n` | Fixed | `3028732b` | `test_clock_domains.py` `run_handler_reset_named_like_container_net_cases` |
| R2 | P2 | Port-domain agreement excludes connectionMaps | Fixed | `3028732b`, `1d3a0b7d` | `test_clock_domains.py` `run_topdown_port_clock_through_connectionmaps_cases`, `run_hasvl_inner_connectionmaps_port_rejected`, `run_hasvl_inner_connectionmaps_port_positive` |
| R3 | P2 | An inferred bus name collides with a register output | Fixed by restriction | `3028732b` | `test_error_passthrough_diagnostics.py` `run_inferred_port_name_colliding_with_register_rejected`, `run_inferred_port_name_colliding_with_connection_port_rejected` |
| R4 | P2 | Router BFMs ignore the selected `addressBlock: reset:` | Fixed | `3028732b` | `test_register_decode_clock.py` `run_router_addressblock_reset_override_not_duplicated`; `test_addrctl_ip_test_view.py` `_assert_unreachable_router_ports_on_bus_domain` |
| R5 | P2 | Dispatch loses the qualified interface identity | Inherited, not fixed | - | None |
| R6 | P2 | A reused router-containing ancestor leaves later occurrences unconnected | Inherited, not fixed | - | None |
| R7 | P2 | A renamed chained map loses the persisted port domain | Fixed | `3028732b` | `test_clock_domains.py` `run_renamed_chained_map_reads_own_domain_cases` |
| R8 | P2 | A BFM binds a local reset that the wrapper cannot see | Fixed by restriction | `3028732b` | `test_clock_domains.py` `run_hasvl_internal_selected_reset_rejected` |
| R9 | P2 | Clock/reset name validation omits inferred interface ports | Fixed | `3028732b` | `test_clock_domains.py` `run_inferred_port_name_collision_cases`, `run_inferred_boundary_port_name_cases` |
| R10 | P2 | Passthrough synthesis bypasses bus width compatibility | Fixed | `3028732b` | `test_error_passthrough_diagnostics.py` `run_passthrough_boundary_width_mismatch_rejected`, `run_inferring_passthrough_width_mismatch_rejected`, `run_parameterised_container_variant_mismatch_rejected` |
| R11 | P2 | Half-period rounding changes accepted clock frequencies | Fixed by restriction | `3028732b` | `test_clock_domains.py` `run_odd_picosecond_period_rejected_cases` |
| R12 | P2 | `clkGen` passes with its divided clock stopped | Fixed | `3028732b`, `8d92719a` | `clkGen` example in `make pipeline-test` (no unit case) |

Notes:

- **2:** the generated wrapper's `clock_gen` asserts at runtime, before the first gated edge, that the half-period is a whole multiple of the lockstep step (`socketSyncClockHalfPeriod()`). Free-running clocks are unaffected.
- **R3:** a collision is rejected at project creation (`config/postParseRegisterPorts.py:856`, `_checkInferredPortName`). The name is not renamed automatically.
- **R8:** every BFM must bind a wrapper-visible reset.
- **R11:** `period:` in odd picoseconds is rejected (`pysrc/processYaml.py:8898-8905`).
- **R5:** still present, and present on `origin/main`.
  - The router-to-leaf dispatch discards the router interface's file context and emits its simple name in the instance's file (`config/postParseRegisterPorts.py:1040`).
  - The register-bus view selects interfaces by simple name (`pysrc/processYaml.py:3438`).
  - The shadowing checks for inferring blocks (`_checkInferredInterfaceScope`) do not cover this router dispatch row.
- **R6:** still present, and present on `origin/main`.
  - The single-router rule counts instance declarations, not hierarchy occurrences (`config/postParseRegisterPorts.py:124-150`).
  - `_findRouterParent` returns the first match (`config/postParseRegisterPorts.py:153-168`).
- **R12:** the example now checks three things:
  - divided-clock edge timing (`examples/clkGen/tb/clkGen/clkGenExternal.cpp:34-80`);
  - reset release;
  - consumer progress (`examples/clkGen/rtl/clkGen.sv:48-72`).

  The stopped-clock mutation has not been rerun against these checks. Its failure is therefore not verified.

## Review warnings

- **APB padding-read hang: fixed.**
  - Every generated read decode now ends in `default: begin nxt_rd_ready = 1'b1; nxt_rd_data = '0; end`, so a padding offset completes with zero data. This covers the same-clock, bridged and memory-register paths (`templates/systemVerilog/moduleRegs.py:782`, `819`, `838`, `878`).
  - Landed in `8d92719a`.
  - No unit test reads a padding offset. The only evidence is the current template and the regenerated example handlers.
- **clkGen functional scoreboard: fixed.** See R12.
- **Lockstep reset-pulse responsibility: accepted by design.** Under co-simulation lockstep, the partner owns reset release timing and the environment copies it at the partner's event. The spec states this at `plans/spec-clock-reset-requirements.md:723-730`, `783-791` and `989-992`.
- **Watchdog wall-time policy: accepted by design.** With no voter registered and no `--scTimeLimit` set, the run fails after the watchdog's wall-clock bound. This follows the decision recorded in `plans/plan-tb-external-terminator.md:131-154` and `186-190`.
- **Free-run to gated transitions** can shorten one interval. This matches the behaviour before the guard, and was not introduced by the branch.
- **`git diff --check d7897c62`** fails with 24 trailing-whitespace and 13 blank-line-at-EOF reports across 21 files.
  - 20 of the files are example sources: `examples/clkGen/base`, `verif` and `model`; `examples/twoClk/model`; and `examples/twoClk/ip/model`.
  - The remaining file is `plans/plan-tb-external-terminator.md:213`.

## Pre-PR findings

- **Mixed co-sim false pass:** fixed. The `cpu.cppm` checks call `errorCode::fail`, so a failed readback fails the run.
- **blockD RTL:** `examples/mixed/rtl/blockD.sv` now implements its table read paths and seeds `blockBTable1` row 0. The `make pipeline-test` mixed leg again runs `VL_DUT=1`.
- **`watchDogBlock` API:** kept. `common/systemc/watchDog.cpp` registers it as `watchDog_model`.
- **`RST` macro:** removed from `common/systemVerilog/flops.sv`. A leftover `define RST` is a compile error (`flops.sv:64-65`).
- **Padding-read hang:** fixed; see the review warnings.
- **New project-creation checks in `pysrc/processYaml.py`** (the `topInstance` checks are scoped to the root project):
  - The `topInstance` is topmost. Its container must reference its own block, its block must not be instantiated elsewhere, and `_topInstance` is a reserved container name.
  - Both ends of a connection lie in one container.
  - Block containment is acyclic (`_validateContainmentAcyclic`).
- **Block clock periods:** `period:` must be a positive integer when authored (`_resolvePositiveCount`).
- **`unittest/test_error_no_primary_router.py` fixture (suite "cyclic router placement"):** corrected. It now builds a real containment cycle and asserts the cycle diagnostic.

## Known follow-ups

- **#152:** testController stalls when a test is not registered. `examples/mixed/tb/mixed/mixedConfig.cpp:55-59` drops the blockD tests to avoid the stall.
- **blockD:** the `blockBTableSP` port is undriven (`examples/mixed/rtl/blockD.sv:21`).
- **projectOpen:** `data` is a class-level mutable attribute (`pysrc/processYaml.py:425`).
- **Unnamed-connection diagnostics:** clockTree prints the internal connection key for unnamed connections (`pysrc/clockTree.py:1352`, `1394`, `1404`, `1596`, `1621`). The container checks in processYaml print a readable label.
- **Padding reads:**
  - The model's `cpu_read` still issues a port read and returns bits beyond the row width (`common/systemc/hwMemory.h:249-260`).
  - The RTL answers zero without a request.
- **clkGen check block:** it uses a raw `always_ff` and the hierarchical reference `uConsumer.count` (`examples/clkGen/rtl/clkGen.sv:50-72`).
- **`_bindTopInstance`:** duplicates the ordinary bind path (`pysrc/clockTree.py:1864`).
- **Unreachable branch:** the zero-primary-router branch (`config/postParseRegisterPorts.py:209-219`) can no longer be reached for YAML-authored designs, because a zero-candidate result needs a containment cycle. A user `postProcess:` script ordered before postParseRegisterPorts could still inject one, since the cycle check runs before any script.
- **Not verified:** synthesis and STA, physical CDC/RDC analysis, and four-state simulation.

## Verification at the final state

These results come from the working tree that the user committed as `6d81a15d` and `5eca0d20`.

| Check | Result |
| :--- | :--- |
| Unit suite | 111/111 suites, `EXIT_CODE=0` |
| `make pipeline-test` | `EXIT_CODE=0`, including the mixed whole-hierarchy co-simulation (`--vlInst mixed`) |
| Clean regeneration of all 22 example roots | No churn |
| `examples/mixed` lint | Clean under `A2C_RESET_SYNC`, `A2C_RESET_ASYNC` and `A2C_RESET_NONE` |
