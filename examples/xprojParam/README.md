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
| `shared/` | `xpShared` | straight-through parameterized `videoIf` over the shared declaration set | **builds and runs** |

`uniq` and `deparam` are the sanctioned de-parameterized boundary: the assembler
declares its own literal-width payload, each stage keeps its own parameterized
interface, and every leg is a cross-interface bind adapted by a generated
push/ack thunker. They differ only in whether the three stage projects spell
their payload identifiers identically.

`shared` is the straight-through parameterized path: both downstream projects
reach the upstream project's `PIXEL_WIDTH` and `videoIf` through `include:`, so
all endpoints share one parameter identity. One declaration reached at two
different Configs is still a cross-interface bind, so the junction between the
upstream stage's variant Config and the downstream stages' default one is
adapted by a thunker.

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
make xproj-param            # the compositions that build and run
make xproj-param-probes     # the recorded compile failure (expected to fail)
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

make -C examples/xprojParam/filterShared -j gen
make -C examples/xprojParam/sinkShared -j gen
make -C examples/xprojParam/shared -j gen
make -C examples/xprojParam/shared/rundir -j run
```

`make xproj-param` is part of `pipeline-test`. The probe target is not: its one
composition is expected to fail to compile, and the failure is the recorded
state of a defect rather than something to fix here.

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
| `xprojParam` | 17 | 2 |
| **total** | **42** | **18** |

The `mtx*` family below is excluded from this table, which predates it; it adds
18 pairs of which 9 correspond, so the whole-tree figure is **27 of 60**.
`xprojParam`'s two here are the `wrapEqSt`/`leafEqSt` pair above and `shared`'s
one same-declaration-two-Configs pair; the other fifteen are the three
counterexamples plus twelve literal-against-parameterized legs.

Two things in the other designs are worth naming, because both are easy to
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
  that container's context as its config context.** This is the `connectionMap`
  half of a conflation whose peer-to-peer half the `mtx*` family below records as
  closed; the map scan still classifies a mapped child's own surface from the
  map's parent interface rather than from the child's declared port. The
  `cppLeaf` blocks are mapped from `xpCppWrap`'s own parameterizable interfaces,
  so their Config structs are emitted in `xpCppWrap`'s context. A variant
  binding declared in `cppLeaf`'s own file is then attributed to a project that owns neither that
  context nor the instantiating assembler, and no descriptor is selected: the
  child instance falls back to the container's default Config, which does not
  carry the child's parameter and does not compile. The bindings are therefore
  declared in `cppAxis/yaml/xpCppWrap.yaml`, alongside the wrapper's own.
- **A connectionMap thunker member is named after the mapped instance alone.**
  Two maps from one container into the *same* child instance produce two members
  with the same name. Each shape here therefore has its own consumer block and
  its own child instance, which is also why `cppLeaf` declares four
  single-port blocks rather than one block with four ports.

## Recorded compile failure: `deparam` — generated C++ namespace ambiguity

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

## `shared` — the straight-through parameterized boundary

`shared` used to carry two independent compile failures. Both are closed and it
now builds and runs the full three-stage chain, so it has moved out of the probe
target and into `xproj-param`, and therefore into `pipeline-test`.

1. The downstream blocks' Config resolved to the upstream project's **default**
   config while the upstream block kept its variant config, so the channel
   payload and the producer port were different C++ types
   (`push_ack_out<videoSt<xpGainV0Config>>` against
   `push_ack_channel<videoSt<xpGainDefaultConfig>>`). Closed by the
   general interface-compatibility work: one declaration reached at two
   different Configs is now a cross-interface bind, and the junction gets a
   generated thunker.

2. The assembler container carries parameterized structures on its surface, so
   it is flagged parameterizable while remaining non-templated, and its
   trampoline registrar included the retired header form of the block
   (`fatal error: 'xpSharedTop.h' file not found`). Closed with the same
   `hasOwnParams` registrar gate the `mtx*` family records below: a
   non-templated block self-registers from its own module unit and needs no
   trampoline.

The db-time payload-compatibility check adjudicates one declaration
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

Rebinding it in a **downstream** project's file is rejected with the same
diagnostic. Both sides resolve through their own `v0` binding, so the check
compares 16 against 8 whichever file moved.

### Variant-binding sizing on the shared-include path

`PIXEL_WIDTH` declares `maxValue: 32`, and binding 64 is rejected at `make db`
from either side. `_post_validateVariantBindingSizing` resolves a block param
through `paramSourceKey`, so a downstream project that reaches the backing
constant by `include:` is held to the same bound, and the diagnostic names the
constant's declaring file rather than the binding's:

```
In ../../yaml/xpFilterShared.yaml:?: variant 'v0' binds param 'PIXEL_WIDTH' to 64,
exceeding the backing ipParameters constant 'PIXEL_WIDTH/../../../gain/yaml/xpGain.yaml'
maxValue 32; raise the constant's maxValue to cover the worst-case binding
```

A binding within the bound reaches the emitted artifacts. A project that names a
foreign constant in its own block's `params:` moves that block's config context
to the vendor's file, which makes the project's own binding of its own block
foreign to the context owner, so a third-party consumer selects it as a last
resort. `xpGain` declares `PIXEL_WIDTH: 12` and every `v0` binds 8, so `uFilter`
and `uSink` are typed at `xpFilterShared_xpFilterSharedV0Config` and
`xpSinkShared_xpSinkSharedV0Config`; each stage asserts the bound 8 and would
fail on the vendor default.

### Placing a declaring project's own foreign Config

The two structs above are owner-qualified and land in the declaring project's
registrar domain, the shape `dpMid/registrar/xpDpMid_xpDpMidVariantConfig.cppm`
already has:
`filterShared/registrar/xpFilterShared_xpFilterSharedVariantConfig.cppm` and its
`sinkShared` peer.

`newModule` and `createBuildManifest` enumerate these from the
`(declaringProject, block)` pairs `calcForeignConfigHeaders` records rather than
from assembler instances, so a project that declares a variant and instantiates
nothing still emits its own Config. That same record names the block whose
registrar domain hosts the artifact, which is the declaring project's
lowest-keyed assembler of the child, or the child itself when that project
assembles nothing. Hence the stamp here reads `--block=xpFilterShared
--parent=xpFilterShared`, and `getForeignConfigData` still derives the owner from
the parent. Regeneration belongs to the declaring project; `shared` compiles both
modules without regenerating either.

## The three-party parameterization matrix (`mtxIp` + `mtx*`)

A third, independent family. The families above vary one thing at a time about a
**thunked** junction; this one varies **who is parameterized** at a peer-to-peer
connection. Three parties meet there:

- **C**, the channel — the interface the assembling container names in
  `connections:`,
- **S**, the producer end's own declared `ports:` interface,
- **D**, the consumer end's own declared `ports:` interface.

All three are different declarations in every cell, which is what makes them
independent parties: an end whose declared `interfaceKey` differs from the
connection's is always adapted, so its parameterization is decided by its own
IP and never by the channel.

### Sub-projects

| Directory | `projectName` | Role | Status |
| :-- | :-- | :-- | :-- |
| `mtxIp/` | `xpMtxIp` | endpoint IP: producer and consumer, literal and parameterized spellings of each | generates |
| `mtxLit/` | `xpMtxLit` | row C=0: literal channel, four cells | **builds and runs** |
| `mtxTpl/` | `xpMtxTpl` | row C=1: parameterized channel typed by the container's own `Config` template parameter, four cells | **builds and runs** |
| `mtxElect/` | `xpMtxElect` | row C=1: parameterized channel typed by an unadapted end's Config (D5), two cells | **builds and runs** |
| `mtxBare/` | `xpMtxBare` | row C=1: parameterized channel with no Config source at all, four cells | **rejected at `make db`** |
| `mtxComp/` | `xpMtxComp` | cross-project reuse of `mtxElect`'s params-less transit container | **builds and runs** |

### Payload

One packed sequence everywhere: `tag@0 w8`, `data@8 w12`, `mark@20 w8`. The
resolved widths of all three parties have to agree exactly — `validatePorts`
compares per-field width and offset positionally and rejects any difference at
`make db` — so what varies between parties is how the middle field is
*declared*, not how wide it resolves. The pixel is 12 bits with a non-zero high
nibble and the marker sits above it, so a copy that truncated to a byte or
mis-sized the pixel is caught by the consumer's assertions rather than
delivering a plausible value.

Every cell drives four samples and every consumer checks every field of every
sample and its own bound width before voting the test done. `make xproj-matrix`
runs the three rows that build: 10 consumers, `checked 4 samples` each.

### Where the channel's Config comes from

The interesting axis is C=1: a parameterizable channel payload is one C++ type
per `Config`, so something has to supply that `Config`. There are exactly three
possibilities and the matrix has one row for each.

- **`mtxTpl` — the container's own class template parameter.** The container
  lists the channel's parameter in `params:`, so it is emitted as
  `template<typename Config>` and the channel spells `mtChSt<Config>`, resolved
  at the container's instantiation site. Nothing elects it: every end is
  adapted, so `channelParentConfig` returns nothing and
  `sc_struct_type_name` falls through to its `Config` placeholder — which is in
  scope precisely because the container is a template.
- **`mtxElect` — an unadapted end elects it (D5).** The channel is the
  producer IP's *own* declaration, so the producer's port shares the
  connection's `interfaceKey`, binds directly, stays in the election set and
  types the channel with its own variant Config: `miSrcParSt<xpMtxSrcParV0Config>`.
  The price is that C is then not an independent party — it *is* S.
- **`mtxBare` — nothing, which is rejected at `make db`.** Same as `mtxTpl` with
  `params:` removed from the container. There is no other way to bind a fixed
  variant to a container that declares no `params:`, so there is no `Config` for
  the channel to be typed at and no valid C++ realization of the design. This is
  the same rule as the own-surface one a scope up: a block that has to name a
  parameterizable type must declare the `params:` that give it a `Config`.
  Emitting a channel that spells an undeclared `Config` and letting the C++
  compiler find it is not an outcome, so the shape is refused with a diagnostic
  naming the channel, both ends and the fix:

  ```
  Block 'xpMtxBareWrap' assembles channel 'out' on parameterizable interface
  'mbChIf' between uSrcLL.out and uDstLL.in (file ../../yaml/xpMtxBareTop.yaml),
  but nothing supplies the Config that channel's payload is typed with: every end
  declares a different interface and is bridged by a generated adapter, and this
  block declares no params:. Add a params: declaration to this block so the
  channel resolves at the block's own Config, or declare one end's port on the
  connection's own interface so that end types the channel.
  ```

### Two authoring constraints this family used to run into — both CLOSED

Both came from one predicate: `calcBlockConfigInfo` classified an endpoint
block's own surface from the interface of every *connection* an instance of it
terminates, without consulting the port the block itself declared. An end whose
declared port carries a different `interfaceKey` is bridged by a generated
thunker and never names the connection's declaration, so it was being credited
with a surface it does not have. The scan now takes the block's own declared
port interface, and falls back to the connection's only for an end that declares
no port of that name and inherits it top-down.

- **A literal-ported endpoint could not be attached to a parameterized channel.**
  It was rejected for declaring no `params:`, so rows C=1 had to use literal
  endpoint blocks carrying an inert `params:` declaration whose parameter
  appeared nowhere on their surface. Those blocks are gone: every row now uses
  the same `xpMtxSrcLit`/`xpMtxDstLit` blocks as `mtxLit`, and `mtxTpl` is cell
  for cell the same design as `mtxLit` over the same endpoint blocks.
- **A parameterized channel relocated every endpoint's config context to the
  assembler's file**, so a variant binding declared in the IP's own file was no
  longer selected and the instance fell back to the assembler context's default
  Config. `mtxTpl` and `mtxBare` had to repeat every endpoint binding in their
  own top file; they no longer do, and each endpoint block's `configContext` in
  `mtxTpl` is `mtxIp/yaml/xpMtxIp.yaml`, the same file `mtxLit` resolves.

The `connectionMap` half of the same conflation is **not** closed: a block
reached through a foreign container's parameterizable interface still takes that
container's context, which is the constraint `cppAxis` records above.

### The gap `mtxTpl` exposed, by injection — CLOSED

**This is the shape `mtxTpl` was built to catch, and it is now caught at
`make db`.** The record of the unfixed behaviour is kept because it is what
makes the fixture worth running: the failure was silent everywhere a build could
have caught it.

The layout gate used to resolve a parameterized channel at an *endpoint's*
binding rather than at the **container's own** variant binding: `validatePorts`
picked the connection-side binding from the connection's endpoints
(leaf-parameterizable end, dst winning a tie), so a parameter owned by the
container and bound only in the container's variant was evaluated at the
constant's declared default instead.

Injected by rebinding `MTX_CH_WIDTH: 16` in `xpMtxTplWrap`'s variant while the
constant's declared `value:` stays 12 and every endpoint stays at 12: `make db`
was **clean**, `make gen` was clean, and the whole design **compiled** clean -
the push/ack adapter's only `static_assert` guards `sizeof` on the direct-copy
arm, not `_bitWidth`. The payload then mis-shifted at run time, and only on some
cells: the two whose adapters are direct-copy on both hops (`PP`) or pack/unpack
on both hops (`LL`) survived, because a whole-value copy ignores `_bitWidth`
entirely and a symmetric pack/unpack pair cancels its own error. The two mixed
cells (`LP`, `PL`) failed, on the *tag* field, which is the field furthest from
the width that changed. Without a per-field assertion at the consumer it was
invisible.

The connection-side binding now mirrors how the channel is actually typed: ends
that are adapted cannot elect it, and with none left to elect it resolves at
every variant the container block is instantiated at. The same injection is
rejected at `make db`, naming the disagreeing field, both structure declaration
sites, and `xpMtxTplWrap` at variant `v0` as the side the channel was resolved
for. Pinned by `unittest/test_container_param_channel_binding.py`.

The binding is restored to 12 in the tree; the injection is recorded, not carried.

### The trampoline registrar a transit container used to get — CLOSED

A container that only *transits* parameterizable structures is flagged
`isParameterizable` while staying non-templated, and the per-assembler
trampoline registrar was selected on that flag. The trampoline exists solely to
pick a class-template instantiation, so for a non-templated block it had nothing
to do and reached for the retired header form of the block instead:

```
mtxElect/registrar/xpMtxElectWrapRegistrar.cppm:9:10: fatal error: 'xpMtxElectWrap.h' file not found
```

The registrar's `cond` now keys on `hasOwnParams`, which is the property the
trampoline is actually about; every non-templated block, transit container
included, self-registers from its own module unit and gets no trampoline. That
was the only thing stopping `mtxElect` from running, and it was also the only
thing left stopping `shared`.

## `mtxComp` — cross-project reuse of a params-less transit container

`mtxElect`'s `xpMtxElectWrap` is the only reusable shape in the tree that is
flagged `isParameterizable` *without* declaring `params:` — parameterizable
structures cross its surface, but it is not a class template. `mtxComp`
(`projectName: xpMtxComp`) references the `xpMtxElect` project and instantiates
that container under its own top, which is the only way that shape is reached
across a project boundary.

Which side registers the child decides which `projectName` the assembler's
`createInstance` lookup must name, and the factory key is
`(blockType, variant, projectName)`:

- a child that declares its own `params:` is a class template with no
  registration in its own module unit; the parent-owned trampoline registers it
  under the **assembler's** projectName;
- every other child — transit container included — self-registers from its own
  module unit under its **owning** project and gets no trampoline.

So `xpMtxCompTop` must emit
`createInstance(..., "xpMtxElectWrap", "", "xpMtxElect")`. Naming the assembler
instead compiles and links cleanly and aborts at elaboration:

```
[Q_ASSERT] Attempted to create an instance uReusedWrap of an unregistered block type xpMtxElectWrap_model
```

which is why this row is a **run** target rather than a database assertion.

### Build and run

```
make xproj-matrix           # the three rows that build and run
make xproj-reuse            # cross-project reuse of the transit container
make xproj-matrix-probes    # mtxBare's db-time rejection, asserted to fail
```

`make xproj-matrix` and `make xproj-reuse` are both part of `pipeline-test`;
`xproj-matrix-probes` is not, because its cell is expected to fail.

## The shared-constant family (`cstIp` + `cstBind` + `cstUse`)

A fourth, independent family. The families above vary how a *declaration* is
reached across a boundary; this one varies how a **value** is. One question:
when a parameterizable IP and the supporting blocks around it must agree on a
width, can that width be stated once — as a named constant — and reach every
block that binds it?

### Sub-projects

| Directory | `projectName` | Role | Status |
| :-- | :-- | :-- | :-- |
| `cstIp/` | `xpCstIp` | the parameterizable IP: owns `CS_PIXEL_WIDTH`, its default, and the DUT block | generates |
| `cstBind/` | `xpCstBind` | assembler: the supporting blocks, and two cells binding two different constants | **builds and runs** |
| `cstUse/` | `xpCstUse` | the supporting blocks NAME the IP's constant, at a non-default value | **builds and runs** |

`cstIp/yaml/xpCstIp.yaml` knows nothing about any consumer. It declares
`CS_PIXEL_WIDTH: {value: 12, maxValue: 32}` in `ipParameters`, consumes it in
its own `xpCstDut` block's `params:` — which the orphan rule requires, and which
is why an IP cannot publish a parameter purely for downstream files to
`include:` — and binds its own default variant as `CS_PIXEL_WIDTH:
CS_PIXEL_WIDTH`, the symbolic form, so the default value is stated once.

`cstBind/yaml/xpCstSup.yaml` `include:`s that IP root and declares the
supporting blocks. `cstBind/yaml/xpCstBindTop.yaml` declares this assembler's
own use-case constant and assembles two chains.

### Payload

`tag@0 w8`, `cfg@8 w8`, `data@16 w<pixel width>`, `mark@(16+width) w8`. The
`cfg` field carries the width the **producing** block resolved, so a consumer
can compare it against its own; the marker sits above the pixel, so a width that
did not propagate shifts the marker rather than delivering a plausible value.

Two assertions carry the claim, and they are deliberately split by who is
entitled to know what:

- the **supporting** blocks — the assembler's own — assert their resolved width
  against the value their variant is supposed to bind, naming expected and
  actual;
- the **IP** asserts only the relation it can own without knowing any consumer:
  the `cfg` its producer stamped must equal the width this instance resolved.

Every consumer additionally checks every field of all four samples, and votes
end-of-test.

The emitted Configs are where the value lands, and cell B's 20 — stated once in
`CS_USE_WIDTH` — reaches all three:

```cpp
// cstBind/model/xpCstSupVariantConfig.h
struct xpCstSrcOwnUseConfig { static constexpr uint32_t CS_OWN_WIDTH   = 20; };
struct xpCstChkOwnUseConfig { static constexpr uint32_t CS_OWN_WIDTH   = 20; };
// cstBind/registrar/xpCstBind_xpCstDutVariantConfig.cppm
export struct xpCstBind_xpCstDutUseConfig
                            { static constexpr uint32_t CS_PIXEL_WIDTH = 20; };
```

Cell A's are the same three at 12, from `CS_PIXEL_WIDTH`'s own `value:`. The
run reports `checked 4 samples at pixel width 12` and `... at pixel width 20`.

### The two cells

- **Cell A, default.** `uSrcA` → `uDutA` → `uChkA`, all at variant `dflt`.
  Every binding in the cell names `CS_PIXEL_WIDTH` itself, so no number appears
  in any variant. All three resolve to 12. The supporting blocks are the **Inc**
  pair, which NAMES the IP's constant in its own `params:` and carries the IP's
  own `csDutIf` on its port — the prescribed reuse-by-include-scope shape.
- **Cell B, use case.** `uSrcB` → `uDutB` → `uChkB`, all at variant `use`.
  `CS_USE_WIDTH: {value: 20}` is an ordinary `constants:` entry in the
  assembler's file, and all three variants bind that one name. The value 20
  appears exactly once in the YAML and reaches all three emitted Configs.
  `xpCstDut`'s `use` variant is declared **at the assembler**, for a block this
  project does not own.

Cell B's supporting blocks are the **Own** pair, which declares a knob of its
own (`CS_OWN_WIDTH`) and binds *that* from the shared constant. That is one of
two legal choices, not a workaround: `cstUse` below is the same use case with an
Inc-style pair naming the IP's constant directly, and it resolves the bound 20.
Declare your own knob when the block genuinely owns one; name the IP's when it
does not.

### What a plain constant may be

Both are exercised, and both work: a variant binding's value may be an ordinary
`constants:` entry (`CS_USE_WIDTH`, cell B) or a parameterizable `ipParameters`
constant reached through `include:` (`CS_PIXEL_WIDTH`, cell A). The schema types
the field `value: const` (`config/schema.yaml:~326`), which resolves any
constant or enum visible in the binding row's own include scope; nothing
restricts it to parameterizable ones. That matters, because an assembler's
use-case constant *cannot* be an `ipParameters` one: it is used as a value and
is named by no block's `params:`, so it would have no same-file block param to
consume it and would fail the orphan rule.

### Variant completeness

Every declared variant must bind **every** parameter its block declares; there
is no default-fill for an omitted one
(`_post_validateVariantParameterCompleteness`). Each block here declares exactly
one parameter, so each variant lists exactly that one — the DUT's `dflt` and
`use` list `CS_PIXEL_WIDTH`, the Own pair's list `CS_OWN_WIDTH`. Completeness is
about the parameter *set*, not about the value: binding the parameter to its own
backing constant satisfies it just as a literal would.

### Thunkers and the layout gate

Every connection names the IP's own `csDutIf`, and every one of the four
DUT-to-supporting-block boundaries gets exactly one generated thunker
(`cstBind/model/xpCstBindWrap.cppm`):

```cpp
push_ack_port_thunker<csDutSt<xpCstDutDfltConfig>,           csDutSt<xpCstBind_xpCstSrcIncDfltConfig>, true> thunker_out_0_uSrcA;
push_ack_port_thunker<csDutSt<xpCstBind_xpCstChkIncDfltConfig>, csDutSt<xpCstDutDfltConfig>,           true> thunker_out_1_uDutA;
push_ack_port_thunker<csDutSt<xpCstBind_xpCstDutUseConfig>,  csOwnSt<xpCstSrcOwnUseConfig>,            true> thunker_out_2_uSrcB;
push_ack_port_thunker<csDutSt<xpCstBind_xpCstDutUseConfig>,  csOwnSt<xpCstChkOwnUseConfig>,            true> thunker_out_3_uChkB;
```

Which *side* carries the thunker follows the channel election, not the block's
role. An end whose declared port interface differs from the connection's is
adapted and cannot elect, so on `out_2`/`out_3` the Own pair is adapted and the
DUT types the channel. On `out_0`/`out_1` both ends declare `csDutIf`, so the
election prefers dst: `uDutA` types `out_0` and `uChkA` types `out_1`, which
leaves the DUT itself as the adapted end of `out_1`. Four boundaries, four
thunkers, either way.

Cell A's pairs are one declaration reached at two Configs; cell B's are two
declarations. Both are cross-interface binds, and `checkInterfacePair` compares
each side's packed form under its own variant bindings before either is emitted.
That gate is live here: rebinding `uChkB` to `dflt` while `uDutB` stays on `use`
— the divergence a per-cell constant is meant to prevent — is rejected at
`make db`:

```
Block xpCstChkOwn connection '...' (file ../../yaml/xpCstBindTop.yaml) binds external
interface csDutIf to child uChkB.in declared as csOwnIf (file ../../yaml/xpCstSup.yaml):
per-field _bitWidth must agree at every payload position, but field index 2 of
structureType 'data_t' differs: parent field 'data' has _bitWidth 20 at bit offset 16 in
structure 'csDutSt' ... while child field 'data' has _bitWidth 12 at bit offset 16 in
structure 'csOwnSt' ...
  parent side: ... resolved for block 'xpCstDut' (project xpCstIp) at variant 'use'
  child side:  ... resolved for block 'xpCstChkOwn' (project xpCstBind) at variant 'dflt'
```

The injection is recorded, not carried; the tree binds both ends at `use`.

### `cstUse` — the supporting blocks name the IP's constant

The shape cell B would have if the supporting blocks NAMED `CS_PIXEL_WIDTH` in
their own `params:` instead of declaring a knob of their own. All three variants
bind the assembler's `CU_USE_WIDTH`, and all three blocks resolve it: the run
reports `checked 4 samples at pixel width 20` against the IP's declared default
of 12. Reaching a parameter through `include:` scope is a legal authoring
choice, and it works at any value.

**What makes it work.** A block param's backing constant is carried on the row
as `blocksparams.paramSourceKey` — a foreign key onto `constants`, resolved
through the param row's own include chain. The sibling `paramKey` qualifies the
param's name with the file declaring the **block**, so it is a block-scoped
identity and not a constant key; for a block whose backing constant is reached
by `include:` the two differ. Every consumer that needs the constant reads the
source link: the layout gate's binding resolver (`SiteBindingIndex`, feeding
`checkInterfacePair`), the `maxValue` sizing check
(`_post_validateVariantBindingSizing`), the parameterized declaration sets
(`deriveParameterizedDeclSets`), the Config context (`calcBlockConfigInfo`), the
orphan check (`_validateIpParametersLinkage`), and the SystemVerilog
module-parameter spelling (`templates/systemVerilog/package.py`).

Before that link existed this cell was a probe asserted to FAIL. The binding was
filed under the block's file, was never found, and the supporting blocks fell
back to the constant's declared 12 while the same-file DUT resolved the bound
20 — so the layout gate reported a genuine-looking width disagreement between
two sides the author had bound identically, while the emitted C++ Config carried
20 for all three. The two directions of that defect, a false rejection and a
silent acceptance of a real divergence, are recorded in
[`../../plans/plan-parameter-sharing.md`](../../plans/plan-parameter-sharing.md) §5 B1.

**A separate gap on the same path, met while shaping `cstBind`.** A structure
declared in the *including* file whose width comes from the *included* constant
does not compile: the per-context round-trip test structs
(`--template=structures --section=testStructsCPP`) are instantiated at Configs
built from that context's own parameterizable constants, which do not carry the
included one.

```
model/xpCstSupIncludes.cppm:52:55: fatal error: no member named 'CS_PIXEL_WIDTH'
   in 'xpCstBind_xpCstSup_test_ns::xpCstSupTestConfigDefault'
```

That is why `cstBind`'s Inc blocks carry the IP's own `csDutIf` rather than a
payload of their own. They still get their own Config and their own thunker, so
nothing about the boundary shape is lost. This gap is independent of the value
path and is still open.

### Build and run

```
make xproj-const            # all three cells build and run
```

`make xproj-const` is part of `pipeline-test`. It shares no sub-project with any
other target, so it needs no ordering against them. `cstUse` shares `cstIp` with
the cells above it and is therefore sequenced after them within the target.

## The depth family (`dpLeaf` + `dpMid` + `dpTop`)

`containerParam:` parameter inheritance through two project levels. The customer
(`dpTop`) states one algorithm on the wrapper it owns; the mid-level IP
(`dpMid`, the ISP analogue) declares that parameter but states no value for it,
sourcing it from its container; the leaf (`dpLeaf`, the debayer analogue) nested
inside the mid resolves it. The mid never declares the leaf's `DP_ALGO` at all,
so the value reaches the leaf through two single-level links rather than being
restated.

`DP_ALGO` appears in no width and no packed position, which separates variant
SELECTION from variant LAYOUT: a wrong algorithm changes no layout, so no
db-time gate can see it and only a run can catch it.

Three customer configurations of the same mid-level IP resolve independently at
their nested leaves, at algorithms 5, 6 and 7. Each has its own checker, which
reads the algorithm it should expect from its OWN Config — an independent path
through the generator from the one that reaches the leaf — and asserts it
per sample.

See `dpTop/README.md` for the full measurement record, including what the shape
rejects and what it does not yet do.

### Build and run

```
make xproj-depth            # dpLeaf, dpMid, dpTop generate; dpTop runs
```

`make xproj-depth` is part of `pipeline-test`. It shares no sub-project with any
other target, so it needs no ordering against them. `dpMid` generates but does
not run: its standalone top's driver and sink are empty scaffolds, so its own
run cannot reach an end of test. `dpTop` is the buildable top.

## The inheritance family (`inhVar`)

The OTHER parameter-inheritance mechanism. `containerParam:` sources named
parameters one at a time; `inheritContainerParam: true` types a contained
instance with the CONTAINER's whole Config, so the child declares no variant of
its own. Both mechanisms make the child a FAMILY of C++ types - one member per
Config the container is instantiated at - and the factory key
`(blockType, variant, projectName)` has no Config dimension to select a member
with, so in both cases the container names the child's implementation class at
its `createInstance` site.

`inheritContainerParam` requires container and child to be owned by ONE project,
so unlike the depth family this cell is a single project, not a composition.

One container block, `xpInhCont`, is instantiated at TWO variants (`default` and
`alt`), each holding two inheriting leaves. That is the whole point: while the
child was resolved through the key it could only be registered at the
container's DEFAULT Config, so every other container variant's generated
`dynamic_pointer_cast` returned null and the container dereferenced it while
binding the child's ports. The file is named for the container block and the
first variant is named `default` on purpose - that makes
`<contextStem>DefaultConfig` and the variant's own struct the same identifier,
which is the shape the product tree's `debayer` is in, and is why one variant
hid the defect there.

Each chain's checker reads the algorithm it should expect from its OWN Config and
asserts it per sample, so `uContDef`'s leaves must resolve 1 and `uContAlt`'s
must resolve 6.

```
make xproj-inherit          # inhVar generates and runs
```

`make xproj-inherit` is part of `pipeline-test`. It shares no sub-project with
any other target, so it needs no ordering.
