# C++ module layout

Every generated SystemC artefact a block or context owns is one of three kinds of file: a
C++20 module interface unit (`.cppm`), a plain translation unit (`.cpp`), or a textual header
(`.h`). This document states which artefact is which and why, how each module is named, the
three zones of a module unit and what may go in each, the generated regions and user slots of
every unit, and the rules that decide what a generated region emits and what a create-once
scaffold may hold. The code is the authority: `config/project.yaml` `fileGeneration.fileMap`,
`templates/fileGen/fileGen.py` (scaffolds), `templates/systemc/moduleScaffold.py`,
`templates/systemc/testbench.py`, `templates/systemc/blockRegistrar.py`,
`pysrc/intf_gen_utils.py` (module-name spelling and dependency sets) and
`pysrc/processYaml.py` (identities).

**Scope.** This document does not cover what to write in a user slot, port and interface
calls, or the migration procedure for legacy `.h`/`.cpp` projects. The user-facing side is
taught by `rules/skills/systemc-core.md` (block files), `rules/skills/verify-testbench.md`
(testbench files) and `rules/skills/migrate-project.md` (migration).

## 1. Artefact inventory

| fileMap key | File | Kind | Why this kind |
| :-- | :-- | :-- | :-- |
| `blockModule` | `model/<block>.cppm` | module unit | Holds the class and every member body, so a templated class is instantiable by an importer with no out-of-line `.cpp`. One form for every block with `hasMdl`. |
| `blockBase` | `base/<block>Base.cppm` | module unit | Base, Inverted and Channels classes, imported by the block, its parent and the testbench. |
| `socket` | `model/<block>Socket.cppm` | module unit | Python-socket shell, laid out like a block. |
| `include` | `model/<includeName>Includes.cppm` | module unit | A context's constants, types, enums and structures. |
| `blockRegistrar` | `registrar/<child>Registrar.cppm` | module unit | Registers a Config-templated child's per-variant classes for one owning project. |
| `configModule` | `registrar/<stub>VariantConfig.cppm` | module unit | One owner-qualified Config module per (declaring project, block). |
| `tbExternal` | `tb/<block>/<block>External.cppm` | module unit | Imports the DUT base, child bases and contexts; imported by the Testbench. |
| `testBench` | `tb/<block>/<block>Testbench.cppm` | module unit | Imports the External; imported by a `Config.cpp` that names the top. |
| `tbConfig` | `tb/<block>/<block>Config.cpp` | translation unit | User code in it interleaves `#include` and `import`, which only a plain TU allows. Nothing imports it. |
| `blockVlRegistrar` | `registrar/<child>VlRegistrar.cpp` | translation unit | Includes the simulator-generated DUT headers, chosen per simulator by the preprocessor. |
| `vlScWrap` | `<vl_wrap>/<block>_hdl_sc_wrapper.h` | header | The Verilator boundary: included next to the textual Verilated model headers by the VlRegistrar TUs. It carries `import <B>.base;`, so only a plain TU can include it. |
| `socketCatalog` | `base/<block>SocketCatalog.h` and `.py` | header + Python | Shared C++/Python name catalog. |
| `includeFW` (opt-in) | `<context>IncludesFW.h` / `.cpp` | header + TU | Firmware must build with C toolchains; it is never a module. The entry is commented out in the base fileMap and a project declares it. |
| `tandem` (builder/pro) | `base/<block>Tandem.h` / `.cpp` | header + TU | Self-contained: only its own `.cpp` includes its header. |

The framework supplies one module of its own, `a2c.endOfTest` (`common/systemc/endOfTest.cppm`).
It is imported, never included, so one `endOfTestState` singleton exists across all modules.

## 2. Module identity

Two tokens qualify every name:

- `<B>` = `qualifyModuleIdentity(block, owner)` for a block, persisted as `BLOCKMODULENAME`.
- `<C>` = `qualifyModuleIdentity(includeName, owner)` for a context, persisted as
  `CONTEXTMODULEIDENTITY`.

`owner` is the project that owns the defining YAML file (`CONTEXTOWNINGPROJECT`), so a child IP
spells the same identity standalone and composed. `qualifyModuleIdentity`
(`pysrc/processYaml.py`) returns `<project>_<name>`, except that a name equal to the project
name, or starting with `<project>_`, is returned unchanged. Both tokens pass through
`sanitizeIdentifierToken`, which maps `-` and `.` to `_`. Qualification always applies; it is
not a collision fallback.

| Unit | Module name | Spelled by |
| :-- | :-- | :-- |
| block | `<B>.block` | `intf_gen_utils.cpp_block_module_name` |
| base | `<B>.base` | `cpp_base_module_name` |
| socket shell | `<B>.socket` | `cpp_socket_module_name` |
| External | `<D>.external` | `cpp_tb_external_module_name` |
| Testbench | `<B>.testbench` | `cpp_tb_module_name` |
| context | `<C>`, namespace `<C>_ns`, test namespace `<C>_test_ns` | `cpp_module_name`, `cpp_namespace_name` |
| Config | `<project>.<block>.config`, or `<block>.config` when the block leads with the project | `processYaml.calcConfigModules`; block view field `ownConfigModule` |
| registrar | `<owner>.<B>.registrar` | `cpp_child_registrar_module_name` |

`<D>` is the DUT's `<B>`. When the External's `GENERATED_CODE_PARAM` names a `_tb` container with
`--excludeInst`, `testbench.py::refactor_tbExternal` takes the identity from the excluded
instance (`instanceTypeModuleName`), so the External keeps the DUT's name.

The Config module has a separate stub, `qualifyModuleIdentity(block, declaringProject)`, which is
the file stem (`<stub>VariantConfig.cppm`) and the struct stem (`<stub>Config`,
`<stub><Variant>Config`, `processYaml.configStructName`). A project that declares variants of
another project's block gets its own Config module for that block.

The registrar module is one per (owning project, child). The pair domains
(`<owner>.<parent B>.<child B>`) are factory domains of the registrations inside it, not module
names.

Examples from the tree:

| Example | Name |
| :-- | :-- |
| `examples/simple_ip/model/dataGen.cppm` | `simple_ip_dataGen.block` |
| `examples/simple_ip/ip/model/ip.cppm` (block `ip`, project `ip`) | `ip.block` |
| `examples/simple_ip/model/simple_ipIncludes.cppm` | `simple_ip`; it imports `common_shared_types` and `ip` |
| `examples/simple_ip/tb/simple_ip/simple_ipExternal.cppm` (`--block=simple_ip_tb --excludeInst=u_simple_ip`) | `simple_ip.external` |
| `examples/mixed/registrar/mixed_blockFVariantConfig.cppm` | `mixed.blockF.config` |
| `examples/ip_test/ip/registrar/ip_ipRegsVariantConfig.cppm` | `ip.ipRegs.config` |
| `examples/mixed/registrar/blockFRegistrar.cppm` | `mixed.mixed_blockF.registrar` |
| `examples/ip_test/top/registrar/ipRegistrar.cppm` | `ip_test.ip.registrar` |

Uniqueness is checked twice. `projectCreate` rejects two contexts, two blocks, or two Config
declarations sharing an emitted name (`deriveModuleIdentities`, `calcConfigModules`, both through
`rejectSharedName`). At build time `pysrc/gen_cpp_module_map.py::render_module_map` fails when two
`.cppm` files export the same module. A `.cppm` with no `export module` line (an unfilled
scaffold) is skipped with a warning.

## 3. The three zones

A module interface unit has three zones, and each kind of content has exactly one legal home.

| Content | Zone | Attaches to |
| :-- | :-- | :-- |
| `module;` then `#include` and preprocessor lines | global module fragment (GMF) | the global module |
| `export module X;` | boundary | |
| `import` lines | preamble: after `export module`, before the first non-import declaration | |
| `using namespace`, classes, definitions | purview | module `X` |

Consequences:

- A non-modular header included in the purview attaches its declarations to `X`. A plain TU that
  imports `X` and also includes the header then sees one entity attached twice, which is a hard
  error. Shared headers therefore go in the GMF.
- A pimpl header whose class is defined in a plain `.cpp` must go in the GMF, so the class
  attaches to the global module and matches the `.cpp` at link time.
- Any declaration ends the preamble. A `using namespace` or a `#include` in the preamble makes a
  later `import` ill-formed.
- Names declared in an imported module's GMF are reachable but not visible to the importer, and
  a plain `import` is not re-exported. A unit therefore imports every module whose names it
  spells, even when another import already depends on it.
- An exported template that names an internal-linkage entity is ill-formed, so generated
  constants are `inline constexpr`, never namespace-scope `const`.

`Config.cpp` and the other plain TUs have no zones: `#include` and `import` may appear in any order.

## 4. Region and slot map

Brackets are generated regions (`GENERATED_CODE_BEGIN --template=... --section=...`). Unbracketed
lines are scaffold-owned: written once by `make newmodule` and never touched by `make gen`.

The two module-unit slots carry one wording everywhere, `fileGen.USER_INCLUDES_SLOT` and
`fileGen.USER_IMPORTS_SLOT`:

```
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
...
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
```

Files scaffolded earlier carry the one-line labels `// user #includes here` and `// user imports
here` (`examples/mixed/model/blockBRegs.cppm`). A label is user content, so `make gen` leaves it
as it is. `pysrc/migrateModuleHeader.py::_INSERT` reproduces the imports label byte for byte.

**Block, `model/<block>.cppm`** (`fileGen.blockModule_cppm`). PARAM `--block=<block> --mode=module`.

```
[moduleScaffold --section=blockModuleHeader]   module; systemc.h, logging.h, DB-directed includes
  slot: user #includes                         GMF
[moduleExport]                                 export module <B>.block; every import
  slot: user imports                           preamble
[classDecl]                                    using-directives, export class head, generated members
  slot: // block implementation members        class body
};                                             scaffold
[constructor --section=init]                   SC_HAS_PROCESS and registration (untemplated), ctor head, init list
  slot: init-list continuation                 each entry starts with a comma
[constructor --section=body]                   { generated body
  slot: constructor body                       SC_THREAD, ADD_TEST, other ctor logic
};                                             scaffold
  slot: out-of-line definitions                to end of file
```

**Register handler, `model/<block><suffix>.cppm`** (`fileGen.blockRegsModule_cppm`). The same
layout and the same five user slots, with `blockRegs --section=header|init|body` in place of
`classDecl` and `constructor`. `blockRegs --section=header` emits the using-directives at its
head, as `classDecl` does. `examples/mixed/model/blockBRegs.cppm` shows the slots.

**Socket shell, `model/<block>Socket.cppm`** (`fileGen.socket_cppm`). `socket --section=moduleHeader`,
includes slot, `socket --section=moduleExport`, imports slot, `socket --section=socket`, a
`// socket shell members` slot, scaffold `};`, `socketConstructor --section=initSocket` and
`--section=bodySocket`, scaffold `}`, then `// user method definitions here`.

**Base, `base/<block>Base.cppm`** (`fileGen.blockBase_cppm`). `moduleScaffold
--section=baseModuleHeader` holds the GMF, `export module <B>.base;`, the context imports and
their using-directives. `baseClassDecl` holds the exported classes and their closing braces.
No user slots; the file is purely generated.

**Context, `model/<includeName>Includes.cppm`** (`fileGen.include_cppm`). PARAM
`--project=<p> --context=<yaml> --mode=module`. Regions: `moduleScaffold --section=moduleHeader`
(GMF and `export module <C>;`), `headers` (imports and using-directives of included contexts),
`includes --section=constants|types|enums`, `structures`, `structures
--section=testStructsHeader|testStructsCPP`. No user slots.

**External, `tb/<block>/<block>External.cppm`** (`fileGen.tbExternal_cppm`). PARAM
`--block=<block> [--variant=<v>] --mode=module`; a user may retarget `--block` at the `_tb`
container and add `--excludeInst=<dut>`.

```
[moduleScaffold --section=tbExternalModuleHeader]  module; systemc.h, logging.h, instanceFactory.h,
                                                   channel and thunker headers (excludeInst only)
  slot: user #includes
[moduleExport --fileMapKey=tbExternal]             export module <D>.external; imports
  slot: user imports
[tbExternal --section=header]                      using-directives, export class, eotThread()
  slot: // external implementation members         seeded with a commented test and voter guide
};                                                 scaffold
[tbExternal --section=init]                        ctor head and init list
  slot: init-list continuation
[tbExternal --section=body]                        { bindings, SC_THREAD(eotThread)
  slot: constructor body                           seeded ADD_TEST / SC_THREAD comments
};                                                 scaffold
  slot: out-of-line definitions
```

**Testbench, `tb/<block>/<block>Testbench.cppm`** (`fileGen.testBench_cppm`).
`moduleScaffold --section=testBenchModuleHeader`, includes slot, `moduleExport
--fileMapKey=testBench`, imports slot, `testbench --section=header` (using-directives and the
whole class including its `};`), `testbench --section=init` (registration and constructor). The
scaffold owns no class seam. The two slots are seeded so a scoreboard header or an import has a
legal zone.

**Config, `tb/<block>/<block>Config.cpp`**: section 8.

**Registrar, Config module, VlRegistrar** (`fileGen.blockRegistrar_cppm`,
`configModule_cppm`, `blockVlRegistrar_src`). PARAM `--block=<child> --parent=<parent>`, then one
region (`blockRegistrar`, `config`, `vlRegistrar`) that emits the whole unit, GMF and module line
included. No user slots.

`moduleExport` dispatches on `--fileMapKey`: absent means the block's own unit;
`tbExternal` and `testBench` select `testbench.ext_module_export` and `tb_module_export`
(`moduleScaffold.TB_MODULE_EXPORTS`).

## 5. Generator invariants

- **`moduleExport` emits `export module` and imports only.** Using-directives go at the head of
  the class region: `classDecl` and `blockRegs` through `intf_gen_utils.sc_class_module_usings`,
  the External and Testbench through `testbench._tb_context_usings`. The preamble slot after
  `moduleExport` then stays legal for a hand-written `import`.
- **The GMF region emits includes only**, and only those a generated line needs (section 7).
  In module mode `classDecl` and `baseClassDecl` suppress their own includes, so each lives once.
- **Children arrive by `import <child B>.base;`, never by forward declaration**
  (`intf_gen_utils.sc_instance_includes`). A forward declaration in a module purview declares a
  distinct entity attached to this module, so the `shared_ptr` member type and the
  `dynamic_pointer_cast` target would differ and the cast would return null.
- **Config modules are imported where they are named.** A unit that spells a Config struct
  imports its module: the block (`cpp_own_config_import`, `sc_instance_config_imports`), the
  External and the Testbench (own Config, plus child Configs in the External), and `Config.cpp`
  (`tbConfig --section=prerequisites`). The import is not inherited from `<B>.base` or from
  `<B>.testbench`, because an import is not re-exported. Without the emitted import, a
  `Config.cpp` that imports `<B>.testbench` to cast the top would still fail on the Config name.
- **A container-typed child's block module is imported** (`import <child B>.block;`) where the
  container names the child class at its `createInstance<Impl>` site, as in
  `examples/mixed/model/blockG.cppm`.
- **Module identity comes from view fields** (`blockModuleName`, `contextModuleIdentity`,
  `ownConfigModule`, `getRegistrarConfigView`), never from a filename, path or stem.

## 6. Exports

The class regions export every class they declare: the block class, the Base, Inverted and
Channels classes, the context namespaces and the Config structs. Two exports have a reason that
generated code alone does not show:

- **`<block>External` is `export class`.** The Testbench unit imports `<D>.external` and holds the
  External as a member.
- **`<block>Testbench` is `export class`** although no generated file imports `<B>.testbench`:
  the factory constructs the top through `createTbTop()` without naming its type. A
  `Config.cpp` commonly imports the module, does `dynamic_cast<<block>Testbench *>` and reaches
  `tb_ptr->external.<member>` before simulation. An unexported class cannot be named by an
  importer. `testbench.py::tb_sec_header` records this.

The registrar exports nothing. It imports `<B>.block` privately, and its registration struct
sits in an anonymous namespace; it only runs its static initialiser.

## 7. Emission rules

1. **A generated region emits an include or import only if a generated line names its symbols,
   or the database directs it.** Convenience includes for user code go in a user slot. The
   block GMF baseline is `systemc.h` (the `SC_MODULE` class and `sc_` ports) and `logging.h` (the
   generated `logBlock log_;`); a user body's `Q_ASSERT`, `std::min` or `clog2` is the user's
   include. The context GMF derives `logging.h`, `<algorithm>`, `bitTwiddling.h` and
   `q_assert.h` from the structures it generates and the `usesClog2` view field
   (`moduleScaffold.moduleHeader`). Emission never depends on user-region text.
2. **A create-once scaffold holds nothing a generated line depends on.** Out-of-region scaffold
   text is frozen for the life of the file, so every prerequisite of generated code lives in a
   region that `make gen` can revise. A scaffold holds markers, slot labels and comments, the
   seam braces that close a class or constructor, and the starting user content it seeds: the
   `Config.cpp` `createTestBench()` and `final()` bodies with the `testController.h` include
   they use, and the External's commented guide.
3. **A purely generated file is deleted and re-scaffolded, never migrated.** No porter, in-place
   fix-up or hand patch is written for a file that hosts no user content; its next
   `make newmodule` plus `make gen` replaces it. In `pysrc/migrateOrphans.py::LEGACY_FILEMAP`
   this is the `delete` disposition (legacy Base header, context includes, packages, SV wrappers).
4. **Classify by hosted user content, not by how clean the scaffold is.** A file whose scaffold
   is markers only can still host user code in a seam. `vlScWrap` hosts `end_ctor_init()` and
   user overrides, the block and External units host class and constructor code, and a
   `.sv` package that carries an `EXTRA_*` generated region inside user code is user-hosted.
   All of these are `port` or `edit`, never `delete`. The Testbench unit is regenerated in full
   but is `port`, because its `GENERATED_CODE_PARAM` `--variant=` is a user choice that must be
   carried across.

## 8. `tbConfig` regions

`<block>Config.cpp` (`fileGen.tbConfigTemplate`), PARAM `--block=<block> [--variant=<v>]` with no
`--mode=module`:

```
[tbConfig --section=prerequisites]   <string>, instanceFactory.h, testBenchConfigFactory.h,
                                     import <own Config module>; (own params only),
                                     import a2c.endOfTest;
  slot: // user #includes and imports here    any order; seeded with #include "testController.h"
[tbConfig --section=class]           class <block>Config : public testBenchConfigBase { ...
                                     protected: createTbTop() ... public:
  slot: createTestBench(), final(), addProgramOptions(), handleProgramOptions() bodies
};                                   scaffold
[tbConfig --section=registration]    register_<block>Config() and its A2C_REGISTRATION_RETAIN static
```

- The two imports exist for the user-owned bodies: `final()` reads `endOfTestState`, and user
  code names the DUT's Config types. The includes (`<string>`, `instanceFactory.h`,
  `testBenchConfigFactory.h`) serve the generated class and registration.
- `createTbTop()` returns `instanceFactory::createInstance("", "tb", "<block>Testbench", "",
  "<project>")`. The project name in the factory key is emitted on every `make gen`, so it always
  matches the Testbench registration.
- `registration` follows the class, so `is_default_testbench_v` sees the complete type,
  including a user-supplied `isDefaultTestBench` marker. `A2C_REGISTRATION_RETAIN`
  (`common/systemc/instanceFactory.h`) protects the static only against dead-code elimination
  and `--gc-sections`; a static archive still needs whole-archive linking.

## 9. Where the user-facing rules live

- `rules/skills/systemc-core.md`: the block file, its slots, module and namespace naming.
- `rules/skills/verify-testbench.md`: External and Testbench slots, `--excludeInst`, the
  `Config.cpp` slot and Config module names.
- `rules/skills/migrate-project.md`: the `.h`/`.cpp` to `.cppm` port, stray imports, and the
  `delete`/`port`/`edit` dispositions.
