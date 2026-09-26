# Clock and reset branch PR review

## Verdict and scope

**Request changes before opening the PR.** The review found nine actionable defects, including generated RTL that cannot elaborate and simulations that silently use incorrect clocks.

- Review date: 2026-09-25.
- Branch: `feature/129-clock-followup`.
- Reviewed HEAD: `b828652b15e415a17fccef428284f18848853b2e`.
- Comparison base: `origin/main` at `d7897c62d08c6d5846023bd13c8b96c204b6451a`.
- Scope: full branch diff, with independent Python, hardware, simulation-wrapper, and register-routing reviews.
- Review method: adversarial review against `builder-base-development`, Python review guidance, and the clock/reset design contracts.

All source paths and line numbers below refer to the reviewed HEAD and are relative to `builder/base`. The review did not modify implementation files. All nine findings are open.

## Actionable findings

### 1. P1: Renaming a router's clock/reset breaks its Verilator wrapper

**Locations:** `templates/systemVerilog/module_hdl_wrapper.py:118`, `templates/systemVerilog/apbDecodeModule.py:42–48`.

A router with `hasVl: true` can map its implicit `clk/rst_n` onto container signals such as `busClk/busRst_n`. The router generator renames the actual module ports, but the wrapper still connects their original names:

```systemverilog
// Generated router declaration
input busClk, busRst_n

// Generated wrapper instantiation
.clk(clk),
.rst_n(rst_n)
```

Database creation and generation succeed. Verilator then reports `PINNOTFOUND` for both connections.

**Impact:** Supported domain renaming breaks standalone router co-simulation and tandem elaboration.

**Suggested fix:** Establish one DUT-port identity contract in the view. Emit wrapper bindings such as `.busClk(clk)` and `.busRst_n(rst_n)`, while preserving the wrapper's SystemC-facing boundary.

Both the Python and hardware reviews independently reproduced this.

### 2. P1: Socket lockstep silently changes sub-nanosecond clock frequencies

**Location:** `templates/systemc/module_hdl_wrapper.py:495–500`.

The clock generator receives notifications every 500 ps and toggles at most once per notification. A valid clock with a 500 ps period needs an edge every 250 ps, which this implementation cannot produce.

A compiled SystemC probe using the actual socket scheduling code produced:

```text
fast edge 0 s
fast edge 500 ps
fast edge 1 ns
fast edge 1500 ps
```

**Impact:** A declared 2 GHz clock runs at 1 GHz. Other half-periods that are not multiples of 500 ps suffer quantization, changing clock ratios and crossing behavior.

**Suggested fix:** Make gated time advancement account for actual clock-edge deadlines. Repeated `sig.write()` calls within one update phase will not solve this, because those writes collapse into one update.

### 3. P2: Reused containers overwrite descendant clock resolutions

**Location:** `pysrc/clockTree.py:2665–2690`.

`_resolveAllInstances()` walks hierarchy occurrences but stores results by declaration-level `instanceKey`. When a container block appears twice, its descendant instance keys repeat. The second traversal overwrites the first.

Reproduction:

```text
uWrapA -> 7 ns clock
  uLeaf
uWrapB -> 9 ns clock
  uLeaf
```

The `hasVl` leaf declares no explicit period. Database creation should reject the ambiguous standalone timing under V21. Instead, it succeeds and selects **9 ns**. Reversing the wrapper declarations selects **7 ns**.

**Impact:** Standalone timing depends on declaration order. Reset attribute resolution has the same information loss.

**Suggested fix:** Preserve all hierarchy-occurrence resolutions and validate agreement before selecting standalone attributes.

### 4. P2: The same inferred port can acquire conflicting clocks across instances

**Location:** `pysrc/processYaml.py:3253–3259`.

Two instances of one block can assign the same top-down port to different block-local clocks through their connections. Validation checks the endpoints individually but never establishes a single domain for the shared block port.

The view subsequently deduplicates the port and chooses one instance:

```python
instanceKey = next(iter(portRow['instance']))
```

A fixture assigning `out` to `clkA` on one instance and `clkB` on another generates successfully. Reversing connection order changes the generated BFM binding between `clkA/rstA_n` and `clkB/rstB_n`.

**Impact:** A single generated wrapper silently samples or drives an interface on the wrong domain for one instance.

**Suggested fix:** During `projectCreate`, validate agreement by block and port using resolved block-local clocks. Persist that domain instead of choosing an instance in the view.

### 5. P2: Reset fan-in creates duplicate named router pins

**Location:** `pysrc/clockTree.py:574–580`.

For router/handler instances, the emitted reset-pin rename is selected by equality of the parent net, rather than identity of the child reset port.

If a router has two resets and both bind to `busRst_n`, generation produces:

```systemverilog
.busRst_n(busRst_n),
.busRst_n(busRst_n)
```

The second declared reset port remains unconnected.

**Impact:** The containing RTL hierarchy fails elaboration, independently of the wrapper defect in finding 1.

**Proof:** Verilator reports a duplicate `busRst_n` connection and a missing `rstExtra_n` pin.

**Suggested fix:** Rename only the selected child bus-reset port, using `name == child.busResetPort`. Apply the identity-based rule to clock-pin handling too.

### 6. P2: Temporary handler bindings reject a valid resetless datapath

**Locations:** `pysrc/clockTree.py:947–953`, `2249–2253`.

A leaf can validly declare:

- Default datapath clock `clkA`, without a reset.
- Register clock `clkB`, with `rstB_n`.
- Its register port on `clkB`.

The initial binding pass treats the synthesized register handler as an implicit `clk/rst_n` child. It binds to default `clkA` and demands a reset before the later register-handler pass can move it to `clkB/rstB_n`.

**Proof:** `make db` rejects this fixture. Adding an unused reset on `clkA` makes it pass.

**Impact:** Valid multi-clock register leaves are rejected. The diagnostic suggests modifying the generator-owned handler.

**Suggested fix:** Resolve synthesized handlers directly onto their final bus domain before reset-binding validation.

### 7. P2: Memory-derived BFM ports bypass reset validation

**Locations:** `templates/systemc/module_hdl_wrapper.py:255–256`, `pysrc/processYaml.py:3271–3287`.

A `hasVl` leaf with `resets: {}` can obtain its interface through a parent-owned memory's `memoryConnections` row. This port category escapes the reset validation applied to ordinary BFM ports.

Database creation and generation succeed, emitting:

```cpp
tbl_bfm.clk(clk);
tbl_bfm.rst_n(None);
```

**Impact:** The generated SystemC wrapper cannot compile.

**Suggested fix:** Validate every port category that emits a BFM during project creation, including memory-derived ports. Reject the missing reset there. A template fallback would hide the broken producer contract.

### 8. P2: Reused passthrough blocks get inconsistent register-bus boundaries

**Locations:** `config/postParseRegisterPorts.py:885–888`, `1056–1060`.

Instantiate one router-less wrapper under two routers whose `registerDecoderPort` names differ. When the wrapper has no explicit `registerPorts:`, dispatch chooses each router's name independently, but the wrapper's internal boundary map uses only the first serving router.

The generated wrapper declares both `apbReg` and `customDecoder`, while its inner leaf connects only to `apbReg`.

**Proof:** Database creation and generation succeed; RTL lint fails with missing interface connections. Making the two router port names agree passes lint.

**Impact:** Accepted YAML produces an unelaboratable hierarchy.

**Suggested fix:** Validate a single inferred boundary binding across all instances of a passthrough block. Reject conflicting inference and require an explicit `registerPorts:` boundary.

### 9. P2: Passthrough inference ignores an authored child-local interface

**Locations:** `config/postParseRegisterPorts.py:755–758`, `1061–1074`.

A reusable wrapper in `child.yaml` declares a register boundary using its own `ipReg` interface. Its inner register-owning leaf relies on inference. An outer router in `parent.yaml` uses a compatible `apbReg` interface.

The recursive serving-router lookup imports the outer router's interface into the child's generated connection map, bypassing the wrapper's authored boundary.

**Proof:** `make db` fails with:

```text
value apbReg was not valid in context child.yaml
but is defined in parent.yaml
```

Explicitly repeating `ipReg` on the inner leaf makes generation pass.

**Impact:** A reusable wrapper cannot infer its internal register connection from its own declared boundary.

**Suggested fix:** Propagate the nearest authored passthrough boundary's interface inward. Resolve handler port naming separately from interface ownership.

## Python architecture assessment

**FAIL: The branch needs producer-contract fixes before approval.**

The strongest issues are concrete data-model failures:

- Hierarchy occurrences collapse into declaration-level keys.
- Port deduplication happens before cross-instance domain agreement is established.
- Emitted router pin identity differs between consumers.
- Reset validation does not cover every generated BFM source.
- Register passthrough inference crosses an authored interface boundary.

These fixes belong primarily in `projectCreate` derivation/validation and shared `projectOpen` views. Adding defaults, compatibility lookups, or template-side recovery would conceal the failures.

The review did not establish additional actionable defects in the `schema.py` or `valueResolver.py` changes.

## Independent hardware assessment

- **PASS:** All 20 existing `memory_reg_bridge` simulation configurations passed, covering reset styles, clock ratios/phases, reset recovery, and CDC-jitter injection.
- **PASS:** Generated 96-bit memory-handler tests passed staged writes, readback, exact write counts, and memory-held-reset error responses in both APB ready modes.
- **PASS:** Targeted `twoClk` simulations passed readback, partial-row accumulation, error propagation, and recovery under synchronous and asynchronous reset builds.
- **PASS:** Targeted `clkGen` RTL simulations checked divided-clock operation, reset assertion, synchronized release, and consumer restart.
- **FAIL:** Router pin generation and wrapper timing have the defects above.

### Additional warnings

1. **Inherited APB padding-read hang.** At `templates/systemVerilog/moduleRegs.py:810–824`, a 96-bit row has a 16-byte stride, but reading padding offset `0xC` matches no word case. The generated handler leaves `pready=0` and issues no bridge request. This remained stuck for 200 bus cycles in both APB ready modes. The new bridged path copies an existing same-clock defect.
2. **The checked-in `clkGen` test is not a functional scoreboard.** Its external test completes after 500 ns, and its leaf models are empty scaffolds. A green example sweep alone does not prove the clock/reset chain.
3. **Lockstep reset pulse responsibility needs explicit documentation.** Socket reset counts use a fixed 1 ns timebase, so a short pulse can miss a slow synchronous domain. This follows the explicit partner-owned reset contract and is not counted as an implementation blocker. See `plans/spec-clock-reset-requirements.md:723–730`, `783–791`, and `989–992`.
4. **The new watchdog imposes a wall-time termination policy.** Delayed voter registration or future force-and-stop completion can be preempted after the grace period. This matches the accepted watchdog plan, so it is a compatibility concern rather than an implementation defect. See `plans/plan-tb-external-terminator.md:131–154` and `186–190`.

Hardware checklist: **4 PASS, 2 FAIL categories, 4 WARN**.

## Verification and reproduction artifacts

The findings were checked with make-driven generation, reopened database views, actual generated artifacts, Verilator elaboration, and compiled SystemC probes.

Temporary reproduction artifacts were retained under `/tmp/opencode` at review time. They are local artifacts, not committed regression fixtures, and may not survive environment cleanup.

```bash
make -C /tmp/opencode/hw129-review -j2 lint-wrapper lint-router
make -C /tmp/opencode -f clock-review.mk -j8 check
```

The lint command intentionally reproduces the router failures.

Additional artifact locations:

| Finding | Reproduction artifact |
| --- | --- |
| 1 | `/tmp/opencode/clock-router`, `/tmp/opencode/hw129-review` |
| 2 | `/tmp/opencode/clock-review.mk`, `/tmp/opencode/socket_clock_review.cpp` |
| 3 | `/tmp/opencode/clock-review/design.yaml`, `/tmp/opencode/clock-review/probe.py` |
| 4 | `/tmp/opencode/clock-ports/design.yaml`, `/tmp/opencode/clock-ports/probe.py` |
| 5 | `/tmp/opencode/hw129-review` |
| 6 | `/tmp/opencode/clock-register/design.yaml` |
| 7 | `/tmp/opencode/verif/leaf_hdl_sc_wrapper.h`, `/tmp/opencode/review-checks.py` |
| 8 | `/tmp/opencode/regports-review-1ajw3w6t`, passing control `/tmp/opencode/regports-review-4ufv_bwq` |
| 9 | `/tmp/opencode/regports-review-l3kydhg9`, passing control `/tmp/opencode/regports-review-_e1fg72u` |
| Padding-read warning | `/tmp/opencode/hw129-review/handler_tb.sv` |

The register-passthrough reproduction driver is `/tmp/opencode/regports_review.py`. It routes database creation and generation through project make targets.

Additional checks reported by the independent reviews:

- All 14 schema-only cases in `test_project_scope.run_schema_cases()` passed.
- 26 cases across 13 register-routing suites passed, covering passthrough chains, reuse, address-group diagnostics, unserved consumers, nested-router rejection, router register/memory ownership, authored handlers, and explicit port names.
- A `Q_ASSERT` after timed `sc_start()` reached the summary path and preserved exit status 1. The suspected assertion-exit regression was excluded.

## Limits and PR recommendation

The full regression suite and full SystemC/tandem example matrix were not run. Physical CDC/RDC analysis, synthesis/STA, and four-state simulation remain unverified. The passing bridge simulations do not establish physical metastability or bundled-data timing guarantees.

**PR recommendation:** Fix the nine findings, then rerun the full suite with these adversarial cases added. The existing happy-path tests miss the identity, reuse, and inference failures that dominate this review.
