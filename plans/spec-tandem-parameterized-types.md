# Specification: Tandem Wrapper Emission under Parameterized Types

**Status:** Descriptive specification of the tandem emission contract as landed on
`feature/116-parameterized-types` (a2cPro). Normative for any generator that emits
tandem wrappers.
**Applies to:** the `<block>Tandem` header emitter (`tandem` template, `tandem`
section) and the `<block>Tandem` implementation emitter (`tandemConstructor`
template, `initTandem` / `bodyTandem` sections).
**Reference implementation:** `builder/pro/templates/systemc/classDeclTandem.py`,
`builder/pro/templates/systemc/constructorTandem.py` (the pro overlay; this document lives
in base so that the emission contract is readable from the open repo).
**Cross-references:** [`plan-block-registration.md`](./plan-block-registration.md) (the
`(blockType, variant, projectName)` factory key this specification registers under),
[`plan-instance-factory-templates.md`](./plan-instance-factory-templates.md) (superseded
analysis of registration patterns for templated blocks),
[`plan-116-review-feedback.md`](./plan-116-review-feedback.md) (work log, including the
tandem-header module-qualification fix restated as R7).

This document is written to be portable: it states the *inputs* a generator needs and
the *emitted C++ contract* it must satisfy, not the Python that currently produces it.
A reimplementation in another host language, or an equivalent emitter in another
generator, is conformant if it satisfies every MUST in §4 and passes §7.

**Tandem is a pro-only feature and there is no tandem example in base.** Base contains no
generated `*Tandem.*` artifact of any kind; its only trace of the feature is a commented-out
`tandem` file-map entry (`unittest/mixed_test_arch/mixedProject.yaml`), and the runtime is
gated behind `A2CPRO`. The emitters, the `run-tandem` skill, and the only in-repo
tandem-emitting example all live under the pro overlay.

This document is nevertheless kept in base, alongside the rest of the `plans/` set, and its
§5 worked examples are anchored on **base** example blocks, so that the emission contract
can be read and checked without the pro tree. That makes those listings derived renderings
rather than copied output; §5.0 states exactly what is real about them and what is not. Do
not read §5 as a claim that these files exist.

Keywords MUST / MUST NOT / SHOULD / MAY are used per RFC 2119.

## 1. Problem

A tandem wrapper is a generated `SC_MODULE` that instantiates two implementations of
the same leaf block side by side — a primary (`verif`, typically RTL-backed) and a
secondary (`model`) — tees every port to both, and lets a checker compare them. Before
this change the wrapper assumed:

1. the block's `Base` / `Inverted` / `Channels` companion classes are non-template
   types, reachable by textual `#include "<block>Base.h"`;
2. a block registers itself with the instance factory exactly once, under a
   `(blockType, variant)` key;
3. all member definitions can be emitted at namespace scope in a `.cpp`.

Parameterized types invalidate all three. When a leaf block declares its own
parameters, its companion classes become class templates on a `Config` policy type,
they now live in a C++20 module interface unit, and a single block can require several
distinct C++ types (one per variant) to coexist in one binary. This specification
defines what the tandem emitter must produce so that the tandem flow works for
parameterized and non-parameterized blocks alike.

## 2. Terminology

| Term | Meaning |
| --- | --- |
| **leaf block** | A block with no sub-instances. Tandem applies to leaf blocks only. |
| **parameterizable** | The block's Config surface is non-empty, whether the parameters are its own or inherited from a container. |
| **own params** | The block declares parameters itself. This — not "parameterizable" — is the condition under which the block is emitted as a class template. A parameterizable block without own params is *not* a template. |
| **Config policy** | A generated struct holding the resolved parameter values for one variant, used as the template argument. |
| **default Config** | The block's Config struct for the case where no per-variant override applies. |
| **variant** | A named instantiation of a block carrying a specific parameter binding. Also the factory key component that selects a Config at runtime. |
| **projectName** | Identity of the project that emitted a registration or lookup; the third factory-key dimension. |
| **base module** | The C++20 module interface unit exporting the block's `Base` / `Inverted` / `Channels` companions. |
| **tee** | The per-port `SC_THREAD` that forwards traffic from the wrapper's own port to both child instances. |

For a leaf block, *own params* implies *parameterizable*. The tandem emitter therefore
needs a single predicate, referred to below as **`hasOwnParams`**, and MUST NOT branch
on `isParameterizable`: a parameterizable-but-not-own-params block is a non-template
class and spelling `<Config>` on it would name a non-template type.

## 3. Required inputs

A conformant generator MUST have access to the following facts about the block being
emitted. Names are the reference implementation's; a port MAY rename them but MUST
preserve the semantics.

| Input | Type | Purpose |
| --- | --- | --- |
| `blockName` | string | Unqualified block identity. Spells class names (`<blockName>Tandem`, `<blockName>Base`, …) and the factory `blockType` keys. MUST NOT be project-qualified. |
| `blockModuleName` | string | **Project-qualified** block identity, used *only* to spell the base module name. Distinct from `blockName`; see R7. |
| `hasOwnParams` | bool | Selects templated vs. non-templated emission. §2. |
| `defaultConfig` | string | C++ struct name of the block's default Config. |
| `variants` | set of string | Variant names for this block. MAY be empty. |
| `variantConfigs` | list of descriptor | Per-variant Config descriptors; each yields a variant name and the C++ Config struct name it emits as (collapsing to `defaultConfig` when the descriptor carries no override values or reuses the default). |
| `configIncludeContext` | set of string | Contexts whose Config-policy headers this block's Config names live in. |
| `includeFiles['config_hdr'][context]` | record with `baseName` | Filename of a context's Config-policy header. |
| `interfaceTypes` | set | Interface types used by the block's ports; selects the `<intf>_port_tee.h` includes (pre-existing behaviour, unchanged). |
| `ports` | grouped map, each entry with `name` | Ports to tee. Iteration order MUST be stable. |
| `projectName` | string | Emitting project identity, from project configuration (`PROJECTNAME`). |
| tandem header filename | string | The emitted header's filename, resolved from the project's file map for the `tandem` file key — MUST NOT be hardcoded as `<block>Tandem.h`. |

## 4. Normative emission rules

### 4.1 Templating

**R1.** When `hasOwnParams` is true, the wrapper MUST be emitted as a class template on
a single type parameter named `Config`, declared immediately before the module
declaration. When false, no template declaration is emitted.

**R2.** Every reference to a companion class MUST carry the template argument suffix
`<Config>` exactly when `hasOwnParams` is true, and nothing when false. This applies to:
the base class in the module declaration; the `verif` and `model` smart-pointer element
types; the `Inverted` port-bundle members; the `Channels` members; the base-class
mem-initializer; and the `dynamic_pointer_cast` target types in the constructor.

**R3.** Out-of-line definitions in the implementation unit (the constructor and every
tee function) MUST each be preceded by the template declaration and MUST qualify the
class as `<block>Tandem<Config>::` when `hasOwnParams` is true.

**R4.** A generator MUST derive the `<Config>` suffix and the `template<typename Config>`
declaration from one shared predicate, so that the non-templated path is byte-identical
to the pre-change output apart from the deltas mandated by R8 and R9.

### 4.2 Dependent-name and macro placement

**R5.** In a tee body, the wrapper's *own* port — inherited from the dependent base
`<block>Base<Config>` — MUST be spelled `this-><port>` when `hasOwnParams` is true, so
that two-phase name lookup resolves it. The `verif_ports.<port>` and
`model_ports.<port>` arguments are members of the current instantiation and MUST NOT be
`this->`-qualified.

**R6.** `SC_HAS_PROCESS` MUST be emitted inside the class body (public section) when
`hasOwnParams` is true, and at namespace scope in the implementation unit when false.
Rationale: the implementation unit cannot name a dependent specialization at namespace
scope, so the macro cannot be applied there for a class template.

### 4.3 Module and include contract

**R7.** The header MUST make the block's companions available by importing the base
module — `import <base-module-name>;` — and MUST NOT `#include` a `<block>Base.h`. The
base module name MUST be derived from the **project-qualified** `blockModuleName`, not
from `blockName`; deriving it from `blockName` produces an unqualified module name that
fails to resolve against the qualified `export module` declaration in a composed
(multi-project) build. Every other emitter uses the qualified field, and the tandem
header MUST match.

The companions are exported at global scope, so the unqualified names the wrapper
spells resolve directly off this import. Unlike the general block class declaration, the
tandem header spells no interface or context payload type unqualified, so it MUST NOT
re-emit interface-context imports.

**R8.** When `hasOwnParams` is true, the header MUST `#include` the Config-policy header
of every context in `configIncludeContext` that has one, in a deterministic (sorted)
order, so that the concrete per-variant Config struct names are nameable by both the
class template and the per-variant registrations of R11. When false, no such includes
are emitted.

**R9.** The implementation unit MUST include the tandem header by its file-map-resolved
filename rather than a hardcoded `<class>.h`, so that the header's stub and extension
remain project configuration.

**R10.** The tandem header remains a classic guarded header. It is *not* promoted to a
module interface unit by this specification, even for templated blocks; see R12 for why
that is sound.

### 4.4 Factory registration and lookup

**R11.** Registration MUST be keyed on `(blockType, variant, projectName)`:

- `blockType` remains `"<blockName>_tandem"`.
- **Non-templated case:** exactly one registration, with an empty variant string, is
  emitted — a default-constructed static registrar whose factory lambda constructs
  `<block>Tandem`.
- **Templated case:** the static registrar MUST take the variant string as a
  constructor argument, and the implementation unit MUST emit one **explicit
  specialization** of that static member per variant in `variants`, in deterministic
  (sorted) order, each passing its own variant string and instantiating the wrapper on
  that variant's Config struct. When `variants` is empty, exactly one specialization on
  `defaultConfig` with an empty variant string MUST be emitted.
- **Distinctness precondition.** Two variants that resolve to the same Config struct
  name would be the same C++ type, and two specializations of the same static member
  would be an ODR violation. The emitter emits one specialization per variant and
  relies on the data model to guarantee distinctness: declared variants map 1:1 onto
  distinctly variant-named Config structs, with no dedup fold, even when a variant's
  values equal the block default. A host whose Config resolution *does* fold variants
  together MUST deduplicate by emitted Config struct name before emitting. The same
  applies to the fallback path for a variant present in the variant set but absent from
  the per-variant descriptors, which resolves to `defaultConfig`: at most one variant
  may take that path.

**R12.** The per-variant explicit specialization is also the *instantiation trigger*.
Defining the static registrar for `<block>Tandem<C>` instantiates that specialization's
registrar constructor, whose factory lambda names `<block>Tandem<C>` and therefore
requires its constructor definition. That definition MUST be visible in the same
translation unit — which it is, because the implementation unit carries both. A
conformant generator therefore needs no separate explicit-instantiation directives and
no promotion of the tandem header to a module unit.

**R13.** Both child lookups (`verif` under the primary factory mode, `model` under the
secondary) MUST pass `projectName` as the trailing lookup argument, matching the
`projectName` used at registration time. This applies to templated and non-templated
blocks alike.

## 5. Reference emitted output

### 5.0 Fixtures

Both worked examples are anchored on blocks in the **base** example set, so a reader can
follow this specification without access to the pro tree or to any product design. Every
identity below (project name, module name, class names, port names, variant names, Config
struct names) is read from the checked-in generated artifacts of those examples.

| Fixture | Where | Shape |
| --- | --- | --- |
| `producer` | `examples/simple` | Non-parameterized leaf. `hasRtl` + `hasMdl`, no `params:`. Project `simple`; base module `simple_producer.base`; companions `producerBase` / `producerInverted` / `producerChannels` are plain classes; ports `tag0`, `tag1` (`push_ack`). |
| `blockF` | `examples/mixed` | Parameterized leaf. `params: [bob, fred]`, `hasVl` + `hasMdl`. Project `mixed`; base module `mixed_blockF.base`; companions are `template<typename Config>` classes; variants `variant0` / `variant1` with Config structs `blockFVariant0Config` / `blockFVariant1Config` in `mixedVariantConfig.h`; default Config `mixedDefaultConfig`; ports `cStuffIf`, `dSout` (src) and `dStuffIf`, `dSin`, `rwD` (dst) over `rdy_vld` and `status`. |

`blockF` is the more instructive fixture because it declares **two** variants, so it
exercises the multi-specialization path of R11 that a single-variant block cannot show.

**Caveat — these two fixtures are not tandem examples.** There is no tandem example in
base at all: no base project emits a `*Tandem.*` file, because the `tandem` file-map entry
is commented out and the runtime is `A2CPRO`-gated. `producer` and `blockF` are ordinary
blocks of the right *shape* — a non-parameterized leaf and a parameterized leaf, each with
a model and an RTL side — not blocks that generate tandem wrappers today.

The listings below are therefore §4 applied to real fixtures: faithful in every identity
(project, module, class, port, variant, Config), but derived rather than copied. They are
what a conformant emitter would produce for these two blocks, and they double as the
expected output should a base project enable the `tandem` file-map entry. The emitters'
actual behaviour was observed on tandem-enabled pro and product projects; §7 is what
re-establishes that correspondence for any port.

### 5.1 Non-parameterized block — `producer`

Header:

```cpp
#include "logging.h"
#include "push_ack_port_tee.h"
#include "instanceFactory.h"
import simple_producer.base;

SC_MODULE(producerTandem), public blockBase, public producerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("producer_tandem", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<producerTandem>(blockName, variant, bbMode));}, "", "simple");
        }
    };
    static registerBlock registerBlock_;
public:
    std::shared_ptr<producerBase> verif; // verification instance
    std::shared_ptr<producerBase> model; // model instance
    producerInverted verif_ports; // ports to connect to the verification instance
    producerInverted model_ports; // ports to connect to the model instance
    producerChannels verif_channels; // channels to connect to the verification instance
    producerChannels model_channels; // channels to connect to the model instance

    producerTandem(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producerTandem() override = default;

private:
    void tag0Tee(void);
    void tag1Tee(void);
```

Implementation:

```cpp
#include "producerTandem.h"

SC_HAS_PROCESS(producerTandem);

producerTandem::registerBlock producerTandem::registerBlock_; //register the block with the factory

void producerTandem::tag0Tee(void) {
    port_tee(tag0, verif_ports.tag0, model_ports.tag0);
}

void producerTandem::tag1Tee(void) {
    port_tee(tag1, verif_ports.tag1, model_ports.tag1);
}

producerTandem::producerTandem(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
        ,verif(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "verif", "producer", INSTANCE_FACTORY_PRIMARY_TYPE, variant, "simple")))
        ,model(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "model", "producer", INSTANCE_FACTORY_SECONDARY_TYPE, variant, "simple")))
        ,verif_ports("Pri")
        ,model_ports("Sec")
        ,verif_channels("PriChnl", "tandem")
        ,model_channels("SecChnl", "tandem")
```

Note what is absent: no template declaration, no `<Config>`, no Config-policy include, no
`this->` on the teed port, `SC_HAS_PROCESS` at namespace scope, and a single registration
under an empty variant key. Relative to the pre-change baseline the only deltas are the
`import` of R7 and the trailing `projectName` arguments of R11 and R13.

### 5.2 Parameterized block — `blockF`

Header:

```cpp
#include "logging.h"
#include "rdy_vld_port_tee.h"
#include "status_port_tee.h"
#include "instanceFactory.h"
import mixed_blockF.base;
#include "mixedVariantConfig.h"

template<typename Config>
SC_MODULE(blockFTandem), public blockBase, public blockFBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockF_tandem", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockFTandem<Config>>(blockName, variant, bbMode));}, variant_, "mixed");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(blockFTandem);
    std::shared_ptr<blockFBase<Config>> verif; // verification instance
    std::shared_ptr<blockFBase<Config>> model; // model instance
    blockFInverted<Config> verif_ports; // ports to connect to the verification instance
    blockFInverted<Config> model_ports; // ports to connect to the model instance
    blockFChannels<Config> verif_channels; // channels to connect to the verification instance
    blockFChannels<Config> model_channels; // channels to connect to the model instance

    blockFTandem(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockFTandem() override = default;

private:
    void cStuffIfTee(void);
    void dSoutTee(void);
    void dStuffIfTee(void);
    void dSinTee(void);
    void rwDTee(void);
```

Implementation (tee bodies elided after the first two):

```cpp
#include "blockFTandem.h"

template<> blockFTandem<blockFVariant0Config>::registerBlock blockFTandem<blockFVariant0Config>::registerBlock_("variant0"); //register the block with the factory
template<> blockFTandem<blockFVariant1Config>::registerBlock blockFTandem<blockFVariant1Config>::registerBlock_("variant1"); //register the block with the factory

template<typename Config>
void blockFTandem<Config>::cStuffIfTee(void) {
    port_tee(this->cStuffIf, verif_ports.cStuffIf, model_ports.cStuffIf);
}

template<typename Config>
void blockFTandem<Config>::dSoutTee(void) {
    port_tee(this->dSout, verif_ports.dSout, model_ports.dSout);
}

template<typename Config>
blockFTandem<Config>::blockFTandem(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase<Config>(name(), variant)
        ,verif(std::dynamic_pointer_cast<blockFBase<Config>>( instanceFactory::createInstance(name(), "verif", "blockF", INSTANCE_FACTORY_PRIMARY_TYPE, variant, "mixed")))
        ,model(std::dynamic_pointer_cast<blockFBase<Config>>( instanceFactory::createInstance(name(), "model", "blockF", INSTANCE_FACTORY_SECONDARY_TYPE, variant, "mixed")))
        ,verif_ports("Pri")
        ,model_ports("Sec")
        ,verif_channels("PriChnl", "tandem")
        ,model_channels("SecChnl", "tandem")
```

Had `blockF` declared no variants, R11's empty-variant fallback would instead emit the
single line:

```cpp
template<> blockFTandem<mixedDefaultConfig>::registerBlock blockFTandem<mixedDefaultConfig>::registerBlock_(""); //register the block with the factory
```

The two per-variant registrations mirror, key for key, how `blockF`'s ordinary model class
already registers itself in [`examples/mixed/registrar/blockFRegistrar.cppm`](../examples/mixed/registrar/blockFRegistrar.cppm)
(`"blockF_model"` under `("variant0", "mixed")` and `("variant1", "mixed")`). The tandem
wrapper differs only in the `blockType` string and in registering through a static class
member rather than a file-local registrar struct.

## 6. Invariants

**I1.** For a block with no own params, emitted output MUST be byte-identical to the
pre-change output except for the R7 import and the `projectName` arguments. The
parameterization work MUST NOT perturb non-parameterized projects otherwise.

**I2.** The constructor body section (logging prefixes, channel binds, `SC_THREAD`
registrations) is unchanged by this specification and MUST remain
parameterization-agnostic: it already spells only members of the current instantiation
and `this->name()`.

**I3.** The wrapper's polymorphic contract is unchanged. Regardless of templating, each
`<block>Tandem<C>` reaches `blockBase` through `<block>Base<C>`, and the factory's
return type stays the non-template `std::shared_ptr<blockBase>`. The factory itself does
not become a template; only *what is registered* changes.

**I4.** The tandem `blockType` key string (`"<block>_tandem"`) is unchanged, so the
containing testbench's tandem selection logic needs no change.

## 7. Acceptance criteria

A conformant implementation MUST satisfy all of the following.

1. **Non-parameterized regression.** Regenerate a project with no parameterized leaf
   blocks; diff the emitted `*Tandem.*` against the baseline. Only the R7 import line
   and the `projectName` arguments differ (I1). The `producer` fixture of §5.1 is the
   minimal case.
2. **Parameterized compile.** A parameterized leaf block with `hasVl`, `hasRtl` and
   `hasMdl` set generates a tandem pair that compiles standalone, with no
   template-dependent-name diagnostics and no `SC_HAS_PROCESS`-at-namespace-scope error.
   The `blockF` fixture of §5.2 is the minimal case, and its two variants also cover
   criterion 4.
3. **Composed-build module resolution.** In a multi-project build where block identities
   are project-qualified, every emitted tandem header's `import` resolves — i.e. it
   names the same module the corresponding base unit exports (R7). A tandem header
   importing an unqualified `<block>.base` against a qualified export is a defect.
4. **Registration coverage.** For each parameterized leaf block, the number of emitted
   static-member specializations equals the number of distinct Config structs across its
   variants; each carries its own variant key; none is duplicated (R11).
5. **Factory key agreement.** Every emitted `registerBlock` and `createInstance` pair
   for a block agrees on `projectName` (R11, R13). A mismatch surfaces as a runtime
   factory lookup failure rather than a compile error, so this MUST be checked.
6. **Functional tandem.** Model/model tandem runs to completion for a parameterized leaf
   block, then RTL/model tandem does. Model/model MUST be proven first.
7. **Determinism.** Two successive generations of the same project produce
   byte-identical output (sorted iteration over contexts and variants).

## 8. Non-goals

- Tandem for hierarchical (non-leaf) blocks, and for register-handler blocks. Out of
  scope; unchanged.
- Making the instance factory itself a template (I3).
- Promoting the tandem header to a C++20 module interface unit (R10, R12).
- Cross-variant factory fallback. Lookup is scoped to a single `projectName`; there is
  no fallback across Config identities.
- Changes to the tee mechanism, the port-tee helpers, or the thunker layer.

## 9. Porting notes

A generator outside this codebase needs only: the block identity in both unqualified and
project-qualified spellings; the own-params predicate; the default and per-variant Config
struct names; the set of Config-policy headers; the port list; the emitting project's
name; and a file-map lookup for the tandem header filename. Everything else in §4 is a
pure function of those inputs.

The two spellings of block identity are the most common source of defects: the
unqualified name spells C++ class names and factory `blockType` keys, the qualified name
spells module names. They MUST NOT be interchanged. Likewise the own-params predicate
MUST NOT be conflated with parameterizability.
