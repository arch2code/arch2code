# Implementation Plan: Foundation + Address Decode (F1-F3, A1-A3)

**Status:** historical. The foundation phase is marked done in
`plan-development-ordering.md` for P0, F1, F2, F3, A1, A2, and A3.
Use `plan-f2-f3-design.md` for the detailed F2/F3 design record.

This is the first real generator change phase, following the completed P0 proof-of-concept (`plan-p0-proof-of-concept.md`) that validated all 7 risks. It implements Option 4 from `plan-development-ordering.md`.

## Related Plans

| Plan | Relevant Sections |
|------|-------------------|
| `plan-development-ordering.md` | Work item definitions F1-F3, A1-A3; dependency graph; Option 4 recommendation |
| `plan-parameterizable-config-template.md` | Steps 1-3 (schema, processing, propagation); Steps 11-12 (address sizing, named constants) |
| `plan-ip-namespaces-and-parameterization.md` | Section 4.2 (P1 infrastructure); Section 5 (Address Decoding Impact) |
| `plan-p0-proof-of-concept.md` | Completed — all 7 validations pass (Clang 20.1.8, SystemC 2.3.4, C++23) |

## Phase Overview

This phase delivers two things:

1. **Foundation infrastructure** (F1-F3): Schema and processing support for `ipParameters`, transitive `isParameterizable` propagation, and worst-case address sizing via `maxBitwidth`/`maxValue`. These are additive — no generated output changes for projects without `ipParameters`.

2. **Address decode text-stability** (A1-A3): Replace hardcoded hex literals in SC model and SV RTL decode logic with named constants. This applies to **all blocks** (not just parameterizable), improves readability, and makes the decode logic text-stable for future parameterization.

### Dependency Chain

```
F1 (schema) -> F2 (propagation) -> F3 (worst-case sizing)
                                        |
                                   A1 + A2 + A3 (parallel)
```

A1, A2, A3 are independent of each other and can be done in parallel after F3.

**Note on ordering flexibility:** A1 and A2 (named-constant refactoring) are technically safe to implement before F3 since the named constants already exist with correct values for non-parameterizable blocks. However, implementing them after F3 ensures that the constant values reflect worst-case sizing from the start, avoiding a two-step value change if someone adds `ipParameters` between A1 and F3. The plan follows the stated dependency ordering.

---

## Work Item Details

### F1: Schema — `ipParameters`, `maxBitwidth/maxValue`

**Files:** `builder/base/config/schema.yaml`, `builder/base/pysrc/processYaml.py`

The `ipParameters` section does NOT define its own schema. Instead, it acts as a container whose sub-sections (`constants`, `types`) are processed through the existing schemas for those sections. This follows the same reuse philosophy as `_mapto` (e.g., `enums: _mapto: types`) but for a nested container.

**Changes:**

#### F1a: Extend existing `constants` node (~line 69) with a new optional field

```yaml
constants:
  constant: key
  value: eval
  desc: required
  maxValue: optional(0)       # NEW — worst-case max value for parameterizable constants
  valueType:
    _type: optional(uint)
    _validate:
      values:
        - uint
        - int
        - real
```

#### F1b: Extend existing `types` node (~line 90) with a new optional field

```yaml
types:
  _attribs: [post(validateTypeWidth)]
  type: key
  desc: required
  isSigned: optional(false)
  maxBitwidth: optional(0)    # NEW — worst-case max bitwidth for parameterizable types
  enum:
    # ... unchanged ...
  width: optionalConst()
  widthLog2: optionalConst()
  widthLog2minus1: optionalConst()
```

#### F1c: Register `ipParameters` as a custom section in processYaml

In `processYaml.py`, add `'ipParameters'` to the `customSections` set (line 2179) and implement a `_process_ipParameters` handler. No schema entry is needed for `ipParameters` itself — the handler bypasses schema validation and delegates to existing section schemas.

**Processing loop change** (`processSingleFile`, ~line 2816-2827): Reorder the section dispatch so `customSections` is checked before the schema check. Currently, custom sections must have a schema entry to pass the gate. With the reorder, custom handlers are invoked directly:

```python
# Current:
if section not in self.ignoreSections:
    if (section in self.schema.data['schema']):       # schema gate
        if section in self.customSections:              # custom check inside
            ...
        else:
            self.processSection(section, sectData, contextFile)
    else:
        printError(f"Unknown section: {section}...")

# New:
if section not in self.ignoreSections:
    if section in self.customSections:                  # custom check first
        funct = '_process_'+ section
        getattr(self, funct)(sectData, contextFile)
    elif (section in self.schema.data['schema']):       # then schema check
        self.processSection(section, sectData, contextFile)
    else:
        printError(f"Unknown section: {section}...")
```

This is a safe refactor — `connections` (the only current custom section) exists in both `customSections` and the schema, so it still hits the custom handler first. The only difference is that custom sections no longer require a schema entry.

**The handler** treats `ipParameters` contents like sections from another YAML file:

```python
def _process_ipParameters(self, data, yamlFile):
    """Process ipParameters by routing sub-sections through existing schemas.
    
    ipParameters:
      constants:        # processed via existing 'constants' schema
        BITS_PER_PIXEL_COLOR:
          value: 8
          maxValue: 16
          desc: "..."
      types:            # processed via existing 'types' schema
        pixel_t:
          width: BITS_PER_PIXEL_COLOR
          maxBitwidth: 16
          desc: "..."
    """
    for section, sectData in data.items():
        if section in self.schema.data['mapto']:
            section = self.schema.data['mapto'][section]
        if section in self.schema.data['schema']:
            # Snapshot existing keys to identify new entries
            existing_keys = set(self.data[section].get(yamlFile, {}).keys())
            # Process through normal section pipeline — same schema, same validation
            self.processSection(section, sectData, yamlFile)
            # Stamp new entries as parameterizable
            new_keys = set(self.data[section].get(yamlFile, {}).keys()) - existing_keys
            for key in new_keys:
                self.data[section][yamlFile][key]['isParameterizable'] = True
        else:
            printError(f"Unknown sub-section '{section}' in ipParameters in {yamlFile}")
            exit(warningAndErrorReport())
```

**Why this approach:**
- Zero schema duplication — `ipParameters.constants` uses the exact same field definitions as regular `constants`
- The `maxValue` and `maxBitwidth` fields are optional on the base schemas (default 0). Regular constants/types ignore them; `ipParameters` entries use them.
- Entries from `ipParameters` are merged into the same `self.data['constants']` and `self.data['types']` dictionaries as regular entries. The `isParameterizable` flag distinguishes them.
- Users can also set `maxValue`/`maxBitwidth` directly on regular constants/types outside of `ipParameters` — the propagation pass (F2) will detect `maxValue > 0` or `maxBitwidth > 0` and mark them as parameterizable too.
- The handler supports `_mapto` aliases (e.g., `enums:` inside `ipParameters` maps to `types`).

**Backward compatibility:** Existing YAML files have no `ipParameters` section. The new optional fields (`maxValue`, `maxBitwidth`) default to 0. No existing projects are affected.

**Validation (enforced in F2d):**
- Entries stamped `isParameterizable` must have `maxValue > 0` (constants) or `maxBitwidth > 0` (types)
- Resolved values must not exceed declared maximums

---

### F2 + F3 — see `plan-f2-f3-design.md`

The detailed implementation design for F2 (transitive propagation of
`isParameterizable`) and F3 (worst-case address sizing) lives in
**[`plan-f2-f3-design.md`](plan-f2-f3-design.md)**. That document is the
authoritative source for: schema additions required beyond F1, the
correctness-by-construction methodology and its three invariants, the
per-handler stamping points in `processYaml.py`, the F3a SQL JOIN +
sizing change, the F3b `maxBytes` surfacing, the `ip_test` fixture
deltas, and the verification checklist.

The remainder of this document covers the broader foundation phase
(P0 wrap, A1/A2/A3 template-side work, phase-level risks, and success
criteria).

---

### A1: Named Constants for Address Offsets in SC Decode

**Files:** `builder/base/templates/systemc/blockRegs.py`, `builder/base/templates/systemc/constructor.py`

**Design decision:** Generate function-local `constexpr` constants in the generated constructor body. This keeps the documentation constants scoped to the decode logic that uses them. The existing `#define` macros in `regAddresses.h` remain unchanged for firmware use.

**Changes (3 parts):**

#### A1a: Generate named constants in blockRegs body (`blockRegs.py`)

In the blockRegs constructor body template, emit function-local `constexpr` constants for each register and memory offset:

```cpp
// Generated register/memory address offsets
constexpr uint64_t REG_ADDR_DEBAYER_BAYER_PATTERN = 0x0;
// For memories:
constexpr uint64_t REG_ADDR_BLOCKB_BLOCKBTABLE1 = 0x0;
```

**Implementation in `get_hwregs()` (~line 45-91):**
- Compute the named constant name: `REG_ADDR_{BLOCK}_{REGISTER}` or `REG_ADDR_{BLOCK}_{MEMORY}` (uppercase), avoiding collision with existing firmware `REG_*` macros.
- Add a `const_name` field to each hwregs entry.

**In the body Jinja template:**
- Add a section at the top of the generated constructor body that emits `constexpr uint64_t` for each register/memory offset.

#### A1b: Reference named constants in blockRegs body (`blockRegs.py`)

Change `addRegister` and `addMemory` calls to reference the named constants:

```cpp
// Current:
regs.addMemory( 0x0, bigSt::_byteWidth, BSIZE, "blockBTable1", &blockBTable1_adapter);
regs.addRegister( 0x140, 1, "rwD", &rwD );

// New:
regs.addMemory( REG_ADDR_BLOCKB_BLOCKBTABLE1, bigSt::_byteWidth, BSIZE, "blockBTable1", &blockBTable1_adapter);
regs.addRegister( REG_ADDR_BLOCKB_RWD, 1, "rwD", &rwD );
```

**Implementation:** In `get_hwregs()`, replace `hex(inst['offset'])` with the named constant name.

#### A1c: Reference named constants in constructor (`constructor.py`)

Change `addRegister`/`addMemory` calls (~lines 223-232):

```cpp
// Current:
regs.addRegister( 0x0, 1, "bayer_pattern", &bayer_pattern );

// New:
regs.addRegister( REG_ADDR_DEBAYER_BAYER_PATTERN, 1, "bayer_pattern", &bayer_pattern );
```

**Implementation:** In `constructorBody()`, compute the same `REG_ADDR_{BLOCK}_{REGISTER}` name, emit a function-local `constexpr`, and use it instead of `0x{offset:0x}`.

**Note on address mask:** The `registerHandler` mask (`(1<<(N))-1` at ~line 42) uses `addressBits` which is already correct for non-parameterizable blocks. For parameterizable blocks (after F3), `addressBits` will be computed from worst-case sizes. The mask expression format does not need to change — the `addressBits` value is computed in processYaml, not in the template.

---

### A2: Named Constants for Address Offsets in SV Decode

**Files:** `builder/base/templates/systemVerilog/moduleRegs.py`

**Design decision:** Generate module-local `localparam` register address constants inside the generated moduleRegs module. This keeps decode documentation scoped to the generated decode logic and avoids exporting extra package symbols.

**Changes (2 parts):**

#### A2a: Generate `localparam` register address constants in moduleRegs (`moduleRegs.py`)

Add register/memory address `localparam` constants to the generated register decode module:

```systemverilog
// Register address offsets
localparam int unsigned REG_DEBAYER_BAYER_PATTERN = 32'h0000_0000;
// Memory address offsets (base and size)
localparam int unsigned REG_BLOCKB_BLOCKBTABLE1 = 32'h0000_0000;
localparam int unsigned REG_BLOCKB_BLOCKBTABLE1_SIZE = 32'h0000_0080;
```

**Implementation:** Add a new section to `moduleRegs.py` that iterates over `data['registers']` and `data['memories']` after the existing preprocessing step.

#### A2b: Reference named constants in moduleRegs case statements (`moduleRegs.py`)

Change case match values:

```systemverilog
// Current:
32'h0 : begin

// New:
REG_DEBAYER_BAYER_PATTERN : begin
```

**Implementation:** In `section_02b_regs()` (~line 269) and `section_03b_regs()` (~line 385), replace `f"32'h{o:x}"` with the named constant reference. The segment generator (`segment_register_gen`) already provides the offset — compute the named constant name from the register data.

For multi-segment registers (wider than 32 bits), the offsets are `base + 0`, `base + 4`, etc. The constant name covers the base offset; additional segments use arithmetic: `REG_BLOCKB_RWD + 32'd4`.

For memory address ranges (using `inside`), use the named constants:

```systemverilog
// Current:
[32'h0:32'h7f] : begin

// New:
[REG_BLOCKB_BLOCKBTABLE1 : REG_BLOCKB_BLOCKBTABLE1 + REG_BLOCKB_BLOCKBTABLE1_SIZE - 1] : begin
```

---

### A3: `hwRegister<N>` Worst-Case Sizing

**Files:** `builder/base/templates/systemc/blockRegs.py`, `builder/base/templates/systemc/classDecl.py`

**Changes:**

In `get_hwregs()` (~line 82-83) and direct model block register declaration generation, when the register's structure is parameterizable, use `maxBitwidth` to compute `size_rounded` instead of the resolved `bytes`:

```python
# Current:
"size_rounded": roundup_multiple(inst['bytes'], 4),
"size": inst['bytes'],

# New:
effective_bytes = inst.get('maxBytes', inst['bytes'])  # maxBytes set by F3b
"size_rounded": roundup_multiple(effective_bytes, 4),
"size": inst['bytes'],  # runtime size stays at resolved value
```

Only `size_rounded` (the template parameter `N` for `hwRegister<N>`) uses the worst-case value. The runtime `size` argument to `addRegister()` stays at the resolved value. The template parameter is the critical one because it determines the `sc_bv<N*8>` storage.

For non-parameterizable blocks: `maxBytes` will not be set, so `inst.get('maxBytes', inst['bytes'])` falls back to the current value. Zero behavioral change.

---

## File-by-File Change Summary

| File | Work Item | Changes |
|------|-----------|---------|
| `config/schema.yaml` | F1, F2, F3 | F1: `constants.maxValue`, `types.maxBitwidth`. F2/F3: `isParameterizable` on constants/types/structures, `structures.maxBitwidth`, `memories.isParameterizable`, `registers.isParameterizable`, `registers.maxBytes` (see `plan-f2-f3-design.md`) |
| `pysrc/processYaml.py` | F1, F2, F3 | F1: `_process_ipParameters`. F2: in-handler stamping (`_constants`, `_post_validateTypeWidth`, new `_auto_struct{IsParameterizable,MaxBitwidth}`, new `_auto_{mem,reg}IsParameterizable`, new `_auto_regMaxBytes`). F3: worst-case path in `calcAddresses` and `maxBytes` surfacing in register dict builders |
| `templates/systemc/blockRegs.py` | A1, A3 | Generate function-local `constexpr` named constants in constructor body; reference them in `addRegister`/`addMemory`; worst-case `size_rounded` |
| `templates/systemc/classDecl.py` | A3 | Use `maxBytes` for direct model block `hwRegister<N>` sizing |
| `templates/systemc/constructor.py` | A1 | Reference named constants in `addRegister`/`addMemory` |
| `templates/systemVerilog/moduleRegs.py` | A2 | Generate module-local address `localparam`s and reference them in `case` statements |

---

## Testing Strategy

### Test Fixture

Create a test fixture in `builder/base/examples/` with `ipParameters` declarations. This keeps the debayer project unchanged while enabling end-to-end validation.

**Recommended approach:** Extend an existing example (e.g., `apbDecode`) with an `ipParameters` section in the YAML. The `apbDecode` example is ideal because it has multiple registers and memories, address decode logic, and both SC model and SV RTL generated code.

Add to the test fixture YAML:
```yaml
ipParameters:
  constants:
    SOME_WIDTH:
      value: 8
      maxValue: 16
      desc: "Parameterizable width for testing"
  types:
    test_data_t:
      width: SOME_WIDTH
      maxBitwidth: 16
      desc: "Parameterizable type for testing"
```

### Test Sequence

| Step | What | How | Validates |
|------|------|-----|-----------|
| 1 | Schema parsing | `make db` on the test fixture with `ipParameters` | F1 — schema accepts new fields |
| 2 | Propagation | `make db`, inspect SQLite database for `isParameterizable` flags | F2 — transitive propagation |
| 3 | Address sizing | `make db`, inspect computed register offsets/sizes | F3 — worst-case sizing |
| 4 | SC named constants | `make gen` on debayer and test fixture, diff generated code | A1 — hex literals replaced with named constants |
| 5 | SV named constants | `make gen` on debayer and test fixture, diff generated RTL | A2 — hex literals replaced with named constants |
| 6 | hwRegister sizing | `make gen` on test fixture, inspect `hwRegister<N>` template params | A3 — worst-case N |
| 7 | SC model runs | `make run` on debayer (behavioral regression) | A1 — named constants are functionally correct |
| 8 | SV lint | `make lint` in RTL directory | A2 — SV syntax correct |
| 9 | Example runs | `make run` on all examples in `builder/base/examples/` | Regression — nothing broken |

### Backward Compatibility Verification

- Run `make gen` on the debayer project (which has no `ipParameters`). The only output changes should be A1/A2 (hex to named constants). No structural changes.
- Run `make run` on the debayer project — must produce identical simulation results.
- Run `make gen` on all existing examples — verify no unexpected changes beyond the named-constant refactoring.

---

## Implementation Order

| Order | Work Item | Effort | Risk | Breaking? |
|-------|-----------|--------|------|-----------|
| 1 | **F1** — Schema changes | Small | Low — additive fields, backward compat | No |
| 2 | **F2** — ipParameters processing + propagation | Medium | Medium — new processing logic, dependency graph traversal | No |
| 3 | **F3** — Worst-case address sizing | Small | Low — guarded by `isParameterizable` check | No |
| 4 | **A1** — SC named constants | Medium | Low — straightforward template changes, functionally equivalent | Yes — generated SC code changes format |
| 5 | **A2** — SV named constants | Medium | Low — straightforward template changes | Yes — generated SV code changes format |
| 6 | **A3** — hwRegister worst-case sizing | Small | Low — only affects parameterizable blocks | No (for existing projects) |

**Recommended commit grouping:**
1. F1 (schema only)
2. F2 (processYaml propagation)
3. F3 + A3 (worst-case sizing — closely related)
4. A1 (SC named constants)
5. A2 (SV named constants)

A1 and A2 are independent and can be done in either order or in parallel.

---

## Design Decisions

### `constexpr` vs `#define` for SC constants

**Decision:** Use function-local `constexpr uint64_t` in the generated constructor body, not `#define` macros.

**Rationale:**
- Type-safe, scoped, debugger-visible.
- Consistent with modern C++ practice.
- The existing `#define` macros in `regAddresses.h` remain unchanged for firmware use.
- Both have the same values — no inconsistency.

### SV register address constant location

**Decision:** Generate `localparam` constants inside the generated register decode module.

**Rationale:**
- Constants are scoped to the decode logic that uses them.
- No new file, package symbol, or import dependency is needed.
- Matches the documentation-only intent of these names.

### Memory address constants for SV

**Decision:** Generate both base offset and size constants for memories:

```systemverilog
localparam int unsigned REG_BLOCKB_BLOCKBTABLE1 = 32'h0000_0000;
localparam int unsigned REG_BLOCKB_BLOCKBTABLE1_SIZE = 32'h0000_0080;
```

This enables the `inside` range pattern to be fully symbolic.

### Named constant scope

**Decision:** Apply to all blocks, not just parameterizable ones.

**Rationale:** Improves readability universally and avoids inconsistency between parameterizable and non-parameterizable blocks.

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Named constant naming collisions | Low | Register and memory names are unique within a block by YAML schema constraint |
| Multi-segment register constants (SV) | Low | Use arithmetic: `REG_NAME + 32'd4` for additional segments |
| Propagation complexity for deep nesting | Low | Correctness-by-construction in-handler stamping (see `plan-f2-f3-design.md`); references resolve via existing file-dependency ordering. |
| Test fixture maintenance | Low | Extend existing example rather than creating new one |
| SV `case` expression compatibility | Low | `localparam` + literal arithmetic is standard SV |

---

## What This Phase Does NOT Include

Per the development ordering plan, these items are deferred to the combined Modules + Config Templates phase:

- C++ module generation (M1-M5)
- Config template types/structs (T1-T8)
- SV per-instance packages (S1-S2)
- Config struct generation (Step 4 of parameterizable plan)
- Any hand-written IP code changes
- Runtime `static_assert` validation (Step 13)

The Foundation + Address Decode phase is purely infrastructure and refactoring — it adds schema/processing capabilities and improves generated code quality without changing any hand-written IP code.

---
## Success Criteria

1. **F1-F3:** A test fixture with `ipParameters` processes through `make db` without errors, with correct `isParameterizable` propagation and worst-case address values in the database.
2. **A1:** All generated SC `addRegister`/`addMemory` calls reference named `constexpr` constants instead of hex literals. `make run` passes on debayer and all examples.
3. **A2:** All generated SV register decode `case` statements reference named `localparam` constants instead of hex literals. `make lint` passes.
4. **A3:** For the test fixture with parameterizable registers, `hwRegister<N>` uses worst-case byte size. For non-parameterizable blocks, `N` is unchanged.
5. **Backward compatibility:** No behavioral changes to any existing project. Only format changes (hex to named constant) in generated output.
