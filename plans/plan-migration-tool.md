# Migration Tool Scope Sketch

**Status:** Sketch only (Task 7 of `proto/p0-deferred-tasks.md`). This document does **not** build the tool; it scopes it so the team can estimate the `[M3+T6]` step in [`plan-development-ordering.md`](./plan-development-ordering.md) Option 4.

**Classification:** historical.

**Status taxonomy:** historical. This is the proto-era scope sketch for
migrating hand-authored C++/SystemC and SystemVerilog code after
parameterization conventions are chosen. If that hand-authored code migration is
revived, treat this document as design only until implementation evidence is
added.

**Not the YAML migration owner:** active YAML format migration is owned by
`plan-yaml-migration.md`. That plan covers `yamlFormat: 2`, eval-string
migration, address-control migration, and the proposed project migration flow.
This sketch remains limited to hand-authored C++/SV source migration and should
not be used as instructions for the active YAML migration workstream.

**Cross-references:** [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md) §11 #7, [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md) "Further considerations" #2, ordering plan Option 4.

## Inventory of hand-written code in this repo

The numbers below are from this repo (`debayer`) on the `proto`-era tree. They are intended as a *typical* IP-sized data point — other projects will scale roughly proportionally to the number of parameterizable IPs.

### C++ (SystemC) model

| Bucket | Count | Notes |
|--------|------:|-------|
| Hand-written model files (`model/*.{h,cpp}`) | 28 | Includes block headers, block impls, two `*Includes.{h,cpp}` types files, two `*_config.h` configuration objects |
| Block classes (`SC_MODULE` declarations) | 6 | apb_decode, cpu, debayer, debayer_regs, interpolate, preprocess, rgb_video_sink, raw_video_src — these would need `template<typename Config>` if the IP they back is parameterizable |
| Files referencing `BITS_PER_PIXEL_COLOR` | 6 | `model/raw_video_src.cpp`, `model/b2p_deb_conv.h`, `model/rgb_img_writer.h`, `model/debayerIncludes.h`, `model/interpolate.cpp`, `model/isp_typesIncludes.h` |
| Files referencing `PIXELS_PER_CLOCK`     | 10 | superset of the above plus `preprocess.cpp`, `raw_video_src.h`, `rgb_video_sink.h`, `debayerIncludes.cpp`, `isp_typesIncludes.cpp` |
| Files referencing `MAX_PIXEL_VALUE`      | 2  | `model/interpolate.cpp`, `model/isp_typesIncludes.h` |
| Files referencing `BPPC_P1` (derived)    | 1  | `model/debayerIncludes.h` |
| Files referencing parameterizable struct names (`rgb_pixel_t` / `*_pixels_per_clock_t` / `video_*_t` / `pixel_t`) | 11 of 28 | Highest-density: `interpolate.cpp` (42 hits), `isp_typesIncludes.cpp` (57), `isp_typesIncludes.h` (68); rest in single digits |
| Generated base headers under `base/` referencing those types | 5 | `debayerBase.h`, `raw_video_srcBase.h`, `rgb_video_sinkBase.h`, `interpolateBase.h`, `preprocessBase.h` (these are *re*-generated, not hand-edited; out of migration scope) |

**Net hand-edit surface:** ~10–12 files in `model/` need real edits. The rest are either non-parameterizable (`apb_decode`, `cpu`, `debayer_regs`, `*_config.h`) or contain only includes / no parameterizable references.

### SystemVerilog RTL

| Bucket | Count | Notes |
|--------|------:|-------|
| `rtl/*.sv` files | 8 | debayer, debayer_package, debayer_regs, debayer_tb_package, interpolate, isp_types_package, preprocess, shared_types_package |
| Files referencing parameterizable constants | 4 | `interpolate.sv`, `isp_types_package.sv`, `debayer_package.sv`, `preprocess.sv` |

The package files (`isp_types_package.sv`) regenerate per variant — those aren't migrated, they're re-emitted. The IP module files (`interpolate.sv`, `preprocess.sv`) need module-parameter pattern (per [`plan-sv-parameterization.md`](./plan-sv-parameterization.md)). That's 2 files of real RTL migration work.

### Summary

- **Hand-edit surface (C++)**: ~10–12 files, ~150 line-level edits.
- **Hand-edit surface (SV)**: ~2 files, ~10–20 line-level edits.
- **Generated artifacts (`base/*Base.h`, `rtl/*_package.sv`)**: re-emitted, not migrated.

This is small. **Order of magnitude: 1 IP = 1 person-week of mechanical edits + judgment, total.** Across a typical multi-IP project (5–10 IPs) the total is still in single digit person-weeks of editing.

## Categorization of edits

### Mechanical (regex- or AST-rewriteable)

These are the high-frequency, low-judgment edits. A `sed` script with anchored patterns gets >80% of them right.

| Pattern | Replace with | Count basis |
|---------|--------------|-------------|
| Bare `BITS_PER_PIXEL_COLOR` | `Config::BITS_PER_PIXEL_COLOR` | All 6 model files; SV-side handled by package regeneration |
| Bare `PIXELS_PER_CLOCK` | `Config::PIXELS_PER_CLOCK` | 10 files |
| Bare `MAX_PIXEL_VALUE` | `Config::MAX_PIXEL_VALUE` | 2 files |
| `rgb_pixel_t` (used as type) | `rgb_pixel_t<Config>` | Inside templated classes; *not* inside non-templated TBs that pin a Config |
| `bayer_pixels_per_clock_t` etc. | `<Config>` parameterized form | Same |
| `pixel_t` (the leaf alias) | unchanged — still `pixel_t<Config>` for symmetry but value-equivalent | Caveat documented in `p0-conclusions.md` "leaf-type alias" |
| `class debayer { … };` | `template<typename Config> class debayer { … };` | One per parameterizable block class |
| Block method definitions in `.cpp` | `template<typename Config> void debayer<Config>::method() { … }` | Per method |
| `using …::isp_types_package::*;` (SV) | (deleted from IP module; constants come via module parameter) | 2 SV files |
| `#include "isp_typesIncludes.h"` | (initially unchanged; if the `Includes` file becomes a template module, switch to `import isp;` later — separate step from this migration) | 9 files |

### Judgment-call

These are the edits where a regex is wrong as often as it's right.

- **Which methods on a templated class need to be `template<typename Config> ReturnT debayer<Config>::method()` vs. inline in the header.** Existing convention puts most impl in `.cpp` with the `interpolate.cpp` "explicit template instantiation" pattern (see `proto/model/block/interpolate.cpp`). The migration must replicate this per method, but the *which methods to inline vs. keep in .cpp* decision stays a judgment call (typically: short → inline, long → keep in `.cpp` with explicit instantiations at the bottom).
- **Which IP-owned types are parameterizable in the first place.** This is *already* declared in YAML once the `ipParameters` block lands; the tool reads YAML to know which types to parameterize. Not migration tool's problem if F1 lands first.
- **Cross-config wiring (interface constraint — Task 1 negative test).** If the existing hand-written code wires a `debayer_8` to a `preprocess_12`, the migration tool *cannot* fix it — by design (umbrella §7 prohibits it). The tool must flag, not auto-rewrite.
- **TB-side type pinning.** A non-parameterizable testbench at the top must pin a Config (`debayer<config_8bpc>`). The tool can't know which Config to pick; it should flag and let a human choose.

## Tool approach options

### Option A — Pure regex/sed scripts

- Cheapest to write (1–2 person-days).
- Catches the high-frequency mechanical patterns above.
- Will misfire on:
  - Identifiers that *contain* `pixel_t` as a substring.
  - References inside string literals or comments.
  - Method definitions in `.cpp` (regex can't reliably rewrite multi-line method signatures).
- Practical use: write the script, run it, hand-fix the misses.

### Option B — clang-tidy / libTooling rewriter

- Most robust (typed AST, knows what's a type vs. an identifier).
- Requires a compilation database (`compile_commands.json`) — already implied by the C++20 modules toolchain plan.
- Build cost: 5–10 person-days for a custom check + tests.
- Practical use: encode the patterns as `MatchFinder`-based rewrites; run idempotently; commit.

### Option C — Manual checklist per IP, no tool

- Zero tool cost.
- Per-IP cost: ~1 person-day reading and editing 10–12 files.
- For a project of 5–10 IPs, 1–2 person-weeks of editing total.
- Risk: drift between IPs as the convention evolves mid-migration. Mitigated by ordering plan Option 4's "single-pass migration" guidance.

## Recommendation

**Hybrid: Option A then Option C.**

The numbers say the AST tool (Option B) is overkill for a single-digit number of IPs. Build a 1–2-day `sed`/Python script that:

1. Reads YAML to learn which types/blocks are parameterizable for each IP.
2. Applies anchored substitutions (`\bBITS_PER_PIXEL_COLOR\b` → `Config::BITS_PER_PIXEL_COLOR`, etc.) over `model/*.{h,cpp}` for the IPs being migrated.
3. Adds `template<typename Config>` to declared classes whose names appear in the YAML's `template-blocks` list.
4. Inserts placeholder explicit-instantiation lines at the bottom of each `.cpp`, commented out — a human un-comments them after picking the right `<Config>` list.
5. Emits a per-file diff report; each IP gets a 5-minute human review pass to fix the misfires Option A will produce.

**Total estimate (single project, ~5 IPs):**

- Tool build: 2 person-days.
- Tool run: < 10 minutes wall-clock.
- Human review per IP: 0.5–1 day. → 3–5 person-days for the project.
- **Total: ~1 person-week** for the whole `[M3+T6]` migration.

If the project grows to 20+ IPs or external IP authors need to run the tool unattended, **upgrade to Option B** at that point. The trigger threshold is "human review time exceeds tool-build time" — i.e., once 5+ person-days are sunk into review, build the AST tool.

## Staging recommendation

Ordering plan Option 4 calls out a single bracketed `[M3+T6]` step, suggesting *atomic* migration. Given the small surface, this is realistic:

- **Single-pass, single-PR migration per project.** Run the script, review, commit. Pre- and post-migration trees are not required to coexist.
- **Per-IP gating, not per-file gating.** The tool processes one IP's `model/` tree in one batch; do not interleave IPs in a single PR.
- **No parallel-build mode.** The "regenerated baseline" + "templated" coexistence the umbrella plan worried about is unnecessary for a tree this small.

The single risk this introduces: a long-lived branch during migration. Mitigated by keeping the migration PR small (one IP at a time) and rebasing aggressively.

## Estimates summary

| Activity | Estimate |
|----------|----------|
| Build the migration script (Option A) | 2 person-days |
| Run + per-IP review (Option C completion) | 0.5–1 person-day per IP |
| Whole-repo migration for a 5-IP project | ~1 person-week |
| Whole-repo migration for a 10-IP project | ~2 person-weeks |
| Switch-to-libTooling break-even | >10 IPs **or** repeated re-runs across teams |

These numbers tighten the umbrella plan's "largest unquantified execution risk" sentence: the migration is a 1–2-week task per project, not a multi-month one.

## Open follow-ups

- **Per-project YAML format for the migration script.** Define a small `migration.yaml` (or extend `project.yaml`) listing: parameterizable blocks, their default Config for non-templated TBs, and any "do not migrate" files.
- **Idempotency.** The script should be safe to re-run (no double-templatising). Achieve this by detecting already-`template<typename Config>`-prefixed declarations and skipping them.
- **Pre-flight check.** Before running, the tool should verify the cross-config wiring rule (Task 1 negative test) — if any TB contains direct cross-config bindings, abort with a list of offending lines.
