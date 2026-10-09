# Specification: Block Registration

A generated SystemC parent never names its child's implementation class. It asks
`instanceFactory` for an instance by a string key, and something linked into the binary
must already have registered a constructor under that key. This spec covers the key,
the lookup, the registration triggers that put a registration into the binary, the
registrar files the generator emits for them, the factory domain that keeps reused children apart, and
the link rules that keep the registrations alive.

**Scope.** Not covered here: authoring parameters and variants
(`specs/spec-parameter-inheritance.md`, skill `design-parameterizable-blocks`), the SV
contents of Verilated wrappers (`specs/spec-verilated-wrappers.md`), and tandem wrapper
emission (`builder/pro/specs/spec-tandem-parameterized-types.md`). The user-facing side
is taught by the `manage-build` skill (scaffolding and stale registrar cleanup) and the
`verify-cosimulation` skill (the `_verif` swap).

## 1. Purpose and invariants

1. A parent and the testbench import only `<child>.base`, plus the child's Config
   module when they cast to `<child>Base<Config>`. The one exception is a
   container-typed child (section 6), whose container imports `<child>.block`.
2. A block's model and base module units are text-stable: adding a project, an
   instance or a Config elsewhere does not change them. Registrations that depend on
   who instantiates a block live in the assembler's registrar files, not in the
   block's module. The block's other files can change: the owner's bare `vlSvWrap`
   file also holds the pair tops of that project's parents, the `vlScWrap` class
   becomes a Config template once a pair registers a `_verif` row, and the Pro
   tandem registrations take their keys from the pairs.
3. Every registration static sits in a translation unit the build links directly, so
   its initializer runs before `main`.
4. Within one pair domain, `(blockType, variant)` maps to exactly one Config. In the
   child-owner domain this holds per assembling project only (section 5).
5. A parent reaches a child only through `instanceFactory::createInstance` and a
   string key. It holds no symbol reference to the child's object file, except for a
   container-typed child (section 6), whose container imports `<child B>.block` and
   names the class (`examples/mixed/model/blockG.cppm`).

## 2. Runtime API

Code: `common/systemc/instanceFactory.h`, `common/systemc/instanceFactory.cpp`.

The map key is `instanceFactory::Key{blockType, variant, projectName}`.

| Field | Content |
| :-- | :-- |
| `blockType` | `<block>_<suffix>` |
| `variant` | The variant label; empty for a block with no declared variants |
| `projectName` | The factory domain (section 5): a pair domain `<owner>.<parentModule>.<childModule>`, or a bare project name (the child-owner domain, or the building project for a self-registering static). Empty only for framework blocks such as `watchDog_model` |

`registerBlock(blockType, factory, variant, projectName)` inserts with `std::map::emplace`.

**Suffix taxonomy.** `createInstance` forms `blockType` from the instance-type map.
`registerInstance(path, type)` stores `type` under `tb.<path>`, and the lookup tries the
instance's qualified name, then `tb.` prepended.

| Suffix | Registered by | Selected when |
| :-- | :-- | :-- |
| `_model` | Self-registering static (non-templated block, testbench top), `blockRegistrar` (templated block), framework blocks | No instance-type entry (default) |
| `_verif` | `vlRegistrar` (`<child>VlRegistrar.cpp`) | `--vlInst <path>`, `--vlType verif` (the default `vlType`) |
| `_socket` | Socket shell static (`constructorSocket.py`) or `blockRegistrar` socket rows for a templated block | The testbench config calls `registerInstance(path, "socket")` (`examples/pySocket/tb/pySocket/pySocketConfig.cpp`) |
| `_tandem` | Pro `constructorTandem.py` | `--vlInst <path> --vlTandem` registers `tandem` for the path |
| `_<vlType>` | Any registration under that suffix | `--vlInst <path> --vlType <vlType>` |

Tandem halves are requested with an explicit `instanceFactoryMode`.
`INSTANCE_FACTORY_PRIMARY_TYPE` maps to the run's `--vlType` (set by
`simController` through `setInstanceFactoryMode`), and `INSTANCE_FACTORY_SECONDARY_TYPE` to
`model`. See the tandem spec for the wrapper itself.

**Lookup order** in `createInstance`, with `projectName` held fixed throughout:

1. The exact key `(blockType, variant, projectName)`.
2. The `containerSuppliedFactory`, only when the requested mode is the model (no
   instance-type entry, or entry `model`). For any other mode it is discarded.
3. The empty-variant key `(blockType, "", projectName)`.
4. `Q_ASSERT`: `Attempted to create an instance <name> of an unregistered block type <blockType>`.

A lookup never falls back to another domain, so an unknown variant cannot borrow
another project's registration.

**First write wins.** A second `registerBlock` under an existing key is silently
dropped, and static-initialization order across translation units is unspecified. The
generator therefore must not emit two different constructors under one key. At
database creation, `processYaml.py::calcRegistrarPairs` raises when a pair maps one
variant to two Configs, and `validate_inherit_container_params` rejects a child reached
both through `inheritContainerParam` and through a variant-less instance. At generation
(`make gen`, `make newmodule`), `getRegistrarConfigView` raises when a project's pairs
map one label to two descriptors, and when the project of the stamped `--parent` owns
no pair for the child. Two different assembler projects in one build that each register
the same label in the child-owner domain (section 5) are not checked; the first static
to run wins.

## 3. Registration triggers

| Trigger | What registers | Where | Static form |
| :-- | :-- | :-- | :-- |
| Retain-marked static: non-templated block (no own `params:`) | `<block>_model` | The block's own module unit: `constructor.py::blockRegistrarInitLines` | `register_<Class>_variants()` called by an `A2C_REGISTRATION_RETAIN` static in an anonymous namespace |
| Retain-marked static: socket shell of a non-templated block | `<block>Socket` as `<block>_socket`, variant `""` only | `<block>Socket.cppm`: `constructorSocket.py::constructorInitSocket` | `register_<block>Socket()` called by an `A2C_REGISTRATION_RETAIN` static in an anonymous namespace |
| Retain-marked static: testbench | `<tb>Testbench_model` in the factory; `<tb>Config` in `testBenchConfigFactory` | `testbench.py` (`sec_tb_class_init_template`, `sec_tb_config_registration_template`) | Same retain-marked static |
| Registrar: child with own `params:` (`hasOwnParams`) | `<child>_model` per Config, plus `_socket` when `hasSkt` | `<child>Registrar.cppm` of the assembling project (`templates/systemc/blockRegistrar.py`) | `static _<child>_registrar` instance in an anonymous namespace |
| VL registrar: child with `hasVl` | `<child>_verif` per Config | `<child>VlRegistrar.cpp` of the assembling project (`templates/systemc/vlRegistrar.py`) | Same, inside `#if defined(VERILATOR) \|\| defined(VCS_DUT) \|\| defined(XCELIUM_DUT)` |
| Retain-marked static: Pro tandem | `<block>_tandem` per Config; a templated block takes its keys from the `verifRegistrations` of this project's pairs, else `PROJECTNAME` | `base/<block>Tandem.cpp` (Pro `constructorTandem.py`) | `register_<suffix>()` functions called by `A2C_REGISTRATION_RETAIN` statics, all in an anonymous namespace |

A self-registering static of a block, socket shell or testbench registers under the
`PROJECTNAME` of the build that generates the file, which the ownership gate makes the
block's owning project. A plain build compiles the VlRegistrar files to empty objects,
so `_verif` exists only in an HDL DUT build.

`A2C_REGISTRATION_RETAIN` expands to `[[gnu::used, gnu::retain]]` on GCC and Clang and to
nothing elsewhere. The registrar statics carry no attribute and rely on direct linking
(section 8).

## 4. Registrar artefacts

All entries are `mode: registrar` in `config/project.yaml` `fileGeneration.fileMap`.
Their `cond`/`condAnd` predicates test the child block's row.

| fileMap key | File | Condition | Content |
| :-- | :-- | :-- | :-- |
| `blockRegistrar` | `<child>Registrar.cppm`, module `<owner>.<child B>.registrar`, where `<owner>` is the assembler's project and `<child B>` is `BLOCKMODULENAME[child]` (`examples/mixed/registrar/blockFRegistrar.cppm` exports `mixed.mixed_blockF.registrar`) | `hasOwnParams` and `hasMdl`; `requiresRegistrations` | Model and socket registrations |
| `blockVlRegistrar` | `<child>VlRegistrar.cpp` | `hasVl` | `_verif` registrations of `<child>_hdl_sc_wrapper` |
| `configModule` | `<stub>VariantConfig.cppm`, module `<declaringProject>.<child>.config` | `hasOwnParams`; `ownerQualified` | The declaring project's default and variant Config structs |
| `vlSvWrapForeign` | Owner-qualified `<stub>_<label>_hdl_sv_wrapper.sv` | `hasOwnParams` and `hasVl`; `ownerQualified`, `variant` | SV top for a label this project declares of a block another project owns |
| `vlSvWrapPair` | `<child>_<label>_hdl_sv_wrapper.sv` | `hasOwnParams` and `hasVl`; `pairVlTop` | Pair-qualified SV tops for pair-specific `_verif` registrations (container-sourced variants and `inheritContainerParam` instances), module `p<n>_<parentSv>_c<m>_<childSv>_<label>_hdl_sv_wrapper`, with the SV module names of parent and child and the parent's active variant as `<label>` (`specs/spec-verilated-wrappers.md` §2; `builder/pro/examples/inhTandem/verif/xpInhLeaf_alt_hdl_sv_wrapper.sv`) |

`<stub>` is `qualifyModuleIdentity(child, declaringProject)` (`specs/spec-cpp-module-layout.md`
§2): `<declaringProject>_<child>`, or the bare child name when it already leads with the
project (`examples/xprojParam/gain/registrar/xpGainVariantConfig.cppm`,
`examples/ip_test/ip/registrar/ipVariantConfig.cppm`).

The Config module drops the project prefix from its module name when the block name
already leads with the project (`examples/xprojParam/shared/registrar/xpGainRegistrar.cppm`
imports `xpGain.config`).

**One file per (owning project, child).** The owning project is the assembler's. The
file aggregates every pair in that project that instantiates the child, so its module
name has no parent in it. `blockRegistrar.py` and `vlRegistrar.py` read the aggregate
through `getRegistrarConfigView`. `builder/pro/examples/inhTandem/registrar/xpInhLeafVlRegistrar.cpp`
carries two parents, `xpInhCont` and `xpInhWrap`, in one file. This holds while the
project's parents of that child share a directory: `artifactRows` emits one row per pair
at that parent's directory, so two parents in different directories or nodes would
produce two files exporting one module, and `gen_cpp_module_map.py::render_module_map`
fails the build.

**Placement.** `pysrc/artifactPaths.py::artifactRows` emits one row per pair and
anchors it at the assembler block's directory in the assembler's layout:
`$root/registrar/<decomp>/` (functional) or `<node>/registrar/` (hierarchical). The
SV entries use the `vl_wrap` segment instead. The `configModule` and `vlSvWrapForeign`
rows are not per pair: there is one per `CONFIGMODULES` or `FOREIGNCONFIGHEADERS` entry
(one `vlSvWrapForeign` row per label), anchored at the entry's `parentKey`, which is the
declaring project's lowest-sorted reachable container of the child, else the child
itself (`processYaml.py::calcConfigModules`).

**`requiresRegistrations`.** A `blockRegistrar` row is dropped when no pair of that
(project, child) has a model registration (`aggregateHasModelRegistrations`). This
happens when every binding of the child is container-typed. If the template is still
reached, it stops with "nothing to register".

**Stamp and ownership.** The scaffold stamps `--block=<child> --parent=<anchor>`. The
anchor is the assembler for a per-pair row and the entry's `parentKey` for a Config
module, which may be the child itself (`examples/xprojParam/gain/registrar/xpGainVariantConfig.cppm`).
`processYaml.py::resolveFileOwner` checks `--parent` before `--block`, so the file
belongs to the anchor's project. `newModule.registrar_create_from_rows` skips rows
another project owns. `newModule.cleanup_stale_registrar_files` deletes generated files
in owned registrar directories that no row names, and `createBuildManifest` warns about
them. A stale `--parent` that names a retired pair still renders, because the
view seeds its identity from any pair of the child.

## 5. Factory domain

The factory domain is the key's third field. `calcRegistrarPairs` sets the pair domain
of each (parent, child) pair to

```
<owner>.<blockModuleName[parent]>.<blockModuleName[child]>
```

where `<owner>` is the parent's owning project. It is computed for every instance with
a block container, reachable or not, so a composing build registers a pair under the
same domain its owner does. Example: `xpInhTandem.xpInhTandem_xpInhCont.xpInhTandem_xpInhLeaf`.

The `projectName` a generated site passes to `createInstance` is
`createInstanceProjectName` (`processYaml.py::getBDInstances`):

| Child | Site passes |
| :-- | :-- |
| Has own `params:` | The pair domain (`PAIRFACTORYPROJECTS[(parent, child)]`) |
| Any other child | The child-owner domain: the child's owning project, bare |
| Testbench DUT and `createTbTop()` | The project's `PROJECTNAME`, bare |

The registrar emits each row under the domains those sites ask for
(`getRegistrarConfigView`):

| Row | Domains |
| :-- | :-- |
| Model | Each pair's domain, plus the child-owner domain |
| `_verif` | The pair domain if the child has own `params:`, else the child-owner domain; plus the child-owner domain for rows that are not pair-specific |
| Socket | Same as model |

The socket rows mirror the model rows, so a parameterizable block with `hasSkt` and no
`hasMdl` would have none; `validateParameterizedSocketHasModel` rejects it.

The child-owner registration serves sites that are not a pair: a standalone testbench,
or a DUT site, asking for `(child, variant, childOwner)`. Container-sourced Configs are
never registered there, because two parents may bind one label to different values.

Two parents reusing one child do not collide because their pair domains differ. Within
one owning project, the descriptor check in section 2 keeps the child-owner domain at one
Config per label. Across projects it does not: every assembling project registers each
of its model rows, including labels another project declares, in the child-owner domain
(`examples/ip_test/top/registrar/ipRegistrar.cppm` registers `ipBridge_ipVariant1Config`
under `("ip_model", "variant1", "ip")`), so two assemblers that bind one label to
different Configs collide there and the first static wins.

## 6. Container-typed children

A child is container-typed when its Config is a function of its container's Config:
an `inheritContainerParam` instance, or a variant with `containerParam` bindings. It is
a family of C++ types, one per container Config, and the key has no Config field to pick
one. So:

- `calcRegistrarPairs` emits no model registration for it, and `blockRegistrar` registers
  nothing for it.
- The container's site names the class:
  `createInstance<<child><ConfigExpr>>(name(), "<inst>", "<child>", variant, "<pairDomain>")`
  (`intf_gen_utils.py::cpp_container_typed_instance_arg`). The variant argument is the
  container's own runtime `variant`, not a literal.
- `createInstance<Impl>` wraps `make_shared<Impl>` as the `containerSuppliedFactory`.
- The exact key is still tried first, so a registration under
  `(<child>_model, containerVariant, pairDomain)` replaces the class the site names.
- Other modes find the pair-specific `_verif` rows the VlRegistrar emits for each parent
  variant. For an `inheritContainerParam` instance the row's Config is the parent's
  Config itself; for a variant with `containerParam` bindings it is the child's Config
  template applied to that parent Config. The supplied factory is never used for them.
- Those rows exist only in the build whose harness owner owns the pair. In a composing
  build, `--vlInst` on an inheriting child inside a reused IP therefore finds no `_verif`
  registration.

Worked example: `examples/xprojParam/inhVar/model/xpInhCont.cppm`.

## 7. Config type identity

The container casts with `std::dynamic_pointer_cast<<child>Base<Cfg>>`. The class that
the registrar or VlRegistrar builds must derive from the same `<child>Base<Cfg>`, which
holds only if every party names `Cfg` from the same declaration. The container
(`configModules` in `getBDInstances`), the SC registrar (`configModules`) and the VL
registrar (`verifConfigModules`) all import the owner-qualified Config module listed in
`CONFIGMODULES`. A Config struct declared a second time, in a header or another module,
is a distinct type. The cast then returns null, and the run fails at the first use of
the child, typically a port bind.

## 8. Link contract

- An object file named on the link line is always linked, and its static initializers
  run. The shipped makefiles link every SystemC object directly (`$(OBJ)` in
  `include/make/a2c-systemc.mk`), so they need no flag. The Verilator archive
  `lib<project>vl_s_wrap.a` holds no registration.
- A static archive member is extracted only if something references a symbol in it.
  A project that packages block or registrar objects into an archive must link it with
  `-Wl,--whole-archive` (GNU and LLVM), `-force_load` (Apple ld64) or `/WHOLEARCHIVE:`
  (MSVC). The registrar and VlRegistrar statics sit in anonymous namespaces, so those
  objects define no external symbol a reference could pull in. No source attribute
  overrides archive extraction.
- `A2C_REGISTRATION_RETAIN` protects only against dead-code elimination and
  `--gc-sections`. On a compiler that is neither GCC nor Clang it expands to nothing.

## 9. Data sources

| Source | Built by | Content |
| :-- | :-- | :-- |
| `REGISTRARPAIRS` | `processYaml.py::calcRegistrarPairs` (projectCreate) | Per reachable `(parentKey, childKey)`: owner, module identities, pair domain (`factoryProject`), `modelRegistrations`, `verifRegistrations` (with DUT top, header and class per simulator), `variantDescriptors`, `pairVlStem`, `ownerPairSpecific`, `aggregateHasModelRegistrations` |
| `PAIRFACTORYPROJECTS` | Same | `(parentKey, childKey)` to pair domain, for every contained instance |
| `CONFIGMODULES` | `processYaml.py::calcConfigModules` (projectCreate) | `(declaringProject, childKey)` to module name, stub and anchor parent |
| `getRegistrarConfigView(child, parent)` | projectOpen view | The (owning project, child) aggregate with model, `_verif` and socket rows already under their domains, and the Config modules to import |

Consumers: `artifactPaths.artifactRows` (shared by `newModule` and
`config/createBuildManifest.py`), `templates/systemc/blockRegistrar.py`,
`templates/systemc/vlRegistrar.py`, `templates/systemVerilog/module_hdl_wrapper.py::pair_registrations`,
`processYaml.py::getBDInstances`, `getBDSvWrapperNames`, `calcVlTops` and
`validateSvDesignUnitNames`, and Pro `constructorTandem.py`.
`createBuildManifest` does not compile a VlRegistrar owned by a project other than the
harness owner when its pair is owner-pair-specific, because such a file includes DUT
headers that only the owner's build generates; it lists it in `A2C_CPP_EXCLUDE_FILES`.
