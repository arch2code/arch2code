# Research: Multi-Config-Per-Block Bindings (T9 Step 10)

## Purpose

The current per-block trampoline (T9, Step 9 outcome) registers exactly
one C++ Config policy per parameterized block: the auto-derived
`<context>DefaultConfig`. Every variant of the same block registers
against the same `ip<ipDefaultConfig>` instantiation. Step 10 of
`plan-block-registration.md` calls for a regression in which the same
block is reachable through the factory under two distinct Config
policies, with distinct C++ instantiations.

This document records the design surface that Step 10 touches and the
decisions that have been settled in conversation. It feeds the
forthcoming revision of `plan-block-registration.md`.

## Background

### Existing mechanisms

- **Variants.** Per-block enumeration of named overrides, declared
  alongside the block (e.g., `variant0`, `variant1` for `ip`).
- **Instances.** Each instance references a variant
  (`uIp0: { variant: variant0 }`).
- **`parameters:` section.** Maps `(variant, param)` to a value.
  Persists into the project DB.
- **`addParam` runtime table.** The trampoline emits one entry per
  `(block, variant, param)` triple. Block constructors call
  `getParam(...)` at runtime to read variant-specific values.
- **`<context>DefaultConfig` struct.** Auto-derived from the
  parameterizable block's context. Contains the block's *default*
  constant values, not variant-specific values.

### What is currently derived per variant versus per block

- **Per variant (runtime, today).** The `addParam` table carries each
  variant's parameter values. Block constructors look up
  `IP_DATA_WIDTH` (etc.) at construction time and size runtime
  resources accordingly. This works for fields whose *type* does not
  depend on the value (the field is always `uint64_t` and only its
  meaningful bit width changes).
- **Per block (compile time, today).** The `Config` struct exposes
  block-default values via `Config::IP_DATA_WIDTH`. All variants share
  the same C++ instantiation (`ip<ipDefaultConfig>`). Compile-time
  expressions that depend on `Config::*` therefore see the block
  defaults regardless of variant.
- **Worst-case sizing.** `processYaml.py::calcAddresses` already
  performs cross-variant max computations for memory sizing. The
  precedent confirms the codebase already accommodates variant-aware
  generator-side decisions.

## Direction — Path C (variant ≅ Config)

Path C is adopted. Variants and Configs are unified: every variant
maps 1:1 to a Config policy in C++ and 1:1 to a parameter set in SV.
The runtime `addParam` / `getParam` path is retired because all of its
values are reachable through `Config::*` at compile time.

Two narrower paths were considered and rejected:

- **Path A — trampoline-only multi-Config.** Generate per-variant
  Configs and emit them in the trampoline; leave parent containers on
  a single Config; validate via a standalone factory-call regression.
  Rejected because it leaves variant and Config as parallel notions.
- **Path B — live multi-Config in the instance tree, addParam
  retained.** Path A plus container/connection rework, but variants
  and Configs remain independent dimensions. Rejected for the same
  reason.

Path C subsumes both: variant *is* the Config. SystemVerilog's
elaboration model — each instance is a distinct compile-time entity
with its own parameter set — is the guiding shape for the SC side.

## Decisions

### D1 — Per-variant Config derivation

- **Text stability of the block class.** If a block is declared
  parameterizable in YAML, its `<block>.h` / `<block>.cpp` are emitted
  as a class template (`template<typename Config> class <block> { ... };`)
  regardless of whether any variant is declared. The block's own
  source text is project-independent and variant-independent. The
  per-project trampoline is the only TU that names specific Config
  types; the block's own files do not change as variants are added
  or removed.
- `<context>DefaultConfig` is eliminated as a special case.
- Every parameterizable block carries one Config struct per variant.
- Blocks that declare no variants in YAML are treated as having a
  single anonymous variant whose values are the block's defaults. The
  anonymous variant is trampolined like any other.
- Selection from the factory uses the variant string. The anonymous
  variant is selected by passing an empty variant string ("").
- Naming convention:
  - **Anonymous variant** (block declares no named variants): the
    Config is `<block>Config` (e.g., `ipConfig`). No variant suffix.
  - **Named variant**: the Config is `<block><Variant>Config`
    (e.g., `ipVariant0Config`, `ipFastConfig`).
  - A given block has either an anonymous variant alone or one or
    more named variants — never both — so `<block>Config` and
    `<block><Variant>Config` never collide.
- **Intra-block dedup.** Variants on the same block whose parameter
  values are byte-for-byte identical share a single Config struct.
  Variant identity is preserved at the factory-key level (both
  variants register against the same lambda).
- **Hierarchical label-only variants are supported.** Two independent
  parent blocks (e.g., `ip1` and `ip2`) may each declare a variant of
  a shared internal block (e.g., `ip3`) whose parameter values happen
  to be byte-identical but whose variant names differ. The two Config
  structs (e.g., `ip3VariantAConfig` and `ip3VariantBConfig`) are
  emitted as distinct C++ types. The corresponding template
  instantiations `ip3<ip3VariantAConfig>` and `ip3<ip3VariantBConfig>`
  are distinct C++ types but layout-compatible; the compiler may
  share machine code via identical-COMDAT folding, and the linker
  handles the duplicate symbols via weak/COMDAT linkage. This
  produces no compile or link errors — at most minor code duplication
  if the toolchain does not fold.
- Per-variant Config structs land in the block's auto-generated
  `<context>Config.h` (same header used today).

### D2 — Eval re-evaluation under variant overrides

- Deferred to a follow-up plan step.
- Intent: move `isParameterizable` constants into compileable output
  in each target language (Config field in C++,
  `parameter`/`localparam` in SV). Eval expressions resolve at
  language-native compile time, not at YAML-processing time.
- Until that work lands, the generator continues to resolve eval
  expressions in `processYaml.py` against each variant's override
  set.

### D3 — Trampoline emission and `configTag` retire

- The factory key collapses from `(blockType, variant, configTag)` to
  `(blockType, variant)`.
- The `noConfigTag` sentinel and the empty-variant fallback both
  retire. The anonymous variant ("") replaces them: every factory
  lookup passes a variant string (empty or named).
- The trampoline emits one `registerBlock(...)` lambda per variant
  per block. The lambda constructs `make_shared<<B><PerVariantConfig>>`.
- Caller code: `instanceFactory::createInstance(name, instance,
  blockType, variant)` is the only signature.

Rationale: under variant ≅ Config, the variant string identifies the
Config unambiguously. `configTag` was solving the case where the same
`(blockType, variant)` pair could attach to two independent Configs;
that case does not exist when variant *is* the Config.

### D4 — Container member-type coupling: Option (a)

The parent container declares each parameterized child with its
concrete per-variant Config:

```cpp
std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
std::shared_ptr<ipBase<ipVariant1Config>> uIp1;
```

This was chosen on cleanliness alone (the user confirmed generated
code carries no real cost). It preserves full compile-time type
safety, mirrors the SV elaboration model, and matches the trampoline's
own per-variant emission. Casts at construction are direct
(`dynamic_pointer_cast<ipBase<ipVariant0Config>>(...)`).

The two rejected alternatives are summarised in Appendix C.

The cleanliness of Option (a) depends on resolving D5 (connection-type
coupling) so the parent does not also have to thread per-instance
Configs into its channel declarations.

### D5 — Connection / channel-type coupling

Working shape:

- YAML's `isParameterizable` flag is authoritative. A struct is
  templated on `Config` in C++ when the YAML flag is set; otherwise
  non-templated. SV's view governs; the resolved-type collapse pass
  is withdrawn.
- The parent container is no longer itself a class template (it
  carries no own `Config`). Each channel between parent and a
  parameterizable child is typed by *the child's Config*. Channels
  between two children with the same Config use that Config.
- Cross-Config connections (one producer feeding differently-
  Configed consumers) are handled by the producer block declaring
  per-port parameters in its Config; each cross-interface bind
  goes through the thunker mechanism settled in Q10/R2. See Q11
  (resolved) for the worked case.
- External boundary surfaces may need a non-templated form of the
  structure, with user code casting between the templated internal
  form and the non-templated external form.

The remaining open items are the protocol-coverage details under
Q10 (push_ack, axi, apb thunkers; diagnostics on packed-form
failure; bottom-up vs. top-down `ports:` checking semantics).
Q11 is closed. Appendix B walks through the SV reference and the
SC mirror that motivate this shape.

### D6 — Testbench / DUT cast site (subsumed)

The testbench is fully YAML-declared. If a regression needs to
exercise two Configs of the same block, the YAML declares two DUT
instances with distinct variants. Each generated DUT pointer's type
follows from D4 (per-instance concrete Config). There is no separate
"TB cast site" issue.

### D7 — Verilated wrappers and tandem registration

Out of scope for Step 10. Verilated wrapper migration to per-block
trampolines is tracked separately in `plan-block-registration.md`
Step 12. Tandem registration (Plan-9) is a separate iteration. Both
inherit the `(blockType, variant)` key shape decided here.

### D8 — Address sizing: all variants share one address map

All variants of a block share the same address map. Worst-case sizing
across variants is preserved precisely for this reason: a single
firmware image targeting the block must work across every variant
(e.g., `variant0` with `IP_MEM_DEPTH=16` and `variant1` with
`IP_MEM_DEPTH=8`), so the address map sizes against the maximum
(`maxValue=32`).

`calcAddresses` already performs cross-variant max computations
(`_resolveBlockParamMaxWordLines`). This precedent is preserved
verbatim under Path C; address maps remain a function of "the union
of all variants" rather than per-variant. (This decision closes the
former Q13.)

### D9 — Cross-cutting decisions

- **`addParam` retirement.** The full `addParam` / `getParam` API and
  its callers in block constructors are removed. Block constructors
  read parameter values from `Config::*` directly.
- **`IP_NONCONST_DEPTH` absorption.** The "no backing constant"
  pattern is an addParam-era artifact. In the new world it surfaces
  as a normal SV `parameter` and as a normal Config field
  (`Config::IP_NONCONST_DEPTH`). The YAML schema can drop the
  separate distinction.
- **Label-only variants.** None exist in the codebase and none need
  to be supported. Every variant overrides at least one parameter.
- **SystemVerilog is the guiding light.** The model platform supports
  only what SV can express. Per-variant Configs in C++ and per-variant
  parameter sets in SV are intentionally the same shape.

### D10 — Bottom-up port declaration

Port declaration is **orthogonal to parameterization**. Any block —
parameterizable or not — may declare its ports explicitly in a
`ports:` map keyed by port name:

```yaml
blocks:
    ip:
        ports:
            dataIn: { interface: ipDataIf, direction: dst }
```

The existing schema is **top-down**: a block's ports are inferred
from `connections:` and `connectionMaps:` that touch the block. The
top-down path is retained for blocks that prefer it. The new
**bottom-up** path lets a block declare its own ports first; the
generator validates that any subsequent connection / connectionMap
references match the declared shape.

- The dict shape (key = port name) reflects the existing invariant
  that port names are unique within a block. No list.
- Direction values reuse existing `src` / `dst` semantics. No new
  direction terminology is introduced.
- The mechanism is the same for parameterizable and
  non-parameterizable blocks. The difference is only that
  non-parameterizable blocks do not need **interface remapping**
  (the cross-interface bridge described under Q10's worked
  example), because their connections describe the port
  fully on the connection side. Parameterizable blocks need
  bottom-up declaration to capture the parameterization that
  top-down inference cannot reconstruct.
- The connectionMap schema is unchanged (R1): flat shape with
  `interface`, `block`, `name`, `direction`, `instance`,
  `instancePort`. The cross-interface bind is detected implicitly
  when the connectionMap's `interface` differs from the child's
  declared port interface.
- Detailed checking semantics — when bottom-up declarations
  interact with top-down inference, what diagnostics fire, how
  partial declarations are handled — are deferred. The decision
  records the direction; mechanics are settled after the research
  completes.

This bottom-up mechanism was anticipated in the schema design. It
is the schema feature that unblocks parameterized IP ports while
remaining available to any block that wants to declare its surface
explicitly.

## Open Questions

These remain to be resolved before the plan is rewritten.

### Q10 — Channel and port type derivation under per-variant Configs

The user's framing: trust YAML's `isParameterizable` flag. A struct
is templated on `Config` in C++ when YAML says it is parameterizable;
otherwise it is non-templated. Channels and ports follow the same
rule by inheritance: a channel of a parameterizable struct is itself
templated; a channel of a non-parameterizable struct is non-templated.

The remaining open generator-side decisions:

- For the "channel between parent and one parameterizable child"
  case, the parent's channel is typed by *the child's Config*. The
  parent itself is no longer a class template (D4); each channel is
  typed by the connected child.
- For the "one producer feeding multiple differently-Configed
  consumers" case — see Q11 (resolved). The producer carries
  per-port parameters in its Config; each bind is a normal
  cross-interface bind handled by the Q10/R2 thunker.
- For the "parent exposes an external interface that internally
  binds to a parameterized child" case — see the worked example
  below. This is the case the user-code cast cannot handle, because
  the connection from the parent's external port into the child's
  internal port is generated, not user-written.

#### Worked example — non-parameterized external, parameterized internal

The scenario from the user: a block exposes two similar
ready/valid interfaces externally — one carries 8-bit data, the
other 16-bit. Internally, those interfaces feed two instances of a
shared parameterizable IP whose data type is `Config::IP_DATA_WIDTH`.
Protocol requires one channel per interface; the parent cannot
unify them with user-code casts because the cross-type binding
sits at the auto-generated parent-to-child wiring site.

##### `ip.yaml` — the parameterizable IP

The parameterizable IP declares its own constants, types, struct,
interface, port (working syntax — see "Open YAML questions" for the
final shape), and variants. The block source text is project- and
variant-independent (D1 text-stability invariant).

```yaml
# ip.yaml — parameterizable IP defined in its own file.

ipParameters:
    constants:
        IP_DATA_WIDTH:
            value:    8
            maxValue: 16
            desc:     "Per-instance data width, max 16 bits"
    types:
        ipDataT:
            width:        IP_DATA_WIDTH
            maxBitwidth:  16
            desc:         "IP data word, parameterizable"

structures:
    ipDataSt:
        data: { varType: ipDataT, desc: "IP data field" }

interfaces:
    ipDataIf:
        desc:          "IP data ready/valid stream"
        interfaceType: rdy_vld
        structures:
            - { structure: ipDataSt, structureType: data_t }

blocks:
    ip:
        desc:    "Parameterizable IP under test"
        params:  [IP_DATA_WIDTH]
        hasMdl:  true
        hasRtl:  true
        # Working syntax for declaring an internal port whose
        # interface and structure are parameterized. The exact
        # ports: schema is TBD (see Open YAML questions); what
        # matters here is that the IP has an inward-facing
        # `ipDataIf` port whose struct type is `ipDataSt<Config>`.
        ports:
            dataIn: { interface: ipDataIf, direction: dst }
```

The `ip.yaml` file does not declare any variants. Variants are
declared by the parent that instantiates `ip`, because variant
choice is a usage-side concern. `ip.yaml` carries only what the IP
itself owns — its parameters' defaults, types, structures,
interfaces, block declaration, and ports.

##### Parent YAML — `container.yaml`

The parent declares its own external types, structs, and
interfaces (non-parameterized in this example), instantiates two
`ip` variants, and uses connectionMaps to wire each external
interface through to one child's parameterized port.

```yaml
# container.yaml — parent that exposes non-parameterized externals.

include:
    - ip.yaml

constants:
    DATA_WIDTH_8:  { value: 8 }
    DATA_WIDTH_16: { value: 16 }

types:
    data8T:  { width: DATA_WIDTH_8,  desc: "Fixed 8-bit data" }
    data16T: { width: DATA_WIDTH_16, desc: "Fixed 16-bit data" }

structures:
    data8St:  { data: { varType: data8T  } }
    data16St: { data: { varType: data16T } }

interfaces:
    data8If:
        desc:          "External 8-bit ready/valid stream"
        interfaceType: rdy_vld
        structures:
            - { structure: data8St,  structureType: data_t }
    data16If:
        desc:          "External 16-bit ready/valid stream"
        interfaceType: rdy_vld
        structures:
            - { structure: data16St, structureType: data_t }

blocks:
    container:
        desc:   "Parent exposing two non-parameterized data interfaces;
                 each fans through to one parameterized ip instance"
        hasMdl: true
    src: 
        desc: if source
        hasMdl: true
    container_tb:
        desc:   "Test container"

instances:
    container_tb: { instanceType: container_tb, instGroup: top }
    u_container:  { container: container_tb,    instanceType: container }
    u_src:        { container: container_tb,    instanceType: src }
    u_ip8:        { container: u_container,     instanceType: ip, variant: variant8  }
    u_ip16:       { container: u_container,     instanceType: ip, variant: variant16 }

# Variant table for ip. Declared in the parent that instantiates ip,
# not in ip.yaml itself: variant choice is a usage-side concern.
parameters:
    ip:
        - { variant: variant8,  param: IP_DATA_WIDTH, value: 8  }
        - { variant: variant16, param: IP_DATA_WIDTH, value: 16 }

# External producer/consumer connections at the testbench level
# (omitted) declare data8If and data16If sources that connect to
# u_container's external ports.

# Cross-interface connectionMap. External side specifies the parent's
# higher-level interface, name, and port. Internal side specifies the
# instance, its port, and its interface. When external and internal
# interface types differ, the generator runs a packed-form
# compatibility check and emits a bridge if the check passes.
connections:
  - {interface: data8If,  src: u_src, dst: u_container, name: small  } # 
  - {interface: data16If, src: u_src, dst: u_container, name: big    } # 

connectionMaps:
  - {interface: data8If,  block: container, name: small, direction: dst, instance: u_ip8,  instancePort: dataIn}
  - {interface: data16If, block: container, name: big,   direction: dst, instance: u_ip16, instancePort: dataIn}
```

##### Generated C++ shape

The channels live in `container_tb` (the parent of `u_src` and
`u_container`), where the connection between them is declared.
`container` is non-templated (D4); inside it, the connectionMap
forwards each external port to a child instance's parameterized
port. The cross-interface thunking happens at this internal
boundary, not at the testbench-level channel.

```cpp
// container_tb — declares the channels for the u_src ↔ u_container
// connections (small / big from the connections: name field) and
// binds both endpoints to them.
class container_tb : public blockBase, public container_tbBase {
    rdy_vld_channel<data8St>  small;
    rdy_vld_channel<data16St> big;

    std::shared_ptr<srcBase>       u_src;
    std::shared_ptr<containerBase> u_container;
};

container_tb::container_tb(...)
    , u_src      (std::dynamic_pointer_cast<srcBase>      (
         instanceFactory::createInstance(name(), "u_src",       "src",       "")))
    , u_container(std::dynamic_pointer_cast<containerBase>(
         instanceFactory::createInstance(name(), "u_container", "container", "")))
{
    u_src      ->small(small);
    u_container->small(small);
    u_src      ->big(big);
    u_container->big(big);
}
```

```cpp
// container — non-templated. External ports are typed by the
// non-parameterized interfaces declared in container.yaml.
// Internal children are parameterized per variant (D4). The
// connectionMap forwards each external port to a child's port
// across an interface boundary; this is where structure thunking
// happens.
class container : public blockBase, public containerBase {
    // External non-parameterized port views (declared by the
    // non-parameterized interface on container's surface).
    rdy_vld_port<data8St>::consumer  small;
    rdy_vld_port<data16St>::consumer big;

    // Internal parameterized children, each with its own Config.
    std::shared_ptr<ipBase<ipVariant8Config>>  u_ip8;
    std::shared_ptr<ipBase<ipVariant16Config>> u_ip16;
};

container::container(...)
    , u_ip8 (std::dynamic_pointer_cast<ipBase<ipVariant8Config>> (
         instanceFactory::createInstance(name(), "u_ip8",  "ip", "variant8")))
    , u_ip16(std::dynamic_pointer_cast<ipBase<ipVariant16Config>>(
         instanceFactory::createInstance(name(), "u_ip16", "ip", "variant16")))
{
    // ConnectionMap binds: external port → child port across
    // an interface boundary. The exact shape of this bind depends
    // on which thunking option is chosen; see the next section.
    //
    //   small (data8If, data8St)        →  u_ip8 ->dataIn (ipDataIf, ipDataSt<ipVariant8Config>)
    //   big   (data16If, data16St)      →  u_ip16->dataIn (ipDataIf, ipDataSt<ipVariant16Config>)
}
```

##### Where the structure thunking happens — options

The cross-interface bind requires translating between two distinct
C++ struct types whose packed-form layouts are compatible. The
question is *where* in the SC stack that translation lives.

Three constraints frame the design:

- The IP block's port is always typed by the parameterized struct
  (`ipDataSt<Config>`). The IP cannot accept a non-templated
  port type without giving up its compile-time parameter
  visibility.
- The channel object itself is declared by the parent of the
  connection (here `container_tb`). That parent may sit far above
  the parameterized IP and may not have visibility to the IP's
  Config. A channel typed by the IP's Config would require the
  testbench-level code to import per-variant Config headers.
- The connectionMap (or connection) endpoints may share an
  interface meta-protocol but use distinct struct types
  (`data8St` vs. `ipDataSt<Config>`). The translation must be
  field-by-field according to the packed-form compatibility
  check.

Below are the candidate locations for the thunk, with a sketch of
each.

###### Option T1 — Channel carries the non-templated struct; IP-side adapter unpacks

The channel uses the parent-side non-templated struct
(`rdy_vld_channel<data8St>`). The IP block's port is bound through
a generator-emitted adapter that reads a `data8St` from the
channel and presents an `ipDataSt<Config>` on the IP's port.

```cpp
// Inside container, generator emits:
//   typed_thunk<data8St, ipDataSt<ipVariant8Config>> thunk_dataIn_8;
//   small.bind(thunk_dataIn_8.upstream());
//   u_ip8->dataIn.bind(thunk_dataIn_8.downstream());
```

- Pros: Channel stays typed by the parent's surface; testbench
  needs no Config visibility. IP block sees its native templated
  port.
- Cons: One thunk object per cross-interface bind. Adds a small
  SC module (or non-module helper) per bind. Threading model
  needs to forward ready/valid handshake events.
- Visibility: The thunk lives in `container.cpp`, which has
  visibility to both `data8St` and `ipDataSt<Config>` (via
  includes). Channel-side parents do not need Config visibility.

###### Option T2 — Channel carries the templated struct; producer-side adapter packs

The channel uses the IP-side templated struct
(`rdy_vld_channel<ipDataSt<ipVariant8Config>>`). The non-templated
producer (`u_src`) is bound through a generator-emitted adapter
that takes a `data8St` from `u_src` and writes an
`ipDataSt<Config>` into the channel.

- Pros: IP port binds directly with no adapter on its side.
- Cons: The channel lives in `container_tb`, which would now need
  Config visibility — `container_tb` must include the IP's Config
  headers. This violates the principle that the testbench-level
  code is Config-agnostic. Rejected on visibility grounds.

###### Option T3 — Channel itself does the conversion (bridging-channel template)

Define a `bridgingChannel<UpType, DownType>` template that exposes
two endpoint views — one of `UpType`, one of `DownType` — and
performs pack/unpack internally on each transfer.

```cpp
// In container_tb, declare a normal channel (parent side):
rdy_vld_channel<data8St> small;
// Inside container, wrap small in a bridging channel for the IP:
bridgingChannel<data8St, ipDataSt<ipVariant8Config>> small_bridge(small);
u_ip8->dataIn.bind(small_bridge.down());
```

- Pros: Conversion encapsulated in one channel-shaped object.
  Endpoints see their native types.
- Cons: Channels are core SC objects with complex pack/unpack and
  protocol handshake semantics. Subclassing them is a heavier
  change than a thin adapter. Requires duplication of the
  channel's protocol logic.

###### Option T4 — Thunker class with encapsulated channel (settled)

A small templated thunker class is held as a member of the
surrounding container. Its constructor takes the two consumer ports
that already exist on the design surface (the parent's external
port and the child's internal port), owns the IP-side channel
internally, performs the elaboration-time bind of the child's port
to that channel, and launches the forwarding thread via `sc_spawn`.
The conversion is a packed-form round trip (`outVal.unpack(inVal.pack())`),
which is safe under the YAML-side packed-form compatibility check.

```cpp
// builder/base/interfaces/rdy_vld/rdy_vld_port_thunker.h
template <class UpT, class DownT>
class rdy_vld_port_thunker
{
public:
    rdy_vld_port_thunker(const char*           name_,
                         rdy_vld_in<UpT>&      upPort,
                         rdy_vld_in<DownT>&    downPort,
                         std::string           blockName)
      : m_up(upPort)
      , m_chDown((std::string(name_) + "_ch").c_str(), blockName)
    {
        downPort(m_chDown);                       // elaboration-time bind
        sc_spawn([this]() { this->thunk(); });
    }
private:
    void thunk()
    {
        while (true) {
            UpT   inVal;
            DownT outVal;
            m_up->readClocked(inVal);
            // Packed-form round-trip. The cast bridges any
            // _packedSt size difference; safe because _bitWidth
            // matches (see "Packed-form compatibility" below).
            outVal.unpack(static_cast<typename DownT::_packedSt>(inVal.pack()));
            m_chDown.writeClocked(outVal);
        }
    }
    rdy_vld_in<UpT>&                m_up;
    sc_core::rdy_vld_channel<DownT> m_chDown;
};
```

For protocols carrying two channel-side types (req_ack uses R, A),
the thunker takes four type parameters — `(UpR, UpA, DownR, DownA)` —
with `reqReceive` / `req` / `ack` on the protocol-specific path. The
shape is otherwise identical: one constructor, encapsulated channel,
elaboration-time `downPort(m_chDown)` bind, `sc_spawn` of the
forwarding thread.

Container plumbing collapses to one declaration plus one initialiser
per cross-interface bind:

```cpp
class container : public blockBase, public containerBase {
    rdy_vld_in<data8St>                       small;
    std::shared_ptr<ipBase<ipVariant8Config>> u_ip8;

    // Generator-emitted per cross-interface bind:
    rdy_vld_port_thunker<data8St, ipDataSt<ipVariant8Config>>  thunker_uIp8;
};

container::container(...)
    : small("small")
    , u_ip8(std::dynamic_pointer_cast<ipBase<ipVariant8Config>>(
          instanceFactory::createInstance(name(), "u_ip8", "ip", "variant8")))
    , thunker_uIp8("thunker_uIp8", small, u_ip8->dataIn, name())
{
}
```

Settled details:

- **Class form, not free function.** The IP-side port binding must
  happen during SC elaboration; only a class constructor (held as a
  container member) reaches that elaboration phase cleanly. A free
  function called from `sc_spawn` runs after elaboration and cannot
  bind ports.
- **Encapsulated channel.** The thunker owns its IP-side channel as
  a member. The channel implements both `<protocol>_in_if` and
  `<protocol>_out_if` directly, so no separate producer port is
  required; the thunker writes via the channel's interface. The
  channel's `m_writer` pointer remains null; per `register_port` it
  drives only static design-rule checks, so direct writes are
  functionally fine.
- **Conversion via packed-form round trip.** `pack()` / `unpack()`
  are already emitted on every structure. The YAML-side packed-form
  compatibility check (see "Packed-form compatibility — the actual
  mechanism" below) enforces that the two structures' `_packedSt`
  underlying types match, which is the precondition.
- **Header placement per interface.** The thunker header lives
  alongside its protocol's channel header, e.g.,
  `builder/base/interfaces/rdy_vld/rdy_vld_port_thunker.h`,
  `builder/base/interfaces/req_ack/req_ack_port_thunker.h`,
  `builder/pro/interfaces/lmmi/lmmi_port_thunker.h`. The header
  may be a separate file or inlined into the channel header at the
  maintainer's discretion. The tees (which live in
  `builder/pro/common/systemc/`) are not the model for placement;
  the channel headers are.
- **Declaration order constraint.** The thunker member is declared
  after the child instance pointer so that `child->port` is
  accessible when the thunker initialiser runs. The generator must
  emit container member declarations in this order.
- **Multi-cycle / pingpong out of scope.** The existing tees do not
  cover those modes either; the cross-interface use cases that need
  thunking are simple non-multicycle channels.

Pros and cons (recorded for completeness):

- Pros: Encapsulates conversion in a reusable, named template per
  protocol. Channel stays simple (non-templated, declared in
  `container_tb`); IP stays templated; thunker owns the translation.
  Per-bind cost is one extra member with one forwarding thread —
  acceptable for a generator-emitted bridge.
- Cons: One additional thread per bind. Idiom break from the tees in
  that the thunker calls channel methods directly rather than going
  through a producer port; justified by encapsulation.

###### Option T5 — Compile-time `reinterpret_cast` at port bind

When the YAML processor confirms that the two structs are byte-
for-byte layout-compatible (same `_packedSt`, same field order,
same field offsets and widths), the generator emits a
`reinterpret_cast` at the bind site:

```cpp
// In container.cpp, no extra object — just a cast at bind time:
u_ip8 ->dataIn(reinterpret_cast<rdy_vld_port<ipDataSt<ipVariant8Config>>::consumer&>(small));
u_ip16->dataIn(reinterpret_cast<rdy_vld_port<ipDataSt<ipVariant16Config>>::consumer&>(big));
```

- Pros: Zero runtime cost. No extra object. Compile-time
  enforcement via `static_assert(sizeof…)`.
- Cons: Only valid when `_packedSt` AND the port's full layout
  are byte-identical. The port's template machinery may carry
  per-Config differences (`_bitWidth`, `_byteWidth`,
  `pack`/`unpack` bodies) that prevent strict aliasing. The
  C++ standard's strict aliasing rules apply; UB risk if the
  layouts diverge in any field.
- Best suited as an *optimisation* under tight constraints, not
  as the default path.

###### Option T6 — Type-erased channel base; typed views adapt at endpoint

Refactor the channel hierarchy so a non-templated base class
holds the protocol state and the payload as a packed bag of bits
(`uint64_t` or a fixed-size byte buffer sized by maxBitwidth).
Each endpoint connects via a templated view that wraps the base
and pack/unpacks at use.

- Pros: Single uniform channel type; conversion built into the
  view layer. No per-bind thunk needed. Endpoints see their
  native types.
- Cons: Significant refactor of the channel hierarchy.
  Pack/unpack happens on every transfer at every endpoint, even
  when no cross-interface bind is needed. Loses some compile-
  time type safety at the channel level (the channel sees only
  `_packedSt`).

###### Option T7 — Inject a runtime converter via a virtual interface

Introduce a non-templated abstract interface with a virtual
`pack()` / `unpack()` between two byte buffers. The channel sees
only the byte buffer; each endpoint provides an implementation of
the interface that knows its struct's pack/unpack. The generator
wires the appropriate implementations at construction time.

- Pros: Channel is fully type-erased and uniform across all
  bindings. Protocol logic lives in the channel; conversion lives
  in injectable pack/unpack helpers. Endpoints see their native
  types.
- Cons: Virtual dispatch on the data path. Heavy for hot
  channels. The injection mechanism adds construction-time
  plumbing.

###### Comparison and settled choice

| Option | Channel type            | Per-bind cost | Visibility burden          | Refactor scope |
|--------|-------------------------|---------------|----------------------------|----------------|
| T1     | non-templated           | adapter shim  | container only             | low            |
| T2     | templated (rejected)    | adapter shim  | container_tb (rejected)    | low            |
| T3     | bridging-channel        | inside chan   | container only             | medium         |
| T4     | non-templated           | thunker class | container only             | low            |
| T5     | non-templated           | none          | container only             | very low       |
| T6     | type-erased base        | view layer    | uniform                    | high           |
| T7     | type-erased + virtuals  | virtual call  | uniform                    | high           |

- **T4 is settled.** The thunker class with encapsulated channel
  (refined design above) is the chosen mechanism. The channel stays
  simple and non-templated at the parent surface; the IP stays
  templated; the thunker owns the IP-side channel, the elaboration-
  time bind, and the forwarding thread. Per-bind generator output is
  one container member declaration plus one initialiser-list entry.
- **T5 is an opportunistic optimisation deferred to a follow-up.**
  When the YAML processor confirms strict byte-identical layout
  (and the port template machinery permits), the generator could
  emit a `reinterpret_cast` bind site instead of a thunker. Not in
  scope for the initial implementation; revisit only if T4's
  per-bind cost becomes a measurable problem.
- **T1 is rejected.** Inline adapters on the IP-side port would
  require widening the IP port template signature to accept a
  non-templated upstream. The IP block surface should not bend to
  accommodate cross-interface plumbing.
- **T6/T7 are deferred.** The refactor scope is significant and not
  justified solely by the cross-interface case. They could be
  revisited if a separate forcing function (e.g., uniform channel
  infrastructure for tandem mode) makes them attractive.

###### R2 — Confirmation readback (thunker shape)

The thunker design is settled as follows. Recorded as a readback so
the plan revision can quote it verbatim.

- Class form held as a container member (not a free function).
- Constructor signature
  `(const char* name, <protocol>_in<UpT>& upPort,
    <protocol>_in<DownT>& downPort, std::string blockName)`,
  with extra type parameters as the protocol requires
  (req_ack uses four).
- Owns the IP-side `<protocol>_channel<DownT>` as a member; binds
  the child's consumer port (`downPort(m_chDown)`) inside the
  constructor; spawns the forwarding thread via `sc_spawn`.
- Forwarding loop calls `m_up->readClocked(...)` (or the protocol
  equivalent),
  `outVal.unpack(static_cast<typename DownT::_packedSt>(inVal.pack()))`,
  and the channel's direct write method. The static_cast bridges
  any `_packedSt` size difference; the `_bitWidth`-exact-match
  rule from the packed-form compatibility check ensures the
  truncated/extended bits are zero in both directions.
- Header lives alongside the protocol's channel header in
  `builder/base/interfaces/<protocol>/` or
  `builder/pro/interfaces/<protocol>/`.
- Generator emits exactly one member declaration and one
  initialiser-list entry per cross-interface bind, with the
  declaration ordered after the child instance pointer.

##### Packed-form compatibility — the actual mechanism

The user noted: "the actual structure could be different due to
size mapping and maxWidth parameters — however the packed variants
should be compatible (by definition)." Grounded in the existing
generator behaviour:

- For a parameterizable structure, the generator sizes the packed
  underlying C++ type by `maxBitwidth`, not by the per-Config
  `width`. See `templates/systemc/structures.py`:
  `packedWidth = value['maxBitwidth'] if isParam else value['width']`.
- The packed underlying type (`_packedSt`) is therefore
  Config-independent for any parameterizable structure: every
  Config of `ipDataSt` types `_packedSt` identically.
- The `pack()` and `unpack()` methods place the field at offsets
  `[0 .. Config::IP_DATA_WIDTH-1]`, so the *bit content* depends on
  Config; the *underlying C++ type* does not.

For two structures (parameterized or non-parameterized) to share a
packed-form bind, the YAML processor needs to confirm:

1. **Interface type match.** The two endpoints must use the same
   meta-protocol (e.g., both `rdy_vld`, both `apb`, both
   `push_ack`). Cross-protocol bridging is not in scope.
2. **Field count and ordering match.** Fields appear in the same
   declared order; no extra fields on either side.
3. **Field name match.** Each field's name must be identical
   across the two structures. Same-bit-layout but different-name
   fields are rejected as a discipline check — the user's intent
   to bridge must be unambiguous, and identical field names
   document that intent.
4. **Field `_bitWidth` exact match.** Each field's `_bitWidth`
   const must match exactly between the two structures (under the
   bound Config for parameterized fields). This is the meaningful
   compatibility requirement — the bits that flow through the
   bridge are the bits the IP cares about. The `_packedSt`
   underlying type may differ between sides (the parameterized
   side sizes its packed type by `maxBitwidth`; the non-
   parameterized side by `width`), and that difference is bridged
   by the thunker's pack/unpack round trip rather than by a YAML
   alignment discipline.
5. **Bit-layout match for the relevant Config.** For the bound
   variant's Config, each field occupies the same bit positions
   in the packed form. The YAML processor already computes this
   when emitting `pack()` / `unpack()` bodies.

For the worked example:

- `data8St`: one field of `data8T` (`_bitWidth = 8`). Resolved
  `_packedSt = uint8_t`. Field at bits [0..7].
- `ipDataSt<ipVariant8Config>`: one field of `ipDataT<Config>`
  (`_bitWidth = Config::IP_DATA_WIDTH = 8`, maxBitwidth = 16).
  Resolved `_packedSt = uint16_t`. Field at bits [0..7].

The two `_bitWidth` consts match exactly (both are 8). The
`_packedSt` underlying types differ (`uint8_t` vs. `uint16_t`)
because of the maxBitwidth-vs-current-width sizing rule, but the
*bits within* the packed form match position-for-position.

The thunker's forwarding loop bridges the size difference with an
explicit cast on the packed value:

```cpp
outVal.unpack(static_cast<typename DownT::_packedSt>(inVal.pack()));
```

Widening (uint8_t → uint16_t) zero-extends; the high bits are
ignored by the consumer because they sit outside the consumer's
`_bitWidth`. Narrowing (uint16_t → uint8_t) truncates; the
truncated high bits are guaranteed zero because the producer's
`pack()` only sets bits within `_bitWidth`, which the matching
rule guarantees fits in the narrower side. Both directions are
safe under the `_bitWidth`-exact-match rule.

The earlier proposal that the YAML processor enforce a
maxBitwidth-alignment discipline (so `_packedSt` matches across
the bridge) is withdrawn. The thunker handles the size
difference; only `_bitWidth` and bit-layout need to align.

##### Open YAML questions

The schema-level shape is now settled: flat connectionMap (D5/R1),
bottom-up `ports:` map for parameterized blocks (D10), top-down
inference retained for non-parameterized blocks. The remaining
questions are mechanics, deferred to a follow-up.

1. **Checking semantics for bottom-up vs. top-down ports.** When a
   block declares some ports explicitly under `ports:` and others
   implicitly via connections, what does the generator do at
   conflict? Are partial declarations allowed? Settled after the
   research completes.
2. **Ports beyond `rdy_vld`.** `push_ack`, `axi`, `apb`, etc.
   carry multiple structures (addr_t, data_t, status_t). The
   packed-form check generalises but each protocol may need its
   own bridge helper.
3. **Diagnostics on failure.** When packed-form compatibility
   fails (`_bitWidth` mismatch, field count mismatch, bit offset
   mismatch, field name mismatch), the generator should name each
   offending field and point at both YAML files.

##### Cross-interface binding also applies to direct connections

The worked example shows the `connectionMaps:` path (parent's
external port mapped to child's internal port). The same shape
arises in the `connections:` path when two instances are wired
directly within a parent and their port interfaces differ.

For example, a non-parameterizable producer with a `data8If`
output port feeding a parameterizable consumer whose port is
`ipDataIf<Config>`:

```yaml
connections:
  - { interface: data8If, src: u_producer, srcport: out,
      dst: u_consumer, dstport: dataIn }
```

If `u_producer.out` is declared as `data8If` (via top-down
inference or an explicit `ports:`) and `u_consumer.dataIn` is
declared as `ipDataIf` under the consumer's Config (via the
consumer block's `ports:`), the generator detects the
cross-interface binding and runs the same compatibility check.
Pass emits a bridge; fail emits a precise diagnostic.

The exact YAML shape for representing per-end interfaces in
`connections:` is left for the plan revision (today the
`connections:` schema carries a single `interface:` field; that
may need to widen to per-end fields, or rely entirely on
bottom-up port declarations for end-side typing).

##### Working position

- The YAML processor runs a packed-form compatibility check on
  every connectionMap or connection whose two endpoint interfaces
  differ. The check applies uniformly across both YAML constructs.
- The check operates on the resolved field list and bit offsets
  under the bound Config (where applicable). It validates
  interface type, field count, field order, field names, per-field
  `_bitWidth` (exact match), and bit positions. It does *not*
  require the unpacked C++ types to match, and it does *not*
  require the `_packedSt` underlying types to match — the
  thunker's `static_cast` on the packed value handles any size
  difference between sides.
- When the check passes, the generator emits a thunker member per
  R2 (T4 settled) at the wiring site.
- When the check fails, the generator hard-errors with a precise
  diagnostic naming the offending fields and pointing at both
  YAML files.

#### Withdrawn alternatives

- **Resolved-type collapse pass.** Earlier text proposed detecting
  Config-independent fields and emitting structs as non-templated.
  Withdrawn because YAML's `isParameterizable` is authoritative and
  SV's view is the guide.
- **Force-equal Configs across a connection.** Validate at
  generation time and reject as an illegal topology. Withdrawn by
  Q11's resolution: producers carry per-port parameters in their
  Config, and each cross-Config bind is a normal cross-interface
  bind handled by the thunker. There is no illegal topology to
  reject.
- **User-code casts at the parent boundary.** Cannot work for
  cross-interface bindings on auto-generated wiring sites — the
  user has no edit handle in generated code. Replaced by the
  generator-emitted layout-compatible bridge above.
- **YAML-side `maxBitwidth` alignment discipline.** Earlier text
  proposed requiring external bridging structures to declare a
  `maxBitwidth` matching the internal struct's so that `_packedSt`
  underlying types aligned across the bridge. Withdrawn: the
  thunker's `static_cast` on the packed value handles any
  `_packedSt` size difference; only `_bitWidth` and bit-layout
  need to match exactly.

### Q11 — Producer with multiple differently-parameterised outputs (resolved)

Concrete case from `ip_top.yaml`:

```yaml
connections:
    - { interface: ipDataIf, src: uSrc, srcport: out0, dst: uIp0 }
    - { interface: ipDataIf, src: uSrc, srcport: out1, dst: uIp1 }
```

The earlier framing of this question rested on a wrong premise:
"`uSrc` has one Config; its two output ports cannot simultaneously
satisfy two differently-Configed consumers." That premise treated
each port as bound to the block's Config wholesale, when in fact a
Config struct carries multiple independent parameter fields — one
or more per port if the block needs them.

#### Resolution

A producer with multiple ports declares one parameter (or one
parameter group) per output port in its YAML. The block's Config
struct then carries those parameters as independent fields. Each
output port's struct type is parameterised by its own field. The
existing `ipConfig` already does the analogous thing — it carries
`IP_DATA_WIDTH` and `IP_MEM_DEPTH` as independent fields, used by
different parts of the block.

For the worked case:

- `src.yaml` declares two parameters, e.g. `OUT0_DATA_WIDTH` and
  `OUT1_DATA_WIDTH`, and two output ports:
  - `out0` typed by some structure parameterised on `OUT0_DATA_WIDTH`.
  - `out1` typed by some structure parameterised on `OUT1_DATA_WIDTH`.
- `src`'s Config struct (per variant) carries both fields.
- `uSrc` is a single instance with one Config containing both
  values.
- The connection from `uSrc.out0` to `uIp0.dataIn` is a normal
  cross-interface bind (different structures on the two ends);
  the thunker mechanism settled in Q10/R2 handles it. The
  `_bitWidth` exact-match check ensures `OUT0_DATA_WIDTH` equals
  `uIp0`'s `IP_DATA_WIDTH` at generation time, with a precise
  diagnostic on mismatch.
- The connection from `uSrc.out1` to `uIp1.dataIn` is independently
  bridged the same way.

This is exactly the SV shape:

```sv
src #(.OUT0_DATA_WIDTH(8), .OUT1_DATA_WIDTH(12)) uSrc (...);
ip  #(.IP_DATA_WIDTH(8))                          uIp0 (...);
ip  #(.IP_DATA_WIDTH(12))                         uIp1 (...);
```

`uSrc` is a single SV module instance with two parameters, one per
output. SV is happy; the SC mirror under Path C is happy for the
same reason — the Config carries multiple independent fields, and
the thunker mechanism handles each cross-interface bind.

#### Consequences

- **No "illegal topology" branch in the generator.** Every
  cross-Config bind is a normal cross-interface bind; the thunker
  is the single mechanism that bridges them.
- **The previous list of generator alternatives** (hard error /
  placeholder / auto-bridge) is withdrawn — none of them apply,
  because the topology is not illegal.
- **The YAML-side discipline shifts to the producer side.** A
  block whose ports may be connected to differently-parameterised
  consumers must declare per-port parameters. That declaration is
  the producer block's responsibility; the parent's connection
  YAML simply uses the produced ports.
- **Splitting `src` into `src0` and `src1` remains a user choice
  for clarity**, not a requirement to pass generation. Both shapes
  generate.

#### Documentation pointer

- The YAML-side convention is recorded in the `design-architecture`
  skill (`builder/base/rules/skills/design-architecture.md`,
  section 5 "Parameterizable IP Parameters", sub-bullet "Per-Port
  Parameters (Q11 producer pattern)"). The skill carries the
  full worked YAML for a producer-with-per-port-parameters block,
  the matching variant bindings, and the connection shape that
  triggers Stage 6.3 thunker emission. The Stage 7.2 example under
  `examples/` validates the same pattern end-to-end.

### Q12 — Migration of existing examples (captured as TODO)

`examples/ip_test`, `examples/mixed`, and other examples were
authored under the addParam-runtime model. Path C requires reviewing
each for SV-legality.

- Captured as a TODO list to track during the plan revision.
  Specific items to verify per example:
  - Every variant overrides at least one parameter (no label-only
    variants).
  - Producers feeding multiple differently-Configed consumers
    declare per-port parameters in their Config (Q11 resolution);
    no producer relies on a single Config wholesale satisfying
    incompatible consumer Configs.
  - No block constructor reads `getParam(...)` after the addParam
    retirement.
  - All `instanceFactory::createInstance` callers pass the variant
    string only (no `configTag`).
- Migration cadence (lockstep vs. piecemeal) is left to the plan
  revision. CI critical-path examples must migrate in the same
  change as the generator.

## Recommendation

- Adopt Path C for Step 10. Decisions D1–D10 are settled above. The
  thunker mechanics under Q10 are settled per R2 (T4: class form,
  encapsulated channel, packed-form `pack()`/`unpack()` conversion
  with `static_cast` on the packed value, `_bitWidth` exact-match
  rule, per-interface header placement). Q11 is closed: producers
  with multiple differently-parameterised outputs declare per-port
  parameters in their Config; each cross-Config bind is a normal
  cross-interface bind handled by the Q10/R2 thunker. Remaining
  open items are Q10's protocol-coverage details (`push_ack`,
  `axi`, `apb` thunkers beyond `rdy_vld` and `req_ack`; diagnostics
  on packed-form failure; bottom-up vs. top-down `ports:` checking
  semantics from D10). All are generator behaviours on top of the
  settled shape, not gates on the direction.
- The natural source of the second Config is the variant — no new
  YAML surface (no top-level `configs:` declaration) is needed.
- Eval resolution (D2) piggybacks on the existing variant-override
  resolver used by `calcAddresses` until the language-native
  compile-time path lands.
- Path C is invasive enough that it warrants its own plan, now
  drafted as
  [`plan-variant-config-unification.md`](./plan-variant-config-unification.md).
  That plan absorbs `plan-block-registration.md` Step 10
  (multi-Config-per-block regression) and groups the Path C work
  into ten implementation stages from per-variant Config emission
  through protocol-coverage extension.

## Appendix A — Why `configTag` Existed and Why It Retires

### What `configTag` was for

The factory key was extended from `(blockType, variant)` to
`(blockType, variant, configTag)` to support a scenario where the
*same* `(blockType, variant)` pair could register two distinct factory
entries pointing at different Config-templated lambdas. The prototype
example was:

- `ip` block with `variant0`.
- Project A binds `variant0` to `ipDefaultConfig`.
- Project B binds `variant0` to `ipFastConfig`.
- Both registrations coexist in the factory map under the same
  variant; `configTag` distinguishes them.

That model treated Config and variant as *independent* dimensions.

### Why it retires under variant ≅ Config

Under D1, variant *is* the Config (1:1, by construction). There is no
second Config that can attach to the same variant; the trampoline
emits exactly one entry per variant, and the variant string identifies
the Config unambiguously. Removing `configTag` simplifies:

- Factory map keys: tuple width drops from 3 to 2.
- Generator output: trampoline emission stops emitting Config-tag
  strings as separate arguments.
- Caller code: `instanceFactory::createInstance(name, instance,
  blockType, variant)` is the only signature.
- Sentinels: `noConfigTag` retires; the empty variant string covers
  the same role for blocks with no declared variants.

## Appendix B — Connection Coupling: SV Reference and SC Mirror

### SV side (reference)

In SV, each module instance has its own parameter values, fully
specialised at elaboration time. Ports of a module are typed by the
*instance's* parameters. Concretely, in `ip_top` today:

- `uIp0` is `ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), ...) uIp0(...)`.
- `uIp1` is `ip #(.IP_DATA_WIDTH(12), .IP_MEM_DEPTH(8), ...) uIp1(...)`.
- `uIp0`'s `ipDataIf` port carries an interface instance of width 8.
- `uIp1`'s `ipDataIf` port carries an interface instance of width 12.
- The parent must declare two distinct interface instances —
  `out0` of width 8 and `out1` of width 12 — and pass each to the
  matching child port. SV cannot connect a width-8 interface to a
  width-12 interface.

In SV the interface declaration is itself parameterised. `out0` and
`out1` are independently parameterised interface instances, each
constructed with the parameter set of the child it serves.

### SC mirror under per-variant Configs

For SC to match SV, the parent's channel type for `out0` must be
derived from `uIp0`'s Config, and similarly `out1` from `uIp1`'s
Config:

```cpp
push_ack_channel<ipDataSt<ipVariant0Config>> out0; // matches uIp0
push_ack_channel<ipDataSt<ipVariant1Config>> out1; // matches uIp1
```

These are distinct C++ types. Parent declares them under their own
member names; the parent's TU includes each variant's Config header
(already on the include path because the trampoline emits them).

### The non-trivial corner — single producer feeding differently-parameterised consumers

Today's `ip_top.yaml`:

```yaml
connections:
    - { interface: ipDataIf, src: uSrc, srcport: out0, dst: uIp0 }
    - { interface: ipDataIf, src: uSrc, srcport: out1, dst: uIp1 }
```

`uSrc` is a single instance with two output ports. The earlier
analysis treated this as illegal under SV ("a single module
instance has one parameter set; both ports must share parameter
values"). That framing was wrong. SV permits a module to declare
multiple parameters and have different ports parameterised by
different parameters:

```sv
src #(.OUT0_DATA_WIDTH(8), .OUT1_DATA_WIDTH(12)) uSrc (...);
ip  #(.IP_DATA_WIDTH(8))                          uIp0 (...);
ip  #(.IP_DATA_WIDTH(12))                         uIp1 (...);
```

`uSrc` is a single SV module instance with two parameters; each
output port's interface instance is parameterised by its own
parameter. The SV-legal shape requires only that `OUT0_DATA_WIDTH`
match `uIp0`'s `IP_DATA_WIDTH` and `OUT1_DATA_WIDTH` match
`uIp1`'s.

The SC mirror under Path C follows the same shape: `src`'s Config
struct (per variant) carries `OUT0_DATA_WIDTH` and
`OUT1_DATA_WIDTH` as independent fields. Each output port is typed
by a structure parameterised on its own field. Each connection
from `uSrc` to a consumer is a normal cross-interface bind handled
by the thunker (Q10/R2); the `_bitWidth` exact-match check ensures
the parameter values agree at generation time.

This is recorded in Q11's resolution. There is no "illegal
topology" under Path C; producers with multiple differently-
parameterised outputs declare per-port parameters in their Config
and the thunker mechanism handles each cross-interface bind.

### Working resolution (D5 + Q10)

Channel and port types in the parent are derived from the connected
child's Config. The parent itself is non-templated. Concretely:

```cpp
class ip_top : public blockBase, public ip_topBase {
    // Channels, each typed by the connected child's Config.
    push_ack_channel<ipDataSt<ipVariant0Config>> out0; // matches uIp0
    push_ack_channel<ipDataSt<ipVariant1Config>> out1; // matches uIp1

    // Parameterized children with concrete per-instance Config.
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ipVariant1Config>> uIp1;

    // Non-parameterized children stay as today.
    std::shared_ptr<apbDecodeBase> uAPBDecode;
};
```

The parent's TU includes each per-variant Config header (already
emitted on the include path because the trampoline pulls them in).
There is no "collapse" — `ipDataSt<ipVariant0Config>` and
`ipDataSt<ipVariant1Config>` are distinct C++ types, exactly as
their SV counterparts are distinct interface instances.

Cross-Config connections (a single producer feeding multiple
differently-Configed consumers) are not illegal under Path C. Per
Q11's resolution, the producer carries per-port parameters in its
Config; each cross-Config bind is a normal cross-interface bind
handled by the thunker mechanism (Q10/R2). The user is free to
split a producer for clarity, but is not required to.

External-boundary surfaces (where the parent exposes a
non-templated interface and binds it through a connectionMap to a
parameterized child's port) cannot use a user-code cast, because
the wiring site is generated, not user-written. The generator
runs the packed-form compatibility check on each such bind
(`_bitWidth` exact match plus bit-layout match per Q10) and emits
a thunker member at the wiring site (Q10/R2). See Q10's worked
example for the full shape.

## Appendix C — Container Member-Type Cleanliness Comparison

The three options considered for D4. Option (a) was chosen.

### Option (a) — Per-instance concrete Config types (chosen)

```cpp
std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
std::shared_ptr<ipBase<ipVariant1Config>> uIp1;
```

- Pros: Maximum compile-time type safety. Parent storage exactly
  mirrors the child's instantiation. Casts at construction are
  direct. Matches the SV elaboration model 1:1.
- Cons: None at zero generation cost. Parent's TU must include each
  variant's Config header — already on the include path because the
  trampoline emits them.
- Cleanliness: Highest. Reads naturally; no indirection.

### Option (b) — Untemplated common base (rejected)

```cpp
class ipBase;                               // untemplated abstract base
template<typename Config>
class ipBaseT : public ipBase { ... };      // templated derived

std::shared_ptr<ipBase> uIp0;
std::shared_ptr<ipBase> uIp1;
```

- Pros: Parent storage is uniform. Parent does not need to know the
  child's Config.
- Cons: Parent loses typed access to Config-dependent surface and
  must downcast for any Config-dependent method. Generator must emit
  two base classes per block.
- Cleanliness: Lower. Adds a class hierarchy layer that exists only
  to erase Config from the parent's view.

### Option (c) — Full type erasure to `blockBase` (rejected for parent storage)

```cpp
std::shared_ptr<blockBase> uIp0;
std::shared_ptr<blockBase> uIp1;
```

- Pros: Maximally uniform; no per-instance type at all.
- Cons: Loses access even to the block's own typed surface (port
  connections, register structs). Every use site downcasts.
- Cleanliness: Lowest. Reserved for `instanceFactory` and other
  genuinely heterogeneous containers; not used for parent storage.

## Related Documents

- [`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
  — the execution plan for Path C; absorbs the multi-Config-per-block
  regression formerly tracked as `plan-block-registration.md`
  Step 10.
- [`plan-block-registration.md`](./plan-block-registration.md) — the
  per-block trampoline plan (T9). Steps 1–9 and 11–12 remain
  authoritative; Step 10 is absorbed by the unification plan.
- [`research-block-registration-options.md`](./research-block-registration-options.md)
  — option-space evaluation that produced the trampoline approach.
- [`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md)
  — the post-processing that today populates `defaultConfig` and
  `isParameterizable`. Per-variant Config derivation extends this
  pass.
- [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md)
  — defines the `<context>DefaultConfig` shape. Per-variant Configs
  extend this template.
