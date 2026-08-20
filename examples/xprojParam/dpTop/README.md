# `dpLeaf` + `dpMid` + `dpTop` — container-sourced parameters at depth

**Status: regression fixture.** The family is the `xproj-depth` target and runs
as part of `pipeline-test`. It is the vehicle for the `containerParam:`
parameter-inheritance design, and it carries a two-link single-level forwarding
chain. The guard is the checkers' per-sample assertion, not the fact that
generation succeeded: driving any link to the wrong algorithm fails the target.

**Both sides are proven by execution.** The SystemVerilog elaborates and runs
under Verilator with the inherited values; the SystemC model of `dpTop` builds,
links and runs, and its checkers assert the algorithm each nested leaf resolved.
Only the SystemC side is gated by `xproj-depth`; the Verilator evidence below is
a manual run.

## The question

An architect's customer wants to use an ISP in a particular configuration, so it
instantiates an instance including a debayer with the appropriate debayer config
including algorithm. There are two project levels between the project that
declares the configuration and the block that is configured.

| Directory | `projectName` | Role |
| :-- | :-- | :-- |
| `dpLeaf/` | `xpDpLeaf` | the leaf IP (debayer analogue): owns `DP_ALGO` and `DP_WIDTH` |
| `dpMid/` | `xpDpMid` | the mid-level IP (ISP analogue): instantiates the leaf, owns `MID_ALGO` |
| `dpTop/` | `xpDpTop` | the customer assembler: instantiates the mid and states the one value |

`DP_ALGO` is a purely behavioural knob. It appears in no width and in no packed
position, so a wrong `DP_ALGO` changes no layout and no db-time layout gate can
see it. That is deliberate: it separates variant SELECTION from variant LAYOUT.

## How it is expressed

A variant parameter is **either** a value **or** sourced from a named parameter
of a named containing block. The two forms are mutually exclusive, and the
singular shorthand `<param>: <scalar>` still means a value, so the container form
is reachable only in the long form.

The container block is **not** named. It is taken from the instance row, which
already carries it, and the linkage is validated after parsing rather than by a
foreign key: a container block's `params:` are not reliably parsed before a child
variant's binding rows.

**Inheritance is single level.** A declaration reaches its immediate container
and no further. Multi-level configuration is a chain of single-level links, in
which each intermediate level declares the parameter it forwards. That mirrors
the hardware: a SystemVerilog parameter reaches a nested module only through a
container that declares it.

`dpMid/yaml/xpDpMid.yaml` — the ISP does not state the algorithm; it passes on
whatever it was configured at, to both of its leaves:

```yaml
parameters:
    xpDpLeaf:
        customer:
            DP_ALGO:  { containerParam: MID_ALGO }
            DP_WIDTH: { containerParam: DP_WIDTH }
```

Note that `DP_ALGO` is sourced from a container parameter of a **different**
name. The names need not match.

`dpTop/yaml/xpDpTop.yaml` — the customer states the value once, on the wrapper it
owns; the mid forwards it, and the leaf takes it from the mid:

```yaml
parameters:
    xpDpWrap:
        customer:
            MID_ALGO: 5
            DP_WIDTH: DP_WIDTH
    xpDpMid:
        customer:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: { containerParam: MID_ALGO }
        customer2:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: 6
```

The chain is two single-level links:
`xpDpWrap.MID_ALGO` = 5 → `xpDpMid.MID_ALGO` → `xpDpLeaf.DP_ALGO`.

`customer2` shows that a value-bound and a container-sourced variant of the same
block coexist; each parameter of each variant chooses its own form.

## Reuse of one child variant under two containers

`uLeafX` instantiates the **same** `xpDpLeaf.customer` variant directly inside
`xpDpWrap`, alongside `uLeafA`/`uLeafB` inside `xpDpMid`. One declaration, two
containers, and `MID_ALGO` on the two containers is backed by **two different
constants** (`xpDpMid`'s, and the customer wrapper's own). This is legal: the
variant means "my container's `MID_ALGO`" at both sites.

What is checked, per site, is that the container's constant cannot admit a value
the child's constant would reject. Measured on this fixture:

| Case | Result |
| :-- | :-- |
| same backing constant on both containers | accepted, no diagnostic |
| different constants, identical `maxValue` | accepted, no diagnostic |
| different constants, container's `maxValue` wider | **rejected**, naming that site and both constants |

The rejection is per site and has no blind spot: a fault confined to the single
reused instance in the third project is caught and named, with every other site
clean.

## What works, measured

- **`make db` and `make gen` are clean** for all three projects.
- **The chain is persisted as a chain**, not flattened: each link carries
  `containerParam` in place of a value, so the relationship survives into the
  database rather than being collapsed to a number.
- **The RTL inherits correctly through both hops.** `xpDpMid` declares no
  `DP_ALGO` at all, yet the leaf receives the customer's value:

```systemverilog
module xpDpMid #( parameter DP_WIDTH, parameter MID_ALGO ) ...
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafA ( ... );
```

- **Verilated and run**, with a hand-written two-level harness that reads the
  leaf's elaborated parameters two hops down. Driving the top at `MID_ALGO=5,
  DP_WIDTH=8` prints `LEAF_DP_ALGO=5 LEAF_DP_WIDTH=8`; driving it at `6, 20`
  prints `LEAF_DP_ALGO=6 LEAF_DP_WIDTH=20`. The declared defaults are `1` and
  `8`, so neither result is a default reaching through.

Before this design, the same fixture emitted `.DP_ALGO(DP_ALGO)` — a symbol
`xpDpMid` does not declare — and Verilator rejected it with `Signal definition
not found, creating implicitly: 'DP_ALGO'` followed by `Can't convert defparam
value to constant`.

- **The C++ inherits correctly through both hops too.** A variant that sources a
  parameter from its container emits a Config TEMPLATE over the container's
  Config, and the container names it applied to its own:

```cpp
export template<typename ContainerConfig>
struct xpDpMid_xpDpLeafCustomerConfig {
    static constexpr uint32_t DP_ALGO  = ContainerConfig::MID_ALGO;
    static constexpr uint32_t DP_WIDTH = ContainerConfig::DP_WIDTH;
};

std::shared_ptr<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>> uLeafA;
```

Such a child is a FAMILY of C++ types, one member per Config its container is
instantiated at, and the factory key `(blockType, variant, projectName)` has no
Config dimension to select a member with. So the container names the member at
the site, as a template argument of one framework-side `createInstance`:

```cpp
uLeafA(std::dynamic_pointer_cast<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>>(
    instanceFactory::createInstance<xpDpLeaf<xpDpMid_xpDpLeafCustomerConfig<Config>>>(
        name(), "uLeafA", "xpDpLeaf", "customer", "xpDpMid")))
```

The keyed lookup for that exact `(blockType, variant, projectName)` is consulted
FIRST and wins, so a registered verification or verilated implementation still
substitutes for the type named here. A request for a mode that has no
registration - `--vlInst` on a `hasVl: false` leaf - is reported rather than
silently given the model, because the type named here is the model class:
`Attempted to create an instance uLeafA of an unregistered block type
xpDpLeaf_verif`.

- **Built, linked and run.** `make -C dpTop/rundir -j all` and
  `make -C dpTop/rundir run` both exit 0. The three chains resolve at algorithms
  **5**, **6** and **7** at leaves nested inside the mid-level IP, and each
  checker asserts the algorithm its own Config declares. The directly
  instantiated `uLeafX` resolves **1** and is asserted too (see the fallback note
  under "What does not work yet").

- **A customer configuration costs the vendors nothing.** Adding a fourth
  configuration of the mid-level IP, declared and instantiated entirely within
  `dpTop` at an algorithm no other cell uses, and cold-regenerating all three
  projects leaves **every file under `dpMid/` and `dpLeaf/` byte-identical**
  (re-measured 2026-08-17 with `customer4` at `MID_ALGO: 3`: 28 emitted files,
  aggregate MD5 `f403704b6ff5462f10be9320fbc9ad96` before, with the fourth
  configuration, and after restoring).
  The vendors' Config templates are instantiated at the new Config, not
  re-emitted.

## What is rejected, and where

| Fault | Rejected at | Message (abbreviated) |
| :-- | :-- | :-- |
| Both a value and a container source | declaration (row-local) | `... states both a value (3) and container source ...` |
| Neither a value nor a container source | declaration (row-local) | `... states neither a value nor a container source ...` |
| A parameter omitted from a container-sourced variant | declaration (row-local) | `Variant 'customer' of block 'xpDpLeaf' ... is missing required parameter(s): DP_WIDTH` |
| Container declares no such parameter | **post-parse, per site** | `instance uLeafX ... sources param 'DP_WIDTH' ... from container parameter 'DP_WIDTH', but container block 'xpDpWrap' declares no such parameter; it declares ['MID_ALGO']` |
| Container constant admits values the child cannot | **post-parse, per site** | `instance uLeafX ... allows values up to 15 while the child parameter's backing constant ... allows only 7; the container can be bound to a value the child cannot accept` |
| Instance is not contained in a block at all | **post-parse, per site** | `... sources parameter(s) [...] from a container parameter, so the instance must be contained in a block` |

Only row-local facts are checked where the variant is declared. Everything that
needs the container is checked after parsing, in
`validate_container_sourced_params`.

## What does not work yet

- **Include-chain shadowing is silent, and this feature makes it load-bearing.**
  `xpDpWrap: params: [MID_ALGO]` in `xpDpTop.yaml` binds the customer's own
  `MID_ALGO`, not the `MID_ALGO` reached through the included `xpDpMid.yaml`,
  purely by include order and with no diagnostic. That choice now decides which
  constant a nested IP's parameter is bounded by. A duplicate-in-scope
  diagnostic on the scoped lookup is the obvious guard.
- **A child variant declared by an intermediate project is not selectable by a
  third project's instance** (stated in full under "Constraints" below). At run
  time `uLeafX` therefore stamps algorithm 1, the leaf's declared default,
  rather than the wrapper's 5. Only the direct instantiation is affected; the
  same variant reached through the mid-level IP resolves correctly. **This is now
  OBSERVED, not merely documented**: `uChkX` (variant `leafX`, `DP_ALGO` bound
  through the leaf's own constant) consumes `uLeafX`'s output and asserts
  algorithm 1 per sample, so a change in that resolution fails the target instead
  of passing in silence. The behaviour is unchanged - only the observation was
  added.
- ~~**The layout gate loses a container-sourced LAYOUT parameter.**~~ **FIXED
  2026-08-17, and no longer a limitation of this family.** Bindings used to be
  resolved per declared variant; a container-sourced binding has no value there,
  so the resolver fell back to the backing constant's declared default. Measured
  on this fixture at the time: with the container at `DP_WIDTH=16` and a sibling
  leaf bound to a literal `16` — identical in truth — `make db` **falsely
  rejected** the junction, reporting `_bitWidth 16` against `_bitWidth 8`.
  Junction resolution is now site-correlated, so a container-sourced parameter is
  compared at the value its instance actually resolves and **may be used in a
  layout**. This family still holds `DP_WIDTH` at its declared default
  everywhere, so it puts no layout question in play; the two arms that do are
  `examples/xprojParam/cpLayout` (accept) and `cpLayoutBad` (reject), guarded by
  the `xproj-container-layout` target.
- `dpTop/registrar/xpDpTop_xpDpLeafVariantConfig.cppm` is a stale orphan left
  from an earlier shape of this fixture. Generated files are not swept when the
  declaration that produced them is removed.

## Constraints the fixture ran into on the way

Each is a measured generator behaviour, recorded because the fixture is shaped
around it.

- **A transit container over a parameterizable IP must declare `params:`.** A
  block carrying a parameterizable payload on its own boundary has no Config to
  instantiate the type with unless it is a class template.
- **A reusable IP project that contains an instance must carry its own
  standalone top.** `Project 'xpDpMid' declares instances but is missing
  topInstance:`. Hence `dpMid/yaml/xpDpMidStdTop.yaml`, mirroring
  `ip_test/bridge/yaml/bridgeStdTop.yaml`.
- **An instance may not name a variant its own project's closure does not
  declare.** So the mid must declare, itself, every variant it names.
- **A connectionMap thunker member is named after the mapped instance alone**, so
  mapping a container's `in` and `out` onto one child emits two members of the
  same name. Hence two chained leaf instances.
- **A connectionMap's channel name is the container port name and a plain
  connection's is the source port name**, and the two share one namespace with a
  connectSingle/connectDouble type check. Hence `midIn` / `midOut` rather than
  `in` / `out`.
- **The testbench External omits `foreignConfigModules`** (plan-parameter-sharing
  B3). For this family the wrapper is load-bearing anyway — it owns the
  customer's `MID_ALGO` — so it is not a B3 workaround here.
- **The External must be retargeted at the `_tb` container**
  (`--block=xpDpTop_tb --excludeInst=u_xpDpTop`), so it holds the DUT's siblings
  — here none — rather than the DUT's own children. Left at the scaffold seed
  (`--block=xpDpTop`), it elaborated the whole chain a SECOND time under
  `tb.external.*`, and the run still reported `No error`. That seed is correct
  only for a leaf DUT with no children.
- **`inheritContainerParam:` cannot cross a project boundary**, which is why it
  could not express this case: `inheritContainerParam requires container block
  'xpDpMid' (project 'xpDpMid') and child block 'xpDpLeaf' (project 'xpDpLeaf')
  to be the same owning project`. The container-sourced form carries no such
  restriction.
- **A variant declared by an intermediate project is not selectable by a third
  project's instance.** `_selectVariantDescriptor` matches either the consuming
  project's own declaration or the child block owner's, so `uLeafX` — declared in
  `xpDpTop`, at a variant declared by `xpDpMid` — resolves no descriptor and
  falls back to the block default Config. The validator therefore checks every
  declaration of the variant label rather than only the one a site would bind,
  so a container-sourced parameter is never silently unchecked.

## A second thing this example guards: peers of the DUT

`xpDpTbPeer` has nothing to do with the three-level depth chain. It is
instantiated only inside `xpDpTop_tb`, the testbench container, as two instances
bound to variants this project declares against a block whose config context
another project owns.

That placement is the point. A generated testbench External emits the DUT's
PEERS, never the DUT's own children, and it is the one consumer of the
per-instance Config machinery that is not a class template and is not on the
block dependency line. So a parameterizable peer is the only way an assembler-
declared (owner-qualified) Config struct is named outside a container that
already imports the module declaring it. Before the import was emitted here the
build stopped at:

```
tb/xpDpTop/xpDpTopExternal.cppm:35:36: fatal error:
  use of undeclared identifier 'xpDpTop_xpDpTbPeerPeerConfig'
```

The two peers drive each other and each asserts the algorithm its partner
stamped against its own Config, so the guard runs rather than merely compiling.

Note that they are two instances of ONE block, and of a block instantiated
nowhere else in the project: a registrar TU is emitted per (parent, child) but
named for the child alone, so a templated child assembled under two different
parents would collide on one path.

## Build and check

```
make xproj-depth
```

`dpTop` is the buildable top of the family; `dpMid` builds and links standalone
but its own driver and sink are empty scaffolds, so its `run` aborts on
"Premature end of test". That is a fixture gap, not a build one, which is why
`xproj-depth` generates `dpMid` but runs only `dpTop`.

The RTL evidence is taken with Verilator directly rather than `make lint`
(Verilator 5.038 rejects the `incdir` form in `common/systemVerilog/a2c.f`):

```
verilator --lint-only --timing \
  -I<base>/interfaces/push_ack -I<base>/interfaces \
  dpLeaf/rtl/xpDpLeaf_package.sv dpLeaf/rtl/xpDpLeaf.sv dpMid/rtl/xpDpMid.sv \
  <two-level harness>.sv --top-module <harnessTop>
```
