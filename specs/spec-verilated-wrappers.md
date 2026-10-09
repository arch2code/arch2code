# Verilated HDL verification wrappers

## Summary

A block with `hasVl: true` gets an HDL verification wrapper: a SystemVerilog
top that flattens the block's interface ports into plain pins, and a SystemC
class that drives those pins from the block's channels. A simulator compiles
the SV top (Verilator, VCS `vlogan -sc_model`, or Xcelium as a foreign module),
and a per-assembler registrar registers the SystemC class with the instance
factory as `<block>_verif`, so `--vlInst` can swap it in for the model at run
time. A parameterized block has one shared parameterized wrapper body and one
small concrete top per parameter set. Each top has fixed integer pin widths.
The build manifest names every top explicitly, and every simulator flow
compiles from those records.

Scope: this spec covers the generated wrapper files, their names and owners,
pin widths, the manifest records and the make rules that consume them. It does
not cover the VCS and Xcelium snapshot flows (`specs/SIMULATOR_INTEGRATION.md`),
variant declaration and Config ownership (`specs/spec-parameter-inheritance.md`),
or tandem. The user-facing side is taught by the `verify-cosimulation` skill,
with build targets in `manage-build`.

## 1. Inputs

| Input | Source | Effect |
| :--- | :--- | :--- |
| `hasVl` | block row | Selects every wrapper fileMap entry (`cond: {hasVl: true}` or `condAnd: {hasVl: true}`). |
| `hasOwnParams` | the block declares `params:` (`artifactPaths.blockCondRow`) | Selects the body/top split, the foreign and pair tops, and a Config-templated SC wrapper. |
| `hasRtl` | block row | Not a condition of any wrapper entry. The wrapper instantiates the block's RTL module (`blockSvModuleName`), so a `hasVl` block needs RTL to verilate. |
| Standalone variants | `variantSelection.standaloneVariantDescriptors` | The labels the block's owner declares, excluding container-sourced labels. One bare top each. |
| Foreign variants | `FOREIGNCONFIGHEADERS` (`projectCreate.calcForeignConfigHeaders`) | Labels a project other than the owner declares for the block, excluding container-sourced labels (`vlVariants`). One owner-qualified top each. |
| Pair registrations | `REGISTRARPAIRS[(parent, child)]['verifRegistrations']` | One concrete Config per parent-child pair and label. Pair-specific rows (container-sourced or `inheritContainerParam`) each get a pair-qualified top. |

`projectCreate.deriveSvWrapperNames` persists every body and top name as
`SVWRAPPERNAMES`. `projectCreate.calcVlTops` persists, per top, the evaluated
width of every parameterizable structure and type its pins carry (`VLTOPS`).
Templates and the manifest read these names. They never derive a top name from
a file name.

## 2. File set and naming

All entries live in `config/project.yaml` `fileGeneration.fileMap`. `<pfx>` is
the owning project's `svFilePrefix` (empty by default). Wrapper files go in the
`vl_wrap` segment: `$root/verif/vl_wrap` in the functional layout, `<node>/verif`
in the hierarchical layout. Registrars go in the `registrar` segment.

| Entry | Mode | Condition | File | Design unit or class |
| :--- | :--- | :--- | :--- | :--- |
| `vlSvWrap` | block, per standalone label | `hasVl` | `<block>_<label>_hdl_sv_wrapper.sv`, or `<block>_hdl_sv_wrapper.sv` for a block without params | `<pfx><block>_<label>_hdl_sv_wrapper` / `<pfx><block>_hdl_sv_wrapper` |
| `vlSvWrapBody` | block | `hasOwnParams` and `hasVl` | `<block>_hdl_sv_wrapper.svh` | `<pfx><block>_hdl_sv_wrapper` (body, never a top) |
| `vlSvWrapForeign` | registrar, per foreign label | `hasOwnParams` and `hasVl` | `<stub>_<label>_hdl_sv_wrapper.sv` in the declaring project | `<pfx><stub>_<label>_hdl_sv_wrapper` |
| `vlSvWrapPair` | registrar, per pair-specific registration | `hasOwnParams` and `hasVl` | `<child>_<label>_hdl_sv_wrapper.sv` in the pair owner's tree | `p<n>_<parentSv>_c<m>_<childSv>_<label>_hdl_sv_wrapper` |
| `vlScWrap` | block | `hasVl` | `<block>_hdl_sc_wrapper.h` | `<block>_hdl_sc_wrapper` |
| `blockVlRegistrar` | registrar, per assembler and child | `hasVl` | `<child>VlRegistrar.cpp` | anonymous-namespace registration static |

- `<stub>` is `processYaml.qualifyModuleIdentity(<block>, <declaringProject>)`:
  `<project>_<block>`, or the bare block name when it already leads with the
  project name. Example: `examples/ip_test/bridge/verif/ipBridge_ip_variant1_hdl_sv_wrapper.sv`,
  top `ipBridge_ip_variant1_hdl_sv_wrapper`, which project `ipBridge` declares
  for block `ip` owned by project `ip`.
- In a pair top, `<parentSv>` and `<childSv>` are the parent and child RTL
  module names, `<n>` and `<m>` their lengths, and `<label>` the parent's
  active variant (`default` when unlabelled). The length prefixes keep two
  pairs from spelling the same name. Example:
  `p8_xpRtWrap_c8_xpRtLeaf_use_hdl_sv_wrapper` in
  `examples/xprojParam/rtInh/verif/xpRtLeaf_use_hdl_sv_wrapper.sv`.
- A pair top's file is named after the child and label. When that path is also
  the child's own `vlSvWrap` file for the same label, the one generated region
  holds the ordinary top followed by the pair tops
  (`templates/systemVerilog/module_hdl_wrapper.py::render_sv`).
- A parameterized block whose labels are all container-sourced has no bare
  top. Its pair tops are its only tops.
- `<child>VlRegistrar.cpp` exists once per (assembling project, child). A
  composing parent therefore carries its own copy for each `hasVl` child it
  instantiates, beside the child's own copy: `examples/simple_ip/registrar/ipVlRegistrar.cpp`
  and `examples/simple_ip/ip/registrar/ipVlRegistrar.cpp`.

`projectCreate.validateSvDesignUnitNames` rejects two modules or packages that
share a name, across RTL modules, bodies, bare, foreign and pair tops, and
packages. `projectCreate.calcRegistrarPairs` rejects one top name bound to two value sets.

### SystemC wrapper

`templates/systemc/module_hdl_wrapper.py` renders `<block>_hdl_sc_wrapper`. It
is a `template <typename DUT_T, typename Config>` class when the block has own
params and at least one standalone label or Verilated pair registration
(`svWrapper.scWrapperConfigTemplated`). Otherwise it is a plain class whose DUT
is the block's single top. The wrapper holds the hdl_if bridges, the BFMs, the
clock and reset drivers, and the user region `end_ctor_init()`. It names no
concrete Config and registers nothing.

### Registrar

`templates/systemc/vlRegistrar.py` fills `<child>VlRegistrar.cpp` from
`projectOpen.getRegistrarConfigView(child, parent)`:

- The whole file is guarded by `#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)`.
  In a model-only build it compiles to an empty TU.
- For each distinct top it includes the simulator's DUT header (`V<top>.h`,
  `<top>.h` from `vlogan`, or `<top>_xcelium.h`) and declares `<top>_dut_t`
  as the simulator's class for that top.
- It imports the Config modules the container imports, so the container's
  `dynamic_pointer_cast` sees the same type.
- Each registration constructs `<child>_hdl_sc_wrapper<<top>_dut_t, <Config>>`
  under the factory key (`<child>_verif`, label, factory project). The factory
  project is the pair's domain `<owner>.<parentModule>.<childModule>` when the
  child has own params, else the child's owning project. A registration that
  is not pair-specific is also registered under the child's owning project, so
  a standalone testbench finds it.

## 3. Canonical body

`render_body` writes the `.svh` body of a parameterized block.

- The body declares every block parameter with no default
  (`parameter <P>`), followed by `localparam`s for the eval-derived constants
  the port widths use. All of them sit in the `#()` list, ahead of the ports,
  so the port width expressions are in scope.
- The ports are the flattened pins with symbolic widths (section 5), then the
  block's clocks and resets in declaration order.
- After the ports come the module-local parameterized typedefs, interface
  reconstruction, and the DUT instance with every parameter passed by name.
- The scaffold wraps the region in an include guard. Each top `` `include ``s
  the body inside its own generated region, so the body is read once per
  compilation however many tops name it.
- The body is never a top. A module without parameter defaults cannot
  elaborate standalone, and the manifest records only `.sv` files as tops.
- Every flow adds each `vl_wrap` directory as `+incdir` (`A2C_VL_WRAP_DIRS`):
  `make lint`, each verilate, `vlogan` and `xrun`. A top reaches a reused
  child's body through that path.

A block without params gets no `.svh`. Its single `.sv` holds the whole
wrapper and is its only top (`render_non_parameterizable`).

## 4. Trampolines

`render_trampoline` writes each concrete top of a parameterized block: bare,
foreign and pair tops alike.

- It binds each block parameter as a `localparam` in its `#()` list to the
  resolved literal for that top: `standaloneVariants[label]`,
  `foreignVariants[label]`, or the pair registration's `values`. A top has no
  parent scope, so a binding written as a parent symbol would not resolve.
- It repeats the body's eval-derived `localparam`s after the bound
  parameters.
- Its port list is the body's port list with the same symbolic widths, which
  resolve against the bound literals.
- It imports the block's packages, so a constant named in a width or binding
  resolves.
- It instantiates the body with every parameter and pin wired by name.

## 5. Boundary widths

`projectOpen.getIntfSignals` classifies each interface signal for one modport.
SV spelling is `intf_gen_utils.sv_signal_type`. SystemC bridge spelling is
`intf_gen_utils.sc_hdl_bridge_type`. Integer pin widths per top come from
`projectOpen.getVlTopBoundaryPins`.

| Signal | `kind` | `vector` | SV pin | SystemC bridge |
| :--- | :--- | :--- | :--- | :--- |
| `bool` signal | fixed | no | `bit` | `bool` |
| signal typed by a named type | fixed | when width > 1 | `bit [W-1:0]` | `sc_bv<W>` |
| fixed-width payload | payload | when width > 1 | `bit [W-1:0]` | `sc_bv<W>` |
| parameterizable struct payload | payload | yes | `bit [(<expr>)-1:0]` | `sc_bv<S<Config>::_bitWidth>` |
| parameterizable type payload | payload | yes | `bit [(<expr>)-1:0]` | `sc_bv<<width expr over Config>>` |
| unbound optional payload | fixed | when `defaultWidth` > 1 | `bit [W-1:0]` | `sc_bv<W>` |
| eval hdlparam over fixed payloads | fixed | yes | `bit [W-1:0]` | `sc_bv<W>` |
| eval hdlparam over a parameterizable payload | bytes | yes | `bit [(((<expr>)+7)/8)-1:0]` | `sc_bv<S<Config>::_byteWidth>` |

- A named signal type resolves as a database type, in the interface
  definition's scope and then `_a2csystem` (`projectOpen.signalTypeWidth`).
- An `isEval` hdlparam is evaluated at `make db`. Over fixed payloads it gives
  an integer. Over a parameterizable payload it names that payload, and the
  pin is sized by the payload's byte count at each top
  (`processYaml.intfEvalPayload`). Evaluating an unbound optional parameter is
  a fatal error (`intfEvalUnbound`).
- Every top has fixed integer widths. The registrar pairs each top with the
  Config built from the same values the trampoline binds, so the SV width and
  the SystemC `_bitWidth` agree at compile time. `unittest/test_vl_boundary_widths_build.py`
  checks that each top's `V<top>.h`, VCS port map and Xcelium shell list the
  same pins.

**Width-1 rule.** A vector pin stays a vector at width 1: SV `bit [0:0]`,
SystemC `sc_bv<1>`, VCS port map `1 bitvector sc_bv`, Xcelium `sc_bv<1>`. The
hand-written BFMs read `sc_bv` for these pins. Verilator runs with
`--pins-bv 2`, which binds wider pins as `sc_bv` but a 1-bit pin as `bool`.
On a Verilated top, every vector pin of width 1 at that top therefore carries
`/*verilator sc_bv*/` (`module_hdl_wrapper.py::sc_bv_pins`). No other pin
carries it, and the body carries none.

## 6. Ownership

| Artifact | Owner |
| :--- | :--- |
| `.svh` body, `<block>_hdl_sc_wrapper.h`, bare `<block>_<label>` tops | the block's owning project |
| Owner-qualified foreign top and its Config module | the project that declares the label |
| Pair top | the project that owns the parent block (`pair['ownerProject']`) |
| `<child>VlRegistrar.cpp` | the project that owns the assembling parent |

- A foreign top is placed under the declaring project's lowest-sorted
  container of the child (`entry['parentKey']`), in that project's layout.
  Any build that reaches the declaration in scope uses that top: in
  `examples/ip_test`, root `ip_top.uIp1` and `ipBridge.uBridgeIp1` both run on
  `ipBridge_ip_variant1_hdl_sv_wrapper`.
- Bare tops and `standaloneVariants` hold only the owner's own,
  non-container-sourced labels. A label declared elsewhere never adds a bare
  top or a file to the owner's tree, so the reused project stays unchanged
  when a composing build generates.
- A build regenerates only the wrapper files it owns. Child-owned tops are
  still verilated and compiled.
- A pair top is built only in the build whose harness owner owns the pair. A
  composing build swaps a reused IP whole through that IP's own top and never
  verilates the IP's internal pairs. A foreign-owned `VlRegistrar.cpp` that
  names pair tops is listed in `A2C_CPP_EXCLUDE_FILES` and not compiled.

## 7. Manifest records

`config/createBuildManifest.py` writes these into `.gen/build.mk`:

| Variable | Content |
| :--- | :--- |
| `A2C_VL_TOPS` | Every Verilated top name: one per `.sv` wrapper row of a `vl` build-group segment, block and registrar mode, any owner. |
| `A2C_VL_SV_<top>` | The physical `.sv` holding that top. Two tops can name one file. |
| `A2C_VL_PORTMAP_<top>` | `.gen/vl/<top>.portmap`. |
| `A2C_VL_TOP_<block>` | The DUT top for that block name: the bare top at its instance's label. It is written for the top block when `hasVl` and for each direct child with `hasVl`. |
| `A2C_VL_WRAP_DIRS` | Every `vl_wrap` directory, used as `+incdir` and `-I`. |
| `A2C_VL_REGISTRAR_SRC` | The compiled `VlRegistrar.cpp` files. |
| `A2C_CPP_EXCLUDE_FILES` | Registrar TUs recorded but not compiled (section 6). |
| `A2C_VL_GEN_INC` | `.gen/vl`. |

The top name always comes from the record. No make rule derives it from a
file name with `$(notdir)` or a pattern.

- `include/make/a2c-vl-wrap.mk::vl_top_rule` runs one verilate per top with
  `--Mdir obj_dir/<top>` and `-top <top>`, so parallel verilates never share
  an output directory. The archive `lib<project>vl_s_wrap.a` takes the members
  of each `obj_dir/<top>/V<top>__ALL.a` plus the runtime objects. All of it
  sits under `A2C_VL_BUILD_DIR` (`$(BIN_DIR)/vl`).
- `include/make/a2c-systemc.mk` adds `-I$(A2C_VL_BUILD_DIR)/obj_dir/<top>` for
  each top under `VL_DUT`, so the registrar finds `V<top>.h`.
- `include/make/a2c-vcs.mk` runs `vlogan -sc_model <top> -sc_portmap $(A2C_VL_PORTMAP_<top>)`
  on `$(A2C_VL_SV_<top>)` for each top.
- `include/make/a2c-xrun.mk` compiles the sorted, de-duplicated set of
  `A2C_VL_SV_<top>` files into the DUT library.

`arch2code.py --vlBoundary` (`pysrc/vlBoundaryGen.py::vlBoundaryGen`) writes
`.gen/vl/<top>.portmap` and `.gen/vl/<top>_xcelium.h` for every manifest top,
from `getVlTopBoundaryPins`. `make gen` runs it only under `USE_VCS` or
`USE_XCELIUM` when `A2C_VL_TOPS` is non-empty. File formats and the simulator
flows are in `specs/SIMULATOR_INTEGRATION.md` §1.5.

## 8. Selecting a Verilated instance

- `--vlInst <path>` registers that instance path with `--vlType` (default
  `verif`) in `common/systemc/simController.cpp`. When the container creates
  that instance, the factory looks up `<block>_verif` under the container's
  factory key and builds the registered wrapper. The instance and its subtree
  run as RTL. A path that matches no instance fails with `Unknown instance`.
- `make run VL_DUT=1` passes `--vlInst $(HDL_TOP_MODULE)`. Projects add
  targets for other instances, such as `run-vl-ip1` and `run-vl-uBridgeIp1` in
  `examples/ip_test/rundir/Makefile`.
- `make lint` (`include/make/a2c-rtl.mk`) lints the top named by
  `A2C_VL_TOP_$(HDL_TOP_MODULE)`, with its source from `A2C_VL_SV_<top>`. When
  neither the top block nor a direct child has `hasVl`, it fails and lists the
  available `A2C_VL_TOP_<block>` keys. A command-line
  `TOP_HDL_SV_WRAPPER_NAME` overrides the lookup.
- `examples/pySocket` is a multi-top case: top block `pySocket` and its child
  `dut` both have `hasVl`, so the manifest carries `A2C_VL_TOP_pySocket` and
  `A2C_VL_TOP_dut`, and `HDL_TOP_MODULE` picks one.

## Reference fixtures

| Fixture | Shows |
| :--- | :--- |
| `examples/ip_test` | Body and bare tops (`ip`, `src`, `ipLeaf`), the foreign top `ipBridge_ip_variant1_hdl_sv_wrapper`, per-assembler registrars in `top/`, `bridge/` and `ip/`, hierarchical layout |
| `examples/simple_ip` | A composing parent's registrar copy for a reused child's bare top |
| `examples/hierVlDemo` | Hierarchical layout with a single non-parameterized top |
| `examples/pySocket` | Two `A2C_VL_TOP_<block>` entries, functional layout (`verif/vl_wrap/`) |
| `examples/xprojParam/rtInh`, and `examples/inhTandem` in A2C Pro | Pair tops sharing a file with the bare top |
| `unittest/fixtures/vl-boundary-widths` | Every top shape and signal form (`test_vl_boundary_widths_build.py`) |
