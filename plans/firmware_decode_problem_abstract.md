# Abstract: Firmware-accessible register/memory decode in a hierarchical arch2code DUT

> **STATUS (2026-06-24): corrected against the current toolchain (`yamlFormat: 2`).**
> This was a post-mortem from an older toolchain. Two findings below are now
> obsolete and several framings were over-stated:
> - **P5/P6 are fixed.** `make newmodule` auto-selects the `apbDecodeModule`
>   template for `addressBlock:` blocks (no manual template switch), and a
>   synthesizable `<block>_regs` is generated for blocks with registers **or**
>   `regAccess` memories (register-only blocks DO get one).
> - **The "leaf-ownership invariant" was wrong** and has been removed. A
>   container block MAY own registers/memories; the real constraint is the
>   decoder-position rule (a block must be served by a sibling/parent decoder and
>   is never decoded by a decoder it contains). The Debayer project is the
>   canonical container-owns-registers example.
> - The decoder is a **generated `addressBlock:` block**, not a manual top-level
>   module. The canonical, current guidance lives in the
>   **Register/Memory Decode** skill (`design-register-decode.md`); prefer it
>   over this historical document.

This document generalizes the implementation-specific lessons in
`apb_register_decode_lessons.md` into a framework-level problem definition. The goal is to
produce material suitable for improving the agent skills (primarily the new
`design-register-decode`, plus `manage-address-space`, `rtl-registers`, and
`design-architecture`), independent of any single design.

---

## 1. The problem, stated abstractly

Given a DUT composed of nested blocks holding firmware-visible state (registers and
memories), make that state reachable from a register bus (for example APB) through a
**synthesizable, framework-generated decoder**, using only YAML configuration and the
standard generation flow. State may live on a leaf sub-block **or on a container block**
(forwarded to children via `registerConnections`); the requirement is that whichever block
owns it is served by a sibling/parent decoder, never by a decoder it contains.

The problem is structural, not behavioral. The difficulty is not writing logic; it is declaring
the design so that the framework can recognize the decode hierarchy and auto-wire it. Most
failure modes are misconfigurations that surface as generator crashes or missing artifacts, and
they are resolved by changing declarations, not by authoring RTL or bus plumbing by hand.

---

## 2. The mental model the agent was missing

The recurring root cause was the absence of a correct model of how the framework decodes. The
abstract model has four invariants:

* **Co-location invariant.** A decoder (router) instance and every register/memory-bearing
  instance it serves must share a single container block. Decode cannot cross a container
  boundary; a router serves its siblings (and nested routers) and never decodes its own
  container block.
* **Decoder-as-generated-block invariant.** The decoder is a first-class block that the
  framework generates: a block with a populated `addressBlock:`, whose RTL comes from the
  `apbDecodeModule` template (auto-selected by `make newmodule`). It is not hand-written RTL
  and it is not a manual top-level module.
* **Decoder-position rule (replaces the retracted "leaf-ownership invariant").** A block that
  owns registers/memories must be served by a sibling/parent decoder. A container block MAY
  own registers (e.g. config registers forwarded to children via `registerConnections`); the
  only failure is a block owning registers with **no** decoder serving its container —
  classically a block holding the *only* decoder *inside itself*.
* **Auto-wiring invariant.** Once routers (`addressBlock:`) and routed leaves are declared and
  co-located, the entire register-bus fan-out below the primary router is synthesized
  (including nested-router feeds). You author only the upstream feed into the primary router;
  any other manual bus connection is a symptom of a broken invariant, not a fix.

A single flag (`regAccess: true`, with `local:` absent) is the intended switch that makes a
memory firmware-accessible. No custom interface is required to expose it.

---

## 3. Failure-mode to root-cause map (diagnostic)

This is the reusable, design-independent diagnostic table. Each observable error maps to the
invariant it violates.

* **"Leaf instance '…' (block '…') is in container '…' which is not served by any router."**
  (current toolchain; replaces the old "same level as decoder" string and the
  `parent_interface_port` crash.)
  * Violation: co-location / decoder-position rule. The routed leaf has no router in its
    container. Classic cause: a block owns registers but holds the *only* decoder *inside
    itself* (that decoder serves the block's children, not the block). Fix: add a router as a
    sibling, or make the owning block a routed leaf of a parent decoder. **Not** a manual
    `connectionMap`.
* **Decoder block generated as an empty skeleton (ports only, no body).**
  * Cause: `make newmodule` ran before `addressBlock:` was present, so the generic template
    was seeded. With `addressBlock:` declared, `make newmodule` selects the `apbDecodeModule`
    template automatically. (The old "manually switch the template" step is obsolete.)
* **Missing module for a register block (a `_regs` module is instantiated but its source file
  does not exist).**
  * Cause (current toolchain): stale generated artifacts or an out-of-date `.gen` cache —
    **not** a register-only limitation. A synthesizable `<block>_regs` is generated for blocks
    with registers **or** `regAccess` memories. Remove orphaned generated files and `.gen`,
    then regenerate.
* **"Block X does not exist in the design" / stale dependency errors after removing a block.**
  * Cause: orphaned generated artifacts and a stale generation cache. Resolution is to remove
    the orphaned generated files and clear the cache before regenerating.
* **Linker or debug-info errors when alternating model and RTL-simulation builds.**
  * Cause: mixed build-mode objects in one build directory. Resolution is a clean build when
    switching modes.

---

## 4. Generalized recipe

To make a sub-block's register/memory state firmware-accessible over a register bus:

1. Mark the memory `regAccess: true` and ensure `local:` is not set.
2. Declare the decoder as a generated router block (a populated `addressBlock:`) and instance
   it in the **same container** as the served sub-blocks.
3. Tag each served sub-block instance with `addressGroup:` naming the router's
   `addressBlock.addressGroup`. (Legacy `addressControl.yaml` projects instead name the router
   via an `AddressGroups` row's `decoderInstance`.)
4. Owning block placement: a leaf may own the state, or a container block may own it and
   forward it to children via `registerConnections` — provided no contained leaf needs its own
   decode block. The only rule is that the owning block is served by a sibling/parent decoder.
5. Author only the upstream feed into the primary router (master→DUT connection, plus a
   DUT-boundary connectionMap when the master is outside the router's container). Everything
   below — including nested-router feeds — is auto-wired.
6. Run the standard database, new-module, and generation steps. `make newmodule` selects the
   `apbDecodeModule` template for the router automatically (no manual template switch).
7. Address firmware accesses as `base + region offset + index * stride`, one bus-width word per
   access.

---

## 5. Generalized rules to encode in skills

1. Read the bundled decoder example before designing any register/memory decode; it is the
   ground-truth structural pattern.
2. Treat generator errors that mention missing blocks, unbound interface ports, or unknown
   blocks as structural YAML misconfigurations first; re-check the four invariants before
   editing RTL or YAML by hand.
3. Never substitute a custom streaming or "load" interface for `regAccess`.
4. Never hand-author decoder demux logic or a manual register-bus connection (beyond the
   single upstream feed into the primary router).
5. Place firmware-visible state on whichever block is served by a sibling/parent decoder. A
   container block may own (e.g. config) registers and forward them to children via
   `registerConnections`; do not invent leaf blocks just to "hold" a register. A contained
   leaf that needs its own decode makes the container a nested-router host (two address
   groups).
6. After removing any block or register, remove orphaned generated artifacts and clear the
   generation cache before regenerating.
7. Use a clean build when switching between model and RTL-simulation build modes.
8. In firmware code (which is not a model module), use the context-form assertion macro rather
   than the module-name form.
9. For multi-word `regAccess` memories, load whole elements; a single bus-width sub-element
   access can round-trip in the model yet mismatch in model/RTL tandem.

---

## 6. Required corrections to current skills

These corrections have been applied to the canonical skills (the new
`design-register-decode` skill is the home for the decode decision rule,
invariants, failure-mode table, and worked examples; `manage-address-space`,
`rtl-registers`, `design-architecture`, and `project-conventions` were corrected
and link to it). For reference, the corrections were:

* The old skills described the top-level decoder as a **manual** module. Corrected: the
  decoder is a **generated `addressBlock:` block** (RTL from `apbDecodeModule`, scaffolded by
  `make newmodule`). Legacy `decoderInstance` is `addressControl.yaml`-only.
* Documented the co-location invariant and the **decoder-position rule** (a routed leaf must
  be served by a sibling/parent decoder; container blocks may own registers). The retracted
  "leaf-ownership invariant" and the "register-only blocks get no `_regs`" limitation are
  **not** carried forward — both are obsolete.
* Documented `regAccess: true` (with `local:` absent) as the single switch for
  firmware-accessible memory, cross-referencing the `apbDecode`/`ip_test` examples.
* Added the failure-mode-to-root-cause table (canonical copy in `design-register-decode.md`).
