# Plan: General Interface Compatibility Check

## Current Status

- **Classification (2026-08-10): SETTLED SPECIFICATION for all three axes.** The exploration is complete. All eleven §8 architect decisions are **RESOLVED (2026-08-10)**: 8.1=(b), 8.2=(c), 8.3=RESOLVED-BY-IMPLICATION from 8.1, 8.4=(b), 8.5=(a), 8.6=(a), 8.7=build it, 8.8=(b) with signedness required, 8.9=generated trait specialization from `buildThunkerView`, 8.10=(a) automatic, 8.11=RESOLVED-BY-IMPLICATION from 8.9. What this document now records is the specification and its sequencing, not a set of open options.
- **Implementation status (2026-08-11): "Plan of record" steps 1 and 5 have LANDED.** Steps 2-4 and the seven missing thunker headers are untouched. Evidence for step 1 in §7.1a; one specification correction to §6.2 is recorded there and inline at §6.2. Two follow-ons deliberately left open by step 1, both from §1.2 and neither covered by the §7.1 layout measurement: the protocol comparison still uses the bare `interfaceType` string (`checkInterfacePair`, `processYaml.py:5988-5989`) where the qualified `interfaceTypeKey` is available, and `maxTransferSize` / `multiCycleMode` are still not compared. The §4.2 ordering wart also stands — the check still runs after `runCreateArtifacts()`, so a compatibility failure aborts having already written build artifacts.
- **Amended 2026-08-11 (mechanism replacement).** The verdict is no longer communicated by an emitted `a2c_payload_direct_copy<To, From>` trait specialization. It is now a trailing defaulted `bool` template parameter on the thunker class template, one per `payloadPairs` slot, in `payloadPairs` order, consumed by `copyPayload<Direct>`. The trait mechanism — the primary template in `bitTwiddling.h`, `_thunker_direct_copy_traits()`, `sc_declare_payload_copy_traits()`, `_payload_is_config_dependent()`, and the namespace-scope emission in `classDecl.py` and `testbench.py` — is **deleted**, not retained alongside. §8.9's rejection of the `bool`-template-parameter spelling (§9.7, "The template must consume, not derive") is **superseded**: it rested on the trait leaving the seven class signatures untouched, which is no longer weighed as decisive against keeping all protocol-specific knowledge in the interface's own header. The two "Deferred / Out of Scope" items about the External trait path and cross-TU reachability of a specialization are **closed as moot** — a template argument is part of the member's type, so it reaches wherever the member does, and the External's mirrored members come from the same `sc_declare_thunkers()` call. Defaults are `false` on every flag so hand-written instantiations (`proto/model/test/test_port_thunker.cpp`) need not supply them. Census re-taken after the change: unchanged at **17 of 41**.
- **Step 5 (the C++ definition compatibility axis, §9) LANDED 2026-08-11, and it is validated rather than merely built.** Evidence in "Plan of record" step 5. The census the evidence gate turned on was re-taken *after* the change and is unchanged at **17 of 41 emitted payload pairs**, which is the intended result: axis 2 selects an adapter implementation and must never move a junction into or out of eligibility. Five points where this document's own specification was wrong or underspecified were found while implementing it; each is corrected in place at the section that stated it (§9.1/§9.4 on the identity arm, §8.9/§9.7 on the trait spelling, on the two copy directions and on deduplication) and none of them changes a resolution. Three semantic decisions the specification did not settle are recorded as decisions of record at §9.3a. Two known-incomplete items are recorded in "Deferred / Out of Scope".
- **Status taxonomy:** specification. The §8 option analysis is retained verbatim beneath each resolution so the reasoning survives. Individual findings remain marked **VERIFIED BY EXECUTION**, **VERIFIED BY CODE READING**, **COMPILE-VERIFIED (xprojParam)**, or **CONJECTURE**.
- **Definitional correction (2026-08-10) that governs §9.** In the architect's words: *"By definition if we need a thunker they are different structure definitions - even if the definition is identical."* A thunked junction therefore **always** has two different structure declarations. This is applied throughout §9; see §9.1.
- **Evidence-base correction (2026-08-10).** The §9.5 eligibility measurement is taken largely on `/work/ws/isp`, which the architect states is *"in partial state and does not have correctly parameterized isp"*. Its zero-eligibility count is **struck as a justification** and the proving ground moves to `builder/base/examples/xprojParam` (§9.5).
- **Evidence gate discharged (2026-08-11), and it reverses §9.5's conclusion.** The eligibility census has been **re-measured on the example fixtures** per 8.7, by reading every emitted `_port_thunker<>` instantiation from generated output and judging each payload pair against §9.3's predicate: **41 payload pairs, of which 17 have corresponding storage.** **VERIFIED BY EXECUTION.** The ISP-based table is superseded and retained beneath the new one (§9.5). Three consequences. (i) §9.5's struck verdict — "the optimization is NOT justified by the evidence available today" — is now **independently disproved by measurement**, not merely overridden by 8.7 on evidence-base grounds. (ii) §9.5's "only if every literal field is 64 bits" claim is **too strong** and is corrected at §9.2 and §9.5 point 2: the `maxBitwidth > 64` word-array bucket is a second and larger route to correspondence. (iii) "Plan of record" step 5's *soft* constraint ("pointless before step 3") is **withdrawn**; the hard constraint (not before step 1) stands and is satisfied.
- **Two further generator defects (2026-08-11)** were exposed by the `cppLeaf`/`cppAxis` fixture, both on `connectionMap`, both worked around rather than fixed, and **neither in scope for any current step**: §5.8.
- **Parent context:** [`plan-ip-project-composition.md`](./plan-ip-project-composition.md) **C6** (Q-C12/G5, ACTIVE) owns the defect inventory G5.1–G5.9. This document does not restate it; it assesses which of those defects a general compatibility check subsumes.
- **Settled constraints this design must live inside:** the cross-config interface prohibition ([`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md):545); `ipParameters` only in an IP's own root file ([`plan-shared-vs-ip-boundary.md`](./plan-shared-vs-ip-boundary.md):41); the per-end protocol thunker as the sanctioned adapter ([`bug7-crossinterface-boundary-thunker-proposal.md`](./bug7-crossinterface-boundary-thunker-proposal.md)).

## Plan of record

Derived from the §4.4 option analysis and the §5.2 sequencing constraint, under the §8 resolutions. Sequence and dependencies only.

1. **Layout check** — **LANDED 2026-08-10.** Option A's diff (§4.4), which is strictly contained in Option B. Removed **G1** and **G2**; added a **resolved-identity short-circuit** so the provably-safe cell 1 still skips while cell 10 does not (§2.1, "One caveat on cell 1 vs cell 10"), now at `checkInterfacePair`, `processYaml.py:5976-5978`; **deleted the field-name comparison** per 8.2 (§1.2.1); rewrote the diagnostics per §6.1-§6.4. Depended on nothing below. Measured blast radius zero, confirmed by execution (§7.1a). *(The G1/G2/field-name line numbers this document quotes throughout are pre-step-1 positions of code that no longer exists; they are retained as the record of what was removed and are marked as such where they appear.)*
2. **Resolution defects** — the projectOpen bare-name re-derivations `_resolveDeclaredPortInterfaceKey` (`processYaml.py:1976-1979`) and `resolveInterfaceKey` (`getBDCrossInterfaceBinds`, `:2608-2611`), plus the context-ownership lexical tie-break (`pysrc/projectScan.py:367-374`). Prerequisite for step 3 only; **not** a prerequisite for step 1 (§5.2).
3. **Predicate unification** — Option B step 5 (§8.1=(b), §8.3). Move the thunker-insertion predicate from name difference to resolved `(interfaceKey, Config)` identity and persist it once at db time, so the validator and the generator share one fact instead of computing two. **Must not land before step 2**: a correct verdict driving a wrongly-resolved payload is worse than today. Carries the per-container-variant evaluation of `inheritContainerParam` junctions (§1.3), which 8.1=(b) makes specifiable.
4. **Endpoint-rule narrowing** — restrict `_validateParameterizedConnectionEndpoints` (`processYaml.py:5357-5404`) to same-key endpoints (§5.3). Depends on step 1, which supplies the adjudicator for the cells it stops covering.

5. **C++-definition adapter selection** — §9. **LANDED 2026-08-11** (approved §8.7). A *second* compatibility axis, distinct from layout, that selects the adapter *implementation* (direct copy vs. pack/`copy_packed_bits`/unpack) rather than deciding accept/reject. The predicate is 8.8=(b) member-storage identity with signedness required; the fact is computed in `buildThunkerView` and delivered as an emitted trait specialization (§8.9), consumed automatically with no authored opt-in (§8.10). **Its proving ground is `examples/xprojParam`, not `/work/ws/isp`** (§8.7). The cost half of the evidence gate is still not measured and is still not claimed (§9.5, experiment 2). **The collapse of the 30 pack/copy/unpack sequences into one shared payload-copy helper is part of this step, not a separate item (§8.11), and is done.**

   **What was built.**

   - A module-level `storageBuckets` table (`processYaml.py:439-446`) plus `projectOpen.storageBucket()` (`:1043-1062`), `projectOpen.typeStorage()` (`:1064-1081`) and `projectOpen.structureStorageSignature()` (`:1083-1130`) — the neutral storage descriptors the predicate compares.
   - `getBDCrossInterfaceBinds.buildThunkerView()` (`processYaml.py:2667-2730`) now returns **`payloadPairs`** alongside `payloads`: one entry per protocol payload slot, carrying the parent payload, the child payload and a `directCopy` boolean (`:2707-2723`).
   - Verdict emission in `pysrc/intf_gen_utils.py` through `_thunker_member_type()`, which appends one `true`/`false` literal per `payloadPairs` entry, in `payloadPairs` order, to the thunker member's template argument list. `_thunker_member_type()`, `sc_declare_thunkers()` and `sc_thunker_protocols()` share one `_flagged_thunker_ends()` walk.
   - The verdicts therefore ride on the member declaration itself, emitted by `templates/systemc/classDecl.py::render_default()` for a block and by `templates/systemc/testbench.py::ext_sec_header()` for the testbench External pseudo-block. Neither template, and no code under `pysrc/`, knows anything protocol-specific: the flag count is `len(payloadPairs)`, which is the count of struct-typed entries in the interface's own declared `parameters:` map.
   - `copyPayload<Direct>(To&, const From&)` (`common/systemc/bitTwiddling.h`) was added to `common/systemc/bitTwiddling.h`, and **all 30 pack/`copy_packed_bits`/unpack sequences collapsed onto it** — `apb` 6, `axi_write` 6, `axi_read` 4, `req_ack` 4, `push_ack` 2, `rdy_vld` 2 in base, plus `lmmi` 6 in pro. No `copy_packed_bits` call site remains in any thunker header. **VERIFIED BY EXECUTION.**
   - A new suite, `unittest/test_payload_direct_copy.py`, registered in both `unittest/run_all_tests_parallel.sh` and `unittest/run_all_tests.sh`.

   **Descriptor shape.** Type storage is `('int', storageBits, isSigned, wordCount)`, or `('enum', typeKey)` for an enumeration. A structure signature is `('struct', ((extent, storage), ...))`, recursive on nested structures, or **`None` when undecidable** — and `None` refuses every comparison it takes part in, so an undecidable side falls back to pack/unpack. A member's `extent` is a resolved integer in which **`0` denotes a non-array member** (`arraySize` is `optionalConst(0)` in `config/schema.yaml:129`).

   **Fixture verdicts.** The four labelled junctions of `examples/xprojParam/cppAxis` produce the verdicts the fixture records (§9.5): (a) `wrapEqSt` ↔ `leafEqSt` **eligible**, spelled as a trailing `true` on the emitted `push_ack_port_thunker<>` member; (b) `wrapOrderSt` ↔ `leafOrderSt` ineligible on reversed storage order; (c) `wrapSignSt` ↔ `leafSignSt` ineligible on differing signedness; (d) `wrapNestSt` ↔ `leafNestSt` ineligible on nested-against-flat. Pinned by `unittest/test_payload_direct_copy.py`, which also matches every descriptor against the declaration `templates/systemc/includes.py::includeTypes` actually emits, across all four storage arms.

   **Census after the change: 17 of 41 — exactly the pre-change measurement.** Breakdown: `ip_test` 14 of 19, `simple_ip` 2 of 4, `xif` 0 of 2, `xprojParam` 1 of 16. **VERIFIED BY EXECUTION**, re-read from emitted output. Identity with the pre-change census is the point, not a coincidence: axis 2 selects an adapter implementation and must not move any junction into or out of eligibility.

   **Validation.** `make xproj-param -j` exits 0 with all four consumers reporting `checked 4 samples` — 16 samples in total, every field asserted. `make pipeline-test -j` exits 0. The unit suite is 95 of 96, the sole failure being the already-recorded `test_param_cross_project_linkage.py` at 4 pass / 2 fail (§7.1a). **The fast path was proven to fire rather than silently falling back to the slow path:** the `bit_cast` arm of `copyPayload` was temporarily replaced with a zeroing statement, and only the eligible junction broke; the probe was then reverted and the tree re-validated. That is the only construction that distinguishes "the fast path is selected" from "the slow path is correct", because the two are observationally identical when both are right.

   **Ordering constraints — corrected 2026-08-11.** The superseded reading was:

   > ~~Ordering constraints, unchanged: it must not land before step 1 (it relies on the layout gate for the parameterized-array-extent corner, §9.3) and is pointless before step 3.~~

   The **hard** constraint stands and is now **satisfied**: step 5 must not land before step 1, because §9.3 condition 3 infers equal parameterized array extents from the layout gate rather than proving them independently (§9.6), and step 1 landed 2026-08-10. The **soft** constraint — "pointless before step 3" — is **withdrawn**. It rested on cell 10 being step 5's only eligible population, which followed from the ISP-based census reporting zero eligible junctions. The re-measured census counts **17 eligible payload pairs among the 41 emitted in `examples/` today** (§9.5), none of which requires step 3 to exist: they are ordinary different-declaration cross-interface binds already being thunked. Step 5 therefore has a present-day consumer independent of step 3. Step 3 still *enlarges* the population step 5 serves — it is what makes cell 10 thunked at all — but it no longer gates it.

**Independent, parallel work:** the **seven** missing protocol thunker headers (§8.4=(b); verified list in §1.1 consequence 3). No ordering relation to steps 1-4. **One ordering relation to step 5 exists and is not optional, step 5 being approved:** the 24 base (30 including pro) three-line pack/copy/unpack sequences (§9.4) are collapsed into one shared payload-copy helper *before* the seven new headers are written, or those headers add ~24 more sites to retrofit (§8.11).

## The Goal As Stated

> "The ultimate goal is that the system determines if the interfaces have compatible definitions, whether parameterized or not. If parameterized — in the specific configuration instantiated. Either or both sides may be parameterized. The field names and types should have compatible definitions, i.e. the order and bit sizes."

Refined by the architect:

> "Compatibility is defined based on SV definition as bit-blasted fields of compatible sizes and order. The thunkers are intended to deal with the C++ structure differences — provided the bit definitions are compatible this should work."

The engine to do this already exists and is already two-sided. `checkInterfacePair` (`pysrc/processYaml.py:5952`) builds a **separate** `ValueResolver` per side from that side's own `context` and its own variant bindings (`checkInterfacePair`, `processYaml.py:6026-6035`) and compares `structPackedFields` triples. What is missing is not the comparator. It is (a) reachability, (b) a definition of "compatible" that survives contact with the C++ back end, and (c) agreement between the validator's notion of "needs adaptation" and the generator's.

## 1. What "Compatible" Must Mean

### 1.1 The goal statement conflates two questions

The `xprojParam` harness (`examples/xprojParam/README.md`, "Recorded compile failures") settles this. On the straight-through parameterized path:

```
shared/model/xpSharedTop.cppm:77:5: fatal error: no matching function for call to object of
  type 'push_ack_out<videoSt<xpGainV0Config>>'
note: no known conversion from 'push_ack_channel<videoSt<xpGainDefaultConfig>>' to
      'push_ack_out_if<xpGain_ns::videoSt<xpGainV0Config>> &' for 1st argument
```

`xpGainV0Config` and `xpGainDefaultConfig` are byte-identical. Every field name, order, width and offset agrees. A check that compares only what the goal sentence names would **pass this junction, and the junction does not compile.** This is not new: `bug7-crossinterface-boundary-thunker-proposal.md`:33-38 already states the rule — "every parameterized struct is generated as `template<typename Config> struct <name>`, keyed on the **whole** `Config`. So `stream_t<dutConfig>` and the boundary struct … are **distinct C++ types** even when their packed layouts are identical."

So there are two independent predicates:

- **(a) LAYOUT compatibility.** Do the two resolved packed forms describe the same bits in the same places? A property of the *architecture*, decidable at db time from persisted rows and each side's resolved configuration. This is what the goal sentence describes and what `checkInterfacePair` computes.
- **(b) BINDABILITY.** Can the emitted code bind the two sides as generated? In SystemC this is C++ type identity of the payload (Config identity included). In SystemVerilog it is vacuously true, because ports are generic modports (see §3.5). Layout compatibility is *necessary* for bindability and nowhere near sufficient.

Per the architect's refinement, bindability is **the thunker's responsibility**, not a compatibility criterion. The design consequence is stated in §8.3: the thunker-insertion predicate must therefore key on resolved type difference, not on declared-identity difference.

**Is a layout-only check worth having on its own? Yes, decisively — but not because it prevents compile failures.** It is worth having because it is the *only* gate on the one path where the generator does not fail: when a thunker is inserted, the payload transfer is a **positional bit copy**, not a field-wise or type-checked conversion.

Every thunker performed the same three-line sequence per payload — quoted here as it stood before step 5 collapsed all 30 sites onto `copyPayload` (Plan of record, step 5):

```cpp
inVal.pack( inPacked );
copy_packed_bits( outPacked, inPacked, DownT::_bitWidth );
outVal.unpack( outPacked );
```

That sequence is now `copyPayload( outVal, inVal );` — `push_ack_port_thunker.h:134` in `thunkIn`, `:157` in `thunkOut` — and it is still what runs whenever the pair is C++-ineligible, because `copyPayload`'s final arm is the same three lines (`common/systemc/bitTwiddling.h:90-95`). `common/systemc/bitTwiddling.h:39-60` shows `copy_packed_bits` is `out = static_cast<Out>(in)` for scalar packed forms, else `pack_bits(out, 0, in, 0, bits)` — a positional copy of exactly `bits` bits. **The point this paragraph makes is unchanged by step 5:** on the slow path the payload transfer is still a positional bit copy, and on the fast path it is a whole-value `std::bit_cast`, which is not field-wise or type-checked either. **VERIFIED BY CODE READING.**

Consequences, which the architect should absorb before reading the rest of this document:

1. A layout-incompatible junction that is thunked compiles cleanly and **silently truncates or zero-extends at runtime**. The thunker is not a safety net; it is precisely where a layout check is load-bearing.
2. The thunker copies by **bit position**, not by field name. Field names are semantically irrelevant to the adapter it generates.
3. The thunker is available for 7 protocols only: `push_ack`, `rdy_vld`, `req_ack`, `apb`, `axi_read`, `axi_write` in base plus `lmmi` in pro (`find interfaces -name '*thunker*'`, plus `bug7-…`:79-92). `buildThunkerView` (`getBDCrossInterfaceBinds`, `processYaml.py:2667`) never checks whether a thunker header exists for the protocol it names; a cross-interface bind on `axi4_stream` would be emitted and fail at compile. **VERIFIED BY CODE READING.**

   **Verified inventory (2026-08-10), and an arithmetic correction.** An earlier revision of this line said "the other six base protocols" and then listed seven. Re-counted directly: `find interfaces -name '*thunker*'` returns **six** base headers (`apb`, `axi_read`, `axi_write`, `push_ack`, `rdy_vld`, `req_ack`) plus one in pro (`lmmi`) — seven headers, six of them base. `ls interfaces/` returns **thirteen** base protocol directories, each carrying its own `<proto>_if.yaml`. Thirteen minus six is **seven**, so **seven** base protocols lack a thunker header, not six:

   > `axi4_stream`, `external_reg`, `memory`, `notify_ack`, `pop_ack`, `raw`, `status`

   The list of names was right all along; only the count was wrong. **VERIFIED BY EXECUTION** (directory listing of `builder/base/interfaces` and `builder/pro/interfaces`).

   **RESOLVED 2026-08-10 (§8.4 = (b)): write the missing headers.** The architect chose to make the sanctioned de-parameterized boundary pattern available on *every* protocol rather than to reject the unadapted ones at db time. So this consequence is no longer a reason to reject; it is a work item. Writing those seven headers is independent parallel work (see "Plan of record") and is not undertaken by this document.

### 1.2 Axis-by-axis definition

Verdicts below were proposals; the ones that needed an architect are now marked **RESOLVED** with the chosen option and carry their §8 cross-reference. The "Today" column still describes current behaviour, so a row whose verdict differs from it is a change the Plan of record must make.

| Axis | Proposed verdict | Rationale | Today |
| --- | --- | --- | --- |
| Protocol / `interfaceType` | **Strict identity of the qualified `interfaceTypeKey`** | The signal set, modport groups and channel type come from `interface_defs`. Two projects each declaring their own `rdy_vld` def are not provably the same def. | Compares the **bare** string (`checkInterfacePair`, `processYaml.py:5988-5989`) while `interfaceTypeKey` is available on the row. Same class of unsoundness as G5.2, one level up. **VERIFIED BY CODE READING.** |
| `structureType` set (payload slots) | **Strict identity** | A missing slot is unbindable and unadaptable; `buildThunkerView` hard-errors on it (`processYaml.py:2694-2698`). | Enforced, `checkInterfacePair`, `processYaml.py:6000-6024`. |
| Field **order** | **Strict** | Order *is* the packed layout. The comparator `zip`s the two flattened lists, so order is compared implicitly and correctly. | Enforced. |
| Per-field **bit width** at the resolved config | **Strict. RESOLVED 2026-08-10 (§8.6 = (a)).** | The wire is that many bits; the thunker copies positionally. Per-field equality with order preserved: a *field-by-field correspondence is required*, so a differing field split at the same total width is **not** compatible (§1.2.2). | Enforced (`checkInterfacePair`, `processYaml.py:6065-6079`). |
| Bit **offset** | **Strict. RESOLVED 2026-08-10 (§8.6 = (a)).** | Implied by widths + order, but check it explicitly: it is the only thing that catches a `Reserved`/`align` divergence that happens to preserve field count. | Enforced (`checkInterfacePair`, `processYaml.py:6080-6092`). |
| **Total payload width** | **Do not check separately** | Implied by the per-field triples. A separate total-width check adds a redundant diagnostic that fires alongside a better one. Under 8.6=(a) equal total width is explicitly **not** sufficient on its own, so this row must not be read as a licence to fall back to a total-width comparison. | Not checked separately; correct. |
| **Nested structures** | **Structural equivalence, not name identity.** **Reconciled under 8.2:** the flattened dotted path is *also* a name, so it is **not compared either** — a nested payload is compared purely as its flattened `(width, offset)` sequence. | `_structPackedFields` (`valueResolver.py:338-387`) flattens sub-structures to dotted paths (`frame.sof`). The sub-structure's *name* was never compared; under 8.2 the *whole dotted path* is no longer compared either, so there is no residual name comparison hiding inside the nesting rule. Two identically shaped `video_frame_t`s from two projects still compare equal, which is what makes the sanctioned de-parameterized boundary work at all. **Consequence, stated plainly:** flattening erases the nesting boundary, so a nested `{frame:{sof:1,eof:1}}` and a flat `{sof:1,eof:1}` now compare **equal**. That is bit-correct — the thunker copies those two bits positionally either way — and it is the same acceptance 8.2 grants at the leaf level, one level up. | Structural, but the dotted path is compared as a field name at `processYaml.py:5888-5901` (pre-step-1 line number, code since removed). That comparison went with the rest of the name check (§1.2.1). |
| **Array fields** (`arraySize` from a parameter) | **Structural, expanded per index.** **Reconciled under 8.2:** the per-index `name[i]` spelling is a name, so it is not compared; only the expanded `(width, offset)` sequence is. | `_structPackedFields:350-366` expands `arraySize > 1` into `name[i]` sub-paths and resolves `arraySize` through the side's own resolver, so a parameter-driven depth is honoured per side. The recorded wart — `arraySize == 1` emits the un-indexed name, so an array of one and a scalar compare **equal** — **is subsumed by 8.2 and is no longer observable**, because no spelling of any kind is compared. The same flattening consequence as the nested row applies: an array of four 8-bit elements and four 8-bit scalar fields compare equal. **VERIFIED BY CODE READING.** | Correct; the wart it noted disappears with the name check. |
| **Enum identity** | **Structural (width) for layout. RESOLVED 2026-08-10 (§8.5 = (a)): member-set divergence is out of scope.** | `typeWidth` resolves an enum type to its width; enumerators are never compared. Two enums of equal width with disjoint members pass. This is a *semantic* mismatch that no bit-level check can see, and the architect scoped it out: it is a value-domain question, not a layout question. It belongs with a types/structures identity check, not here. | Structural. Correct as-is; no separate semantic gate is added by this plan. |
| **`varType` / type-name identity** | **Do not compare** | Comparing type names would reject the sanctioned literal-boundary pattern, which exists precisely to pair `isp_pixel_t` with `pixel_t`. | Not compared. Correct. |
| Field **names** | **RESOLVED 2026-08-10 (§8.2 = (c)): not compared.** Compare widths and offsets positionally only. Names may be *printed* in a diagnostic; they are never *compared*. | The thunker copies by position, so names are *provably irrelevant* to generated correctness. The recorded counter-argument is preserved, because it is exactly the risk the architect accepted: names are the only signal that distinguishes "two authors described the same payload" from "two authors described different payloads that happen to share a width profile" — e.g. `{r:8,g:8,b:8}` bound to `{y:8,u:8,v:8}`. Silently thunking that is a real bug class, and under this resolution it **will** be silently thunked. **The architect accepted that explicitly:** "ignore the names, its the engineers job to make it work, our job is to prevent obvious incompatabilities." A transposed-but-same-width datapath is deliberately left to the engineer; the tool's remit is obvious incompatibility, which means bit layout. | Enforced as an error before step 1 (`processYaml.py:5888-5901`, pre-step-1 line number, code since removed), including the flattened nested path. **That was a regression to remove, not merely a rule not to add — see §1.2.1; step 1 removed it.** |
| **Direction / modport** | **Not part of compatibility** | Owned by `validateDeclaredPorts` (`processYaml.py:5826-5836`), which reconciles declared vs. inferred direction independently. Keep the separation. | Correct. |
| `maxTransferSize` / `multiCycleMode` | **Strict** | Present on the `interfaces` row and semantically load-bearing for multi-cycle protocols. Two same-protocol interfaces with different `maxTransferSize` are not interchangeable. | **GAP: not compared.** **VERIFIED BY CODE READING.** |
| `trackerType`, `desc` | **Unconstrained** | Cosmetic. | Not compared. Correct. |
| **Config / C++ type identity** | **Question (b), not (a).** The thunker's responsibility, per the architect. **RESOLVED 2026-08-10 (§8.1 = (b), §8.3 = (b)):** not a compatibility criterion, but it *is* the thunker-insertion predicate — a resolved-type difference at a layout-compatible junction means adapt, not reject. | See §8.1/§8.3. Sequenced after the resolution defects. | Not checked anywhere; the predicate still keys on interface **name** difference (`getBDCrossInterfaceBinds.annotate`, `processYaml.py:2777-2778`, `:2794-2795`). |

### 1.2.1 8.2 makes an existing rule a regression to remove

This is the one place in the plan where a resolution deletes working code rather than adding a check, so it is called out separately.

**`processYaml.py:5888-5901` must be deleted — done by step 1; the line numbers are pre-step-1 positions of code that no longer exists.** That block sat inside `checkInterfacePair`'s `zip` over the two flattened field lists and, on `pname != cname`, emits "cross-interface bind requires matching field names in declared order …" and then `exit(warningAndErrorReport())`. Under 8.2=(c) a field-name difference is not a defect at all, so the block is not reworded, not downgraded to a warning, and not left in place unexercised — it is removed. The `continue` it performs also currently *suppresses* the width and offset checks for that field pair, so leaving it would additionally mask the checks that 8.6 makes load-bearing.

**Consequence, stated so nobody is surprised by it: designs that fail `make db` today on a field-name mismatch *alone* will begin to pass.** That is an intended behaviour change and it is the **only permissive** change in this plan; every other change in the Plan of record is strictly more restrictive. Two qualifications:

- The permissiveness is bounded. A name mismatch that accompanies a width or offset mismatch still fails, and now fails with the *better* diagnostic, because the name check no longer short-circuits ahead of it.
- Nothing currently in the tree relies on the rule. Every design and example in the tree builds green today, so no junction presently trips the name check; deleting it therefore changes no current verdict. This is weaker than the §7.1 layout measurement — it is an inference from "the tree is green", not a replay — and is recorded as such.

The recorded gap fixture holds this line honestly: `unittest/test_param_cross_project_linkage.py::test_gap_cross_project_width_mismatch_detected` deliberately keeps the field name identical on both sides (`collisionTop.yaml`: "The field name is deliberately the same ('data') so the ONLY difference between the bound forms is the payload bit width"), so the diagnostic it expects is the `_bitWidth` one and its expectation is unaffected by 8.2.

### 1.2.2 The final field-comparison rule (8.2 with 8.6)

The two resolutions compose into one rule, which supersedes any looser reading of "compatible sizes and order" elsewhere in this document:

> Flatten each side's payload to its resolved `(width, offset)` sequence. The two sequences must have the **same length** and must agree **element by element, in order, on both width and offset**. Field names — leaf names, dotted nested paths, and `name[i]` array spellings alike — are **printed in diagnostics but never compared**.

Read the two halves against each other, because each closes a hole the other would leave:

- **8.6=(a) forbids re-splitting.** One side declaring a 32-bit field where the other declares two 16-bit fields is bit-identical on the wire and would be copied correctly by the positional thunker, and it is **still rejected**: the sequences differ in length. Equal total width is not compatibility. Without this, 8.2 would leave the comparison with nothing but a total-width equality to enforce, since names would be gone and the split would be free.
- **8.2=(c) forbids nothing about names.** Given the field-by-field correspondence 8.6 requires, the *identity* of each corresponding pair is settled positionally, so the name adds no information the check needs — only information a human reader wants, which is why it is still printed.

The accepted residual risk is exactly the one named in the field-names row: `{r:8,g:8,b:8}` against `{y:8,u:8,v:8}` passes, is thunked, and simulates cleanly with the channels transposed. That is the engineer's problem by the architect's explicit decision.

### 1.3 What is infeasible within the settled constraints

Stated plainly, because the goal sentence implies more than can be delivered:

- **"Either or both sides may be parameterized, in the configuration instantiated" can be fully *decided*, but for one cell it cannot be made to *work* without a thunker.** When both sides are parameterized on distinct Configs and the layouts agree, the only two legal outcomes are *insert a thunker* or *reject*. `plan-parameterizable-config-template.md`:545 prohibits differently-parameterized instances communicating over a parameterized interface, and the emitted C++ enforces that prohibition mechanically (§1.1). Making that junction bind directly is out of reach; a check can only choose between adapting it and refusing it.
- **"In the configuration instantiated" is not yet single-valued for `inheritContainerParam` children.** `_resolveInstanceConfigFields` (`processYaml.py:1594-1612`) documents this: "the descriptor is resolved from the child's own variant binding (frozen here), not from the parent's `Config` template parameter." An inheriting child's instance row carries `variant: ''` — **VERIFIED BY EXECUTION**: all nine `inheritContainerParam` instances in `/work/ws/isp/isp_top.db` (`u_preprocess`, `u_interpolate`, `u_blc_correction`, `u_lsc_core`, `u_gain_calculation`, `u_correction`, `u_ccm_core`, `u_rgb_gain_core`, `u_lut_core`) have `variant = ''`, and their blocks declare only a `default` variant. `variantValueBindings(blockKey, '')` therefore returns nothing and the junction is evaluated at the constants' **declared defaults**, not at the container's bound configuration. In `isp_top` the `isp` variant binds `BITS_PER_PIXEL_COLOR: 8`, which equals the declared default 8, so this currently coincides. It does not honour "the configuration instantiated". A check that genuinely honours the goal must evaluate such a junction once per reachable container variant.

  > **CORRECTION 2026-08-10, found while implementing step 1. The struck claim was "It produces no false positives (both sides get the same wrong bindings)". That is FALSE, and it was false only because G1 was hiding it.** "Both sides get the same wrong bindings" holds when *both* ends inherit. When an inheriting child is wired to a **variant-bound sibling**, the inheriting end resolves at the declared defaults while the sibling resolves at its bound value, and the junction is reported as a payload mismatch on a design that is correct — in emitted code the inheriting child is templated on the container's `Config`, so both ends really are the container's width.
  >
  > **VERIFIED BY EXECUTION**, both wiring directions, on a fixture with declared default `WIDTH: 8` and container variant `WIDTH: 32`: pre-change `make db` is clean, post-G1-removal it reports `parent field 'data' has _bitWidth 32 ... while child field 'data' has _bitWidth 8`. The misresolution is **not confined to the inheriting end** — `_connectionBinding` prefers the `dst` leaf, so when the inheriting instance is the dst the bogus default-width resolution becomes the *connection* side and the diagnostic lands on the correctly-bound sibling instead.
  >
  > Because an inheriting endpoint's configuration is genuinely unknown at db time, neither side of such a connection can be adjudicated. **Step 1 therefore skips any connection with an `inheritContainerParam` endpoint**, which restores the §7.4 no-false-positive property and leaves the residual false negative this bullet already describes. The per-container-variant evaluation that would actually decide these junctions remains step 3's, as the Plan of record states. Guarded by two cells in `unittest/test_inherit_container_param.py` (both wiring directions), which fail without the skip.

## 2. The Case Matrix

Key axis note: an interface key is `<name>/<declaring context>`. **Different name therefore implies different key**; the "different key, same name" and "different key, different name" cells are the only two off-diagonal cells, and "same key, different name" is unrepresentable.

Two gates stand between a junction and the comparator, and **both** must be cleared:

- **G1 (name gate)** in `validatePorts`: `if portIface == parentIfaceName: continue  # Names agree; not a cross-interface bind` — `processYaml.py:6036` (connections) and `processYaml.py:6098` (connectionMaps). **Both pre-step-1 line number, code since removed.**
- **G2 (key gate)** inside the comparator itself: `if parentIface['interfaceKey'] == childIface['interfaceKey']: return` — `processYaml.py:5813` (pre-step-1 line number, code since removed; step 1 replaced it with the resolved-identity short-circuit at `checkInterfacePair`, `processYaml.py:5976-5978`).

There is also a **precondition**: the endpoint block must carry a `ports:` (or `registerPorts:`) declaration for that port, else `validatePorts` `continue`s at `validatePorts`, `processYaml.py:6213-6218`. With no bottom-up declaration the port's interface *is* the connection interface, so there is nothing to compare; that is correct, not a gap.

And a topology note that changes how the matrix reads: **the check today is star-shaped, not endpoint-to-endpoint.** It compares (connection interface, resolved under a heuristic binding) against (endpoint's declared port interface, resolved under that endpoint's own variant). It never directly compares src port against dst port. `_connectionBinding(conn)` (inside `validatePorts`, `processYaml.py:6145-6162`) is a pure function of the connection and prefers the `dst` leaf, so the parent side resolves *identically* for both hops. Therefore **when both ends are cross-interface binds, src≡dst follows transitively**; when only one end is, it does not. **VERIFIED BY CODE READING**, and **VERIFIED BY EXECUTION** against `isp_top.db` (§7.1: all nine ISP datapath hops have both ends cross-interface).

| # | Parameterization | Interface relation | Reached today? | What the tool does today | Target behaviour |
| --- | --- | --- | --- | --- | --- |
| 1 | neither | same key | No — G1 and G2 | nothing | Nothing needed. Layout is identical by construction (one row, one resolver-independent evaluation). Skip legitimately. |
| 2 | neither | diff key, same name | No — **G1** | nothing. This is **G5.1**, and the failing cell `test_gap_cross_project_width_mismatch_detected` (`unittest/test_param_cross_project_linkage.py:264`) | **Must be checked.** Layout must agree, else reject. Nine `video_rgb_stream` and six `video_raw_stream` declarations exist in `isp_top.db` (**VERIFIED BY EXECUTION**), so this is the field-realistic cell. |
| 3 | neither | diff name | **Yes** | full comparator | Unchanged. |
| 4 | src only | same key | No — G1 and G2 | nothing | Check. src resolves at its variant; dst resolves the same row at declared defaults. A real mismatch is possible and invisible. |
| 5 | src only | diff key, same name | No — **G1** | nothing | Check. |
| 6 | src only | diff name | **Yes** | full comparator, but the **parent side is resolved under the dst's binding** (`_connectionBinding` prefers `dst`), i.e. under the *non*-parameterized end. Since the parent interface is literal in every real design, this is currently harmless. | Check with the parent side resolved under the *producer's* config, matching what the generator emits (§4.3). |
| 7 | dst only | same key | No — G1 and G2 | nothing | Check. |
| 8 | dst only | diff key, same name | No — **G1** | nothing | Check. |
| 9 | dst only | diff name | **Yes** | full comparator; here parent binding == child binding, so the two resolvers are identical and the comparison is purely structural | Check. Adequate today. |
| 10 | **both** | **same key** | **No — G1 *and* G2** | **nothing at db time.** SystemC compile fails with the `no matching function` message of §1.1. SystemVerilog accepts it silently and coerces (§3.5). | **The central gap.** See §2.1. |
| 11 | both | diff key, same name | No — **G1** | nothing | Check. This was the ISP's original authoring attempt; see §5.3. |
| 12 | both | diff name | **Yes** | full comparator; both hops checked, so src≡dst transitively | Unchanged in substance; fix the producer-side binding per row 6. |

**Nine of twelve cells are unreached. Every unreached cell is unreached because of G1, and rows 1/4/7/10 would remain unreached even if G1 were deleted, because of G2.** This is the single most important structural fact in this document: *removing the name gate is necessary but not sufficient.*

### 2.1 The same-key / different-config case — the empirical answer

The architect asked specifically about **same interface key on both sides, two endpoint instances resolving different configurations**, and asked for evidence rather than assumption.

**Answer: it is skipped silently, and it is skipped twice over. Confirmed, not refuted.**

Reachability — **VERIFIED BY CODE READING**, exhaustively:
- `checkInterfacePair` has exactly three callers in the tree: `validatePorts`, `processYaml.py:6253` and `:6291`, and `config/postParseRegisterPorts.py:655` (`grep -rn checkInterfacePair --include=*.py`).
- All three were gated by G2 at `processYaml.py:5813` (pre-step-1 line number, code since removed), which returned before any resolver is built when the keys are equal. The two `validatePorts` callers are additionally gated by G1.
- There is no other check anywhere that compares two endpoints' resolved configurations. `grep printError pysrc/processYaml.py | grep -i variant` returns nothing.
- `resolveConnectionConfig` (inside `getBDCrossInterfaceBinds`, `processYaml.py:2624-2654`) *observes* the disagreement and resolves it by policy rather than reporting it — its own comment reads "prefer dst when both ends are leaf-parameterizable and therefore disagree" (`processYaml.py:2646-2647`). The generator knows the ends can disagree and picks one.

Divergence — **VERIFIED BY EXECUTION** against the committed `examples/ip_test/ip_test.db`, read-only. One single interface key, evaluated under the two variants the design already declares:

```
iface ipDataIf/../../ip/yaml/ip.yaml   isParameterizable=1
  variant=variant0   data_t  total=9    fields=[('marker',1,0), ('data',8,1)]
  variant=variant1   data_t  total=71   fields=[('marker',1,0), ('data',70,1)]
```

`uIp0` binds `variant0`, `uIp1` binds `variant1`. A one-line authored connection `- {interface: ipDataIf, src: uIp0, dst: uIp1}` puts a 9-bit producer against a 71-bit consumer on one interface key. Both endpoints declare `ipDataIf` in `ports:`, so `portIface == parentIfaceName` on both ends → G1 skips both; and even without G1, `parentIfaceKey == childIfaceKey` → G2 returns. Zero diagnostics. The design is intra-project.

What happens downstream instead of a diagnostic:
- **SystemC:** the channel is typed from `resolveConnectionConfig`'s dst preference and the src port keeps its own Config, producing exactly the `xprojParam` `shared` failure — **COMPILE-VERIFIED (xprojParam)**, message in §1.1. An accidental catch, with a message that names neither the connection, the field, nor the widths.
- **SystemVerilog:** silent. See §3.5.

**So the gap is not confined to composition.** Any project with one parameterized block instantiated at two variants and a direct hop between them is exposed, in one file, today.

**One caveat on cell 1 vs cell 10.** They are the same code path but not the same risk: cell 1 (neither side parameterized, same key) is *provably* safe to skip, cell 10 is not. Any fix must distinguish them by resolved configuration, not by key equality.

**Architect clarification, 2026-08-10, and what it settles.** In the architect's words: *"static same name interfaceKey within a project a project are guarenteed to be the same"*. **VERIFIED BY CODE READING:** an `interfaceKey` is built as `<interface>/<declaring context>` (`pysrc/schema.py::build_storage_key`; `interfaces` is a single-entry `flat` section), so equal keys imply the same declaring context and therefore the same static declaration, by construction. All three `checkInterfacePair` callers pass that declaring context — the two `validatePorts` callers read `ifaceRow['_context']` directly, and the `postParseRegisterPorts` caller passes the `qualification` returned by `lookupInScope`, which is the `data[section][context][name]` bucket the row is stored under, i.e. the row's own `_context`.

Two consequences, and the second is the one that matters:

- **Equal keys need no structural re-establishment.** There is no need to prove the two sides' declarations agree; they *are* one declaration. For an equal-key junction the whole question reduces to evaluating that single declaration under two configurations.
- **Equal keys are still not a licence to skip.** Cell 10 is precisely equal `interfaceKey` with two endpoints at different configurations. So the predicate is `equal key AND equal resolved configuration`, never `equal key` alone.

This makes any `parentContext == childContext` term in the short-circuit **provably redundant** — it cannot be false when the key comparison is true — and it was removed from the step-1 implementation accordingly.

## 3. Junction Kinds The Check Must Cover

`validatePorts` iterates exactly two collections: `connections` (`validatePorts`, `processYaml.py:6180-6260`) and `connectionMaps` (`:6262-6295`). Everything below is measured against that.

### 3.1 `connections`
Covered, subject to G1/G2 and to the declared-port precondition. Synthesised rows (`_context == '_global'`) are exempt by design (`validatePorts`, `processYaml.py:6183-6184`).

### 3.2 `connectionMaps`
Covered, subject to the same gates, plus two narrower limitations: it consults only `blockRow['ports']`, never `registerPorts` (`validatePorts`, `processYaml.py:6272`), and the parent binding uses `_mapParentBinding` (`:6164-6172`), an explicitly "best-effort" heuristic that returns `('','')` unless the mapped block has its own params.

### 3.3 Block `ports:`
Not a junction in its own right — it is the bottom-up declaration that supplies the *child* side of every junction above. `validateDeclaredPorts` (`processYaml.py:5689-5875`) reconciles declared vs. inferred **name and direction** only; it never compares payloads. Correct division of labour.

### 3.4 `registerPorts:` and register-bus dispatch
- **Router → routed leaf:** `postParseRegisterPorts.py` deliberately does *not* check at synthesis time — its comment at `config/postParseRegisterPorts.py:600-604` states "compatibility of an authored leaf is checked at the end of projectCreate by validatePorts, which reads registerPorts: as part of the leaf's declared-port surface; synthesis only emits the bind here." `validatePorts` does read `registerPorts` (`processYaml.py:6208-6212`) and builds a good `locationStr` (`:6241-6246`) — **but G1 still applies.** **VERIFIED BY EXECUTION:** all nine router→leaf dispatches in `isp_top.db` are same-key/same-name and therefore skipped (`u_apb_decode.cpu_apb_reg_u_<x>` ↔ `u_<x>.regs`, all on `cpu_apb_reg/../../isp_shared/yaml/shared_types.yaml`). In `ip_test.db` the same relation *is* checked, only because the leaf spells its port interface `ipReg` while the router dispatches `apbReg`. Coverage is an accident of naming.
- **Router → nested router:** checked at synthesis time (`config/postParseRegisterPorts.py:655-666`), with a good location string. Still subject to G2.
- The follow-up recorded in [`plan-register-bus-cross-interface-check.md`](./plan-register-bus-cross-interface-check.md) "Open Questions" — the leaf-to-handler `connectionMap` — remains unchecked and is now in scope for this plan.

### 3.5 The RTL path — confirmation that the db check is the only real gate
**VERIFIED BY READING GENERATED SV.**

Child module port lists use bare modports with no payload type:
```systemverilog
// /work/ws/isp/isp_blc/rtl/blc.sv:16-18
    rdy_vld_if.dst raw_video_in,
    rdy_vld_if.src raw_video_out,
    apb_if.dst regs,
```
The container instantiates one channel per connection, typed from **its own** resolution:
```systemverilog
// /work/ws/isp/rtl/isp_top.sv:29
    rdy_vld_if #(.data_t(isp_video_bayer_t)) raw_csi2raw_stream();
// /work/ws/isp/debayer/rtl/debayer.sv:101
    rdy_vld_if #(.data_t(bayer_preprocess_stream_t)) bayer_preprocess_stream();
```
`rdy_vld_if.dst raw_video_in` is a *generic* interface port: SystemVerilog checks the interface name and modport, never the parameter values. Each child re-declares its own payload struct from its own module parameters (`blc.sv:24-38`) and assigns positionally from the channel (`isp_blc/rtl/blc_correction.sv:80` `n_stg1_data = raw_video_in.data.data;`). A width disagreement is silently coerced.

There is exactly **one** channel type per connection in SV and it comes from the container's parameters. A container cannot express two different payload widths for one channel, so the SV back end is structurally incapable of representing — let alone catching — cell 10. **The db check is the only gate that exists for RTL.**

This is also why the architect's definition being SV-derived is a specification of *intent* rather than an existing enforcement point: nothing in the SV flow enforces it.

### 3.6 Testbench / DUT boundary
This is the `--excludeInst` pruned-connection path (`bug7-…`:56-62: "A DUT is always excluded from its own tbExternal … A DUT-boundary connection can never be a `connectDouble`"). Two findings:

- The *connection* is checked at db time like any other, because `validatePorts` runs at `projectCreate` and knows nothing about generator-time exclusion.
- But **the pair validated is not the pair emitted.** At emission, `annotate` supplies `parentConfigOverride=connVal['excludedEndConfig']` — the DUT's config (`getBDCrossInterfaceBinds`, `processYaml.py:2874`) — and for non-pruned binds `resolveConnectionConfig(connVal, excludeEndKey=endKey)` excludes the end being annotated so the *producer* governs the up side (`resolveConnectionConfig`, `processYaml.py:2624-2632`). At db time `_connectionBinding(conn)` has **no** exclusion and prefers `dst`. So for a connection whose ends are both leaf-parameterizable, the validator checks the src port against the connection interface resolved under the **dst's** parameters while the generator emits a thunker whose up side is resolved under the **src's**. `examples/xif` passes only because `src`, `dut` and `sink` all bind `DATA_WIDTH: 16` (`examples/xif/arch/yaml/xif.yaml:96-108`). **VERIFIED BY CODE READING.**

### 3.7 Out of scope by construction
`memoryConnections` and `registerConnections` are passed to `validateDeclaredPorts` with `interfaceKey=''` (`processYaml.py:5774-5798`); a declared port bound by one whose interface name differs is rejected outright with "does not provide a connection interface for cross-interface validation" (`validateDeclaredPorts`, `processYaml.py:5813-5824`). There is no payload to compare. Correct as-is; name it so nobody looks for the gap later.

## 4. Where The Check Belongs

### 4.1 db-time vs. projectOpen — settled, with a citation
db time. The contract is already written down: `getBDCrossInterfaceBinds`'s own header states "projectCreate.validatePorts() performs the expensive structural compatibility checks. This view pass only records already-valid semantic facts so language templates do not need to re-walk raw project tables" (`getBDCrossInterfaceBinds`, `processYaml.py:2579-2583`). This matches `builder-base-development` ("project-wide truth derived from YAML … in `projectCreate`"). Do not move the comparator into a view.

### 4.2 Cost — measured, not estimated
**VERIFIED BY EXECUTION**, read-only replay against `/work/ws/isp/isp_top.db` (the largest design available: 90 instances, 32 interfaces, 121 structures, ~50 YAML files across 11 projects):

- Junction **sides** enumerated across all user `connections` ends plus all `connectionMaps` (both the mapped instance side and the parent side): **158**.
- Distinct `(interfaceKey, blockKey, variant)` triples among them: **112** (29% dedup).
- Wall time to resolve all 158 sides, un-memoised, including the two-statement SQL variant-binding query per side: **0.235 s**.
- Memoised on the triple: **0.185 s**.
- For reference, `projectOpen` load of the same db: 0.250 s.

Read the numbers correctly: **there is no blow-up.** A quarter of a second for every junction of an eleven-project design. Memoisation on `(interfaceKey, blockKey, variant)` is sound — the resolved packed form is a pure function of that triple — but buys ~22%, and most of the residual is the per-side SQL. Under the `builder-base-development` rule against speculative caches, **do not memoise until a design makes it matter.** Scaling is linear in junctions × fields; **CONJECTURE:** it stays well under a second for designs several times this size.

The correct cost concern is not CPU. It is that the check currently runs at `projectCreate.__init__`, `processYaml.py:3837`, *after* `runCreateArtifacts()` at `:3835` — so a compatibility failure aborts having already written build artifacts. Worth moving earlier; it has no dependency on artifact creation.

### 4.3 Ordering and FK invariants
No new ordering hazard.

- `validatePorts()` runs last in `projectCreate.__init__` (`processYaml.py:3837`), after `processYamls`, `calcAddresses`, `calcBlockConfigInfo` and `deriveParameterizedDeclSets`. `isParameterizable`, `configContext` and the full variant tables are complete.
- Per `config/SCHEMA_SPECIFICATION.md`, "Governing Invariants": this is legitimately a project-wide pass, because a junction is a relation among rows in three tables authored in as many files, with no single row to hook. It already is one.
- **It must resolve every reference in its own scope.** `checkInterfacePair` does this correctly — one `ValueResolver` per side with that side's `context` (`checkInterfacePair`, `processYaml.py:6026-6035`), and block params re-resolved through the block's own include chain via `lookupInScope('constants', row['_context'], row['param'])` (`deriveParameterizedDeclSets`, `processYaml.py:5290-5298`), the documented-correct idiom. Nothing here needs `scope: global`.
- One latent soundness note, **VERIFIED BY CODE READING**: `variantValueBindings` (`processYaml.py:5922-5924`) inserts the **bare** param name into the resolver's `values` dict alongside the two qualified keys, and `_resolveActiveValue` checks `if ref in self.values` **before** any context resolution (`valueResolver.py:132-133`). A side's bare-name override therefore applies to *any* same-named constant reachable from that side's context. For a transit container whose params collide by name with a sub-project's, this can silently apply the wrong project's value. Not currently triggered by any design in the tree; worth recording.

### 4.4 Options

**Option A — delete the gates, keep the topology.**
Remove G1 at `:6036` and `:6098`; remove G2 at `:5813`; add a cheap identity short-circuit for cell 1 (both sides resolve to the same triple ⇒ skip); and, per §8.2=(c), delete the field-name comparison at `:5888-5901` (§1.2.1). **All four are pre-step-1 line number, code since removed.** Roughly a five-line change plus the new short-circuit and the deletion.
- *For:* smallest possible diff. Reuses a comparator whose diagnostics are already good. Measured blast radius **zero** across every database in the tree (§7). Lands cells 2, 4, 5, 7, 8, 10, 11 immediately.
- *Against:* keeps the star topology, so cells 4/5/7/8/10 are checked against the connection interface under a *heuristically chosen* binding rather than endpoint-to-endpoint. Keeps `_connectionBinding`'s dst preference, which is the wrong parent for the src hop (§3.6). Fixes nothing about bindability, so cell 10 becomes an error where today it is a compile failure — an improvement, but it does not enable the case. Leaves the projectOpen thunker predicate still keyed on **name** difference (`getBDCrossInterfaceBinds.annotate`, `processYaml.py:2777-2778`, `:2794-2795`), so the validator and the generator continue to disagree about which junctions need adaptation.

**Option B — one junction-oriented pass, endpoint-to-endpoint, with the adaptation predicate persisted (RECOMMENDED).**
A `projectCreate` pass that (1) enumerates every junction from the resolved design — both connection ends, connectionMaps, and the register-bus binds, with `registerPorts` in the surface everywhere; (2) computes each side's *effective* interface (declared port interface if present, else the connection interface) and its resolved configuration identity; (3) compares src↔dst directly **and** each side↔channel, since the channel is what is emitted; (4) rejects layout incompatibility; and (5) persists a per-junction "adaptation required" fact so `getBDCrossInterfaceBinds` reads it instead of recomputing a name comparison. The per-pair comparator stays exactly as it is.
- *For:* fixes the topology, not just the gates. Makes the validator's and generator's notions of "needs adaptation" **one** fact rather than two independently-computed name comparisons — which is what §1.1 shows is actually broken. Puts the register-bus relations under the same rule instead of leaving coverage to naming accident. Aligns with the stated contract at `getBDCrossInterfaceBinds`, `processYaml.py:2579-2583` (projectCreate decides, the view records). Naturally accommodates the per-container-variant evaluation that `inheritContainerParam` requires (§1.3).
- *Against:* larger. Touches the projectOpen thunker predicate, which **changes generated code** for junctions that are same-name but different-config — currently un-thunked. Needed an architect answer to §8.1/§8.3 before it could be specified; both are **RESOLVED 2026-08-10 as (b)**, so it is specifiable and is "Plan of record" step 3.

**Option C — move to projectOpen.** Rejected. Contradicts `getBDCrossInterfaceBinds`, `processYaml.py:2579-2583`, would run once per generator invocation, and gives no diagnostic at `make db`.

**Recommendation: Option B**, with Option A's gate removal as its first, independently-valuable step — Option A's diff is strictly contained in Option B, ships the entire layout half of the goal, and has measured-zero blast radius.

**Recommendation adopted. RESOLVED 2026-08-10:** §8.1=(b) selects **Option B**, with Option A's gate removal as its first, independently-valuable step. The paragraph below is retained as the record of the alternative that was not taken; it is no longer live.

**What would change my mind.** If the architect answers §8.1 as "layout only; the straight-through parameterized path stays permanently out of scope and cell 10 is simply an error", then Option A *is* the whole answer and Option B is over-engineering — the thunker predicate never needs to become config-aware, because a config difference will always be a hard error rather than something to adapt. I would also switch to Option A if the projectOpen predicate change turns out to alter generated output for any junction in `examples/` or `/work/ws/isp`; my §7 measurement says it does not, but that measurement covers layout, not the thunker predicate.

## 5. Interaction With The Recorded Gaps

Cross-reference: defect definitions are in [`plan-ip-project-composition.md`](./plan-ip-project-composition.md) C6, "Recorded defects" and "Findings from the test matrix". Not restated here.

### 5.1 G5.1 — subsumed, but only if **both** gates go
G5.1 *is* this check. C6 records the name gate. It does not record G2 at `processYaml.py:5813` (pre-step-1 line number, code since removed). Deleting G1 alone leaves cells 1, 4, 7 and **10** — the dangerous one — exactly as unchecked as before. Recording this is the single most useful correction this document makes to C6.

### 5.2 G5.2 — **not** subsumed, and **not** a prerequisite for validation
This corrects an earlier framing. The db-time check does **not** use the bare-name fallback: `validatePorts` reads the persisted parse-time foreign key directly, `childIfaceKey = portEntry['interfaceKey']` (`validatePorts`, `processYaml.py:6221`, and `:6280` for connectionMaps). C6's own refinement says the same: "the parse-time foreign key resolves the port's interface correctly in the block's own scope and persists it on the ports row". So a db-time compatibility check compares the **right** interfaces.

The bare-name fallbacks at `processYaml.py:1976-1979` (`_resolveDeclaredPortInterfaceKey`) and `:2608-2611` (`resolveInterfaceKey` inside `getBDCrossInterfaceBinds`) are **projectOpen** re-derivations. They corrupt the **emitted thunker payload**, not the validation verdict.

Therefore: **resolution correctness is a prerequisite for the emission half (Option B step 5), not for the validation half (Option A / Option B steps 1-4).** Landing the layout check first is sound and does not wait on G5.2. Conversely, unifying the adaptation predicate while `resolveInterfaceKey` can still first-match-wins across nine `video_rgb_stream` declarations would propagate a verified-correct verdict onto a wrongly-resolved payload — worse than today, because it would carry an air of authority. Sequence accordingly.

### 5.3 G5.3 — subsumed only if `_validateParameterizedConnectionEndpoints` is narrowed
`_validateParameterizedConnectionEndpoints` (`processYaml.py:5357-5404`) enforces a genuinely different invariant from layout compatibility: *a SystemVerilog module can only size a payload from parameters it owns*, so an endpoint reached through a parameterized interface must itself carry that interface's backing parameters. A layout check cannot express that. **It is still necessary. It is also over-broad.**

The over-breadth is the source of the misleading message. The rule iterates every end of every parameterizable connection with **no exemption for an endpoint that declares its own interface** (`_validateParameterizedConnectionEndpoints`, `processYaml.py:5388-5401`). But when an endpoint's port carries its *own* interface — a cross-interface bind — the block does not need the connection interface's parameters at all: it sizes its port from its own, and a thunker bridges. The invariant only genuinely applies when the endpoint's declared port interface resolves to the **same interface key** as the connection.

That narrowing is exactly the ISP field case. `/work/ws/isp/yaml/isp_top.yaml:43-48` records it verbatim:

> "nine of the ten IP files each define a `video_rgb_stream` and six define a `video_raw_stream`. Naming those IP-owned types on the ISP's connections meant one definition won and the parameter backing resolved in that file's scope, so every block from ccm onward failed 'does not declare the required parameter(s)'."

(**VERIFIED BY EXECUTION:** exactly 9 `video_rgb_stream` and 6 `video_raw_stream` interface keys in `isp_top.db`.) Under the narrowing, that authoring shape would pass the endpoint rule — correctly, since each block sizes its own port — and land in cell 11, where the general layout check is the right adjudicator.

**Assessment: narrower, not redundant.** Restrict it to same-key endpoints; the general check takes cells 2/5/8/11.

### 5.4 G5.4 — not subsumed
Config-struct composition from a single `configContext` (`_buildVariantConfigDescriptors`, `processYaml.py:1841-1852`) is orthogonal. A layout check evaluates *widths*; G5.4 is about which *fields a Config struct has*. Independent.

Note the correction that supersedes C6's "Findings from the test matrix": the shared-`include:` path is db-clean and gen-clean but **not** compile-clean. **COMPILE-VERIFIED (xprojParam):** two independent failures — `templates/systemc/blockRegistrar.py:100-101` emitting the retired `#include "<block>.h"` form when a container is `isParameterizable` with `hasOwnParams` false, and downstream instances typed on the **upstream default** config (`xpFilterSharedBase<xpGainDefaultConfig>`) while the parameter-owning block keeps its variant config (`xpGainBase<xpGainV0Config>`). C6's "a parameterized cross-project path DOES exist and is accepted" holds **at db level only** and should be amended there. Root cause of the second failure is the documented limitation at `_resolveInstanceConfigFields`, `processYaml.py:1602-1607`, not the layout check's business.

### 5.5 G5.9 — not subsumed, and the compatibility check **cannot** detect it
Worse than C6 records. **COMPILE-VERIFIED (xprojParam):** on the include-reached path an over-max binding is not merely unchecked — it is **silently discarded**, leaves no trace in any generated artifact, and the instance is typed at the upstream default width. The identical binding in the owning file is correctly rejected at db time.

This is unreachable for a compatibility check by construction: if the binding is discarded, **both** sides resolve at the upstream default, the layout agrees, and the check passes. The failure mode is "the design silently isn't what you asked for", not "the two sides disagree". `_post_validateVariantBindingSizing` (`processYaml.py:7984`) must be fixed on its own terms.

### 5.6 G5.6 — reclassified
**COMPILE-VERIFIED (xprojParam):** reproduces, and is *not* a composition defect.
```
deparam/model/xpDeparamTop.cppm:53:39: fatal error: reference to 'videoSt' is ambiguous
  candidates: xpGain_ns::videoSt, xpFilter_ns::videoSt, xpSink_ns::videoSt
```
The `uniq` control — identical topology, identical generated shape, prefixed identifiers — compiles and runs clean. Cause: **unqualified naming of a colliding identifier in the generated block module**, reachable whenever sibling namespaces export the same type name. Independent of parameterization and independent of this plan; it is a generated-code qualification defect. Named here only so nobody attributes it to the compatibility check.

### 5.7 Two further prerequisites the harness surfaced
- **No-variant is not a fallback.** A parameterizable child instance with no `variant:` crashes `make gen`: `_resolveSvInstanceParams`, `processYaml.py:2006`, `spelling = str(variantValues[paramName])`, raises `KeyError` on the param name. **VERIFIED BY CODE READING** (line confirmed) and **COMPILE-VERIFIED** by the harness. So "leave it on `DefaultConfig`" is not an available remedy for any junction this check rejects.
- **Ownership resolution decides what is being compared.** Context ownership among equal-depth providers is a **lexical tie-break on provider path** — `pysrc/projectScan.py:367-374`, "Shallow-to-deep so the deepest closure that reaches a shared file wins; equal-depth ties break lexically on the provider path". In the harness this renamed an upstream module and broke the composed build until the project references were restructured so the upstream provider sits at depth 2 (`examples/xprojParam/README.md`, "Reference depth decides context ownership"). Since ownership determines which project's declarations a junction resolves against, this belongs with G5.2 in the resolution-correctness prerequisite for the **emission** half.

### 5.8 Two further defects the `cppLeaf`/`cppAxis` fixture surfaced — out of scope for every step

Recorded here beside the other prerequisite/defect notes rather than in §9, because neither is a compatibility question and neither is in scope for any step in the Plan of record. Both were found while building the parameterized-against-parameterized fixture that discharges §9.5's evidence gate, and the fixture is **shaped around** both rather than blocked by either. Listed in "Deferred / Out of Scope".

- **A `connectionMap` whose parent interface is parameterizable mis-attributes the mapped child's config context.** `calcBlockConfigInfo` step 3 (`processYaml.py:4950-4956`) adds a map's interface with `own_surface=True` whenever `cm['instanceKey']` is an instance of the block being walked — i.e. it attributes the *container's* parameterizable interface to the mapped **child** block's own surface. The interface's structures are declared in the container's file, so that file lands in `contexts`, and when it lands first it becomes `contexts[0]`, which `:5015-5030` persists verbatim as the child's `configContext` and turns into its `defaultConfig`. **VERIFIED BY EXECUTION**, read-only against the fixture's two databases: in `examples/xprojParam/cppLeaf/xpCppLeaf.db` each `xpCppLeaf*` block has `configContext = ../../yaml/xpCppLeaf.yaml` / `defaultConfig = xpCppLeafDefaultConfig`; in the composed `examples/xprojParam/cppAxis/xpCppAxis.db` the same four blocks have `configContext = ../../yaml/xpCppWrap.yaml` / `defaultConfig = xpCppWrapDefaultConfig` — the container's file, in a project that owns neither the child nor its declarations.

  The downstream consequence is a *silent* wrong Config, not a diagnostic. `_buildVariantConfigDescriptors` computes `owner_project = self.contextOwningProject[config_context]` (`processYaml.py:1832-1840`) from that mis-attributed context, so a variant binding declared in the child's **own** file is classified `isForeign`. `_resolveInstanceConfigFields` then passes `consumer_project = self.contextOwningProject[instanceData['_context']]` (`processYaml.py:1643-1646`) — the container's project — and `_selectVariantDescriptor` (`processYaml.py:1665-1681`) returns the foreign descriptor only when `desc['declaringProject'] == consumerProject`, which is a third project here, and has no same-project descriptor to fall back on. It selects **nothing**, so the instance falls back to `defaultConfig`, which does not carry the child's parameter. **Observed symptom:** the child instance typed `xpCppLeafEqBase<xpCppWrapDefaultConfig>`, which does not compile. **VERIFIED BY CODE READING** for the selection chain. The fixture works around it by declaring the `cppLeaf` variants in the container's file (`examples/xprojParam/cppAxis/yaml/xpCppWrap.yaml:106-114`) rather than in `cppLeaf`'s own. `examples/ip_test/bridge` never reaches it: its two `connectionMap` parent interfaces are `data8If`/`data70If` (`bridge/yaml/ipBridge.yaml:131-132`), whose payloads `data8St`/`data70St` are literal, so `add_interface` returns before adding any context.

- **`connectionMap` thunker members collide by name.** `_thunker_member_name` (`pysrc/intf_gen_utils.py:899-906`) names a `connectionMap` thunker member `thunker_<instance>` and nothing else — no map, port or interface component — while the peer-to-peer arm qualifies with the channel name. `sc_declare_thunkers` (`pysrc/intf_gen_utils.py:930-940`) emits one member per flagged end, and `_flagged_thunker_ends` yields one flagged end per map (`:923-925`), so **two maps from one container into the same child instance emit two identically-named members**, which is invalid C++. **VERIFIED BY CODE READING.** The fixture works around it by giving each of its four boundary shapes its own consumer block and its own child instance (`xpCppWrap.yaml:101-104`, four maps into `uLeafEq`/`uLeafOrder`/`uLeafSign`/`uLeafNest`) — which is why `cppLeaf` declares four single-port blocks rather than one block with four ports. `examples/ip_test/bridge` never reaches it either: its two maps target `uBridgeIp0` and `uBridgeIp1` (`bridge/yaml/ipBridge.yaml:131-132`).

## 6. Diagnostics Design

### 6.1 What a message must carry
Both sides, and for each: the instance and port, the block, the **owning project**, the **declaring file**, the **resolved variant and Config identity**, and the **first differing field position, with both widths and both offsets**. Plus a remedy that is actually available given §1.1 (`DefaultConfig` is not a fallback per §5.7; and once 8.4=(b) lands, a thunker exists for every protocol, so the "no adapter on this protocol" caveat is time-limited).

**The first difference is identified by field index, not by field name (§8.2 = (c)).** Names are uncompared, so no name can be the thing that differs and no name can name the position. Both sides' names are still *printed* on their own lines, because a reader needs them to find the field in the YAML — and because when the names legitimately differ the message must show both rather than imply one. Printing a name is fine; comparing it is not.

### 6.2 Before / after — the layout case (G5.3, the real message)

**Before** (asserted verbatim in `unittest/test_param_cross_project_linkage.py:155-161`; the shape of the message quoted from the field at `/work/ws/isp/yaml/isp_top.yaml:43-48`):

```
Parameterized interface 'dataIf' on the connection 'uA' -> 'uB' connects endpoint
instance 'uB' (block 'bIp'), which does not declare the required parameter(s):
missing WIDTH. A block reached through a parameterized interface must itself carry
the backing parameter(s) so the payload is sized in its own module scope.
```

Three things are wrong with it. It says `WIDTH` is missing from a block that demonstrably declares `WIDTH`. It never mentions that the mismatch is one of *declaring file / project identity*. And it offers a remedy — declare the parameter — that the author has already followed.

**After**, for the same fixture under the general check (the endpoint rule having been narrowed per §5.3, so the junction reaches the layout comparator):

```
error: interface payloads at this junction are not compatible in the configurations
       instantiated.
  junction: connection 'uA' -> 'uB' on interface 'dataIf'
            (declared in ../../top/yaml/chainTop.yaml)
  src end:  uA.out   block 'aIp'  project 'projA'
            interface dataIf   declared in ../../projA/yaml/aTop.yaml
            configuration: variant 'v0'  (aIpV0Config)   WIDTH=8
  dst end:  uB.in    block 'bIp'  project 'projB'
            interface dataIf   declared in ../../projB/yaml/bTop.yaml
            configuration: variant 'v0'  (bIpV0Config)   WIDTH=16
  first difference: field index 1 of structureType data_t (fields are compared
            positionally; names are shown for reference only and are not compared)
            src: 'data'  width 8  at bit offset 1  (structure dataSt, ../../projA/yaml/aTop.yaml)
            dst: 'data'  width 16 at bit offset 1  (structure dataSt, ../../projB/yaml/bTop.yaml)
  These are two distinct declarations that share the name 'dataIf'; they resolve to
  different parameters (WIDTH/../../projA/yaml/aTop.yaml vs
  WIDTH/../../projB/yaml/bTop.yaml) and therefore cannot track one another.
  Remedy: declare an assembler-owned literal-width boundary interface and let a
  thunker adapt each leg (see examples/xprojParam/uniq), or bind both endpoints to
  one shared declaration reached by include:.
```

Every field in that message is available at the call site today: the project from `contextOwningProject`, the Config identity from `_buildVariantConfigDescriptors` / `_selectVariantDescriptor`, and the field triples from `structPackedFields`.

**Correction 2026-08-10, found during step 1 implementation: the Config-identity half of that sentence is wrong.** `_buildVariantConfigDescriptors` and `_selectVariantDescriptor` are **`projectOpen`** methods, and `projectCreate` is not a subclass of `projectOpen` — so they are unreachable from `checkInterfacePair`. Two further facts close the option off rather than merely complicating it:

- The block fields the descriptors are built from (`defaultConfig`, `configContext`) are persisted by `calcBlockConfigInfo`, which runs *after* `postYamlExternalScript()`. One of `checkInterfacePair`'s three callers is `config/postParseRegisterPorts.py`, which runs inside that earlier phase, so those fields do not yet exist for that caller.
- The `<block><Variant>Config` spelling is a **C++ spelling** produced in the template layer (`intf_gen_utils.cpp_variant_config_name`); `_buildVariantConfigDescriptors` documents that its descriptors carry "NEUTRAL identity only … never here in core". Emitting that struct name from `projectCreate` would put a language-specific spelling in the language-neutral layer.

What step 1 prints instead is the configuration identity that *is* uniformly available at all three call sites and is neutral: **owning project + block + resolved variant label**, for each side, alongside the interface's declaring file. The resolved parameter *values* (`WIDTH=8`) are also not printed: `variantValueBindings` returns bare, block-param-qualified and param-qualified keys in one dict, so isolating the bare names would mean string-inspecting dict keys, which `builder-base-development` forbids. The differing widths and offsets — the actionable numbers — are printed by the field diagnostic itself.

### 6.3 Before / after — cell 10, the same-key case
**Before:** nothing at `make db`; at `make gen`+compile,
```
fatal error: no matching function for call to object of type 'push_ack_out<videoSt<xpGainV0Config>>'
note: no known conversion from 'push_ack_channel<videoSt<xpGainDefaultConfig>>' ...
```
which names no connection, no instance, no field, no width — and in the RTL flow, nothing at all.

**After:**
```
error: interface 'ipDataIf' is instantiated at two different configurations across
       one junction.
  junction: connection 'uIp0' -> 'uIp1' on interface 'ipDataIf'
            (../../ip/yaml/ip.yaml)  - one declaration, two configurations
  src end:  uIp0.ipDataIf  block 'ip'  variant 'variant0'  (ipVariant0Config)
            IP_DATA_WIDTH=8   payload data_t: marker@0 w1, data@1 w8   (total 9)
  dst end:  uIp1.ipDataIf  block 'ip'  variant 'variant1'  (ipVariant1Config)
            IP_DATA_WIDTH=70  payload data_t: marker@0 w1, data@1 w70  (total 71)
  first difference: field index 1 of structureType data_t - width 8 vs 70, both at
            offset 1. src field 'data', dst field 'data'. (Positional comparison;
            names shown for reference only and not compared.)
  A parameterized interface cannot carry two configurations
  (plan-parameterizable-config-template.md:545). Introduce a literal-width boundary
  interface on this connection so each end binds its own interface and a thunker
  adapts, or bind both instances to one variant.
```

### 6.4 Three diagnostics defects to fix alongside
- The message says "cross-interface bind" throughout (`processYaml.py:5820`, `:5840`, `:5879`, `:5890`, `:5905`, `:5918` — all pre-step-1 line number, code since removed; step 1 reworded every one of them to "the two interfaces at this junction", §7.1a). Once cell 10 is reachable the junction is *not* a cross-interface bind — it is one interface at two configurations. The wording must not presuppose the old topology.
- Both widths and offsets are already in the width and offset messages (pre-step-1 `processYaml.py:5903-5926`; now `checkInterfacePair`, `:6065-6092`), but the **structure name is printed without its declaring file** on the width message, and neither project nor variant appears anywhere. In a composed build `dataSt` vs `dataSt` is unreadable without the qualification.
- The width and offset messages identify the field by **name** (`field '{pname}' of …`). Under 8.2 that is no longer a well-defined identifier, because the two sides' names may legitimately differ — the messages would then print one side's name for a pair that has two. They must lead with the **field index** and print both names, per §6.1. The third message, the field-name mismatch at `processYaml.py:5888-5901` (pre-step-1 line number, code since removed), is not reworded at all: it is **deleted** (§1.2.1).

## 7. Migration and Blast Radius

### 7.1 Measured, not estimated
**VERIFIED BY EXECUTION.** A replay of the proposed endpoint-to-endpoint layout check — each side's effective interface resolved through its own `ValueResolver` with its own context and its own variant bindings, exactly as `checkInterfacePair` does — over every two-ended user connection in every database in the tree, read-only:

| Database | Two-ended user connections | Layout mismatches under the general check |
| --- | --- | --- |
| `/work/ws/isp/isp_top.db` (11 projects, 90 instances) | 21 reached, of which 18 are `isp_top`-owned | **0** |
| `/work/ws/isp/debayer/debayer.db` | 5 | **0** |
| `examples/ip_test/ip_test.db` | 15 | **0** |
| `examples/simple_ip/simple_ip.db` | 5 | **0** |
| `examples/xif/xif.db` | 2 | **0** |

**Nothing in the tree breaks.** For `isp_top` specifically: 18 owned connections, of which 9 are the datapath hops and 9 the register-bus dispatch; the nine datapath hops all resolve to identical packed forms on both sides (`video_raw_stream` 35 bits both ends, `video_rgb_stream` 99 bits both ends, across `csi2raw`→`blc`→`lsc`→`gain`→`debayer`→`awb`→`ccm`→`rgb_gain`→`lut`→`vid2axis`); the nine register-bus dispatches are all `cpu_apb_reg` at 64 bits both ends. Nine of the eighteen are currently skipped by G1 (all nine register-bus binds).

`examples/xprojParam` is excluded from this table — its `deparam` and `shared` configurations are recorded *expected* compile failures.

### 7.1a Confirmed by execution after step 1 landed (2026-08-10)
The §7.1 prediction held. With G1 and G2 removed and the field-name check deleted:

- Unit suite (`unittest/run_all_tests_parallel.sh`): **95 suites, 94 passed**. The single failure is `test_param_cross_project_linkage.py` at **4/6**, up from 3/6: the G5.1 width-mismatch cell now passes, and the two remaining failures are the G5.2 bare-name cell (step 2 work) and the G5.9 sizing cell (an independent defect, §5.5).
- `make pipeline-test` (15 example targets: `nested`, `hello-world`, `mixed`, `pySocket`, `in-and-out`, `lint-axi`, `lint-hier`, `apbDecode`, `axiDemo`, `axi4sDemo`, `hierVlDemo`, `ip-test`, `simple-ip`, `xproj-param`, `diagram-and-doc`) — **green**, including the verilated cosim runs.
- `examples/xif` — builds and runs clean.
- The ISP design (`prj/yaml/isp_topProject.yaml`, 90 instances / 51 connections / 32 interfaces, replayed against a copy of the tree) — **db-clean, zero diagnostics**.
- `/work/ws/debayer` — `make clean && make db && make gen` clean, with **byte-identical generated output** (no working-tree churn), as expected from a check that persists nothing.

Three unit suites asserted the old `"cross-interface bind"` wording and were updated as the deliberate, visible test change §6.4 requires: `test_error_declared_ports.py`, `test_error_register_interface_type_mismatch.py`, `test_error_register_packed_form.py`.

**Cell 10 is now caught, verified by execution.** A purpose-built probe — one parameterizable block declaring its own `ipDataIf`, instantiated twice at `WIDTH: 8` and `WIDTH: 70` with a direct connection between them — produced **zero diagnostics** on the pre-change generator and is now rejected:

```
... per-field _bitWidth must agree at every payload position, but field index 1 of
structureType 'data_t' differs: parent field 'data' has _bitWidth 70 at bit offset 1
in structure 'dataSt' (file cell10probe_arch.yaml) while child field 'data' has
_bitWidth 8 at bit offset 1 in structure 'dataSt' (file cell10probe_arch.yaml).
Fields are compared positionally; the names are shown for reference only and are not compared.
  parent side: interface 'ipDataIf' declared in cell10probe_arch.yaml (project cell10probe)
    resolved for block 'ip' (project cell10probe) at variant 'v1'
  child side: interface 'ipDataIf' declared in cell10probe_arch.yaml (project cell10probe)
    resolved for block 'ip' (project cell10probe) at variant 'v0'
```

**One defect found by review and fixed inside step 1.** Removing G1 exposed a false positive on the `inheritContainerParam` shape that §1.3 and §7.4 had both asserted could not occur. It is reproduced, corrected in place at §1.3 and §7.4, and guarded by two new cells in `unittest/test_inherit_container_param.py`. Step 1 now declines to adjudicate any connection with an inheriting endpoint.

**Three residuals, recorded rather than fixed.**

- The short-circuit keys on resolved *layout* inputs, so cell 10 with two distinct variants that happen to bind **equal values** is still skipped. That is correct for a layout check — the packed forms are genuinely identical — but the junction remains non-bindable in C++ because the two `Config` types differ (§1.1). Closing that is step 3's thunker-predicate move.
- The diagnostic's side blocks name the **block**, not the **instance**, so in a cell-10 message both sides read `block 'ip'` and differ only by variant. §6.1's target message carries the instance. This follows from Option A keeping the **star topology** — the parent side is a connection interface under a chosen binding, not an endpoint — so it resolves naturally with the endpoint-to-endpoint pass, not before it.
- `_junctionSideIdentity` indexes `contextOwningProject[...]`, which is keyed by real file paths and has no entry for the special contexts `_global` / `_a2csystem`. It is **not reachable today**: no base or pro `*_if.yaml` declares an `interfaces:` section, user `systemFiles:` are not loaded, and the shipped post-parse scripts re-feed per real context. It is recorded rather than guarded because a guard would be a fallback path for a case no caller produces, which `builder-base-development` forbids. Should a system-context or `_global` interface/block row ever become reachable, this turns an intended error message into a traceback.

**The `shared` probe did not move to `make db`, and the reason is the cleanest available demonstration that steps 1 and 3 address different failures.** After step 1 landed, `examples/xprojParam/shared` — the straight-through parameterized path, one declaration reached from two endpoints — was expected to start failing at `make db` as a same-declaration/two-configurations shape. **It does not.** `make clean && make db && make gen` remain clean and the failure point is unchanged, still at compile with the two failures §5.4 records. **VERIFIED BY EXECUTION.**

The reason is residual 1 above, in the field. Every instance in `shared` binds `PIXEL_WIDTH: 8`, so both sides' resolved packed forms are the identical `tag@0 w4, data@4 w8` and the resolved-identity short-circuit **correctly** skips the junction: there is no layout disagreement to find. What `shared` actually carries is two distinct `Config` **types** at one junction holding equal values — a bindability defect (§1.1), which no packed-form comparison can see and which only step 3's predicate move addresses.

Both halves of that are confirmed by rebinding, and the two rebindings diverge for a third, already-recorded reason. **VERIFIED BY EXECUTION:** rebinding `PIXEL_WIDTH: 16` in the **owning** project's own file does produce the step-1 per-field diagnostic at `make db` (the `_bitWidth 8` vs `16` at field index 1 of `data_t`, transcribed at `examples/xprojParam/README.md`, "`shared` — straight-through parameterized boundary"). Rebinding it in a **downstream** file leaves `make db` clean, because that binding is discarded outright before anything can compare it — the G5.9 sizing defect §5.5 already records as undetectable by this check by construction. So step 1 is not silent on `shared` because it is weak; it is silent because `shared`'s defect is not step 1's defect.

### 7.2 `/work/ws/isp` specifically
Survives. The reason is structural, not luck: the ISP already converged on the sanctioned pattern — ISP-owned literal-width boundary types (`/work/ws/isp/yaml/isp_top.yaml:40-60`, and the file declares **no** `ipParameters`), with each module keeping its own IP-owned port interface. That makes **both** ends of every datapath hop a cross-interface bind — the file says so itself at `isp_top.yaml:50-53`: "each module port keeps its own IP-owned interface type while the connection carries the ISP type, so BOTH endpoints of every inter-module hop differ from the wire and the toolchain emits a thunker at each — two thunkers per connection, by design."

Two ends cross-interface means, per §2's transitivity note, that src≡dst is **already** established transitively on those nine hops today. The ISP datapath is the best-checked part of the design. What is *not* checked today is its nine register-bus dispatches, and the general check finds them compatible.

### 7.3 `builder/base/examples`
- **`ip_test`** survives. Its boundary types are hand-declared to match each variant's expectation and the comment at `examples/ip_test/top/yaml/ip_top.yaml:31-40` documents the intent explicitly ("concrete, non-parameterized interfaces/structs whose field order and bit widths match each connected variant's expectation (variant0/variantSrc0 -> 8-bit, variant1/variantSrc0 -> 70-bit; marker 1 bit)"). Verified: 15/15 compatible. The nearby `plan-register-bus-cross-interface-check.md` gate — "`examples/ip_test/` builds unchanged" — is met.
- **`xif`** survives, but for a weaker reason: all three blocks bind `DATA_WIDTH: 16` (`examples/xif/arch/yaml/xif.yaml:96-108`), which masks the producer/consumer parent-binding divergence of §3.6. If `sink` dropped `DATA_WIDTH`, today's check would compare `dutStreamIf` at the *declared default* against `streamBndrySt`, not at the DUT's bound value. Worth a fixture.
- **`simple_ip`, `debayer`** survive.

### 7.4 Would any legitimate pattern be wrongly rejected?
One class was found, and it is a *false negative* rather than a false positive — which is the safer direction but should be stated: for `inheritContainerParam` children the check evaluates at declared defaults rather than the instantiated configuration (§1.3). Both sides get the same substitution, so no legitimate design is rejected; a genuine mismatch between an inheriting child and a variant-bound sibling would be missed.

> **CORRECTION 2026-08-10 (see §1.3).** The reasoning above holds only when *both* ends inherit. An inheriting child wired to a **variant-bound sibling** IS wrongly rejected once G1 is removed, in both wiring directions — **VERIFIED BY EXECUTION**. So this section's "no legitimate pattern is wrongly rejected" conclusion was not safe as written; it was protected by the gate the plan removes. Step 1 restores it by declining to adjudicate any connection with an inheriting endpoint. The measurement in §7.1 is unaffected: no design in the tree has an inheriting child wired to a variant-bound sibling at a differing width, which is why the blast-radius replay did not surface this.

**No** legitimate pattern was found that a strict layout check wrongly rejects — with one caveat that was properly an architect question, not an engineering one: if the architect answers §8.2 as "names may differ", then today's name check is itself the wrongly-rejecting rule, and structurally identical payloads with different field names (`{r,g,b}` vs `{y,u,v}`) would need to be accepted and thunked.

**That caveat is now the resolved case. RESOLVED 2026-08-10 (§8.2 = (c)):** names may differ. Today's name check *is* the wrongly-rejecting rule and is removed (§1.2.1); `{r,g,b}` against `{y,u,v}` is accepted and thunked. Nothing else in this section changes — the §7.1 measurement is a layout measurement and is unaffected, and removing a rejection cannot turn a passing design into a failing one.

### 7.5 Escape hatch — recommend **none**
**Argument against.** The measured blast radius is zero on every design in the tree. An opt-out would be introduced with no design needing it, which the `builder-base-development` rules forbid ("Do not add compatibility wrappers, optional parameters, fallback paths … unless a current caller requires them"). Worse, the failure this check guards is silent bit truncation inside a generated thunker (§1.1) and silent width coercion in generated SV (§3.5) — the two places where a suppressed diagnostic costs the most. And there is already a first-class, documented, working remedy: the assembler-owned literal boundary plus a thunker per leg (`examples/xprojParam/uniq`, `examples/ip_test`, the whole ISP datapath).

**The honest argument for**, so the architect can weigh it: at the moment a check goes live, a design that has been *running in simulation* may start failing `make db`, and the literal-boundary rewrite is not a one-line change. That is an argument for staging the rollout (warning first, error second) — not for a permanent per-connection suppression. If a hatch is required, make it a **global, time-boxed severity knob** rather than a per-junction annotation: the latter becomes permanent and invisible in the YAML, and turns "compatible" into a per-connection opinion.

## 8. Decisions For The Architect — all eleven RESOLVED 2026-08-10

Every resolved decision below carries its resolution first and its original analysis unchanged beneath it. The options and recommendations are retained deliberately: where the architect chose against the recommendation (8.2, 8.4, 8.7, and 8.8's signedness sub-choice) the rejected argument is the record of what risk was knowingly accepted or what alternative was knowingly declined.

| # | Question | Resolution (2026-08-10) |
| --- | --- | --- |
| 8.1 | Layout-only, or layout *and* bindability? | **(b)** — layout plus a thunker wherever the resolved types differ, **delivered in that order**: layout check first, then the predicate move. |
| 8.2 | Are structurally identical payloads with different field names compatible? | **(c)** — ignore field names entirely; compare widths and offsets positionally only. *Against* the document's recommendation of (a). |
| 8.3 | Move the thunker-insertion predicate from name-difference to config/key-difference? | **RESOLVED-BY-IMPLICATION** of 8.1=(b) — **(b)**, sequenced after the resolution defects. |
| 8.4 | Reject a bind on a protocol with no thunker header? | **(b)** — write the missing thunker headers. *Against* the document's recommendation of "(a) now, (b) on demand".  **Seven**, not six (§1.1 consequence 3). |
| 8.5 | Is enum member-set divergence at equal width in scope? | **(a)** — out of scope. |
| 8.6 | Per-field equality, or same-total-width with a free split? | **(a)** — per-field equality with order preserved; a differing split at equal total width is **not** compatible. |
| 8.7 | Build the C++-compatibility axis at all, given zero currently-eligible junctions? | **(b) — build it.** The zero-eligibility evidence is **rejected**, not the work deferred: it was measured on a partially-parameterized tree. The evidence gate is *retargeted* to `examples/xprojParam`, not dropped. *Against* the document's recommendation of (c)/(a). |
| 8.8 | What is the C++-compatibility predicate — same declaration, or member-sequence identity? | **(b)** — structural member-storage identity, **with matching signedness required**. Option (a) is **vacuous** under the definitional correction (§9.1). Signedness was argued droppable; the architect required it anyway. |
| 8.9 | Where does the selection fact live — pure C++ in the adapter, or a generator-computed fact? | **A generated parameter passed to the thunker from the database:** computed per payload pair in `buildThunkerView` and emitted as one trait specialization per eligible junction. The pure-C++ option is **removed** (§9.1), not merely unchosen. `projectCreate` persistence stays rejected. |
| 8.10 | Automatic when provably safe, or an authored opt-in? | **(a)** — automatic, no authored opt-in, no YAML switch. Matches the recommendation; not separately deliberated (see the block). |
| 8.11 | Collapse the 24 pack/copy/unpack sites into one helper before or after the seven new headers (8.4)? | **RESOLVED-BY-IMPLICATION** of 8.9 — **(a)**, collapse first. The shared payload-copy helper *is* 8.9's consumer, so the collapse is part of implementing 8.9. Ordering constraint against 8.4's seven headers stands. |

**8.1 — Is the target predicate layout-only, or layout *and* bindability?**

> **RESOLVED 2026-08-10: option (b), delivered in that order.** The layout check lands first; the thunker-insertion predicate then moves to resolved-type difference so that the same-key/different-config case (cell 10) is *adapted* rather than left to the C++ compiler. The delivery order is part of the decision, not a scheduling preference: (a) is a standalone deliverable with zero measured blast radius, and it is the only gate the RTL flow will ever have. See "Plan of record" steps 1 and 3.

The goal sentence describes layout, and the architect's refinement assigns bindability to the thunker. `xprojParam` proves layout alone is insufficient to compile: a byte-identical-but-distinct Config passes layout and fails to compile (§1.1) because no thunker was inserted.
- *(a) Layout only.* The check reports layout incompatibility; a layout-compatible-but-non-bindable junction remains a compile error. Simple, ships now, Option A suffices.
- *(b) Layout, plus a thunker wherever the resolved types differ.* The check additionally drives adaptation, so a layout-compatible/type-distinct junction is auto-thunked rather than left to clang. Requires Option B and §8.3.
- **Recommendation: (b), delivered in that order.** Land (a) first — it is small, zero-blast-radius, and covers the RTL flow where nothing else can. But (a) alone leaves cell 10 diagnosed by clang, which is unacceptable for the RTL flow because clang is not in it: in SV the case is *silent* (§3.5). Do not stop at (a).

**8.2 — Are two structurally identical payloads with different field names compatible?**

> **RESOLVED 2026-08-10: option (c), ignore field names entirely.** In the architect's words: *"ignore the names, its the engineers job to make it work, our job is to prevent obvious incompatabilities."* Compare widths and offsets positionally only. This is **against** the recommendation of (a) recorded below, and the recommendation is kept so the accepted risk is legible: a `{r,g,b}`↔`{y,u,v}` transposition will pass, be thunked, and simulate cleanly. The tool's remit is obvious — that is, bit-level — incompatibility.
>
> This resolution **removes existing behaviour**: `processYaml.py:5888-5901` (pre-step-1 line number, code since removed) must be deleted, and designs that fail today on a name mismatch alone will begin to pass. See §1.2.1 for the full consequence, §1.2.2 for the resulting rule with 8.6, and §6.1/§6.2/§6.3 for the positional diagnostics it forces.

The thunker copies by bit position, so field names are provably irrelevant to generated correctness (§1.1). Yet names are the only thing distinguishing "the same payload described twice" from "two different payloads with the same width profile" — `{r:8,g:8,b:8}` against `{y:8,u:8,v:8}` is layout-identical.
- *(a) Error* (behaviour at the time of writing, `processYaml.py:5888-5901`, pre-step-1 line number, code since removed).
- *(b) Warning, then thunk.*
- *(c) Ignore names entirely; compare widths and offsets only.*
- **Recommendation: (a).** A name divergence at a junction is nearly always an authoring error, and the cost of being wrong in the (b)/(c) direction is a semantically-transposed datapath that simulates cleanly. If (a) proves too strict in practice, the escape is to rename a field — cheap and visible. Note that answering (b) or (c) makes today's behaviour a *regression* to be undone, so this needs a decision either way.

**8.3 — Should the thunker-insertion predicate move from name-difference to configuration/key-difference?**

> **RESOLVED-BY-IMPLICATION 2026-08-10: option (b)**, following from 8.1=(b). The predicate moves to resolved `(interfaceKey, Config)` identity, persisted once at db time. **The sequencing constraint stands and is part of the resolution:** it must land *after* the resolution defects of §5.2 and §5.7, because a correct verdict driving a wrongly-resolved payload is worse than today. "Plan of record" step 3, gated on step 2.

Today both the validator (G1, since removed by step 1) and the generator (`getBDCrossInterfaceBinds.annotate`, `processYaml.py:2777-2778`, `:2794-2795`) decide "needs adaptation" by comparing interface **names**, independently and in two places. §1.1 shows the correct criterion is configuration/type identity. Unifying them is what makes cell 10 adaptable rather than merely diagnosable — and it **changes generated code** for junctions that are same-name/different-config, which are un-thunked today.
- *(a) Leave the predicate on names; cell 10 is always a hard error.*
- *(b) Move the predicate to resolved (interfaceKey, Config) identity and persist it once at db time; cell 10 gets a thunker when layouts agree.*
- **Recommendation: (b)**, gated on 8.1=(b). But it must not land before the resolution defects (§5.2, §5.7) — a correct verdict driving a wrongly-resolved payload is worse than today.

**8.4 — Should a cross-interface bind on a protocol with no thunker header be rejected at db time?**

> **RESOLVED 2026-08-10: option (b), write the missing thunker headers.** The architect chose to make the sanctioned de-parameterized boundary pattern available on **every** protocol rather than to reject the unadapted ones at db time. This is **against** the recommendation of "(a) now, (b) on demand" recorded below; (a) is not adopted even as an interim measure, because once every protocol has an adapter the rejection has nothing left to reject.
>
> **Verified follow-on work — seven headers, not six.** The count in the original text was wrong; the list of names was right. Re-counted 2026-08-10 by `find interfaces -name '*thunker*'` and `ls interfaces/` (**VERIFIED BY EXECUTION**, §1.1 consequence 3): six base thunkers exist (`apb`, `axi_read`, `axi_write`, `push_ack`, `rdy_vld`, `req_ack`) plus `lmmi` in pro, against thirteen base protocol directories. The **seven** base protocols still needing a thunker header are:
>
> - `axi4_stream`
> - `external_reg`
> - `memory`
> - `notify_ack`
> - `pop_ack`
> - `raw`
> - `status`
>
> Independent parallel work with no ordering relation to the layout check or the predicate move ("Plan of record"). Not written by this document. `buildThunkerView` (`processYaml.py:2667`) still never checks that a header exists for the protocol it names; once all seven land that check has no failing case, so it is not proposed.

Thunkers exist for 7 of 13 base protocols; `buildThunkerView` never checks (§1.1). Today a bind on `axi4_stream`/`memory`/`status`/`raw`/`pop_ack`/`notify_ack`/`external_reg` is emitted and fails at C++ compile with no arch2code diagnostic.
- *(a) Reject at db time with "protocol X has no adapter; use a protocol changer or match the interfaces."*
- *(b) Write the missing thunker headers.*
- *(c) Leave it.*
- **Recommendation: (a) now, (b) on demand.** (a) is small and turns a link error into an actionable message; (b) is real work and should be driven by a design that needs it. This is genuinely the architect's call because it decides whether the sanctioned de-parameterized boundary pattern is available on all protocols or only on seven.

**8.5 — Is enum member-set divergence at equal width in scope?**

> **RESOLVED 2026-08-10: option (a), out of scope.** Enum member-set divergence at equal width is not a layout question, so it is not this check's business. Recorded in "Deferred / Out of Scope". This matches the recommendation below.

Two enums of the same width with disjoint enumerators are layout-identical and semantically incompatible. No bit-level check can see it.
- *(a) Out of scope — layout only.*
- *(b) In scope as an error.*
- *(c) In scope as a warning.*
- **Recommendation: (a).** It is a different kind of question (value-domain, not layout) and belongs with a types/structures identity check, not here. Raised only because it is the one axis where "compatible definitions … field names and types" could reasonably be read to include it, and the narrowing should be explicit rather than silent.

**8.6 — Must per-field sizes be individually equal, or is a differing field split with the same total width compatible?**

> **RESOLVED 2026-08-10: option (a), per-field equality with order preserved.** A differing field split at the same total width is **NOT** compatible: a field-by-field correspondence is required, so the two flattened sequences must be the same length and agree element-wise on width and offset. Combined with 8.2 this gives the final rule in §1.2.2 — a positional field-by-field comparison of `(width, offset)`, with names printed but not compared. This matches the recommendation below.

"Compatible sizes and order" is not the same word as "identical". One side declaring a 32-bit field where the other declares two 16-bit fields is bit-identical on the wire and would be copied correctly by the positional thunker.
- *(a) Per-field equality with order preserved* — a field-by-field correspondence is required.
- *(b) Same total width and consistent ordering* — the field split may differ.
- **Recommendation: (a).** "Fields … of compatible sizes and order" implies a field-by-field correspondence, and (b) would make the check unable to distinguish a deliberate re-split from an accidental one. Raised because the architect's wording admits both readings.

**8.7 — Is the C++-compatibility axis worth building at all?**

> **RESOLVED 2026-08-10: option (b), build the axis — with `examples/xprojParam` as the proving ground.** This is **against** the recommendation of (c)-in-practice-(a) recorded below, and the reason matters: **the architect rejected the *evidence*, not the work.** In the architect's words, the zero-eligibility count is an artefact of the tree it was measured on — *"that is because the isp, is in partial state and does not have correctly parameterized isp. Focus effort on example fixture."* §9.5's measurement is taken largely on `/work/ws/isp`, so it does not characterise the intended end state and cannot carry a "do not build" verdict.
>
> **The evidence gate of option (c) is retargeted, not dropped.** The eligibility measurement, and any cost measurement, are re-run on `builder/base/examples/xprojParam` once it carries correctly-parameterized cases — not on the ISP tree. §9.5's table is retained as a factual record of what is emitted today and is relabelled accordingly; it is no longer a justification.
>
> "Plan of record" step 5 is therefore **approved**, with its ordering constraints unchanged: not before step 1, ~~pointless before step 3~~.
>
> **Ordering correction 2026-08-11, following the re-measurement this resolution ordered.** The retargeted census has been taken and counts **17 eligible payload pairs among the 41 emitted in `examples/`** (§9.5). "Pointless before step 3" is therefore **withdrawn**: it assumed cell 10 was step 5's only eligible population, which was itself a consequence of the struck ISP measurement. The hard constraint — not before step 1 — stands and is satisfied. See "Plan of record", step 5.

§9.5 measures **zero** eligible junctions among the ~43 thunkers emitted in the tree, and shows the five eligible ones are all low-traffic register-bus adapters. The sanctioned literal-boundary-vs-parameterized pattern is ineligible **by construction** (§9.2). The pack/unpack cost as a fraction of simulation time is **unquantified**; the surrounding per-transaction cost is ~4 SystemC context switches and 4 delta-cycle notifications, which a code-reading bound suggests dominate. *(Both sentences stand as measurements; neither survives as an argument — see the resolution above.)*

- *(a) Do not build it.* CLAUDE.md forbids speculative flexibility; nothing in the tree needs it.
- *(b) Build it now.*
- *(c) Defer behind an evidence gate:* land Plan-of-record step 3, re-run the eligibility measurement, and only then measure the cost delta on one real simulation (§9.5).
- **Recommendation: (c), which in practice is (a) until the measurement says otherwise.** If the motivation is genuinely simulation speed, the field-wise assignment adapter (§9.5) is the change that would deliver it and this one is not; that trade should be made explicitly rather than by default.

**8.8 — What is the C++-compatibility predicate?**

> **RESOLVED 2026-08-10: option (b), structural member-storage identity — with matching signedness required.** The predicate is a structural comparison of the two declarations' member storage sequences: **equal member count at every nesting level**; corresponding members (taken **positionally**; names are never compared) have **identical underlying storage width** and **equal statically-known array extents**; nested structs compared **recursively with nesting boundaries respected, never flattened**; and **matching signedness required**. This is §9.3's "Definition adopted", now adopted in fact.
>
> **Option (a) is not merely unchosen — it is vacuous.** Under the definitional correction (§9.1), a thunked junction always has two different structure declarations, so "same `structureKey` on both sides" can never fire at a junction the predicate is asked about. §9.3's "cheap sufficient special case" is retained for its reasoning — declaration-level storage is what makes conditions 1-3 decidable at all — but not as a case that occurs.
>
> **The signedness sub-choice went against an argument to drop it, and the record should be plain about that.** It was pointed out that signedness could be dropped: pack/unpack reinterprets sign exactly as a direct copy would, so an `int8_t`/`uint8_t` pair at equal width is **observationally equivalent either way**, and requiring signedness only costs the fast path on such pairs. The architect chose to require matching signedness regardless. This is **strictly safe** — a false "not compatible" verdict costs only a fallback to the existing pack/unpack path, never a wrong copy (§9.6). The choice is between two framings of the predicate:
>
> - *"the definitions are identical"* — signedness required. **CHOSEN.**
> - *"the fast path is observationally equivalent to the slow path"* — the weaker predicate, which would admit the signedness-differing pair. Not chosen.
>
> **Option (c), flattened comparison, remains rejected as unsound**, on §9.3's existing counterexample: nested `sizeof == 12` against flattened `sizeof == 8`, because a nested struct's trailing padding is preserved as a member and elided when inlined. **VERIFIED BY EXECUTION** (§9.3).

§9.3 rules out "trivially copyable + equal `sizeof`" as unsound — **VERIFIED BY EXECUTION**, `{uint8_t;uint32_t}` and `{uint32_t;uint8_t}` pass it and scramble.

- *(a) Same structure declaration only* (same `structureKey`), possibly at two Configs. Decidable by one key comparison; needs no generator change (§9.7). **Covers the architect's stated example and nothing else** — none of the five currently-eligible junctions in the tree are same-declaration. *(Superseded: vacuous under §9.1, and the reading of the architect's example that motivated it was wrong — see §9.5.)*
- *(b) Structural member-storage identity* per §9.3 — equal member counts at each nesting level, identical storage including signedness, equal array extents, nesting boundaries respected. Covers (a) as a special case plus the `apb` register-bus pairs. Requires the fact to be computed in `buildThunkerView`.
- *(c) Flattened member-storage identity.* **Rejected outright**: §9.3's nested-padding counterexample (`sizeof 12` vs `sizeof 8`) makes it unsound.
- **Recommendation: (b) if 8.7 is answered "build".** (a) is simpler but delivers nothing measurable today.

**8.9 — Where does the selection fact live?**

> **RESOLVED 2026-08-10: a generated parameter passed to the thunker from the database, delivered as an emitted trait specialization.** In the architect's words: *"we need to pass a generated parameter to the thunker from the database."*
>
> Concretely: the boolean is computed **per payload pair in `buildThunkerView`** (`pysrc/processYaml.py:2667`), whose payload rows already carry `structureType`, `structure`, `structureKey` and `configSelection` (`processYaml.py:2699-2705`) and which already establishes the parent-to-child payload pairing. The generator emits trait specializations which a shared payload-copy helper consults — the spelling recorded in §9.7, emitted by `sc_declare_payload_copy_traits()` (`pysrc/intf_gen_utils.py:943-956`) and formatted in `_thunker_direct_copy_traits()` (`:879-896`).
>
> **Three corrections to this record, 2026-08-11, found while implementing it. None changes the resolution; all three change what "one trait specialization per eligible junction" means.**
>
> - ~~The spelling is always `template<> struct ...`.~~ **It is not always legal.** Where a payload is spelled on a parameterizable container's own `Config` **template parameter** — a parameterizable payload with no `Config` selection of its own — there is no concrete type to name, so an explicit (`template<>`) specialization cannot be written. A **partial** specialization deducing `Config` is required instead: `template<typename Config> struct a2c_payload_direct_copy<...<Config>, ...> : std::true_type {};`. This is not a corner case: it is fixture case (a), `wrapEqSt<Config>` ↔ `leafEqSt<xpCppLeafEqV0Config>`, the **only** eligible pair in `xprojParam`. The choice between the two heads is made by `_payload_is_config_dependent()` (`pysrc/intf_gen_utils.py:862-867`).
> - ~~One specialization per eligible pair.~~ **Two are required.** An adapter copies parent to child *and* child to parent, so both orderings must be declared. This is sound because the storage correspondence the predicate establishes is **symmetric**: if the parent's declaration may be copied whole onto the child's, the converse holds by the same equality.
> - **Deduplication is required, and was not anticipated here.** One container can hold two adapters bridging the **same** pair of payload types — the two identical `apb` adapters in `ip_top` are exactly that — and a C++ specialization may be declared only once. `sc_declare_payload_copy_traits()` therefore emits each distinct specialization at most once per rendered scope.
>
> **The pure-C++ option is removed, not merely unchosen.** Under the definitional correction the two sides are always different C++ types, so the predicate is **not decidable in C++**: there is no reflection with which to compare the member sequences of two unrelated types. §9.7's first candidate home therefore has no viable form. See §9.1 and §9.7.
>
> Two alternatives were considered and rejected:
> - **An extra template parameter on each thunker class.** Rejected: it would change all **seven** existing class signatures (six base plus `lmmi` in pro) and all **seven** new ones from 8.4=(b). The trait specialization leaves every signature untouched.
> - **A constructor argument.** Rejected: it makes the selection a runtime branch and gives up the compile-time selection, which is the entire point of the fast path.
>
> **`projectCreate` persistence remains rejected**, unchanged: no db-time consumer, no diagnostic, no acceptance gate.

Determined by 8.8. 8.8=(a) ⟹ pure C++ `if constexpr` in a shared `copyPayload` helper, **no `projectCreate`, `projectOpen` or template change**. 8.8=(b) ⟹ C++ cannot decide it, so the boolean is computed per payload pair in `buildThunkerView` (`processYaml.py:2667`, whose payload rows already carry `structureKey` and `configSelection`) and consumed by `sc_declare_payload_copy_traits()` (`pysrc/intf_gen_utils.py:943-956`) as emitted trait specializations. *(8.8 resolved as (b), and §9.1 removes the (a) branch outright.)*

- `projectCreate` persistence is **rejected** in both cases: no db-time consumer exists, and the fact gates no acceptance and produces no diagnostic.
- Named tension for the record: "C++-compatible" is a language-specific question living in a language-neutral view. It is phrased over storage descriptors, not C++ spellings; the precedent is `platformDataType`, ~~already persisted at `processYaml.py:1150`~~ **derived in the `projectOpen` view `getContextData()` (`processYaml.py:1252`) and never persisted — corrected 2026-08-11, see §9.2 and §9.7**.

**8.10 — Automatic when provably safe, or an authored opt-in?**

> **RESOLVED 2026-08-10: option (a), automatic — no authored opt-in, no YAML switch, no flag.** This was the document's own recommendation and **nothing in the architect's answers contradicts it**; it is marked resolved on that basis, and the basis is stated so nobody reads it as a separately deliberated choice. It is also settled by construction: 8.9 selects a **generator-driven** trait specialization emitted per eligible junction, so there is no place for an author to intervene and nothing for an author to decide.

The architect's "allow the option of straight memcopy" admits both readings. *(Read as "make the option available to the generator" — §9.7, and confirmed directionally by the architect's note on the memcpy phrasing recorded in §9.4.)*

- *(a) Automatic* whenever the predicate holds; no user-visible control of any kind.
- *(b) Authored opt-in* per connection or per project.
- **Recommendation: (a).** The selection is semantics-preserving whenever it fires, so there is nothing for an author to decide; a per-junction annotation becomes permanent and invisible in the YAML (the same objection §7.5 raises against escape hatches); and CLAUDE.md forbids an option with no concrete current call site. **No `project.yaml` switch and no per-connection annotation is proposed.**

**8.11 — Collapse the 24 pack/copy/unpack sites into one helper before or after 8.4's seven headers?**

> **RESOLVED-BY-IMPLICATION 2026-08-10: option (a), collapse first.** Not separately decided. 8.9 selects *a shared payload-copy helper consulting an emitted trait* as the mechanism, and that helper is what the three-line sequences must become in order for the trait to have a consumer. So the 24 base (30 including pro) `pack`/`copy_packed_bits`/`unpack` sequences collapse into calls to that helper **as part of implementing 8.9**, not as an independent simplification exercise. It is "Plan of record" step 5, not a separate item.
>
> **The ordering constraint relative to 8.4's seven new headers stands and is part of the resolution:** collapse first, so the seven new headers are written against the helper rather than adding roughly 24 more three-line sites to retrofit.

**It is a real ordering constraint, not a preference.** **VERIFIED BY EXECUTION:** there were **24** `copy_packed_bits` call sites across the six base thunker headers and **6** more in `builder/pro/interfaces/lmmi` — 30. 8.4=(b) adds roughly 24 more. **All 30 have since been collapsed onto `copyPayload` by step 5**, and no `copy_packed_bits` call site remains in any thunker header, so the seven new headers are now written against the helper as this resolution requires.

- *(a) Collapse first,* then write the seven headers against `copyPayload(out, in)`.
- *(b) Write the seven headers first,* then retrofit ~54 sites.
- **Recommendation: (a), and it stands independently of 8.7.** Replacing thirty three-line sequences with thirty one-liners is a simplification on its own terms, and it is the only change that makes any future direct-copy path a single-file edit rather than a fifty-four-site one.

## 9. The C++ Definition Compatibility Axis

New requirement, 2026-08-10, verbatim:

> "The pack/unpack process support bit compatible conversion. When this is between parameterized variants this can get a bit more complicated. We want to also add a check for c++ compatible conversions. For example two parameterized structs may actually be c++ compatible. We should have a separate check for the c++ definitions are actually compatible and allow the option of straight memcopy instead of bit pack/unpack while we are visiting all this code."

Two architect corrections of 2026-08-10 govern the whole of this section and are applied throughout it. They are stated here once, before the analysis they reshape.

**Correction 1 — definitional, and it reshapes the predicate.** Verbatim:

> "By definition if we need a thunker they are different structure definitions - even if the definition is identical."

A thunked junction therefore **always** has two different structure declarations. Two consequences run through everything below and are worked out in §9.1: the "same `structureKey` on both sides" special case (§9.3, and 8.8 option (a)) is **vacuous** for thunked junctions, and — because the two sides are always different C++ types — the predicate is **not decidable in C++**, which removes the pure-C++ implementation option from §9.7 entirely.

**Correction 2 — the evidence base.** Verbatim:

> "that is because the isp, is in partial state and does not have correctly parameterized isp. Focus effort on example fixture."

§9.5's eligibility measurement is taken largely on `/work/ws/isp`, which does not have a correctly parameterized ISP top. Its zero-eligibility count is **struck as a justification** (§8.7); the table is kept as a factual record of what is emitted today and relabelled as non-representative. The proving ground is `builder/base/examples/xprojParam` (§9.5).

The architect also stated that the memcpy phrasing in the requirement below was **directional** — the requirement is for a fast direct-copy path, not literally `std::memcpy`. §9.4's conclusion that `std::bit_cast` is the defensible mechanism therefore **stands, and is consistent with the requirement** rather than a departure from it.

This section adds an axis to the specification; it does not modify §§1-7. Three axes now exist and must not be conflated:

| # | Axis | Decides | Owner | Status |
| --- | --- | --- | --- | --- |
| 1 | **SV bit-layout compatibility** — positional per-field `(width, offset)` | accept / reject, at every junction | `projectCreate.validatePorts` | specified (§1.2.2) |
| 2 | **C++ definition compatibility** — emitted member storage sequence | *which adapter implementation*, at an already-accepted junction | `buildThunkerView` → emitted trait (§8.9, §9.7) | specified (§9.3 as amended, §8.7-8.11) |
| 3 | **Bindability** — C++ type identity incl. `Config` | whether an adapter is needed at all | the thunker (8.1) | resolved |

**Axis 2 never rejects anything.** It is a selector on the adaptation step, downstream of axis 1 and downstream of the axis-3 decision to insert an adapter at all.

### 9.1 The two axes are not ordered by strength — and the obvious example is unreachable

**The definitional correction, applied first, because it removes two options the rest of this section was written around.**

> "By definition if we need a thunker they are different structure definitions - even if the definition is identical."

This is a definition, not an observation, and it settles two things:

1. **A thunked junction always has two different structure declarations**, whatever the relation between their contents. "Same declaration on both sides" is therefore **not a case the axis-2 predicate ever sees**. It is not merely rare; it is excluded by the definition of the junctions the predicate is asked about. §9.3's "cheap sufficient special case" and 8.8 option (a) are **vacuous** — see §9.3, where the passage is kept rather than deleted because the reasoning it contains (storage is a *declaration*-level fact, which is what makes conditions 1-3 decidable at all) is precisely what justifies the general predicate.
2. **The predicate is not decidable in C++.** Because the two sides are always different C++ types, deciding compatibility means comparing the member sequences of two *unrelated* class types. C++ has no reflection with which to do that, and no `if constexpr` trait can substitute for it: `std::is_same_v` is false by construction, `sizeof` equality is proven unsound in §9.3, and a same-class-template deduction has nothing to deduce across unrelated templates. **This removes the "pure C++ helper, no generator change" option from §9.7 entirely** — it is not a simpler alternative that lost on merit, it has no viable form. The fact must be supplied constructively by the generator, which is what 8.9 resolves.

Everything below stands as written except where these two points are applied inline.

The requirement's framing was that layout-identical payloads can be C++-incompatible, and that C++-identical payloads can span different `Config` arguments. Both halves are true, but the first needs a correction and the second is stronger than stated.

- **Layout-compatible ⇏ C++-compatible: TRUE, and it is the dominant real case** (§9.2, §9.5). But *not* by the "three 8-bit fields against one 24-bit field" example: under **8.6=(a)** those two flattened sequences have different lengths and the junction is **rejected on axis 1** before axis 2 is consulted (§1.2.2). That example is unreachable. The reachable forms are (a) a literal-width side against a parameterized side, and (b) equal widths with differing signedness. **VERIFIED BY CODE READING** (`templates/systemc/includes.py:118-146`) **and BY EXECUTION** (§9.2).
- **C++-compatible ⇏ layout-compatible: TRUE and unconditional.** A parameterizable type is emitted as a container sized from `maxBitwidth`, which is a *declaration*-level fact, not a variant-level one (`templates/systemc/includes.py:121-136`). So `video_rgb_t<CfgA>` and `video_rgb_t<CfgB>` have identical member declarations and identical `sizeof` **for every pair of Configs**, including ones whose resolved bit widths differ by a factor of two. **VERIFIED BY EXECUTION.** Axis 2 is therefore *blind* to exactly the divergence axis 1 exists to catch, which is the strongest possible argument for keeping the two checks separate and for never letting axis 2 substitute for axis 1.

  **Correction under the definitional rule: the pair used to illustrate this is not a thunked junction.** `video_rgb_t<CfgA>` against `video_rgb_t<CfgB>` is *one* declaration at two Configs, which the definitional correction excludes from the set of junctions axis 2 ever sees. **The property it demonstrates survives intact, and reaches further than the illustration does**, because `maxBitwidth`-derived storage is declaration-level: *two different parameterizable declarations* likewise each emit `uint64_t`/`int64_t` (or `uint64_t word[ceil(maxBitwidth/64)]`) irrespective of any variant's resolved width (`templates/systemc/includes.py:118-137`, **VERIFIED BY CODE READING**). Two distinct parameterized declarations whose members correspond can therefore be C++-compatible while resolving to different bit widths — which is both the reachable form of this bullet and, per §9.5, the class the requirement actually names.

Neither axis implies the other in either direction. They are orthogonal.

### 9.2 How the C++ structures are actually emitted

A member's C++ type is decided in exactly two places, and it is **not** the declared `varType` spelling and **not** the resolved bit width:

1. `templates/systemc/structures.py::declareVars` (`:482-495`) emits `<cppTypeName(vardata)> <variable>[<arraySize>];`. `cppTypeName` (`:183-195`) returns the *declared type name* — `isp_pixel_t`, `pixel_t<Config>`, or a sub-struct name. It selects no storage of its own.
2. The storage behind that name is decided by `templates/systemc/includes.py::includeTypes` (`:115-146`), in four arms:

| Type row | Emitted C++ | Storage decided by |
| --- | --- | --- |
| non-parameterizable, `typeArraySize == 1` | `typedef <platformDataType> T;` | **integer-size bucket** of the *resolved* width, plus signedness |
| non-parameterizable, `typeArraySize > 1` | `struct T { <platformDataType> word[N]; };` | same bucket, `N` from resolved width |
| parameterizable, `maxBitwidth <= 64` | `template<typename Config> using T = uint64_t;` (`int64_t` if signed) | **`maxBitwidth`, i.e. declaration-level — never the variant width** |
| parameterizable, `maxBitwidth > 64` | `template<typename Config> struct T { uint64_t word[ceil(maxBitwidth/64)]; };` | same |

`platformDataType` is derived from `resolveTypeWidth(value)` and `isSigned` through the `dataTypeMapping` buckets (1/8→`uint8_t`, 16→`uint16_t`, 32→`uint32_t`, 64→`uint64_t`, above→`uint64_t word[]`).

> ~~It is derived once at db time in `pysrc/processYaml.py:1131-1152`. It is already a C++ spelling persisted in the database — relevant to §9.7's ownership question.~~

**CORRECTION 2026-08-11 — `platformDataType` is NOT persisted, and the ownership argument that rested on it does not stand.** It is computed at render time in `projectOpen.getContextData()` (`processYaml.py:1234-1254`) and mutated into `prj.data['types']` in place (`:1252-1253`). The `types` table carries no such column: its columns are `type`, `typeKey`, `desc`, `isSigned`, `maxBitwidth`, `isParameterizable`, `width`, `widthKey`, `widthLog2`, `widthLog2Key`, `widthLog2minus1`, `widthLog2minus1Key`, `_context` (`config/schema.yaml:94-108`). **VERIFIED BY EXECUTION.** So `platformDataType` is not a precedent for a C-family spelling *persisted at db time*; it is a precedent for one *derived in a `projectOpen` view*, which is a weaker claim and is the one §9.7 must make. The consequence is stated at §9.7.

**Four copies of the bucket table now exist, and one has already diverged. VERIFIED BY EXECUTION.** `pysrc/processYaml.py::storageBuckets` (`:439-446`), `pysrc/systemcGen.py::dataTypeMappings` (`:13-20`) and `pysrc/systemVerilogGenerator.py::dataTypeMappings` (`:18-25`) all end at `maxSize` **1024**, while `templates/systemc/structures.py::dataTypeMappings` (`:4-11`) ends at `maxSize` **4096**. The fourth drives `_packedSt` selection in `convertToType()` (`structures.py:101-120`) rather than member storage, so no live bug follows from the divergence — but it is direct evidence that this table is not kept in step. See §9.3a for the single-source route that was available and not taken.

Array extents are the one variant-dependent part of a member declaration: `cppArraySize` (`structures.py:164-169`) emits `Config::<CONST>` for a parameterizable `arraySize`. **VERIFIED BY CODE READING.**

Real emitted output, the ISP datapath pair. Assembler-owned literal boundary, `/work/ws/isp/model/isp_topIncludes.cppm:51`, `:91-95`, `:250-252`, `:494-497`:

```cpp
typedef uint8_t isp_pixel_t; // [8] ISP per-color pixel data. LITERAL, not parameterized

struct isp_rgb_pixel_t {
    isp_pixel_t r; //
    isp_pixel_t g; //
    isp_pixel_t b; //
    ...
struct isp_rgb_pixels_per_clock_t {
    isp_rgb_pixel_t pixels[4]; //
    ...
struct isp_video_rgb_t {
    video_frame_t frame; //
    isp_rgb_pixels_per_clock_t data; //
```

IP-owned parameterized counterpart, `/work/ws/isp/debayer/model/debayerIncludes.cppm:32`, `:74-78`, `:425-428`:

```cpp
template<typename Config> using pixel_t = uint64_t; // [max:16] Per color pixel data

template<typename Config>
struct rgb_pixel_t {
    pixel_t<Config> r; //
    pixel_t<Config> g; //
    pixel_t<Config> b; //
    ...
template<typename Config>
struct video_rgb_t {
    video_frame_t frame; //
    rgb_pixels_per_clock_t<Config> data; //
```

§7.1 measured these two as **layout-identical, 99 bits both ends**. Their C++ definitions are not remotely compatible: `sizeof(isp_video_rgb_t) == 15`, `sizeof(video_rgb_t<Config>) == 104`. **VERIFIED BY EXECUTION** (`g++ 13.1 -std=c++20`, static_asserts over a faithful transcription of the emitted shapes above; the transcription omits only member functions, which cannot affect layout).

**Correction 2026-08-11 — the fourth arm is a second and larger route to correspondence, and it is not confined to parameterized-against-parameterized pairs.** The pair above is representative of the `maxBitwidth <= 64` case only, where the parameterizable side collapses to a bare `uint64_t`/`int64_t` and can meet a literal side only in the 64-bit bucket. Once a parameterizable type's `maxBitwidth` **exceeds 64** the fourth arm emits `struct T { uint64_t word[ceil(maxBitwidth/64)]; }` (`templates/systemc/includes.py::includeTypes`, `:133-137`), and the non-parameterizable `typeArraySize > 1` arm emits `struct T { <platformDataType> word[N]; }` (`:143-146`). **Those two are the same storage whenever the two `N` agree** — a literal side and a parameterizable side then correspond, at any resolved width. **VERIFIED BY CODE READING** (`templates/systemc/includes.py:115-146`).

Concrete, from generated output — **VERIFIED BY EXECUTION**. `ip_test`'s `ipDataT` is `template<typename Config> struct ipDataT { uint64_t word[ 2 ]; }` at `[max:128]` (`examples/ip_test/ip/model/ipIncludes.cppm:33`), i.e. `uint64_t word[2]` **at every variant**, and the assembler's literal 70-bit boundary type is `struct srcOut1BoundaryT { uint64_t word[ 2 ]; }` at `[70]` (`examples/ip_test/top/model/ip_topIncludes.cppm:39`). The two structs wrapping them each carry that member plus a 1-bit `uint8_t` marker, so `srcOut1BoundarySt` corresponds to the parameterizable `srcOut1St<…>` and `ipDataSt<…>` and, since `data70T` is itself a literal `uint64_t word[2]` at `[70]`, to `data70St` as well — while their 8-bit siblings (`srcOut0BoundaryT` → `uint8_t`, against the same `ipDataT` `word[2]`) do not. This is what §9.5's re-measured census counts, and it is why the §9.5 point-2 claim that the two "can only coincide if every field of the literal side is itself 64 bits wide" is corrected there.

### 9.3 When two emitted structures are genuinely C++-compatible

**Are the emitted structs trivially copyable and standard-layout? Yes — verified, not assumed.**

- `structures.py:386-388` emits a **user-provided default constructor** (`<Name>() {}`, or a `memset` form in `fw` mode). A user-provided *default* constructor defeats trivial default construction but **not** trivial copyability. **VERIFIED BY EXECUTION:** `is_trivially_copyable_v` is `true` and `is_trivially_default_constructible_v` is `false` for the emitted shape.
- No copy/move constructor, copy/move assignment operator, or destructor is emitted anywhere in `structures.py`; the `codeMapping` feature set (`:311-350`) is `equal`, `sc_trace`, `operatorStream`, `prtFmt`, `tracker`, `getSet`, `fw_pack`, `fw_unpack`, `registerFeatures`, `sc_pack`, `sc_unpack` and three `explicit` converting constructors. None is a special member function that suppresses triviality. **VERIFIED BY CODE READING.**
- Standard layout: no base classes, no virtuals, no access specifiers emitted (so all members are public), all members declared in the same class. **VERIFIED BY EXECUTION.**
- **No non-trivial member type is reachable.** `declareVars` can emit only a `platformDataType` typedef, a `uint64_t word[N]` struct, an enum, or a nested generated struct — recursively the same set. `sc_dt` types, `std::array`, and `std::string` appear only in *member function signatures* (`sc_pack`, `prt`), never as data members. **VERIFIED BY CODE READING** (`structures.py:482-495`) and corroborated across every `*Includes.cppm` in `/work/ws/isp`.

**`sizeof` equality is necessary and nowhere near sufficient.** **VERIFIED BY EXECUTION:** `struct X { uint8_t a; uint32_t b; }` and `struct Y { uint32_t a; uint8_t b; }` have equal `sizeof`, both are trivially copyable, and `std::bit_cast<Y>(X{})` compiles — and scrambles the values. Any predicate of the form "trivially copyable + equal `sizeof`" is unsound and must not be adopted.

**Flattening is also unsound on this axis, unlike on the bit axis.** **VERIFIED BY EXECUTION:** `struct N { uint32_t a; uint8_t b; }` nested as `struct W { N n; uint8_t c; }` has `sizeof == 12`, while the flattened `struct F { uint32_t a; uint8_t b; uint8_t c; }` has `sizeof == 8`. A nested struct's *trailing padding* is preserved when it is a member and elided when its members are inlined. The C++ axis must therefore compare **structurally, respecting nesting boundaries**, where the bit axis compares the flattened sequence.

**Definition adopted (proposed).** Two payload sides are **C++-compatible** iff their emitted member sequences are *declaration-identical*, defined recursively:

1. equal member count at every nesting level;
2. corresponding members (positionally — names are **not** compared, §9.6) have identical **storage**, where storage is `platformDataType`+`typeArraySize` for a non-parameterizable type, the `maxBitwidth`-derived container for a parameterizable type, the enum's underlying type for an enum, and recursive declaration-identity for a nested struct. Type *names* are irrelevant; two distinct typedefs of `uint32_t` are the same storage;
3. corresponding array members have equal, statically-known extents;
4. `sizeof` equality follows from 1-3 and is asserted, not assumed.

Padding and alignment need no separate rule: identical member sequences on one ABI produce identical padding. Signedness *is* part of storage, so an `int8_t` field against a `uint8_t` field at the same width and offset is layout-compatible and **not** C++-compatible — correctly, since a direct copy would reinterpret the sign bit.

**The cheap sufficient special case — VACUOUS for thunked junctions, and retained for its reasoning.** If both sides resolve to the **same structure declaration** (same `structureKey`), conditions 1-3 hold automatically — every member's storage is declaration-level, and the array-extent condition is guaranteed by axis 1 having already established equality of the resolved `(width, offset)` sequences (a differing parameterized extent shows up as a differing flattened sequence).

**Under the definitional correction this case can never fire.** "By definition if we need a thunker they are different structure definitions - even if the definition is identical" (§9.1): a thunked junction always has two different declarations, so `structureKey` equality is not a shortcut that is merely uncommon — it is unreachable at every junction the predicate is asked about. It is not the whole predicate, and it is not part of the predicate. 8.8 option (a) is vacuous for the same reason (§8.8).

**The passage is kept rather than deleted because the reasoning in it is what justifies the general predicate.** The observation that every member's storage is a *declaration*-level fact — `platformDataType` + `typeArraySize` for a non-parameterizable type, the `maxBitwidth`-derived container for a parameterizable one (§9.2) — is exactly why conditions 1-3 are decidable *at all*, and therefore why two **different** declarations can be compared member-for-member without reference to either side's variant. Remove the same-declaration shortcut; keep the reason it would have worked. It was also mis-read as "the architect's *two parameterized structs may actually be c++ compatible* case" — that reading is corrected in §9.5.

### 9.3a Semantic decisions taken while implementing the predicate — decisions of record, 2026-08-11

§9.3's four conditions leave three member kinds unsettled. Each was decided during step 5, each is implemented in `projectOpen.structureStorageSignature()` (`processYaml.py:1083-1130`), and each is recorded here rather than in the implementation because each is a specification choice and not a coding detail.

- **`Reserved` padding fields take the storage the generator EMITS, not the storage it appears to intend.** A `Reserved` field's C++ storage is chosen in `pysrc/systemcGen.py` (`:136-144`), **not** in `templates/systemc/includes.py::includeTypes`: it is the bucket of `align`, it is **always unsigned**, and it is **never a word array**, because that arm selects only `myType['unsignedType']` and ignores the bucket's `arrayElementSize`. The predicate mirrors that emitted behaviour exactly — `('int', storageBits, False, 1)` — rather than the behaviour the bucket table appears to intend. This is the only defensible choice: the predicate is sound only insofar as it agrees with the emitter, and disagreeing with it "correctly" would produce a wrong verdict and a scrambling copy.

  **The above-64-bit case is a suspected latent generator defect, and it was deliberately not touched.** A `Reserved` field wider than 64 bits selects the final bucket's `uint64_t` spelling but emits it as a **scalar**, so the emitted member cannot hold the field. No example in the tree declares one. Fixing it is a generator change with its own blast radius, outside step 5's scope; it is listed in "Deferred / Out of Scope".

- **Two enumeration members count as identical storage only when they are the same declaration.** An unscoped enumeration's underlying type is implementation-defined, so nothing about two independently declared enums — not equal width, not equal enumerator sets — establishes that they occupy the same storage. The descriptor is therefore `('enum', typeKey)`, which compares equal only on declaration identity. **This is not vacuous**, and the definitional correction of §9.1 does not make it so: §9.1 says the two *structure* declarations at a thunked junction always differ, not that every member type differs. A single enum declaration reached from both sides through `include:` is legitimate and reachable, and it compares equal.

- **A parameterizable array extent makes the pair ineligible.** `structureStorageSignature()` returns `None` on such a member (`processYaml.py:1100-1104`), and `None` refuses every comparison. The reason is the one §9.2 already records: `cppArraySize` emits `Config::<CONST>` for a parameterizable `arraySize` (`templates/systemc/structures.py:164-169`), so the extent is a property of the **instantiation**, not of the **declaration**. §9.3 condition 3 requires *statically-known* extents, and a `Config::` reference is not one at the declaration level the rest of the predicate works at.

**Open item — the bucket table was duplicated where it could have been single-sourced.** `storageBuckets` (`processYaml.py:439-446`) is a fourth copy of a table that already existed three times (§9.2), and the justification recorded in its own comment — that the per-language `dataTypeMapping` tables are the same boundaries plus a spelling — does not by itself establish that a fourth copy was necessary. **It does not survive review:** `getContextData()` is itself a `projectOpen` method (`processYaml.py:1175`), and its bucket-selection loop (`:1239-1248`) is arithmetically identical to `storageBucket()` (`:1043-1062`), including the word-count rounding. Inverting the dependency — having `getContextData()` call `self.storageBucket()` and consult the per-language table for **spelling only** — would remove the duplication for the two widest arms by construction. That route was available and was not taken. Recorded as an open item, not a resolution: as things stand the drift risk is held off by `unittest/test_payload_direct_copy.py::test_storage_descriptor_matches_emitted_declaration` alone, which pins the descriptor against the emitted declaration but does not prevent a fifth copy appearing.

### 9.4 Is a straight memory copy valid, and under what conditions?

**The requirement's "memcpy" was directional (architect, 2026-08-10).** What is asked for is a **fast direct-copy path**, not literally `std::memcpy`. The conclusion below — that `std::bit_cast` is the defensible mechanism — is therefore **consistent with the requirement rather than a departure from it**, and the analysis of `memcpy`'s standing is retained as the reason the mechanism is spelled the way it is, not as a disagreement with the request.

Stated without softening and without overstating.

- **`std::memcpy` between two distinct struct types is not blessed by the standard.** [basic.types.general] guarantees value preservation for a byte copy between objects of **the same** trivially copyable type. Copying the object representation of one type into a *different* type yields an unspecified value. In practice it works on every toolchain this project supports, but it is type-punning and should not be written as if it were defined.
- **`std::bit_cast` is the defensible mechanism and is already available.** The project builds with `-std=c++23` (`common/systemc/Makefile:18`), so `<bit>` is present. `std::bit_cast<To>(from)` is constrained on `sizeof(To) == sizeof(From)` and both types trivially copyable — both compiler-enforced — and its result is specified as the value whose object representation is `from`'s bytes, with only padding bits left unspecified. It introduces no aliasing violation. **VERIFIED BY EXECUTION:** `bit_cast` between the two `Config` instantiations of the emitted `video_rgb_t` shape compiles; between `{uint8_t r,g,b}` and `{uint32_t rgb}` it is **rejected** by the compiler on the size constraint.
- **When the two sides are the same C++ type, no punning arises at all**: `outVal = inVal` is an ordinary trivially-copyable assignment, fully defined, and strictly better than either alternative. Any design here must special-case identity first.

  > ~~**Under the definitional correction this cannot arise at a thunked junction** (§9.1): the two sides are always different declarations, hence always different C++ types, so `std::is_same_v<To, From>` is false by construction on every payload pair the helper is given. The identity arm is recorded as the correct answer *if* the two sides are ever the same type; it is not a case the payload-copy helper needs to serve, and it must not be relied on to carry any junction.~~

  **CORRECTION 2026-08-11, found while implementing step 5: the `std::is_same_v<To, From>` arm is NOT dead, and it fires today.** The struck reading generalised the definitional correction from *payload pairs* to *every value an adapter copies*, and an adapter copies more than its payload pairs. `axi_write`'s **response phase** copies `axiWriteRespSt` onto `axiWriteRespSt` — see `axi_write_port_thunker.h:166-169` and `:204-207`, where `respIn` and `respOut` are both declared `axiWriteRespSt`. That struct is a hard-coded, non-parameterized envelope declared on both sides of the adapter rather than a view payload, so identity holds by construction there. **VERIFIED BY CODE READING.** The narrower claim survives untouched and is the one §9.1 actually licenses: **no *view payload pair* has identical types.** The identity arm must therefore be kept, and it is kept, as the first arm of `copyPayload` (`common/systemc/bitTwiddling.h:86-87`).
- **The minimum sound precondition** is therefore: *both trivially copyable* (compiler-checked by `bit_cast`) **and** *equal `sizeof`* (compiler-checked) **and** *declaration-identical member sequences per §9.3* — the third of which **C++ cannot check** in this standard (no reflection). It must be supplied constructively **by the generator** (§9.7, §8.9). The alternative once offered here — a same-class-template deduction inside the adapter — is **removed** by the definitional correction: across two unrelated declarations there is no common class template to deduce (§9.1). **Do not ship the first two conditions alone**; §9.3 proves by execution that they admit value-scrambling pairs.
- Honest residual: even with all three conditions, `bit_cast` copies padding bytes whose values are unspecified. No emitted code reads padding, so this is a theoretical rather than practical concern — but it is why the mechanism is `bit_cast`/assignment and not a `reinterpret_cast` through a pointer.

### 9.5 What the current adapter costs, and where the eligibility measurement must be taken

**What the adapter does.** Every thunker performed the same three-line sequence per payload, per transaction. The line citations this paragraph carried are **pre-step-5 positions**; each of those sites is now a single `copyPayload( out, in );` call — `push_ack_port_thunker.h:134`, `:157`; `rdy_vld_port_thunker.h:130`, `:148`; `req_ack_port_thunker.h:136`, `:138`, `:160`, `:162`; `apb_port_thunker.h:149`, `:155`, `:165`, `:190`, `:195`, `:205`; `axi_read_port_thunker.h:139`, `:149`, `:169`, `:179`; `axi_write_port_thunker.h:152`, `:162`, `:169`, `:190`, `:200`, `:207`; and `builder/pro/interfaces/lmmi/lmmi_port_thunker.h:148`, `:154`, `:164`, `:188`, `:194`, `:204`. The sequence itself now lives once, in `copyPayload`'s slow-path arm (`common/systemc/bitTwiddling.h:90-95`):

```cpp
inVal.pack( inPacked );
copy_packed_bits( outPacked, inPacked, DownT::_bitWidth );
outVal.unpack( outPacked );
```

**Verified count: 24 `copy_packed_bits` call sites across the six base thunker headers (apb 6, axi_write 6, axi_read 4, req_ack 4, push_ack 2, rdy_vld 2), plus 6 in `builder/pro/interfaces/lmmi` — 30 in total.** **VERIFIED BY EXECUTION.** This mattered for §8.11: the change was not one edit, it was thirty, and 8.4=(b) will add roughly twenty-four more. **All thirty were collapsed onto `copyPayload` by step 5**, with the per-header counts unchanged (apb 6, axi_write 6, axi_read 4, req_ack 4, push_ack 2, rdy_vld 2, lmmi 6). **VERIFIED BY EXECUTION.**

**What that work is.** For the ISP's `video_rgb_t<Config>` → `isp_video_rgb_t` hop: `pack()` descends `frame.pack()` plus a 4-iteration loop over `rgb_pixel_t::pack()`, each issuing three `pack_bits` calls — roughly **13 out-of-line `pack_bits` calls plus a `memset`**; `copy_packed_bits` then runs one `pack_bits` over 99 bits (2 words); `unpack()` performs ~13 shift-and-mask extractions. `pack_bits` is **not** inline — it lives in `common/systemc/bitTwiddling.cpp:72-136` as an out-of-line loop with two `std::min`s and a branch per iteration. So order 15 function calls and 40-60 arithmetic operations per bridged transaction. **VERIFIED BY CODE READING.**

**What surrounds it.** The same transaction also performs, at minimum, two `sc_core::wait()` suspensions and two `sc_event::notify(SC_ZERO_TIME)` on the owned down channel and the parent channel (`interfaces/push_ack/push_ack_channel.h:200-263`), i.e. roughly four SystemC coroutine context switches and four delta-cycle event schedulings, plus a by-value payload copy of the full struct. **VERIFIED BY CODE READING.** On any normal SystemC kernel those dominate 40-60 integer operations by a wide margin.

**The pack/unpack cost is therefore unquantified as a fraction of simulation time, and this document does not invent a number.** The bound above is a code-reading bound, not a measurement.

**The eligibility census, re-measured on the example fixtures (2026-08-11). This is the section's evidence. The ISP-based table beneath it is superseded and kept only as history.** Taken per resolution 8.7 on `builder/base/examples` rather than on `/work/ws/isp`: every emitted `_port_thunker<>` instantiation was read from generated output and each of its payload pairs judged against §9.3's predicate — recursive, positional, nesting-respecting storage identity **including signedness**. **VERIFIED BY EXECUTION.** The unit is the **payload pair**, not the instantiation: a stream-protocol thunker carries one pair, an `apb` thunker carries two (address and data), so pairs exceed instantiations.

| Design | Payload pairs | Corresponding storage |
| --- | --- | --- |
| `ip_test` | 19 | 14 |
| `simple_ip` | 4 | 2 |
| `xif` | 2 | 0 |
| `xprojParam` | 16 | 1 |
| **total** | **41** | **17** |

**A note on how the four designs were built, recorded 2026-08-11 because it is easy to assume otherwise.** `make pipeline-test` has **15** targets, not 16, and **`xif` is not one of them** — the Makefile carries no `xif` target at all (`Makefile:264`; the 15 are listed at §7.1a). `xif` was generated separately, from its own project makefile, in order to be counted here. Any future re-run of this census must do the same or it will silently measure 39 pairs across three designs rather than 41 across four. **VERIFIED BY EXECUTION.**

**Seventeen eligible pairs, emitted today, on designs that need no further work to produce them.** Where they come from, because the distribution is not the one the ISP-based table would predict:

- **`ip_test`'s 14 are 8 + 6.** Eight are the register-bus `apb` pairs (four `apb` thunkers, two pairs each) — single-member structs over `uint32_t` typedefs, the class the old table already identified. The other six are `push_ack`, and split as follows. **Five are 70-bit `uint64_t word[2]` pairs** — `srcOut1BoundarySt` against `srcOut1St<…>` (twice), against `ipDataSt<…>` and against `data70St`, plus `data70St` against `ipDataSt<…>` — eligible for the reason corrected at §9.2, not because any of them is same-declaration; **four of those five put a literal side against a parameterizable one**, and the fifth (`srcOut1BoundarySt` ↔ `data70St`) is literal against literal, both being `word[2]`. The sixth is an 8-bit literal-against-literal pair, `srcOut0BoundarySt` against `data8St`. The 8-bit *siblings* of the five are **not** eligible, which is the discriminator: `ipDataT` is `uint64_t word[2]` at every variant, matching a 70-bit literal and not an 8-bit one.
- **`simple_ip`'s 2** are its single `apb` thunker's two pairs; both its `push_ack` pairs are 8-bit literal against `word[2]` and are not.
- **`xif`'s 0** is the `maxBitwidth <= 64` shape: `streamSt<dutDutV0Config>`'s parameterizable member is a bare `uint64_t` against a 16-bit literal's `uint16_t`.
- **`xprojParam`'s 1** is the `wrapEqSt`/`leafEqSt` pair the fixture was built to supply — two independently authored *parameterized* declarations, `{uint64_t, uint8_t}` on both sides. The other fifteen are the fixture's three deliberate counterexamples plus twelve literal-against-parameterized legs.

**The eligibility measurement — a factual record of what is emitted today, and NOT representative of the intended end state. SUPERSEDED as the section's evidence 2026-08-11 by the census above; retained so the history is legible.** It was written as "the decisive finding"; it is not, and the architect struck it as a justification: *"that is because the isp, is in partial state and does not have correctly parameterized isp. Focus effort on example fixture."* The bulk of the rows below come from `/work/ws/isp`, which is in a partial state and does not have a correctly parameterized ISP top, so its thunker population does not characterise the parameterized designs the axis exists to serve. **The zero-eligibility count is struck as an argument against building the axis** (§8.7 = build). What the table still is, and is kept for, is an accurate inventory of every thunker instantiation emitted in the tree as it stands today.

**Where the measurement must be re-taken: `builder/base/examples/xprojParam`.** Both the eligibility count and any cost measurement are re-run there, once it carries correctly-parameterized cases — not on the ISP tree. *(The eligibility half was re-taken 2026-08-11 and is the census above; the cost half is still open.)* Every thunker instantiation emitted anywhere in the tree, read from generated output (**VERIFIED BY EXECUTION**, `grep -rn "_port_thunker<"` over `/work/ws/isp` and `builder/base/examples`):

| Design | Thunker instantiations | Shape | C++-compatible? |
| --- | --- | --- | --- |
| `/work/ws/isp/model/isp_top.cppm:141-158` | 18 `rdy_vld` datapath | `<isp_video_*_t, video_*_t<...IspConfig>>` — literal boundary vs. parameterized IP | **No** — 15 bytes vs 104 |
| `/work/ws/isp/model/isp_top.cppm:159-160` | `raw`, `axi4_stream` | same shape | **No** |
| `/work/ws/isp/*/tb/*/*External.cppm:57-58` | 12 DUT-boundary | `<video_*_t<...DefaultConfig>, video_*_bndry_t>` | **No** |
| `examples/ip_test/top/model/ip_top.cppm:81-88`, `bridge/…:58-59`, `examples/simple_ip` | 11 `push_ack` | `<literalSt, ipDataSt<...Config>>` | **No** |
| `examples/ip_test/top/model/ip_top.cppm:89-90`, `bridge/…:56-57`, `examples/simple_ip/model/simple_ip.cppm:55` | 5 `apb` register-bus | `<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt>` — all four `{uint32_t}` single-member structs | **Yes** |
| `examples/xif/tb/dut/dutExternal.cppm:43-44` | 2 `push_ack` | `<streamSt<dutDutV0Config>, streamBndrySt>` | **No** |

The `apb` pair is genuinely eligible: `apbAddrSt { apbAddrT address; }` with `typedef uint32_t apbAddrT` (`examples/ip_test/common/model/shared_typesIncludes.cppm:28, :42-43`) against `ipRegAddrSt { ipRegAddrT address; }` with `typedef uint32_t ipRegAddrT` (`examples/ip_test/ip/model/ipIncludes.cppm:50, :1428-1429`) — different declarations, identical storage, identical `sizeof`.

**Read this table plainly, and read it as a snapshot of a partially-parameterized tree:**

1. **Zero of the ~43 datapath thunkers *in this tree today* are eligible, and all 5 eligible thunkers are register-bus adapters.** Within this snapshot the optimization is available on the cold path (register accesses during test setup) and unavailable on the hot path (per-pixel video). **This count carries no verdict** — the tree it is taken on is not correctly parameterized (see the lead-in above and §8.7).

   **SUPERSEDED 2026-08-11 for the `examples/` half, by measurement.** The row above is still an accurate reading of the ISP rows of this table, but the sentence "all 5 eligible thunkers are register-bus adapters" is **false of `examples/`**: the re-measured census counts **17 eligible payload pairs, of which 7 are not register-bus** — six `push_ack` pairs in `ip_test` (five 70-bit word-array pairs plus an 8-bit literal-against-literal pair), one parameterized-against-parameterized pair in `xprojParam`, and none in `xif`. (The other 10 are register-bus: eight `apb` pairs in `ip_test`, two in `simple_ip`.) One row of this table also carries a wrong verdict in its last column: the `11 push_ack … **No**` row lumps `ip_test`'s 70-bit pairs in with its 8-bit ones, and those pairs are not homogeneous. The error is one of granularity — the row judges a *shape* where the predicate applies per *pair* — which is why the census above counts pairs. The `xif` row and the `apb` row are unaffected, and the ISP rows are not re-judged here.
2. **For literal-versus-parameterized boundaries this is not an accident of the current designs; it is a consequence of the sanctioned pattern.** The de-parameterized boundary exists precisely to pair a *literal-width* assembler struct against a *parameterized* IP struct. Per §9.2, the literal side gets size-bucketed storage and the parameterized side always gets `uint64_t`. ~~Those two can only coincide if every field of the literal side is itself 64 bits wide. That form is ineligible by construction.~~ **It does not generalise to the parameterized-versus-parameterized form**, where per §9.1 *both* sides get `maxBitwidth`-derived storage and correspondence is therefore common rather than accidental — which is the form `examples/xprojParam` must supply and the ISP tree does not.

   **CORRECTION 2026-08-11 — the struck sentences are too strong, and the point they support does not survive as stated.** They are true only of the `maxBitwidth <= 64` arm, where the parameterizable side really does collapse to a bare `uint64_t`. Once `maxBitwidth` exceeds 64 **both** sides emit `uint64_t word[N]`, and they correspond whenever the two `N` agree — no field need be 64 bits wide, and the *resolved* widths need not match either (§9.2, `templates/systemc/includes.py:115-146`). So the literal-versus-parameterized form is **not** ineligible by construction; it is ineligible in the narrow bucket and eligible in the wide one. This is the larger of the two routes to correspondence in the tree as it stands: of the 17 eligible pairs, **four** are literal-against-parameterized word-array pairs in `ip_test`, against **one** parameterized-against-parameterized pair in `xprojParam` (the remaining twelve are ten register-bus `apb` pairs and two literal-against-literal pairs). What survives of the original point is only the narrow claim — a *bare-`uint64_t`* parameterizable member meets a literal member only in the 64-bit bucket, which is why `xif` scores zero.
3. **The one class the requirement actually names — "two parameterized structs may actually be c++ compatible" — was mis-read here, and the correction changes the conclusion.** It was read as the *same-declaration/two-Config* case (cell 10, `xprojParam/shared`), and on that reading the class "does not exist yet". **That reading is wrong.** Under the definitional correction (§9.1) a thunked junction never has one declaration on both sides, so the same-declaration/two-Config case is not a thunked junction at all and cannot be what the requirement names. What the architect means is **two *different* declarations whose content is identical** — two independently authored parameterized structs, each `maxBitwidth`-sized, corresponding member for member. That class is the general different-declaration case the 8.8=(b) predicate is written for, and it does not wait on Plan-of-record step 3 to come into existence. The five `apb` thunkers in the table — **ten** payload pairs, the census above counting per pair — are already instances of the *general different-declaration* case: different declarations, identical storage, identical `sizeof`, though non-parameterizable pairs rather than the parameterized ones the requirement names. **What the tree lacks is not the class; it is correctly-parameterized examples of it**, which is what `examples/xprojParam` must supply. *(Supplied 2026-08-11: `wrapEqSt` ↔ `leafEqSt`. The census also shows the class was never confined to non-parameterizable pairs — five of the eligible pairs put a literal side against a parameterizable one through the word-array bucket, per the correction to point 2 above.)*

**Verdict — SUPERSEDED. The original verdict is struck, and the reason is recorded rather than erased.**

> ~~Verdict, stated as CLAUDE.md's "simplest solution first" and "no speculative flexibility" require it: the optimization is NOT justified by the evidence available today. It would add a second compatibility predicate, a new view or trait mechanism, and a change to 30 (soon ~54) adapter call sites, in order to speed up five register-bus adapters whose transaction rate nobody has claimed is a problem.~~

That verdict rested entirely on the eligibility count of the table above, which is measured on a tree that is not correctly parameterized. **RESOLVED 2026-08-10 (§8.7): the axis is built.** The cost objection is not answered by this document and is not claimed to be — it is re-tasked, not dismissed (see below).

**Now false on its own terms, 2026-08-11, and the override is independently confirmed.** 8.7 struck the verdict on evidence-*base* grounds: the measurement was taken on the wrong tree, so it could not carry a "do not build". The re-measurement on the right tree settles the stronger question, and it settles it the other way. The verdict's premise — that the work would be undertaken "in order to speed up five register-bus adapters" — is **wrong by measurement**: **17** payload pairs are eligible today, **7 of them outside the register bus**, in `examples/` alone, with no further work required to produce them. Even the register-bus half is undercounted by the verdict's "five adapters": five `apb` thunkers carry **ten** payload pairs. So the verdict is not merely unsupported by its evidence; its factual claim is false. 8.7's override was right, and would have been right even had the architect's evidence-base objection not been raised.

**How the evidence gate is discharged — retargeted to the example fixture, not dropped. Experiment 1 has now been RUN and PASSED (2026-08-11); experiment 2 is still open.** The two experiments below stand as written except for where they are run, and except for the step-3 ordering in the first, corrected beneath it:

1. **Eligibility first, cost second.** ~~Land Plan-of-record step 3 (§8.1=(b)/§8.3), then~~ re-run the eligibility grep **on `examples/xprojParam`**, once that fixture carries correctly-parameterized cases. `/work/ws/isp` is not the measurement site and a null result there settles nothing.

   **DISCHARGED 2026-08-11.** The census above is that measurement, widened from `xprojParam` to all four example designs because the corrected §9.2 reading makes `ip_test` a contributor rather than a null. **Result: 17 of 41 payload pairs eligible — the gate passes.** The struck precondition is withdrawn with it: step 3 is *not* a prerequisite for the measurement, because none of the 17 depends on it (Plan of record, step 5). Running the grep before step 3 was in fact necessary to see that, since a step-3-gated measurement would have counted only cell-10 junctions and reproduced the null.

2. **Cost:** measure on the fixture rather than implementing against an assumed benefit — run one datapath simulation under `perf record`, or temporarily stub the three-line sequence with an unconditional `bit_cast` in one thunker header and compare wall-clock over a fixed transaction count. The delta-cycle bound above predicts the surrounding SystemC machinery dominates; that prediction is **unmeasured** and is recorded as the open quantitative question. It does not gate the work — 8.7 resolved that — but it is the number that would tell anyone whether the fast path was worth its complexity.

**What the fixture now provides, and what its role becomes.** `examples/xprojParam/cppLeaf` + `cppAxis` were built to discharge experiment 1 and have done so. Their standing role from here is not evidence but **acceptance**: they are four thunked junctions with **known verdicts**, all four bit-layout compatible and therefore all four reaching the adapter with `make db` clean, differing only in emitted C++ member storage. An implementation of step 5 that gets any of the four wrong is wrong visibly. Documented shape by shape in `examples/xprojParam/README.md`, "C++ definitions at a thunked junction":

| Shape | Verdict | Why, and what it pins |
| --- | --- | --- |
| `wrapEqSt` ↔ `leafEqSt` | **eligible** | storage `(uint64_t, uint8_t)` on both sides, `sizeof` 16/16. The positive case; two independently authored parameterized declarations. |
| `wrapOrderSt` ↔ `leafOrderSt` | ineligible — **storage order** | `{uint8_t, uint64_t}` against `{uint64_t, uint8_t}`, **equal `sizeof`** (16) and **identical packed sequences** (both members 8 bits wide). Pins §9.3's proof that trivial copyability plus equal `sizeof` is unsound: a byte copy here scrambles the payload. |
| `wrapSignSt` ↔ `leafSignSt` | ineligible — **signedness only** | `uint64_t` against `int64_t`, one member each, same width, same position, `sizeof` 8/8. A direct copy would in fact be correct, so this pins 8.8's *deliberately conservative* choice: the predicate is "the definitions are identical", not "a copy happens to be equivalent" (§9.6). |
| `wrapNestSt` ↔ `leafNestSt` | ineligible — **nesting** | three members against four, `sizeof` **24 against 16**, packed sequences identical `(32,0) (8,32) (8,40) (8,48)`. `std::bit_cast` would not even compile on it. Pins §9.3's requirement that the C++ axis respect nesting boundaries where the bit axis flattens. |

Plus a **literal-against-parameterized** leg per shape, confirmed ineligible: `bndEqSt` is `sizeof` 2 against `wrapEqSt`'s 16. That is the narrow-bucket form the corrected point 2 above still calls ineligible by construction — not the wide-bucket form `ip_test` supplies.

**The alternative worth weighing, because it targets the path memcpy cannot.** A *field-wise assignment* adapter would replace the pack/copy/unpack sequence with one scalar assignment per field (for `isp_video_rgb_t` ↔ `video_rgb_t<Config>`, 15 integer assignments with implicit conversion, against ~15 out-of-line calls plus a `memset` today). It requires only **layout** compatibility, which 8.6=(a) already guarantees at every accepted junction, so it applies to **all 43** datapath thunkers ~~rather than none of them~~ **rather than to the eligible subset only** (corrected 2026-08-11: that subset is 17 of 41 payload pairs in `examples/`, not none — the alternative's advantage over the direct-copy path is that it is universal, which is narrower than the original wording claimed but is unchanged in kind). Its cost is that the converter must be *generated* (C++ cannot enumerate members), so it is a larger change than a `bit_cast` branch. It is recorded here, not recommended, because it is subject to the same unmeasured-benefit objection — but if the motivation really is SystemC simulation speed, this is the change that would deliver it and the memcpy path is not.

### 9.6 Interaction with the resolved decisions

**8.2 (field names ignored).** The C++ axis does **not** need names either, and for the same reason: `bit_cast` and assignment are positional, and §9.3's correspondence is positional. **Rule: names are spelled in emitted code and printed in diagnostics; they are never compared, on either axis.** One qualification the architect should see: names *would* be needed to **spell** a field-wise assignment adapter (§9.5) — but even there the *correspondence* remains positional, so 8.2 is not disturbed by it.

**8.6 (per-field correspondence).** The C++ axis needs a **strictly stronger** correspondence than the bit axis, in two respects, both verified by execution in §9.3: (a) it must be **structural, not flattened**, because nesting preserves trailing padding that inlining elides; (b) it must compare **storage including signedness**, which the bit axis deliberately ignores. Consequently axis 2 rejects a strict superset of what axis 1 rejects among the pairs axis 1 accepts — which is exactly the containment relation a *selector* should have, and is safe: a false "incompatible" verdict costs only the existing pack/unpack path.

Both respects are now the resolved predicate (§8.8 = (b)). On signedness specifically, the safety argument above is the one the resolution turns on: an `int8_t`/`uint8_t` pair at equal width is *observationally equivalent* under either adapter — pack/unpack reinterprets the sign bit exactly as a direct copy would — so requiring matching signedness excludes a pair that would in fact have copied correctly, at a cost of nothing but the existing slow path. The architect required it anyway, which makes the predicate **"the definitions are identical"** rather than the weaker **"the fast path is observationally equivalent to the slow path"**. Both framings are recorded in §8.8; the first is chosen.

**8.1 (layout first, then adaptation).** The C++ check belongs to the **adaptation step, not the layout step** — Plan-of-record step 5, ~~after step 3~~ **after step 1** (corrected 2026-08-11; the step-3 ordering is withdrawn per the census in §9.5, and none of the three reasons below ever supported it). Three reasons, in decreasing order of force: it never rejects, so it cannot be part of a validator; it is meaningless before an adapter exists to select an implementation for — and **17 such adapters already exist** (§9.5), which is why step 3 is not the thing that brings them into being; and it **depends** on the layout gate for soundness (§9.3 condition 3 — equal parameterized array extents are inferred from axis 1's equal flattened sequences, not proven independently). Running it before step 1 is unsound.

**8.4 (seven missing thunker headers).** The memcpy path does **not** change what those headers must *contain* semantically, but it changes how much work they are. Today those headers are written by transcribing the three-line pack/copy/unpack sequence at every site — 24 base sites exist and the seven new headers would add roughly the same again. If the sequence is first collapsed into one shared helper (§9.7), each new header carries `copyPayload(outVal, inVal);` at each site and inherits the direct-copy path for free. **RESOLVED 2026-08-10 (§8.11, by implication of §8.9): the helper collapse lands before the seven headers.** It is no longer a recommendation resting on simplification grounds, and no longer conditional on 8.7: the shared helper is the consumer of the trait 8.9 emits, so the collapse is part of Plan-of-record step 5.

**The nested-vs-flat worked example (the §8.2 consequence).** Take the recorded pair: nested `{frame:{sof:1,eof:1}}` against flat `{sof:1,eof:1}`.

- **Axis 1 says EQUAL.** Both flatten to `[(1,0),(1,1)]`; the dotted path `frame.sof` is a name and 8.2 does not compare it. The junction is accepted and thunked. The bits are copied correctly by the positional adapter.
- **Axis 2 says INCOMPATIBLE.** The emitted C++ is `struct W { video_frame_t frame; }` — one member — against `struct F { sof_t sof; eof_t eof; }` — two members. Member counts differ at the top level, so §9.3 condition 1 fails and the pair takes the existing pack/unpack path.
- **And that is the right answer even though a `bit_cast` would happen to work here** (both are two `uint8_t`s, `sizeof == 2`), because the *general* nested-vs-flat pair does not work: §9.3's `sizeof 12` vs `sizeof 8` counterexample is the same shape with a wider first field. A rule that flattened the C++ member sequence to accept this pair would silently mis-copy its near neighbour. **This example is the reason §9.3 is structural.**

### 9.7 Where the fact lives, what it is called, and automatic vs. authored

**Three candidate homes were considered. The first is REMOVED by the definitional correction; of the remaining two, `buildThunkerView` is chosen (§8.9).**

- ~~**The thunker header, compile-time.**~~ **REMOVED 2026-08-10 — not rejected on merit; it has no viable form.** The option was: a shared helper dispatching `if constexpr` on `std::is_same_v<To,From>` → `out = in;` · eligible → `out = std::bit_cast<To>(in);` · otherwise → today's pack/copy/unpack, with C++ proving the *same-declaration/two-Config* case on its own via a two-line `sameClassTemplate` trait plus the `sizeof` constraint `bit_cast` already enforces — **requiring no `projectCreate`, `projectOpen` or template change at all**.

  **It cannot work.** Under the definitional correction (§9.1) a thunked junction always has two *different* declarations, hence two unrelated C++ types. So `std::is_same_v` is false by construction, there is no common class template for a `sameClassTemplate` trait to deduce, `sizeof` equality is proven unsound as a predicate by §9.3, and C++ has no reflection with which to compare the member sequences of two unrelated types. **The predicate is not decidable in C++.** The option is therefore removed from consideration entirely, together with the 8.8=(a) predicate that was its only justification.

  **What survives from it, and is retained, is the *helper*, not the *decision*.** `copyPayload(To& out, const From& in)` in `common/systemc/bitTwiddling.h` beside `copy_packed_bits` (`:38-60`), replacing all 30 three-line sequences with one call, is exactly the shared payload-copy helper 8.9 selects and 8.11 orders first. It still dispatches with `if constexpr`; what it dispatches *on* is the generator-emitted trait below, not a self-computed predicate. The thunker headers remain hand-written runtime library rather than generated code, so the view/template ownership split still does not govern them.
- **`buildThunkerView` (`getBDCrossInterfaceBinds`, `processYaml.py:2667`), a projectOpen view helper. CHOSEN, and built (Plan of record, step 5).** This is the right home if the predicate is the general member-sequence one (8.8=(b)), because C++ cannot decide it. The view already assembles exactly the needed inputs: each payload entry carries `structureType`, `structure`, `structureKey` and `configSelection` (`processYaml.py:2699-2705`), and the pairing of parent to child payload is already established there. The added fact is one boolean per payload pair. This matches the CLAUDE.md rule directly — "language-neutral reshaping for one rendering context … includes cross-interface bind classification" — and matches the view's own stated contract at `getBDCrossInterfaceBinds`, `processYaml.py:2579-2583`. Note the one genuine tension: "is this C++-compatible" is by nature a language-specific question, so the fact must be phrased over *storage descriptors* rather than C++ spellings.

  > ~~There is precedent — `platformDataType` is already a C-family spelling persisted at db time (`processYaml.py:1150`).~~

  **CORRECTED 2026-08-11.** `platformDataType` is not persisted at all; it is derived in the `projectOpen` view `getContextData()` and mutated into `prj.data['types']` in place, and the `types` table has no such column (§9.2). The precedent therefore supports a *weaker* proposition than the one recorded: a C-family-adjacent fact may be derived **in a `projectOpen` view**, which is exactly where `structureStorageSignature()` and `typeStorage()` were put. It does **not** support persisting such a fact at db time — and nothing in this plan proposes to, since `projectCreate` persistence stays rejected below. The tension is named rather than glossed either way.
- **`projectCreate`.** Rejected. There is no db-time consumer: the fact produces no diagnostic and gates no acceptance. Persisting it would be exactly the speculative durable state CLAUDE.md forbids. If a `make db` report is later wanted, it moves.

**RESOLVED 2026-08-10 (§8.9): `buildThunkerView`, delivered as an emitted trait specialization.** In the architect's words, *"we need to pass a generated parameter to the thunker from the database."* The choice is no longer contingent on 8.8: 8.8 resolved as (b), and the (a) branch — the pure-C++ helper with no generator change — is removed outright as undecidable in C++ (above, §9.1). The boolean is computed per payload pair in `buildThunkerView` (`pysrc/processYaml.py:2565`), whose payload rows already carry `structureType`, `structure`, `structureKey` and `configSelection` (`processYaml.py:2597-2603`).

**The template must consume, not derive.** `_thunker_member_type` spells the thunker's template arguments from the view's payload list. The template selects a precomputed boolean and emits one literal per pair; it derives nothing. That part stands.

> ~~The chosen spelling is a generated trait specialization consulted by the shared `copyPayload` helper. That leaves all seven existing thunker class signatures untouched, and the seven that 8.4=(b) adds, unlike adding a `bool` template parameter to each ... Both alternatives are rejected on those grounds (§8.9).~~
>
> **Reversed 2026-08-11.** The `bool`-template-parameter spelling is now the mechanism and the trait is deleted. Leaving the class signatures untouched was the whole of the case against it, and that is outweighed by the architectural constraint that **no interface-specific knowledge may live in the generator or the templates**. The trait spelling pushed protocol-specific structure generator-side — which pair, which copy direction, which specialization head, and deduplication across adapters — while the `bool` spelling reduces the generator to appending `len(payloadPairs)` literals and moves every protocol-specific fact (which flag gates which call site, `apb`/`lmmi`'s data flag firing at four sites, `axi_write`'s `DirectData && DirectStrb` conjunction, its unflagged response leg, and every `static_assert`) into the interface's own hand-written thunker header, beside its YAML and channel header. The constructor-argument alternative remains rejected: it would turn a compile-time selection into a runtime branch.

**Superseded 2026-08-11 by the mechanism replacement above — the three corrections below are retained as history of the trait spelling, which no longer exists:**

> ~~a generated trait specialization emitted once per eligible junction — `template<> struct a2c_payload_direct_copy<To, From> : std::true_type {};`~~

1. **`template<>` is not always legal.** A payload spelled on the container's own `Config` template parameter has no concrete type to name, so a **partial** specialization deducing `Config` is required. That is fixture case (a), the only eligible pair in `xprojParam`.
2. **Two specializations per eligible pair, not one** — parent-to-child and child-to-parent, because an adapter copies both ways and the correspondence is symmetric.
3. **Deduplicated per rendered scope**, because one container may hold two adapters bridging the same pair of payload types (the two identical `apb` adapters in `ip_top`) and a specialization may be declared only once.

**Current spelling.** One `true`/`false` literal per `payloadPairs` entry, appended in `payloadPairs` order to the thunker member's template argument list by `_thunker_member_type()` (`pysrc/intf_gen_utils.py`). All three corrections above dissolve rather than being carried forward: there is no specialization head to choose, no second copy direction to emit, and nothing to deduplicate, because the verdict is part of the member's own type. The class template defaults every flag to `false`, so a wrong or absent slot degrades to the packed path rather than to a miscopy.

**Automatic or authored opt-in? RESOLVED 2026-08-10 (§8.10 = (a)): automatic, and no YAML switch.** The architect's phrase "allow the option of straight memcopy" is read as *make the option available to the generator*, not *give the author a knob* — a reading the architect's later note that the memcpy phrasing was directional (§9.4) supports. Three reasons: the selection is provably semantics-preserving whenever it fires, so there is nothing for an author to decide; a per-junction annotation would become permanent and invisible in the YAML, which is exactly the objection §7.5 raises against per-connection escape hatches; and CLAUDE.md forbids an option with no concrete current call site. **No `project.yaml` switch, no per-connection annotation, and no `--` flag is proposed.** The mechanism settles it by construction: the fact is generator-emitted per junction as a template argument, so there is no authored surface to opt in on.

## Deferred / Out of Scope

**Known-incomplete items left by step 5 (2026-08-11). BOTH CLOSED AS MOOT 2026-08-11 by the mechanism replacement** — a template argument is part of the member's type, so it is emitted wherever the member is emitted and reaches wherever the member reaches. `xif`'s External now carries explicit `false` flags on both mirrored members, which pins the External path by emitted output rather than only structurally. The two items are retained below as history.

- **The testbench External trait path is wired but has no non-empty output anywhere in the tree.** `templates/systemc/testbench.py::ext_sec_header()` (`:510`) calls `sc_declare_payload_copy_traits()` on the External pseudo-block, and every build exercises the call — but no example emits a trait through it. `xif` is the only example whose External mirrors adapters at all, and **both** of its payload pairs are ineligible (§9.5). So the path is exercised *structurally* by every build and shares its emitter with the block path, but no emitted result pins it. **It is not speculative flexibility, and it must not be removed as such:** without it, the External's mirrored adapter would take the slow path while the DUT's own adapter takes the fast path for the same payload pair, inside the same program. What is missing is a fixture whose External mirrors an *eligible* pair.
- **Cross-translation-unit reachability of the specialization is not proven by construction.** The trait is declared in the block module's purview. An importer — a registrar, say — that implicitly instantiates the same adapter relies on **module reachability** to see it. The runtime probe recorded in step 5 confirms the fast path does fire in `cppAxis`, which is evidence for the case measured and not a proof for the general case. **The failure mode is stated explicitly so nobody hunts a data-corruption bug that cannot occur:** if some translation unit did not see the trait, that unit selects the **slow path**, which is observationally identical to the fast one. The consequence of a reachability gap is lost speed, never a wrong copy.

Other deferred items:

- **`Reserved` padding fields wider than 64 bits are emitted as a scalar container that cannot hold them** (`pysrc/systemcGen.py:136-144`, which selects the bucket's `unsignedType` and ignores its `arrayElementSize`) — a suspected latent generator defect, deliberately not touched by step 5, which mirrors the emitted behaviour rather than the apparently intended one (§9.3a). No example in the tree declares one.
- **Four copies of the storage-bucket table, one already diverged** (§9.2), and the single-source route through `getContextData()` that was available and not taken (§9.3a). Not a live bug; a drift risk currently held off by one pinning test.
- **G5.9** (variant-binding sizing on the include-reached path) — undetectable by this check by construction (§5.5). Own fix.
- **G5.4** (Config composition from one `configContext`) — orthogonal (§5.4).
- **G5.6** (unqualified colliding identifier in generated block modules) — reclassified as a generated-code qualification defect, independent of parameterization (§5.6).
- **`_resolveSvInstanceParams` KeyError on a variant-less parameterizable child** (`_resolveSvInstanceParams`, `processYaml.py:2006`) — a prerequisite, not part of this check (§5.7).
- **Context-ownership lexical tie-break** (`pysrc/projectScan.py:367-374`) — prerequisite for the emission half only (§5.7).
- **`connectionMap` with a parameterizable parent interface mis-attributes the mapped child's config context** (`calcBlockConfigInfo` step 3, `processYaml.py:4950-4956`, consumed at `:5015-5030`; selection fails in `_selectVariantDescriptor`, `:1665-1681`) — found 2026-08-11, in scope for no step (§5.8). The fixture works around it.
- **`connectionMap` thunker members collide by name** (`_thunker_member_name`, `pysrc/intf_gen_utils.py:899-906`; emitted by `sc_declare_thunkers`, `:930-940`) — found 2026-08-11, in scope for no step (§5.8). The fixture works around it.
- `memoryConnections` / `registerConnections` payload comparison — no interface exists to compare (§3.7).
- **Enum member-set divergence at equal width** — **RESOLVED 2026-08-10 (§8.5 = (a)): out of scope.** A value-domain question, not a layout question; it belongs with a types/structures identity check.
- **Field-name divergence as a defect** — **RESOLVED 2026-08-10 (§8.2 = (c)): out of scope, and removed where it exists today** (§1.2.1). Not deferred: deliberately not the tool's business.
- ~~Per-container-variant evaluation of `inheritContainerParam` junctions — specifying it depends on 8.1.~~ **No longer deferred.** 8.1 is RESOLVED as (b), so this is specifiable and belongs to the Option B pass — "Plan of record" step 3 (§1.3).
- Any implementation schedule or effort estimate, and any code. **Sequencing is no longer out of scope:** it is recorded in "Plan of record", which states order and dependencies only.
