# Item 5 — Mechanizing the `.cpp/.h` → `.cppm` User-Region Transplant

Read-only feasibility + desirability assessment. No files changed, no config
flipped, no builds run. Scope: Item 5 converts **all** block implementations to
a single `.cppm` module; today `make migrate` scaffolds the `.cppm`, reports
`TODO_PORT`, and leaves an agent to transplant the user code per block. Question:
should the transplant be mechanized on top of the `codeText` region splitter?

## 1. The `codeText` API (`pysrc/textfileHelper.py`)

`class codeText(fileName, commentDelimiter="//")` parses a marker file at
construction into two **positionally-correlated** lists plus the PARAM row:

- `self.sections` — one dict **per `GENERATED_CODE_BEGIN`**, in file order:
  `{'command': <string after BEGIN>, 'indent': <col>, 'lineNo': <n>}`. `command`
  is the raw template invocation, e.g. `--template=classDecl` or
  `--template=constructor --section=init`.
- `self.ungeneratedSections` — the **N+1 non-generated spans** around those N
  sections. `[0]` is everything before the first BEGIN; `[i]` is the span from
  section `i-1`'s END through section `i`'s BEGIN; the last is from the final END
  to EOF. Each span **embeds the bracketing END line at its head and the next
  BEGIN line at its tail** (the marker lines are copied into the ungenerated
  text, not stripped).
- `self.params` — parsed `GENERATED_CODE_PARAM` (`block`, `context`, `mode`,
  `variant`, `project`, …). `self.block`, `self.parent` are convenience fields.
- `genFile(genList)` — rewrites only generated regions, interleaving `genList`
  with the preserved ungenerated spans. (The write path, not needed for a port.)

**Key limitation for mechanization:** `codeText` exposes region *boundaries*, not
slot-keyed user text. It gives no "user region for template X" accessor. A
mechanizer must (a) read `--template=`/`--section=` out of each `command`, (b)
take the ungenerated span that *follows* that section, and (c) strip the embedded
END/BEGIN marker lines and any trailing `};`. That correlation + marker-strip is
a thin, deterministic layer to build on top; `codeText` itself does not do it.

## 2. Old structure — four user slots (verified on `examples/mixed/model/blockA.{h,cpp}`)

`blockA` is a real non-parameterized block, already includes-migrated (its
generated regions already carry `import blockA.base;` / `import mixed;`):

| # | Slot | Location in old file | Bracketing generated section |
|---|------|----------------------|------------------------------|
| 1 | Class body members | `.h`: after `classDecl` END, before class `};` | `--template=classDecl` |
| 2 | Ctor init-list | `.cpp`: between `constructor --section=init` END and `--section=body` BEGIN | `constructor --section=init` |
| 3 | Ctor body (incl. `SC_THREAD`, `static_assert`) | `.cpp`: after `--section=body` END, before ctor `};` | `constructor --section=body` |
| 4 | Out-of-line defs | `.cpp`: after ctor `};` to EOF | (tail; same section-3 anchor) |

Slots 3 and 4 are one contiguous span split only by the ctor `};`. Boilerplate to
drop: `#ifndef` guard, `#include "systemc.h"`, `#include "<block>.h"`.

**Verified fact that de-risks the port:** across the 74 non-parameterized example
blocks, every `import`/`#include` sits **inside a generated region** (e.g.
`simple_ip.cpp` emits `import apbDecode.base;` inside the generated
`constructor --section=init`). The four user slots carry **no** import/include
directives. So moving the four slots loses no import information.

## 3. New structure — `.cppm` sections (verified on `blockF.cppm`, `debayer.cppm`, `interpolate.cppm`)

Section order in the ported module:

1. `moduleScaffold --section=blockModuleHeader` — GMF: `module;` + all system /
   arch2code / `<ctx>VariantConfig.h` `#include`s. **Generated.**
2. `// user #includes here` — GMF user slot (global-module includes only).
3. `moduleExport` — `export module <block>.block;` + structural `import`s.
   **Ends import-only** (no `using namespace`).
4. `// user imports here` — module-preamble user slot.
5. `classDecl` — **head emits the `using namespace <ctx>_ns;` lines**, then class.
6. Class-body user slot (after `classDecl` END, before `};`).
7. `constructor --section=init` + init-list user slot.
8. `constructor --section=body` + body user slot; out-of-line defs at tail.

## 4. Mapping table (old slot → `.cppm` target)

| Old slot | `.cppm` target | Deterministic (non-param)? |
|----------|----------------|----------------------------|
| 1 Class body | after `classDecl` END, before `};` | **Yes** — same anchor |
| 2 Ctor init-list | between `constructor init` END and `body` BEGIN | **Yes** |
| 3 Ctor body | after `constructor body` END, before ctor `};` | **Yes** |
| 4 Out-of-line | module tail (after ctor `};`) | **Yes** |
| (boilerplate) | dropped | **Yes** — fixed strings |
| slot-0 top-of-file user code (rare) | GMF `#includes` slot / preamble import slot | **No** — needs triage |

For a **non-parameterized** block the map is fully deterministic: the four slots
have identical section anchors in both files, and the generator re-emits the
structural imports in the new `moduleExport`/init regions.

## 5. Gotchas — mechanical vs. judgment

- **`#include` → `import` rewrite (T2):** Mechanically **moot** for the 74 —
  user slots carry no includes; imports are generator-owned and re-emitted. Only
  a stray user include in slot-0 would need triage (std/system → GMF; sibling
  module → `import <sib>.block;`). **Flag, don't auto-rewrite.**
- **Import placement / C++20 purview:** **Resolved by the current template
  structure, not a blocker.** The module-header restructure moved every
  `using namespace` to the `classDecl` head, so `moduleExport` ends import-only
  and the `// user imports here` slot is *always* a valid open preamble — in the
  leaf case (`interpolate`) **and** the mixed case (`debayer`). The old MEMORY
  "mixed case has no valid user slot" described the pre-restructure single-region
  header; it no longer applies. A mechanizer placing user imports in that slot is
  always legal.
- **Slot with no clean target:** only slot-0 (top-of-file). Handle by detecting
  non-boilerplate content in `ungeneratedSections[0]` and flagging for agent.
- **Reg-handler blocks (`blockRegs`):** regenerate-not-port — no user slots.
  Mechanically **exclude** (delete legacy pair, let `make gen` recreate). Trivial.
- **Templatization (T2 for parameterized blocks):** `template<typename Config>`
  prefixes, `<block>::`→`<block><Config>::`, dependent-type/trailing-return
  qualification, `this->` insertion. **Semantic — not mechanizable by text
  moves.** But parameterized blocks are *not* the Item-5 74; they are the ~10
  already-ported `.block` modules.
- **Body-only context imports:** a context type used only in a method body
  (`bayer_pattern_reg_t`, `NUM_LINE_BUFFERS`) that neither generator emits
  structurally. Absent in the 74 (all imports generated); real only in complex
  parameterized blocks. Residual agent fix; surfaces as a build error.
- **Module-hostile libraries (OpenCV etc.):** design decision (pimpl / keep
  non-modular). Rare, **needs agent.**

## 6. Fraction estimate (~74 blocks)

The 74 count = all non-parameterized `.cpp/.h` model blocks in the example suite
(measured). Item 5's scope is exactly these; the 10 parameterized blocks are
already `.cppm`.

- **Clean mechanical (~90%+):** non-parameterized blocks, no T2, no import
  triage, four deterministic slot moves + fixed boilerplate drop.
- **Trivial exclude (~3–5%):** reg-handler pairs — delete + regenerate.
- **Needs agent (~few %):** blocks with non-boilerplate slot-0 content, or a
  module-hostile library. Flagged, not silent.
- **Not in scope:** the parameterized/T2 blocks (already ported by agent).

## 7. Recommendation — HYBRID (mechanical bulk + agent for flagged edges)

**Mechanize the non-parameterized subset** with a `codeText`-driven four-slot
transplant: parse old `.h`+`.cpp` and new `.cppm` with `codeText`, correlate
slots by the `--template=`/`--section=` in each `command`, move the four
ungenerated spans (marker-stripped, trailing `};` handled), drop the fixed
boilerplate. This is deterministic and safe *because* imports are generator-owned
and the preamble slot is now always valid — the two historical blockers are gone.

**Keep agent-driven** for: (a) parameterized blocks (T2 templatization is
semantic), (b) module-hostile-library blocks, (c) any block whose slot-0 carries
non-boilerplate. The mechanizer should **detect and flag** (b)/(c) rather than
attempt them, and should exclude reg-handlers (regenerate path).

Reasoning: the mechanical transform eliminates the bulk of a tedious, error-prone
74-block hand transplant with zero semantic reasoning, while the residue that
genuinely needs judgment (templatization, library confinement) is precisely the
part a text mover cannot do and would corrupt if it tried. A pure-mechanize
stance would silently mis-handle those; a keep-agent stance wastes agent effort
on 70+ deterministic moves. Hybrid matches the work to the tool.

**Do not build this now** — assessment only. If pursued, the deliverable is a
thin slot-correlation layer over `codeText` in a migration helper, gated to
non-parameterized blocks, emitting a per-block "mechanized" / "flagged-for-agent"
report.
