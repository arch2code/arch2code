# Plan: `ip_test` Minimal Example for F1 / IP Parameterization

**Status:** historical. This records the original `ip_test` fixture
shape; current `ip_test` evolution is owned by
`plan-variant-config-unification.md` for variant/Config fixture changes,
`plan-param-constant-collision.md` for SV parameter collision work, and
`plan-eval-symbolic-emission.md` for symbolic-eval parameter work.

## 1. Goal

Create a small, focused example under `builder/base/examples/ip_test` that exercises the
new F1 builder/base support (and provides scaffolding for F2/F3, T1–T8 work later).
The example must:

1. Instantiate **one IP block twice** in a single design, with **different parameter
   values per instance** (Scenario B from `plan-ip-namespaces-and-parameterization.md`).
2. Have the IP block contain **at least one register and one memory** so address-decode,
   register, and memory generation are all covered.
3. Be **as small as possible** — a much smaller surface than `mixed` so it is easy to
   diff generated output, lint, debug, and use as the canonical regression for parameter
   work.
4. Run cleanly through `make db`, `make gen`, `make run`, and `make lint` once the F1
   work is complete (today it should already pass `make db`/`make gen`/`make run` using
   the existing `parameters: + variant:` mechanism).

This example is intentionally **separate** from `mixed`. `mixed` keeps its role as the
"everything turned on" feature soak; `ip_test` is the minimum viable IP-parameterization
test.

## 2. Block Diagram

```
                        +---------------------+
                        |        cpu          |
                        |   (APB master)      |
                        +----------+----------+
                                   | apbReg (cpu_main)
                                   v
+----------------------------------------------------------------+
|                       ip_top  (top block)                      |
|                                                                |
|     +-----------+              +-----------------+             |
|     | apbDecode |--addressGroup| topAddressGroup |             |
|     +-----+-----+              +-----------------+             |
|           |                                                    |
|           | apbReg                                             |
|           |                                                    |
|     +-----v-----+                                              |
|     |   src     |                                              |
|     | (driver)  |                                              |
|     +-+-------+-+                                              |
|       |       |                                                |
|       | dataIf| dataIf                                         |
|       v       v                                                |
|  +----+--+  +-+-----+                                          |
|  | uIp0  |  | uIp1  |                                          |
|  | ip    |  | ip    |                                          |
|  |variant0| |variant1|                                         |
|  |W=8     | |W=12   |                                          |
|  |D=16    | |D=8    |                                          |
|  +-------+  +-------+                                          |
+----------------------------------------------------------------+
```

Block summary:

| Block       | Role                              | hasMdl | hasRtl | hasTb | hasVl |
|-------------|-----------------------------------|:------:|:------:|:-----:|:-----:|
| `ip_top`    | Top container                     | ✓      |        | ✓     |        |
| `ip_top_tb` | Testbench container (mirrors `mixed_tb`) | ✓ |        | ✓     |        |
| `cpu`       | RISC-V style APB master (reused / minimal) | ✓ |     | ✓     |        |
| `apbDecode` | Address decoder (boilerplate)     | ✓      |        | ✓     |        |
| `src`       | Stimulus block — drives `ipDataIf` to both IP instances | ✓ |   | ✓     |        |
| `ip`        | The parameterizable IP under test | ✓      | (later)| ✓     | (later)|

`src` has two output ports of `ipDataIf` (`out0`, `out1`) so that one connection map
routes each port to the matching IP instance. It is intentionally trivial — no
registers, no memory, just a pair of stream sources — so the parameter machinery
around `ip` is the only interesting variable in the design.

The IP is the only "interesting" block. We deliberately keep RTL/Verilator off in the
first cut so the focus is on YAML schema, processYaml, and the SystemC + address-decode
pipeline (the F1/F2/F3/A1/A3 work).

## 3. The `ip` Block — Internal Structure

Described conceptually (authoritative grammar lives in the skill files referenced in
Step 2):

* **Block parameters** (`params:` on the `ip` block): `IP_DATA_WIDTH`,
  `IP_MEM_DEPTH`. Values are bound per-instance via the file-level `parameters:`
  section keyed on the block name (the `mixed.yaml` `blockF` pattern).
* **`ipParameters.constants`** (F1): `IP_DATA_WIDTH` and `IP_MEM_DEPTH` with default
  `value` and `maxValue`. Same names as the block params so width/depth references
  resolve to the same identifier.
* **`ipParameters.types`** (F1): `ipDataT` with `width: IP_DATA_WIDTH` and
  `maxBitwidth: 16`.
* **Plain `types`**: `ipMemAddrT` (`widthLog2: IP_MEM_DEPTH`), `apbAddrT`,
  `apbDataT`, plus an enum `ipModeT`.
* **`variables`**: thin aliases binding field names to types (e.g.
  `data: {type: ipDataT, desc: ...}`), in the `mixed.yaml` style so structures can
  use the variable-name shorthand.
* **`structures`**:
  * `ipDataSt` — one `data` field.
  * `ipCfgSt` — three fields: `enable`, `mode`, `threshold`.
  * `ipMemSt` — one `data` field.
  * `ipMemAddrSt` — one `index` field with `generator: address`.
  * `apbAddrSt` / `apbDataSt` for the register bus.
* **`interfaces`**: `ipDataIf` (`rdy_vld`, structure `ipDataSt`), `apbReg` (`apb`).
* **Register**: `ipCfg` — `regType: rw`, `structure: ipCfgSt`.
* **Memory register**: `ipMem` — `regType: memory`, `structure: ipMemSt`,
  `addressStruct: ipMemAddrSt`, `wordLines: IP_MEM_DEPTH`. (We use the
  `regType: memory` register pattern from `mixed.yaml`'s `blockBTableExt`, not a
  top-level `memories:` entry, so address-decode covers the memory too.)

Two instances are declared with different parameter values:

| Instance | variant   | IP_DATA_WIDTH | IP_MEM_DEPTH |
|----------|-----------|---------------|--------------|
| `uIp0`   | variant0  | 8             | 16           |
| `uIp1`   | variant1  | 12            | 8            |

The differing widths/depths are what F1 work needs to size correctly:

* Constants `IP_DATA_WIDTH` / `IP_MEM_DEPTH` carry `maxValue`.
* Type `ipDataT` carries `maxBitwidth: 16`.
* Structure `ipCfgSt` therefore becomes parameterizable; its `_bitWidth` must be
  text-stable / symbolic (T-series work).
* Memory `ipMem`'s `wordLines` is parameterizable; address sizing must use the
  worst-case (F3 / A3).

## 4. Step-by-Step Plan

### Step 1 — Copy `mixed` to `ip_test` and clean implementation files

```
cp -r builder/base/examples/mixed builder/base/examples/ip_test
```

The goal of the cleanup is to **keep the directory skeleton, hand-written Makefiles,
and `.gitignore` files** so the project's build wiring is preserved verbatim, while
**deleting all generated artifacts and any block-specific implementation files** that
reference the `mixed` block names. `make gen` regenerates everything we delete.

In `builder/base/examples/ip_test`:

1. Delete `arch/mixed.odg` (no diagram is carried into `ip_test`).
2. In `arch/yaml/`:
   * Delete `mixed.yaml`, `mixedInclude.yaml`, `mixedNestedInclude.yaml`,
     `mixedBlockC.yaml`. They are replaced by a single new `ip_top.yaml`.
   * Keep `exampleAddress.yaml` and `project.yaml` for editing in Step 2.
3. In `base/`: delete every `*Base.h` (all generated). Keep the directory.
4. In `model/`: delete every `*.cpp` / `*.h` and the `build/` subdirectory (all
   generated). Keep the directory.
5. In `rtl/`: delete every `*.sv` and every `*.f` (all generated). Keep the directory,
   `Makefile`, and `.gitignore`.
6. In `systemVerilog/`: delete `.gen_file`. Keep the directory.
7. In `tb/`: delete the `mixed/` sub-directory (block-specific, will be regenerated
   for the new top block as `tb/ip_top/`). Keep the `tb/` directory itself.
8. In `verif/`:
   * Keep `Makefile`, `blocks/Makefile`, `blocks/.gitignore`,
     `vl_wrap/Makefile`, `vl_wrap/.gitignore`.
   * Delete the per-block sub-directories `blocks/blockA/` and
     `blocks/blockF_variant0/` (block-specific testbench scaffolding
     regenerated by `make newmodule` if needed).
   * In `vl_wrap/`: delete every `*.sv`, `*.h`, `*.cpp` (all generated).
9. In the example root: delete `.mixed.db`, `mixed.db`, and any other stray
   generated artifacts. Keep the top-level `Makefile` and `include/make/shared.mk`.

Then update the project metadata (still in Step 1, so Step 2 starts from a clean,
renamed shell):

10. `arch/yaml/project.yaml`:
    * `projectName: ip_test`
    * `projectFiles: [ip_top.yaml]`
    * `topInstance: ip_top_tb`
    * Keep `addressControl: exampleAddress.yaml`.
11. The example's top-level `Makefile` references `REPO_ROOT = $(shell git rev-parse
    --show-toplevel)/examples/mixed`. Update the suffix to
    `/examples/ip_test`. Same for any other path that hard-codes `mixed`.
12. Trim `arch/yaml/exampleAddress.yaml` to two address groups: `top` (containing
    `u_ip_top`) and `ip` (containing `uIp0`, `uIp1`). Drop `ip2` and `ip3`.

### Step 2 — Write the trimmed YAML

Create `arch/yaml/ip_top.yaml`. Treat the snippets below as a **sketch only**; the
authoritative grammar lives in the project skill files and must be re-checked against
them (and `make db`) when the file is actually written:

* `builder/base/rules/skills/design-types-structures.md`
* `builder/base/rules/skills/design-architecture.md`
* `builder/base/rules/skills/design-yaml-includes.md`
* `builder/base/plan-foundation-address-decode.md` §F1 for `ipParameters` and the
  `maxValue` / `maxBitwidth` fields.

Where uncertain, copy the corresponding pattern verbatim from `mixed.yaml`
(constants, variables, structures with `generator: address`, the `cpu` /
`apbDecode` blocks, the `apbReg` interface, register/memory entries, and
`parameters:` for `blockF`).

Section-by-section content:

* **`include`**: empty (single file).
* **`blockDir`**: `.`
* **`ipParameters`** (F1; in Step 3 these live as plain `constants`/`types` until F1
  schema lands):
  * `constants`:
    * `IP_DATA_WIDTH` — `value: 8`, `maxValue: 16`.
    * `IP_MEM_DEPTH`  — `value: 16`, `maxValue: 32`.
  * `types`:
    * `ipDataT` — `width: IP_DATA_WIDTH`, `maxBitwidth: 16`.
* **`constants`**: `DWORD: 32` (for the APB types).
* **`types`**:
  * `ipModeT` — enum (`IP_MODE_OFF`, `IP_MODE_LOW`, `IP_MODE_HIGH`).
  * `enableT` — `width: 1`.
  * `ipMemAddrT` — `widthLog2: IP_MEM_DEPTH`.
  * `apbAddrT` / `apbDataT` — `width: DWORD`.
* **`variables`**: aliases used by structure shorthand:
  `enable: {type: enableT}`, `mode: {type: ipModeT}`,
  `threshold: {type: ipDataT}`, `data: {type: ipDataT}`,
  `index: {type: ipMemAddrT}`. (Each with a `desc:`.)
* **`structures`**:
  * `ipDataSt`     — `{ data: {} }`
  * `ipCfgSt`      — `{ enable: {}, mode: {}, threshold: {} }`
  * `ipMemSt`      — `{ data: {} }`
  * `ipMemAddrSt`  — `{ index: {generator: address} }`
  * `apbAddrSt`    — `{ address: {varType: apbAddrT, generator: address, desc: ...} }`
  * `apbDataSt`    — `{ data:    {varType: apbDataT, desc: ...} }`
* **`interfaces`**:
  * `ipDataIf` — `interfaceType: rdy_vld`, structures `[{structure: ipDataSt, structureType: data_t}]`.
  * `apbReg`   — `interfaceType: apb`, structures `apbAddrSt` (`addr_t`) and `apbDataSt` (`data_t`).
* **`blocks`**:
  * `ip_top`, `ip_top_tb`, `cpu`, `apbDecode`, `src` — `hasMdl: true`, `hasTb` as
    appropriate, `hasRtl: false`, `hasVl: false`.
  * `ip` — same flags **plus** `params: [IP_DATA_WIDTH, IP_MEM_DEPTH]` (block-level
    parameter declaration, exactly like `blockF` in `mixed.yaml`).
* **`instances`**:
  * `ip_top_tb` self-reference (mirrors `mixed_tb`).
  * `u_ip_top`, `uCPU` in `ip_top_tb`.
  * `uAPBDecode`, `uSrc`, `uIp0`, `uIp1` in `ip_top`.
  * `uIp0` / `uIp1` carry `addressGroup: ip` and `variant: variant0` /
    `variant: variant1` respectively.
* **`connections`**:
  * `apbReg`   `uCPU` → `u_ip_top`, `name: cpu_main`.
  * `ipDataIf` `uSrc` (`srcport: out0`) → `uIp0`.
  * `ipDataIf` `uSrc` (`srcport: out1`) → `uIp1`.
  * (`out0` / `out1` are declared implicitly via `srcport:` exactly the way
    `mixed.yaml`'s `blockD` declares `dee0` / `dee1`.)
* **`connectionMaps`**:
  * `apbReg` block `ip_top`, direction `dst`, instance `uAPBDecode`,
    `name: cpu_main`.
* **`parameters`** (per-variant binding for the `ip` block):

  ```yaml
  parameters:
    ip:
      - {variant: variant0, param: IP_DATA_WIDTH, value: 8}
      - {variant: variant0, param: IP_MEM_DEPTH,  value: 16}
      - {variant: variant1, param: IP_DATA_WIDTH, value: 12}
      - {variant: variant1, param: IP_MEM_DEPTH,  value: 8}
  ```

* **`registers`**:

  ```yaml
  registers:
    - {register: ipCfg, regType: rw,     block: ip, structure: ipCfgSt,
       desc: "IP configuration"}
    - {register: ipMem, regType: memory, block: ip, structure: ipMemSt,
       addressStruct: ipMemAddrSt, wordLines: IP_MEM_DEPTH,
       desc: "IP scratch memory (FW-accessible)"}
  ```

  Note `addressStruct` is a **structure** (`ipMemAddrSt`), not a type. This matches
  `mixed.yaml`'s use of `bSizeSt` for `blockBTableExt`.

* **`registerConnections`**:

  ```yaml
  registerConnections:
    - {register: ipCfg, block: ip, instance: uIp0}
    - {register: ipCfg, block: ip, instance: uIp1}
    - {register: ipMem, block: ip, instance: uIp0}
    - {register: ipMem, block: ip, instance: uIp1}
  ```

* **`memories`**: omit (we used the `regType: memory` register form instead).
* **`flows`**: remove (or stub a single trivial `.pu` file). Flows are not part of
  the F1 fixture.

Also trim `arch/yaml/exampleAddress.yaml` to two address groups: `top` (containing
`u_ip_top`) and `ip` (containing `uIp0`, `uIp1`). Drop `ip2` and `ip3`.

Target: `ip_top.yaml` ≲ ~150 lines (vs ~530 for `mixed.yaml`).

### Step 3 — Generate baseline (pre-F1 form)

Even before F1 lands, the file should generate using the existing `parameters:` /
`variant:` mechanism (without `ipParameters:` / `maxValue` / `maxBitwidth`).
This gives us a known-good golden reference.

```
cd builder/base/examples/ip_test
make clean
make db
make gen
make run     # SystemC behavioral
```

Commit the resulting layout (YAML + Makefile + addressControl + a `README.md`).
Generated dirs stay `.gitignore`-d as in the other examples.

### Step 4 — Add `ipParameters` and F1-specific fields

The `ipParameters:` block, `maxValue`, and `maxBitwidth` shown in Step 2 are the F1
schema additions from `plan-foundation-address-decode.md` §F1. For the Step 3
baseline build (before F1 lands), define `IP_DATA_WIDTH` / `IP_MEM_DEPTH` / `ipDataT`
as plain `constants:` / `types:` entries. Once F1 schema support is in place, move
them under `ipParameters:` and add `maxValue` / `maxBitwidth`. Until F2 lands,
propagation to derived structures is manual; until F3 lands, address sizing uses the
resolved value rather than the worst-case.

### Step 5 — Add to top-level test runners

1. Add `ip_test` to whatever loop runs every example under
   `builder/base/examples/` (today this is referenced in
   `plan-foundation-address-decode.md` §Testing Strategy step 9).
2. Add a CI hook / `make` target so `make run` over the example suite includes
   `ip_test`.
3. Add a brief `README.md` in `builder/base/examples/ip_test/` describing what it
   exercises and pointing to `plan-foundation-address-decode.md`.

### Step 6 — Use as the regression for F2/F3/A1/A3 work

The example is then the primary fixture for:

* **F2** — verifying transitive `isParameterizable` propagation (`ip_data_t` →
  `ip_cfg_st` / `ip_mem_st`).
* **F3** — verifying worst-case address sizing on `ipMem` (sized with
  `IP_MEM_DEPTH.maxValue = 32`, not the resolved 16/8).
* **A1/A2/A3** — verifying named-constant generation in SC and SV decode for both
  instances, and `hwRegister<N>` worst-case `N`.
* **T-series** — the same fixture extends naturally into Config-template work; the
  block already has all the elements (constant, type, struct, register, memory,
  interface) that need to become symbolic.

### Current Checkpoint — Modules + Config Structure Harness

Date: 2026-05-01

`ip_test` is now the active checkpoint fixture for the hard-replace C++20 module and Config-template path:

- Generated context include outputs are `.cppm` module interface units: `model/ipIncludes.cppm` and `model/ip_topIncludes.cppm`.
- `model/ipIncludes.cppm` includes the structure test harness sections generated from `structures --section=testStructsHeader` and `structures --section=testStructsCPP`.
- `test_ip_structs` is generated as a Config-templated module test class, and the test body covers both parameterizable structures and fixed non-Config structures.
- The testbench config calls `test_ip_structs<ipDefaultConfig>::test()` before creating the hierarchy.
- The new non-Config constant/type/structure coverage in `arch/yaml/ip.yaml` remains present and is exercised by the fixed-structure portion of the generated harness.

Validation status:

- `make db`: up to date.
- `make gen`: passes and regenerates `model/ipIncludes.cppm`.
- `make` from `rundir`: passes.
- `make run` from `rundir`: expected to fail later at the known factory-registration gap; it prints `Running test_ip_structs` first and does not fail in the structure tests.

## 5. Out of Scope (intentionally)

* RTL / Verilator generation (`hasRtl`, `hasVl`) — keep these `false` in v1.
  Add later when SV parameterization (`plan-sv-parameterization.md`) is implemented.
* C++ modules (`.cppm`) — covered by M1–M5 work; the example is structured to make
  that addition mechanical but does not require it.
* Namespaces (`namespace:` field) — Phase 1 of the IP plan; `ip_test` is single-IP so
  it does not need them, but it must not block them (no name clashes with shared
  shipped types).
* Encoders, complex flows, threeCs-style multi-instance containers, signed-arithmetic
  test types — all live in `mixed`.

## 6. Open Questions

1. Should `cpu` / `apbDecode` be **shared** with `mixed` (via include or copied)?
   Recommendation: **copy and trim** for now — the `mixed` versions carry baggage
   (`startDone`, `dupIf`, etc.) that we'd have to drop anyway. Once Phase 1
   namespaces land, we can revisit shared infrastructure.
2. Do we want a single-port memory or dual-port? Default to **single-port memory
   register** (`regType: memory`) since that's the most common IP shape and matches
   `mixed`'s `blockBTableExt`.
3. Should `src` eventually grow a register (e.g. a per-output rate or pattern
   selector) so it also exercises register decode? Recommendation: **no**, keep it
   register-less in v1; that role is fully covered by `ip` itself. Add only if a
   later test needs a non-parameterizable register adjacent to a parameterizable
   one.

---

## Appendix — File Layout After Step 1+2

Directories preserved from `mixed` are kept (so `make gen` knows where to drop
output); only the YAML inputs and the example's top-level files change.

```
builder/base/examples/ip_test/
├── Makefile                                    (REPO_ROOT suffix updated)
├── README.md                                  (new, short)
├── arch/
│   └── yaml/
│       ├── exampleAddress.yaml                (trimmed: top + ip only)
│       ├── ip_top.yaml                        (new, ~150 lines)
│       └── project.yaml                       (renamed/edited)
├── base/                                       (empty, generated by make gen)
├── include/
│   └── make/shared.mk                         (unchanged)
├── model/                                      (empty, generated by make gen)
├── rtl/
│   ├── .gitignore                             (unchanged)
│   └── Makefile                               (unchanged)
├── rundir/
│   └── Makefile                               (unchanged)
├── systemVerilog/                              (empty, generated by make gen)
├── tb/                                         (empty, generated by make gen)
└── verif/
    ├── Makefile                               (unchanged)
    ├── blocks/
    │   ├── .gitignore                         (unchanged)
    │   └── Makefile                           (unchanged)
    └── vl_wrap/
        ├── .gitignore                         (unchanged)
        └── Makefile                           (unchanged)
```

Generated `base/`, `model/`, `tb/`, `rtl/`, `systemVerilog/`, `verif/blocks/<block>/`,
and `verif/vl_wrap/*.{h,cpp,sv}` directories/files are produced by `make gen` and are
not committed (matching `mixed`'s `.gitignore` policy).
