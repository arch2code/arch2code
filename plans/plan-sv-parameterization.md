# SystemVerilog Parameterization Strategy

**Status:** historical. Keep this as the strategy decision record for the
SV shape; use `plan-param-constant-collision.md` for current SV execution
and `plan-canonical-verilated-wrappers.md` for canonical wrapper details.

**Original status:** Decision (Task 5 of `proto/p0-deferred-tasks.md`).
**Cross-references:** [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md) §4.3 (four-options enumeration), §11 #2; [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md) Step 10. Validated by R1/R2/R3/R6 in [`../../proto/p0-conclusions.md`](../../proto/p0-conclusions.md).

## Recap: the four options from umbrella §4.3

1. **Separate package per instance** — one `isp_types_pkg` source, regenerated per variant with different `localparam` values; same package name across variants. Each variant is a separate compile.
2. **Module-level parameters defaulting from package** — IP module declares `parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR` and defines parameterized types locally; multiple instances at different parameter values coexist in one elaboration.
3. **SV-2012 parameterized packages** — `package isp_types_pkg #(parameter int BPP = 8); … endpackage`. EDA-tool support is uneven.
4. **Generate-block strategies** — variant selection through `generate` constructs around a single source.

## Decision

Adopt a **complementary pair**:

- **Primary text-stability strategy: separate-packages-per-instance (§4.3 option 1).** Each variant is regenerated as its own `isp_types_pkg.sv` *file*, all sharing the same package name but living under per-variant build directories. This is what R1/R2 validated and what the prototype shows.
- **Multi-instance escape hatch: module-level parameters defaulting from package (§4.3 option 2).** An IP's module file declares parameters that default to the package values and then defines its parameterized types locally from those parameters. R3 validated this; R6 confirmed it composes through containers.

These are **not alternatives**. Option 1 supplies the per-variant *constants* used as the default. Option 2 makes the *module* portable across variants when a single elaboration must contain more than one bitwidth.

**SV-2012 parameterized packages (§4.3 option 3) and generate-block strategies (§4.3 option 4) are explicitly out of scope** for this generator. They may be revisited if EDA tool coverage improves; this is a future-only follow-up.

## File-structure spec

For an IP `<ip>` with parameterizable types and one or more variants `<v>` (e.g., `8bpc`, `12bpc`):

```
<consuming-project>/build/<v>/
    isp_types_pkg.sv             # generated PER VARIANT, package name unchanged
    <other_pkg>.sv               # per-variant if it transitively depends on the parameter
<ip>/rtl/
    <ip>.sv                      # text-stable IP source — parameters default from package,
                                 #   types defined locally; uses module-level parameters (§4.3 #2)
    <ip>_pkg.sv                  # IP's symbolic-constant package (per-variant only if that IP
                                 #   has parameter-dependent constants of its own)
```

Naming convention: the *package name* is invariant (`isp_types_package`); the *file path* distinguishes variants. R1 confirmed Verilator accepts this with `-Wno-DECLFILENAME`. The umbrella plan calls this out explicitly; do not invent variant suffixes inside the package name.

### Who generates what

| Artifact | Generator | Owner |
|----------|-----------|-------|
| `isp_types_pkg.sv` (per variant) | arch2code, called from the consuming project's flow | Consuming project (one copy per `(IP, variant)` pair the project instantiates) |
| `<ip>.sv` (text-stable IP body) | arch2code, called from the IP's flow | IP (one copy total) |
| `<ip>_pkg.sv` (IP's own symbolic constants) | arch2code, called from the IP's flow | IP (per-variant only if needed) |
| `tb_<ip>.sv` (per-variant TB) | arch2code | Consuming project |

The text-stability invariant (umbrella §3 / `p0-conclusions.md` "SV text-stability confirmed") is preserved: the *IP-owned* files (`<ip>.sv`, optionally `<ip>_pkg.sv`) are byte-stable across variants. Only consuming-project artifacts (`isp_types_pkg.sv`) regenerate.

## Generator file map (arch2code)

The plan stub below is a *map*, not an implementation. Each row is what Step 10 of [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md) needs to land.

| Step 10 sub-item | Generator file | Notes |
|------------------|----------------|-------|
| Emit per-variant `isp_types_pkg.sv` with parameter values substituted | extension of the existing package emitter (likely `builder/base/pysrc/svPackages.py` or equivalent — verify before F2) | Same template, different value bindings |
| Strip parameterizable constants from IP package (or keep as defaults) | same emitter, gated on `ipParameters` presence | When the IP has `ipParameters`, those constants migrate from the IP package to the per-variant `isp_types_pkg` |
| Emit module-level `parameter` declarations defaulting from package | SV module emitter | One `parameter` per `ipParameter` row |
| Define parameterized types locally inside the module | SV module emitter | Replaces import-based type references for the parameterizable subset |
| Container modules: define per-instance local types | SV container emitter | R6 pattern; needed for multi-instance sub-systems |
| Per-variant build directory wiring | build-system glue (Makefile / `f.list`) | Symlink IP source, pull variant-specific package |

(Exact filenames to be confirmed against `builder/base/pysrc/` during F2 implementation; this stub is the *what*, not the *where*.)

## Worked-example mapping

For the prototype's `interpolate` IP at two variants (`8bpc`, `12bpc`):

- IP source files (text-stable, one copy):
  - `interpolate.sv` — declares `parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR;` and defines its `pixel_t`, `bayer_pixels_per_clock_t`, etc., locally from that parameter.
- Consuming-project build outputs (regenerated per variant):
  - `build/8bpc/isp_types_pkg.sv` — `localparam int unsigned BITS_PER_PIXEL_COLOR = 8;`
  - `build/12bpc/isp_types_pkg.sv` — `localparam int unsigned BITS_PER_PIXEL_COLOR = 12;`
- Multi-instance container (R6):
  - `camera_subsystem.sv` instantiates `interpolate #(.BITS_PER_PIXEL_COLOR(8))` and `interpolate #(.BITS_PER_PIXEL_COLOR(12))` in one elaboration; defines local `struct packed` types per instance for the wires connecting them.

## Open follow-ups

- **SV-2012 parameterized packages.** Re-evaluate when:
  - All EDA tools used by the project support `package #(...) ... endpackage` correctly (synthesis + sim + lint).
  - The per-variant build-directory cost (Option 1) becomes a maintenance burden (currently negligible).
- **Generate-block strategies.** Not pursued; left as a recorded option. They would only be reconsidered if a future variant axis needs run-time-style selection inside a single elaboration, which is not on the current roadmap.
- **`hwRegister<N>` from `maxBitwidth`** (umbrella §3 / R4 deferred remainder). Still design-only on the SV side as well; tracked separately under address-decode work.
- **Remove `examples/ip_test/rtl/ip.sv` field-wise widening workaround.** The current package emitter leaves `ipDataSt`/`ipDataT` at the package default/max width even when an `ip` instance binds `IP_DATA_WIDTH` to a narrower variant. The hand RTL widens fields explicitly to keep lint clean without shifting packed-field positions. Once parameterizable SV types are emitted as module-local types driven by instance parameters, delete that workaround and use the parameter-tracking type directly.
