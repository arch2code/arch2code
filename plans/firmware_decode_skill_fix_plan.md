# Plan: Correct register/memory decode guidance in canonical skills

Status: **DRAFT for review.** Decision rule corrected (decoder-position, not
leaf-ownership). Arm A baseline eval run (see §8); skill not yet drafted.

## 1. Why

An agent (on an older toolchain) failed to make leaf-block registers/memories
firmware-accessible. The post-mortem is in `apb_register_decode_lessons.md` and
`firmware_decode_problem_abstract.md`. Re-checked against the **current**
toolchain, the situation is:

- The toolchain has moved to the per-block `addressBlock:` / `registerPorts:`
  schema (`yamlFormat: 2`). The decoder/router is a **generated** block
  (`addressBlock:` → `apbDecodeModule` template), auto-scaffolded by
  `make newmodule`, and the register bus is auto-wired.
- Several canonical skills **and** the reference doc they cite still teach the
  old "you must manually create the top-level decoder" model. That is now
  factually wrong and is the root cause the agent could not recover from.
- Two specific old failure modes are already fixed in the toolchain (see §3),
  so guidance that warns about them is obsolete.

The headline product goal: **give agents a clear rule for deciding whether
registers/memories go on a container block or get pushed down to a child leaf.**
The rule is about the **decoder's position**, not a blanket "registers only on
leaves" (see §2 — Debayer is a valid container-owns-registers case).

## 2. Ground truth (verified in this toolchain)

Sources of truth: `builder/base/examples/apbDecode/`, the **Debayer** project
itself (`arch/yaml/debayer.yaml` + `arch/yaml/debayer_tb.yaml`, both
`yamlFormat: 2`), and `builder/base/config/postParseRegisterPorts.py`.

- A block that owns `registers` **or** `regAccess: true` memories is a **routed
  leaf**: it gets a synthesised `<block>_regs` handler and a router→leaf
  dispatch connection (`collectBlocksNeedingRegHandler`, dispatch loop).
- A router is a block with a populated `addressBlock:`. A router instance
  **serves the other instances in its own container** (its siblings) and nested
  routers — it does **not** serve its own container block.
  (`decoderContainer` is keyed by each router instance's `containerKey`.)
- A block that owns registers but whose **container has no decoder serving it**
  fails with: *"Leaf instance '…' (block '…') is in container '…' which is not
  served by any router."* (postParseRegisterPorts.py ~L412-419). This replaces
  the old `parent_interface_port` crash.
- `make newmodule` auto-scaffolds a block with `addressBlock:` using
  `--template=apbDecodeModule` (`builder/base/templates/fileGen/fileGen.py`
  `isApbRouter`), emitting the full synthesizable router.
- **Upstream feed vs. fan-out (authored vs. synthesized).** You hand-author only
  the *external* feed into the **primary** router: the bus-master→DUT
  `connection` plus the DUT-boundary `connectionMap` into the primary router
  instance. (When the master and the primary router share a container — e.g.
  `debayer_tb` — only the `connection` is needed, no `connectionMap`.) Everything
  below the primary router is synthesized: router→leaf dispatch, `<leaf>_regs`
  handlers, and — confirmed in `postParseRegisterPorts.py` ~L535-566 — the
  **parent→child router connection AND the nested-router boundary
  `connectionMap`**. So for nested routers you author **nothing**; over-authoring
  the nested boundary map is wrong.
- **Leaf↔router association** is by **container co-location** (the dispatch loop
  matches a leaf instance's `containerKey` to a router instance in the same
  container); the leaf instance's `addressGroup:` selects the address space/enum
  and must name the serving router's `addressBlock.addressGroup`.
- **Debayer (canonical container-owns-registers case):** block `debayer` owns a
  config register `bayer_pattern` and contains stream leaves
  `u_preprocess`/`u_interpolate` (no registers). `debayer` is itself a routed
  leaf served by its **sibling** `u_apb_decode` (both in `debayer_tb`), and the
  register is forwarded to a child with
  `registerConnections: {register: bayer_pattern, block: debayer, instance: u_interpolate}`.
  This is valid and idiomatic — a single container-level reg block is fine.

### The decision rule (the deliverable text — CORRECTED)

> A block that owns registers or `regAccess` memories is a **routed leaf**: the
> framework synthesises its `<block>_regs` handler and a decoder dispatches to
> it. A decoder serves the **instances in its own container (its siblings)** and
> nested routers — it **never decodes its own container block**. So the question
> is not "container vs leaf"; it is **"is this block served by a sibling/parent
> decoder?"**
>
> - **A container block MAY own registers/memories — provided none of its
>   contained leaves need their own register-decode block** (i.e. no contained
>   sub-block owns registers/`regAccess` memories). In that case the container is
>   simply a routed leaf served by a sibling/parent decoder, and it forwards its
>   own register values to sub-blocks via `registerConnections`. This is the
>   common config-register pattern; **Debayer is the canonical example** — a
>   single container-level reg block is correct (its `u_preprocess`/`u_interpolate`
>   own no registers, so nothing inside `debayer` needs a decoder).
> - **If a contained leaf DOES need a reg-decode block**, a decoder must be
>   instanced *inside* the container to serve that leaf — the container becomes a
>   decoder-host. A decoder-host that also owns registers is the **nested-router
>   case**: the container must itself be a routed leaf of a parent decoder (two
>   address groups). Either nest deliberately, or move the container's registers
>   onto a dedicated child leaf the inner decoder serves.
> - **The failure case** is a block that owns registers but has *no decoder
>   serving its container* — classically the DUT-top block that contains the
>   *only* decoder *inside itself* (that inner decoder serves the top's children,
>   not the top). Fix: add a decoder in the parent/testbench (the block becomes a
>   routed leaf), or move those registers onto a child leaf the inner decoder
>   serves.
>
> `regAccess: true` (with `local:` absent) is the single switch for FW-accessible
> memory. The router RTL is generated (`addressBlock:` → `apbDecodeModule`,
> auto-scaffolded by `make newmodule`); never hand-write it. The register-bus
> **fan-out below the decoder is synthesized**; you still author the upstream
> feed (CPU→decoder connection) and any `registerConnections` that forward a
> block's own registers down to its children.

## 3. Obsolete lessons (do NOT carry forward as warnings)

- **P5** "decoder generates as an empty skeleton; manually switch to
  `apbDecodeModule`." Fixed — `make newmodule` now auto-selects the template.
- **P6 / old Rule 7** "register-only sub-blocks get no synthesizable `_regs`."
  Fixed — `_regs` is now synthesised for blocks with registers **or** regAccess
  memories.
- The `addressControl.yaml` + `AddressGroups` + `decoderInstance` recipe is
  superseded by per-block `addressBlock:` for new work (`decoderInstance`,
  `primaryDecode`, `varTypeContext` no longer migrate).
- The `parent_interface_port` `UnboundLocalError` and the
  "same level as decoder" string no longer exist; structured diagnostics
  replace them.
- **WRONG lesson to discard:** `apb_register_decode_lessons.md` Rule 6 /
  "leaf-ownership invariant" — *"Container/wrapper blocks must not own registers
  or memories."* This is **over-stated and incorrect**. A container block may own
  (config) registers (Debayer). The real constraint is the decoder-position rule
  in §2: the block must be served by a sibling/parent decoder; a block is never
  decoded by a decoder it contains.

## 4. Still-valid invariants (keep / document)

Co-location (a routed leaf and its serving decoder share a container),
decoder-as-generated-block, auto-wiring of the fan-out below the decoder, and
the single `regAccess` switch all still hold. **Do NOT** state a
"leaf-ownership" invariant; replace it with the §2 decoder-position rule
(container blocks may own registers).

## 5. Files to change (canonical sources only)

Edit only under `builder/base/` (a submodule — user stages/commits). Deployed
copies in `.cursor/skills`, `.claude/skills`, `.gemini`, `.opencode`,
`.agents`, and `.cursor/rules/*.mdc` are **regenerated** by
`make cursor-setup` / `make agents-setup`; never hand-edit them.

1. **`builder/base/ARCH2CODE_AI_RULES.md`** (upstream source of the
   misconception). Full rewrite of the affected sections:
   - "Register Decoder Architecture (Critical Understanding)" (~L1681+) —
     remove the "(MANUAL)" top-level decoder model.
   - "Registers & Address Management" / "AddressGroups" / "RegisterBusInterface"
     (~L959, 1272-1418, 1531-1605, 1657-1689) — replace manual-decoder language
     with `addressBlock:` routers + `registerPorts:` leaves, generated
     `apbDecodeModule` RTL, and the §2 decision rule.

2. **NEW `builder/base/rules/skills/design-register-decode.md`** — canonical
   greenfield decode skill (see §7): decision rule, invariants, failure-mode
   table, recipe, `apbDecode` walkthrough.

3. **`builder/base/AGENTS.md.template`** — add "Register/Memory Decode" routing
   row (~L11). Refresh repo-root `AGENTS.md` + `CLAUDE.md` routing tables (they
   are always-applied and already exist).

4. **`builder/base/rules/skills/manage-address-space.md`** — remove "manual
   top-level decoder" (L35, L39-42); keep it scoped to address-policy + FW
   headers; link to the new decode skill.

5. **`builder/base/rules/skills/rtl-registers.md`** — correct prerequisite
   (L15) and "Level 1 (Manual): You implement the top-level decoder" (L20-21) to
   the generated-router reality; note `registerPorts:` for reusable-IP leaves;
   keep `ext`/`ro`/`rw` guidance; link to the new decode skill.

6. **`builder/base/rules/skills/design-architecture.md`** — add `addressBlock:`
   (router blocks) and `registerPorts:` (reusable-IP leaves) field reference;
   state the leaf-ownership rule; link to the new decode skill.

7. **`builder/base/rules/project-conventions.md`** — fix checklist line
   ("Decoders: You MUST manually create the top-level bus decoder") to the
   generated `addressBlock:` router; keep "never hand-create `<block>_regs`".

8. **Sweep** the other canonical skills (`systemc-to-rtl.md`,
   `rtl-to-systemc.md`, `rtl-core.md`, `setup-project.md`,
   `design-yaml-includes.md`) for residual manual-decoder / register-only-`_regs`
   claims and correct any found.

## 6. Propagate & verify

- Regenerate deployed copies: `make cursor-setup` and `make agents-setup`
  (and `agent-dev-setup` if dev skills change).
- Grep canonical + deployed trees for residual `manual decoder`,
  `decoderInstance`, `apb_decode_system`.
- Confirm `builder/base/examples/apbDecode` still matches the documented recipe;
  sanity-run `make db` on it.
- **Required (not optional):** correct `firmware_decode_problem_abstract.md` and
  `apb_register_decode_lessons.md` — mark P5/P6 fixed, restate the recipe in
  `addressBlock:` terms, and **remove the over-stated "leaf-ownership /
  containers must not own registers" framing** (replace with the §2
  decoder-position rule). The Arm A eval (§8) showed this framing actively
  contaminates agent reasoning, so it must not remain in any repo doc.

## 7. Skills structure — DECIDED (Option B)

There is no skill that teaches **greenfield decode-hierarchy design**
(`address-migration.md` is migration-only; `manage-address-space.md` is
policy/FW-header oriented). Decision:

- **New skill `builder/base/rules/skills/design-register-decode.md`** is the
  canonical home for greenfield decode design: the §2 decision rule, the four
  invariants, the **failure-mode → diagnostic table (canonical copy lives
  here)**, the `regAccess`/router/leaf recipe, and a walkthrough of the
  `builder/base/examples/apbDecode` example.
- `design-architecture.md` carries the **field reference** only
  (`addressBlock:`, `registerPorts:`, `regAccess`) and links to the new skill.
- `manage-address-space.md` stays scoped to address-policy + FW headers and
  links to the new skill for decode hierarchy.
- `rtl-registers.md` keeps the RTL-side `ext`/`ro`/`rw` guidance and links to the
  new skill for the router/leaf model.
- ARCH2CODE_AI_RULES.md keeps a short pointer to the new skill's failure table
  rather than duplicating it.

### Registering the new skill (routing)

- Add a routing row to **`builder/base/AGENTS.md.template`** (canonical, ~L11):
  `| **Register/Memory Decode** | design-register-decode.md (...) |`.
- The repo-root `AGENTS.md` and `CLAUDE.md` are always-applied and are only
  generated from the template when absent; this repo already has them, so their
  routing tables must be refreshed too (manual edit or re-run setup with FORCE).
- `make agents-setup` / `make cursor-setup` will deploy the new
  `design-register-decode.md` to all per-tool skill dirs automatically (the
  setup loops over every `rules/skills/*.md`).

## 8. Documentation eval (agent-based) — methodology & findings

The skill/docs are validated by launching live agents on hypothetical
configuration tasks and grading their decisions against a rubric — not by unit
tests. Two arms, same prompts:

- **Arm A′ (baseline):** the *shipped skills only* (with the leak docs below
  excluded). Expected to reproduce the original failures.
- **Arm B (candidate):** the new `design-register-decode` skill as the sole
  added guidance. Expected correct, including the Debayer-shaped H7.

**Eval set (user-voiced hypotheticals, graded by rubric):**

| ID | Scenario | Correct decision |
| --- | --- | --- |
| H1 | DUT-top owns a `status` reg AND contains the only decoder + leaves | Decoder is inside the block, so it does not decode the block → push `status` to a child leaf, or nest a parent decoder. NOT a manual connectionMap. |
| H2 | Make a leaf's memory FW-accessible | `regAccess: true`, no `local:`; leaf served by a sibling decoder; fan-out auto. |
| H3 | Add the decoder/router block | Block with `addressBlock:`, RTL generated (`apbDecodeModule`), scaffolded by `make newmodule`; no hand-written demux. |
| H4 | Connect CPU bus into the hierarchy | Author master→DUT connection + DUT-boundary connectionMap into the primary router only; everything below auto-wired. |
| H5 | Reusable IP needs register access | Author one `registerPorts:` row on the IP; plain leaves omit it. |
| H6 | Nested routers | Two `addressBlock:` routers; subsystem is a routed leaf of the parent; **nested feed auto-wired** (do not author the nested boundary map). |
| H7 | **(Debayer-shaped, discriminator)** container owns config regs, decoder is its **sibling**, sub-blocks have no regs | **Keep the regs on the container**; forward to children via `registerConnections`. Do NOT invent leaf blocks. Catches an over-corrected "registers must be on leaves" skill. |
| H8 | **(boundary discriminator)** container owns config regs AND a contained sub-block ALSO owns registers (needs decode) | No longer the simple case: a decoder must be instanced inside the container to serve the sub-block, so the container is a decoder-host → **nested-router** (container is a routed leaf of a parent decoder, two address groups), or restructure. Tests the "provided no contained leaf needs a reg-decode block" condition. |

**Arm A run (2026-06-24) — result:** all six of H1–H6 reached defensible
answers, **but the baseline is contaminated and therefore invalid as a test of
the skills:**

- No agent trusted the shipped skills. All six explicitly flagged
  `manage-address-space`, `rtl-registers`, `project-conventions.mdc`, and
  `architecture-yaml.mdc` as obsolete ("You MUST manually create the top-level
  decoder") and routed around them.
- They reached correct answers by leaning on (a) the `apbDecode` / `ip_test`
  examples + the Debayer project, and (b) the **leak docs**:
  `firmware_decode_skill_fix_plan.md`, `apb_register_decode_lessons.md`,
  `firmware_decode_problem_abstract.md` — which contain the answer key.
- H1 and H6 carried forward the **over-stated "leaf-ownership / container must
  not own registers"** framing from the lessons/abstract docs — direct evidence
  that wrong framing propagates into agent decisions (and would fail H7).

**Conclusions / actions feeding this plan:**

1. For a valid A/B, eval agents must run with the three leak docs **excluded**,
   so only the skill-under-test + repo code/examples are visible.
2. The lessons/abstract docs must be corrected (now a required item in §6), not
   just the skills.
3. Add **H7** as the discriminator that catches over-correction.
4. Concrete gap-answers obtained and folded into §2: nested-router feeds are
   fully synthesized (author nothing); the upstream feed boundary is the only
   hand-authored register-bus wiring.

**Next step:** draft the gap-closed `design-register-decode` skill, then run the
clean A/B (leak docs excluded) over H1–H8.
