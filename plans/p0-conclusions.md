# P0 Proof-of-Concept Conclusions — SV & SystemC Parameterization

## Summary

Two throwaway prototypes validated that the target parameterization patterns work end-to-end with the project's toolchain. Both prototypes passed all validations within their stated scopes. No fundamental blockers were identified within the P0 scope; remaining concerns are listed in [§ Not Validated in P0 / Deferred](#not-validated-in-p0--deferred).

| Prototype | Language | Toolchain | Risks Validated | Result |
|-----------|----------|-----------|-----------------|--------|
| `proto/model/` | SystemC / C++23 | Clang 20.1.8, SystemC 2.3.4 | V1–V7 | All pass |
| `proto/rtl/` | SystemVerilog | Verilator 5.038 | R1–R4, R6 | All pass |

R5 was reserved during planning for a co-simulation TB integration item but was deemed out of P0 scope and is intentionally absent. The numbering is preserved for traceability with the original validation matrix.

## Validation Item Definitions

The `V*` and `R*` IDs used throughout this document refer to the following validation items. Each maps to a concrete artifact in the prototype tree.

### SystemC validation items (`proto/model/`)

| ID | Description | Artifact |
|----|-------------|----------|
| **V1** | `template<typename Config> SC_MODULE(...)` with `SC_HAS_PROCESS` and `SC_THREAD` registration | `block/interpolate.h`, `block/interpolate.cpp` |
| **V2** | `rdy_vld_in`/`rdy_vld_out` ports with template payload (`video_bayer_t<Config>`); channel binding and end-to-end data fidelity | `util/rdy_vld_channel.h`, `test/test_sc_module.cpp` |
| **V3** | `inline friend sc_trace(...)` defined inside template structs; ADL discovery for concrete instantiations | `types/isp_types.h` (per-struct `sc_trace` friend) |
| **V4** | Two distinct Configs coexist in one binary as types: `rgb_pixel_t<config_8bpc>` (24-bit) vs. `rgb_pixel_t<config_12bpc>` (36-bit); pack/unpack and `sc_pack`/`sc_unpack` roundtrips | `test/test_structs.cpp` |
| **V5** | C++20 module interface unit `export module isp;` with global module fragment `module; #include "systemc.h";`; template structs in `export namespace` | `types/isp_types.cppm`, `test/test_module_types.cpp` |
| **V6** | Module import with `using namespace`; ADL still resolves friend `sc_trace` across module boundary | `test/test_module_types.cpp` |
| **V7** | Templated `SC_MODULE` exported from a C++20 module, imported by consumer, instantiated, bound, and simulated | `block/interpolate.cppm`, `test/test_module_block.cpp` |
| **V8** | Multi-word `_packedSt` (`uint64_t[N]`): pack/unpack a `wide_pixel_array_t<Config>` whose `_bitWidth` exceeds 64 bits round-trips correctly, including pixels that straddle 64-bit word boundaries. Coverage spans single-word (`config_8bpc`, 35 bits, 1 word), low-end multi-word at the production-shape Config (`config_12bpc`, 99 bits, 2 words), and high-end multi-word at test-only wide Configs (`config_wide_8bpc`/`config_wide_12bpc`, 195/291 bits, 4/5 words). | `types/wide_struct_test.h`, `types/wide_struct_test_configs.h`, `test/test_wide_struct.cpp` |

### SystemVerilog validation items (`proto/rtl/`)

| ID | Description | Artifact |
|----|-------------|----------|
| **R1** | Same module source elaborates against per-variant package files (8bpc and 12bpc) producing distinct widths | `packages/isp_types_pkg_{8bpc,12bpc}.sv`, `rtl/{interpolate,preprocess,debayer}.sv`, `test/tb_variant.sv` |
| **R2** | Derived constant chains (`BPPC_P1`, accumulator types) propagate correctly across variants; full type dependency chain elaborates | same as R1; verified via observed widths in `tb_variant` |
| **R3** | Module-level `parameter` defaulting from package + module-local types; two differently-parameterized instances coexist in one Verilator build | `rtl/interpolate_mparam.sv`, `test/tb_mparam.sv` |
| **R4** | Register decode `case` statements use `localparam` named constants instead of hex literals | `rtl/decode_named.sv`, `test/tb_decode.sv` |
| **R5** | *(reserved — not in P0 scope)* | — |
| **R6** | System container with two same-IP instances at different parameters; data flows across structural-type-compatible boundaries (TB → container → module) | `rtl/{camera_subsystem,interpolate_mparam,preprocess_mparam}.sv`, `test/tb_dual_instance.sv` |

## Confirmed Parameterization Strategy

The prototypes confirm a two-level parameterization strategy that works identically in both SystemC and SystemVerilog:

| Level | Use Case | SystemC Mechanism | SystemVerilog Mechanism |
|-------|----------|-------------------|------------------------|
| **Single-instance** | Leaf-level tandem, per-variant builds | Config template struct (`config_8bpc`, `config_12bpc`) | Per-variant package generation (same `isp_types_package` name, different `localparam` values) |
| **Multi-instance** | System with multiple IP variants in one build | Two Config instantiations in same binary (`interpolate<config_8bpc>`, `interpolate<config_12bpc>`) | Module parameters defaulting from package + module-local type definitions |

Both mechanisms produce text-stable IP source — the module/block source files are identical across variants. Only the parameter container (Config struct or package localparams) changes.

## SystemC (Model) Conclusions

### What works

1. **Config-templated SC_MODULE** (V1) — `template<typename Config> SC_MODULE(interpolate)` with `SC_HAS_PROCESS` and `SC_THREAD` works correctly. The C++ injected class name rule makes `SC_HAS_PROCESS(interpolate)` resolve to `typedef interpolate<Config> SC_CURRENT_USER_MODULE` inside the template scope.

2. **Templated rdy_vld binding** (V2) — `rdy_vld_channel<video_bayer_t<Config>>` binds to `rdy_vld_in`/`rdy_vld_out` ports. Data transfers with full struct fidelity through the channel.

3. **sc_trace with template structs** (V3) — `inline friend void sc_trace(...)` inside template structs works. ADL discovers the friend function for concrete instantiations.

4. **Two Configs coexisting** (V4) — `rgb_pixel_t<config_8bpc>` (24-bit) and `rgb_pixel_t<config_12bpc>` (36-bit) are distinct types (verified by `static_assert(!std::is_same_v<...>)`). Pack/unpack roundtrips and `sc_bv<_bitWidth>` round-trips verified for `rgb_pixel_t`, `bayer_pixels_per_clock_t`, and the compound `video_bayer_t`. `sc_bv<_bitWidth>` with constexpr template arguments works.

   *Caveat on the leaf-type alias:* `pixel_t<Config>` is declared as `template<typename Config> using pixel_t = uint64_t;`. Because the alias does not actually depend on `Config`, `pixel_t<config_8bpc>` and `pixel_t<config_12bpc>` are the *same* C++ type. Type distinctness for cross-config protection is therefore established at the *enclosing struct* level (`rgb_pixel_t<C>`, `video_bayer_t<C>`, etc.), not at the leaf scalar level. This is sufficient for the interface-prohibition rule because all interface payloads are structs, but generators must rely on the wrapping struct — not the leaf alias — for type-system separation. The empty-`Config` alias was retained over a phantom-tag wrapper struct to avoid disturbing existing arithmetic on pixel scalars in hand-written code.

5. **C++20 modules with SystemC** (V5/V6) — `module; #include "systemc.h"; export module isp;` compiles. SystemC macros from the global module fragment are visible in the module purview. Template structs export from `export namespace` and import correctly.

6. **Full pipeline: module + template SC_MODULE** (V7) — Templated SC_MODULE exported from a C++20 module, imported by consumer, instantiated, bound, and simulated successfully.

### Issues encountered (all resolved)

| Issue | Resolution | Generator Impact |
|-------|-----------|------------------|
| Explicit instantiation must use `template struct` not `template class` | `SC_MODULE` expands to `struct`, so instantiation keyword must match | Minor — generator emits `struct` keyword |
| `rdy_vld_channel` namespace ambiguity with redundant `using` alias | Don't create a global alias when `using namespace sc_core` already imports the name | None — production code doesn't have this redundancy |
| `.pcm` → `.o` compilation requires `-fmodule-file=` for all imported modules | Propagate module file flags to all compilation steps | Build system must track module dependency chains |
| `_packedSt` sizing for types > 64 bits | *Validated in V8 (post-P0 deferred-task work).* The `uint64_t[(_bitWidth + 63) / 64]` strategy round-trips a 99-bit struct (2 words at the production-shape `config_12bpc`), a 195-bit struct (4 words at a wider test-only Config), and a 291-bit struct (5 words at a wider 12bpc test-only Config), including straddling-pixel positions across word boundaries. The struct (`wide_pixel_array_t<Config>`) follows the standard single-Config-parameter convention used throughout `isp_types.h`. The existing `video_rgb_t` definition in `types/isp_types.h` retains its single-`uint64_t` POC simplification with the original limitation comment; the generator-target form is exercised separately in `types/wide_struct_test.h`. | Generator may emit the multi-word path with confidence; reference implementation is `wide_pixel_array_t` in `types/wide_struct_test.h`. |

### Required Clang flags for C++20 modules

| Flag | Purpose |
|------|---------|
| `--precompile` | `.cppm` → `.pcm` |
| `-fmodule-file=<name>=<path>` | Module dependency reference (needed at all compilation stages) |

No flags beyond the standard project set (`-std=c++23`, `-DSC_CPLUSPLUS=201703L`, `-DSC_INCLUDE_DYNAMIC_PROCESSES`) were required.

*Note on `SC_CPLUSPLUS=201703L` paired with `-std=c++23`:* SystemC's `SC_CPLUSPLUS` macro is its internal feature-detection switch. Pinning it to 201703 while compiling at C++23 keeps SystemC on its conservative C++17 code paths even though the user code uses C++23 features (modules, `<format>`, etc.). This is intentional for SystemC 2.3.4 stability and matches the existing project convention; it is not a P0 finding. If a future SystemC release gates a desired feature on `SC_CPLUSPLUS >= 202002L`, this pin will need to be revisited.

### Cross-config negative test (Task 1)

The interface-constraint rule from umbrella §7 (no wiring of `interpolate<config_8bpc>` to a `config_12bpc` channel) is enforced at compile time by the C++ type system. Verified manually with:

```
clang++ -std=c++23 -g -Wall -Wextra -Wno-unused-parameter -pthread \
    -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES \
    -Iconfigs -Itypes -Iblock -Iutil -I/usr/include \
    -c proto/model/test/test_cross_config_negative.cpp -o /tmp/xneg.o
```

First diagnostic emitted (truncated):

```
test/test_cross_config_negative.cpp:40:9: error: no matching function for call
  to object of type 'rdy_vld_in<video_bayer_t<config_8bpc>>'
  (aka 'sc_port<sc_core::rdy_vld_in_if<video_bayer_t<config_8bpc>>>')
   40 |         u_interp_8.video_bayer_stream(bayer_ch_12);
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/usr/include/sysc/communication/sc_port.h:288:10: note: candidate function not
  viable: no known conversion from
  'rdy_vld_channel<video_bayer_t<config_12bpc>>'
  to 'sc_core::rdy_vld_in_if<video_bayer_t<config_8bpc>> &' for 1st argument
```

A second, identical-shape error follows for `video_rgb_stream`. Judgment: clear and actionable — both incompatible types are spelled out, including their `<config_…>` arguments, so a developer can immediately see *which* Config mismatch caused the failure. The test file (`test/test_cross_config_negative.cpp`) is intentionally NOT part of `make all`; the comment at the top of the file shows the manual compile invocation.

### Build-time measurements (Task 3)

Measured on the same Clang 20.1.8 / SystemC 2.3.4 stack as the rest of the prototype, `make -j1`, median of 3 runs from clean:

| Build target | What it builds | Median wall-clock |
|--------------|----------------|------------------:|
| `step1` (`test_structs`) | Templated structs, no SC_MODULE, headers | 0.97 s |
| `step2` (`test_sc_module`) | Templated `SC_MODULE` + channel binding, headers | 1.85 s |
| `step3` (`test_module_types`) | C++20 module of types only, no SC_MODULE | 1.53 s |
| `step4` (`test_module_block`) | Templated `SC_MODULE` through C++20 module | 2.94 s |
| `step5` (`test_wide_struct`) | Multi-word `_packedSt` test, headers | 0.96 s |
| **Baseline** (`baseline/test_baseline`) | Non-template SC_MODULE (8bpc-only), headers | 1.73 s |

Reproducibility: Clang 20.1.8 (already documented above), Linux x86_64 development host, SystemC 2.3.4. Source for the non-template baseline lives at `proto/model/baseline/`.

**Interpretation.** Templated headers cost ~7 % over the non-template baseline (1.85 s vs. 1.73 s). The C++20 modules path (`step4`) costs ~60 % over templated headers (2.94 s vs. 1.85 s); modules trade absolute compile-time for *re-compile* time once a module is precompiled, so this baseline-of-1 figure is conservative — incremental builds amortize the precompile across consumers. Neither result is large enough to reconsider Option 4. **Judgment: go.**

### Verilator-generated headers + C++20 modules interop (Task 8)

A sniff test (`proto/model/test/test_modules_with_verilator_headers.cpp`) compiles a TU that *both* `import isp;` *and* `#include`s a Verilator-style header (a self-contained header that itself includes `"systemc.h"` and declares an `sc_module`-derived class — same shape as `builder/base/examples/apbDecode/verif/vl_wrap/obj_dir/V*.h`). Compiles cleanly with the same `-fmodule-file=isp=…` flag set used elsewhere; running the binary prints the expected output. The textual include and the module import coexist without symbol-resolution conflicts: `sc_module`, `sc_in`, etc. resolve to the single SystemC TU shared by the program. The cosim work may safely assume `import isp;` and Verilator-generated headers are mixable in the same TU. Test file is intentionally not part of `make all`; compile command is documented at the top of the file.

## SystemVerilog (RTL) Conclusions

### What works

1. **Per-variant package generation** (R1/R2) — The same module source (`interpolate.sv`, `preprocess.sv`, `debayer.sv`) elaborates and simulates correctly against both 8bpc and 12bpc package variants. Types, widths, and array dimensions resolve correctly in each variant. Each variant is a separate Verilator build.

   - 8bpc: `pixel_t` = 8 bits, `video_bayer_t` = 35 bits, `video_rgb_t` = 99 bits
   - 12bpc: `pixel_t` = 12 bits, `video_bayer_t` = 99 bits, `video_rgb_t` = 291 bits

2. **Derived constant chain correctness** (R2) — Constants derived from parameterizable constants (`BPPC_P1 = BITS_PER_PIXEL_COLOR + 1`, accumulator types `acc2_t`, `acc4_t`) resolve correctly when base constants change between variants. The full type dependency chain — constants → types → structs → interface data types — elaborates without width mismatches.

3. **IP module pattern with local types** (R3) — A module declaring `parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR` (defaulting from package), defining all parameterized types locally from its parameters, works correctly. Two differently-parameterized instances (`interpolate_mparam #(.BITS_PER_PIXEL_COLOR(8))` and `interpolate_mparam #(.BITS_PER_PIXEL_COLOR(12))`) coexist in one Verilator build.

4. **Named constant register decode** (R4) — Register decode `case` statements using `localparam` named constants instead of hex literals work correctly. Functionally equivalent to literal decode.

   *Scope of R4:* The prototype validates only the *literal-substitution* part of the address-decode plan (umbrella §5.6 approach 1). It does **not** exercise:
   - Cumulative offsets derived from `maxBitwidth`-based worst-case sizing.
   - A register set containing parameterizable structures.
   - The SystemC `hwRegister<N>` template-parameter sourced from `maxBitwidth`.

   These remain design-only and must be exercised before Step 11/Step 12 of `plan-parameterizable-config-template.md` are considered de-risked. R4 confirms only that the named-constant *mechanism* works in Verilator.

5. **Dual-instance integration with structural type compatibility** (R6) — A system container (`camera_subsystem`) instantiates the same IP twice with different parameters (12bpc/8PPC and 8bpc/4PPC). The container defines local types per instance to create internal interfaces. Data flows correctly across the type boundary: TB-local types → container-local types → module-local types. Structural type compatibility for `struct packed` across scopes is confirmed in Verilator.

### Verilator-specific findings

| Finding | Resolution | Impact |
|---------|-----------|--------|
| `DECLFILENAME` warning — variant package filename doesn't match `package isp_types_package` name | `-Wno-DECLFILENAME` | Expected and benign — per-variant files intentionally share a package name |
| `VARHIDDEN` warning — module parameters shadow wildcard-imported package constants | `-Wno-VARHIDDEN` | Expected and intentional in generator-emitted code, but a footgun for hand-written code: a TB doing `import isp_types_package::*;` and then referencing `BITS_PER_PIXEL_COLOR` inside a parameterized module will silently get the *parameter* value, not the package value. Generator and review guidelines must call this out. |
| `--x-initial-edge` causes timing scheduler conflicts with `--timing` | Remove `--x-initial-edge` | Verilator 5.038-specific interaction; not needed for prototype validation |

### SV text-stability confirmed

The diff between 8bpc and 12bpc packages is exactly 3 `localparam` value lines. Everything else — derived constants, types, structs, expressions — is byte-for-byte identical. A generator can emit the package once as a template and substitute only the parameter values per variant.

## Cross-Language Mapping

The two prototypes validate the same parameterization architecture expressed in two languages:

| Concept | SystemC (C++) | SystemVerilog |
|---------|---------------|---------------|
| Parameter container | `struct config_8bpc { static constexpr ... }` | `package isp_types_package; localparam ... endpackage` |
| Type text-stability | `template<typename Config> struct rgb_pixel_t` with `Config::` refs | `typedef struct packed { pixel_t b, g, r; }` referencing symbolic constants |
| What varies per variant | Config struct (external to IP) | Package `localparam` values (regenerated) |
| What's text-stable | All IP source (templates resolve at compile time) | All IP module source + package type/struct definitions |
| Single-instance build | Compile with specific Config | Verilate with specific package file |
| Multi-instance build | Two Config instantiations in same binary | Module parameters (default from package) + local types |
| Tandem pairing | `interpolate<config_8bpc>` model ↔ RTL with 8bpc package | Model compiled with `config_8bpc` ↔ RTL verilated with 8bpc package |

## Implications for Generator Changes

### Package generation (SV)

- IP packages become per-variant: regenerate with different `localparam` values, same package name
- Type/struct definitions within the package are already text-stable — no changes needed
- A shared types package (`shared_types_pkg`) holds non-parameterizable types unchanged

### Config struct generation (C++)

- Config structs are new generated artifacts — one per variant
- Template struct definitions replace current concrete struct definitions
- Pack/unpack use `Config::` symbolic expressions instead of resolved literals
- Explicit template instantiation lines needed for each supported Config

### IP module generation (SV, multi-instance case)

- Modules declare parameters defaulting from package
- All parameterized types defined locally from module parameters — not imported from package
- Container modules define per-instance local types for internal interfaces

### Build system

- Per-variant build directories with symlinked module source and variant-specific package files
- Verilator flags: `-Wno-DECLFILENAME -Wno-VARHIDDEN` for the IP module pattern
- C++20 module support: `--precompile`, `-fmodule-file=` flag propagation through dependency chains

## Risks Retired

All risks listed below were validated within their stated P0 scope, or closed by the post-P0 deferred-task work tracked in [`p0-deferred-tasks.md`](./p0-deferred-tasks.md). See [§ Not Validated in P0 / Deferred](#not-validated-in-p0--deferred) for items that remain open.

| Risk | Status | Notes |
|------|--------|-------|
| Config-templated SC_MODULE with SystemC macros | Retired | SC_HAS_PROCESS, SC_THREAD, SC_CTOR all work with templates |
| rdy_vld binding with template payload types | Retired | Channel/port binding works, data fidelity confirmed |
| sc_trace with template structs (ADL) | Retired | Friend function ADL works for template instantiations |
| Two Configs coexisting in same binary | Retired | Distinct types at struct level, correct widths, pack/unpack verified. Leaf-alias caveat documented. |
| C++20 modules with SystemC headers | Retired | Global module fragment pattern works |
| Template export/import through C++20 modules | Retired | Types and SC_MODULEs both export/import correctly |
| Per-variant SV package generation | Retired | Same source, different constants, correct elaboration |
| Derived constant chain across SV variants | Retired | Full chain propagates correctly |
| Module-local types from parameters in Verilator | Retired | Two instances with different widths coexist |
| Named constant register decode (mechanism) | Retired | Literal-substitution path validated; worst-case sizing path not exercised — see deferred items |
| Structural type compatibility across SV scopes | Retired | TB, container, and module scopes all interoperate |
| Cross-config interface wiring negative test | Retired (Task 1) | Compile-time error captured; see "Cross-config negative test" subsection above. |
| Multi-word `_packedSt` (`uint64_t[N]`) | Retired (Task 2 / V8) | Round-trip validated for 2-, 4- and 5-word cases (including the production-shape `config_12bpc`) with word-boundary straddling pixels. |
| Build-time / compile-cost measurements | Retired (Task 3) | Templated headers ~7 % over non-template baseline; modules path ~60 % over templated headers. Go. |
| Shared-vs-IP namespace boundary | Retired (Task 4) | Decision documented in [`builder/base/plan-shared-vs-ip-boundary.md`](./plan-shared-vs-ip-boundary.md): `ipParameters` only in IP-owned YAML. |
| SV parameterization strategy pinned | Retired (Task 5) | Plan in [`builder/base/plan-sv-parameterization.md`](./plan-sv-parameterization.md): separate-packages-per-instance + module-level parameters. SV-2012 parameterized packages explicitly deferred. |
| `instanceFactory` strategy with templated blocks | Retired (Task 6) | Plan in [`builder/base/plan-instance-factory-templates.md`](./plan-instance-factory-templates.md): use existing `registerBlock(blockType, fn, variant)` overload (Pattern A); no factory changes required. |
| Migration tooling scope | Retired (Task 7) | Sketch in [`builder/base/plan-migration-tool.md`](./plan-migration-tool.md): hybrid sed-script + manual review; ~1–2 person-weeks per project. |
| C++20 modules + Verilator-generated headers interop | Retired (Task 8) | Sniff test in `proto/model/test/test_modules_with_verilator_headers.cpp` compiles cleanly. |

## Not Validated in P0 / Deferred

All items originally listed here have been resolved by the deferred-task pass tracked in [`p0-deferred-tasks.md`](./p0-deferred-tasks.md) and rolled up into [§ Risks Retired](#risks-retired). The few items that remain are *explicitly* re-deferred with rationale below.

| Item | Status | Rationale |
|------|--------|-----------|
| **Address-decode worst-case sizing** | Re-deferred to Steps 11–12 of `plan-parameterizable-config-template.md`. | R4 validated only the *named-constant substitution* path. Cumulative-offset-from-`maxBitwidth` and `hwRegister<N>`-from-`maxBitwidth` are register-set generator concerns out of P0 scope; they will be exercised when a register set with parameterizable structures lands. |
| **SV-2012 parameterized packages** | Explicitly deferred per [`plan-sv-parameterization.md`](./plan-sv-parameterization.md). | Out of scope for this generator; revisit only if EDA tool coverage materially improves. |
| **R5 (reserved)** | Out of P0 scope by design. | The slot was reserved for a co-simulation TB integration item and intentionally left empty; the cosim work itself is a separate Phase. |

All P0 deferred items closed as of 2025. Phase 2 foundation work (F1–F3, A1–A3) may begin.

## Closure of Umbrella Plan Open Questions

Mapping P0 outcomes to the open questions in `plan-ip-namespaces-and-parameterization.md` §11:

| Open Question | P0 Outcome |
|---------------|-----------|
| #1 — Shared type namespaces and parameterization boundary | **Not addressed.** P0 used a flat `isp` module/package; shared-vs-IP boundary still needs schema-level definition. |
| #2 — SV parameterization strategy | **Partially closed.** Separate-packages-per-instance and module-level-parameters approaches both validated (R1–R3, R6). Parameterized packages and generate blocks remain unexplored. |
| #3 — `maxBitwidth` compound cases | **Partially closed.** `bayer_pixels_per_clock_t<Config>` exercises array-of-parameterizable-element pack/unpack; works correctly. Compound case where both `arraySize` and element bitwidth are parameterizable was not constructed. |
| #4 — SystemC template compatibility | **Closed.** V1–V3 retire the SC_MODULE/SC_THREAD/sc_trace concerns. Signal/channel binding with template port types confirmed (V2). |
| #5 — C++ module + SystemC interop | **Closed.** V5–V7 retire this. Global module fragment pattern with `module; #include "systemc.h";` works as documented. |
| #6 — `instanceFactory` with templates | **Closed by [`plan-instance-factory-templates.md`](./plan-instance-factory-templates.md).** Existing string-keyed factory used as-is, with `(blockType, variant)` registrations per `(IP, Config)` pair. |
| #7 — Migration tooling scope | **Closed by [`plan-migration-tool.md`](./plan-migration-tool.md).** Hybrid sed-script + manual review; ~1–2 person-weeks per project of typical size. |

## Implications for `plan-development-ordering.md`

P0 validated both the modules and templates legs of Option 4 (combined modules + Config templates) and uncovered no toolchain incompatibilities that would force a fallback. Specifically:

- The combined module-interface-unit + templated-`SC_MODULE` pattern (V7) compiles and simulates with the project's Clang/SystemC stack. The ordering plan's P0 prerequisite for Option 4 is satisfied.
- The Option 2 fallback ("templates first on headers, modules later") is not required — modules did not introduce blocking issues.
- The build-system cost (`-fmodule-file=` flag propagation through dependency chains) is real but tractable; this lands as M4 in the ordering plan and is not a deferral trigger.
- The hand-written-code migration risk that Option 4 was designed to minimize has been *scoped* by Task 7 (see [`builder/base/plan-migration-tool.md`](./plan-migration-tool.md)): for a typical project the migration is ~1–2 person-weeks of work using a hybrid sed-script + manual-review approach, with a clear escalation path to libTooling if the IP count grows.

**Net recommendation:** Proceed with Option 4 as written. The P0 outcome supports the recommendation, and the post-P0 deferred-task pass closes the items that were originally flagged as the largest unquantified risks: the `instanceFactory` strategy is a no-change extension of the existing factory, the multi-word `_packedSt` path is validated by V8, and the migration tool sketch puts the `[M3+T6]` step at ~1–2 person-weeks for a typical project rather than the previously-unbounded estimate. Phase 2 foundation work (F1–F3, A1–A3) may begin.
