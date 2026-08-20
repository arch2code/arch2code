# Authoring Guide: Parameter Inheritance

**Who this is for.** An engineer authoring a design in YAML. It states what the YAML looks
like, what is generated from it, and what is allowed and what is not. It does not describe
how the generator works; that belongs to
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md), which also carries the decision
history and the outstanding work.

**Everything specified here ships.** §5 lists the three things that are not covered, and is
worth reading before putting an inherited parameter on a register-bus router width.

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
- **Peer blocks share a parameter.** Two blocks that do not contain one another — a stimulus
  and a checker either side of an IP, for example — must be configured alike. If they share a
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
        MID_ALGO: { value: 3, maxValue: 7, desc: "The customer's own algorithm knob" }

blocks:
    xpDpWrap:
        desc: "Container of the chain; declares the customer knob the mid-level IP inherits"
        params: [MID_ALGO, DP_WIDTH]

instances:
    uWrap: { container: xpDpTop,  instanceType: xpDpWrap, instGroup: top, variant: customer }
    uMid:  { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer }
    uMid2: { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer2 }

parameters:
    xpDpWrap:
        customer:
            MID_ALGO: 5                              # the one value the customer states
            DP_WIDTH: DP_WIDTH
    xpDpMid:
        customer:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: { containerParam: MID_ALGO }   # inherited from xpDpWrap
        customer2:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: 6                              # fixed instead
```

The value travels one level per link:
`xpDpWrap.MID_ALGO = 5` → `xpDpMid.MID_ALGO` → `xpDpLeaf.DP_ALGO`.

Each level declares the parameter it passes on. The customer writes the number once, on the
one block it owns.

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

Each declared variant of a block produces one `Config` whose members are that block's
parameters. It takes one of two forms, and the variant's own bindings decide which:

- **Every parameter bound to a value** produces a plain struct of resolved numbers.
- **Any parameter sourced from the container** produces a struct **template** over the
  container's `Config`. An inherited member reads the named parameter off that `Config`; a
  bound member is still a number.

The leaf IP's own project emits its default and its `dflt` variant. Both bind every
parameter, so both are plain structs:

```cpp
struct xpDpLeafDefaultConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};

struct xpDpLeafDfltConfig {
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
    static constexpr uint32_t MID_ALGO = ContainerConfig::MID_ALGO;
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

## 4. Rules

### What is allowed

- A parameter is declared once, as an `ipParameters:` constant in the IP root file that owns
  it. Its `value:` is the default and its `maxValue:` is the largest value the IP accepts.
- Any block may **name** that parameter in its own `params:` list, provided it can reach the
  declaration through `include:`. Naming is not declaring, and a block in another project may
  name it.
- A parameter inside a variant may be bound to a value, or sourced from a parameter of the
  block that contains the instance.
- The child's parameter and the container's parameter need not share a name.
  `DP_ALGO: { containerParam: MID_ALGO }` is an ordinary shape, not a workaround.
- A variant may mix the two forms freely, and a block may declare several variants, some
  inheriting a given parameter and some fixing it.
- One variant may be instantiated under different containers. It means the same thing at
  every site — "take my container's `MID_ALGO`" — and each site is checked separately.
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
  constants and both bounds. Declaring the customer's `MID_ALGO` at `maxValue: 15` in §2.3,
  against a leaf that accepts `7`, is exactly this error.
- **An inherited parameter may not be selected on a top-level instance.** An instance with no
  containing block has no container to inherit from.

Where one variant is reused under several containers, the same rules apply once per site.
Two containers backed by the same constant, and two backed by different constants with the
same `maxValue`, are both accepted; only a container whose accepted range exceeds the child's
is rejected, and only at the site where that happens.

### What is not checked

`maxValue` is the whole of the compatibility relation. It bounds the magnitude the container
may bind and says nothing about the value's **type**, so **`valueType` is not compared**: a
signed container parameter sourced into an unsigned child parameter is accepted, and the
child's Config member is emitted at the child's own declared type. Extending the relation to
`valueType` was raised and **declined** — the failure needs a signed container parameter bound
into an unsigned child, which was judged too narrow to widen the relation for. It is a known
and accepted gap, so there is no diagnostic to wait for.

Keeping the container's and the child's `valueType` in agreement is therefore the author's
responsibility, not the generator's.

---

## 5. What Is Supported Today

All four situations in §1 are available and in use. For parameter inheritance — the fourth, and
the subject of this document — that means:

- The authored YAML of §2 is accepted, and every rule in §4 is enforced with the messages
  described there.
- The SystemVerilog of §3.2 is complete: parameters are forwarded through each level and the
  design elaborates and runs with the inherited values.
- The C++ of §3.1 is complete: a customer's value reaches a leaf two project levels down, and
  two containers of one IP at different values resolve independently at run time.
- An inherited parameter that appears in a **width** is inside the interface layout comparison,
  resolved at the value the site actually binds.
- All of the above is held by automated targets rather than by recorded runs.

Three things are not covered, and an author has to know all three:

- **A nested register-bus router is not resolved per site.** It is compared against its parent
  router, which sits one level above rather than beside it, so an inherited parameter on a
  register-bus router width falls back to its constant's declared default there. Every other
  connection is resolved at its site.
- **`valueType` is not compared** between the container's parameter and the child's; see
  "What is not checked" in §4.
- **A block's Config may carry parameters declared in the same file that the block does not
  name.** A limitation of Config composition generally, not of inheritance.

The status, the remaining work and the evidence behind each claim are tracked at
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md) §6, step 7, which also carries the
history of what this document used to say.

`inheritContainerParam:` remains the shipping mechanism for a child that takes its container's
whole configuration, and is the right choice today where it applies: the container and the
child must belong to the same project, and the child's parameters must be a same-named subset
of the container's. It is the all-or-nothing, same-name, same-project case of what this
document specifies. Migrating authored designs off it onto `containerParam:` is a separate,
undecided step and is not implied by anything here.
