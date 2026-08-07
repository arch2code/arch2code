# Plan: Testbench File Family to C++20 Modules

Status: COMPLETE — S0, S1, S2, S3, S4, S5 all DONE, plus S6 closing the two seams S5
reported to the user (D-7, D-8). R1 (GCC) closed as a pre-existing compiler blocker,
measured and unchanged by this work.

## 1. Goal

Convert the generated testbench file family from textual `.h`/`.cpp` pairs to C++20
module interface units, and close the create-once scaffold coverage gaps that the
current split ownership hides. Five emitted files per testbench block become three.

Two outcomes are wanted, and the second is not merely cosmetic:

- Eliminate the leaked include prerequisite that forces every consumer of
  `<block>External.h` to `import a2c.endOfTest;` before including it.
- Move every piece of framework boilerplate out of create-once scaffolds and into
  generated regions, so `make gen` can revise it in an existing project.

The second goal is the steady state that [[plan-cppm-module-scaffold-sections]]
already set for context `.cppm` files: **copyright is the only non-marker file text
outside a generated region**, because any generated semantic content outside a region
drifts when module names, namespaces or dependencies change. The testbench family is
the last place that rule is not applied.

## 2. Scope

In scope (all `builder/base`):

| fileMap key | Current emission | Target |
| :--- | :--- | :--- |
| `tbExternal` | `<block>External.h` + `.cpp` | `<block>External.cppm` |
| `testBench` | `<block>Testbench.h` + `.cpp` | `<block>Testbench.cppm` |
| `tbConfig` | `<block>Config.cpp` | `<block>Config.cpp` (stays a plain TU; scaffold and regions reworked) |

Out of scope, with reasons:

- `tandem` (`builder/pro/config/project.yaml:31`, `<block>Tandem.h`/`.cpp`) — the
  fourth remaining `.h`/`.cpp` pair. Self-contained: only its own `.cpp` includes its
  header, so it has no coupling to the testbench include chain. Separate follow-on.
- `<context>VariantConfig.h` — deliberately a header. It is textually included in the
  global module fragment of every block module. Must not become a module.
- `<block>_hdl_sc_wrapper.h` — Verilator boundary.
- `<context>IncludesFW.h`/`.cpp` — C-consumable firmware, must stay textual.

## 3. Current State

### 3.1 Emission and consumption

- `builder/base/config/project.yaml:189-191` declares the three fileMap entries.
- Scaffolds (create-once, user-owned thereafter) live in
  `builder/base/templates/fileGen/fileGen.py`: `tbConfigTemplate` (460),
  `testBench_hdrTemplate` (517), `testBench_srcTemplate` (534),
  `tbExternal_hdrTemplate` (546), `tbExternal_srcTemplate` (567).
- Generated regions are rendered by `builder/base/templates/systemc/testbench.py`.
- `builder/base/pysrc/migrateOrphans.py:112-113` marks `tbConfig` and `tbExternal`
  `MIGRATE_LEAVE`: the orphan sweep must never rewrite them. (S4 changed this:
  `testBench` is now `MIGRATE_DELETE` and `tbExternal` `MIGRATE_PORT`; `tbConfig` is
  `MIGRATE_EDIT`, the disposition D-9 renamed from `MIGRATE_LEAVE`. The `ext` values
  stayed on the frozen legacy pair.)
- The include chain is `Config.cpp` -> `Testbench.h` -> `External.h`.
- The `--block=<tb_block> --excludeInst=<dut>` form of the External file's
  `GENERATED_CODE_PARAM` is a documented user edit (see the `verify-testbench` skill).
  The scaffold seeds `--block=<dut>`; the user retargets it at the `_tb` container.
  Module identity must therefore be resolved at gen time, not scaffold time.

### 3.2 Defects found

**D1 — The External header declares a dependency it does not satisfy.**
`sec_tb_external_header_template` defines `eotThread()` inline in the class body
(`testbench.py:541`) and that body names `endOfTestState`, which is available only
from the module `a2c.endOfTest` (`builder/common/systemc/endOfTest.cppm`). No header
provides it, and no `<block>Base.cppm` re-exports it (verified). Every TU that includes
`<block>External.h` must therefore import the module first. The generator satisfies
this by emitting the import immediately before the include, at `testbench.py:113`/`129`
(External) and `testbench.py:463-464` (Testbench). This is the root defect; D2 and D3
are its consequences.

The hazard is not hypothetical: `lmmiDemoExternal.cpp` includes the header at slot-0
with **no** preceding import, which is the unsafe ordering. It cannot be observed as a
compile failure today because `lmmiDemo` fails earlier for an unrelated reason (see
section 4). Once that is fixed, `lmmiDemo` is the natural regression witness for D1.

**D2 — Duplicated preamble in 15 of 16 base and pro examples.**
Every `<block>External.cpp` except `builder/base/examples/simple` carries a hand-added
`import a2c.endOfTest;` plus `#include "<block>External.h"` above the scaffold's
`#include "workerThread.h"`, duplicating what the `init` region now emits. It is
historical residue from the endOfTest module migration, silenced by the include guard.
It is fragile rather than merely untidy: deleting only the duplicated `import` while
keeping the duplicated `#include` breaks the build, because the header is then expanded
before the import is seen.

**D3 — A freshly scaffolded `Config.cpp` does not compile.**
`tbConfigTemplate`'s scaffolded `final()` body calls
`endOfTestState::GetInstance().isEndOfTest()` but the scaffold emits no
`import a2c.endOfTest;`. This is the *only* missing prerequisite — `Q_ASSERT_CTX`,
`errorCode` and `is_default_testbench_v` all arrive transitively through
`testBenchConfigFactory.h` -> `testBenchConfigBase.h` -> `logging.h` -> `q_assert.h`.
Confirmation: all 16 examples carry exactly that one line hand-added.

**D4 — The Config registration definition is untemplated.**
`tbConfigTemplate` ends with, in the create-once scaffold:

```
};
__tbclassname__Config::registerTestBenchConfig __tbclassname__Config::registerTestBenchConfig_;
```

That definition is the mandatory pair of the in-class
`static registerTestBenchConfig registerTestBenchConfig_;` declaration emitted by the
*generated* `tbConfig` region. Ownership of one mechanism is split across a generated
region and a file the generator may never touch again, so the registration mechanism
cannot be revised in any existing project. `Config` is the last member of the family
still on this pattern: the testbench top (`sec_tb_class_init_template`) and the block
registrars both moved to an `A2C_REGISTRATION_RETAIN` anonymous-namespace static
emitted wholly inside a generated region.

**D5 — Framework prerequisite includes sit in create-once scaffolds.**
`systemc.h`, `<string>`, `instanceFactory.h`, `testBenchConfigFactory.h` (Config);
`systemc.h`, `logging.h` (External header); `workerThread.h` (External source). All are
unconditional framework baseline, none is a user choice, and none can be corrected by
`make gen`. Contrast the block family, where `moduleScaffold --section=blockModuleHeader`
generates the entire baseline (`moduleScaffold.py:40-70`).
CORRECTION: `workerThread.h` was misclassified here — it is NOT baseline. See post-review
fix 5 below; the other five entries stand.

**D6 — A stale comment is fossilised in a create-once scaffold.**
`tbConfigTemplate`'s `createTestBench()` comment states the registration static lives
in `<block>Testbench.cpp`. It is already imprecise and becomes wrong once that file is
a `.cppm`. Being create-once, it can never be corrected in an existing project.

**D7 — The External header has no user-slot anchor.**
Between `GENERATED_CODE_END` and the scaffold's `};` there is no marker comment. The
block scaffold has `// block implementation members` in the equivalent position
(`fileGen.py:182`). The migration porter needs a stable anchor.

**D8 — Child Base forward declarations are safe only in the global module.**
`ext_sec_header` forward-declares the Base class of each non-parameterizable child
(`class apb_decodeBase;`) and relies on the `.cpp` importing that child's Base module
to complete it. The comment at `testbench.py:296-305` records exactly why this works: a
global-module forward declaration merges with the module's exported class, whereas a
declaration in a *module purview* is a distinct entity, producing mismatched RTTI and a
null `dynamic_pointer_cast`. Under the merge this branch must be removed and all
children reached by `import <child>.base;`. Overlooking it yields a silent runtime null
cast, not a compile error.

**D9 — The seeded slot comments do not state the rules they exist to enforce.**
`blockModule_cppm` and `blockRegsModule_cppm` seed exactly `// user #includes here`
(`fileGen.py:175`, `205`) and `// user imports here` (`178`, `208`). Five words each,
with no statement of which zone the slot is, what the content attaches to, or that
imports must precede includes within the second slot. The rich explanations in
`model/raw_video_src.cppm` and `model/rgb_video_sink.cppm` are **hand-written**, not
scaffolded, so a developer creating a new block today gets no guidance at the one moment
the decision is made. The tb scaffolds seed no slot comment at all (D7). Since the whole
5.2 contract is invisible at the point of use, this is a primary cause of the difficulty
rather than a cosmetic gap.

Two exact-text couplings constrain the fix:

- `pysrc/migrateModuleHeader.py:60-64` (`_INSERT`) is documented as "byte for byte the
  fresh-scaffold shape". Its seeded `// user imports here` line must change in lockstep,
  or a migrated file stops being byte-identical to a fresh scaffold — a requirement the
  block-module plan locked as its D1. Idempotency itself is keyed on the presence of the
  `moduleExport` region, not the comment text, so it is unaffected.
- `pysrc/migrateBlockModulePort.py:83` (`_IMPL_MEMBERS_COMMENT`) matches
  `// block implementation members` by exact string equality to drop the scaffold
  comment during a class-body transplant. Change that string in only one place and the
  porter silently duplicates it.

### 3.3 Verified against the updated tree (2026-08-05)

The tree was advanced to `ad6c510` (builder `7fb9055`, "#116 release 2.0"). Re-checked:

- **All nine defects above are still present**, unchanged, in the latest code. The
  duplicated `import a2c.endOfTest;` / `#include "debayerExternal.h"` pair sits at
  `tb/debayer/debayerExternal.cpp:1-2` against the generated `:7`/`:12`, and the
  untemplated registration definition is still `tb/debayer/debayerConfig.cpp:106`.
- `make gen -j8` succeeds and modifies **nothing** under `tb/` or `model/`, so
  generation is stable and the plan is written against current emission.
- `rundir` builds clean. The only warnings are two pre-existing ones in
  `model/interpolate.cppm` (an unneeded internal declaration at `:164` and a sign
  comparison at `:683`), unrelated to this work.
- The 5.2 contract is being followed correctly by the two model modules that exercise
  it. Both pimpl boundaries (`b2p_deb_conv_impl.h`, `rgb_img_writer_impl.h`) are in the
  GMF and **carry include guards**, which is what keeps them attached to the global
  module when the purview wrapper includes them a second time in the same TU. Both
  purview wrappers (`b2p_deb_conv.h`, `rgb_img_writer.h`) genuinely name `Config` types,
  and in both files `import a2c.endOfTest;` precedes the purview includes.

One inconsistency found, latent rather than broken:

- **F1 — `raw_video_src_config.h` is in the wrong slot.** It sits in the *purview* slot
  of `model/raw_video_src.cppm:32`, while its structurally identical twin
  `rgb_video_sink_config.h` sits in the *GMF* slot of `model/rgb_video_sink.cppm:23`
  with a comment stating why the GMF is correct. Both are plain classes over
  `#include <string>` naming no module or `Config` type, so by the 5.2 rule both belong
  in the GMF. It compiles today only because exactly one TU includes it, so there is no
  second attachment; `debayerConfig.cpp:78` reaches `m_config.use_rgb_file` without
  naming the type, which the reachability rule permits. The moment any other TU includes
  that header textually, it becomes the L1 attachment clash. Moving it to the GMF slot
  is a one-line user-code fix.
- Minor: `b2p_deb_conv.h`, `rgb_img_writer.h` and both `*_config.h` have no include
  guard. Safe today because each is included once per TU, but an unguarded header is a
  poor fit for a zone-sensitive slot.

## 4. Prerequisite: the pro layer was left behind by the endOfTest conversion

Discovered while validating this plan (2026-08-05). `endOfTest.h` was deleted when it
became `endOfTest.cppm`, but three live files still include it:

- `builder/pro/common/systemc/inPlaceList.h:10` — a **shared pro framework header**.
  Currently dormant: no live file in the tree includes `inPlaceList.h`, so it breaks
  nothing today and is a trap for the first pro project to use `inPlaceList`.
- `builder/pro/examples/lmmiDemo/model/lmmi_m_drv.cppm:14`
- `builder/pro/examples/lmmiDemo/tb/lmmiDemo/lmmiDemoConfig.cpp:8`

Measured state: `builder/base/examples/simple` builds clean from `make clean`, so the
base suite baseline is good. `lmmiDemo` fails at
`lmmi_m_drv.cppm:14:10: fatal error: 'endOfTest.h' file not found`.

This is the B3/B5 lesson from the block refactor recurring — the sweep covered base and
the pro layer was not carried through. It is **blocking for the S5 gate**, which
requires the pro suite to build, and it must be fixed before S5 regardless of this
plan. It is not otherwise part of this work.

The 50-odd other hits for `endOfTest.h` are all under `isp_shared/builder/`, which is a
vendored older checkout of the builder, not live code.

## 4a. `inPlaceList.h` — OUT OF SCOPE, owned elsewhere

Resolved 2026-08-05: the header is heavily used in another project, and the user will
convert it there if it needs converting. It is not part of this plan and not part of S0.
Leave `builder/pro/common/systemc/inPlaceList.h:10` as it stands.

The "nothing in the live tree includes it, so no build can validate a fix" measurement
below was scoped to this workspace only and must not be read as the header being dormant.
The real consumer base is outside this tree, which also voids the argument that a
consumer-visible contract change is cheap here — it is not ours to price. The analysis is
kept only because the zone constraint it records (a GMF-zone header admits no
import-declaration, and `endOfTestState` is non-dependent in a class-template member, so a
forward declaration will not serve) is the same constraint that will govern whoever does
convert it.

### Prior analysis, retained for the constraint it records

Measured (2026-08-05): the only endOfTest use is `inPlaceList<T,N,S>::prt()` at
`inPlaceList.h:189`, `endOfTestState::GetInstance().isEndOfTest()`, gating one
resource-leak warning string. `endOfTestState` is a non-dependent name in a class
template member, so it must be *declared before* the template definition; a forward
declaration is not enough because the body calls its members. No other pro or base header
references endOfTest, and nothing in the live tree includes `inPlaceList.h`, so no build
can validate a fix.

An `import` cannot go in the header: `inPlaceList.h` sits alongside `q_assert.h`,
`log.h`, `synchLock.h`, `blockBase.h`, i.e. it is a GMF-zone header, and the GMF admits
no import-declaration. Every remaining option changes something a consumer sees:

| Option | Cost |
| :--- | :--- |
| Drop the include; require the consumer to `import a2c.endOfTest;` before including | Adds a leaked include prerequisite to the header's contract — exactly the defect §1 of this plan exists to remove for `<block>External.h`. Matches current base practice though. |
| Convert to `inPlaceList.cppm` (`export module a2c.inPlaceList;`) | Consumers move from `#include` to `import`. Also puts three exported class templates through the exported-template/internal-linkage rule (L4). Aligns with the plan's direction. |
| Keep the header plain; add a non-inline `bool` eot query declared in the header and defined in a new plain TU that imports `a2c.endOfTest` | No consumer-visible contract change for GMF use, but adds framework API and a TU for a header with zero current callers, which the builder simplicity rules discourage. |

## 5. Learnings Carried Forward from the Block-Module Refactor

These are binding constraints, not background. Sources:
[[plan-block-module-3section]], [[plan-cppm-module-scaffold-sections]],
[[plan-item5-port-mechanization-assessment]], `docs/vcs-build.md`.

### 5.1 The three-zone rule — every piece of content has exactly one legal home

| Content | Zone | Rule | Attaches to |
| :--- | :--- | :--- | :--- |
| Non-modular shared `#include` | **GMF** (before `export module`) | includes/preprocessor only | **global module** |
| `export module X;` | boundary | after all includes, before all imports | — |
| `import` (any kind) | **preamble** (after `export module`, before first non-import) | all imports grouped here | (imported) |
| `using namespace`, class, definitions | **purview** (after imports) | anything | **module X** |

Consequences that must be designed for, not discovered:

- **L1 — the attachment clash.** A non-modular shared header included in the *purview*
  attaches its declarations to that module. Any plain TU that both imports the module
  and textually includes the same header then sees one entity attached two ways:
  `declaration '…' attached to named module '…' cannot be attached to other modules`.
  This is precisely why the GMF user slot exists. Note that
  [[plan-block-module-3section]] named *this file family* as the victim in its worked
  example ("the tb-config via a generated `External.h`").
- **L2 — `using namespace` closes the preamble.** A generated using-directive left at
  the tail of a `moduleExport` region makes the following `// user imports here` slot
  illegal for a body-only `import`. The block work fixed this by moving the usings to
  the `classDecl` region head, keeping `moduleExport` import-only. The External and
  Testbench regions must follow the same rule: **`moduleExport` ends import-only**.
- **L3 — the user-injection contract (see 5.2).** Two seeded slots,
  `// user #includes here` and `// user imports here`, are not interchangeable and the
  second is dual-purpose. Both are mandatory in the new scaffolds, and the contract
  below must be reproduced exactly.
- **L4 — exported templates and internal linkage.** An exported template that
  references an internal-linkage entity is ill-formed and GCC enforces it. Generated
  constants are therefore `inline constexpr`, never namespace-scope `const`
  (`docs/vcs-build.md` §C). Already fixed globally; listed so it is not reintroduced.

### 5.2 The user-injection contract — users must be able to add both headers and imports

This is the part that was painful to establish and is now encoded in the block
templates. A user must be able to add a `#include` **and** an `import`, and the slot is
chosen by what the header attaches to, not by convenience. Both live examples are in
the `debayer` tree (`model/raw_video_src.cppm`, `model/rgb_video_sink.cppm`).

| User content | Slot | Reason |
| :--- | :--- | :--- |
| Header whose definitions live in a plain global-module TU (a pimpl boundary such as `b2p_deb_conv_impl.h`, `rgb_img_writer_impl.h`) | `// user #includes here` (**GMF**) | Its class must attach to the **global module** so it matches those `.cpp` definitions at link time. |
| Header naming no module or `Config` types (a plain config class such as `rgb_video_sink_config.h`) | `// user #includes here` (**GMF**) | Nothing forces module attachment; the GMF keeps it shared. |
| Module `import` (for example `import a2c.endOfTest;`) | `// user imports here`, **first** | Still inside the preamble, where imports are legal. |
| Header that *names* module or `Config` types (a template wrapper such as `b2p_deb_conv.h`, `rgb_img_writer.h`) | `// user imports here`, **after the imports** | It must attach to **this** module and needs the preceding imports already visible. |

Two invariants make the second slot work, and both are easy to break:

- **Imports before includes, within that one slot.** A `#include` is a non-import
  declaration, so the first one **closes the preamble**. Any `import` placed after it is
  ill-formed. The seeded slot is therefore ordered: imports, then purview includes.
- **The slot must open before the first using-directive.** `classDecl` emits the context
  `using namespace` lines at its region head precisely so this slot is reachable; that
  is the same rule as L2 seen from the user's side. A generated using-directive above the
  slot would make it unusable for an `import`, which is the historical failure the block
  restructure fixed.

There is deliberately **no** fourth slot below the using-directives. A header needing
the using-directives already visible would be relying on unqualified lookup into an
imported module, which is not a shape this generator emits.

### 5.3 Migration mechanics — what the tool may do and what needs judgment

- **L5 — `codeText` gives boundaries, not slot-keyed text**
  (`pysrc/textfileHelper.py`). `sections` is one dict per `GENERATED_CODE_BEGIN` with
  the raw `command`; `ungeneratedSections` is the N+1 spans around them, and **each span
  embeds the bracketing END line at its head and the next BEGIN line at its tail**. A
  porter must correlate by the `--template=`/`--section=` in `command`, then strip the
  embedded marker lines and any trailing `};`. There is no "user region for template X"
  accessor and one must not be invented in a template utility.
- **L6 — marker insertion places old user text in the right zone for free.** Inserting
  the new region markers *below* the old header region leaves the pre-existing user gap
  above `moduleExport`, i.e. in the GMF zone, so an existing non-modular `#include`
  lands in the GMF slot automatically. Use the same trick; only stray `import` lines
  need to move down.
- **L7 — a missed slot is silent user-code loss.** The block port enumerated four slots
  and required all four to move. The equivalent enumeration for this family is section
  6.2, and it must be complete before any file is rewritten.
- **L8 — regenerate-not-port is a distinct, cheaper path.** Reg-handlers held no user
  code, so the block work deleted the legacy pair and let `make gen` recreate the
  `.cppm` rather than running the slot procedure. The tell is an empty user slot. This
  applies directly here (section 6.2).
- **L9 — flag, do not auto-rewrite, an `#include` that should become an `import`.**
  Mechanical rewriting of user includes was explicitly rejected.
- **L10 — a child project must be regenerated in its own project**, not through its
  parent. Sixteen stale files across three composed sub-projects were the cost of
  learning this (B3).
- **L11 — deleting a header strands dependency files.** After `endOfTest.h` was
  deleted, `.d` files naming it broke the next build until `rundir/build` was removed
  (B4; `BIN_DIR` now lives in `a2c-common.mk` so the shared `clean` owns it). This plan
  deletes two headers per testbench block, so **every migrated project must `make
  clean`**, not an incremental rebuild. Confirmed live: `lmmiDemo` first failed with
  `No rule to make target '.../endOfTest.h', needed by '.../lmmi_m_drv.pcm'` and needed
  a clean before the real error surfaced.
- **L12 — golden/emit expectation churn is expected.** Update bucket-A expectations
  that encode the old file shape; never weaken an assertion to make it pass.
- **L13 — retry regen and Verilator flakes once from clean before diagnosing**, and do
  not kill the unit runner under a short timeout.

## 6. Target Design

### 6.1 `<block>External.cppm`

Merges `External.h` and `External.cpp`. Follows the block-module seam pattern
(`fileGen.py::blockModule_cppm`, 169-189) exactly — including the convention that the
scaffold, not the generated region, owns the closing `};` so the user keeps an in-class
slot and an in-constructor-body slot (decision D-3):

```
//<copyright>

// GENERATED_CODE_PARAM --block=<block> --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
// GENERATED_CODE_END
// user #includes here                        <- L3 (GMF)
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
// GENERATED_CODE_END
// user imports here                          <- L3 (preamble)
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

    // GENERATED_CODE_END
    // external implementation members        <- fixes D7

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
    // GENERATED_CODE_END
};
```

Region content changes:

- New `moduleScaffold --section=tbExternalModuleHeader` owns the GMF: the
  `systemc.h`/`logging.h` baseline, `workerThread.h`, the channel and thunker headers,
  and the Config header. Fixes D5. (`workerThread.h` was later removed from this region —
  post-review fix 5.)
- `moduleExport` gains the `a2c.endOfTest` import and every child `.base` import,
  unconditionally, for parameterizable and non-parameterizable children alike. Fixes D1
  and D8. It must end **import-only** (L2); the context using-directives stay at the
  `tbExternal --section=header` region head, mirroring `classDecl`.
- `ext_sec_header` loses its `#include`/forward-declaration emission entirely and emits
  only the usings plus the class. `ext_sec_init` loses the `import a2c.endOfTest;` and
  `#include "<block>External.h"` lines at `testbench.py:113` and `129`.

Slot semantics are the 5.2 contract verbatim, and the External is a realistic consumer
of every row of it: a testbench External is exactly where a user reaches for a
non-modular stimulus helper, a file reader or a scoreboard header. Concretely it must
support all four placements — a pimpl-boundary or plain header in the GMF slot, an
`import` first in the preamble slot, and a header naming DUT `Config` types after that
import in the same slot. The two seeded comments keep the **same text** as the block
scaffold (`// user #includes here`, `// user imports here`) so one rule covers both
families; the decision table itself belongs in the `verify-testbench` skill, which today
documents `--excludeInst` but says nothing about module zones.

### 6.2 Slot inventory — measured, and it makes the port cheaper than the block port

Surveyed across all 17 instances (16 examples plus `debayer`):

| File | User slot | Instances non-empty | Disposition |
| :--- | :--- | :--- | :--- |
| `External.h` | class body (after header END, before `};`) | 6 of 17 | **port** |
| `External.cpp` | ctor init-list (between init END and body BEGIN) | 1 of 17 (`debayer`) | **port** |
| `External.cpp` | ctor body + out-of-line tail (after body END) | 5 of 17 | **port** |
| `External.cpp` | slot-0 (file preamble) | 16 of 17 | **drop** (fixed list) |
| `Testbench.h` | after END, before `#endif` | **0 of 17** | regenerate-not-port |
| `Testbench.cpp` | after last END | **0 of 17** | regenerate-not-port |

Two measurements materially de-risk this:

- **`testBench` is entirely generated in every instance.** Every `Testbench.h` user slot
  is empty and every `Testbench.cpp` ends exactly at its final `GENERATED_CODE_END`.
  This is L8: delete the pair, let `make gen` create the `.cppm`, no slot procedure.
  One of the two porter branches disappears.
- **External slot-0 is a closed boilerplate set with no user content.** Enumerated
  across all 17 files it is only ever these four lines, in this order, with some
  omitted: an optional copyright comment; `import a2c.endOfTest;`;
  `#include "<block>External.h"`; `#include "workerThread.h"`. It is a fixed set, so the
  slot-0 triage that [[plan-item5-port-mechanization-assessment]] flagged as the one
  non-deterministic case does not arise here. (Three of the four are dropped; post-review
  fix 5 relocates `workerThread.h` to the GMF user slot instead.)
- **No External user slot contains any `import` or `#include`.** Verified across the
  suite for both the class-body slot and the ctor/tail slot. The de-risking fact the
  block port relied on holds here too, so moving the slots loses no dependency
  information and L9 triage is not needed.

Note that user slots do consume module entities — `ipExternal.h` declares
`endOfTest eot_{true};` as a class member. That member ends up in the purview and
resolves through the generated preamble import, which is exactly what 6.1 provides.

### 6.3 `<block>Testbench.cppm`

Regenerate-not-port per 6.2. Same three-zone shape; imports `<qualified>.external`.
`sec_tb_class_init_template` loses its `import a2c.endOfTest;` and
`#include "<block>Testbench.h"` head (`testbench.py:463-464`); the
`A2C_REGISTRATION_RETAIN` registration block it already carries is unchanged.

Both 5.2 slots are still seeded even though no project uses them today. The file is
100 percent generated only by measurement, not by design — a user may legitimately add
a scoreboard include or an import here — and a scaffold that omits the slots would force
that user into a zone-illegal placement, which is the whole class of failure this work
exists to remove.

### 6.4 `<block>Config.cpp`

Stays a plain translation unit (decision D-1). The measured evidence is decisive, not
merely ergonomic: every `Config.cpp` slot-0 **interleaves** user `#include`s and user
`import`s. `ip_topConfig.cpp` is includes, then `import a2c.endOfTest;`, then
`testController.h`/`workerThread.h`/`fwModelMain.h`/`ipVariantConfig.h`, then
`import ip;`. That interleaving is legal in a plain TU and illegal in a module unit,
where the includes must precede `export module` and the imports must follow it. Making
Config a `.cppm` would mean rewriting hand-written user code in 16 projects for no
functional gain, and it is a leaf that nothing imports.

Stated as a contract: in `Config.cpp` there are **no zone rules**. A user may interleave
`#include` and `import` freely in any order, which is the one place in the family where
that is true. The single seeded slot is therefore
`// user #includes and imports here`, deliberately worded differently from the two
module-unit slots so the distinction is visible in the file rather than only in
documentation.

Two changes:

```
// <copyright>

// GENERATED_CODE_PARAM --block=<block> [--variant=<v>]
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites   <- NEW, fixes D3/D5
// GENERATED_CODE_END
// user #includes and imports here
// GENERATED_CODE_BEGIN --template=tbConfig --section=class
// GENERATED_CODE_END

    ... user overrides: addProgramOptions / handleProgramOptions /
        createTestBench / final ...

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration    <- NEW, fixes D4
// GENERATED_CODE_END
```

- `--section=prerequisites` emits the framework baseline (`systemc.h`, `<string>`,
  `instanceFactory.h`, `testBenchConfigFactory.h`) plus `import a2c.endOfTest;`.
- `--section=registration` replaces the untemplated out-of-class static with the same
  `A2C_REGISTRATION_RETAIN` anonymous-namespace pattern the testbench top and the block
  registrars already use, so the whole mechanism lives in one generated region. The
  in-class `static registerTestBenchConfig registerTestBenchConfig_;` declaration is
  dropped from `--section=class` in the same change; declaration and definition must
  move together.
- The stale `createTestBench()` comment (D6) is corrected in the scaffold rewrite. New
  projects get the accurate text; existing projects keep their copy. That residual is
  the whole reason nothing else is left in a create-once scaffold.

### 6.5 Module naming

Two new spelling helpers in `intf_gen_utils.py`, mirroring `cpp_base_module_name`
(377) and `cpp_block_module_name` (368):

- `cpp_tb_module_name(blockName)` -> `<block>.testbench`
- `cpp_tb_external_module_name(blockName)` -> `<block>.external`

Both take the block identity from the view field `data['blockModuleName']`, never from
a filename, path or stem — the rule [[plan-cppm-include-contract-cleanup]] was written
to enforce. For the External unit that field is the one `refactor_tbExternal` resolves
from the excluded DUT instance (`dutInst['instanceTypeModuleName']`,
`testbench.py:410-422`), which keeps the module name aligned with the class-name family
when the file's `GENERATED_CODE_PARAM` targets the `_tb` container rather than the DUT.

`gen_cpp_module_map.py` fails hard on duplicate providers, so owner-qualified names are
mandatory, not stylistic.

### 6.6 Infrastructure impact: none expected

- Build: `a2c-systemc.mk:97-101` already discovers `*.cppm` by wildcard across
  `PRJ_SRC_DIRS` (set from `A2C_SC_SRC_DIRS` at `a2c-systemc.mk:52`), and `tb/<block>`
  is already a member. Module scanning, pcm/CMI ordering and object linking are generic.
  No makefile change is anticipated; this is a stage gate, not an assumption.
- Registration: under the project's direct-`.o` link model the initialiser runs
  unconditionally (`instanceFactory.h:12-30`). Module linkage does not change this.
- Verilator: orthogonal. The verilated wrapper header and the DUT factory path do not
  touch the testbench file family.

## 7. Implementation Stages

Each stage ends at a stop gate. Do not begin the next stage until the gate is closed.

**S0 — Unblock the pro layer.** DONE (2026-08-05) except `inPlaceList.h`. Fix the three
stale `endOfTest.h` includes in section 4.
Independent of this plan but blocking its S5 gate.
*Gate:* `lmmiDemo` builds and runs from `make clean`. — CLOSED: `make clean && make gen`,
then `make` and `make run` in `rundir`, all clean ("No error").

Landed: `lmmi_m_drv.cppm` (GMF include → `import a2c.endOfTest;` in the `// user imports
here` slot), `lmmiDemoConfig.cpp` (include → import). Two further pro-layer leftovers
found by the gate and fixed: `lmmiDemoExternal.cpp` did not compile at all (it included
`lmmiDemoExternal.h`, whose inline `eotThread()` names `endOfTestState`, with no
preceding import — every other example has the import first), and
`lmmiDemo/rundir/Makefile` was missing the `EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp`
opt-in that the BSP relocation requires (`modelComm.h` not found).

`builder/pro/common/systemc/inPlaceList.h:10` is still unfixed and deliberately so — see
section 4a.

**S1 — Naming helpers and fileMap flip.** DONE (2026-08-05).
Add the two `intf_gen_utils` helpers. Change `tbExternal` and `testBench` to
`ext: {cppm: "cppm"}` in `builder/base/config/project.yaml` and in the duplicated copy in
`pysrc/newProject.py:81-82`, which must stay in step. `pysrc/migrateOrphans.py:112-113`
is NOT a copy of the current map and must not be flipped — see the correction below.
*Gate:* `make db` succeeds on `builder/base/examples/simple`; the change is reflected
in `.gen/build.mk`. — CLOSED: `make clean && make db -j8` exit 0; `.gen/build.mk` now
lists `tb/simple/simpleExternal.cppm` and `tb/simple/simpleTestbench.cppm` in both
`A2C_CPP_MODULE_FILES` and `A2C_SC_GEN_FILES`, replacing the four `.h`/`.cpp` entries.

Landed: `cpp_tb_module_name` / `cpp_tb_external_module_name` in `pysrc/intf_gen_utils.py`
(both take `data['blockModuleName']`, mirroring `cpp_base_module_name`); the ext flip in
`config/project.yaml`, `pysrc/newProject.py` and `pysrc/migrateOrphans.py` (dispositions
unchanged — `tbConfig` and `tbExternal` stay `MIGRATE_LEAVE`).

**Correction — S1's "all three must stay in step" was wrong.**
`pysrc/migrateOrphans.py::LEGACY_FILEMAP` is not a third live copy of the current fileMap.
Its own header states it is captured verbatim from `main`, the pre-migration layout, so the
sweep classifies against a FROZEN legacy map rather than the evolving merged map; the same
header's omission rule ("an entry only earns its place by giving the sweep a legacy form to
act on") means an entry whose legacy form equals its current form does not belong at all.
Flipping the tb entries to `cppm` therefore both erased the legacy on-disk form and made the
entries self-cancelling. The two `ext` values were reverted to `{hdr: h, src: cpp}`, along
with the two `test_migrate_orphans.py` lines that staged and asserted the `.cppm` name;
`test_migrate_orphans.py` re-run PASS (21 checks, 0 failures). The fixture's manifest fix
(`tb` → `tb/myblk`) was kept: the tb entries are `blockDir`, so a real `.gen/build.mk`
lists `tb/<block>`, not the `tb` segment root.

Dispositions are now S4's decision, not S1's, and they must change there: after the flip the
legacy `.h`/`.cpp` pair IS a legacy form the sweep can see, so `MIGRATE_LEAVE` no longer
describes either entry. `tbExternal` becomes `MIGRATE_PORT` (identify and report, never
delete — the porter moves the user slots), and `testBench` becomes `MIGRATE_DELETE` on the
D-4 evidence that it carries no user code in any of the 17 instances. Getting this backwards
deletes user code, so it is a stop-gate item for S4, not a detail.

A **fourth** copy of that fileMap block exists and was deliberately left alone:
`unittest/fixtures/hier-layout/prj/yaml/hierProject.yaml:22-24` overrides the tb entries
at project level. It is a user-YAML override, which the generator must keep supporting,
so the fixture and its golden stay on the legacy shape until S5; the test passes
unchanged. `examples/nested` has no such override, so its `expected_tree.golden` was
updated to the two `.cppm` names (L12).

**S2 — Scaffold rewrite, including the slot comments (D9).** DONE (2026-08-05).
Replace `tbExternal_hdrTemplate`/`tbExternal_srcTemplate` with a single
`tbExternal_cppm`, and `testBench_hdrTemplate`/`testBench_srcTemplate` with a single
`testBench_cppm`, both seeding the two L3 user slots. Rework `tbConfigTemplate` per 6.4.

Rewrite the seeded slot comments so the 5.2 rule is stated where the decision is made,
in both the new tb scaffolds and the existing `blockModule_cppm` /
`blockRegsModule_cppm`, so one wording covers every module unit. Keep them short and
behaviour-explaining — the zone, what the content attaches to, and the ordering
invariant — for example:

```
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
```
```
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
```

Both D9 couplings must be honoured in the same change: update
`migrateModuleHeader._INSERT` in lockstep so a migrated file stays byte-identical to a
fresh scaffold, and leave `migrateBlockModulePort._IMPL_MEMBERS_COMMENT` and the
`// block implementation members` scaffold string in agreement.

*Gate:* `make newmodule` on a scratch copy of `simple` produces three files whose shape
matches 6.1/6.3/6.4, whose only non-marker text outside a generated region is the
copyright line and the seeded user slots, and whose slot comments state the rule. Run
`make migrate` on an already-migrated project and diff a restructured file against a
fresh scaffold to prove byte-identity survived the comment change.
— CLOSED, both parts:

1. `make newmodule` on a scratch copy of `simple` (scaffolds deleted first) emitted
   `simpleExternal.cppm` (24 lines), `simpleTestbench.cppm` (16) and `simpleConfig.cpp`
   (30), each matching 6.1/6.3/6.4 marker for marker. Outside the generated regions the
   only text is the copyright line, the seeded slots, `// external implementation
   members`, the D-3 scaffold-owned `};` seams, and — in `Config.cpp` alone, which is
   not a module unit — the four overridable bodies 6.4 keeps there.
2. Byte-identity: the fresh `blockModule_cppm` scaffold was reduced to the legacy
   single-region shape by removing exactly `migrateModuleHeader._INSERT`, then
   `migrateModuleHeaderInProject(..., write=True)` was run over the project; the result
   compares **byte-identical** to the fresh scaffold (one `MODULE_HEADER_RESTRUCTURE`
   applied, no manual items). `migrateYaml.py --write` re-run on the already-migrated
   project reports "block module headers already three-section; nothing to do", exit 0.

Landed in `templates/fileGen/fileGen.py`: `tbExternal_cppm` and `testBench_cppm` replace
the four `.h`/`.cpp` skeletons (both built as `out.append` functions like
`blockModule_cppm`, sharing a `_tb_param_line` helper that carries `--mode=module` and
the `--variant` parameter); `tbConfigTemplate` reworked to `prerequisites` / `class` /
`registration` with the framework includes and the untemplated registration definition
removed and the D6 comment corrected to name the class, not a file; the two slot comments
promoted to module-level `USER_INCLUDES_SLOT` / `USER_IMPORTS_SLOT` constants consumed by
all four module-unit scaffolds. `_tb_subst` lost its two header-guard tokens.

Both D9 couplings honoured, plus a third found by grep:
`migrateModuleHeader._INSERT` reproduces `USER_IMPORTS_SLOT` verbatim (proved above);
`migrateBlockModulePort._IMPL_MEMBERS_COMMENT` and the scaffold string
`// block implementation members` were both left unchanged (the External's anchor is the
distinct `// external implementation members`); and
`migrateBlockModulePort._buildPorted` inserted sibling imports at the hard-coded
`exp.end + 2`, i.e. one line past a **single-line** label — now
`_afterCommentBlock(lines, exp.end + 1)`, which skips a seeded label of any length and
stops at the next generated-region marker, removing the line-count coupling entirely.

Intermediate state, expected and owned by S3: `make gen` fails on a project whose tb
`.cppm` have been scaffolded, with `Unknown section 'tbExternalModuleHeader'` /
`'testBenchModuleHeader'` for template `moduleScaffold`. The scaffolds also emit
`moduleExport --fileMapKey=tbExternal` and `--fileMapKey=testBench`. S3 must add both
`moduleScaffold` sections (6.3 requires the testbench top to carry the same three-zone
shape and both slots, so it needs its own GMF section, named for its fileMap key the way
`tbExternalModuleHeader` is) and teach `moduleExport` both keys.

Four things the post-coding review raised that S3/S4 must not lose:

- `--fileMapKey` currently means *context-include* fileMap key only: `moduleExport` looks
  it up in `data['includeFiles']`, which holds context-mode entries alone, and does so
  through `.get(fileMapKey, {})` — so `tbExternal`/`testBench` resolve to nothing
  SILENTLY, and `moduleExport` still hard-codes `cpp_block_module_name`. S3 must widen
  that key's meaning deliberately (or select the unit on `--section=`) and drop the
  fallback so a bad key fails loudly.
- `sec_tb_class_header_template` (`testbench.py:431-432`) emits `systemc.h` and
  `instanceFactory.h` inside the class region, which under the new scaffold lands in
  module purview. It belongs in the new GMF section with the rest of the baseline —
  6.3 implies this but does not say it.
- `<block>Config.cpp` is user-owned and existing copies carry a bare
  `--template=tbConfig` region with no `--section`. S4's "insert the two new region
  markers" must also RENAME that region to `--section=class`, or the split leaves every
  existing project on a command the generator no longer routes.
- NIT for S4: `_buildPorted` still inserts `slots.userIncludes` at `hdr.end + 1`, i.e.
  ABOVE the `// user #includes here` label, while sibling imports now land below theirs.
  `_afterCommentBlock` makes the two symmetric.

**S3 — Region rewrite.** DONE (2026-08-05).
Add `moduleScaffold --section=tbExternalModuleHeader`. Teach `moduleExport` the
`tbExternal` fileMapKey, keeping it import-only (L2). Rewrite `ext_sec_header` to emit
usings plus class only, with all child Bases imported (D8). Strip the redundant
import/include emission from `ext_sec_init` and `sec_tb_class_init_template`. Split
`tbConfig` into `prerequisites` / `class` / `registration`.
*Gate, three parts:* — CLOSED, all three:

1. `make clean && make gen -j8` then `make -C rundir -j8 all` and `make -C rundir run` on
   `builder/base/examples/simple`: exit 0 throughout, **zero** compiler diagnostics.
   R3 satisfied by the run output: `TestBench Selected: simple`, the DUT hierarchy
   elaborated (`tb.simple.u_producer` / `u_consumer`), both registered tests ran to
   completion, `eotThread` fired (`Simulation stopped by user`), `No error`. Compiler was
   clang++ `-std=c++23`; R1's GCC flavour is NOT covered by this gate.
2. **Slot-placement proof, on `simple`'s External.** All three placements added by hand at
   once — `#include "probe_plain.h"` (plain class, no module/Config type) in the GMF slot;
   `import simple;` first in the preamble slot; `#include "probe_purview.h"` (names the
   module type `simple_ns::tag_st`) after that import in the same slot — plus members of
   both probe types in the in-class user slot so they are really instantiated. Built and
   ran clean (`No error`). Moving only the purview include ABOVE the import then failed:

   ```
   In file included from .../tb/simple/simpleExternal.cppm:22:
   .../tb/simple/probe_purview.h:8:16: fatal error: declaration of 'tag_st' must be
   imported from module 'simple' before it is required
       8 |     simple_ns::tag_st last_{};
   .../model/simpleIncludes.cppm:42:8: note: declaration here is not visible
   ```

   Note the shape of the diagnostic: clang did not reject the trailing `import` itself, it
   rejected the header's *use* of a not-yet-imported type. The invariant bites as a
   name-visibility error, so a purview header that happens to name nothing from the
   imports below it would pass — which is exactly why the rule has to be stated in the slot
   comment rather than left to the compiler. Probe reverted; the example is clean again
   from `make clean` (gen, build, run all green, zero diagnostics).
3. Verilator path on `axi4sDemo` (`make -C rundir -j8 all VL_DUT=1` then
   `run VL_DUT=1`): exit 0, zero compiler and zero Verilator diagnostics, verilated DUT
   selected (`--vlInst axi4sDemo`), 4 frames received end to end, `No error`. `apbDecode`
   was deliberately not used — its `run-vl-blockA` has a known model-only seed gap in the
   example itself, unrelated to this work.

Landed in `templates/systemc/testbench.py`:
`ext_module_header` / `tb_module_header` emit the two GMF sections; `ext_module_export` /
`tb_module_export` emit the two import-only preambles. `_tb_context_import_lines` became
`_tb_context_lines` plus the `_tb_context_imports` / `_tb_context_usings` selectors, so the
context imports go to `moduleExport` and their using-directives to the class-region head
(L2, mirroring `classDecl`). The External's include derivation moved out of
`ext_sec_header` into `_ext_channel_includes` / `_ext_config_includes`, consumed by the GMF
section. `ext_sec_header` now emits usings plus the class only, and the class is
`export class` because the Testbench unit imports it. `ext_sec_init` lost
`import a2c.endOfTest;`, `sc_instance_includes` and `#include "<block>External.h"`;
`sec_tb_class_init_template` lost its `import a2c.endOfTest;` and `.h` include;
`sec_tb_class_header_template` lost `systemc.h`, `instanceFactory.h`, the base import and
the External include. `tbConfig` split into `prerequisites` (D3/D5) / `class` /
`registration` (D4), with the in-class `registerTestBenchConfig` struct and its static both
removed in favour of an `A2C_REGISTRATION_RETAIN` anonymous-namespace static.

Landed in `templates/systemc/moduleScaffold.py`: the two new `--section` cases plus a
`TB_MODULE_EXPORTS` dispatch at the head of `moduleExport`, so `--fileMapKey` on a
`moduleExport` region names the fileMap entry of the unit whose preamble it is (absent =
the block's own `<block>.cppm`). Dispatching the two tb keys explicitly also closes S2's
"resolve to nothing SILENTLY" concern for them by construction — they never reach the
context lookup. The pre-existing `.get(fileMapKey, {})` was left alone on instruction, so a
*mistyped* key on a hand-edited region still degrades silently; that remains open.
`moduleScaffold.py` now does `from templates.systemc.testbench import ...`, matching the
existing `templates/systemVerilog/*` → `package.py` and `blockRegs.py` → `constructor.py`
practice; no cycle, testbench.py imports nothing from moduleScaffold.

D1, D4, D5, D8 are closed by the above; D8 specifically by deleting the
non-parameterizable-child forward-declaration branch outright, so every child Base now
arrives via `sc_instance_includes` in `moduleExport` (visible in
`axi4sDemoExternal.cppm`, where `class axi4s_m_drvBase;` / `class axi4s_s_drvBase;` became
`import axi4sDemo_axi4s_m_drv.base;` / `import axi4sDemo_axi4s_s_drv.base;`).

Three examples were migrated by hand to run the gates, and **S5 must not redo them**:
`examples/simple`, `examples/axi4sDemo` and `examples/xif`. All three were regenerate-not-port (L8 — every
External and Testbench user slot in all three was empty): the four `.h`/`.cpp` were deleted,
`make newmodule` scaffolded the two `.cppm`, and the External's `GENERATED_CODE_PARAM` was
retargeted by hand to `--block=<blk>_tb --excludeInst=<dut> --mode=module`. Their
`Config.cpp` were ported per 6.4: framework preamble deleted (it is now the
`prerequisites` region), the bare `--template=tbConfig` region **renamed** to
`--section=class`, and the trailing untemplated registration definition replaced by the
`--section=registration` region. `simple` and `xif` each kept their one real user
include (`#include "testController.h"`) in the new `// user #includes and imports here` slot.

Exact-text coupling sweep (S2 predicted a fourth; there is one, and it is documentation):
`ARCH2CODE_AI_RULES.md:2745-2750` "File-to-PARAM mapping" still lists `*Testbench.h`,
`*Testbench.cpp`, `*External.h`, `*External.cpp` and gives `tbConfig` section *(none)* —
all four rows are now wrong, and the section-9 diagram at `:2877-2881` and the tree at
`:3807` name the same legacy pair. Left for S5's doc sweep rather than half-fixed here.
Checked and confirmed NOT coupled: `migrateModuleHeader` gates on
`--template=moduleScaffold --section=blockModuleHeader` at `:125` before its
`MODULE_EXPORT_MARKER` test, so a tb `.cppm` (which carries `tbExternalModuleHeader` /
`testBenchModuleHeader`) is skipped and its `--template=moduleExport --fileMapKey=...`
substring never matches; `migrateBlockModulePort` keys on `classDecl` regions and on the
distinct `// block implementation members` string; `newModule._TB_FILE_KEYS` keys on
fileMap keys, which did not change; `unittest/fixtures/hier-layout` deliberately overrides
the tb fileMap to the legacy shape and its bare `--template=tbConfig` region is never
rendered (`test_layout_hierarchical.py` runs `--newmodule` only, not `--systemc`).

One bucket-A test regressed as a direct, expected consequence and must be closed by S5, not
weakened (L12): `unittest/test_build_manifest.py` now reports `generation failed` for
`apbDecode, axiDemo, helloWorld, hierVlDemo, ip_test, mixed, nested, simple_ip` —
every un-migrated example, and nothing else (`xif` was on that list before it was migrated
for the extra gate part). `simple`, `axi4sDemo` and `xif` pass, which is the
useful signal. The cause is confirmed as
`ValueError: Unknown section '' for template 'tbConfig'` on each project's un-renamed
`--template=tbConfig` region; no example source file is damaged by the failure (the
exception is raised during renderSections, before any write, and `git status` on
`examples/` stays clean). Note `args.section` arrives as `''`, not `None`, for a region
command with no `--section`.

Deliberately not done: no classic (`.h`/`.cpp`) branch was kept in these templates, so
`make gen` now FAILS on an un-migrated project's `Config.cpp` (bare `--template=tbConfig`
→ `Unknown section ''`) and silently stops regenerating its External/Testbench (the
`.cppm` the fileMap names do not exist). That is S4/S5's boundary, restated here because it
means the other 14 base + pro examples and `debayer` are currently unbuildable and must be
migrated as a set. `<block>Testbench`'s class is deliberately NOT exported — nothing
imports `<block>.testbench` — and R2's no-`--excludeInst` sentinel path is unchanged code
reached through the same `refactor_tbExternal` call, so it is no better and no worse
covered than before.

**Post-coding review found one real correctness bug, now fixed and proven both ways.**
The first cut of `tb_module_header` emitted only `systemc.h` + `instanceFactory.h`, omitting
the per-context `<context>VariantConfig.h`. The testbench top spells the DUT's Config **by
name** three times (`<DUT>Channels<Cfg>`, `std::shared_ptr<<DUT>Base<Cfg>>`, and the
`createInstance` cast), and until this plan it obtained the declaration only through the
textual `#include "<block>External.h"` that S3 deletes. A Config struct in the External
unit's global module fragment is *reachable but not visible* to an importer, so every
parameterized DUT's `Testbench.cppm` would have failed to compile. It was invisible to the
original gate because `simple` and `axi4sDemo` are both non-parameterizable, so `{{cfg}}` is
empty in each.

Fixed by adding `cpp_config_header_includes(data)` to `pysrc/intf_gen_utils.py` (next to
`sc_channel_header_includes`) and calling it from all three units that name a Config:
`sc_class_dependency_includes`, `ext_module_header` and `tb_module_header`. That also
removed the duplicate copy of the three-line config-header walk the review flagged, so the
set cannot drift — the same "two rendering contexts share this set" pattern the file already
uses. Block-module emission is byte-identical (`git diff` on `examples/xif/model` and
`base/` is empty after regen).

**Extra gate part, added because the original three could not have caught it:**
`examples/xif` — a parameterized DUT (`dutDutV0Config`), a templated `dutInverted<Cfg>` base,
two `push_ack` cross-interface thunkers and two child instances — was migrated the same
regenerate-not-port way and now generates, builds and runs clean from `make clean`
(`GEN=0`, `BUILD=0`, zero diagnostics, `TestBench Selected: dut`,
`src`/`sink` both complete `test_stream`, `No error`). `S5 must not redo xif either.`
Negative proof, by removing only the new line and rebuilding from clean:

```
/work/ws/debayer/builder/base/examples/xif/tb/dut/dutTestbench.cppm:24:76: fatal error:
missing '#include "xifVariantConfig.h"'; 'dutDutV0Config' must be declared before it is used
```

Also from the review: `tb_sec_header` gained a durable comment recording that the testbench
top class is deliberately NOT exported (nothing imports `<block>.testbench`; the top is
only ever reached through the string-keyed instanceFactory), which had been an unexplained
asymmetry against the `export class <block>External` the Testbench unit does import.

Review points deliberately not acted on: dispatching the tb units on `--section` instead of
`--fileMapKey` (the S3 scope fixes `--fileMapKey`, and S2's scaffolds already emit it, so
changing it would mean reopening S2 — the two key namespaces do not collide and the dict
guard runs first); adding `bitTwiddling.h` / `q_assert.h` to the External GMF (6.1 enumerates
that set deliberately and the legacy `External.h` did not carry them either); converting
`cpp_context_include_lines` to kinded `(kind, line)` pairs to delete four `startswith`
sites (worth doing, but it touches `moduleExport`'s block path and `classDecl`, i.e. beyond
S3); the `data.get('connectionMaps', …)` / `.get('configIncludeContext', …)` defensive reads
and the unused `is_parameterizable` / `default_config` template kwargs (all pre-existing,
and identical patterns remain in sibling functions this stage does not own). The
`refactor_tbExternal` call in `ext_module_header` was KEPT although no consumer in that
function reads the fields it sets: removing it would change the state the include derivation
sees, because that derivation previously ran only after the refactor. Every tbExternal-unit
entry point resolving the DUT identity first is the invariant worth keeping.

**S4 — Migration porter.** DONE (2026-08-05).
Extend the existing agent-driven porter with testbench slot mapping:

- `testBench`: delete the `.h`/`.cpp` pair, regenerate (L8). No slot procedure.
- `tbExternal`: merge `External.h` into `External.cppm`, moving the three user slots in
  6.2 and dropping the fixed slot-0 list. Correlate slots by `--template=`/`--section=`
  per L5, stripping embedded markers and the trailing `};`.
- `tbConfig`: no file move, but THREE edits, not one, and the second and third are
  mandatory or `make gen` breaks the project (found in S3, confirmed against every
  un-migrated example):
  1. Insert the two new region markers; L6 puts the existing user preamble in the right
     place automatically. Delete the framework prerequisite includes it now duplicates
     (`systemc.h`, `<string>`, `instanceFactory.h`, `testBenchConfigFactory.h`,
     `import a2c.endOfTest;`) while keeping any genuine user include such as
     `testController.h`.
  2. RENAME the existing bare `--template=tbConfig` region to
     `--template=tbConfig --section=class`. Without this, gen aborts with
     `ValueError: Unknown section '' for template 'tbConfig'` — note the empty string, not
     `None`.
  3. DELETE the user-region tail line
     `<blk>Config::registerTestBenchConfig <blk>Config::registerTestBenchConfig_;`.
     S3 removed the nested `registerTestBenchConfig` struct from the class region, so this
     out-of-class definition is left naming a type that no longer exists — a hard compile
     error, and it sits in the user-owned tail where gen will never touch it. Present in
     `axiDemo:65`, `mixed:70`, `hierVlDemo:50`, `apbDecode:59`, `helloWorld:63` and every
     other un-migrated project. A porter that inserts markers without doing 2 and 3
     produces a project that no longer builds.

*Gate:* a no-loss guard is mandatory (L7). Prior wrapper migration silently dropped a
`setTimedLocal` override. Prove the guard with a fixture whose External carries content
in **all three** ported slots **plus** all four 5.2 injection placements, and confirm the
porter fails loudly rather than dropping one. The injection placements matter here
because a porter that moves a user's GMF include into the preamble slot, or vice versa,
produces a zone error rather than obvious data loss. `ip_test/ip` (class-body plus tail)
and `debayer` (all three slots) are the real-world witnesses.
— CLOSED, all parts. Gate vehicle: `examples/simple_ip`, chosen because it is the only
remaining un-migrated example with a PARAMETERIZED DUT (`ip`, `--variant=variant0`) that
is not `debayer` (S5's) or the much larger `ip_test`. It is also composed, so it
exercises L10 bottom-up ordering. Both of its projects were migrated with `make migrate`
and the gate ran on the child `ip`.

1. **Three ported slots plus the two legacy-reachable 5.2 placements, by PLACEMENT not
   presence.** `ip`'s legacy External was augmented with content in all three slots
   (class body, ctor init-list, ctor body + out-of-line tail) and, at slot-0, a plain
   header `probe_plain.h` and a pimpl boundary `probe_pimpl.h` whose definitions live in
   a plain `probe_pimpl.cpp`. The port put both includes in the **GMF** slot (above
   `export module ip.external;`) and each of the three payloads in its own
   marker-delimited gap. The other two 5.2 placements cannot exist in a legacy pair —
   a legacy header include never attached to a module, so a purview placement would be a
   semantic CHANGE the port must not make — so they were added by hand to the ported
   `.cppm` afterwards (`import ip_ipTop;` first in the imports slot, then
   `#include "probe_purview.h"`, which names the module type
   `ip_ipTop_ns::ipStdMarkerT`). All four then executed in a clean build+run:

   ```
   tb.external:tb.external probes plain=probePlain pimpl=1 purview marker=1
   ```

   `pimpl=1` is the load-bearing one: it can only resolve if the GMF placement kept
   `probePimpl` attached to the global module, matching `probe_pimpl.cpp`.

2. **Negative placement proof.** Moving ONLY `probe_pimpl.h` from the GMF slot into the
   imports slot compiles without a single diagnostic and fails at LINK:

   ```
   ipExternal.module.o: in function `_ZNW2ipW8external10ipExternalC2EN7sc_core14sc_module_nameE':
   ipExternal.pcm:(.text+0x16c): undefined reference to `_ZNW2ipW8external10probePimplC1Ev'
   ```

   The mangled name carries `W2ipW8external`, i.e. the class attached to module
   `ip.external` instead of the global module. This is exactly the "zone error rather
   than obvious data loss" failure the gate was written for, and it confirms why a
   relocated legacy include must go to the GMF slot and nowhere else.

3. **No-loss guard fails LOUDLY, twice, non-destructively.** A stray user `import` at
   slot-0 (a zone decision the port refuses to guess):

   ```
   tb/ip/ipExternal.cpp  TODO_PORT_SLOT0  block 'ip' External has non-boilerplate
   top-of-file content the port cannot place ('import ip_ipTop;'); a stray `import` has
   to go in the `// user imports here` slot and a declaration in the class or module
   purview — place it by hand
   ```

   and a hand-edited class close (`};  // end External`) the boundary walk cannot see,
   which without the guard would have silently dropped the whole class-body slot:

   ```
   ipExternal.h:41  TODO_PORT_UNPLACED  block 'ip' External: the port could not place 8
   source line(s); first unplaced at ipExternal.h:41: 'void stimulusThread(void);'.
   Refusing to delete the legacy pair (extraction miss — fix the slot boundaries, do not
   lose this code)
   ```

   In both cases the exit code was 1, the legacy `.h`/`.cpp` were still on disk, and the
   target `.cppm` was byte-identical to its fresh scaffold.

4. **Real-world witnesses, read-only.** The extraction was run against
   `examples/ip_test/ip/tb/ip` and `/work/ws/debayer/tb/debayer` with no writes. Zero
   unaccounted lines in both. `ip` yields class body (8 lines) + ctor body + a 19-line
   tail; `debayer` yields all three slots (`void fwThread(void);` / `sc_event fwEvent;`,
   `,fwEvent("fwEvent")`, `SC_THREAD(fwThread);` + the 4-line `fwThread` definition) and
   carries its PARAM across as `--block=debayer_tb --excludeInst=u_debayer --mode=module`.
   The `tbConfig` restructure was verified on `helloWorld`, `nested` and `debayer` the
   same way (no writes, zero no-loss misses) — `debayer` being the parameterized case,
   whose `--variant=default` survives on the PARAM line.

5. **Suite.** `unittest/run_all_tests_parallel.sh`: 89 suites, 88 pass. The one failure is
   `test_build_manifest.py`, still S5's, and it is now SHORTER by one — `simple_ip` moved
   to OK, leaving `apbDecode, axiDemo, helloWorld, hierVlDemo, ip_test, mixed, nested`.
   Both `simple_ip` projects build from `make clean` with **zero** compiler diagnostics
   and run to `No error`, and `make migrate` re-runs clean (exit 0, no edits).

**A fourth mandatory edit for `tbExternal` that the S4 bullet did not name, and the
phase-ordering it forces.** The External's `GENERATED_CODE_PARAM` argument tail is a
documented user retarget (`--block=<blk>_tb --excludeInst=<dut>`), and a fresh scaffold
seeds only the bare DUT. Measured: 12 of the 14 legacy Externals in base+pro+debayer
carry a tail that differs from what `newmodule` scaffolds (the two exceptions are
`ip_test/ip` and `simple_ip/ip`, whose sentinel-path `--block=ip --variant=variant0`
already matches). So the port must carry the legacy tail across, appending
`--mode=module` — which reproduces exactly what S3 did by hand for `simple`, `axi4sDemo`
and `xif`, including `xif`'s dropping of `--variant=dutV0` on the External while the
Testbench keeps it.

That retarget has to be visible to `gen`, and the `tbConfig` `--section=class` rename has
to happen before `gen` runs at all, so **the testbench port cannot live in the post-`gen`
`--port` phase**. It is a new phase, `migrateYaml.py --port-tb`, run BETWEEN `make
newmodule` and `make gen`. The scaffold already carries every region marker the
transplant anchors on (empty regions), so an un-filled target is sufficient; this was
verified directly. `make migrate` is now a seven-step pipeline, and `--port-tb`'s exit
code is folded into the sweep's rather than halting the chain, for the same reason the
sweep's does not halt — a flagged hand-port must not leave the tree un-generated.

Landed:
- `pysrc/migrateOrphans.py`: `testBench` → `MIGRATE_DELETE`, `tbExternal` → `MIGRATE_PORT`,
  `tbConfig` → `MIGRATE_EDIT` (D-9). All three `ext` values left on the frozen legacy
  `{hdr: h, src: cpp}` / `{src: cpp}`, with a new header note stating that `ext` is the
  legacy snapshot and disposition is independent of it, so the reverted S1 flip cannot be
  reapplied by accident. The `tb` segment stays MIXED (delete ⊕ port ⊕ edit), so it is
  never directory-cleared. Two consequences arrive free: the sweep now reports
  `TODO_PORT` on the External pair, and `<blk>Testbench.h` enters the deleted-header diff,
  which is what surfaces `debayerConfig.cpp:10` as `TODO_USER_INCLUDE` (see below).
- `pysrc/migrateBlockModulePort.py`: the four-slot extraction and transplant are now
  parameterized by a frozen `PortShape` (class/ctor region names, GMF section, scaffold
  class-body label, framework include/import drop set), with `BLOCK_SHAPE` and
  `TB_EXTERNAL_SHAPE` as its two instances, plus the new `portTbExternals` driver. The
  block path is behaviourally unchanged and is asserted as such by the new test. Two
  incidental improvements fell out: the file's own header now comes from the
  fileMap-resolved legacy path instead of `f"{blockName}.h"`, and S2's NIT is closed —
  relocated GMF includes now insert BELOW the `// user #includes here` label
  (`_afterCommentBlock`), symmetric with the imports slot.
- `pysrc/migrateTbConfig.py` (new): the three `Config.cpp` edits. It reconstructs the file
  as head → PARAM → `prerequisites` region → seeded slot → residual user preamble →
  renamed `class` region → tail, with the retired
  `<blk>Config::registerTestBenchConfig_` definition REPLACED IN PLACE by the
  `registration` region. Moving the residual preamble below the region (rather than
  inserting the region below it, which L6 would suggest) is deliberate: the region emits
  `systemc.h` and friends, and a user include such as `testController.h` must still come
  after them. Its own no-loss guard requires every code-bearing original line to appear
  in the output unless it is on the recognized drop list. A file with no registration
  anchor is REPORTED, not silently left without the region — losing the registration is a
  run-time failure (R3), not a build error.
- `migrateYaml.py`: the `--port-tb` mode. `include/make/a2c-common.mk`: the new pipeline
  step, with the rc folded rather than halting.
- `unittest/test_migrate_tb_port.py` (new, 53 checks): drives both phases for real over
  staged files against a fake `projectOpen` handle. Its transplant TARGET and its
  `Config.cpp` skeleton comparison are obtained by CALLING `templates/fileGen/fileGen.py`
  rather than copying its text, so a scaffold change cannot drift away from what the port
  expects. Asserts zone placement (not presence), the PARAM carry-across, idempotency,
  both loud failures with a non-destructive outcome, and the block shape over the same
  mechanism.
- `unittest/test_migrate_orphans.py`: L12 expectation update — the staged
  `myblkTestbench.{h,cpp}` moved from the `leave` survivors to the delete set, and a
  staged `myblkExternal.{h,cpp}` (port) and `myblkConfig.cpp` (leave) were added.
  `unittest/run_all_tests.sh` gained suite 19q; the parallel runner's suite-count guard
  went 88 → 89.
- `rules/skills/migrate-project.md`: the pipeline is documented as seven steps with the
  new `--port-tb` step described, the `tb`-segment sweep behaviour corrected (it said "the
  `tb` segment is left untouched"), five new manual-TODO kinds added to the table, and the
  frozen-`ext` rule recorded against `migrateOrphans`. Pre-existing gap found and closed
  in the same edit: the `--port` step was never documented at all, which is why the doc
  said "five-step".

Exact-text coupling sweep — one found, and it is a fixture that must NOT be updated:
`unittest/fixtures/hier-layout/core/tb/core/coreConfig.cpp:11` carries a bare
`--template=tbConfig` region. Per S1 that fixture deliberately overrides the tb fileMap to
the legacy shape and its region is never rendered (`test_layout_hierarchical.py` runs
`--newmodule` only), and the new phase only runs under `make migrate`, so it is untouched
and the test still passes. Also checked and confirmed NOT coupled: `_IMPL_MEMBERS_COMMENT`
and the `// block implementation members` scaffold string are unchanged (the External's
anchor is the distinct `// external implementation members`, now `_EXT_MEMBERS_COMMENT`);
`migrateModuleHeader._INSERT` is untouched; `renderBlockPortReport` gained an optional
`label` with both call sites updated.

**Post-coding review (subagent, `builder-base-development`) found five real defects, all
latent rather than live, all now fixed with tests.** In every case the reviewer measured
all 17 `Config.cpp` / 14 External pairs in base + pro + `debayer` and confirmed no current
project trips them — they are invariants that were implicit rather than enforced:

1. `_restructure` never carried the span BETWEEN the PARAM line and the class region.
   Code-bearing lines there tripped the no-loss guard, but a comment-only line was lost
   with no report. That span is now carried with the residual preamble.
2. The `Config.cpp` no-loss guard compares a SET of stripped lines, so it is blind to a
   reordering. Since the restructure deliberately moves the residual preamble BELOW the
   `prerequisites` region, a preamble `#define SC_INCLUDE_DYNAMIC_PROCESSES` (or any
   non-`#include` directive) would have been re-scoped with a clean report. Such a
   directive is now REFUSED (`TODO_TBCONFIG_DIRECTIVE`) rather than moved.
3. `_buildPorted` dereferenced its five target regions unconditionally. A `.cppm` that
   carries the marker (so `_isGenerated` passes) but has lost a region faulted mid-loop,
   AFTER earlier blocks had been written and their legacy pairs deleted. A
   `_missingRegions` pre-check now reports `TODO_PORT_TARGET_DAMAGED` on both the block
   and the testbench path.
4. "Target has no PARAM line" was reported as `TODO_PORT_NO_CPPM` (whose fix instruction
   is about a MISSING file), and "both legacy PARAM lines absent" was reported as
   `TODO_PORT_PARAM_SPLIT` with the message "lines disagree (None vs None)". Split into
   `TODO_PORT_TARGET_DAMAGED` and `TODO_PORT_NO_PARAM_LINE`.
5. `renderBlockPortReport`'s `label` was optional with one call site passing it and one
   relying on the default; now required at both.

Two rule violations were fixed by relocation rather than duplication:
`_regions`/`_find`, `_includeTarget`/`_importTarget`, `_noCodeMask`/`_stripBlankEnds` and
the `GENERATED_CODE_PARAM` read/rewrite pair moved into `pysrc/migrateCommon.py`, which
already owns the sibling `userRegionLines`. That removes a near-verbatim copy of
`migrateProjectParam._restampParamLine` (one contract now, `(hasParamLine, newText)`) and
the cross-module import of six private helpers the reviewer flagged as too thin for the
existing precedent. `migrateTbConfig`'s `PREREQ_INCLUDES`/`PREREQ_IMPORTS` are now pinned
by a test that DERIVES the expected set by calling `tb_config_prerequisites`, so the
migrator's drop list and the region's emission cannot drift. Test count 53 → 61.

One correction to this entry from the same review: "the block path is behaviourally
unchanged" overstates it. GMF includes moved from above the `// user #includes here` label
to below it, and the sibling-import insertion point moved past the label — the latter
fixing a latent defect where `exp.end + 2` landed BETWEEN lines 1 and 2 of the three-line
`USER_IMPORTS_SLOT`. Both are improvements, but they are changes.

**S5 blocker found, reported not fixed: `debayer` cannot build with a non-exported
Testbench class.** `tb/debayer/debayerConfig.cpp:10` includes `debayerTestbench.h` and
line 73 does `dynamic_cast<debayerTestbench *>(tb.get())` to reach
`tb_ptr->external.u_raw_src`. S3 deliberately did NOT export `<block>Testbench`'s class,
on the reasoning that nothing imports `<block>.testbench`; `debayer` is the counter-example,
and no other project in base or pro has this pattern (verified across all 17 Config.cpp).
The sweep now reports it automatically as `TODO_USER_INCLUDE` at `debayerConfig.cpp:10`
rather than letting it become a mystery build failure, but resolving it is a design call
for S5: either export the Testbench class (and let Config `import <blk>.testbench;`), or
rewrite `debayerConfig` to reach the sub-instances without naming the top type.

**S5 note.** `debayer.db` was found STALE (its persisted FILEMAP still carried the
pre-S1 `{hdr: h, src: cpp}` tb entries), which silently suppressed the `TODO_PORT` and
`TODO_USER_INCLUDE` items above until the database was rebuilt. `make db` was a no-op
because the project file's mtime predates the builder change, so S5 must force a db
rebuild (touch the project file, or `make clean`) before trusting any sweep report.

Deliberately not done: the block-implementation `--port` path has no live exercise left in
the tree (no example still carries a legacy block `.h`/`.cpp` pair except `pySocket`, which
is not `yamlFormat: 2`), so its regression is the shape-level assertion in the new test
plus the no-op driver runs during the two `simple_ip` migrations. The probe fixture used
for gate parts 1 and 2 was REVERTED, leaving `simple_ip` migrated but otherwise unchanged;
`examples/simple`, `examples/axi4sDemo` and `examples/xif` were not touched. The remaining
seven examples, the pro suite and `debayer` are S5's, as are `ARCH2CODE_AI_RULES.md` and
`rules/systemc-testbench.md`. GCC validation (R1) is untouched by this stage — every build
here was clang++ `-std=c++23`.

**Post-review fixes (2026-08-06).** Defects found by independent review of the migrate
work, all fixed.

1. `testBench` was `MIGRATE_DELETE`, so the orphan sweep deleted the legacy pair and
   create-only `make newmodule` re-scaffolded the `.cppm` with the block's FIRST declared
   variant — silently discarding the user's `--variant=` DUT selection (documented as a
   user edit at `newModule.py:95-107`). The D-4 measurement (no user *code* in 39
   instances) is still correct; what it did not license was dropping the PARAM tail. The
   entry is now `MIGRATE_PORT` and `migrateBlockModulePort.portTbTops` carries the
   selection onto the scaffold in the `--port-tb` phase before deleting the pair, refusing
   with `TODO_PORT_STALE_VARIANT` when the named variant is no longer declared and with
   `TODO_PORT_TAIL_UNPLACED` when the legacy line holds any other hand-edited argument.
   The sweep cannot do the carry itself: it runs before the scaffold exists, in a
   separate process. KNOWN CONSEQUENCE: `<blk>Testbench.h` leaves the sweep's
   deleted-header diff, so a residual user `#include` of it is no longer reported as
   `TODO_USER_INCLUDE` (see the S5 blocker note above, which relied on that report). The
   live instance that note names — `debayerConfig.cpp` — was resolved by exporting the
   Testbench class, so it now `import`s the module; in every remaining occurrence in these
   trees the reported include was the legacy `.cpp` including its own `.h`, deleted in the
   same run. The gap is real but has no live case, and the same gap pre-exists for the
   `block` port.
   FOLLOW-UP (approved separately): the same stale-variant protection now covers
   `portTbExternals`, which carries its legacy tail VERBATIM and could therefore stamp a
   retired variant — the identical damage class, with a live precondition in
   `simple_ip/ip` (`variant1` genuinely retired). Both porters share
   `_generatorValidatedVariants`, which mirrors the real resolution instead of assuming
   it: `systemcGen` builds the block view from the file's OWN `--block=` argument, and
   `intf_gen_utils.resolve_dut_variant_selection` validates `--variant=` against that
   block's declared variants ONLY when it owns `params:`. So the check skips a
   `_tb`-retargeted External (a different block's variants are the ones resolved) and a
   block without own params (`xif_tb` is parameterizable transitively yet owns none, and
   its variant would pass through to the instance factory unchecked) — refusing either
   would refuse a migration `gen` accepts. Verified in three real databases that
   `getQualBlockVariants` and the `variantConfigs` descriptor labels are the same set, and
   that `getBlockConfigView()['hasOwnParams']` matches the `block_row['params']` signal
   `getBDConfigInfo` uses. The External path deliberately gets NO tail accounting: its
   `--block=<blk>_tb --excludeInst=<dut>` retarget is the documented normal case.
2. `migrateProjectParam` carried a near-verbatim second copy of `PARAM_MARKER` and
   `_restampParamLine`; both now come from `migrateCommon` (the bodies were diffed as
   byte-identical first). `migrateModuleHeader._isImportLine` was likewise a third
   spelling of `migrateCommon._importTarget` and is gone.
3. `--port-tb`'s exit code was folded into the sweep's, which was right for a refused
   External but wrong for a refused `tbConfig` restructure: the bare
   `--template=tbConfig` region it leaves makes the very next `gen` raise
   `ValueError: Unknown section ''`, so the operator got a template traceback and a
   half-regenerated tree instead of the TODO list. `migrateYaml.py` now has named exit
   statuses (`RC_CLEAN`/`RC_TODO`/`RC_BLOCKED`) and returns `RC_BLOCKED` for a Config
   refusal; the `migrate` recipe halts on anything above `RC_TODO`. A blocked run also
   reports the External and tb-top ports without applying them, since their targets are
   files the blocked `gen` will never fill. Verified A/B on `examples/mixed` with a
   deliberately un-restructured Config: old form ran 38 gen steps then the traceback, new
   form runs 0 and ends on the migrator's report.
4. TWO GAPS DECLINED DELIBERATELY — do not re-open them as newly found defects.
   (a) The sweep's `TODO_USER_INCLUDE` no longer fires for `<blk>Testbench.h` (item 1's
   KNOWN CONSEQUENCE). Declined because there is no live case and the residual signal is a
   compile error naming file and line. If it is ever closed, the fix belongs in the PORTER
   phases, which know they deleted the pair — NOT in widening the sweep's diff, since at
   sweep time a ported header still exists and flagging it there would be wrong.
   (b) `RC_TODO = 1` shares its value with a Python traceback's exit 1, so a crash in
   `--port-tb` or `--sweep` is folded as "manual work remains" rather than halting.
   Declined because it needs a crash to reach, the damage is a confusing exit status that a
   re-run clears, and renumbering touches three modes plus the sweep's rc handling and
   changes the published exit contract. Do it standalone if at all.
5. `workerThread.h` REMOVED from the External's generated GMF region (D5's classification
   of it as framework baseline was wrong). The rule: a generated region may emit only what
   the generated code itself needs or what the database directs. No generated region names
   any `worker*` symbol — a grep for `workerFactory|workerBase|workerEvent|
   startSystemCThread` across `templates/` returns nothing — so the header exists purely
   for a user's stimulus thread and is user content, whatever its history (it was the first
   line of the create-once `tbExternal_srcTemplate`, which is why all 16 legacy Externals
   carry it and why the conversion mistook it for baseline). `ext_module_header` now emits
   only `systemc.h` (sc_module / sc_ types), `logging.h` (the generated `logBlock log_;`),
   `instanceFactory.h` (`createInstance` in the generated ctor init list) and the
   database-directed channel / Config / thunker headers. `TB_EXTERNAL_SHAPE.dropIncludes`
   correspondingly drops it from the drop-list, so a legacy copy relocates to the GMF user
   slot through the existing external-header path rather than being deleted (no new special
   case: `_classifyTopOfFile` routes every non-dropped `#include` to `userIncludes`, so
   `TODO_PORT_SLOT0` is not reachable for an include). Four of the 17 ported Externals use
   worker symbols and gained the include in their user slot — `debayer`, `simple_ip`,
   `ip_test/ip_top`, pro `lmmiDemo`; the other 13 lost the line to regeneration.
   PINNED AFTERWARDS, both halves: the relocation assertions in
   `unittest/test_migrate_tb_port.py` were anchored on generated-region BEGIN markers, so
   the accepted band spanned the generated region itself — four sibling assertions shared
   the flaw, including the block shape's sibling-import check, where an import inside the
   `moduleExport` region would have passed. They now anchor on the region END and the
   seeded slot label. The template half was unpinned entirely (no test rendered
   `ext_module_header`); `unittest/test_build_manifest.py` now asserts the regenerated
   `tbExternalModuleHeader` region of all 14 Externals contains the baseline and NOT
   `workerThread.h`, using the generator run that suite already performs.
   TWO ACCEPTED CONSEQUENCES: (a) the porter relocates unconditionally, so a project
   migrated today gets the include in EVERY External's user slot, including the 13 shapes
   that do not use it, which differs from the examples in this tree (ported before this
   fix). Correct default — never discard user content — and the fix if it ever matters is
   the informational relocated-include report, not symbol sniffing. (b)
   `unittest/fixtures/hier-layout/core/tb/core/coreExternal.cpp` still models the retired
   legacy shape; inert (that fixture node emits no tb artifacts) but it is now the only
   place in the tree reading as though a scaffolded External starts with `workerThread.h`.

**S5 — Suite migration and validation.** DONE (2026-08-05).
Port all 16 base and pro examples plus `debayer`. Already done and NOT redone:
`examples/simple`, `examples/axi4sDemo`, `examples/xif` (S3 gates) and
`examples/simple_ip` — both of its projects, `ip` and the root (S4 gate). The extension
flip requires a per-example `newmodule`, so `ip_test` alone is insufficient coverage.
Every project regenerated **in its own project**, not through a parent (L10), and
rebuilt from `make clean` because two headers per block are deleted (L11).
*Gate:* section 8. — CLOSED, all parts:

1. **D-6 landed first, as the blocker it was.** `sec_tb_class_header_template` now emits
   `export class {{tbclassname}}Testbench`, and S3's comment recording the non-export
   rationale was REPLACED (not deleted) with one recording why it IS exported: the
   factory path is how the top is constructed, not the only way it is legitimately
   named. Witnessed live — `debayer`'s `Config.cpp` names the class, does
   `dynamic_cast<debayerTestbench *>(tb.get())`, and reaches
   `tb_ptr->external.u_raw_src` / `u_rgb_sink` to configure both instances before
   simulation; the run then drives frames through them to `No error`.

2. **Suite migrated, 15 projects across 12 example trees.** Every one converged to
   `make migrate` exit 0 on the idempotent re-run except where a PRE-EXISTING non-tb
   item blocks the stamp (below), and every one builds from `make clean` with **zero**
   compiler diagnostics and runs to `No error`:
   `helloWorld`, `apbDecode`, `axiDemo`, `hierVlDemo`, `mixed`, `nested`, `pySocket`,
   `ip_test/common` + `ip_test/ip` + `ip_test/bridge` + `ip_test` (bottom-up, four
   separate `make migrate` runs in four separate trees), the pro `lmmiDemo`, and
   `debayer`. Uniform shape in all of them: `TB_CONFIG_RESTRUCTURE` split the bare
   `tbConfig` region into `prerequisites`/`class`/`registration` and dropped the five
   framework prerequisite lines plus the retired out-of-class registration definition;
   `TB_EXTERNAL_PORTED` merged the External pair into one `.cppm`; the sweep deleted the
   `Testbench` pair and `newmodule`+`gen` recreated it. 60 legacy files deleted, 30
   `.cppm` created, 16 `Config.cpp` edited — and **nothing else** in any example tree,
   confirmed by `git status`.

3. **Verilator.** `axi4sDemo` green (`VL_DUT=1` build + run, zero compiler and zero
   Verilator diagnostics, 4 frames end to end, `No error`). `hierVlDemo` and the
   `ip_test` top also green on the VL path, first attempt, no retry. `apbDecode` was
   deliberately not used — its `run-vl-blockA` has a known model-only seed gap in the
   example itself.

4. **`debayer` regression suite: 44 runs, 44 passed, 0 failed.** An earlier attempt
   reported 18 failures, all `Error: (E549) uncaught exception: Resource temporarily
   unavailable` at 0.01s — thread-creation `EAGAIN` from concurrent migration builds, not
   a functional failure. This is L13 in a new guise: the suite must be run with the
   machine otherwise idle. Re-run alone, it is clean.

5. **Unit suite.** `unittest/run_all_tests_parallel.sh`: **89 suites, 89 passed, 0
   failed.** `test_build_manifest.py` went green by the migration completing, with no
   assertion touched — it now reports `[OK]` for all 12 project roots it walks
   (`pySocket` remains its recorded SKIP). `examples/nested/expected_tree.golden` needed
   no edit: S1 had already updated it to the two `.cppm` names.

6. **Slot-placement proof reproduced on the `debayer` tree**, as section 8 requires, on
   the External that already carries user members and a firmware thread. All four 5.2
   placements at once — `probe_plain.h` (plain class) in the GMF slot,
   `import debayer_interpolate.base;` first in the preamble slot,
   `probe_purview.h` (names the module template `interpolateBase`) after that import in
   the same slot, plus members of both types in the class-body slot and a use of both in
   the constructor-body slot. Built and ran clean:
   `Info: probe: plain=probePlain purview=1` … `No error`. Moving ONLY the purview
   include above its import then failed:

   ```
   In file included from /work/ws/debayer/tb/debayer/debayerExternal.cppm:33:
   /work/ws/debayer/tb/debayer/probe_purview.h:6:5: fatal error: no template named
   'interpolateBase'
       6 |     interpolateBase<interpolateDefaultConfig> *probed_{nullptr};
   ```

   Same shape as S3's diagnostic: the invariant bites as a name-visibility error on the
   header's *use*, not as a rejection of the trailing `import`. Probe reverted; the
   External is byte-identical to before it (md5 `a71a96cd…` both sides) and `debayer` is
   green again from `make clean`.

7. **Grep gates clean.** No `#include "<block>External.h"` or
   `#include "<block>Testbench.h"` anywhere outside `unittest/fixtures`. No
   `#include "endOfTest.h"` in the live tree except
   `builder/pro/common/systemc/inPlaceList.h:10`, which section 4a puts out of scope.

**R1 — CLOSED as a pre-existing compiler blocker, not a defect in this work.** The GCC
flavour is selected with `USE_GCC=1` (`a2c-common.mk:118` sets `CXX=g++`;
`a2c-systemc.mk:124` swaps in `-fmodules-ts -fno-module-lazy` and the one-step
`.cppm` → `.module.o` rule). Run on `debayer` — the tree where the ICE was recorded — with
the only GCC on this machine, `g++ (Ubuntu 13.1.0-8ubuntu1~22.04) 13.1.0`:

```
of module isp_shared_shared_types, imported at /work/ws/debayer/model/debayerIncludes.cppm:16:
/usr/include/c++/13/bits/allocator.h:193:39: internal compiler error: in make_decl_rtl, at varasm.cc:1442
  193 |             if (__builtin_mul_overflow(__n, sizeof(_Tp), &__n))
during RTL pass: expand
make[1]: *** [.../debayerIncludes.module.o] Error 1
```

The failing unit is `model/debayerIncludes.cppm`, the **context includes** module — a
file family two refactors older than this plan and untouched by it. The build never
reaches a testbench `.cppm`: it dies on the leaf every other module depends on. The ICE
signature is byte-for-byte the one `docs/vcs-build.md` §D records for GCC 13.2.1
(`in make_decl_rtl, at varasm.cc:1442`), so §D's conclusion stands unchanged — a maturity
defect in GCC 13.x named modules combined with SystemC's standard-header weight, not
fixable in the makefile or in generated code. `examples/simple` reproduces it
independently on `base/consumerBase.module.o` and `base/producerBase.module.o`, both
block Base modules, again upstream of this work; only after those does it also segfault on
`simpleExternal.cppm`. **This plan therefore neither causes nor worsens R1**, and the two
tb modules per block cannot be evaluated under GCC 13.x at all until the toolchain moves
(§6: GCC 14+, or the Clang-compile/VCS-link path already wired in `a2cProEnv.mk`).

**Documentation (section 9 / 9.1 / D-5) landed.**
- `ARCH2CODE_AI_RULES.md`: the "File-to-PARAM mapping" table rewritten to the three-file
  family with each unit's `moduleScaffold` / `moduleExport` / `testbench` regions and the
  `--mode=module` note; the per-file PARAM example corrected from five files to three;
  the `testbench.py` row of the templates table; and the project tree listing.
- `rules/systemc-testbench.md`: the "File Structure" listing rewritten to the three
  files, with a pointer to `verify-testbench`'s zone table and the statement that
  `Config.cpp` is a plain TU. Its front-matter `globs:` gained `tb/**/*.cppm` — the
  rule file would otherwise no longer match two of the three files it governs.
- `rules/skills/systemc-core.md`: two bullets in "Implementation Location" (imports
  before purview `#include`s inside the one slot; which slot a header belongs in, with
  the plain-TU-definition attachment reason) plus one comment line in the example block.

**Two seams found by the suite, both reported rather than absorbed.**

- **A parameterized project's `Config.cpp` loses its Config declaration.** `debayer`'s
  `Config.cpp` names `raw_video_srcDefaultConfig` and `rgb_video_sinkDefaultConfig`, and
  until this plan obtained them transitively through
  `#include "<blk>Testbench.h"` → `<blk>External.h` → `<ctx>VariantConfig.h`. With both
  those headers gone, `import <blk>.testbench;` supplies the class but NOT the Config
  structs: they sit in the tb modules' global module fragment, so they are *reachable but
  not visible* to an importer, and `<ctx>VariantConfig.h` deliberately cannot become a
  module (section 2). Diagnostic:

  ```
  tb/debayer/debayerConfig.cpp:95:19: fatal error: missing '#include "debayerVariantConfig.h"';
  'raw_video_srcDefaultConfig' must be declared before it is used
  ```

  Fixed the minimal way — one `#include "debayerVariantConfig.h"` in the file's own
  `// user #includes and imports here` slot, which exists for exactly this and carries no
  zone rules (6.4). **The alternative was NOT taken and is a live design option:** emit
  `cpp_config_header_includes(data)` from `tbConfig --section=prerequisites`, which would
  make this zero-edit for every project. There is precedent inside that region — it
  already emits `import a2c.endOfTest;` only because the scaffolded `final()` body needs
  it — but the generated `class` region itself names no Config type, so emitting it would
  be generosity ahead of a generated consumer. Measured reach if promoted: `debayer` plus
  the 8 `/work/ws/isp` projects that reach through `tb_ptr->external.<member>`, i.e. the
  same corpus D-6 was decided on. Left for the user.

- **Both `common` sub-projects do not build standalone**, pre-existing and unrelated.
  `ip_test/common` and `simple_ip/common` fail identically:

  ```
  common/cpu/model/cpu.cppm:16:10: fatal error: 'modelComm.h' file not found
  ```

  Neither `common/rundir/Makefile` carries
  `EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp`, which the BSP relocation requires;
  `ip_test/rundir`, `ip_test/bridge/rundir` and `simple_ip/rundir` all do, which is why
  every parent builds. The sibling `ip` projects build without it because `cpu` is
  owned by `common` and skipped there. Neither `common` has a `run` target either, so
  neither is exercised standalone by any suite. The migration edited **zero** files in
  either — both trees are byte-identical to HEAD — so this predates the plan entirely.
  Reported, not fixed: it is a one-line addition mirroring three siblings, but it is
  not this plan's, and whether these two are meant to build standalone is a question
  about the composition fixtures rather than about the testbench family.

Also reported, not fixed: five `TODO_UNMANIFESTED_SRC_DIR` items in `debayer`
(`proto/model/{baseline,block,test,types}`, `utils/vconv`) and five in `mixed`
(`verif/vl_wrap/{sc_main.cpp,vl_dummy.sv}` as `TODO_UNGENERATED_FILE`, two
`verif/blocks/*/src` dirs, and a `TODO_USER_INCLUDE` in the retired
`verif/blocks/blockF_variant0` harness whose three referenced headers no longer exist
anywhere in the repo). All are project-content decisions the skill explicitly refuses to
make by default, all predate this work, and none blocks a build or a run. `mixed` and
`lmmiDemo` therefore still exit non-zero from `make migrate` for those reasons while
building and running green.

Deliberately not done: `builder/pro/common/systemc/inPlaceList.h` (section 4a — the user
owns that conversion); F1, the `raw_video_src_config.h` slot inconsistency in section 3.3,
which is user code in the product tree and still latent; and promoting the
`<ctx>VariantConfig.h` include into the `prerequisites` region, per the option recorded
above.

One scope note on the suite migration: while resolving pre-existing
`TODO_UNMANIFESTED_SRC_DIR` items, `pro/examples/lmmiDemo/rundir/Makefile` was rewired
from `EXTRA_CPP_SRC`/`EXTRA_CPP_INCLUDES` to `EXTRA_PRJ_SRC_DIRS` for `model/fw` and
`fw/src` (the sweep only counts the latter as covered; keeping both seams would
double-link each `.o`). That is unrelated to this plan, is validated by a clean link and a
green run, and is trivially revertable. A deletion of
`pro/examples/lmmiDemo/verif/vl_wrap/vl_dummy.sv` made in the same pass was REVERTED —
`axi4sDemo` and `mixed` carry the same marker-less residue and were left alone, so
deleting only lmmiDemo's would have made the suite inconsistent for no gain.

**S6 — The two seams S5 reported, decided and closed.** DONE (2026-08-06).
Both were left for the user at the end of S5 and both were decided as stated in D-7 and
D-8. No part of the conversion design was reopened.

1. **The `<context>VariantConfig.h` prerequisite is GENERATED (D-7).**
   `tb_config_prerequisites` now emits `cpp_config_header_includes(data)` between the four
   framework `#include`s and the trailing `import a2c.endOfTest;`, so every project gets
   the declaration with zero hand edits. The region already emitted `import a2c.endOfTest;`
   purely because scaffolded user code needs it, which is the same shape of obligation, and
   the function now carries a durable comment saying so for both lines — a reader checking
   the generated lines alone will find neither prerequisite named there, and would delete
   them as unused.

   The two hand-added copies were removed in the same change:
   `/work/ws/debayer/tb/debayer/debayerConfig.cpp` (S5's minimal fix, with its three-line
   explanatory comment, now redundant against the region's own comment) and
   `examples/ip_test/top/tb/ip_top/ip_topConfig.cpp` (a LEGACY hand include, predating this
   plan — 6.4 quotes it in the interleaving evidence). After regeneration seven `Config.cpp`
   carry the include, all inside the region at line 9, and no hand-added copy remains
   anywhere in base, pro or `debayer`: `debayer`, `mixed`, `xif`, `ip_top`, `ip_test/ip`,
   `simple_ip/ip`, `simple_ip`. The other ten are non-parameterizable, where
   `configIncludeContext` is empty and the region is byte-identical to before.

   Scope limit worth stating: the emitted set is the block view's `configIncludeContext`,
   i.e. the block's own config context plus that of each parameterizable child — exactly the
   set `ext_module_header` and `tb_module_header` already emit. A `tb_ptr->external.<member>`
   sibling is NOT in that set; `debayer` works because the header is per *context*, so
   `debayerVariantConfig.h` carries `raw_video_srcDefaultConfig` alongside the DUT's own. A
   Config declared in a different context remains the author's include. This is the same
   coverage the two module units have, where before this change `Config.cpp` had none at all.

2. **The BSP opt-in gap closed, and swept (D-8).**
   `EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp` added to
   `examples/ip_test/common/rundir/Makefile` and `examples/simple_ip/common/rundir/Makefile`,
   the opt-in line copied verbatim from the siblings with a comment stating this project's
   own reason (it OWNS the `cpu` block that uses the stubs, where `bridge` reaches the same
   block through composition).

   Swept all 18 `rundir/Makefile` in `builder/base/examples` and `builder/pro/examples`
   against the BSP surface (`modelComm.h`, `fwlog.h`, `regRdWr.h`, and the `.cpp` of the
   last two). Only five projects reference it at all — `ip_test` root, `ip_test/common`,
   `ip_test/bridge`, `simple_ip` root, `simple_ip/common`, plus the pro `lmmiDemo` — and
   NO project supplies its own copy of any BSP file, so a straight opt-in is the whole fix
   in every case. The two `common` projects were the only ones missing it; this was the
   third and last instance of the gap (`lmmiDemo` in S0, these two here). The remaining
   twelve example projects **need no fix and did not get one** — they never name a BSP
   header, directly or through a generated firmware file. `ip_test/ip` and `simple_ip/ip`
   are the interesting negatives: they compose `common` but `cpu` is owned there and skipped,
   so they build without the opt-in, as S5 measured.

*Gates:* all green, first attempt, no retry.

- `debayer`: `make clean`, `make gen -j8`, `make -j8`, `./build/run -t debayer` (the tree
  has no `run` target) — exit 0 throughout, **zero** compiler diagnostics, frames driven
  end to end, `No error`. Parameterized, so it is a real test of the emission rather than
  an empty `{{cfg}}`.
- `examples/xif` (parameterized DUT) and `examples/simple_ip` (parameterized, composed;
  child `ip` first, then the root per L10): `make clean` → gen → build → run, exit 0, zero
  diagnostics, `No error`.
- Both `common` projects now build standalone from `make clean`: gen 0, build 0, zero
  diagnostics, and `-I.../common/fw/bsp` present in the compile line. Neither has a `run`
  target, so building is the whole gate.
- Whole-suite sweep, because the change alters a generated region in EVERY project:
  `helloWorld`, `apbDecode`, `axiDemo`, `axi4sDemo`, `mixed`, `nested`, `hierVlDemo`,
  `ip_test/ip`, `ip_test/bridge`, `ip_test` root, `simple`, `pySocket` and the pro
  `lmmiDemo` — each from `make clean`, all `gen=0 build=0 diagnostics=0 run=0`, each
  reaching `No error`. `mixed` and `xif` put a second and third parameterized project
  through the new emission.
- `unittest/run_all_tests_parallel.sh`: **89 suites, 89 passed, 0 failed** — unchanged from
  S5. `test_build_manifest.py` re-run standalone reports `[OK]` for all 12 project roots.

Landed:
- `templates/systemc/testbench.py`: `tb_config_prerequisites` gains the
  `cpp_config_header_includes(data)` call plus the durable comment. No new helper: the
  function was already imported into this module by S3 for `ext_module_header` /
  `tb_module_header`, so the set cannot drift between the three units that name a Config.
- `pysrc/migrateTbConfig.py`: comment only, above `PREREQ_INCLUDES`/`PREREQ_IMPORTS`,
  recording that the region's one project-dependent line is deliberately NOT on the
  migrator's drop list. The header is include-guarded, so a legacy hand-added copy left in
  the user slot is a no-op, whereas dropping a user line by a name the migrator would have
  to derive per block is the riskier of the two. Behaviour unchanged.
- `unittest/test_migrate_tb_port.py`: `test_tbconfig_drop_set_matches_the_template` passed
  `(None, None, None)` and now has to supply a view. It pins BOTH halves — a `data` with no
  config context still derives the drop set exactly, and a `data` with one context proves
  the `VariantConfig.h` line is emitted and is absent from the drop set.
- `rules/skills/verify-testbench.md`: the paragraph telling the user to add the include by
  hand now says the region emits it, and says not to delete it on the evidence of the
  generated lines around it.
- `examples/ip_test/common/rundir/Makefile`, `examples/simple_ip/common/rundir/Makefile`:
  the opt-in.
- `examples/ip_test/top/tb/ip_top/ip_topConfig.cpp`, `/work/ws/debayer/tb/debayer/debayerConfig.cpp`:
  hand-added include removed.

Exact-text coupling sweep — one found, and it is the documentation the change contradicts:
`rules/skills/verify-testbench.md:111` instructed the user to hand-add
`#include "<context>VariantConfig.h"`, which is now wrong in the direction that costs most
(a reader would delete the generated line as a duplicate of advice they had already
followed). Rewritten. Checked and confirmed NOT coupled: no `.golden` or emit expectation
encodes the region's line set; `migrateTbConfig._PREREQ_INSERT` seeds only the marker pair
and the slot label, not the region body, so the region gaining a line cannot make a migrated
file differ from a fresh scaffold; `fileGen.py:485` likewise seeds an EMPTY region; and
`unittest/fixtures/hier-layout/core/tb/core/coreConfig.cpp` keeps its bare
`--template=tbConfig` region, which is still never rendered (S1/S4).

**Post-coding review (subagent, `builder-base-development`) — three items acted on, none a
live defect.** It confirmed the view contract (`getBlockData` creates both
`configIncludeContext` and `includeFiles` unconditionally, and `tbConfig` is `mode: block`
with no `--context`, so the block view is always supplied and a non-parameterizable block
yields a byte-identical region), that no fallback pattern was added, that nothing is derived
from a filename or path, and that no `.golden`, makefile or emit expectation encodes the
region's line set. Acted on:

1. The skill paragraph over-promised. It said "for every config context of the block", but
   the emission set is the DUT block's own config context plus each parameterizable child's;
   a `tb_ptr->external.<member>` SIBLING is not in that set and is covered only because the
   header is per *context*, so a sibling Config declared in another context is still the
   author's include. Now stated that way, with the residual case named.
2. `check("topVariantConfig.h" not in PREREQ_INCLUDES, ...)` could not fail — it compared an
   invented name against a fixed four-name tuple. It now asserts through
   `migrateTbConfig._isPrerequisite`, which is the predicate that would actually start
   dropping the line if the drop test were ever widened to a pattern or suffix match.
3. The fake view supplied `configIncludeContext` as a list where the real view is a dict; it
   passed only because the helper uses `sorted()` and membership. Corrected to a dict so the
   seam matches the contract it stands in for. The function comment was also cut roughly in
   half.

Its one reported "regeneration gap" was an artifact of reading the tree while the suite sweep
was mid-flight, and is worth recording because it will mislead the next reader the same way:
`unittest/test_build_manifest.py` is the in-place writer and does `clean` + `db` + `gen` on
all 12 example roots, so running the unit suite AFTER a build sweep empties every example's
`rundir/build`. Object files older than their source therefore prove nothing about whether an
example was built. Re-checked directly: all six parameterized `Config.cpp` carry the include
and every project in the sweep above built and ran green before the suite cleaned it.

Deliberately not done: the `debayer` regression suite was NOT re-run. S5 ran it (44/44) and
records that it needs an otherwise-idle machine; the whole-suite example sweep above was
running concurrently, and the change is one generated `#include` line in a file the suite
does not vary. `builder/pro/common/systemc/inPlaceList.h` (section 4a), F1 (section 3.3),
`tandem` (D-2) and R1 (GCC) are all unchanged. The DEPLOYED skill copy
`/work/ws/debayer/.claude/skills/verify-testbench/SKILL.md` is stale against
`rules/skills/verify-testbench.md` (101 lines vs 122) and was left alone: it was already
stale before S3's additions, and deploying skills is a user-run step, not this plan's.

## 8. Validation

- `make clean && make gen -j && make run -j` green on every example under
  `builder/base/examples` and `builder/pro/examples`.
- `make run-vl` green on `ip_test`, `apbDecode` and `axi4sDemo` (the three known-good
  Verilator paths; `axiDemo` and `simple` are accepted model-only and must not be
  re-diagnosed). Retry a Verilator or regen flake once from clean before diagnosing
  (L13).
- `make clean && make gen && make run` green on the `debayer` product tree, which
  exercises the parameterized DUT, cross-interface thunkers in the External, a register
  decode router and a firmware worker thread — the densest single consumer of this file
  family — followed by its regression suite.
- `unittest/run_all_tests.sh` in full, not killed under a short timeout (L13). Update
  bucket-A golden/emit expectations that encode the old file shape; never weaken one
  (L12). Known pending since S3: `test_build_manifest.py` fails for the eight un-migrated
  examples and must go green on suite migration, not by relaxing the assertion.
- A regression test that *executes*: no structural DB-readback test. The S4 porter
  fixture must build and run, asserting every ported slot survived.
- Grep gates: no `#include "<block>External.h"` or `#include "<block>Testbench.h"`
  remains outside `builder/base/unittest/fixtures`; no `#include "endOfTest.h"` remains
  in the live tree.
- The S3 slot-placement proof (both the passing and the deliberately-failing ordering)
  reproduced once on the `debayer` tree, whose External already carries user members and
  a firmware thread.
- Post-coding review of the generator changes by a subagent using the
  `builder-base-development` skill.

## 9. Documentation Deliverable

The 5.2 contract must ship with the change, not live only in this plan. The
`verify-testbench` skill documents `--excludeInst` and the External/Testbench structure
but says nothing about module zones, so a user hitting the choice has nowhere to look.
Add to `verify-testbench`:

- the 5.2 decision table, with the two live `debayer` examples named;
- the imports-before-includes invariant inside the preamble slot;
- the statement that `Config.cpp` has no zone rules;
- a pointer to `endOfTest.cppm`'s own warning against reintroducing a textual include of
  a module in a purview.

This is the same knowledge the block templates already carry as behaviour comments; the
skill is where a user, rather than a generator author, will find it.

DONE in S3 (2026-08-05): `rules/skills/verify-testbench.md` gained a new instruction 4,
"Where to add your own `#include` / `import`" — the 5.2 table with the four `debayer`
files named, the imports-before-includes invariant with the real error text, the
include-guard note, the pointer to `endOfTest.cppm`'s own warning, and the statement that
`Config.cpp` has no zone rules. The `--excludeInst` usage lines in instruction 3 were
corrected from "both the `*External.h` and `*External.cpp`" to the single `*External.cppm`
with `--mode=module`. Still legacy and left for S5: `rules/systemc-testbench.md:17-28`
and the `ARCH2CODE_AI_RULES.md` references noted in the S3 entry.

### 9.1 Block modules: `systemc-core`

The block-module zone contract belongs in `systemc-core`, which already documents the
three generated regions and both user slots. It is missing only the ordering rule inside
the second slot, so the addition is small and must stay small:

- imports first, then any `#include` of a header that names module or `Config` types —
  an `import` after a non-import declaration is ill-formed;
- such a header belongs in this purview slot, not the global-module-fragment slot, unless
  it is the boundary of a class also defined in a plain translation unit, which must
  attach to the global module.

Do not restate the plan, the defect list, or the reasoning chain. Two bullets in the
existing "Implementation Location" list, and the corresponding comment line in the
example block, are the whole deliverable.

## 10. Decisions Recorded

- **D-1:** `<block>Config.cpp` remains a plain translation unit. Confirmed by the user;
  reinforced by the measured include/import interleaving in 6.4.
- **D-2:** `tandem` is a separate follow-on. Confirmed by the user.
- **D-3:** The scaffold retains ownership of the closing `};` on both class and
  constructor, matching `blockModule_cppm`. This is a deliberate user-slot seam, not a
  coverage gap, and is not changed by this plan.
- **D-4:** `testBench` is regenerate-not-port, on the measured evidence in 6.2, and
  independently confirmed against the `/work/ws/isp` workspace (2026-08-05): 22 files
  across 11 further projects, including the salvaged root integration, carry **zero**
  non-trivial content outside their generated regions. The only outside-region text is
  the include-guard triple, which the `.cppm` form does not have. This is the corpus that
  authorises `MIGRATE_DELETE` for the entry in S4; 39 instances now agree.

  Incidental defect found by that survey, fixed by this plan rather than needing its own
  change: 10 of those 11 `Testbench.h` files carry the guard macro `<BLOCK>_TANDEM_H`,
  identical to the guard in the same block's `<block>Tandem.h`. Two headers sharing one
  guard means whichever is included second expands to nothing, silently. Only
  `debayer/tb/debayer/debayerTestbench.h` has the correct `DEBAYER_TESTBENCH_H`. The
  conversion dissolves this class of defect outright, since a module interface unit has no
  guard; S2 removed the dead guard tokens from `_tb_subst` for the same reason.
- **D-5:** The block-module zone contract is documented in `systemc-core`, not a new
  shared section. Confirmed by the user, with the direction to keep it brief. See 9.1.
- **D-6:** The testbench top class **is exported** (`export class <block>Testbench`).
  S3 deliberately left it unexported, reasoning that nothing imports
  `<block>.testbench` because the top is reached only through the string-keyed factory.
  That is true of the base and pro examples and false of every real project: measured
  2026-08-05, `dynamic_cast<<block>Testbench *>` appears in the `Config.cpp` of 8
  `/work/ws/isp` projects plus `debayer`, with 16 further sites reaching through it as
  `tb_ptr->external.<member>` to configure instances before simulation. A `Config.cpp`
  that cannot name the class cannot do this.

  So the choice is a one-word generator change against rewriting the testbench
  configuration of nine independent projects. Export wins on cost and on correctness:
  the factory path is how the top is *constructed*, not the only way it is legitimately
  *named*. S3's own comment recording the non-export rationale must be replaced, not
  merely deleted, so the next reader does not re-derive the wrong conclusion from the
  examples alone. This is a further instance of the standing caution that the bundled
  examples are not a source of truth for real usage.

  Implemented in S5 (2026-08-05), comment replaced in `tb_sec_header`. Note the seam it
  exposes, recorded in the S5 entry: `import <blk>.testbench;` restores the *class* name
  but not the DUT `Config` structs the old header chain also carried, so a parameterized
  project's `Config.cpp` needs its own `#include "<ctx>VariantConfig.h"`. D-7 makes that
  include generated rather than hand-added.
- **D-7:** The `<context>VariantConfig.h` prerequisite of a parameterized project's
  `Config.cpp` is **GENERATED**, from `tbConfig --section=prerequisites`, not hand-added
  per project. Decided by the user 2026-08-06 against S5's alternative of leaving the
  one-line hand fix in place.

  S5's argument for leaving it — the generated `class` region names no Config type, so
  emitting the header would be "generosity ahead of a generated consumer" — reads the region
  wrongly. `prerequisites` exists to make the file's USER-owned bodies compile, and it
  already emits `import a2c.endOfTest;` for exactly that reason and no other: nothing in any
  generated region of `Config.cpp` votes on `endOfTestState`, the scaffolded `final()` body
  does. The `Config` header is the same obligation with the same justification, so the
  precedent is inside the region rather than being extended to it.

  Cost decides it the same way D-6 did, on the same corpus: one generator line against
  hand-editing `debayer` plus the 8 `/work/ws/isp` projects that reach through
  `tb_ptr->external.<member>`, forever, for every project created after them. A prerequisite
  a user must remember is a prerequisite that will be forgotten, and the failure lands as a
  confusing `missing '#include "<ctx>VariantConfig.h"'` on a file the user did not change.

  The line looks unused when read against the generated lines around it, so the region
  carries a durable comment for both prerequisites saying whose code needs them. Without it
  a future reader deletes them as dead. Implemented in S6.
- **D-8:** The missing BSP opt-in in `ip_test/common` and `simple_ip/common` is **FIXED
  NOW**, and swept across base and pro rather than fixed in place. Decided by the user
  2026-08-06 against S5's "reported, not fixed" on the grounds that whether these two are
  meant to build standalone is a composition-fixture question.

  It is not, and the deciding evidence is that this was the THIRD instance of one gap:
  `pro/examples/lmmiDemo` in S0, then these two. A defect found three times in one refactor
  is a systematic omission of the BSP relocation, not a per-project intention, and the
  cost of the sweep is one grep over 18 makefiles. Two projects still not building
  standalone also means two projects no suite exercises, which is how the gap survived the
  relocation in the first place.

  The sweep's result is recorded in the S6 entry and is itself the useful artifact: exactly
  five projects plus `lmmiDemo` touch the BSP, none supplies its own copy, so the opt-in is
  the complete fix wherever it is needed and the other twelve example projects correctly
  have nothing. Implemented in S6.

- **D-9:** The `MIGRATE_LEAVE` disposition is **renamed to `MIGRATE_EDIT` ("edit")**.
  Decided by the user 2026-08-06 after reviewing the strategy question this change raises.

  This work moved all three testbench entries off never-touched in one step (`testBench`
  → delete, `tbExternal` → port, `tbConfig` → auto-restructured), and `leave`'s definition
  had to weaken from "never touched" to "never touched *here*" to keep describing
  `tbConfig`. A disposition that no longer answers "will this file be modified?" is how
  user code gets deleted later, so the word is removed rather than redefined: nothing in
  the map is labelled `leave`, and the vocabulary block now states outright that every
  entry present is modified by SOME phase and that an unaffected file is OMITTED — the
  map's own pre-existing omission rule, promoted to the reader's first fact about it.

  Behaviour is unchanged: `edit` is expanded for deletion exactly as `leave` was, i.e.
  never. `test_migrate_orphans.py` re-run PASS (21 checks, 0 failures). The disposition
  is referenced by name in `rules/skills/migrate-project.md` §11, updated with it.

## 10a. Follow-on: out-of-region scaffold sweep, Group A (LANDED 2026-08-06)

A read-only inventory of every `fileGen.py` scaffold's out-of-region content, taken after
S6, found the same defect classes D5 and D6 name still open in scaffolds OUTSIDE the
testbench family. The items whose fix costs nothing on existing files ("Group A") landed
as one change; the items needing a migration pass over existing files did not, and are
recorded below as deliberate deviations.

**Landed.**

- **Reg-handler module preamble (new D5-adjacent defect, wrong-advice class).** The shared
  `USER_IMPORTS_SLOT` comment told the user to place `import` in a zone `moduleExport`
  had already closed for a reg-handler: `moduleExport` appended every `using namespace`
  at its own tail whenever `isRegHandler`, and a using-directive closes the module
  preamble. Fixed at the generator rather than by rewording the frozen comment, because
  a scaffold comment fix never reaches the existing corpus. `moduleExport` now emits
  imports only for every block; `blockRegs --section=header` emits the usings at its
  class-region head exactly as `classDecl` already did, through a new shared
  `intf_gen_utils.sc_class_module_usings` so the two class emitters cannot drift. The
  `isRegHandler` special case is gone. This is a between-regions move, so every existing
  reg-handler self-heals on the next `make gen` with no duplicate — proven on
  `examples/mixed/model/blockBRegs.cppm` and `blockGRegs.cppm`.
- **`<cstring>` and `<cstdint>` on FW headers (open D5 instances).** Both were frozen
  outside the region AND absent from the generator's own derivation, so the scaffold was
  silently covering for it: every `fw`-mode struct gets a `memset` default constructor
  (`structures.py:342`), `memcpy` array copies (`:986`) and the pack/unpack memsets, plus
  `static constexpr uint16_t _bitWidth`/`_byteWidth` and a `uint*_t _packedSt` typedef.
  A reader deleting the apparently-unused `<cstring>` would never get it back. Now
  emitted from `structures.py::systemIncludes` via a mode-keyed `baselineIncludes`
  (exhaustive over `model`/`fw`/`module`; only `fw` carries entries, since a model/module
  header pulls both in through `systemc.h`).
- **`<cstdint>` on `<context>VariantConfig.h` (open D5 instance).** Emitted from
  `config.py::includeConfig`, ahead of its paramless early return, so a context with no
  parameterizable constants still gets it. This closes an inconsistency inside one
  generator: the sibling `foreignConfig` path already emitted `<cstdint>` in-region.
- The scaffolds keep their outside copies of all three; a guarded standard header
  included twice is idempotent, and sweeping the outside copies is a separate optional
  job. Coverage was proven instead of assumed: on one FW witness
  (`examples/simple/fw/include/simpleIncludesFW.h`) and one config witness
  (`examples/mixed/model/mixedVariantConfig.h`) the outside copy was deleted, the project
  regenerated, built and ran green on the region-supplied copy alone, then restored.
- **`instanceFactory.h` deleted from `vlScWrap_hdrTemplate` (a rotted D5 line).** Dead in
  all 26 migrated Verilated SC wrappers — the registration it existed for moved to
  `blockVlRegistrar`. The one file with a second hit,
  `examples/inAndOut/systemVerilog/simInAndOut/inAndOut_hdl_sc_wrapper.h`, is an
  un-migrated legacy wrapper with no `preamble` region and is unaffected.
- **`systemc.h` AND `blockBase.h` moved into `module_hdl_sc_wrapper --section=preamble`
  (open D5 instance).** `blockBase.h` was not in the original inventory: it was arriving
  transitively through the very `instanceFactory.h` being deleted above
  (`instanceFactory.h:10`). The generated wrapper class names `blockBase` as a base class
  and `blockBaseMode` as a ctor argument, so rule 1 puts it in the region outright, and
  `import <block>.base;` cannot supply it — it sits in that module's global module
  fragment, whose names are reachable but not visible to an importer. Caught in review,
  before it could ship as a fresh-scaffold-only build break invisible to every existing
  project. Existing wrappers carry both twice, harmlessly; a fresh scaffold now carries no
  out-of-region include at all. Proven by deleting
  `examples/axi4sDemo/verif/vl_wrap/axi4sDemo_hdl_sc_wrapper.h`, re-scaffolding it via
  `make newmodule`, and running the `axi4sDemo` `VL_DUT=1` cosim green on the region's
  includes alone — plus `hierVlDemo`, `mixed`, `pySocket`, `simple-ip` and `ip-test`, which
  are the other targets that actually compile the SC wrapper.
- **New D6 instance closed.** The comment above `vlScWrap_hdrTemplate` claimed newmodule
  lays down "only the minimal skeleton (guard, PARAM line, markers)" and that nothing
  between the PARAM line and the first marker carries generator-owned content. It also
  lays down two includes, the `end_ctor_init` hook and the closing `};`, and one of those
  includes was the rotted `instanceFactory.h` — i.e. exactly the failure the comment
  asserted could not happen here. Rewritten to name what the scaffold actually seeds.
- **D6 hygiene in `tbConfigTemplate`.** The four-line `A2C_REGISTRATION_RETAIN` /
  direct-`.o`-linking explanation inside `createTestBench` is trimmed to one line. The
  wording was accurate, but it described a *generated* mechanism from inside a
  create-once file, which is how D6 happened the first time; the mechanism stays
  documented in the two generated regions that implement it.
- **D7 anchor for the tandem family.** `tandem_hdrTemplate`'s bare `private:` gains
  `// tandem implementation members`, matching the anchor D7 added to the External, so a
  future tandem porter has the same stable landmark. `tandem_srcTemplate` also gains the
  copyright line every other `.cpp`/`.cppm` scaffold carries.
- **`config_hdr` guard.** `__HEADERGUARD___CONFIG_H` emitted `<NAME>_H_CONFIG_H`, a fossil
  of the pre-rename filename; now `<NAME>_H_`, matching the FW header's spelling.

**Deliberate deviations, recorded not fixed.**

- `namespace fw_ns {` / `}` in `includeFW_hdrTemplate` — **SUPERSEDED, see Group B below.**
- `includeFW_src` out-of-region preamble — **SUPERSEDED, see Group B below.**
- `include_hdr` / `include_src` carry the same class of out-of-region include, but the
  path is dead (`config/project.yaml` defines `include` as `cppm`-only and
  `migrateIncludes.py` removes any override back to `{hdr, src}`). Whether to retire the
  entries is a separate decision — **RESOLVED: retired, see 10e (C3) below.**
- Removing `bitTwiddling.h` / `q_assert.h` / `<algorithm>` from `blockModuleHeader`, and
  `systemc.h` from `tb_config_prerequisites`, are in-region reductions that need a
  fix-up pass over existing files; deferred to a separate change — **LANDED, see 10c
  (Group B) below**, which also resolved the `moduleHeader` (context unit) baseline and
  found the premise there to be wrong. `<string>` STAYS in
  `tb_config_prerequisites`: generated code names `std::string` directly, so the rule is
  to name the header directly even though `instanceFactory.h` supplies it transitively.

**Known consequence, accepted.** The FW and config-header scaffolds now seed a standard
header the region also emits, so a freshly scaffolded file carries each twice. This is the
deliberate trade that keeps the change free of a fix-up pass: an include-guarded standard
header is idempotent, and sweeping the outside copies from both scaffolds is an optional
tidy-up. It is the one place this change knowingly differs from the `vlScWrap_hdrTemplate`
treatment, where the scaffold copy WAS removed because there the frozen line had rotted.

**Open convention finding, not fixed here.** `sc_class_dependency_includes` labels both
`import` and `using namespace` lines with a single `kind` of `'import'`, so every consumer
re-splits them with `line.startswith('using namespace ')`. Now that the two go to different
regions, the contract-driven form is a third `kind` at the producer. Deferred because the
prefix test predates this change in `baseModuleHeader` and both dependency helpers, so
fixing it is a separate sweep rather than a line edit.

**Gates.** `unittest/run_all_tests_parallel.sh` 89/89. Every example tree
`make clean && make -j8 && make run` exit 0 across base and pro (the two definitions-only
`common` projects have no `run` target by design), plus `debayer` built and run directly
and the `inAndOut` / `hierInclude` SV-lint-only trees. `make gen` twice on one example
produced no further diff.

## 10b. Follow-on: out-of-region scaffold sweep, C1 — FW artifacts (LANDED 2026-08-06)

Group A left the two FW findings (P7, P8/P9) as deviations because moving the namespace
braces into regions looked like it needed a migration phase. It does not. The FW artifacts
are 100% generated: across every `*IncludesFW.h`/`.cpp` in `builder/base`, `builder/pro`
and `debayer` the only out-of-region content was the include guard, the project-configured
copyright line, the PARAM line, the namespace braces, the two standard-include copies, the
`.cpp`'s sibling `#include` and its `using`. There is no hand-written content and no user
slot in either scaffold, which makes delete-and-rescaffold legal and makes a migration
phase unnecessary.

**Decisions recorded (user, 2026-08-06).**

- FW include artifacts stay a `.h` plus `.cpp` pair, for compatibility with a wider set of
  toolchains. Retiring the `includeFW` `src` extension, or converting FW includes to
  modules, is off the table — Group A's open fileMap question is closed, not deferred.
- `<ctx>IncludesFW.cpp` being structurally empty today is **reserved headroom, not a
  defect**: `codeMapping['fw']` carries no `'split'` entry, so both regions render empty.
  The file, its regions and its content stay. Adding a split `fw` feature must not require
  a scaffold change, which is what drove the preamble design below.

**Landed.**

- **`fw_ns` is region-owned in both artifacts (closes P7).** Each of the four in-namespace
  header regions (`includes --section=constants|types|enums`, `structures`) now emits its
  own complete `namespace fw_ns { … }` via `intf_gen_utils.wrap_fw_namespace`, the fw twin
  of `wrap_module_namespace`. Adjacent self-contained blocks were chosen over one region
  opening the namespace and a later one closing it, because a split pair breaks the moment
  a region renders empty — which happens for real: a structure-less context
  (`examples/axiDemo` `axiStd`) emits nothing from its `structures` region. Reopening the
  same namespace keeps every earlier region's declarations visible to later ones. The
  `structures --section=headerIncludes` region stays outside, since `#include` lines cannot
  sit inside a namespace.
- **The `.cpp` keeps `using namespace fw_ns;`, region-owned (closes P8 without deleting
  anything).** The `cpp` section spells its out-of-line definitions `fw_ns::<struct>::`
  from `args.namespace`, so wrapping that region in the namespace would double-qualify;
  the `using` is what lets a split definition's *leading* return type (e.g.
  `sc_pack`'s `{structType} fw_ns::<struct>::sc_pack(...)`) name an fw type unqualified,
  which the declarator qualification alone does not cover. It is now emitted from
  `structures --section=cppIncludes` in `fw` mode. That region owns the whole `.cpp`
  preamble, so a future `'split'` entry in `codeMapping['fw']` starts producing
  definitions with no scaffold change. Review established the precise limit of that
  headroom: `fw_pack` and `fw_unpack` flipped to `'split'` would compile, since both
  `cpp_split` declarations return `void` and `_packedSt` sits after the declarator-id
  where class-scope lookup applies; the directive is therefore reserved for a future
  feature with a leading return type, and is not a substitute for `--namespace=fw_ns`,
  which an out-of-class member definition needs regardless. `constructor` cannot be
  split at all — it is emitted only on the `not isCpp` path and takes no handle.
- **The sibling `#include "<ctx>IncludesFW.h"` moved into the same region (closes P9).**
  Read from `includeFiles['includeFW_src'][context]['siblingHeaderName']`, matching the
  `tandem_src` precedent; nothing is reconstructed from a filename.
- **`#include <cstdint>` / `#include <cstring>` removed from `includeFW_hdrTemplate`.**
  Group A's `baselineIncludes` emission owns them. This is the step that finally removes
  the frozen copies rather than leaving duplicates, so Group A's "known consequence,
  accepted" no longer applies to the FW header.
- **`fw_ns` has one source.** It is a framework constant, not a derivation — unlike the
  per-context module namespace there is nothing in the database to derive it from. It now
  lives once as `intf_gen_utils.FW_NAMESPACE`, and both the region emitters and the
  scaffold's `--namespace=` region argument spell it from there.
- **Latent Group A gap fixed, found by this change.** `structures.render` early-returned on
  an empty structure set for *every* section, so Group A's `baselineIncludes` never reached
  a structure-less fw context — `axiStdIncludesFW.h` has `typedef uint8_t` types and no
  structs, and building it failed with `unknown type name 'uint8_t'` the moment the frozen
  scaffold copy was gone. The include sections no longer short-circuit on an empty
  structure set; only the struct-bearing sections do, and `systemIncludes` gates just its
  `codeMapping`-derived (struct-member) includes on structure presence.
- **Pre-existing bug fixed as a side effect.** `hierVlDemo_tbIncludesFW.h` carried the
  header guard `AXI4SDEMO_TBINCLUDESFW_H_`, copied from `axi4sDemo` when the example was
  created. Any translation unit including both headers would have silently skipped the
  second. The re-scaffold derives `HIERVLDEMO_TBINCLUDESFW_H_`.

**Re-scaffold gate.** 50 owned FW artifacts across 19 projects (both layouts: functional
`examples/simple`, hierarchical `examples/nested`, `debayer`, multi-node `examples/ip_test`)
were deleted, re-scaffolded with `make newmodule` and regenerated. **Every PARAM line came
back byte-identical**, including the `--context=` values that differ by layout
(`simple.yaml` vs `../../yaml/nested.yaml`). Every other changed line was accounted for:
25 headers lose the two includes, the namespace open/close and one blank; 99 namespace
open/close pairs appear inside regions (4 per header, 3 for the structure-less one); 25
`.cpp` preambles relocate; plus the single header-guard fix above.

**Propagation requirement for trees not re-scaffolded here (review finding, deliberately
not automated).** Because `codeText` preserves out-of-region content verbatim, a tree still
holding the legacy FW shape gets `fw_ns` nested inside `fw_ns` the first time it runs
`make gen` on this builder. Reproduced by the reviewer against a scratch copy of the
pre-change `simpleIncludesFW.h`. In this workspace the only such artifacts are
`isp_shared`'s `isp_typesIncludesFW.*` and `shared_typesIncludesFW.*`, and they are not
exposed: `isp_shared/builder` is a **separate** builder checkout (submodule commit
`7fd14fe`, versus `7fb9055` here), so they regenerate against a tree without this change.
The propagation step, when that submodule's builder is updated, is the same
delete-then-`make newmodule`-then-`make gen` performed here — not a code change. A
migration phase was NOT added, per the standing decision that FW artifacts are wholly
generated and re-scaffold is the mechanism. The now-misleading claim that `includeFW`
needs nothing from migration was corrected at `pysrc/migrateOrphans.py:129-135`: the entry
does self-cancel in the sweep's legacy-minus-current fileMap diff, but that is a statement
about the fileMap entry, not about the file's content.

**Out of scope.** `examples/ip_test/bridge/fw/bridgeStdTopIncludesFW.{h,cpp}` are orphans —
no project's gen file list contains them, which is why they still carry a pre-`--project`
PARAM stamp. They were left untouched; they belong to an orphan sweep, not to this change.
`debayer`'s `fw/isp_typesIncludesFW.*` and `fw/shared_typesIncludesFW.*` are isp_shared-owned
and regenerate against that submodule's own checkout. Old-style and new-style FW headers
interoperate freely: the cross-context `#include` lines sit above the namespace in both
forms, so a new-style header including an old-style one nests nothing.

**Gates.** `unittest/run_all_tests_parallel.sh` 89/89. All 19 projects
`make clean` then `make -C rundir -j8 all` + `make run` exit 0 (the two definitions-only
`common` projects have no `run` target by design; `debayer`'s rundir has no `run` target
either — it runs through `regrLauncher.py`, so its binary was run directly and reported
"No error"). Idempotence: a second full `make clean && make gen` across all 19 projects
rewrote nothing. Fresh-scaffold proof: `simpleIncludesFW.{h,cpp}` and
`nestedIncludesFW.{h,cpp}` were deleted, re-scaffolded from nothing and regenerated
byte-identically, then built and ran green; their only remaining out-of-region content is
the include guard, the copyright line and the PARAM line.

## 10c. Follow-on: out-of-region scaffold sweep, Group B (LANDED 2026-08-06)

Group A deferred four in-region include reductions because they need a fix-up pass over
existing files. This change makes them, at three emission sites, under the two standing
rules: a generated region emits an include only when a generated line names a symbol from
it or the database directs it (rule 1), and an ideal create-once scaffold is markers and
comments only (rule 2). Every removal was re-measured first, and the measurement changed
the answer at one of the three sites.

**Measurement.** Generated-region versus user-region symbol counts across the whole
corpus (90 block `.cppm`, 30 context `.cppm`, 17 `<block>Config.cpp` in `builder/base`,
`builder/pro` and `debayer`; `isp_shared` excluded, it pins an older builder):

| site | header | named in a GENERATED region | named in a USER region |
| :--- | :--- | ---: | ---: |
| B1 `<block>.cppm` | `bitTwiddling.h` | 0 | 0 |
| B1 | `q_assert.h` | 0 | 60 (20 files) |
| B1 | `<algorithm>` | 0 | 5 (1 file) |
| B1 | `systemc.h` / `logging.h` | 466 / 90 | — |
| B2 `<ctx>Includes.cppm` | `bitTwiddling.h` | 202 (`clog2` 101, `pack_bits` 84, `unpack_bits` 36) | 0 |
| B2 | `q_assert.h` | 84 (`Q_ASSERT`) | 0 |
| B2 | `<algorithm>` | 109 (`std::min`) | 0 |
| B2 | `systemc.h` | 1211 | 0 |
| B3 `<block>Config.cpp` | `systemc.h` | 0 | 7 (1 file) |
| B3 | `<string>` | 17 (one per file) | — |

**Landed.**

- **B1 `blockModuleHeader` reduced to `systemc.h` + `logging.h`** (plus the DB-directed
  dependency includes it already emitted). The measurement confirmed Group A's premise
  exactly: nothing generated in a block `.cppm` names a `Q_ASSERT` macro, a
  `std::<algorithm>` call or a bitTwiddling symbol. `systemc.h` stays for the
  `SC_MODULE`/`SC_HAS_PROCESS` class and its `sc_` port types, `logging.h` for the
  generated `logBlock log_;`.
- **B2 `moduleHeader` is now derived, not a fixed list — and the premise was WRONG.** The
  brief expected the same "0 generated uses" answer here; it is not. A context module's
  own generated regions name `Q_ASSERT` and `std::min` (the struct round-trip test region,
  `structures.py::_roundTripHelperLines`), `pack_bits`/`unpack_bits` (the struct pack
  code) and `clog2` (parameterized width expressions). All five headers are therefore
  justified by rule 1 for a struct-bearing context, and deleting them would have broken
  every one. The premise's proposed mechanism was also incomplete: the
  `widthLog2`/`widthLog2minus1` predicate decides `clog2` only, not `pack_bits`.
  What landed instead makes each entry answerable:
  - `systemc.h` unconditional, as the whole-file baseline. It is what supplies `uint*_t`
    to a struct-less context's typedefs — the exact failure C1 hit (`unknown type name
    'uint8_t'`), so this one is deliberately NOT conditional.
  - `logging.h`, `<algorithm>`, `bitTwiddling.h` now come from
    `structures.py::systemIncludes` in `module`/`headerIncludes` mode, i.e. from the same
    `codeMapping`/`includeMapping` tables the non-module header path uses, so the two
    cannot drift. The answer to Group A's open question is that this path did NOT already
    cover the context unit: `include_cppmTemplate` has no `structures --section=headerIncludes`
    region, and cannot have one — an `#include` must sit in the global module fragment,
    above `export module`. The GMF emitter is therefore the right owner, and
    `systemIncludes` now takes an explicit `(mode, section, hasStructures)` rather than
    reading `args`, because its new caller's own section name is not one of its own.
  - `q_assert.h` is gated on the context declaring structures, because the round-trip test
    region is what names `Q_ASSERT`. The non-module path proves the intent: `structTest`
    emits `#include "q_assert.h"` itself at its point of use on the `not useConfig` branch,
    which a module unit cannot do.
  - `bitTwiddling.h` additionally follows the `clog2` fact, which is now a
    `projectOpen` view field (`getContextData` -> `usesClog2`) rather than a broad
    `prj.data['types']` walk inside a template. `templates/systemc/headers.py` consumes
    the same field, so the two call sites share one derivation.
  Net effect on the corpus: the two struct-less contexts
  (`examples/axiDemo/model/axiStdIncludes.cppm`, `examples/mixed/model/mixedIncludeIncludes.cppm`)
  drop to `systemc.h` alone; the other 26 keep the same five headers in
  codeMapping-derived order.
- **B3 `tb_config_prerequisites` drops `#include "systemc.h"`.** No generated line in a
  `<block>Config.cpp` names a SystemC symbol; the scaffolded `createTestBench`/`final`
  bodies reach it transitively through `instanceFactory.h` -> `blockBase.h`. `<string>` STAYS
  (the generated registration lambda spells `std::string`), as already decided, and so do
  `instanceFactory.h`, `testBenchConfigFactory.h`, the per-context `<ctx>VariantConfig.h`
  and `import a2c.endOfTest;`.
- **Relocation, not stripping: 22 include lines added to 21 files' USER slots.** Per
  project: `apbDecode` 2, `axi4sDemo` 2, `axiDemo` 1, `hierVlDemo` 2, `ip_test` 3,
  `nested` 1, `pySocket` 1, `simple` 1, `simple_ip` 2, `xif` 1, `pro/lmmiDemo` 1,
  `debayer` 4. 20 files gain `#include "q_assert.h"`, `debayer`'s `model/interpolate.cppm`
  also gains `#include <algorithm>` (`std::max`/`std::min`/`std::clamp` in its user body),
  and `examples/pySocket/tb/pySocket/pySocketConfig.cpp` gains `#include "systemc.h"`. The
  generator's emission is NOT conditional on user-region text — that would be forbidden
  inference and would churn includes on every user edit.
  Honest note on how load-bearing that is: measured on this toolchain, none of the 22 are
  strictly required — `systemc.h` alone already compiles `std::clamp`/`std::max`, and
  `logging.h` alone already compiles `Q_ASSERT_CTX` (it includes `q_assert.h`), and the
  Config's `instanceFactory.h` -> `blockBase.h` already supplies `systemc.h`. They were
  relocated anyway, because a user body's prerequisite belongs in the user slot by rule 1,
  and because silent reliance on a transitive supplier is exactly the fragility that made
  the Group A `instanceFactory.h` and C1 `<cstdint>` removals break only on a fresh
  scaffold.
- **Porter fix-up.** `migrateTbConfig.PREREQ_INCLUDES` loses `systemc.h`, so a legacy
  preamble copy now RELOCATES to the user slot instead of being deleted — the same
  correction `workerThread.h` needed in the External shape. `unittest/test_migrate_tb_port.py`
  asserts the relocation directly, and its existing pin (the drop set derived from the
  template's own emission) keeps the two from drifting.
  `migrateBlockModulePort.BLOCK_SHAPE.dropIncludes` needed no change: it lists only
  `systemc.h`, which the block GMF still emits, and the three removed headers were never
  in it, so a legacy copy of one already relocated.
- **Scaffolds needed no change.** Neither `blockModule_cppm`/`blockRegsModule_cppm`,
  `include_cppmTemplate` nor `tbConfigTemplate` carries an out-of-region copy of any
  removed header, so Group A's "a fresh file carries it twice" trade does not recur here.

**Fresh-scaffold proof (the decisive gate).** Five artifacts across three projects were
deleted, re-scaffolded from nothing with `make newmodule`, regenerated and BUILT, then
restored from a byte copy (never `git checkout` — the working tree is ahead of HEAD):

- `examples/simple/model/consumer.cppm` (block), `examples/simple/model/simpleIncludes.cppm`
  (struct-bearing context) and `examples/simple/tb/simple/simpleConfig.cpp` (Config) —
  built together, exit 0. The fresh Config compiles with no `systemc.h` anywhere in the
  file, which is the transitive-supplier check Group A's `instanceFactory.h` deletion
  failed and C1's `<cstdint>` removal failed.
- `examples/axiDemo/model/axiStdIncludes.cppm`, the struct-LESS context: freshly scaffolded
  it carries `#include "systemc.h"` alone in its GMF and builds, proving the typedef-only
  context still gets `uint8_t`.
- `examples/simple_ip/ip/model/ip.cppm`, a parameterizable (variant-bearing, register- and
  memory-owning) block: freshly scaffolded and built, exit 0.

All three projects were then restored, `make clean && make gen`-ed, rebuilt and re-run
green, and `simple_ip` re-ran its verilated cosim green.

**Deviation, recorded not forced.** Three existing files carry no `// user #includes here`
slot label at all — `examples/ip_test/ip/model/ip.cppm`,
`examples/ip_test/src/model/src.cppm`, `examples/simple_ip/ip/model/ip.cppm`. The label is
out-of-region content, so `make gen` can never add it (rule 2 again, in its absence form).
Their relocated include was placed in the same GMF user zone (between the
`blockModuleHeader` region's end and the `moduleExport` region, so a non-modular header
still attaches to the global module) and the missing label seeded above it by hand, once.
The seeded wording is the corpus-majority `// user #includes here` (82 files) rather than
the current scaffold's longer form (30 files) — the label is frozen out-of-region text, so
the two forms already coexist and matching the majority keeps these three consistent with
their siblings. No migration phase was invented for this; if more such files appear, the
same one-line seed is the fix.

**Propagation requirement for trees not relocated here.** The B1 reduction removes three
includes from a GENERATED region, so any project already on `.cppm` loses them on its next
`make gen`, with no migration step and no TODO — `migrateBlockModulePort.BLOCK_SHAPE`
relocates them only on the legacy `.h`/`.cpp` port path. The 22 in-tree occurrences were
relocated by hand (above) and none is strictly required on this toolchain, so the exposure
is limited to out-of-tree projects whose block bodies name `Q_ASSERT`, a `std::<algorithm>`
call or a bitTwiddling symbol; the fix there is the same one-line add to the file's
`// user #includes here` slot. Deliberately not automated, and no migration phase was
invented for it.

**Review findings folded in (2026-08-06).** A review of this change caught one real defect
in the new gate: `CTX_GMF_STRUCTLESS_FORBIDDEN` originally forbade `bitTwiddling.h` in a
struct-less context, which contradicts the emitter — the `clog2` gate is independent of the
structure set, so a struct-less context declaring a log2-derived width legitimately carries
it, and the gate would have failed the first such fixture. `bitTwiddling.h` moved to
`CTX_GMF_STRUCT_REQUIRED` instead (guaranteed there by `codeMapping['module']['fw_pack'] ==
'inline'`, now asserted across 23 struct-bearing contexts) and is no longer forbidden
anywhere. Two comment fixes followed. Two review nits were considered and left as they are,
recorded so the choice is deliberate: the view field is `usesClog2`, not `contextUsesClog2`,
even though sibling context-view fields carry the `context` prefix to avoid silently
shadowing a block-view field under `data.update` — no block view defines it, and the
unprefixed name is checked as collision-free today; and the dedup membership test in
`moduleHeader` stays, with a comment recording that it is load-bearing (it collapses the
struct-feature and `clog2` sources of `bitTwiddling.h`) rather than defensive.

**Pre-existing failure found, NOT fixed (out of scope).**
`examples/simple_ip/ip/rundir/Makefile:31` invokes `$(MAKE) run-vl-dut` without `VL_DUT=1`,
so the aggregate `run-vl` target rebuilds a non-verilated binary and dies at
`Attempted to create an instance ip of an unregistered block type ip_verif`. Its twin
`examples/ip_test/ip/rundir/Makefile:29` passes `VL_DUT=1` and is green. Proven unrelated
to this change: the same tree passes when the flag is supplied
(`make all VL_DUT=1 && make run-vl-dut VL_DUT=1` -> "No error", exit 0). The target is in
no gate — `base/Makefile`'s `simple-ip` runs only the top project's `run-vl` — and the file
is a project-owned scaffold-once makefile, so it is reported rather than edited.

**Gates.**
- `unittest/run_all_tests_parallel.sh`: `Ran 89 suites: 89 passed, 0 failed`.
- New unit assertions, in the style of the existing External GMF gate in
  `unittest/test_build_manifest.py`: the region reader is generalized to
  `gen_region(path, marker)` (whole-line match, so a bare region command cannot also match
  a `--section=` variant) and three gates were added beside the External one — block GMF
  (requires `systemc.h`/`logging.h`, forbids the three removed headers), context GMF
  (requires `systemc.h`; requires the struct-feature four only when the file's
  `structures` region has content, forbids all four when it does not), and tbConfig
  prerequisites (requires `<string>` + the two factory headers + the endOfTest import,
  forbids `systemc.h`). Each gate fails if it finds no regions at all. Report:
  `External GMF regions: 14 checked`, `block GMF regions: 77 checked`,
  `context GMF regions: 25 checked`, `tbConfig prerequisites regions: 14 checked`.
  The context gate was falsified in development before it passed: it initially treated a
  struct-less context's one-blank-line `structures` region as content and failed
  `axiDemo`/`mixed`, which is the distinction it exists to make.
- All 19 projects `make clean` + `make -j8 gen`: 19/19 OK.
- `make -C builder/base pipeline-test` exit 0 — `nested`, `helloWorld`, `mixed` (+`VL_DUT=1`
  + rtl lint), `pySocket` (+`VL_DUT=1` + rtl lint), `inAndOut` and `hierInclude` SV lint,
  `lint-axi`, `apbDecode` (rtl lint + run), `axiDemo`, `axi4sDemo` (`VL_DUT=1`),
  `hierVlDemo` (`VL_DUT=1`), `ip-test` (`run` + `run-vl` for top, ip and bridge),
  `simple-ip` (`run` + `run-vl`), plus the diagram/doc golden comparisons.
- Not in `pipeline-test`, run separately: `xif` build + run "No error";
  `examples/ip_test/common` and `examples/simple_ip/common` build (definitions-only, no
  `run` target by design); `pro/examples/lmmiDemo` build + run "No error"; `debayer`
  `make -j8` in `rundir` then `./build/run debayer --verbosity=medium` -> "No error",
  exit 0.
- Verilated cosim: green in `mixed`, `pySocket`, `axi4sDemo`, `hierVlDemo`, `ip_test`
  (top/ip/bridge) and `simple_ip` via the above; `simple_ip/ip` green when its makefile's
  missing `VL_DUT=1` is supplied (see the pre-existing failure above). `axiDemo` and
  `apbDecode` cosim remain deliberately omitted for the reasons recorded in
  `base/Makefile`.
- Idempotence: a second full `make clean && make gen` across all 19 projects changed no
  tracked file (`git diff` hash identical in all three repos before and after).
- `GENERATED_CODE_PARAM` lines: unchanged. Note that `git diff` against HEAD cannot show
  this directly here, because the working tree already carries the uncommitted 10a/10b/S6
  changes (which do move PARAM lines, e.g. the deleted External/Testbench `.h`/`.cpp`
  pairs and the re-scaffolded FW artifacts). What was verified instead is that the SET of
  PARAM-line differences against HEAD is byte-identical before and after this change's
  regeneration — i.e. this change adds none.

## 10d. Standing rule: purely generated files are delete-and-rescaffolded (2026-08-06)

**User decision.** Always delete and rescaffold any purely generated file. Never write a
migration porter, an in-place fix-up phase or a hand-patch for an artifact that carries no
user content. This generalises the mechanism approved for the FW includes (10b) into the
default for the whole artifact set, and it retires two items this sweep had left open: no
fail-loud shape check is needed for a legacy-shaped generated artifact, and no manual
propagation step is needed for another tree, because its first `make gen` on the new builder
replaces the file rather than preserving its frozen zone.

**Classify by hosted user content, not by a clean scaffold.** The two differ. A scaffold can
contain nothing but markers and comments while its generated artifacts still hold
hand-written code in an unmarked frozen zone. Measured out-of-region non-trivial content,
`isp_shared` excluded:

- Already clean, so rescaffolding is a no-op: `blockBase` 94/94, `include_cppm` 31/31,
  `blockRegistrar`/`foreignConfig` 22/22, `package_sv` 32/33.
- `config_hdr` 8/8 carried one frozen `#include <cstdint>` — the only outstanding artifact
  debt the rule cleared. Done, below.
- `vlScWrap` does NOT qualify, and this is not an exception to the rule: the wrapper hosts
  user code (an `end_ctor_init()` body in all 13 builder wrappers, plus a `setTimedLocal`
  override in each of debayer's 3), which makes it an ordinary user-hosted file like
  `blockModule` and `testBench`. No migration is required and none should be written. The
  narrow open item is the porter, which lost such an override once during #116; the zone
  itself is discoverable from its own descriptive comment.
- `examples/mixed/rtl/mixedEncoder_package.sv` does not qualify either: it is a user-hosted
  file that merely contains generated regions (the EXTRA_* seam). It shares its extension
  with the 32 wholly generated packages, so extension is not the discriminator.

**`config_hdr` cleared, and rescaffold alone was not sufficient.** The first rescaffold
returned the same duplicate, because `config_hdrTemplate` still emitted
`#include <cstdint>` outside the region — 10a added the region emission and accepted the
duplicate. The scaffold line was removed first, then the 8 artifacts were deleted,
re-scaffolded with `make newmodule` and regenerated. All 8 now hold exactly one `<cstdint>`
and no out-of-region content beyond the guard, the copyright line and the PARAM line.

**A frozen include guard was corrected in all 8 as a side effect.**
`<NAME>VARIANTCONFIG_H_CONFIG_H` became `<NAME>VARIANTCONFIG_H_`; the doubled suffix dates
from before the artifact was renamed off `<context>Config.h`, and no regeneration could ever
have fixed it. Third instance of the frozen-guard class, after 10b's `hierVlDemo` guard and
10a's false frozen comments. Pre-existing and not introduced here: three distinct
`ipVariantConfig.h` files (`ip_test/ip`, `ip_test/bridge/ip`, `simple_ip/ip`) share one
guard, as they did in the doubled form, so a single TU including two of them silently skips
the second.

**Method note for the PARAM gate.** A bare grep for PARAM lines in `git diff` is misleading
while the tree carries the S6 conversion, because whole files were added and deleted. Match
removals against additions PER FILE and report only a file holding both with differing text;
that is empty across all three repos, which is the statement the gate needs.

**Gates.** PARAM lines byte-identical across all 8. Unit suite
`✅ ALL TEST SUITES PASSED!` (89/89). `ip_test/ip`, `ip_test/bridge`, `ip_test`,
`simple_ip/ip`, `mixed` and `xif` all `build=OK run=OK`. `debayer` builds and
`./build/run debayer --verbosity=medium` prints `No error` at exit 0.

## 10e. Follow-on: out-of-region scaffold sweep, C3 — legacy include path retired (LANDED 2026-08-06)

Group A left `include_hdr` / `include_src` as a recorded deviation: the same class of
out-of-region content as the FW artifacts, but on a path believed dead, with "whether to
retire the entries is a separate decision". This is that decision, applied. The per-context
types artifact is now a single C++20 module interface unit and nothing reachable can ask for
the `.h`/`.cpp` pair, so the pair's scaffold, its PARAM-stamp table entries and the
header-mode selector plumbing that existed only to serve it are gone.

**The reachability gate, established by reading the code before deleting anything.** All
three conditions hold, and the second-order case (a composed child) was checked separately
because `migrateSubProjects.py` exists precisely because the gate reads one project file:

1. **An un-migrated project cannot reach generation.** `projectCreate.__init__`
   (`pysrc/processYaml.py:3563`) calls `_gateYamlFormat()` immediately after
   `mergeProjectConfig` and before the schema, address, eval or fileMap work — a project
   without `yamlFormat:`, or with an older value, exits there with the `make migrate`
   remediation. Neither `builder/base/config/project.yaml` nor `builder/pro/config/project.yaml`
   declares `yamlFormat`, so the merged view cannot satisfy the sentinel on the user's
   behalf: it must come from the user project file. `make gen` runs against a `--db` only,
   so no database means no generation.
2. **A composed child cannot smuggle the shape in either, for a different reason than the
   gate.** `FILEMAP`/`INCLUDEFILES` are built from `self.proj` alone
   (`saveIncludeFiles`, `processYaml.py:5278`), i.e. the ROOT project file merged with
   base/pro. `childProjectRaw` is consumed only by `buildProjectLayout` for the child's
   `dirs:`/segment resolution (`processYaml.py:3950-3960`), never for its fileMap. A child's
   own `include:` override therefore has no effect on the parent's generation, and the
   child's own build gates its own project file.
3. **A migrated project cannot re-request the pair.** `migrateIncludes.py` deletes the whole
   `include` line from `fileGeneration.fileMap` (`_fileMapIncludeLine` + `_deleteLine`), so
   the project inherits the base `cppm`-only definition; `config/project.yaml:192` declares
   `ext: {cppm: "cppm"}`.
4. **Phase ordering inside `make migrate` was checked, not assumed.** `restampContextParam`
   calls `contextParamMode` for every `INCLUDEFILES` key, which after this change fails loud
   on `include_hdr`. It runs in the `--sweep` phase, and `include/make/a2c-common.mk:195-203`
   runs the text phases (which remove the override) BEFORE `make db`, so the swept database
   can no longer contain the key.

**One live requester was found and fixed, and it is worth recording because the literal form
of condition 3 was FALSE at the start.** `unittest/mixed_test_arch/mixedProject.yaml:62`
declared `yamlFormat: 2` AND pinned `include` to `{hdr, src}` — a migrated project asking for
the retired shape. It is a database-only unit fixture (its Makefile has a `db` target and
nothing else; the six suites that use it call `arch2code.py --yaml --db` and read the
schema), so it could never reach a scaffold or a render, which is why the gate's PURPOSE
held. Its `include` entry was moved to the current `cppm` form rather than left as a shape
nothing can serve. Its neighbouring legacy entries (`block: {hdr, src}`, `vlScWrap`) were
left alone: those scaffold keys still exist in `fileGen.py`, so they are stale-but-servable,
and retiring the block `.h`/`.cpp` scaffold is a separate job.

**Removed.**

- **`include_hdrTemplate` + `include_hdr()` and `include_srcTemplate` + `include_src()`, with
  their two `case` arms** (`templates/fileGen/fileGen.py`). What would consume them: the
  scaffold dispatch, keyed on `<fileType>_<ext>` from the project's fileMap. No reachable
  fileMap produces `include_hdr`/`include_src` (gate above), so the arms were unreachable.
  This also removes the last out-of-region `#include "systemc.h"` in the include family and
  the `.cpp`'s out-of-region sibling `#include`, which is what Group A had deferred.
- **`'include_hdr': ''` and `'include_src': ''` from `genFileParam._CONTEXT_FILE_MODE`.** What
  would consume them: `contextParamMode`, called by the fileGen scaffolds (deleted above) and
  by `migrateProjectParam._contextModeFiles` over `INCLUDEFILES` keys (cannot contain them,
  per the phase-order check). The table is deliberately EXHAUSTIVE with no default, so the
  entries' absence is the fail-loud statement that the shape is retired.
  **Correction (2026-08-07): that fail-loud claim held for the `make migrate` path ONLY.** A
  project that hand-re-added the override got an actionable error naming the file to edit on
  the migrate path (`_contextModeFiles` → `contextParamMode`, covered by
  `unittest/test_project_param.py::test_unregistered_context_filekey_fails_loud`), but NOT on
  the `make newmodule` scaffold path: `fileGen.render` dispatches on the
  `<fileType>_<ext>` key BEFORE any template calls `contextParamMode`, and its `case _`
  default was fail-quiet (`print` + bare `exit()`, i.e. `SystemExit(None)` = status 0), so
  `make newmodule` stopped mid-loop and still reported success. See the
  **Follow-on: fail-loud dispatch + get_intf_defs contract** entry below: Item A closes that
  gap, and the scaffold path now has its own coverage
  (`test_unregistered_scaffold_filekey_fails_loud`).
- **The `return 'include_hdr'` fallback in `templates/systemc/headers.py::_file_map_key`.** It
  did NOT collapse to a single outcome, so the function stays: a `--template=headers` region
  either names its key (`--fileMapKey=includeFW_hdr`, 29 owned artifacts) or is the
  context module unit's own unkeyed region. What remains is `args.fileMapKey` or
  `include_cppm`, and the `args.mode == 'module'` test went with the fallback it guarded — it
  distinguished two outcomes that are now one. Verified output-neutral by measurement, since
  this was the one place a silent regression was possible: all 30 unkeyed
  `--template=headers` regions in the owned corpus carry `--mode=module`, so none flips, and
  the sibling `bitTwiddling.h` gate at `headers.py:15` (which keys off the same value) is
  unaffected.
- **The header-mode branch of `intf_gen_utils.cpp_context_include_lines`, and the
  `fileMapKey` selector that fed it.** The task flagged the FW header and the per-context
  config header as candidate live callers; both were checked and neither uses this function —
  the FW header goes through `headers.py::_include_context_modules` (whose textual-`#include`
  branch IS live for `includeFW_hdr` and is untouched), and the config header through
  `cpp_config_header_includes`. The seven remaining call sites are `classDecl`, `moduleScaffold`
  (`moduleExport`), `module_hdl_wrapper`, `testbench` and the three `intf_gen_utils`
  dependency helpers; two passed the literal `'include_cppm'` and five used
  `args.fileMapKey if args.fileMapKey else 'include_cppm'`. A corpus-wide inventory of
  `--fileMapKey=` values found exactly five (`package_sv`, `includeFW_hdr`, `testBench`,
  `tbExternal`, `include_hdr`), and none of them reaches those five sites: no `classDecl` /
  `moduleScaffold --section=*ModuleHeader` / `baseClassDecl` region carries a key at all, and
  the two testbench `moduleExport` keys return early through `TB_MODULE_EXPORTS` into
  `templates/systemc/testbench.py`, which never calls the three dependency helpers. The
  function now takes `(prj, context)` — with the branch gone it needed neither `data` nor the
  key — and the five sites spell `include_cppm` directly. The `.get('include_cppm', {})`
  membership test STAYS a `.get`: `saveIncludeFiles` uses `setdefault`, so a project whose
  every context is smartInclude-empty carries no `include_cppm` key at all. That is an
  optional row, not a contracted field treated as optional.
- **The `kind = 'import' if line.startswith(...) else 'include'` ternary at the two
  dependency-helper sites.** Its `'include'` outcome existed only for the header-mode line;
  every remaining line is an `import`/`using namespace` pair, so the sites append
  `('import', line)` directly. This does NOT close 10a's open finding about `kind` conflating
  `import` and `using namespace` — that prefix test is still how consumers split the two, and
  the third-`kind`-at-the-producer sweep remains deferred.
- **The now-dead `args` parameter of `sc_base_dependency_includes`,
  `sc_class_dependency_includes`, `sc_class_module_usings` and `blockRegs.get_include_deps`**
  (10 call sites across `intf_gen_utils`, `classDecl`, `baseClassDecl`, `blockRegs`,
  `moduleScaffold`). `args` was read by these for exactly one purpose, `args.fileMapKey`, and
  for nothing else. Kept parameters would have been unused flexibility with no consumer. The
  `blockRegs` wrapper was missed on the first pass and caught in review.

- **The stale include-artifact tables in `ARCH2CODE_AI_RULES.md`.** They told a reader to
  author a `headers` region with `--fileMapKey=include_hdr` and documented a paired
  `model/*Includes.cpp`. After this change that key is unservable three ways over (no scaffold
  arm, no `_CONTEXT_FILE_MODE` entry, an empty render), so following the doc would have
  produced a silently empty region. Replaced by one table for the `.cppm` module unit listing
  the regions `include_cppmTemplate` actually seeds. Other `*Includes.h/cpp` prose elsewhere in
  that document is stale from the earlier cppm conversion, not from this change, and is left
  for a doc pass.

**Not touched, deliberately.** The FW include pair (`includeFW`, `.h` + `.cpp`) is the
standing user decision recorded in 10b and is a different file type with a live scaffold, a
live `--fileMapKey=includeFW_hdr` region in 29 owned corpus artifacts and a live
textual-include path in `headers.py` (proven live, not assumed:
`examples/axiDemo/fw/include/axiDemoIncludesFW.h:7` emits `#include "axiStdIncludesFW.h"`
from that branch). `migrateIncludes.py` keeps its full legacy-shape handling: it is the code
that MAKES the gate true for a legacy project, so it must keep understanding the old form. So
does `pysrc/migrateOrphans.py:165`, which holds the other frozen `include: {hdr, src}`
snapshot — that is what lets the sweep recognize the old pair on disk, and it must not be
tidied away alongside the live path.
The block `.h`/`.cpp` scaffold (`block_hdr`/`block_src`) is equally undeclared by the current
base fileMap but was left alone as out of scope.

**Largest recorded residue, deliberately NOT retired here (found in review).** With the
include pair gone, `structures.py`'s `'model'` emission flavour — selected by an ABSENT
`--mode` (`structures.py:30-31`, with `codeMapping`/predicate entries at `:74`, `:318`, `:604`
and `:640`) — is reachable only from the two unreachable files above. Measured across base,
pro and debayer, every live file carrying a `--template=structures` region is `--mode=module`
(30) or `--mode=fw` (25); the only four with no mode are those two pairs.
`genFileParam.py:31-34` still describes the absent-mode `'model'` flavour as one of three live
flavours, and after this change no live context file key selects it (`config_hdr` and
`package_sv` are the two remaining `''` entries and they render through `config.py` and the SV
package template, not through `structures.py`). Retiring that flavour is a larger job than
this one and is not attempted here.

**Output neutrality proven by A/B, not by inspection.** Because the working tree is far ahead
of HEAD, `git diff` cannot isolate this change, so the pre-change generator was reconstructed
in place (exact reverse edits to all 10 files), all 19 projects `make clean && make -j8 gen`,
and the generated-artifact diff hashed per repo; then the post-change files were restored
byte-for-byte and the same sweep re-run. The three hashes are identical across the A/B
(`builder/base -- examples/` `83f3cddeb054f053`, `builder -- pro/examples/`
`2e681c4c2d891865`, `debayer` artifact dirs `e87b9c093fdf8866`), i.e. the retirement changes
not one byte of generated output anywhere in the corpus.

**The two corpus files that still carry a `--fileMapKey=include_hdr` region are unreachable,
each for its own reason — verified rather than assumed.**
`examples/pySocket/model/pySocketIncludes.{h,cpp}` are absent from the project's
`A2C_SC_GEN_FILES` (`examples/pySocket/.gen/build.mk:11`), so `make gen` never visits them.
`examples/inAndOut/systemVerilog/simInAndOut/inAndOutIncludes.{h,cpp}` ARE named as explicit
`arch2code.py --file` targets by `examples/inAndOut/systemVerilog/Makefile:31-32` — but only
in its `sim` recipe, and `Makefile:151-153`'s `in-and-out` target runs verilator lint only,
for the reason recorded there (the tree stays a header-mode SV-generation demo whose SystemC
sim cannot regenerate under the cppm-default include). Either way the region was already
inert before this change: both projects inherit the `cppm`-only `include`, so
`data['includeFiles']` has no `include_hdr` key and the region rendered empty. All four files
are byte-unchanged from HEAD across five full corpus regenerations here. `pySocketIncludes.cpp` does still sit in a globbed `A2C_SC_SRC_DIRS`
directory and so is still COMPILED while never being regenerated — a pre-existing orphan
condition belonging to the deferred whole-suite orphan sweep, not to this change. Nothing was
deleted: the ban on deleting implementation files applies, and a stale generated region in an
orphan is the sweep's business.

**Gates.**
- `unittest/run_all_tests_parallel.sh`: `Ran 89 suites: 89 passed, 0 failed` /
  `✅ ALL TEST SUITES PASSED!`. No unit test asserted the legacy templates existed, so no
  coverage was deleted; the retirement's fail-loud consequence is covered by the existing
  `test_unregistered_context_filekey_fails_loud`.
- All 19 projects `make clean` + `make -j8 gen`: 19/19 `gen=OK` (run four times in total —
  twice for the A/B and twice for idempotence).
- `make -C builder/base pipeline-test` exit 0: `nested`, `helloWorld`, `mixed` (+`VL_DUT=1`
  + rtl lint), `pySocket` (+`VL_DUT=1` + rtl lint), `inAndOut` and `hierInclude` SV lint,
  `lint-axi`, `apbDecode` (rtl lint + run), `axiDemo`, `axi4sDemo` (`VL_DUT=1`), `hierVlDemo`
  (`VL_DUT=1`), `ip-test` (`run` + `run-vl` for top, ip and bridge), `simple-ip`
  (`run` + `run-vl`), plus the diagram/doc golden comparisons.
- Not in `pipeline-test`, run separately: `simple` build + run `No error`; `xif` build + run
  `No error`; `examples/ip_test/common` and `examples/simple_ip/common` build (definitions-only,
  no `run` target by design); `pro/examples/lmmiDemo` build + run `No error`; `debayer`
  `make -j8` in `rundir` then `./build/run debayer --verbosity=medium` -> `No error`, exit 0.
- Fresh-scaffold proof: `examples/simple`'s `model/simpleIncludes.cppm` (the retired path's
  replacement), `rtl/simple_package.sv` and `fw/include/simpleIncludesFW.{h,cpp}` — every
  other context artifact `_CONTEXT_FILE_MODE` covers — were deleted, re-scaffolded from
  nothing with `make newmodule`, regenerated and BUILT + run green; all four came back
  byte-identical, PARAM lines included (`--mode=module` on the `.cppm`, `--mode=fw` on the
  pair, no `--mode` on the package). `examples/mixed/model/mixedVariantConfig.h` (the
  `config_hdr` entry) was deleted, re-scaffolded, regenerated byte-identical, and `mixed`
  rebuilt (`VL_DUT=1`) and re-run green.
- Idempotence: a second full `make clean && make gen` across all 19 projects left the three
  repos' `git diff` hashes unchanged (`.` `6d331a2d5db709eb`, `builder` `176b3761285cd3c1`,
  `builder/base` `87a4717b8e8b9170`).
- `GENERATED_CODE_PARAM` lines: unchanged by this change. Measured with 10d's per-file
  method — 20 files hold both a PARAM removal and a PARAM addition with differing text, and
  every one is a pre-existing S6/10a-10d item (the `<block>Config.cpp` region split collapsing
  five PARAM lines to one, the deleted External/Testbench `.h`/`.cpp` pairs, plus `fileGen.py`
  and two docs quoting PARAM lines as prose). The A/B above is the stronger statement: the
  generated-artifact bytes, PARAM lines included, are identical with and without this change.
- Pre-existing failure re-confirmed, NOT fixed: `examples/simple_ip/ip/rundir/Makefile:29`
  invokes `$(MAKE) run-vl-dut` without `VL_DUT=1` (line 28 does pass it to `all`), so
  `make run-vl` in that tree dies at `Attempted to create an instance ip of an unregistered
  block type ip_verif` (exit 2). Green when the flag is supplied:
  `make -j8 all VL_DUT=1 && make run-vl-dut VL_DUT=1` -> `No error`, exit 0. 10c cites this
  as line 31; the `run-vl-dut` recipe line is 29 and the `run-vl-dut` target is 31.

## 10f. Follow-on: testbench.py contracted-field sweep (LANDED 2026-08-07)

Scope: `templates/systemc/testbench.py` only. Behaviour-preserving removal of `.get()`
fallbacks on fields the DB/view contract guarantees, per the builder rule that required
fields on existing DB/view rows are read directly and only optional rows / optional
relationships are branched on.

### Fixed — contracted, now read directly

| Site (post-change line) | Before | After |
| :--- | :--- | :--- |
| `_ext_channel_includes` 190 | `data.get('connectionMaps', dict())` | `data['connectionMaps']` |
| `_ext_channel_includes` 193 | `prj.data['interfaces'].get(value.get('interfaceKey', ''))` + `if intfInfo:` guard | `prj.data['interfaces'][value['interfaceKey']]`, guard removed |
| `ext_sec_init` 321 | `data_.get('variant', '')` | `data_['variant']` |
| `ext_sec_init` 325 | `v.get('instance')`, `v.get('direction')` | `v['instance']`, `v['direction']` |
| `ext_sec_init` 350/353/354 | `data.get('connectionMaps', dict())`, `value.get('instance','')`, `value.get('instancePortName','')` | direct |
| `ext_sec_init` 368 | `data.get('prunedConnections', dict())` | `data['prunedConnections']` |
| `ext_sec_body` 392 | `data.get('prunedConnections', dict())` | `data['prunedConnections']` |
| `ext_sec_body` 408 | `data.get('connections', dict())` | `data['connections']` |
| `ext_sec_body` 418/421/422 | `data.get('connectionMaps', dict())`, `value.get('instance','')`, `value.get('instancePortName','')` | direct |
| `ext_sec_header` 478/481/482 | same connectionMaps trio | direct |
| `ext_sec_header` 483 | `prj.data['interfaces'].get(value.get('interfaceKey',''))` + `if not intfInfo: continue` | direct subscript, guard removed |
| `ext_sec_header` 487 | `intfInfo.get('maxTransferSize', '0')` | `intfInfo['maxTransferSize']` |
| `ext_sec_header` 490-492 | `data.get('subBlockInstances', {}).get(value.get('instanceKey',''), {}).get('instanceConfigSelection')` | `data['subBlockInstances'][value['instanceKey']]['instanceConfigSelection']` — whole chain direct, see "row lookup" below |

Contract evidence:

- `connectionMaps` / `connections` / `prunedConnections` / `connectDouble`: `getBlockData`'s
  `blockDataSet` (`processYaml.py:1308`) lists all four and `:1322` does
  `for k in blockDataSet: ret[k] = dict()`, so every key exists on every block view.
- `subBlockInstances`: assigned unconditionally at `processYaml.py:1975` and already read
  directly at `:2155`, `:2216`, `:2319`, `:2347`.
- `connectionMaps.instance` / `.direction` / `.block` / `.interface` are
  `_type: required` in `config/schema.yaml`; `instancePortName` / `portName` are
  `auto(...)`. Measured over 28 databases: 50 of 50 connectionMaps rows carry
  `instance`, `instancePortName`, `instanceKey`, `portName`, `direction` and
  `interfaceKey` populated, zero null/empty.
- `connectionMaps.interfaceKey` is always resolvable. A `required` validated field takes the
  `ret[field+'Key'] = varInfo[...] + '/' + varContext` path (`processYaml.py:6485`); the only
  ways it is not a live interfaces key are `'InvalidValueInYaml'` (`:6505`), which is
  accompanied by `logError` and aborts, and the `optional`-and-empty `""` path (`:6468`),
  which `required` cannot reach. Measured 50/50 rows resolvable. `processYaml.py:2388`
  and `:2394` already do `self.data['interfaces'][connVal['interfaceKey']]` directly.
- `interfaces.maxTransferSize` is `optionalConst(0)` (`config/schema.yaml:191`), so it always
  materialises: measured 88 interface rows across 26 databases, zero null.
  `templates/systemc/constructor.py:148` already reads it directly. The stored value is TEXT
  when defaulted and INTEGER when the user authored one; because the field is always present
  the direct read reproduces the old value exactly, so no coercion was added.

The two `intfInfo` guards were REMOVED rather than left as harmless redundancy: with a
`.get()` lookup an unresolvable `interfaceKey` would silently drop a channel header include
or a whole local-only channel declaration, producing a subtly wrong artifact. A direct
subscript fails loud at the defect, which is the behaviour the rule exists to get.

### Deliberately left as `.get()` — genuinely optional

- `endvalue.get('crossInterface')` (`ext_sec_init` 370): set only where a cross-interface bind
  exists (`processYaml.py:2695`, `:2723`, `:2750`). Optional relationship.
- `get_intf_defs(...).get('multiDst', False)` (`ext_sec_body` 394): left UNCHANGED, but the
  stated reason for leaving it ("optional `interface_defs` field, absent for most protocols")
  is WRONG — see the discrepancy note below.
- `data['includeFiles'].get('include_cppm', {})` (`_tb_context_lines` 21): INCLUDEFILES
  carries no `include_cppm` key at all when every context is smartInclude-empty. Optional
  file type, already established as legitimate.
- Line 161 is prose inside a comment (`tb.get()`); line 594 is a `shared_ptr::get()` in a
  Jinja template. Neither is a dict access.

### The `subBlockInstances` row lookup is ALSO contracted — the old comment was wrong

The pre-change chain ended `.get(value.get('instanceKey',''), {}).get('instanceConfigSelection')`
and the pre-change comment justified it with "None when the instance is absent or not
parameterizable". Both halves of that justification are false, so the whole chain is now a
direct subscript and the dead `else None` branch is gone:

- The row is never absent. `getBDConnectionMaps` admits a row into `ret['connectionMaps']`
  only when `connMap['instanceKey'] in containedInstances` (`processYaml.py:2322`), and
  `containedInstances` there is bound from `ret['subBlockInstances']` (`:2319`) — the same
  object `getBDInstances` assigned at `:1975`. `getBDInstances` runs first in `getBlockData`
  and `ret['subBlockInstances']` is assigned exactly once in the whole file, so the
  membership test is against the very dict the template later indexes.
- `instanceConfigSelection` is never None: it is set unconditionally for every contained
  instance (`processYaml.py:2015`) and every excluded instance (`:2054`). Non-parameterizable
  children are represented by `isParameterizable: False` INSIDE the dict, not by its absence.
- Runtime proof through the real view code, not just by reading it: a read-only probe opened
  24 databases and built 310 `getBlockData()` views (both `trimRegLeafInstance` settings),
  yielding 73 `connectionMaps` rows. Rows whose `instanceKey` was absent from
  `subBlockInstances`: **0**. Rows present but lacking `instanceConfigSelection`: **0**.

This site was NOT in the enumerated task list — the task asked only for the outer
`data.get('subBlockInstances', {})` and the inner `value.get('instanceKey','')`. It was found
while verifying, and fixed because the rule is categorical: treating a contracted
relationship as optional is the violation, and a dead `else None` in a template is exactly
the defensive shape the rule exists to remove.

### Provenance findings for the verify-first items (both proved contracted, both fixed)

- `data_['variant']` (`ext_sec_init` 321): `data_` iterates
  `data['subBlockInstances'].values()`. `getBDInstances` builds that dict as
  `containedInstances[inst_key] = inst_data` where `inst_data` is a raw
  `self.data['instances']` row (`processYaml.py:1930`), enriched IN PLACE — not a synthesised
  dict. The same rows are read as `inst_data['variant']` at `:1936` and
  `instInfo['variant']` at `:2001`. `instances.variant` is schema `optional`, so it always
  materialises; measured 198 instances rows across 26 databases, zero null. Contracted.
- `v['instance']` / `v['direction']` (`ext_sec_init` 325): `v` iterates
  `data['connectDouble'][channelType][connKey]['ends']`. `getBDConnectionsFinal`
  (`connMapping`, `processYaml.py:2768`) sources `connectDouble` from `ret['connections']`
  and `ret['registerConnections']` as `dict(connVal)` shallow copies, so the `ends` dicts are
  the originals. Both feeders guarantee both fields: `connections.ends` declares
  `direction: required` and `instance: required` in `config/schema.yaml:422`, and the
  synthesised registerConnections ends set both explicitly (`processYaml.py:2246-2247`,
  `:2306-2307`). Measured 280 connections-ends rows, zero null/empty in either field. The
  one ends shape in the file that lacks `instance` — the zero-instance definition-driven
  `connectionPorts` end at `processYaml.py:2440` — never reaches `connectDouble`.
  Contracted.

### Discrepancy: `multiDst` is contracted, NOT optional — deliberately left for a follow-up

`ext_sec_body:394` still reads
`get_intf_defs(get_intf_type(value['interfaceType'], data), data).get('multiDst', False)`.
It was classified as a genuinely optional field and left alone; that classification does not
survive checking:

- `config/schema.yaml:177` declares `multiDst: optional(False)` on `interface_defs`, so it
  always materialises on the row.
- Measured 314 `interface_defs` rows across 24 databases: `multiDst` NULL in **0** of them,
  and always stored as INTEGER (290 rows `0`, 24 rows `1`) — never absent, never text.
- So this is a contracted-field fallback of exactly the kind this sweep removes.

The optionality that DOES exist here is one level up and is unrelated to the `.get()`:
`get_intf_defs` returns `None` when the interface type is not in `block_data['interface_defs']`
(`pysrc/intf_gen_utils.py`), and the current chained call would raise on `None` anyway, so the
`.get('multiDst', False)` is not what guards that case.

It was NOT changed, because the task defining this sweep listed it explicitly under
"leave these alone" and instructed that a claim found to be false be reported rather than
worked around. Recommended follow-up: `...['multiDst']`, together with the sibling
`pysrc/intf_gen_utils.py:240` `interface_defs.get(intf_type, {}).get('multiDst', False)`,
decided as one change since both encode the same assumption.

### Gate results

- Unit suite (`./unittest/run_all_tests_parallel.sh`):
  `Ran 89 suites: 89 passed, 0 failed`, `Total wall-clock: 22s`, exit 0. Matches baseline.
- All example projects `make clean && make -j8 gen` (19 projects bottom-up — ip_test
  common/ip/bridge/top, simple_ip common/ip/top, apbDecode, axi4sDemo, axiDemo, helloWorld,
  hierVlDemo, mixed, nested, pySocket, simple, xif, lmmiDemo, debayer — plus the two
  `arch`-only trees hierInclude and inAndOut): `GEN_ALL_RC=0`, zero `GEN FAILED`.
- `make -C builder/base pipeline-test`: exit 0, tail `No error`.
- debayer: `make clean && make -j8 gen` exit 0; `cd rundir && make -j8` exit 0;
  `./build/run debayer --verbosity=medium` exit 0, printing `No error`.
- debayer regression (`cd rundir && make regr`):
  `Run session completed succesfully (runs: 44, passed: 44, failed: 0, skipped: 0) [0:03:49]`,
  exit 0. Matches baseline.
- Idempotence: a second `make gen` over the whole corpus changed nothing — the md5 manifest
  is identical before and after the second pass, for the original template, the
  intermediate edit, and the final version (`M1`/`M2`, `M3`/`M4`, `M8`/`M9`).

Every gate above was re-run from scratch on the FINAL version of the file (after the
`subBlockInstances` fix), not only on the intermediate one: unit suite
`Ran 89 suites: 89 passed, 0 failed`; corpus clean + gen `GEN_ALL_RC=0`; `pipeline-test`
exit 0 with 38 `No error` lines; debayer gen + build + run exit 0 with `No error`; debayer
regression `runs: 44, passed: 44, failed: 0, skipped: 0 [0:03:50]`.

### A/B byte-identity proof

Manifest = md5 of every file under `/work/ws/debayer` excluding `.git`, `*.db`,
`__pycache__`/`*.pyc`, `obj_dir`, `build`, `.d`, object/archive artifacts, `gv_out`, and the
edited template itself.

First pass, over 6089 files (before the `subBlockInstances` fix was found):

1. `M1`: original template, clean + gen across the corpus.
2. `M2`: original template, gen again -> `diff M1 M2` empty (baseline idempotent, zero
   manifest noise, so the comparison has no confounder).
3. First edit applied.
4. `M3`: clean + gen -> **`diff M2 M3` empty.**
5. `M4`: gen again -> `diff M3 M4` empty.

Final pass, re-run from scratch after the `subBlockInstances` fix so the proof covers the
file as it actually lands, over 6179 files (the count grew only because the earlier gate runs
left `.gen/*.mk` build manifests and `rundir/regr/` logs in the tree):

6. `M7`: original template restored verbatim from the saved pre-change copy, clean + gen.
7. Final template restored.
8. `M8`: clean + gen -> **`diff M7 M8` empty. Zero differing bytes across all 6179 files.**
9. `M9`: gen again -> `diff M8 M9` empty.

Step 8 is the load-bearing statement: the whole change, both edits together, is byte-neutral
against the untouched original across the entire corpus.

`GENERATED_CODE_PARAM` stability was checked per file (removals matched against additions
within the same file, not by a tree-wide grep) across all three working trees — the debayer
superproject, the `builder` submodule, and the nested `builder/base` submodule. Exactly 20
files hold both a removal and an addition with differing text, the same 20 already recorded
in 10e: 17 `<block>Config.cpp` region splits collapsing five PARAM lines to one (with the
`--block=<tb> --excludeInst=...` PARAM relocated into the newly added
`<block>External.cppm` / `<block>Testbench.cppm`), plus `templates/fileGen/fileGen.py` and
two docs quoting PARAM lines as prose. None is attributable to this change: **all 20 carry
an IDENTICAL md5 in `M2` and `M3`.**

### Known items confirmed still open, deliberately NOT touched

- `templates/systemc/baseClassDecl.py:315` defaults `maxTransferSize` to integer `0` while
  the schema default materialises as string `"0"`; `trackerType` and `multiCycleMode` on the
  same rows are likewise `.get()`-defaulted there. Out of scope.
- `pysrc/processYaml.py:3119` `(ret.get('subBlockInstances') or {})`. Out of scope.

### multiDst follow-up (LANDED 2026-08-07)

Removed the `multiDst` contracted-field `.get()` fallback at the two sites named in 10f.
`config/schema.yaml:177` declares `multiDst: optional(False)` on `interface_defs`, so the
field always materialises: 314 `interface_defs` rows across 24 databases, zero null, always
stored as INTEGER (290 rows `0`, 24 rows `1`).

The two sites did NOT start from the same form, and reconciling them was the substance of
the change. Both are now a direct subscript:

- `templates/systemc/testbench.py:394` (`ext_sec_body`, over `prunedConnections`) —
  `get_intf_defs(...).get('multiDst', False)` became `get_intf_defs(...)['multiDst']`.
- `pysrc/intf_gen_utils.py:240` (`sc_connect_channel_type`, over `connectDouble`) — was
  `interface_defs.get(intf_type, {}).get('multiDst', False)`, i.e. an optional-ROW fallback
  *and* a contracted-field fallback stacked, and became
  `interface_defs[intf_type]['multiDst']`.

**`get_intf_defs` `None` finding.** `get_intf_defs` (`pysrc/intf_gen_utils.py:993`) ends
`return interface_defs.get(intf_type, None)`, so in isolation it can return `None`. It
cannot at these call sites, because the row is contracted-present:

- `getBDGetIntfStructs` (`pysrc/processYaml.py:1846`) registers
  `ret['interfaceTypes'][intf_type]` **unconditionally**, and `getBDConnections` calls it for
  every entry in `connections` (`:2395`). The narrower registration at `:2390` is gated on
  `connectionCount > 1 or isPort`, but `:2395` is not, so the
  `connectionCount == 1 and allowSingleEnded` case is covered too.
- Pruned connections are popped out of `connections` only *after* that loop
  (`:2401-2404`), so every `prunedConnections` row was registered before it moved — which is
  what makes the testbench site safe.
- `registerConnections`, the other half of `connectDouble` (`connMapping`, `:2768`), lands in
  `registerInterfaceTypes` and is resolved through `mappedFrom` by `getBDInterfaceDefs`
  (`:3149-3162`), which then fills `ret['interface_defs'][intf_type]` for every registered
  type. Alias resolution agrees on both sides: the view keys on the canonical
  `interfaceType`, and the call sites resolve `reg_rw`-style aliases through
  `get_intf_type` before looking up. The premise that closes the argument — every `reg_*`
  alias is guaranteed a `mappedFrom` row in scope — rests on two facts. First, the alias set
  is closed: the alias is built as `'reg_' + regType` (`processYaml.py:2231`, `:2261`,
  `:2283`) and `regType` is schema-validated to exactly `{ro, rw, ext, memory}`
  (`config/schema.yaml:522-529`), so there are exactly four possible aliases. Second, the
  four `mappedFrom` entries that cover them are not user-supplied: `reg_ro`/`reg_rw` come from
  `interfaces/status/status_if.yaml`, `reg_ext` from
  `interfaces/external_reg/external_reg_if.yaml`, and `reg_memory` from
  `interfaces/memory/memory_if.yaml`, and all three files are `systemFiles` read from
  `a2cProj` (`config/project.yaml:9,14,15`, loaded at `pysrc/processYaml.py:3597-3600`) rather
  than from the user project, so a user can neither omit nor override them.

So the direct subscript is correct at both sites, and neither fallback was protecting
anything. Note that the two forms failed *differently* before, which is why the naive
symmetric edit was not safe to assume: on a missing row the testbench site already crashed
either way (`AttributeError: 'NoneType' object has no attribute 'get'` before,
`TypeError: 'NoneType' object is not subscriptable` after), whereas the `intf_gen_utils`
site defaulted to `{}` and returned `False` without raising. The `intf_gen_utils` row
fallback was therefore dead code rather than a live guard, and removing it is not a
behaviour change; had the row been genuinely optional there, the fallthrough would also have
misreported the fault, since the diagnostic it reaches reports an ends-count error rather
than a missing interface definition.

Row-presence and reachability were measured, not only reasoned. Probes at both sites over
the whole corpus (15 example projects plus debayer, clean + gen) and the 89-suite unit run
recorded **2 hits, both at the `intf_gen_utils` site**, both
`intfType='reg_rw' resolved='status' rowPresent=True raw=1 rawType=int`. A separate
read-only sweep of 269 `connectDouble` and `prunedConnections` rows across every corpus
database (including 88 pruned rows, the exact testbench-site population) found zero rows
resolving to a missing `interface_defs` entry. The `testbench.py` site's `len(ends) > 2`
guard never fires anywhere in the corpus, so its change rests on the contract argument above
rather than on execution coverage.

Adjacent contracted-view-field fallbacks on the same and neighbouring lines were left alone
as out of scope: `pysrc/intf_gen_utils.py:235` `block_data.get('interface_defs', {})`,
`get_intf_type` at `:33` `block_data.get('interface_type_mappings', {})`, and `get_intf_defs`
itself at `:1003-1004` `interface_defs.get(intf_type, None)`. All three keys are
unconditionally initialised by `getBlockData`. **CLOSED 2026-08-07 by Item B of the follow-on
entry below** — all three now read directly.

**Integer versus bool.** The removed default was the Python bool `False`; the stored value is
INTEGER `0`/`1`. Both are falsy. Each site consumes the value exactly once, in `if not
multiDst:`, and neither compares with `is False` / `== False` nor serialises it into emitted
text, so `0` versus `False` cannot reach any artifact. Verified by grep over `templates/`
and `pysrc/`: the only uses of the `multiDst` local are the assignment and that test.

Gate results:

- Unit suite (`./unittest/run_all_tests_parallel.sh`): `Ran 89 suites: 89 passed, 0 failed`.
- Whole corpus `make clean && make -j8 gen`: all 16 trees OK, exit 0.
- `make -C builder/base pipeline-test`: exit 0.
- debayer `make -j8 gen` + `cd rundir && make -j8` + `./build/run debayer
  --verbosity=medium`: exit 0, prints `No error`.
- debayer regression `make regr`: `runs: 44, passed: 44, failed: 0, skipped: 0 [0:03:47]`.
- Idempotence: a second `make gen` with no clean reproduced the snapshot exactly.

**A/B byte-identity proof.** Snapshot = md5 of all 711 generated text artifacts (`*.cpp`,
`*.h`, `*.hpp`, `*.cppm`, `*.sv`, `*.svh`, `*.v`, `*.f`, `*.mk`, `*.adoc`, `*.txt`, `*.json`,
`Makefile`) across the example corpus and the debayer trees, excluding `obj_dir`, `build`,
and `__pycache__`. `snapshot-A` was taken after a full clean + gen with both files restored
verbatim from saved pre-change copies. `snapshot-C` was taken after a full clean + gen on the
FINAL form of both edits. **`diff snapshot-A snapshot-C` is empty — zero differing bytes
across all 711 artifacts.** A further snapshot after a second gen matched `snapshot-C`
exactly, so the result is idempotent as well as neutral. (An intermediate `snapshot-B`, taken
before the `intf_gen_utils` row fallback was shown to be dead and flattened, was also
byte-identical to `snapshot-A`; every gate below was re-run from scratch on the final form.)

`GENERATED_CODE_PARAM` was checked per file (removals matched against additions within the
same file) across the debayer superproject, `builder`, and `builder/base`. The files that
hold both with differing text are the pre-existing 10e/10f set already recorded above; none
is attributable to this change, which produced no generated-file delta at all and whose own
diff touches zero `GENERATED_CODE_PARAM` lines.

### Follow-on: fail-loud dispatch + get_intf_defs contract (LANDED 2026-08-07)

Two SHOULD-FIX findings from the reviews of the 10e/10f work above, plus the plan-record
corrections they imply. Item A changes an error path only; Item B is output-neutral.

**Item A — `templates/fileGen/fileGen.py` scaffold dispatch was fail-QUIET.** The `case _`
default of `render`'s `match data['target']` was `print(...)` followed by a bare `exit()`.
A bare `exit()` raises `SystemExit(None)`, which is exit status **0**, and `pysrc/renderer.py`
installs no `except`, so nothing intercepted it. `pysrc/newModule.py:480` assigns
`data['target'] = fileKey` straight from the `INCLUDEFILES` key, so any `<fileType>_<ext>`
pair a fileMap can name — including one with no case arm — reached that default.

The consequence was that `make newmodule` printed one line, terminated mid-loop, and still
reported SUCCESS: `newModule.create_from_templates` renders the remaining context artifacts
and then `scaffold_create` (`newModule.py:123`, the create-once user makefiles) in the same
pass, and all of it was skipped. The state is authorable, not hypothetical: a migrated
project (`yamlFormat: 2`) whose `fileGeneration.fileMap` hand-declares
`include: { ext: {hdr: h, src: cpp} }` produces the key `include_hdr`, whose arms were
deleted in 10e — exactly the shape `unittest/mixed_test_arch/mixedProject.yaml` carried until
that section fixed it.

Fixed to the established idiom (`printError(...)` then `exit(warningAndErrorReport())`, as
`pysrc/genFileParam.py:52-57` does), naming the offending key and both places a new file type
must be registered.

*Measured, not reasoned.* The failure and the fix were both driven end to end through
`make newmodule`, by temporarily injecting the retired
`include : { ext: {hdr: "h", src: "cpp"}, mode: context }` entry into
`examples/simple/arch/yaml/project.yaml` (restored byte-identically afterwards, md5 verified):

- OLD arm: `make newmodule` printed `Unknown section: include_hdr`, stopped after
  `Making simpleIncludes.h`, still ran the recipe's `touch` of the db stamp, and exited **0**.
- NEW arm: same point of failure, but `Error Number 1: fileMap file key 'include_hdr' has no
  scaffold in ...` / `Found 1 Error.` and
  `make: *** [include/make/a2c-common.mk:217: newmodule] Error 1`, exit **2**.

Coverage added: `unittest/test_project_param.py::test_unregistered_scaffold_filekey_fails_loud`
— the `make newmodule` sibling of the existing `test_unregistered_context_filekey_fails_loud`.
It drives the key through the real `pysrc.renderer.renderer` (constructed with
`directTemplate`, so no project database is needed), which both exercises the whole dispatch
path and asserts the renderer wraps the call in no handler, then asserts the `SystemExit` code
is non-zero rather than merely that a `SystemExit` occurred. It lives in that suite rather than
a new file, so the runner still reports 89 suites.

**Item B — the row-level fallback removed at one `multiDst` site was still live at the
other, and at its two neighbours.** (Line numbers below are post-change unless marked.)
`templates/systemc/testbench.py:394` now subscripts `get_intf_defs(...)` directly, so a
missing row yielded `TypeError: 'NoneType' object is not subscriptable`, naming neither the
interface type nor the block — while the sibling site at `intf_gen_utils.py:241` was already
fixed to raise a `KeyError` that names the type. The documented `None` return was dead at
every consumer: none of the three guards it (`intf_gen_utils.py:503`
`["sc_channel"]["type"]`, `templates/systemc/module_hdl_wrapper.py:83`
`intf_def.get('skip', None)` — which would raise `AttributeError` on `None` — and
`testbench.py:394` `['multiDst']`).

All three keys are unconditionally initialised by `getBlockData`:
`processYaml.py:1311-1312` lists both `interface_defs` and `interface_type_mappings` in
`blockDataSet`, `:1322-1323` initialises every member to `dict()`, `getBDInterfaceDefs` is
called unconditionally from `getBlockData` (`:1366`) with no early return, and it assigns
`ret['interface_type_mappings']` outright (`:3160`) and fills `ret['interface_defs']`
(`:3162`). So **all six** reads of these two keys in the file now read directly:

- `get_intf_defs` (`:1004`) — `return block_data['interface_defs'][intf_type]`, and the
  docstring, which documented the false `None` contract, was corrected.
- `sc_connect_channel_type` (`:236`) — `block_data['interface_defs']`.
- `get_intf_type` (`:34`) — `block_data['interface_type_mappings']`. The INNER
  `type_mappings.get(ifType, ifType)` is left alone: an unmapped alias passes through by
  design, since only register interface types are aliased. A short comment now records that.
- `sv_gen_modport_signal_blast` (`:139`), `sc_gen_modport_signal_blast` (`:670`) and
  `sc_gen_block_channels` (`:780`) — `block_data['interface_defs']`. These three were
  initially left out of scope and are described below.

Every caller was checked to pass a real `getBlockData()` view, not an ad-hoc dict. The eleven
template sites across six files (`moduleRegs.py:151`, `moduleInterfacesInstances.py:47`,
`systemVerilog/module_hdl_wrapper.py:78,94,115`, `systemc/module_hdl_wrapper.py:80,82`,
`blockRegs.py:88`, `testbench.py:189,194,394`) all index other contracted view keys
(`ports`, `parameterizedDecls`, `interfaceTypes`, `prunedConnections`, `blockModuleName`) on
the same dict, and `unittest/test_boundary_signals.py` calls `proj.getBlockData(...)`. The
hierarchy-mode branch of `systemc/module_hdl_wrapper.py` never reaches its `get_intf_defs`
call, on two independent grounds: `systemcGen.py:78-79` replaces `data` wholesale with
`{"qualTop": qualTop}` in hierarchy mode and no PARAM line in the corpus carries
`--hierarchy`, and the enclosing `sec_bfm_includes` already indexes `data['includeContext']`
(`:74`) and `data['interfaceTypes']` (`:80`) unguarded. No caller passes a non-view dict.

**The three sibling reads in `sv_gen_modport_signal_blast`, `sc_gen_modport_signal_blast` and
`sc_gen_block_channels` are CLOSED too** (now `:139`, `:670`, `:780`). They were initially
scoped out because each is immediately followed by an `assert`, so they were not silent. The
follow-on review flagged that as insufficient, and the reasoning is the durable part: the
`{}` fallback could not prevent a failure at any of the three, because the very next line
already dereferences `interface_defs[intf_type]` (`:140`, `:671`, `:781`). It was dead code
whose only effect was to degrade a `KeyError: 'interface_defs'` into a message-less
`AssertionError` — and leaving it meant the file carried both spellings of the same read, so
the next agent copying a neighbouring line had even odds of copying the violation. A
builder-base violation is not excused by sitting in a neighbouring function; the rule applies
categorically, and "the three sites I verified" is not a ceiling on it.

Scope was held tight: only the key access changed. The `assert`s were left exactly as they
are — not restructured, not converted to `printError`. Whether an `assert` in a render helper
should be a loud error is a separate question and is NOT settled here. The redundant
`# Get interface definition from block_data` comment above each read was dropped rather than
replaced with rationale prose.

Callers were re-verified for these three as they were for the first set, and all pass a
genuine `getBlockData()` view: `sv_gen_modport_signal_blast` from
`systemVerilog/module_hdl_wrapper.py:19` (`systemVerilogGenerator.py:59`/`:67`) and
`unittest/test_boundary_signals.py:65`; `sc_gen_modport_signal_blast` from
`baseClassDecl.py:101,243`, `classDecl.py:128`, `systemc/module_hdl_wrapper.py:205` and
`test_boundary_signals.py:70`; `sc_gen_block_channels` from `testbench.py:188,330,495`,
`constructor.py:128` and `intf_gen_utils.py:840` (via `sc_declare_channels`, called from
`testbench.py:471` and `classDecl.py:140`) — all `systemcGen.py:56`. The hierarchy
substitution at `systemcGen.py:78-79` reaches none of them; the one call in the Verilated SC
wrapper (`systemc/module_hdl_wrapper.py:205`) sits inside `if not args.hierarchy:` (`:202`).

Two further pre-existing items the same review surfaced, both out of scope and left alone:

- `templates/systemc/module_hdl_wrapper.py:17-21` documents `data` as
  "project/hierarchy-level when it renders `vl_wrap.cpp`", and the ~10 `data.get(...)`
  defaults at `:22-46` plus the `if not args.hierarchy` gate at `:202` exist to serve that
  path. `vl_wrap.cpp` is retired (`config/project.yaml:154`) and `vlScWrap` is `mode: block`
  (`:174`), so those defaults protect a dead path — the same rule class Item B just closed.
  This stale docstring is the sole reason Item B's blast radius needed proving.
- `pysrc/processYaml.py:1312` declares `interface_type_mappings_qualified` in `blockDataSet`
  and `getBDInterfaceDefs` computes it (`:3148`, `:3157`) but never assigns it to `ret`. It
  has zero readers.

**Open item (recorded, deliberately NOT fixed).** `pysrc/interfaces_defs.py` hard-codes an
`INTF_DEFS` dict — including `'multiDst': True` on `status` — and has **zero importers**
(grep over `*.py`/`*.mk`/`*.yaml` across `builder` finds only its own definition). It is a
stale duplicate of what `interfaces/*/*_if.yaml` owns and the schema loads into
`prj.data['interface_defs']`, and therefore a trap for the next `multiDst` edit: it looks
authoritative and is not. It is left in place because deleting an implementation file needs
the user's explicit approval.

Gate results:

- Unit suite (`./unittest/run_all_tests_parallel.sh`): `Ran 89 suites: 89 passed, 0 failed`.
- Whole corpus `make clean && make -j8 gen`: all 15 trees exit 0, `CORPUS_OVERALL_EXIT=0`.
- `make pipeline-test`: exit 0.
- debayer `make clean && make -j8 gen` + `make -j8` + `./build/run debayer
  --verbosity=medium`: exit 0, prints `No error`; tree diffstat unchanged at
  25 files, 70 insertions, 244 deletions.
- Idempotence: a second `make gen` with no clean reproduced both snapshots exactly
  (corpus and debayer).
- Item A fail-loud proof: `make newmodule` exit 2 (was 0), see above.

**A/B byte-identity proof.** Snapshot = md5 of 736 artifacts (581 across the 15 base+pro
example trees, 155 across debayer; `*.cppm`, `*.cpp`, `*.h`, `*.hpp`, `*.sv`, `*.svh`, `*.f`,
`*.mk`, `*.adoc`, excluding `build`, `obj_dir`, `.gen` and `__pycache__`), each taken after a
full clean + gen. **`diff A B` is empty in both halves — zero differing bytes.** A third
snapshot taken after the `make newmodule` probe and a clean re-gen of `examples/simple` also
matches A exactly.

### Follow-on: structures.py `--mode` consumers made fail-loud (LANDED 2026-08-07)

Direct sequel to Item A above. (Line numbers below are post-change unless marked.)
`_CONTEXT_FILE_MODE` (`pysrc/genFileParam.py:42-48`) is EXHAUSTIVE with no default because
the `--mode` token on a `GENERATED_CODE_PARAM` line selects the emission flavour a file
regenerates with. Every consumer of that token in `templates/systemc/structures.py` was weaker
than the contract that produces it.

**Defect 1 — the mode check stated a fallback it did not perform.** `render` had (pre-change
`:30-33`):

```python
if args.mode == '':
    args.mode = 'model'
if args.mode not in codeMapping:
    print(f"Warning: mode {args.mode} not found in codeMapping, defaulting to model")
```

Nothing assigned `args.mode`. Verified from disk before changing: the only assignment anywhere
in the file was the legitimate `'' -> 'model'` default on the line above, and execution fell
through the warning to `oneStruct`'s `featureMapping = codeMapping[args.mode].copy()`
(pre-change `:409`, now `:422`), reached for any non-parameterizable struct or any
header-section render. So the real outcome was a `KeyError` raised ~380 lines from the cause,
preceded by a warning that misdescribed it.

The premise correction worth recording: this arm was **not** fail-quiet. The `KeyError` already
aborted non-zero; the fix here is diagnostic quality and locality, not exit status.

**Defect 1b — two more mode-keyed lookups bypassed the check entirely (review MUST-FIX).** The
first draft put the guard inside `render`'s `'' | 'cpp' | 'header'` branch, which is where the
brief located it. That was insufficient. `systemIncludes` performs two further mode-keyed
lookups — `baselineIncludes[mode]` (`:87`) and `codeMapping[mode]` (`:90`) — and the
`headerIncludes` / `cppIncludes` sections that call it sit OUTSIDE that branch (pre-change
`:45-50`). Worse, on the fw artifacts the `_CONTEXT_FILE_MODE` contract actually
governs, the includes region is the FIRST structures region in the file
(`examples/simple/fw/include/simpleIncludesFW.h:10` vs the default section at `:38`;
`simpleIncludesFW.cpp:4` vs `:9`), so the new diagnostic was **unreachable** on exactly the
artifacts that motivated it. Measured, not reasoned: with the pre-change code an
`--mode=notAMode` on `simpleIncludesFW.h` produced a bare
`KeyError: 'notAMode'` at `baselineIncludes[mode]`, with no warning and no diagnostic at all.

Resolved by making the flavour resolution a single named guard, `resolveMode` (`:358`), placed
directly after the `codeMapping` table it enforces — the same shape `contextParamMode` has
after `_CONTEXT_FILE_MODE` in `genFileParam.py`. It absorbs the `'' -> 'model'` default that
`render` and `systemIncludes` each used to spell separately, and both call it (`:31`, `:82`),
so all three mode-keyed lookups are behind one gate. It also covers
`moduleScaffold.py:59`, the third `systemIncludes` caller. It requires the mode to key BOTH
tables (`:361`), not just `codeMapping`, because `baselineIncludes[mode]` at `:87` is one of the
three lookups it makes safe. Diagnostic names the unrecognised mode and all three registration
sites (both tables here, `_CONTEXT_FILE_MODE` for a context artifact's token), in the
`genFileParam.py:52-57` / `fileGen.py:98-104` idiom.

Deliberately unchanged: `render` still assigns the resolved mode only in the declaration
branch, so `testStructsHeader` / `testStructsCPP` continue to see `args.mode == ''` and
`systemIncludes` still resolves its own local copy without mutating `args`. This is a
minimal-diff choice, NOT a correctness constraint — the second review checked and hoisting
would have been behaviour-neutral: `isModel = args.mode in ('model', 'module')` (`:625`,
`:661`) sits in `prt`/`prtFmt`, reachable only from `oneStruct` (`:440`, `:442`), whose only
caller is `render:36` inside the branch, so `args.mode` is never `''` there in either form;
and the test-struct path's only mode reader, `useConfig = args.mode == 'module'` (`:1624`), is
`False` for `''` and `'model'` alike. The resulting asymmetry is observable by nothing today —
`renderer.py:39` builds a fresh `Namespace` per section — but it is worth knowing it rests on
scope discipline, not on a flip that would break.

**Defect 2 — `oneStruct`'s feature dispatch default was fail-QUIET.** `case _:` was
`print("bad codeMapping entry")` + a bare `exit()`, i.e. `SystemExit(None)` = status **0**, the
same defect Item A fixed, and the weakest possible diagnostic: no feature, no mode, no struct.
Now `printError` + `exit(warningAndErrorReport())` at `:473-479`, naming the feature, the mode,
its handling, and the struct being rendered.

Reachability confirmed as internal-only: `codeMapping` is a module-level table at `:314`, never
built from YAML and never indexed by user input beyond the `--mode` key that `resolveMode` now
validates, so the guard fires only on the developer mistake of adding a `codeMapping` feature
without its `case` arm. No user-authorable input reaches it.

*Measured, not reasoned.* Every arm driven end to end through a real `make gen` in
`examples/simple`, each probe restored byte-identically afterwards (md5 verified):

- Defect 1, `--mode=notAMode` on `model/simpleIncludes.cppm`'s PARAM line. OLD: the misleading
  warning, then `KeyError: 'notAMode'` through `renderer.py:65` into `structures.py:409`
  (pre-change), exit **2**. NEW: `Error Number 1: emission mode 'notAMode' is not registered in
  the codeMapping table ...` / `Found 1 Error.`, exit **2** — same status, cause named at the
  point of detection.
- Defect 1b, the same token on `fw/include/simpleIncludesFW.h`. OLD: bare
  `KeyError: 'notAMode'` at `structures.py:90` in `systemIncludes` (pre-change; now `:87`),
  no diagnostic, exit **2**.
  NEW: the `resolveMode` diagnostic on that artifact, exit **2**.
- Defect 2, a `'noSuchFeature': 'inline'` entry injected into `codeMapping['fw']`. OLD:
  `bad codeMapping entry` printed twice and `make gen` exited **0** while leaving both
  `fw/include/simpleIncludesFW.{h,cpp}` unwritten — md5-identical to the pre-probe snapshot,
  i.e. a silent no-op reported as success. NEW: `Error Number 1: codeMapping feature
  'noSuchFeature' (mode 'fw', handling 'inline') has no case arm ... for struct 'tag_st'` on
  both artifacts and `make: *** [...simpleIncludesFW.cpp.scgen] Error 1`, exit **2**.

Coverage added in `unittest/test_project_param.py` (the suite that already owns the
`--mode` / file-key fail-loud family), each driven through the real `renderer` rather than
calling the arm, and each fail-loud case asserting a **non-zero** `SystemExit.code`:

- `test_unregistered_structures_mode_fails_loud` (`:370`) — iterates all four sections that
  consume the token (`header`, `cpp`, `headerIncludes`, `cppIncludes`), so the Defect 1b gap
  cannot reopen silently.
- `test_absent_structures_mode_defaults_to_model` (`:394`) — the documented default the guard
  must not reject, asserted on `resolveMode` and on a real include-section render.
- `test_unrendered_codemapping_feature_fails_loud` (`:413`) — injects a mode carrying ONLY the
  unrendered feature, so the dispatch reaches the guard without first rendering a real one.

All share `_structuresRenderer` (`:358`), which returns `renderer.pythonTemplate['structures']`
because `loadTemplates` imports the template by path: that is the module instance `render`
actually executes, so it is the one the injection must patch. Registered in `run_all_tests()`
(`:471`).

Categorical sweep of the file touched: `templates/systemc/structures.py` held the only bare
`exit()` and the only misdescribing warning under `templates/` and `pysrc/` — after this change
`grep -rn "\bexit(" templates/ pysrc/` finds no bare `exit()` at all. The one other `exit()`
hit is commented out at `arch2codeHelper.py:123`; the one `exit(0)` is the deliberate all-passed
branch of `pysrc/table_format/test_table_format.py:446`. The fourteen `args.mode` readers
outside this file are all equality comparisons, not table lookups, so none carries a silent
default on the token — but note that the sweep that counted them is what missed Defect 1b,
because the includes branch *passed* `args.mode` (pre-change `:50`, now `:48`) rather than
comparing it. The `raise ValueError` at `:17-19`
is left alone: it already fails loud and names both the offending section and the template, so
converting it would be a behaviour change to an unrelated check.

Recorded, NOT fixed here (out of scope, same class as the 10f sweep): `structures.py` reads the
contracted `isParameterizable` field both ways — directly at `:374`, `:502`, `:543` and with a
`.get('isParameterizable', False)` fallback at `:146`, `:182`, `:191`. `config/schema.yaml:134`
declares it `auto(structIsParameterizable)`, so it is present on every row. There are roughly
twenty further `.get(` sites in the file needing the same triage.

Gate results (all re-run on the final form after the MUST-FIX):

- Unit suite (`./unittest/run_all_tests_parallel.sh`): `Ran 89 suites: 89 passed, 0 failed`,
  first attempt, no retry needed.
- Whole corpus `make clean && make -j8 gen`: 13 gen trees + 2 db-only arch trees
  (`hierInclude`, `inAndOut`) each exit 0, `CORPUS_OVERALL_EXIT=0`.
- `make pipeline-test`: exit 0.
- debayer `make clean && make -j8 gen` + `make -j8` + `./build/run debayer
  --verbosity=medium`: exit 0, prints `No error`; tree diffstat unchanged at
  25 files, 70 insertions, 244 deletions.
- Idempotence: a second `make gen` with no clean over all 13 trees plus debayer reproduced both
  snapshots exactly.

**A/B byte-identity proof.** Same 736-artifact snapshot definition as the section above
(581 corpus + 155 debayer, each taken after a full clean + gen). Snapshot A was taken with
`structures.py` reverted to its exact pre-change form (the hunks reverse-applied and diffed to
confirm nothing else moved); the final-form snapshot after a full clean + gen on the landed
code. **`diff` is empty in both halves — zero differing bytes.** A further snapshot taken after
all three `make gen` probes were restored and `examples/simple` re-genned from clean also
matches A exactly. The `resolveMode` refactor is output-neutral by construction — it absorbs
two `'' -> 'model'` defaults that were already equivalent — and the snapshot confirms it.

### Follow-on: structures.py `isParameterizable` contracted-field sweep (LANDED 2026-08-07)

Closes the item the section above recorded as out of scope. `templates/systemc/structures.py`
read `isParameterizable` **both ways in the same file** — direct subscripts against
`.get(..., False)` fallbacks — and the sweep of the rest of the file that the rule demands
found the same split on four more fields. All line numbers below are **post-change** unless
marked *(pre-change)*.

**Premise corrections to the task brief.** Two, neither affecting the substance:

- The debayer database is at `/work/ws/debayer/debayer.db`, not `rundir/debayer.db`.
- The stated A/B expectation "581 corpus + 155 debayer artifacts" mixes two exclusion sets.
  581 is the corpus count with `.gen` pruned; 155 is the debayer count with `.gen` *included*
  **and taken after a build**. `.gen` holds `build.mk` plus `cpp-modules.mk`, and the latter
  is written by the build rather than by gen, so including `.gen` makes the snapshot
  build-state dependent — the exact confounder these proofs are supposed to exclude. The
  deterministic definition (`.gen` pruned) is 581 + 153, and the two `.gen/*.mk` manifests are
  proved byte-stable separately, so nothing is left uncovered.

The brief's reading of `config/schema.yaml:134` is **correct**:
`structures.isParameterizable: auto(structIsParameterizable)`.

#### The contract, per section

Three different schema sections were involved and each was checked on its own declaration, as
the brief required:

| Section | Declaration | Where |
| :--- | :--- | :--- |
| `structures` | `isParameterizable: auto(structIsParameterizable)` | `config/schema.yaml:134` |
| `types` | `isParameterizable: optional(false)` | `config/schema.yaml:100` |
| `constants` | `isParameterizable: optional(false)` | `config/schema.yaml:76` |

`auto(...)` is computed for every row; `optional(false)` always materialises. Critically for a
behaviour-preserving edit, `pysrc/schema.py:1024-1026` coerces a `true`/`false` default to a
real Python bool, so `optional(false)` stores `False` — **not** the string `"false"`, which
would have been truthy and would have made every one of these edits a behaviour change.

Corpus measurement, read-only `sqlite3` over 21 databases (19 example + debayer + the pro
`lmmiDemo`): **zero nulls and only `integer` 0/1 in all three sections** — `structures` 229
rows (173/56), `types` 284 rows (244/40), `constants` 170 rows (104/66). The DB columns are
declared with no type, so BLOB affinity applies and no coercion is masking a stored string;
`integer` is the genuine value.

#### The row lookups had to be settled first, and `systemcGen` settles them

Three of the five sites wrapped the field read in an *optional-row* fallback
(`prj.data['structures'].get(vardata['subStructKey'], {})`), so the field read could not be
made direct without answering the row question. It is answered upstream rather than by
schema reasoning: `pysrc/systemcGen.py::calcStructure` enriches every var **in place** before
any template renders, and it already does the same lookups **unguarded** —
`prj.data['structures'][varData['subStructKey']]` (`systemcGen.py:147`) for `NamedStruct` and
`prj.data['types'][varData['varTypeKey']]` (`systemcGen.py:151`) for everything else
non-`Reserved`. If
either row were absent the generator would already have raised a `KeyError` long before the
template ran, so both `{}` fallbacks were dead by construction. `calcStructure` is also what
produces the `bitwidth` / `isArray` / `arraySizeValue` fields these same functions read.

`entryType` is the discriminator that makes this airtight: `_auto_entryType`
(`processYaml.py:7066-7067`) returns `NamedStruct` **only** when `subStruct` is truthy, so at
the `NamedStruct` sites `subStructKey` took the validated-FK path (`processYaml.py:6485`) and
is a live key; the `optional`-and-empty `""` path (`processYaml.py:6468`) is unreachable there,
and the `'InvalidValueInYaml'` path (`processYaml.py:6505`) carries a `logError` that aborts.

#### `Reserved` is the one genuine optional relationship, and it is why one guard stays

The corpus has **zero `Reserved` rows** — 378 `structuresvars` rows across all 21 databases
are `NamedType` (300), `NamedStruct` (60), `NamedVar` (18) — so corpus coverage could not
settle it and reasoning alone would have been guessing. `Reserved` is nonetheless authorable
and `cppTypeName` explicitly handles it (`declareVars:491`, `constructor:1029` both
name `Reserved` in the guard). So it was **measured**: a `probeReserved: {entryType: Reserved,
align: 5}` var was injected into `examples/mixed/arch/yaml/mixed.yaml` and driven through a
real `make gen` (restored afterwards, md5 verified `94cbf4d9421411f2380b66fbb7fe7367`).

The row it produces is `varTypeKey=''`, `varType=''`, `subStructKey=''`, `arraySize='0'`,
`arraySizeKey=''` — every field **present**, two of them empty. Instrumented at the site, the
`Reserved` var reported `have_varTypeKey=true` but `rowPresent=false`.

That splits the two questions the brief asked to be judged separately:

- The **field** `varTypeKey` is contracted-present even for `Reserved`, so
  `vardata.get('varTypeKey', '')` was a dead fallback → now `vardata['varTypeKey']` (`:192`).
- The `and typeKey` truthiness test is a **genuine optional-relationship branch and is KEPT**
  (`:193`). A `Reserved` field references no type; removing that test would turn
  `prj.data['types']['']` into a `KeyError`. It short-circuits before the lookup, which is
  precisely why the row fallback behind it was dead.

`arraySize` being TEXT `'0'` on that row also confirms the returned value is unchanged by
making `:169` direct: the old `.get('arraySize', ...)` already returned that same `'0'`.

#### Site-by-site verdicts

Measurement column = hits recorded by instrumenting each site and running the whole corpus
(18 gen invocations), debayer gen, and the 89-suite unit run — 7489 observations.

| Site *(pre-change)* | Before | After | Contract | Measured |
| :--- | :--- | :--- | :--- | :--- |
| `:146` | `subStructInfo.get('isParameterizable', False)` | `subStructInfo['isParameterizable']` (`:142`) | `auto()` | 80/80 present |
| `:145` | `prj.data['structures'].get(key, {})` | direct (`:141`) | `systemcGen.py:147` | 80/80 row present |
| `:170` | `prj.data['constants'][k].get('isParameterizable', False)` | direct (`:167`) | `optional(false)` | 300/300 present |
| `:182` | `subStructInfo.get('isParameterizable', False)` | direct (`:177`) | `auto()` | 258/258 |
| `:181` | `.get(key, {})` | direct (`:176`) | `systemcGen.py:147` | 258/258 |
| `:191` | `subStructInfo.get('isParameterizable', False)` | direct (`:186`) | `auto()` | 445/445 |
| `:190` | `.get(key, {})` | direct (`:185`) | `systemcGen.py:147` | 445/445 |
| `:196` | `prj.data['types'].get(typeKey, {}).get('isParameterizable', False)` | `prj.data['types'][typeKey]['isParameterizable']`, `and typeKey` kept (`:193`) | `optional(false)` + `systemcGen.py:151` | 2200/2200 |

Sites the brief did not enumerate, found by the categorical sweep and fixed on the same
grounds. Each was already read **directly** elsewhere in this same file on the same rows, so
the file genuinely carried both spellings of each:

| Site *(pre-change)* | Before | After | Why contracted |
| :--- | :--- | :--- | :--- |
| `:139` | `prj.data['types'].get(...)` + `if typeInfo:` + dead `else` | direct, guard and `else` removed (`:139`) | `systemcGen.py:151`; 514/514 |
| `:177` | same shape, dead fall-through | direct (`:174`) | `systemcGen.py:151`; 1758/1758 |
| `:1520` | `.get(varTypeKey)` + `if typeInfo and` | `prj.data['types'][...]['isSigned']` (`:1517`) | same; 384/384 |
| `:1526` | `.get(nestedStructKey)` + `if nestedStruct and` | direct (`:1521`) | `systemcGen.py:147`; 53/53 |
| `:135` | `vardata.get('arraySizeValue', 1)` | direct (`:135`) | set unconditionally at `systemcGen.py:131`; already read directly at `:1122`; 594/594 |
| `:136` | `vardata.get('isArray', False)` | direct (`:136`) | set unconditionally at `systemcGen.py:132-135`; **already read directly on 31 other lines of this file**; 594/594 |
| `:169` | `vardata.get('arraySizeKey', '')` | direct (`:166`) | `arraySize: optionalConst(0)` creates the `Key` field (`schema.py:1013-1015`); 590/590 + `Reserved` |
| `:172` | `vardata.get('arraySize', vardata.get('arraySizeValue', 1))` | `vardata['arraySize']` (`:169`) | `optionalConst(0)`; nested fallback dead; 590/590 |
| `:272` | `varData.get('arraySizeValue', 0)` | direct (`:269`) | as `:135`; 29/29 |
| `:1302`, `:1303` | `fw_pack_vars.get('prj')`, `.get('useConfig', False)` | direct (`:1299-1300`) | `setupVars['prj']`/`['useConfig']` assigned unconditionally two frames up (`:1462-1463`), and `setupVars` **is** `fw_pack_vars` |
| `:1358`, `:1359` | same | direct (`:1355-1356`) | same |

The `fw_pack_vars` value of `prj` may legitimately be `None`; the **key** is what is
contracted, and `.get('prj')` with no default returned `None` in that case anyway, so the
downstream `if prj else` branches are untouched.

#### Deliberately left alone, with reasons

- **`:105` `myType.get('arrayElementSize', 0)`** — `dataTypeMappings` (`structures.py:4-11`) is
  a module-level literal, not a DB/view row, and the key genuinely exists on only 1 of its 6
  entries. A heterogeneous internal table, so the fallback is correct.
- **`:220` `vardata.get('enum', False)`** — **stays, but not for the reason first recorded.**
  The producer sets `enum` only inside the non-array *and* non-`NamedStruct` branch
  (`systemcGen.py:171`, `:177`). The first draft of this entry said contracting it depends on an
  unestablished "printOneVar is only ever reached for non-arrays" invariant; the review showed
  that invariant is trivially establishable and the claim was therefore wrong. `printOneVar` has
  exactly two call sites, `:627` and `:663`, and **both sit in the `else` of an `isArray` chain**,
  so an array var can never reach it — which is also the mirror of `varLoopCount`, set only on
  the array branch and read directly by `printOneArray:272`.
  The array half is thus a non-issue. What does keep the `.get()` is the datapath exposure in
  the note below: a `subStruct` field carrying `generator: datapath` takes the `NamedStruct`
  format branch during the enrichment loop (`systemcGen.py:168-169`) and so is **never given
  `enum`**, then has its `entryType` rewritten to `NamedType` after the loop, which admits it
  to `printOneVar`'s guard. For that one shape the fallback is live. The durable fix is the same
  `projectCreate` validation named below, not a template fallback.
- **`:1452`, `:1460`, `:1465`, `:1466`, `:1476`, `:1477`, `:1505`** — all index the
  module-level `packUnpack` per-feature descriptor table, whose keys differ per feature by
  design (`'fw_unpack': None` is itself an entry). Not DB/view rows.

#### Was each removed fallback dead or live?

**Every one was dead on every input the corpus can produce.** The A/B diff is empty, which is
the direct evidence: had any fallback been live, its removal would have changed an artifact or
raised.

**One residual exposure, found by review, deliberately NOT papered over.** The `datapath`
backdoor rewrite is the single authorable shape that can still reach a now-direct read with an
empty key. `systemcGen.py:196-199` rewrites the datapath var **after** the per-var enrichment
loop — forcing `entryType = 'NamedType'` and `varType = 'uint8_t *'` — but does **not** set
`varTypeKey`. So a field declared `{subStruct: someSt, generator: datapath}` keeps
`varTypeKey == ''` while presenting as `NamedType`, and would now raise `KeyError: ''` at
`:139`, `:174` and `:1517`. `cppTypeName:193` is immune because the retained `and typeKey`
guard short-circuits first.

Three reasons it is recorded rather than guarded:

- It is unexercised and nonsensical to author. `generator: datapath` appears in **no** YAML in
  the corpus or debayer; the distinct `generator` values across all 21 databases are
  `address`, `data`, `register`, `tracker(cmd)`, `tracker(cmdid)`, `tracker(length)` and empty.
  A datapath backdoor is by definition a `uint8_t *`, so declaring it as a nested struct is
  incoherent.
- The old fallback was not handling this case, it was **masking** it: the `.get()` fell through
  to `str(vardata['bitwidth'])`, emitting the sub-struct's bit width for a var typed
  `uint8_t *`. Silently wrong output, which is exactly what the rule exists to convert into a
  loud failure.
- Restoring a `.get()` would reintroduce the pattern this sweep removes. Per
  `builder/base/CLAUDE.md`, a missing required field is fixed in `projectCreate` validation, not
  by a template fallback. The durable fix is a `projectCreate` check that `generator: datapath`
  requires a `varType` / `variables` reference and forbids `subStruct`. **Not done here** — it is
  a validation change outside this file's scope.

#### Gate results

- Unit suite (`./unittest/run_all_tests_parallel.sh`): `Ran 89 suites: 89 passed, 0 failed`,
  first attempt, no retry needed. Matches the baseline.
- Whole corpus `make clean && make -j8 gen`: **13 gen trees + 2 db-only arch trees**
  (`hierInclude`, `inAndOut`), run as 18 gen invocations because ip_test contributes
  common/ip/bridge/top and simple_ip contributes common/ip/top, built bottom-up. Every
  invocation `rc=0`, `CORPUS_OVERALL_EXIT=0`.
- `make pipeline-test`: exit 0, 38 `No error` lines.
- debayer: `make clean && make -j8 gen` exit 0; `cd rundir && make -j8 gen` exit 0;
  `make -j8` exit 0; `./build/run debayer --verbosity=medium` exit 0, printing `No error`.
  Tree diffstat unchanged at **25 files, 70 insertions, 244 deletions**.
- Idempotence: a second `make gen` with no clean, over all 18 corpus invocations plus debayer,
  reproduced both snapshots exactly.

#### A/B byte-identity proof

Snapshot = md5 of **581 corpus + 153 debayer** artifacts (`*.cppm`, `*.cpp`, `*.h`, `*.hpp`,
`*.sv`, `*.svh`, `*.f`, `*.mk`, `*.adoc`; excluding `build`, `obj_dir`, `__pycache__`, `.gen`,
and — on the debayer half — the `builder` and `isp_shared` submodules), each taken after a full
clean + gen of the whole corpus and of debayer.

Snapshot A was taken with `structures.py` restored byte-identically from the saved pre-change
copy (md5 `57cc9686c275cabbb6ce10b9a8323d7e`); snapshot B on the landed form
(md5 `3496c1c1892aa2ab2549fc16985becb5`). **`diff A B` is empty in both halves — zero
differing bytes across all 734 artifacts.** A third snapshot after a second gen matched B
exactly.

The two `.gen/*.mk` build manifests that the deterministic snapshot prunes were proved
separately: all **25** `.gen/*.mk` files across the corpus and debayer were md5-captured after
a full `make -j8` on each side, and **that diff is empty too**. So the build-state-dependent
files are covered without letting them into the snapshot definition.

Because the change is byte-neutral, no `GENERATED_CODE_PARAM` line moved: the edit touches
none, and no generated file changed at all.

#### Recorded, still open

- `templates/systemc/structures.py:220` `vardata.get('enum', False)` — see above. Its array
  justification is disproved; what keeps it is the datapath shape. Resolving it means adding the
  `projectCreate` validation that rejects `generator: datapath` on a `subStruct` field, which
  would close `:220`, `:139`, `:174` and `:1517` together.
- The `generator: datapath` / `subStruct` validation gap itself, per the residual-exposure note
  above. `systemcGen.py:196-199` rewrites `entryType` without maintaining `varTypeKey`, so the
  two fields disagree for that one authorable shape.
- `pysrc/interfaces_defs.py` remains a zero-importer stale duplicate, unchanged from the
  section above.

## 11. Open Risks

- **R1:** GCC's `-fno-module-lazy` workaround (`a2c-systemc.mk:122-132`) exists because
  GCC 13.2 hits `recursive lazy load` on modules that pull in heavy standard headers,
  and `docs/vcs-build.md` §D records a GCC 13.2 internal compiler error on
  `debayer_tbIncludes.cppm`. This plan adds two modules per testbench block to that
  import graph, in the same neighbourhood as the known failure. Validate the GCC
  flavour explicitly; a green Clang result does not generalise.
  **CLOSED in S5 (2026-08-05):** measured under `USE_GCC=1`. GCC 13.x ICEs on
  `model/debayerIncludes.cppm` — the context includes module, upstream of anything this
  plan touches — so no testbench `.cppm` is ever reached. Not caused or worsened here;
  §D's conclusion stands. Full diagnostic in the S5 entry.
- **R2:** The External unit's module name depends on `refactor_tbExternal` having
  resolved the DUT. A testbench with no `--excludeInst` takes the sentinel path
  (`testbench.py:423-428`) where `data` is already the DUT. Both paths need a fixture;
  `simple` covers the no-exclude case and `mixed` covers the excluded case.
- **R3:** D4's fix moves an in-class declaration and its out-of-class definition in one
  change. A partial application compiles in some orders but fails to *register* the
  testbench, which surfaces at run time, not build time. Gates must assert the
  testbench ran.
- **R4:** The External class is `sc_module` plus `<DUT>Inverted<Config>`. For a
  non-parameterizable DUT it is an untemplated class in a module purview. That path is
  now proven by the item-5 block conversion, but it was flagged as a latent first-use
  risk there and the same caution applies to the first ported External.
