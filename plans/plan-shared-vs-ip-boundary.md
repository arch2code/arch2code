# Shared vs IP Namespace Boundary

**Classification:** historical.
**Status taxonomy:** historical.
**Current owner:** this is a retained P0 decision record for the
`ipParameters` ownership boundary. Current execution for parameterized type,
Config, and eval behavior is tracked by the later implementation plans rather
than this document.

**Status:** Decision (Task 4 of `proto/p0-deferred-tasks.md`).
**Cross-references:** [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md) §11 #1, [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md) "Further considerations" #1.

## Question

May `ipParameters` (the YAML block that introduces a parameterizable Config — `BITS_PER_PIXEL_COLOR`, `PIXELS_PER_CLOCK`, etc.) appear *only* in IP-owned YAML, or also in shared YAML files (e.g., `isp_types.yaml`) that are `include:`-ed by multiple IPs?

This must be answered before F1 (schema changes) so the loader can enforce the rule.

## Implications by choice

### Choice A — `ipParameters` allowed in shared YAML

- A shared file (e.g. `isp_types.yaml`) could declare a Config used by every IP that imports it.
- Two IPs that include the same shared file would *share a single Config type* (`isp::config_8bpc`) at the C++ level — they could not be instantiated at different bitwidths in one binary.
- Multi-instance use (umbrella §4 / R3 / R6) is *broken* unless every IP that participates in the multi-instance system uses its own Config copy.
- The shared file becomes a coupling point: changing it changes every IP that imports it. If a downstream consumer needs a 12bpc instance and an 8bpc instance, it must edit the shared file (impossible — it's shared) or fork it.
- Schema-level enforcement is hard: "include only once across the whole project" is a global graph property, not a per-file property.

### Choice B — `ipParameters` only in IP-owned YAML *(recommended default)*

- Each IP declares its own `ipParameters` block, producing its own Config struct (`debayer::config`, `preprocess::config`, …) or a suitably-scoped Config that is local to the IP.
- Shared YAML files contain only:
  - Non-parameterizable types (e.g., `video_frame_t`'s 1-bit `eof`/`sof`/`eol` in P0).
  - Parameterizable *templates* whose Config is supplied by the consumer at use site (`template<typename Config> struct rgb_pixel_t { … };`).
- Multi-instance is unrestricted: any consumer can instantiate `rgb_pixel_t<config_8bpc>` and `rgb_pixel_t<config_12bpc>` side-by-side from the same shared header.
- The shared file is decoupled from any specific bitwidth choice.
- Schema-level enforcement is local and trivial: a YAML loader rule (see below).

## Decision

**Choice B.** `ipParameters` may appear *only* in YAML files that an IP claims as its own (typically the IP's `project.yaml` or whatever the IP-root file is named). Shared YAML files MUST NOT declare `ipParameters`.

Rationale: the entire point of the umbrella plan's multi-instance pattern (umbrella §4, validated by R3/R6) is that two IPs at different bitwidths can coexist in one binary. Choice A defeats that. Choice B costs nothing — shared files can still define template structs that *consume* a Config; they just don't *bind* a Config.

## Schema rule (for F1)

Add the following loader-time check:

> When loading a YAML file `F`, if `F` contains a top-level `ipParameters:` key, then `F` MUST be the IP-root file of an IP (e.g., the file matched by the project's IP-root naming convention, or the file named in the IP discovery pass). If `F` is `include:`d from another file, error out with:
>
> ```
> error: <F>: ipParameters is only permitted in IP-root YAML files,
>        not in shared/included files. Move the parameterizable Config
>        to the IP that owns it, or split this file so the parameter
>        block lives in an IP-root.
> ```

Equivalent phrasing if "IP-root" is hard to identify: "any file appearing as a value under any `include:` list MUST NOT contain `ipParameters`." The two phrasings are equivalent under the current project layout; pick whichever is easiest for the loader to evaluate.

### What shared files MAY contain

- Non-parameterizable scalar/struct/enum definitions.
- `template<typename Config>` struct/class definitions whose `Config` is bound at the *consumer* site.
- `include:` directives pulling in still-more-shared files (which transitively also forbid `ipParameters`).

### What shared files MUST NOT contain

- `ipParameters:`
- Concrete instantiations of parameterizable types (those belong to the consumer / IP-root).

## Open follow-ups

- The detailed plan currently puts all P0 types in a flat `isp` namespace. Once F1 lands and the schema rule is enforced, revisit whether the plan's "namespace per IP" guidance needs an explicit sub-namespace for shared types (e.g., `isp::shared::`). Not blocking F1.
- If the project adopts SV-2012 parameterized packages later (deferred — see [`plan-sv-parameterization.md`](./plan-sv-parameterization.md)), a parallel rule applies on the SV side. The rule on the C++/YAML side is unchanged.
