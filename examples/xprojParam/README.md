# `xprojParam` — parameterized interface across project boundaries

A composed example whose sub-projects are **separately named projects that each
own a parameterized block**, wired into a chain by an assembler project. Where
`ip_test` demonstrates hierarchical composition in general, this example exists
for one axis only: what happens to a **parameterized** interface when it crosses
a project boundary, in the two shapes that a real assembler runs into.

A second, independent family (`cppLeaf` + `cppAxis`) carries the shapes a
**thunked** junction can take once both sides are parameterized: pairs whose bit
layouts agree while their emitted C++ member storage agrees or disagrees. See
"C++ definitions at a thunked junction".

The db-level behaviour of these shapes is pinned by
`unittest/test_param_cross_project_linkage.py`. This example covers what a
`db`/`gen` pass cannot reach: **actual C++ compilation and a running
simulation**.

## Sub-projects

Each stage project is self-contained (own `prj/`, `yaml/`, `include/make`,
`Makefile`) and owns one or two parameterized blocks. None declares a
`topInstance`: they are reusable IP projects, generated and built by their own
`make gen`, instantiated by the assemblers.

| Directory | `projectName` | Blocks | Declaration set |
| :-- | :-- | :-- | :-- |
| `gain/` | `xpGain` | `xpGain`, `xpGainUniq` | own `PIXEL_WIDTH` / `pixel_t` / `videoSt` / `videoIf`, plus a `gn`-prefixed copy |
| `filter/` | `xpFilter` | `xpFilter`, `xpFilterUniq` | own same-named set, plus an `fl`-prefixed copy |
| `sink/` | `xpSink` | `xpSink`, `xpSinkUniq` | own same-named set, plus an `sk`-prefixed copy |
| `filterShared/` | `xpFilterShared` | `xpFilterShared` | none of its own; `include:`s `gain`'s IP root |
| `sinkShared/` | `xpSinkShared` | `xpSinkShared` | none of its own; `include:`s `gain`'s IP root |
| `cppLeaf/` | `xpCppLeaf` | `xpCppLeafEq`, `xpCppLeafOrder`, `xpCppLeafSign`, `xpCppLeafNest` | own `LEAF_PIXEL_WIDTH` plus one parameterizable payload shape per block |

The unprefixed sets in `gain`, `filter` and `sink` deliberately use **identical
identifier names** across the three projects, matching the field shape where
several sub-project namespaces export the same payload spelling. The prefixed
(`Uniq`) sets are the same topology with names that cannot collide.

The upstream project's own block consumes `PIXEL_WIDTH`. That is required, not
incidental: an exposed `ipParameters` constant must be consumed by a block param
declared in the **same file**, so an upstream project cannot publish a parameter
purely for downstream projects to `include:`.

## Chain behaviour

The three chain compositions (`uniq`, `deparam`, `shared`) wire the same
three-stage chain and assert on real data:

- the source stage pushes four samples, `tag = i`, `data = 0x10 + i`,
- the middle stage adds `0x20` and forwards,
- the sink stage checks `tag == i` and `data == 0x30 + i` for all four, logs the
  count, and ends the test.

Each stage also asserts its own `PIXEL_WIDTH` resolves to the bound variant
value, so a parameter that stops reaching a stage across the boundary fails loud
rather than truncating silently.

`cppAxis` drives four samples on each of its four boundary shapes instead, with a
distinct value per field per iteration, and each consumer checks every field of
every sample and its own bound `LEAF_PIXEL_WIDTH` before voting the test done.
That matters for the pairs whose members are storage-transposed: a positional
adapter that copied the wrong field or the wrong number of bits shows up as a
mismatch rather than as a value that happens to survive.

## Assemblers

| Directory | `projectName` | Boundary | Status |
| :-- | :-- | :-- | :-- |
| `uniq/` | `xpUniq` | assembler-owned literal `boundaryIf`, prefixed stage blocks | **builds and runs** |
| `cppAxis/` | `xpCppAxis` | assembler-owned literal boundary into a parameterized wrapper, which maps each shape to a `cppLeaf` child | **builds and runs** |
| `deparam/` | `xpDeparam` | assembler-owned literal `boundaryIf`, same-named stage blocks | `db`/`gen` pass, **compile fails** |
| `shared/` | `xpShared` | straight-through parameterized `videoIf` over the shared declaration set | `db`/`gen` pass, **compile fails** |

`uniq` and `deparam` are the sanctioned de-parameterized boundary: the assembler
declares its own literal-width payload, each stage keeps its own parameterized
interface, and every leg is a cross-interface bind adapted by a generated
push/ack thunker. They differ only in whether the three stage projects spell
their payload identifiers identically.

`shared` is the straight-through parameterized path: both downstream projects
reach the upstream project's `PIXEL_WIDTH` and `videoIf` through `include:`, so
all endpoints share one parameter identity and the connection needs no thunker.

### Reference depth decides context ownership

`shared/prj/yaml/xpSharedProject.yaml` references only the two downstream stage
projects; the upstream stage project is reached **through** them. That is
required, not cosmetic. Context ownership is awarded to the deepest provider
closure that reaches a file, with equal depth broken lexically on the provider
path. Because both downstream IP roots `include:` the upstream IP root, listing
the upstream project alongside them puts all three providers at the same depth
and the upstream context is attributed to whichever downstream project sorts
last — which renames its generated module (`xpSinkShared_xpGain` instead of
`xpGain`) and makes the composed build unresolvable.

## Build and run

Leaf-first, as with any composed project. From `builder/base`:

```
make xproj-param            # the composition that builds and runs
make xproj-param-probes     # the two recorded compile failures (expected to fail)
```

Or directly:

```
make -C examples/xprojParam/gain    -j gen
make -C examples/xprojParam/filter  -j gen
make -C examples/xprojParam/sink    -j gen
make -C examples/xprojParam/uniq    -j gen
make -C examples/xprojParam/uniq/rundir -j run

make -C examples/xprojParam/cppLeaf -j gen
make -C examples/xprojParam/cppAxis -j gen
make -C examples/xprojParam/cppAxis/rundir -j run
```

`make xproj-param` is part of `pipeline-test`. The probe target is not: both of
its compositions are expected to fail to compile, and each failure is the
recorded state of a defect rather than something to fix here.

There is deliberately **no Makefile at this example's root**. The example is a
family of independent top projects over shared IP projects, not one composed
project, so it has no single root manifest. `unittest/test_build_manifest.py`
discovers examples by their root Makefile and compares one root manifest against
the glob set of every nested project root; a root Makefile here would make it
compare one assembler's manifest against every assembler's tree and fail.
Build and generated output is covered by the consolidated `examples/.gitignore`.

## C++ definitions at a thunked junction

The de-parameterized boundary compositions above only ever pair a
**literal-width** assembler struct against a **parameterized** IP struct. That
pairing tells you nothing about how two *parameterized* declarations relate,
because a parameterizable type is emitted as a container sized from its declared
`maxBitwidth` while a literal type is emitted in the integer-size bucket of its
resolved width. `cppLeaf` + `cppAxis` supply the parameterized-against-
parameterized pairs.

`cppAxis` holds a parameterized wrapper block, `xpCppWrap`, that owns four
parameterizable payload declarations and routes each of its boundary ports to a
`cppLeaf` consumer through a `connectionMap`. Each map's parent interface is the
wrapper's own declaration and the child's port interface is the IP's own, so
every map is a cross-interface bind and the generator emits one push/ack thunker
per map with a parameterizable declaration on **both** sides. The top itself
stays untemplated: it drives literal-width boundary interfaces into the
wrapper's ports, which adds a second, literal-against-parameterized thunker per
leg.

All four pairs are **bit-layout compatible** — the fields carry the same widths
at the same packed positions, which is why every one of them reaches the adapter
and `make db` is clean. They differ in emitted C++ member storage. Emitted
members are listed in reverse declaration order, so the tables below read
low-packed-position last.

### Corresponding storage

```cpp
template<typename Config>              template<typename Config>
struct wrapEqSt {                      struct leafEqSt {
    wrapPixelT<Config> data;               leafPixelT<Config> data;
    wrapTagT tag;                          leafTagT tag;
};                                     };
// wrapPixelT -> uint64_t              // leafPixelT -> uint64_t
// wrapTagT   -> uint8_t               // leafTagT   -> uint8_t
```

`sizeof` 16 on both sides, member storage identical position for position. Two
different declarations owned by two different projects, so a thunker is required,
and a direct payload copy would serve it. This is the shape a correctly
parameterized design produces routinely, because both sides' storage comes from
`maxBitwidth` rather than from either side's bound width.

### Reversed member storage order

```cpp
template<typename Config>              template<typename Config>
struct wrapOrderSt {                   struct leafOrderSt {
    wrapFlagT second;                      leafPixelT<Config> second;
    wrapPixelT<Config> first;              leafFlagT first;
};                                     };
```

Both members are 8 bits wide, so each field occupies the same packed position as
its namesake and the values arrive intact. `sizeof` is 16 on both sides and both
are trivially copyable — yet the storage sequences are `{uint8_t, uint64_t}`
against `{uint64_t, uint8_t}`. A byte-for-byte copy between them would scramble
the payload, so equal size and trivial copyability are not sufficient grounds for
one.

### Differing signedness

```cpp
template<typename Config>              template<typename Config>
struct wrapSignSt {                    struct leafSignSt {
    wrapPixelT<Config> data;               leafSignedPixelT<Config> data;
};                                     };
// wrapPixelT       -> uint64_t        // leafSignedPixelT -> int64_t
```

`sizeof` 8 on both sides, one member each, same width, same position. Only the
signedness of the container differs. **A direct copy here would in fact be
correct** — the pack/unpack path reinterprets the sign bit exactly as a copy
would — so this pair is recorded as a deliberately conservative verdict: the
predicate is "the definitions are identical", not "a copy happens to be
equivalent". Being wrong in this direction costs only the existing adapter path.

### Nested against flat

```cpp
struct wrapNestHdrSt {
    wrapFlagT flag;
    wrapWordT word;
};
template<typename Config>              template<typename Config>
struct wrapNestSt {                    struct leafNestSt {
    wrapPixelT<Config> data;               leafPixelT<Config> data;
    wrapFlagT tail;                        leafFlagT tail;
    wrapNestHdrSt hdr;                     leafFlagT flag;
};                                         leafWordT word;
                                       };
```

The packed sequences are identical — `(32,0) (8,32) (8,40) (8,48)` on both sides,
because flattening erases the sub-structure boundary. The C++ definitions are
not: three members against four, and `sizeof` **24 against 16**. The nested
header's trailing padding survives as part of a member here and is elided where
the same fields are inlined, so the two objects do not even have the same size,
let alone the same layout. This pair is the sharpest demonstration that bit
layout and C++ definition are separate questions: one axis accepts it, the other
must reject it.

### Literal against parameterized

Already covered by `uniq`, `deparam`, and the four top-level legs of `cppAxis`
(`bndEqSt` against `wrapEqSt<...>` and friends): the literal side is
size-bucketed from its resolved width (`uint8_t`, `uint32_t`) and the
parameterized side is a `maxBitwidth` container, so the two coincide only when
every literal field happens to land in the same bucket. `bndEqSt` is `sizeof` 2
against `wrapEqSt`'s 16. Ineligible by construction, not by accident; not
duplicated as a separate case.

### Pair census over the emitted thunkers

Judging every emitted `_port_thunker<>` payload pair in `examples/` by recursive,
positional, nesting-respecting storage identity including signedness:

| Design | Payload pairs | Corresponding storage |
| :-- | --: | --: |
| `ip_test` | 19 | 14 |
| `simple_ip` | 4 | 2 |
| `xif` | 2 | 0 |
| `xprojParam` | 16 | 1 |
| **total** | **41** | **17** |

`xprojParam`'s single one is the `wrapEqSt`/`leafEqSt` pair above; the other
fifteen are the three counterexamples plus twelve literal-against-parameterized
legs. Two things in the other designs are worth naming, because both are easy to
predict wrongly:

- The register-bus `apb` pairs (`apbAddrSt`/`ipRegAddrSt`,
  `apbDataSt`/`ipRegDataSt`) all correspond: single-member structs over
  `uint32_t` typedefs.
- A literal side and a parameterizable side **do** correspond once the
  parameterizable `maxBitwidth` exceeds 64, because both then emit
  `uint64_t word[N]` for the same `N`. That is why `ip_test`'s 70-bit boundary
  pairs (`srcOut1BoundarySt` against `srcOut1St<...>`, `ipDataSt<...>` and
  `data70St`) correspond while their 8-bit siblings do not: `ipDataT` is
  `uint64_t word[2]` at every variant, which matches a 70-bit literal and not an
  8-bit one.

### Two authoring constraints this family runs into

Both are generator behaviours, recorded here because the fixture is shaped around
them rather than because they are being fixed here.

- **A block reached through a foreign container's parameterizable interface takes
  that container's context as its config context.** The `cppLeaf` blocks are
  mapped from `xpCppWrap`'s own parameterizable interfaces, so their Config
  structs are emitted in `xpCppWrap`'s context. A variant binding declared in
  `cppLeaf`'s own file is then attributed to a project that owns neither that
  context nor the instantiating assembler, and no descriptor is selected: the
  child instance falls back to the container's default Config, which does not
  carry the child's parameter and does not compile. The bindings are therefore
  declared in `cppAxis/yaml/xpCppWrap.yaml`, alongside the wrapper's own.
- **A connectionMap thunker member is named after the mapped instance alone.**
  Two maps from one container into the *same* child instance produce two members
  with the same name. Each shape here therefore has its own consumer block and
  its own child instance, which is also why `cppLeaf` declares four
  single-port blocks rather than one block with four ports.

## Recorded compile failures

### `deparam` — generated C++ namespace ambiguity

The assembler's generated block module emits one `using namespace <ip>_ns;` per
sub-project and then names the thunker payload type **unqualified**. With three
namespaces exporting `videoSt`, the reference cannot resolve:

```
deparam/model/xpDeparamTop.cppm:53:39: fatal error: reference to 'videoSt' is ambiguous
   53 |     push_ack_port_thunker<boundarySt, videoSt<xpGainV0Config>> thunker_videoOut_0_uGain;
      |                                       ^
gain/model/xpGainIncludes.cppm:42:8: note: candidate found by name lookup is 'xpGain_ns::videoSt'
filter/model/xpFilterIncludes.cppm:42:8: note: candidate found by name lookup is 'xpFilter_ns::videoSt'
sink/model/xpSinkIncludes.cppm:42:8: note: candidate found by name lookup is 'xpSink_ns::videoSt'
```

`uniq` is the control: identical topology, identical generated shape, prefixed
payload names, and it compiles and runs. The failure is the identifier
collision, not the composition.

### `shared` — straight-through parameterized boundary

Two independent failures:

1. The assembler container carries parameterized structures on its surface, so
   it is flagged parameterizable while remaining non-templated. Its trampoline
   registrar then includes the retired header form of the block:

   ```
   shared/registrar/xpSharedTopRegistrar.cppm:9:10: fatal error: 'xpSharedTop.h' file not found
   ```

2. The downstream blocks' Config resolves to the upstream project's
   **default** config while the upstream block keeps its variant config, so the
   channel payload and the producer port are different C++ types:

   ```
   shared/model/xpSharedTop.cppm:77:5: fatal error: no matching function for call to object of
   type 'push_ack_out<videoSt<xpGainV0Config>>'
   note: no known conversion from 'push_ack_channel<videoSt<xpGainDefaultConfig>>' ...
   ```

**Both failures are still compile-time; `make db` and `make gen` on `shared` are
clean.** The db-time payload-compatibility check adjudicates one declaration
reached from two differently bound endpoints, and it compares the two sides'
resolved packed forms — so it skips a junction whose sides resolve identically.
Every instance in `shared` binds `PIXEL_WIDTH: 8`, so both packed forms are
`tag@0 w4, data@4 w8` and the layouts genuinely do agree. What `shared`
demonstrates is not a layout disagreement but two distinct `Config` **types** at
one junction with equal values, which no packed-form comparison can see.

Rebinding `PIXEL_WIDTH: 16` in the **upstream** project's own file does make the
same check reject the junction at `make db`:

```
Block xpGain connection '...' (file ../../yaml/xpSharedTop.yaml) binds external interface
videoIf to child uGain.videoOut declared as videoIf (file ../../../gain/yaml/xpGain.yaml):
per-field _bitWidth must agree at every payload position, but field index 1 of
structureType 'data_t' differs: parent field 'data' has _bitWidth 8 at bit offset 4 in
structure 'videoSt' ... while child field 'data' has _bitWidth 16 at bit offset 4 in
structure 'videoSt' ... Fields are compared positionally; the names are shown for
reference only and are not compared.
  parent side: ... resolved for block 'xpFilterShared' (project xpFilterShared) at variant 'v0'
  child side:  ... resolved for block 'xpGain' (project xpGain) at variant 'v0'
```

Rebinding it in a **downstream** project's file leaves `make db` clean instead,
because that binding is discarded outright — see the next section.

### Variant-binding sizing on the shared-include path

`PIXEL_WIDTH` declares `maxValue: 32`. Binding 64 in the upstream project's own
file is rejected at `make db`. The same binding in a downstream project, whose
backing constant is reached by `include:`, is accepted, leaves no trace in any
generated artifact, and the instance is typed with the upstream default width.
