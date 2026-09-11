# Authoring Guide: Parameter Inheritance

**Who this is for.** An engineer authoring a design in YAML. It states what the YAML looks
like, what is generated from it, and what is allowed and what is not. It does not describe
how the generator works; that belongs to
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md), which also carries the decision
history and the outstanding work.

**The rules section is normative.** Where the generator does not yet enforce a rule, the list at
the end of that section says so and names the plan step. §5 lists the two things that are not
covered at all, and is worth reading before putting an inherited parameter on a register-bus
router width.

---

## Rules (confirmed with the architect, 2026-09-07)

The point of parameterization is to let an author choose where each fact comes from without
stating it twice. There are three facts: a parameter's declaration, a block's use of it, and the
value an instance sees. Each has a small set of legal sources, and every rule below exists to keep
each source unambiguous. This section is the normative statement; the rest of this document
shows the YAML, and [`plan-parameter-sharing.md`](./plan-parameter-sharing.md) holds the history
and the evidence. The first draft was iterated with the architect rule by rule on 2026-09-07; each rule carries
the date it was confirmed or ruled, and the list at the end records where the tree has not
caught up.

Declaration.

1. A parameter is declared once, as an `ipParameters:` constant, and that one declaration is
   its identity everywhere it is reached. The declaring file may be any file, including a
   definitions-only file of a shared project that holds no `blocks:`, so that several IPs and
   several projects name one parameter (an image pipeline's `BITS_PER_PIXEL`). Nothing requires
   the declaring file, or the declaring project, to name the parameter itself. (Ruled and landed
   2026-09-07/08, plan step 12a.)
2. A block names the parameters it uses in `params:`. Each name resolves through the block's
   include scope to one declaration. Zero visible declarations is an error, and so is more than
   one. Visible means reachable from the block's own file through its include chain; a
   same-named declaration in a file the block does not reach is a different parameter, not a
   collision. The block's own file does not shadow an included declaration: two visible
   declarations of one name are two definitions, and are rejected however they are placed.
   (Confirmed 2026-09-07.)
3. A block's configuration is exactly the parameters it names. Anything derived from them is
   computed in the implementation, never configured. The derivation may be written once in YAML
   as an `eval:` constant; it is emitted as a computed value, never as a Config member, and may
   not itself be named in `params:`. (Confirmed 2026-09-07.)

Value.

4. An instance's values come from its container or from a variant, and a variant binds every
   parameter of its block, once each, from one of three sources:
   - a literal;
   - a constant visible in scope;
   - a parameter of the containing block, named by `containerParam:`. The names need not match,
     so this is also how a child parameter is renamed at the boundary. The container parameter's
     bound may not exceed the child's.
   Nothing fills in an omitted binding. The whole-container form, `inheritContainerParam: true`
   on the instance, sources every parameter of the block from the container's parameter of the
   same name, so the block's parameter set must be a subset of the container's; it names no
   variant and renames nothing, and it is confined to a container and child owned by one
   project. Across projects the child takes a declared variant whose bindings are
   `containerParam:`. `containerParam:` is the flexible form and `inheritContainerParam:` the
   same-project shorthand for the same-name subset case. (Ruled 2026-09-07.) Each shared name must
   also be the same `ipParameters` constant on both sides. A same-named child declaration with a
   smaller `maxValue` would otherwise pass the subset check and be sized below what the container
   can bind. Use `containerParam:` where the two must stay distinct declarations. (Ruled 2026-09-09.)

   How the factory selects a container-sourced child, in both forms alike: the child's C++
   type is a function of the container's Config, so the container names the concrete class as
   the template argument of `instanceFactory::createInstance` and forwards its own runtime
   variant label in place of a child label. The registry key is (child block, that forwarded
   label, the pair-qualified domain). An exact match, which is how a Verilated or tandem
   replacement registered per container variant is found, wins; otherwise the class named at
   the site is constructed. A child that names no variant therefore has an identity at the
   factory: its container's.
5. A variant is owned by the project that declares it. Its identity is (block, variant,
   declaring project), its name carries the project, and the declaring project emits it without
   touching another project's artefacts. (Confirmed 2026-09-07; landed as plan step 15 the same day.)
6. Any project may declare a variant of any block visible to it, whether or not it owns the block.
   (Confirmed 2026-09-07.)

Selection.

7. An instance of a parameterized block selects its configuration either by naming a variant or
   by taking its container's whole configuration (`inheritContainerParam:`, rule 4's
   whole-container form). A named variant resolves through the instance's include scope, the
   include chain of the file holding the instance row, to one declaration. Zero or more than one
   visible declaration is an error, and the message names every declaring file. (Confirmed
   2026-09-07.)
8. A top instance is not parameterized. (Confirmed 2026-09-07.)

Guarantees.

9. The two ends of a connection are compared at the values their instances actually resolve, and
   a disagreement is a db-time error naming both sides.
10. Nothing falls back to a default silently. Where a source cannot be resolved, the build stops
    and says which rule failed. (Rules 9 and 10 confirmed 2026-09-07.)

Scope decides what is visible. Project decides who owns. The file a statement sits in decides
neither.

### Where the tree deviates today

Recorded so the iteration argues about facts. Dated 2026-09-07; delete each line as it closes.

- Rules 2 and 7, visibility: both say include chain. Every scoped lookup in the tree, the two
  scope checks included, sees a file, the files it includes, and the files those include, and no
  further (`GENERATOR_ARCHITECTURE.md` section 4 records the two-level flattening as deliberate).
  A declaration three includes away is reported as out of scope. Whether the rule or the tool
  changes is for the architect; found 2026-09-08 when `ip_test`'s bridge top lost `ip_package.sv`
  from its `rtl.f` after dropping a direct include.
- Rules 5 and 6, one label from two projects in one build: identity is (block, variant, project),
  and the Configs are distinct since step 15, but the per-label HDL wrapper and registration
  artefacts are named by label alone. A build whose own project does not declare a label that two
  other projects declare is rejected at db time (`validateVariantLabelBuildOwnership`, 2026-09-08)
  rather than emitting one of the two silently. Project-qualified wrapper naming would lift it.
- Rule 9: the layout index collapses cross-project bindings into one slot (item 9B of
  [`plan-116-review-feedback.md`](./plan-116-review-feedback.md)).

### Direction, not a rule

Direction (user, 2026-09-09): SV is the guiding principle. A child binds on its defined ports and
ignores container Config members it does not use. In SC that means payload struct types keyed on
the parameter values they use, with the `<Config>` spelling kept as an alias, so two Configs with
equal values give one type and same-interface thunkers retire. Not yet a plan step.

---

## 1. What This Lets You Do

Four authoring situations recur when a parameterizable IP is reused. Each is served by a
different mechanism, and only the last is the subject of this document.

- **A parent block reuses a sub-block's parameter.** The parent needs the same knob its
  child has, because the child's parameterized payload appears on the parent's own boundary.
  The parent names the child's parameter in its own `params:` list, reaching the declaration
  through `include:`. The parameter is still declared once, by the IP that owns it.
- **Several projects share one parameter.** Two projects that must agree on a width name the
  same declaration, again through `include:`. There is one declaration and one identity, so
  the two ends of a connection between them cannot drift apart.
- **Peer blocks share a parameter.** Two blocks that do not contain one another, such as a
  stimulus and a checker either side of an IP, must be configured alike. If they share a
  container, each takes the parameter from that container and agreement is structural. If they
  do not, the assembler declares one plain constant carrying the value and every binding names
  that constant, so the number is written once.
- **A child takes its parameters from the block that contains it.** This is parameter
  inheritance, and it is what the rest of this document specifies. A block is configured by
  the block it sits inside, so a consumer several levels above an IP can configure that IP
  without naming it, and without the IP knowing anything about its consumers.

---

## 2. The YAML

The running example is a three-level design: a leaf IP, a mid-level IP that contains it, and
a customer assembler that contains the mid-level IP and states one value. The leaf is a
debayer, the mid-level IP is an image signal processor, and the customer wants that
processor's debayer configured at a particular algorithm.

| Project | Role |
| :-- | :-- |
| `xpDpLeaf` | leaf IP; owns the parameters `DP_ALGO` and `DP_WIDTH` |
| `xpDpMid` | mid-level IP; contains the leaf, owns its own parameter `MID_ALGO` |
| `xpDpTop` | customer assembler; contains the mid-level IP and states the value |

### 2.1 The IP declares its parameters, names them, and binds its own default variant

```yaml
# xpDpLeaf: the leaf IP. It knows nothing about any consumer.
ipParameters:
    constants:
        DP_ALGO:  { value: 1, maxValue: 7,  desc: "Interpolation algorithm select" }
        DP_WIDTH: { value: 8, maxValue: 32, desc: "Per-instance pixel width" }
    types:
        dpPixelT: { width: DP_WIDTH, maxBitwidth: 32, desc: "Parameterizable pixel word" }

blocks:
    xpDpLeaf:
        desc: "The parameterizable leaf IP"
        params: [DP_ALGO, DP_WIDTH]        # which parameters this block uses
        hasMdl: true
        hasRtl: true
        ports:
            in:  { interface: dpIf, direction: dst }
            out: { interface: dpIf, direction: src }

parameters:
    xpDpLeaf:
        dflt:                              # the IP's own default variant
            DP_ALGO: DP_ALGO               # bound to the constant of the same name,
            DP_WIDTH: DP_WIDTH             # which is how the declared default is written
```

Three facts appear once each. The parameter is **declared** in `ipParameters:`, with its
default in `value:` and the largest value it accepts in `maxValue:`. It is **named** by the
block that uses it, in `params:`. It is **bound** by a variant, which states where an
instance's value comes from.

### 2.2 The container declares its own knob and passes it down

```yaml
# xpDpMid: the mid-level IP. It contains two leaves and passes on whatever it
# was configured at, without stating an algorithm of its own.
include:
    - ../../dpLeaf/yaml/xpDpLeaf.yaml

ipParameters:
    constants:
        MID_ALGO: { value: 2, maxValue: 7, desc: "The algorithm this container asks its leaves for" }

blocks:
    xpDpMid:
        desc: "Mid-level IP containing two leaf instances"
        params: [DP_WIDTH, MID_ALGO]       # DP_WIDTH is the leaf's, reached by include
        hasMdl: true
        hasRtl: true
        ports:
            midIn:  { interface: dpIf, direction: dst }
            midOut: { interface: dpIf, direction: src }

instances:
    uLeafA: { container: xpDpMid, instanceType: xpDpLeaf, instGroup: top, variant: customer }
    uLeafB: { container: xpDpMid, instanceType: xpDpLeaf, instGroup: top, variant: customer }

parameters:
    xpDpLeaf:
        customer:
            DP_ALGO:  { containerParam: MID_ALGO }   # take my container's MID_ALGO
            DP_WIDTH: { containerParam: DP_WIDTH }   # take my container's DP_WIDTH
```

`{ containerParam: NAME }` says: *take this parameter from the parameter called `NAME` on
the block that contains me.* The variant does not name the containing block. The container is
whichever block the instance sits in, which the instance row already states.

Both leaf instances resolve the same container parameter, so the two peers cannot be
configured differently by accident.

### 2.3 The customer states the value once

```yaml
# xpDpTop: the customer. It configures the IP it actually instantiates and never
# names a block two levels down.
include:
    - ../../dpMid/yaml/xpDpMid.yaml

ipParameters:
    constants:
        CUST_ALGO: { value: 3, maxValue: 7, desc: "The customer's own algorithm knob" }

blocks:
    xpDpWrap:
        desc: "Container of the chain; declares the customer knob the mid-level IP inherits"
        params: [CUST_ALGO, DP_WIDTH]

instances:
    uWrap: { container: xpDpTop,  instanceType: xpDpWrap, instGroup: top, variant: customer }
    uMid:  { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer }
    uMid2: { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer2 }

parameters:
    xpDpWrap:
        customer:
            CUST_ALGO: 5                             # the one value the customer states
            DP_WIDTH: DP_WIDTH
    xpDpMid:
        customer:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: { containerParam: CUST_ALGO }  # inherited from xpDpWrap
        customer2:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: 6                              # fixed instead
```

The value travels one level per link: `xpDpWrap.CUST_ALGO = 5` reaches `xpDpMid.MID_ALGO`,
which reaches `xpDpLeaf.DP_ALGO`.

Each level declares the parameter it passes on. The customer writes the number once, on the
one block it owns.

The customer's knob has its own name. The customer file includes `xpDpMid.yaml`, which already
declares `MID_ALGO`, and rule 2 rejects a second visible declaration of that name. (The fixture
`examples/xprojParam/dpTop` spells it `CUST_ALGO`.)

### 2.4 Mixing inherited and fixed parameters

Two kinds of mixture are normal, and both appear above.

**Within one variant.** `xpDpMid.customer` binds `DP_WIDTH` to a value and inherits
`MID_ALGO`. Every parameter of every variant chooses its own form independently.

**Between variants of one block.** `xpDpMid.customer` inherits `MID_ALGO` while
`xpDpMid.customer2` fixes it at `6`. The two variants coexist, and an instance selects
between them with `variant:`.

A container passes on only the parameters it declares itself. `xpDpMid` declares `DP_WIDTH`
and `MID_ALGO` but not `DP_ALGO`, and the leaf's `DP_ALGO` therefore reaches the container's
`MID_ALGO`. A container never becomes a conduit for everything beneath it.

### 2.5 The binding forms

A parameter inside a declared variant may be written in any of these ways, and in no others.

| Written as | Meaning |
| :-- | :-- |
| `PARAM: 5` | the literal value 5 |
| `PARAM: PARAM` | the value of the named constant |
| `PARAM: { value: 5 }` | the literal value 5, long form |
| `PARAM: { containerParam: OTHER }` | taken from the container's parameter `OTHER` |

The short form `PARAM: <scalar>` always means a value, so inheritance is written in the long
mapping form.

---

## 3. What Is Generated

### 3.1 The C++ Config structs

Each declared variant of a block, and the block's default, produces one `Config` whose members
are that block's parameters. Its name carries the project that declares it (rule 5). It takes one of two forms,
and the variant's own bindings decide which:

- **Every parameter bound to a value** produces a plain struct of resolved numbers.
- **Any parameter sourced from the container** produces a struct **template** over the
  container's `Config`. An inherited member reads the named parameter off that `Config`; a
  bound member is still a number.

The leaf IP's own project emits its default and its `dflt` variant. Both bind every
parameter, so both are plain structs:

```cpp
struct xpDpLeaf_xpDpLeafDefaultConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};

struct xpDpLeaf_xpDpLeafDfltConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};
```

The mid-level IP declares the leaf variant it instantiates, and sources both of its
parameters from itself, so it emits one template:

```cpp
export template<typename ContainerConfig>
struct xpDpMid_xpDpLeafCustomerConfig {
    static constexpr uint32_t DP_ALGO  = ContainerConfig::MID_ALGO;
    static constexpr uint32_t DP_WIDTH = ContainerConfig::DP_WIDTH;
};
```

The customer's project emits one Config per variant it declares, qualified by the project
that declares it, each in whichever form its own bindings call for. `customer` inherits
`MID_ALGO` and is therefore a template; `customer2` fixes it and is a plain struct:

```cpp
export template<typename ContainerConfig>
struct xpDpTop_xpDpMidCustomerConfig {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = ContainerConfig::CUST_ALGO;
};

export struct xpDpTop_xpDpMidCustomer2Config {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = 6;
};
```

A container names its child's Config applied to its own, so the value arrives where the
container is instantiated rather than where the variant is declared:

```cpp
template<typename Config>
class xpDpMid ... {
    std::shared_ptr<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>> uLeafA;
```

This is the same statement the SystemVerilog makes by forwarding a symbol rather than a
number, and it chains through as many levels as the design has: the leaf inside the
customer's first chain is configured at
`xpDpMid_xpDpLeafCustomerConfig<xpDpTop_xpDpMidCustomerConfig<xpDpTop_xpDpWrapCustomerConfig>>`,
which resolves `DP_ALGO` to the 5 the customer wrote.

A bound value is resolved to a literal. A binding written as `MID_ALGO: MID_ALGO` and one
written as `MID_ALGO: 3` therefore emit the same member; the relationship to the constant is
kept in the authored YAML, not in the emitted struct. An inherited value is not resolved,
because there is nothing to resolve it to until an instantiation states it.

**One Config is emitted per declared variant per block, however many instances select it and
at however many values.** The running example produces two in the leaf IP's own project (its
default and its `dflt` variant), one in the mid-level IP's (the leaf variant that IP
declares), and one per variant the customer declares, in the customer's project. A customer
that adds a third configuration of the mid-level IP adds one Config to its own project and
changes nothing in either IP: the templates the IPs emitted are instantiated at the new
Config, not re-emitted.

Two blocks that resolve to identical numbers still get two distinct Configs, and therefore
two distinct C++ types, with a generated adapter wherever the two meet.

### 3.2 The SystemVerilog

A block's parameters become the module's parameter list, in the order the block names them:

```systemverilog
module xpDpLeaf
import xpDpLeaf_package::*;
#(
    parameter DP_ALGO,
    parameter DP_WIDTH
)
```

A container's parameter list is exactly what that container declares, and an inherited child
parameter is instantiated with the container's own symbol:

```systemverilog
module xpDpMid
#(
    parameter DP_WIDTH,
    parameter MID_ALGO
)
...
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafA ( ... );
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafB ( ... );
```

Note that `xpDpMid` declares no `DP_ALGO` at all. The leaf receives the container's
`MID_ALGO`, which is the whole point: the symbol forwarded is the container's, and the names
need not match. A parameter bound to a value rather than inherited appears at the
instantiation as a literal instead of a symbol.

Parameterizable widths follow the same parameters, so a payload declared over `DP_WIDTH`
becomes `typedef logic[DP_WIDTH-1:0] dpPixelT;` inside each module.

---

## 4. Accepted And Rejected Shapes

The rules at the top of this document are normative. This section lists the shapes they accept
and reject and what each message says. A shape marked *not yet enforced* is rejected by the
rules and still accepted by the tree; the deviation list under the rules names the plan step.

### What is allowed

- A parameter is declared once, as an `ipParameters:` constant, in the IP root file or in a
  definitions-only shared file (rule 1). Its `value:` is the default and its `maxValue:` is the
  largest value the IP accepts.
- Any block may **name** that parameter in its own `params:` list, provided it can reach the
  declaration through `include:`. Naming is not declaring, and a block in another project may
  name it.
- A parameter inside a variant may be bound to a value, or sourced from a parameter of the
  block that contains the instance.
- A block's owner may declare a variant labelled `default`. It is then the block's default
  Config, spelled `<project>_<block>DefaultConfig`, and no separate default is emitted for that
  block; its bound values are what the default carries. (Ruled 2026-09-07, from a step 15
  review finding; the product tree declares every variant this way.)
- The child's parameter and the container's parameter need not share a name.
  `DP_ALGO: { containerParam: MID_ALGO }` is an ordinary shape, not a workaround.
- A variant may mix the two forms freely, and a block may declare several variants, some
  inheriting a given parameter and some fixing it.
- One variant may be instantiated under different containers. It means the same thing at
  every site, "take my container's `MID_ALGO`", and each site is checked separately.
- The container's parameter and the child's may be backed by different constants, in
  different projects. They need not be the same declaration.

### What is not allowed

- **A parameter may not be both bound and inherited.** Writing
  `PARAM: { value: 3, containerParam: OTHER }` states the parameter twice. The message names
  the variant and the parameter and says that a parameter is either bound to a value or
  sourced from a container parameter, never both.
- **A parameter may not be left empty.** Writing `PARAM: {}` states nothing. The message says
  that every parameter of a declared variant must be bound or container-sourced.
- **A variant may not omit a parameter its block declares.** There is no default for an
  omitted parameter, and nothing is filled in. The message names the missing parameters and
  lists the ones the block declares.
- **A parameter may not be inherited from a container that does not declare it.** The
  container has nothing to give and, in SystemVerilog, no symbol to forward. The message names
  the instance, the child parameter, the container block, and the parameters that container
  does declare.
- **Inheritance reaches the immediate container only.** A parameter cannot be taken from a
  block two levels up. To configure something deeper, declare the parameter at each
  intervening level and inherit it at each link, as `xpDpMid` does in §2.2. This mirrors
  SystemVerilog, in which a parameter reaches a nested module only through a module that
  declares it.
- **A container parameter may not accept values the child would reject.** If the container's
  parameter is declared with a larger `maxValue` than the child's, it can be bound to a value
  the child cannot accept, and the site is rejected. The message names the instance, both
  constants and both bounds. Declaring the customer's `CUST_ALGO` at `maxValue: 15` in §2.3,
  against a leaf that accepts `7`, is exactly this error.
- **An inherited parameter may not be selected on a top-level instance.** An instance with no
  containing block has no container to inherit from.
- **An instance of a params-declaring block may not select nothing.** The shapes that name a
  Config are the whole list: a variant binding values, a variant sourcing from the container
  per parameter, and `inheritContainerParam: true`. An instance naming none of them leaves the
  block parameterized and the instance untyped, and the two languages then disagree about which
  values it carries. The message names the instance, the block, the block's owning project, the
  file and the line, and lists the parameters the block declares.
- **A top instance's block may not declare `params:` at all.** A top has no container, so
  neither container-sourcing form is reachable, and a project declares one top, so a variant
  could only ever bind one set of literals, which a plain constant expresses without the
  variant machinery. Put an unparameterized block at the root and the parameterized block one
  level down. `examples/xif` is that shape: `xif_top` is the root and the parameterized
  testbench harness `xif_tb` sits inside it at a stated variant. The message states the
  restructure.

- **Two visible declarations of one parameter name** (rule 2), whether the second sits in the
  block's own file or in another included file. The message names every declaring file.
- **A variant label with zero or two visible declarations** (rule 7). The message names every
  declaring file it can see, or the file(s) that declare it out of scope.
- **An instance of a block without `params:` names a variant.** No file could ever declare a
  variant of it, so the message says the block declares no params rather than that no file
  declares the label.
- **`inheritContainerParam:` across a project boundary** (rule 4). The message names both
  projects. A cross-project child takes a declared variant whose bindings are `containerParam:`.

Where one variant is reused under several containers, the same rules apply once per site.
Two containers backed by the same constant, and two backed by different constants with the
same `maxValue`, are both accepted; only a container whose accepted range exceeds the child's
is rejected, and only at the site where that happens.

### What is not checked

`maxValue` is the whole of the compatibility relation. It bounds the magnitude the container
may bind and says nothing about the value's **type**, so **`valueType` is not compared**: a
signed container parameter sourced into an unsigned child parameter is accepted, and the
child's Config member is emitted at the child's own declared type. Extending the relation to
`valueType` was raised and **declined**. The failure needs a signed container parameter bound
into an unsigned child, which was judged too narrow to widen the relation for. It is a known
and accepted gap, so there is no diagnostic to wait for.

Keeping the container's and the child's `valueType` in agreement is therefore the author's
responsibility, not the generator's.

---

## 5. What Is Supported Today

All four situations in §1 are available and in use, including the shared declaration of rule 1,
a definitions-only file declaring a parameter for several IPs (`examples/xprojParam/cstShared`).
For parameter inheritance, the fourth and the subject of this document, that means:

- The authored YAML of §2 is accepted, and every shape in §4 not marked *not yet enforced* is
  rejected with the message described there.
- The SystemVerilog of §3.2 is complete: parameters are forwarded through each level and the
  design elaborates and runs with the inherited values.
- The C++ of §3.1 is complete: a customer's value reaches a leaf two project levels down, and
  two containers of one IP at different values resolve independently at run time.
- An inherited parameter that appears in a **width** is inside the interface layout comparison,
  resolved at the value the site actually binds.
- All of the above is held by automated targets rather than by recorded runs.

Two things are not covered, and an author has to know both:

- **A register-bus interface carries no parameterizable structure.** A router serves one bus type,
  named by its `addressBlock.upstreamPort`, on both of its sides. A router block may declare
  `params:` and inherit or take `containerParam:` values like any block, and the junction between a
  parent router and a nested router is adjudicated at the configuration that governs both, the
  same as every other connection. No bridge exists between two register-bus types. Neither a
  router dispatch nor a `registerPorts:` boundary emits a thunker, and the root testbench cannot
  share a Config with the design, so no master can drive a bus struct sized by a parameter. Keep
  register-bus structures fixed-width; put the parameter in the register payload instead.
- **`valueType` is not compared** between the container's parameter and the child's; see
  "What is not checked" in §4.

A third item stood here until 2026-09-07: that a block's Config could carry parameters
declared in the same file that the block does not name. Since 2026-09-05 a block's Config
carries exactly the parameters its `params:` list names, and derived constants are computed in
the implementation ([`plan-parameter-sharing.md`](./plan-parameter-sharing.md) §6, step 3).
A block that names parameters from two files gets one Config name and one home whatever its
`params:` order: every Config name carries the declaring project, and each (declaring project,
block) emits one module (rule 5, plan step 15, landed 2026-09-07).

The status, the remaining work and the evidence behind each claim are tracked at
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md) §6, step 7, which also carries the
history of what this document used to say.

`inheritContainerParam:` stays supported as rule 4's same-project, same-name shorthand, and the
synthesised register handler keeps using it. The product tree's `u_preprocess`/`u_interpolate` use
`inheritContainerParam:`; the `containerParam:` form remains for a child that differs from its
container by name or project.
