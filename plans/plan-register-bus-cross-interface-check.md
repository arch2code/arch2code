# Plan: Cross-Interface Compatibility Check for the Synthesised Register Bus

## Current Status

- **Classification (reconciled 2026-07-24):** core implementation complete;
  minor design follow-ups deferred.
- **Status taxonomy:** committed and verified for E3.1/E3.2.
- **Current state:** `postParseRegisterPorts.py::checkInterfacePair()` performs
  the shared router/leaf and nested-router compatibility check, with focused
  E3.1/E3.2 coverage in the completed Stage 7 matrix.
- **Parent context:** `plan-address-control-refactor.md` remains the address
  refactor parent. The implementation sections below are retained as the design
  record, not as pending generator instructions.

Companion to [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md)
and [`plan-address-control-refactor.md`](./plan-address-control-refactor.md).
This document is a placement decision for the `E3.1` / `E3.2`
validation work named in the test plan. It does not change what is
checked; it decides where the check lives.

## Problem Statement

The new register-bus path synthesises a router-to-leaf connection per
routed-leaf instance, and a parent-router-to-child-router connection
per nested router. Both sides have explicit interfaces:

- Router side: the interface resolved from the router block's
  `addressBlock.upstreamPort` port name.
- Leaf side: the leaf block's `registerPorts:` row (a single row, by
  Stage 1.5 schema rule).
- Nested-router upstream side: the interface resolved from the nested
  router's own `addressBlock.upstreamPort` port name.

These two interfaces must be packed-form compatible under the bound
variant, exactly as the existing user-authored cross-interface bind
check requires (same `interfaceType`, paired structures, per-field
name / width / offset). Today, nothing performs that check for the
register-bus relationship:

- `validatePorts()` walks user-authored connections and anchors its
  cross-interface check on the child block's `ports:` declaration
  (`pysrc/processYaml.py:4368-4376`). A routed leaf declares its
  register-bus surface in `registerPorts:`, not in `ports:`, so the
  anchor is absent and the check returns early.
- `config/postParseRegisterPorts.py` synthesises the connection from
  the two sides but does not currently verify that they are
  packed-form compatible.

The result is that an incompatibility surfaces only as a downstream
template or build failure on the generated code, not as an
arch2code diagnostic naming the offending leaf, router, and field.

## Related Documents

| Document | Relevance |
| -------- | --------- |
| [`plan-address-control-refactor.md`](./plan-address-control-refactor.md) | Parent refactor; Stage 5 owns post-parse validation. |
| [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md) | Names E3.1 / E3.2 and their required diagnostic substrings. |
| [`config/postParseRegisterPorts.py`](./config/postParseRegisterPorts.py) | Synthesises the router-to-leaf and router-to-router register-bus connections. |
| [`pysrc/processYaml.py`](./pysrc/processYaml.py) | Contains the existing cross-interface check (`validatePorts._checkPair`, line 4226). |

## Options Considered

### Option A: extend `validatePorts()` with a register-bus walk

- Add a second iteration in `validatePorts()` that walks the
  synthesised register-bus connections (owner context, not `_global`)
  and anchors on the leaf's `registerPorts:` row instead of `ports:`.
- Reuse the existing nested `_checkPair` directly.
- Trade-off: keeps all cross-interface validation in one method but
  splits ownership of the register-bus relationship across two files
  (`postParseRegisterPorts.py` builds the connection;
  `validatePorts()` checks it). A post-hoc complaint about a row that
  the script already emitted is less actionable than a synthesis-time
  refusal.

### Option B: validate inside `postParseRegisterPorts.py` at synthesis time (recommended)

- Extract `_checkPair` (and its supporting helpers
  `_walkStructFields`, `_resolveTypeWidth`, `_resolveConstValue`,
  `_resolveArraySize`, `_structureRows`) from inside `validatePorts()`
  into a module-level or class-level helper.
- `validatePorts()` continues to call the extracted helper for
  user-authored connections and connectionMaps.
- `postParseRegisterPorts.py` calls the same helper for each
  synthesised router-to-leaf and router-to-router pair before
  emitting the connection.
- Trade-off: requires one extraction step in `processYaml.py`; in
  exchange, the script that owns the synthesis also owns the
  compatibility gate, and the diagnostic can include the synthesis
  context (leaf instance key, router instance key, the
  `registerPorts:` row name) which `validatePorts()` does not see.

The recommendation is Option B. The duplication concern is fully
addressed by the helper extraction: the per-pair check is written
once; only the iteration that finds pairs to check differs between
callers (user-authored connections versus synthesis targets).

## Recommended Approach (Option B)

### Step 1 — extract the helper

- Pull the nested function `_checkPair` from
  `pysrc/processYaml.py:4226-4341` out to a class method
  `checkInterfacePair(self, parentIfaceKey, childIfaceKey,
  childBlockKey, childVariant, locationStr, parentContext,
  childContext, parentBlockKey='', parentVariant='')`.
- Pull its supporting nested helpers (`_walkStructFields`,
  `_resolveTypeWidth`, `_resolveConstValue`, `_resolveArraySize`,
  `_structureRows`, `_resolveInterfaceDef`) into private methods or
  module-level functions that the new public method calls.
- Move the flattening of `interfaces_flat`, `interface_defs_flat`,
  `structures_flat`, `constants_flat`, `types_flat`, and
  `variant_overrides` into the class so the helper can read them
  without each caller rebuilding them. The flattening is a fixed
  function of `self.data` and the `parametersvariants` table; doing
  it once is correct.
- Keep `validatePorts()`'s existing iteration intact; replace its
  inline `_checkPair` call with `self.checkInterfacePair(...)`.
- Verify: `unittest/run_all_tests.sh` green; no behaviour change for
  any existing user-authored cross-interface case.

### Step 2 — call the helper from `postParseRegisterPorts.py`

- In the router-to-leaf synthesis loop (around the existing Step 5),
  resolve the parent qualified interface key from the router block's
  `addressBlock.upstreamPort` port name and the child qualified
  interface key from the leaf's `registerPorts:` row. The helper needs
  both qualified keys; the existing post-parse code already resolves
  the router-side unqualified interface through
  `_resolveRouterRegisterBusInterface(...)` and can preserve or return
  the qualified form through the same context lookup.
- Compute the child binding from the leaf instance's `variant` (the
  helper already supports `''` for non-parameterized leaves).
- Compute the parent binding the same way the existing
  `_connectionBinding` helper does for user-authored connections,
  with the router instance and any parameterizable transit blocks.
- Call `prj.checkInterfacePair(...)` with a `locationStr` that names
  the leaf block, the leaf instance, the router instance, and the
  `registerPorts:` row name. On failure the helper emits the
  diagnostic and the script halts via `warningAndErrorReport()`.
- Repeat for the parent-router-to-child-router synthesis loop, with
  the interface resolved from the child router's
  `addressBlock.upstreamPort` in place of the leaf's `registerPorts:`
  interface.

### Step 3 — pin the diagnostic substrings the tests assert

- `E3.1`: when the two `interfaceType` values differ, `_checkPair`
  emits the existing diagnostic at lines 4242-4250
  ("cross-interface bind requires the same interface meta-protocol
  on both ends, but parent interface ... has interfaceType '...' ...
  while child interface ... has interfaceType '...'"). The
  test fixture asserts the two `interfaceType` values plus the
  protocol-changer guidance. Append the protocol-changer guidance
  sentence to the existing message body so the assertion has a
  stable substring.
- `E3.2`: when packed forms differ, `_checkPair` already emits per
  failure category (field count, name, width, offset). The fixture
  asserts both packed-form widths and the offending field name; the
  existing width-mismatch message at lines 4317-4329 already
  includes both `_bitWidth` values and the field name and is a
  suitable assertion target.

### Step 4 — fixtures and gate

- Add `unittest/test_error_register_interface_type_mismatch.py` for
  E3.1 (leaf and router resolve to different `interfaceType`).
- Add `unittest/test_error_register_packed_form.py` for E3.2 (same
  `interfaceType`, packed-form mismatch). Use a parameterized leaf
  whose register-bus structure resolves to a different width than
  the router-side structure under the bound variant.
- Register both in `unittest/run_all_tests.sh`.
- Gate: `unittest/run_all_tests.sh` green;
  `examples/ip_test/` builds unchanged (the existing example must
  remain compatible because its leaf and router share the same
  `interfaceType: apb` and packed form).

## Plan-Document Updates

Once the placement is agreed:

- Update the `Current Repository Status` section of
  [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md):
  rewrite the E3.1 / E3.2 prerequisite so it names
  `postParseRegisterPorts.py` (synthesis-time check) and the helper
  extraction from `validatePorts()`, not a new walk inside
  `validatePorts()`.
- Update the parent
  [`plan-address-control-refactor.md`](./plan-address-control-refactor.md)
  Stage 5 description if it currently locates the check inside
  `validatePorts()`.

## Risks

- **Helper extraction is a structural refactor of `validatePorts()`.**
  It must not change the diagnostic strings the existing
  cross-interface tests assert. Mitigation: run `run_all_tests.sh`
  after Step 1 and before any new code is added.
- **Synthesis-time refusal halts before any synthesised row is
  emitted.** This is the intended behaviour, but means that
  downstream rows that would have been emitted are not present for
  any caller that inspects the database after a failed
  `arch2code.py` run. Mitigation: the script already exits via
  `warningAndErrorReport()` on other errors; this case follows the
  same pattern.
- **Parent-binding resolution for the router side may differ from
  `_connectionBinding`'s logic.** The router side is typically a
  non-parameterized router; the helper accepts an empty binding and
  falls back to default constant values. Mitigation: start with
  empty parent binding and only thread a real binding through if a
  fixture requires it.

## Open Questions

- **Should `connectionMaps` synthesised for leaf-to-handler binds
  also be checked?** The handler block's register-bus port is the
  canonical interface (named after the router's
  `registerDecoderPort`). If the leaf's `registerPorts:` interface
  resolves differently from the handler-side interface, today the
  generator silently emits an adapter that may or may not work.
  Recommendation: scope this plan to the router-to-leaf and
  router-to-router connections; treat the leaf-to-handler
  `connectionMap` as a separate question for a follow-up.
- **Where does the protocol-changer guidance sentence belong:
  inside `_checkPair` for all callers, or only in the register-bus
  caller's `locationStr`?** Recommendation: add it inside
  `_checkPair` so user-authored cross-protocol attempts also see
  the same guidance.

## Deferred / Out of Scope

- The leaf-to-handler `connectionMap` compatibility check (see Open
  Questions).
- E3.3 and E3.4, which the test plan covers separately and which do
  not require validator extension.
- Any change to the legacy `addressControl.yaml` path; that path's
  `_global`-tagged rows remain exempt from `validatePorts()` exactly
  as today.
