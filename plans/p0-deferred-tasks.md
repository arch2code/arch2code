# P0 Deferred Items — Task Brief

This document is a self-contained work plan for closing the items flagged in [`p0-conclusions.md` § Not Validated in P0 / Deferred](./p0-conclusions.md#not-validated-in-p0--deferred). The agent picking this up does not need to read the full plan set — only the cross-references called out below.

## Context (read these first)

| Document | What you need from it |
|----------|----------------------|
| [`p0-conclusions.md`](./p0-conclusions.md) (also at `proto/p0-conclusions.md`) | The "Not Validated in P0 / Deferred" section is the source of these tasks. The "Validation Item Definitions" section explains V1–V7 / R1–R6. |
| [`builder/base/plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md) | §4.6 "Underlying C++ Type Strategy" (multi-word `_packedSt`); §7 "Interface Constraint" (cross-config prohibition); §11 open questions. |
| [`builder/base/plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md) | Step 6c (`_packedSt`); the broader Config-template approach. |
| [`builder/base/plan-development-ordering.md`](./plan-development-ordering.md) | Confirms Option 4 is the chosen path; these tasks gate Phase 2. |

## Goal

Close all items in the deferred list so that Phase 2 (the bracketed `[M1+M5+M2 + T1+T2+T3+T4+T5]` step from the ordering plan) can begin without unquantified risks.

When this task is complete:
- Every row in the "Not Validated in P0 / Deferred" table of `p0-conclusions.md` is either resolved (with a link to the artifact / decision) or explicitly re-deferred with stated rationale.
- New prototype tests live alongside the existing ones in `proto/model/`.
- New design notes live alongside existing plans in `builder/base/`.

## Rules of Engagement

1. **Do not modify the existing P0 prototype tests** (V1–V7, R1–R6). Add new files; don't alter `test_structs.cpp`, `test_sc_module.cpp`, etc.
2. **Update `p0-conclusions.md`** as each task closes — move rows from "Deferred" to "Retired" (or annotate with what changed).
3. **Each task ends with a one-paragraph entry in `p0-conclusions.md`** describing what was tested/decided and pointing to the artifact.
4. **Stop at the gate, not past it.** None of these tasks should start touching the actual generator code (`builder/base/pysrc/`, `builder/base/templates/`). That's Phase 2.
5. **Ask before deviating from the plan.** If a task reveals something that changes the chosen approach (Option 4), surface it instead of working around it.

---

## Phase 1 — Prototype Validations

### Task 1: Cross-config negative test

**Goal:** Confirm the C++ type system actually rejects connections between differently-parameterized instances, and capture the compiler diagnostic so future developers know what the error looks like.

**Background:** Umbrella plan §7 ("Interface Constraint") states that wiring `interpolate<config_8bpc>` to `interpolate<config_12bpc>` is prohibited. P0 validated the *positive* case (V2: same-Config binding works) but never tried the *negative* case to confirm the compiler enforces the prohibition.

**Deliverables:**

1. A new file `proto/model/test/test_cross_config_negative.cpp` that:
   - Includes the existing `isp_types.h`, `debayer_configs.h`, and `rdy_vld_channel.h`.
   - Attempts to bind a `rdy_vld_out<video_bayer_t<config_8bpc>>` port to a `rdy_vld_in<video_bayer_t<config_12bpc>>` channel (or equivalent cross-config wiring).
   - Is structured as a "this should NOT compile" demonstration. Keep it minimal — ~30 lines.

2. A manual run captured in the conclusions doc:
   - Compile the file with the same flags the Makefile uses for `test_sc_module`.
   - Capture the compiler's diagnostic (first 10–20 lines is enough).
   - Add a "Cross-config negative test" subsection under SystemC Conclusions in `p0-conclusions.md` with: file reference, compile command, and the captured diagnostic.

3. **Do not add a Makefile target** for this — it's a scratch validation, not a CI test. A comment at the top of the file showing the manual compile command is sufficient.

**Acceptance criteria:**
- File exists and demonstrates the cross-config wiring attempt.
- The compile error is captured in `p0-conclusions.md` and is judged "clear and actionable" (i.e., a developer reading it would understand which two types are incompatible).
- The deferred-items table row is moved to retired.

**Out of scope:**
- Any positive test (V2 already covered that).
- Adding the test to `make all`.
- Trying to make the diagnostic prettier — we just want to know what it actually looks like today.

---

### Task 2: Multi-word `_packedSt`

**Goal:** Validate the `uint64_t[N]` multi-word `_packedSt` strategy by actually packing and unpacking a struct >64 bits wide.

**Background:** Step 6c of `plan-parameterizable-config-template.md` and umbrella §4.6 ("Underlying C++ Type Strategy") specify `uint64_t[(_bitWidth + 63) / 64]` for structs whose `_bitWidth` exceeds 64. P0's `video_rgb_t<config_12bpc>` is 291 bits but the prototype currently uses `typedef uint64_t _packedSt;` with a POC-limitation comment — the multi-word path was never exercised.

**Deliverables:**

1. A new struct in a new header `proto/model/types/wide_struct_test.h` (do **not** modify `isp_types.h`):
   - A `template<typename Config>` struct with `_bitWidth > 64` for at least one Config (target: 200+ bits to exercise multiple `uint64_t` words).
   - Use `typedef uint64_t _packedSt[(_bitWidth + 63) / 64];` (or equivalent constexpr expression).
   - Implement `pack(_packedSt &)` and `unpack(const _packedSt &)` that correctly handle the multi-word case using bit shifts/positions across word boundaries. Use `pack_bits()` / `unpack_bits()`-style helpers if useful (see `bitTwiddling.h`).
   - Match the existing struct conventions in `isp_types.h` (`_bitWidth`, `_byteWidth`, `operator==`, `prt()`).

2. A new test file `proto/model/test/test_wide_struct.cpp`:
   - Constructs an instance with non-trivial values across multiple words (set values that span a `uint64_t` boundary so a buggy implementation would be detected).
   - Round-trips through `pack`/`unpack` and asserts equality.
   - Covers at least one Config that exercises the multi-word path and one that stays single-word (to confirm the boundary case works in both directions).
   - Follows the style of `test_structs.cpp` (printf-based, returns 0 on success).

3. A new Makefile target `step5` in `proto/model/Makefile`:
   - Compiles and runs `test_wide_struct`.
   - Add `step5` to the `all` target.
   - Make `step5` depend on the necessary headers.

4. Update `p0-conclusions.md`:
   - Add V8 to the validation-items table covering this test.
   - Move the "Multi-word `_packedSt`" row from deferred to retired.
   - Update the "Issues encountered" table entry for `_packedSt` sizing — replace the "design intent only" caveat with a confirmation pointing to V8.

**Acceptance criteria:**
- `make step5` passes.
- The test demonstrably exercises a multi-word case (i.e., values placed in word 1 round-trip correctly through the multi-word `_packedSt`).
- Conclusions doc updated.

**Out of scope:**
- Modifying the existing `isp_types.h` `video_rgb_t` definition. Leave the POC-limitation comment in place — the new file proves the design separately.
- `sc_pack`/`sc_unpack` for the wide struct (the SystemC-side `sc_bv<>` already handles arbitrary widths; the open question was specifically the `_packedSt` C array path).
- Generator changes — this is prototype-level only.

**Hints:**
- The existing `bayer_pixels_per_clock_t<Config>` in `isp_types.h` already uses a `_pos` runtime tracker for array packing. The pattern transfers to multi-word words: track which `uint64_t` word and bit-position-within-word.
- A simple wide struct: an array of `pixel_t<Config>` with enough elements to exceed 64 bits at 12bpc, plus a `video_frame_t` header. Or define a synthetic struct with three `uint64_t`-equivalent fields just for the test.

---

### Task 3: Build-time / compile-cost spike

**Goal:** Quantify the compile-time cost of the templated/modules path vs. a non-template baseline, so the team has data before committing the whole codebase to Option 4.

**Background:** P0 validated functional correctness but not performance. Templated `SC_MODULE`s and C++20 module precompilation can have meaningful compile-time impact. We don't currently have any numbers.

**Deliverables:**

1. Run timing measurements on the existing prototype:
   - Baseline: time to do `make clean && make step2` (templated SC_MODULE, header-based) on a clean build.
   - Modules path: time to do `make clean && make step4` (templated SC_MODULE through C++20 module).
   - Capture wall-clock and (if straightforward) per-step breakdown using `make -j1` for reproducibility.
   - Run each at least 3 times and report the median.

2. (Optional, if quick) A minimal non-template baseline:
   - Create `proto/model/baseline/` with a non-template version of `interpolate.h`/`.cpp` and `isp_types.h` (concrete `config_8bpc` types only — no templates).
   - Time it the same way for an apples-to-apples comparison.
   - If this would take more than ~30 minutes, skip and note in the writeup that we have no baseline; the relative comparison between header and module paths is still useful.

3. Write the results into a new section in `p0-conclusions.md` titled "Build-time measurements":
   - Table with: build target / compile time / notes.
   - One paragraph of interpretation: is the modules path comparable to the headers path? Is there a flag-on-the-wall reason to reconsider Option 4?
   - Move the "Build-time / compile-cost measurements" row from deferred to retired.

**Acceptance criteria:**
- Measurements captured and recorded with reproducibility info (machine, Clang version already in conclusions doc).
- A clear "go / reconsider" judgment in one sentence based on the data.

**Out of scope:**
- Optimizing the prototype. We just want a reading.
- Profiling-grade analysis. Wall-clock is enough.

---

## Phase 2 — Design Decisions

### Task 4: Shared-vs-IP namespace boundary

**Goal:** Decide and document whether `ipParameters` may appear only in IP-owned YAML, or also in shared includes (e.g., `isp_types.yaml`).

**Background:** Umbrella plan §11 #1 and detailed plan "Further considerations" #1 both flag this as unresolved. It must land before F1 (schema changes) so the schema rule is enforceable.

**Deliverables:**

1. A short design note `builder/base/plan-shared-vs-ip-boundary.md` (target: 1–2 pages):
   - State the question precisely.
   - List the implications of each choice (e.g., "if shared YAML can declare `ipParameters`, then two IPs sharing it must use the same Config type, which constrains multi-instance use").
   - Pick a default and justify it. Recommended default (based on existing analysis): **`ipParameters` may only appear in IP-owned YAML**, and shared YAML files must contain only non-parameterizable definitions. Justify or override.
   - Define the schema rule needed to enforce this (e.g., a YAML-loading check that errors if `ipParameters` appears in a file that's `include:`d by more than one IP, or simply: only the IP's `project.yaml` may contain `ipParameters`).
   - Note any open follow-ups.

2. Update `p0-conclusions.md`:
   - Move the "Shared-vs-IP namespace boundary" item out of the open-questions crosswalk if applicable, or annotate with the decision.

**Acceptance criteria:**
- File exists with a clear, justified decision.
- The schema-enforcement rule is concrete enough that F1 work can implement it without further design.

**Out of scope:**
- Implementing the schema check (that's F1).
- Re-litigating namespace design more broadly.

---

### Task 5: SV parameterization plan stub

**Goal:** Commit to an SV parameterization strategy so Step 10 of the detailed plan has a clear destination.

**Background:** Umbrella §4.3 lists four SV options. P0 validated two (separate-packages-per-instance via R1/R2/R6, module-level parameters via R3). The detailed plan defers the choice. Without a chosen strategy, Step 10 ("omit parameterizable constants from IP package") is incomplete because there's no documented place for those constants to go.

**Deliverables:**

1. A new file `builder/base/plan-sv-parameterization.md` (target: 2–3 pages):
   - Recap the four options from umbrella §4.3.
   - Pick the **separate-packages-per-instance** approach as the primary strategy, citing R1/R2/R6 as evidence.
   - Document how it integrates with the IP module pattern from R3 (module-level parameters defaulting from the package). The two are complementary, not alternatives.
   - File-structure spec: where does the per-instance package live? What's the naming convention (`isp_types_pkg_8bpc.sv`)? Who generates it (consuming project) vs. the IP itself (the symbolic-constant package and module sources)?
   - Generator file map: list which arch2code generator files (existing or new) produce what.
   - Open follow-ups: anything that still needs to be decided (e.g., parameterized packages SV-2012 as a future option if EDA tool support improves).

2. Update `p0-conclusions.md`:
   - Move the "SV parameterized-package option" row from deferred to retired (the *decision* is made; SV-2012 remains explicitly out of scope).
   - Update the umbrella-§11 #2 row in the open-questions crosswalk to "Closed by `plan-sv-parameterization.md`".

**Acceptance criteria:**
- Plan exists and pins the strategy.
- A reader can map every "what changes in SV" item from the detailed plan to a section of this stub.

**Out of scope:**
- SV-2012 parameterized packages (explicitly deferred pending EDA tool validation).
- Generate-block strategies.
- Implementation. This is a planning artifact.

---

### Task 6: `instanceFactory` strategy with templates

**Goal:** Decide how the consuming project registers templated block instantiations with the existing string-keyed `instanceFactory`, and document the mechanism so T6 (template block classes) doesn't run into a wall.

**Background:** The current factory uses string-based block name lookup. Templated blocks (`interpolate<config_8bpc>`, `interpolate<config_12bpc>`) need a way for the consumer to register each instantiation. Umbrella §11 #6 and detailed plan "Further considerations" #3 both flag this; P0 did not exercise it.

**Deliverables:**

1. A new design note `builder/base/plan-instance-factory-templates.md` (target: 2–3 pages):
   - Read enough of `builder/base/common/systemc/` and the existing factory infrastructure to understand the current mechanism. Cite the specific files.
   - Lay out 2–3 candidate registration patterns (e.g., explicit per-instantiation `factory.register<interpolate<config_8bpc>>("u_interp_hd")`, generated registration TU per consuming project, alternative factory-template approach).
   - Pick one. Justify against: (a) how much hand-written code per IP instance, (b) generator complexity, (c) compatibility with the existing string-keyed lookup for non-templated blocks.
   - Sketch a minimal example: given `ipInstances` YAML with two `debayer` instances at different Configs, what does the generated registration code look like?
   - Document the boundary: what does arch2code generate vs. what does the consuming project provide?

2. (Optional) A small prototype validation under `proto/model/`:
   - If the chosen strategy is non-obvious or has compile-time concerns, write a small test that registers two `interpolate<Config>` instantiations with a stub factory and looks them up by name.
   - Skip if the chosen strategy is trivially correct (e.g., explicit registration calls).
   - Don't extend P0 prototypes' Makefile; treat this as a separate scratch validation.

3. Update `p0-conclusions.md`:
   - Move the "`instanceFactory` with templated blocks" row from deferred to retired.
   - Update umbrella §11 #6 in the open-questions crosswalk.

**Acceptance criteria:**
- Plan exists with a concrete chosen mechanism.
- T6 work can proceed without further factory design.

**Out of scope:**
- Implementing the factory changes (Phase 3 work).
- Refactoring the existing string-keyed lookup.

---

### Task 7: Migration tool scope sketch

**Goal:** Scope (don't build) the migration tool that will edit hand-written IP code in the `[M3+T6]` step. This is the largest unquantified execution risk in the plan set.

**Background:** Every plan document mentions a migration tool but none describe one. The ordering plan's Option 4 recommendation explicitly relies on a single-pass migration. Without a sketch, the team can't estimate Phase 2 cost.

**Deliverables:**

1. A new file `builder/base/plan-migration-tool.md` (target: 2–3 pages):

   **Scope:**
   - Inventory the hand-written IP code that will need migration. Use `find` / `grep` against the existing project to count files affected. Report: how many `.h`/`.cpp` files touch parameterizable types, how many block classes, how many enum references, how many constant references. Numbers matter for the recommendation.

   **Categorization of edits:**
   - Mechanical edits (regex- or AST-rewriteable): e.g., `BITS_PER_PIXEL_COLOR` → `Config::BITS_PER_PIXEL_COLOR`, `rgb_pixel_t` → `rgb_pixel_t<Config>`, adding `using namespace isp;`, `#include` → `import`.
   - Judgment-call edits: e.g., when a block class becomes `template<typename Config>`, which methods need template-method-definition migration; deciding which IP-owned types should be parameterized.

   **Tool approach options:**
   - Option A: Pure regex/sed scripts. Cheapest, fragile.
   - Option B: clang-tidy / clang-rewriter (libTooling). Robust, requires compilation database, more work to write.
   - Option C: Manual checklist per IP, no tool. Cheapest if the count is small (<10 files).

   - Recommend one based on the inventory count and complexity.

   **Staging:**
   - Single-IP-at-a-time migration vs. bulk. Given ordering plan Option 4 recommends a single bracketed `[M3+T6]` step, the migration tool needs to either (a) run atomically across all IPs, or (b) support a parallel-build mode where pre- and post-migration code coexists. Recommend an approach.

   **Estimate:**
   - Rough person-day estimate for building the tool given the chosen approach.
   - Rough person-day estimate for running it (manual review per file).

2. Update `p0-conclusions.md`:
   - Move the "Migration tooling scope" row from deferred to retired.
   - Update umbrella §11 #7 in the open-questions crosswalk.

**Acceptance criteria:**
- Inventory count is concrete (real numbers from the existing repo).
- A staffing/duration estimate exists for Phase 2 to use.
- The recommended approach is clear enough to start building when Phase 2 reaches `[M3+T6]`.

**Out of scope:**
- Building the tool. Sketch only.
- Migrating any code.

---

## Phase 3 — Cleanup

### Task 8: Verilator-generated-headers + C++20 modules interop

**Goal:** Confirm (or at least document the expected behavior of) the cosim path where Verilator-generated C++ headers coexist with C++20 module imports in the same TU.

**Background:** Verilator emits header-based C++. A cosim wrapper that uses both `import isp;` and `#include "Vmodule.h"` (Verilator output) hasn't been validated. Likely benign — headers and modules can coexist via the global module fragment — but unverified.

**Deliverables:**

1. A short note added to `p0-conclusions.md` under "Verilator-specific findings" or as a new subsection:
   - Either: a small sniff-test that compiles a TU mixing `import isp;` with a Verilator-generated header (10 min if the existing prototype's RTL has a Verilator artifact handy) and reports the result.
   - Or: a documented note saying "expected to work via global module fragment; will verify when the first cosim wrapper is generated; flagged here so the cosim work doesn't assume it's free."

2. Update `p0-conclusions.md`:
   - Move the row from deferred to retired (if validated) or annotate as "explicitly deferred to cosim work; documented expectation".

**Acceptance criteria:**
- The interop expectation is explicitly documented somewhere actionable.

**Out of scope:**
- Building a real cosim wrapper.

---

## Final Step: Update the Conclusions Document

Once Tasks 1–8 are complete:

1. Move all closed rows from "Not Validated in P0 / Deferred" to "Risks Retired".
2. Update the "Closure of Umbrella Plan Open Questions" table — questions #6 and #7 should now be Closed (referencing the new plan files).
3. Update the "Implications for `plan-development-ordering.md`" section if any deferred-item resolution changes the recommendation. Most likely: the migration-tool sketch (Task 7) will tighten the "largest unquantified execution risk" sentence to reference real numbers.
4. Add a final paragraph: "All P0 deferred items closed as of [date]. Phase 2 foundation work (F1–F3, A1–A3) may begin."

## Suggested Ordering (Confirmed)

1. Task 1 (cross-config negative test)
2. Task 2 (multi-word `_packedSt`)
3. Task 3 (build-time spike)
4. Task 4 (shared-vs-IP boundary)
5. Task 5 (SV parameterization plan)
6. Task 6 (`instanceFactory` strategy)
7. Task 7 (migration tool scope)
8. Task 8 (Verilator + modules note)
9. Final conclusions-doc consolidation

Each task is independent of subsequent tasks except where noted (Task 4 should land before any F1 schema work, but F1 isn't started in this brief). If a task surfaces a problem that invalidates Option 4, **stop and escalate** rather than redesigning.

## Definition of Done

- All eight task acceptance criteria met.
- `p0-conclusions.md` "Not Validated in P0 / Deferred" section is empty (or contains only items explicitly re-deferred with rationale).
- New plan files exist for the design-decision tasks (4, 5, 6, 7).
- `proto/model/Makefile` builds and runs the new tests cleanly.
- No changes have been made to `builder/base/pysrc/` or `builder/base/templates/` (those are Phase 2).
