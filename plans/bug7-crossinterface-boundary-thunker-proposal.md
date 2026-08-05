# BUG 7 — cross-interface boundary thunker at the testbench/DUT boundary

- **Status:** IMPLEMENTED and green (2026-07-28). All edits unstaged in `builder/base`.
- **Source:** `~/isp-parameterization-bug-report.md`, BUG 7 (was Open, High)
- **Components touched:** six `interfaces/<proto>/<proto>_port_thunker.h`;
  `pysrc/processYaml.py` (`projectOpen` view); `pysrc/intf_gen_utils.py`
  (template utility); `templates/systemc/testbench.py` (emission).
- **Fixture:** new `examples/xif` (model-only) reproduces RED and proves GREEN.

> **History note.** The original proposal on this page framed BUG 7 as a
> single `projectOpen` view change with "no template changes", on the premise
> that `testbench.py` already emitted the thunker mirror and would light up
> unchanged. Implementation disproved that premise. This document has been
> rewritten to record what the fix actually required. The corrected root cause
> is in §2.

---

## 1. Problem

When a parameterized DUT is parameterized on a **subset** of its model
testbench's source/sink parameters (e.g. a point-operation DUT drops
`HORIZONTAL_SIZE` / `VERTICAL_SIZE` while the stimulus and sink keep them to
shape frames), the generated model bind fails to compile:

```
no matching function for call to object of type 'push_ack_out<streamBndrySt>'
   ... uSrc->out(streamIn);                        (xif dutExternal.cpp:20 — reproduced)
```

Every parameterized struct is generated as `template<typename Config> struct
<name>`, keyed on the **whole** `Config`. So `stream_t<dutConfig>` and the
boundary struct carried by the stimulus are **distinct C++ types** even when
their packed layouts are identical. The DUT port keeps its `<dutConfig>` type;
the External stimulus port carries the boundary struct; the direct bind between
them does not type-check.

**Affected product:** isp_blc, isp_ccm, isp_gain, isp_lut, isp_rgb_gain — every
standalone DUT whose testbench drives it through connected model source/sink
blocks over a parameterized video stream. These modules ship at the uniform
footprint (H/V retained on the DUT as inert) as an interim workaround; the
accurate-footprint goal is what BUG 7 unblocks.

The framework already solves the identical problem for **hierarchical IP
containers** via a per-end `<proto>_port_thunker` (see
`examples/ip_test/top/yaml/ip_top.yaml:106`, `srcOut0BoundaryIf`). BUG 7 was
that the same mechanism did not reach the testbench/DUT boundary.

---

## 2. Verified root cause (corrected)

The External pseudo-block's thunker mirror was **not** already wired for this
case. It is emitted **only** inside the `connectDouble` loop
(`testbench.py:148-167`), and `sc_declare_thunkers` / `sc_thunker_protocols`
(`intf_gen_utils.py`) iterated **only** `connectDouble` and `connectionMaps` —
never `prunedConnections`.

The decisive fact the original proposal missed:

> **A DUT is always excluded from its own tbExternal.** Every connection with an
> end on the excluded DUT instance is therefore moved into `prunedConnections`
> by `getBDConnections`. A DUT-boundary connection can **never** be a
> `connectDouble`, so it can never reach the only path that emitted the thunker
> mirror. The pruned end was bound **raw** in `ext_sec_body`
> (`testbench.py:197-205`) — the exact site of the failing bind.

So classifying the pruned end (the original "Part A") is **necessary but
inert on its own**: nothing consumed the annotation on the pruned path. Reaching
green required emission changes in the template utility and the testbench
template, plus a missing thunker constructor shape.

A second, independent blocker surfaced during implementation: the tbExternal
previously **forward-declared** a parameterizable child's Base as a global-module
`template<...> class XBase;`. That forward declaration is a distinct entity from
the module's *exported* template, so the member type and the `createInstance`
`dynamic_pointer_cast` target carried mismatched RTTI and the cast returned null.
It only ever worked for the DUT itself because `<dut>Testbench` already imports
`<dut>.base`. This is on BUG 7's critical path because the boundary thunker
inherently requires parameterized siblings.

---

## 3. The fix — four coupled parts

### Part 0 — thunker constructor shape 4 (all six protocol headers)

Each `<proto>_port_thunker` offered a 2×2 family with one empty cell. The two
axes are (a) child-end data direction — consumer (`in`) vs producer (`out`) —
and (b) how the parent (up) side is captured — a fully-bound channel **interface**
(eager) vs an unbound parent **port** (lazy, resolved on the spawned thread's
first iteration because the port binds only during elaboration). The three
existing shapes were consumer+port, consumer+iface, producer+iface. The missing
cell is **producer child + parent port (lazy)** — exactly the tbExternal
boundary, where the up side is an inherited `<DUT>Inverted` OUT port that binds
after construction.

Added the fourth constructor to all **seven** protocol thunker headers: the six
in base (`push_ack`, `rdy_vld`, `req_ack`, `apb`, `axi_read`, `axi_write`) plus
`lmmi` in `builder/pro/interfaces/lmmi/` (the structural twin of `apb`). Each is
purely additive — new overload, a new `m_up_out_port` member (nulled in the three
existing constructors), and one lazy-resolve line in `thunkOut()`
(`m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->()`), plus an
updated 2×2-family class comment. All seven shared the identical three-shape
family with the same gap. No existing call site matches the new overload, so
current projects are unaffected. (The pro `lmmi` header is easy to miss — it lives
outside the base `interfaces/` tree.)

### Part A — classify the pruned DUT-boundary end (`processYaml.py`)

`getBDCrossInterfaceBinds` now also walks `ret['prunedConnections']` and runs the
existing `annotate(...)` classifier over each pruned connection's surviving
(non-excluded) end, attaching the same `crossInterfaceEnds` annotation the
`connectDouble` path produces. The excluded DUT end's `Config` selection is
captured at prune time (`excludedEndConfig`) and passed to `annotate` via a new
`parentConfigOverride` so the parent (up) type resolves to the DUT's `<Config>`.

### Part B — iterate the pruned bucket (`intf_gen_utils.py`)

`sc_declare_thunkers` and `sc_thunker_protocols` now also iterate
`data['prunedConnections']`, using the same `_resolve_cross_interface_ends` walk,
member-declaration, and protocol-include emission as the `connectDouble` loop.

### Part C — emit and bind at the boundary (`testbench.py`)

- `ext_sec_init` constructs a boundary thunker per cross-interface pruned end;
  the overload resolves by direction (connectionMap/consumer shape for consumer
  ends, shape 4 for producer ends), binding the child port through the thunker to
  the inherited `<DUT>Inverted` parent port.
- `ext_sec_body` suppresses the raw bind for cross-interface pruned ends **only**
  (non-cross-interface pruned ends keep the raw bind unchanged).
- `ext_sec_header` **imports** a parameterizable child's Base module instead of
  forward-declaring it (the RTTI fix from §2).

---

## 4. Authoring contract (unchanged, still required)

`annotate` classifies a bind as cross-interface **only when the child's declared
port interface name differs** from the connection's interface name
(`processYaml.py`: `if not childInterfaceName or childInterfaceName ==
parentInterfaceName: return None`). A pure same-interface, subset-`<Config>` DUT
does **not** trip this test. The module owner must therefore declare a distinct
**non-parameterized boundary interface** on the stimulus/sink side, exactly as the
hierarchical fixture does (`ip_top.yaml:106` `srcOut0BoundaryIf`) and as `xif`
does (`streamBndryIf` / `streamBndrySt`):

- declare a non-parameterized boundary interface + struct;
- give `src` / `sink` explicit stream ports on that boundary interface;
- keep the DUT port on its parameterized interface;
- drop `H`/`V` from the DUT config, keep them on src/sink.

The packed layout of the boundary struct and the resolved `<dutConfig>` struct
must be identical — the thunk is a reinterpretation between two identically-laid-out
packed structs. The db-time compatibility check gates this; the fix does not
weaken it.

> **Documentation follow-up:** this authoring contract should be written into the
> testbench / parameterization skill so owners know the boundary interface is a
> required declaration, not optional.

---

## 5. Verification (done)

- **RED → GREEN on `examples/xif`.** New model-only example: subset-parameterized
  DUT (`dut`, `[DATA_WIDTH]`, ports on `dutStreamIf` / `streamSt<Config>`) driven
  by superset-parameterized `src`/`sink` (`[DATA_WIDTH, FRAME_HEIGHT, FRAME_WIDTH]`)
  whose ports are on the plain differing-name boundary `streamBndryIf` /
  `streamBndrySt`; connections on `dutStreamIf`; `uDut` is the `--excludeInst`. The
  two boundary binds land in `prunedConnections` — one producer end, one consumer
  end — exercising **both** thunker directions. Pre-fix: the verbatim RED above.
  Post-fix: thunker binds emitted, raw binds gone, `push_ack_port_thunker.h`
  include present, `make run` → "No error" (sink `Q_ASSERT` on the thunked payload
  passes across all 16 items).
- **No-regression.** Full base+pro example suite regenerates **byte-identical**
  (the new constructor is additive; the view/emission changes are inert wherever no
  pruned cross-interface boundary exists and no parameterized child sits in a tb
  External). Unit suite **82/82** (incl. `test_thunker_view.py`,
  `test_boundary_signals.py`).

---

## 6. Rollout

The accurate-footprint (H/V-dropped) configuration for isp_blc, isp_ccm,
isp_gain, isp_lut, isp_rgb_gain can now be authored using the §4 boundary-interface
pattern — the same producer boundary (`raw_video_src → blc`) that shape 4 unblocks.
Independent of the BUG 1–6 workaround retirements.
