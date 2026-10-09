# Specification: Project Composition

A project can instantiate blocks that another project defines, and that other project still
builds and tests on its own. The parent lists the child's project file in `projectFiles:`,
includes the child's design file for scope, and instantiates the child's block by its plain
name. The database holds every parsed file. Each file has exactly one owning project, and only
that project generates, scaffolds or regenerates it. The parent compiles everything it reaches
and regenerates only what it owns. This document states the rules that decide which physical
file provides a project, which project owns each file, how generated names stay unique across
projects, what the active build compiles, and the order in which composed projects are built
and migrated.

**Scope.** This document does not cover include scope inside one project, parameter
declaration and binding (see `specs/spec-parameter-inheritance.md`), or the directory layout of
one project. The user-facing side is taught by `rules/skills/design-yaml-includes.md`, with
`setup-project.md`, `manage-build.md` and `migrate-project.md` for project setup, builds and
migration.

---

## 1. Terms

| Term | Meaning |
| :--- | :--- |
| Project | One project file (`projectName`, `dirs`, `fileGeneration`) and the design files it reaches. It has its own `$root`, layout, `rundir/` and database. |
| Project file | A YAML file carrying all three of `projectName`, `dirs` and `fileGeneration`. `pysrc/processYaml.py::projectCreate._isChildProjectFile` is the classifier. |
| Child project | A project file reached through a `projectFiles:` entry. Reached any other way, it is an error (§11). |
| Provider | The physical project file selected to supply one `projectName` in a build. |
| Owning project | The project that generates a file. Every parsed context has exactly one, persisted as `CONTEXTOWNINGPROJECT`. |
| Assembler | A project whose blocks instantiate a block owned by another project. It owns the registrar trampolines and the Config modules it declares for that child. |
| Definitions-only project | A project that declares no instances. It omits `topInstance` and generates packages, includes and firmware headers for its files. |
| Standalone harness | A child project's own `topInstance` and everything below it. It is parsed into a parent's database but is not part of the parent's build. |

## 2. The author's contract

Composition takes two statements in two files.

- The parent's project file lists the child's project file in `projectFiles:`. This opens the
  child for discovery and ownership. `projectFiles:` contributes nothing to name resolution.
- A parent design file lists the child's design file in `include:`. This makes the child's
  names visible. Include scope is two levels deep: a file sees itself, its includes, and their
  includes.
- Instance rows carry no project qualification. `instanceType: ip` resolves through the
  instance file's include scope like any other block.
- A project file named in `include:` stops `make db`. A project file provides nothing to
  include scope.

`examples/ip_test/prj/yaml/ip_testProject.yaml` lists the `common`, `ip` and `ipBridge` project
files plus its own `top/yaml/ip_top.yaml`, and `ip_top.yaml` includes the child design files
whose names it uses.

## 3. Provider selection

A build has one provider per `projectName`. Path identity is the whole lexical path relative to
the root project file's directory. Nothing dereferences symlinks, matches basenames, or compares
directory prefixes, so a symlinked copy of a project is a second, distinct path.

- **Duplicate provider.** Two distinct paths that open the same `projectName` stop `make db`
  unless an ancestor's `projectOverrides:` selects one.
- **Override form.** `projectOverrides: { <projectName>: <path to a project file> }`. The path
  is relative to the declaring project file and normalised lexically. The override chooses a
  file for a name. It does not change design content.
- **Highest ancestor wins.** An ancestor's entry is never displaced by a descendant's. A child's
  override applies when no shallower project overrides that name. Every nesting level must build
  standalone and composed, so each level declares the overrides its own standalone build needs.
- **Same-depth conflict.** Two declarers at the same depth that select different files for one
  name stop `make db`. Neither dominates, so no master can be chosen.
- **Target validation.** The target must exist, be a project file, and declare the requested
  `projectName`. It need not be reachable by any `projectFiles:` edge; the scan reads it anyway.
- **Member-level aliasing.** Every file reached through a non-selected copy is aliased onto the
  same relative file in the selected master copy, and only master files are parsed.
- **Divergence.** When non-master copies of one file differ from each other, `make db` warns.
  The comparison ignores comments, layout and key order. A copy that differs only from the
  master draws no warning, because development happens in the master. A master with no file
  matching a copy's file draws a warning and leaves those copies unaliased.

The vendored-symlink pattern is in `examples/ip_test/bridge`. `bridge/ip` and `bridge/common`
are symlinks to the real `ip` and `common`. Standalone, `ipBridgeProject.yaml` overrides both
names onto the real-tree paths, so its `projectFiles:` path through the symlink and its
`include:` path through the real tree resolve to one provider. Composed, the root's overrides
win.

Implementation: `pysrc/projectScan.py::ProjectScanner._foldEffective` and `_selectMasters`;
`pysrc/processYaml.py::projectCreate._mergeOverrides`, `_selectProvider` and `readRaw`.

## 4. Ownership and generation

`pysrc/projectScan.py::ProjectScanner` runs before the parse and walks the whole
`projectFiles:` and `include:` closure, including every copy's own closure. It assigns each file
one owner. `projectCreate._deriveOwnershipFromScan` copies the result into
`contextOwningProject`. A parsed design context missing from the scan result stops `make db`;
nothing defaults to the root.

Ownership rules, applied in order:

1. The root project owns its own closure. A reference to a child project file is a boundary;
   the walk records it and does not cross it.
2. A file listed directly in a project's `projectFiles:` belongs to that project. Two projects
   listing the same file directly is an error.
3. Any other file reached by several providers belongs to the provider with the longest path
   from the root over the provider graph. A dependee therefore ranks below the project that
   depends on it, even when the root also lists the dependee.
4. An edge to a copy of a project also ranks that project's override-selected master. A
   provider reached only by an override ranks below every provider reached by a reference.
5. A tie at the greatest depth is an error naming the file and the tied providers. Listing the
   file directly in the owner's `projectFiles:` resolves it (rule 2).
6. A cycle of `projectFiles:` or `include:` references between providers is an error.

Directory location plays no part. Implementation:
`pysrc/projectScan.py::ProjectScanner._assignOwnership`. Fixtures: `unittest/fixtures/scan-ownership-tie`
and the cells in `unittest/test_project_scan.py`.

The parent parses everything and generates only what it owns. Three gates enforce this.

| Gate | Code | Effect |
| :--- | :--- | :--- |
| Generation | `pysrc/systemcGen.py`, `pysrc/systemVerilogGenerator.py`, both via `projectOpen.resolveFileOwner` | A file whose owner is another project is skipped. |
| Scaffolding | `pysrc/newModule.py` | Each write site checks the row's owner against `PROJECTNAME`. |
| Build manifest | `config/createBuildManifest.py::record` | Regeneration lists (`scGenFiles`, `svGenFiles`, `pyGenFiles`) are owned-only. Module, compile and directory sets include foreign files. |

`PROJECTLAYOUT` holds one layout per owning project, resolved against that project's own
`dirs.root`, so a child-owned file is placed by the child's layout under the child's tree. A
parent build therefore writes only its own tree, and every file a child owns is byte-identical
whether the child is built standalone or composed.

`resolveFileOwner` reads the `GENERATED_CODE_PARAM` line. `--project=<name>` names the owner
directly and is checked first, because a child's standalone stamp spells its `--context` relative
to the child's root, which a parent cannot resolve. Per-project artefacts such as `rtl.f` and
migrated context files carry `--project`.

## 5. Identity across projects

| Identity | Spelling | Source |
| :--- | :--- | :--- |
| C++ context module and namespace | `<owner>_<includeName>`, namespace plus `_ns` | `deriveModuleIdentities` |
| C++ block module | `<owner>_<block>` | `deriveModuleIdentities` |
| Config struct and module | `<declaringProject>_<block>[<Variant>]Config`, module `<declaringProject>.<block>.config` | `calcConfigModules` |
| SV package and module | The owning project's file stem: `svFilePrefix` plus the local name | `deriveModuleIdentities`, `artifactPaths.fileStem` |
| Address group | Tuple `(owner, group)`, shown as `owner::group` | `calcAddresses`, `generateAddressEnums` |

- `qualifyModuleIdentity` leaves a name unchanged when it already equals the project name or
  starts with `<project>_`. `sanitizeIdentifierToken` maps `-` and `.` to `_`.
- The owner is the intrinsic owning project, so a child spells every identity the same way
  standalone and composed.
- SV names are not project-qualified. Verilator keeps modules and packages in one namespace, so
  two projects that emit the same SV stem collide. A distinct `svFilePrefix` or `includeName`
  separates them.
- `make db` rejects any shared emitted name: context module identities, block C++ module names,
  Config stems and Config module names, and all SV modules, wrappers, variant tops and packages
  together (`rejectSharedName`, `validateSvDesignUnitNames`). It also rejects SV names that are
  not legal identifiers or are keywords.
- Each `(declaringProject, block)` pair gets one Config module. A project other than the block's
  owner that declares variants of it gets its own module and its own foreign Verilated tops
  (`calcForeignConfigHeaders`).
- The instance factory key is `Key{blockType, variant, projectName}`
  (`common/systemc/instanceFactory.h`). For a child that declares its own `params:`, the
  assembler's trampoline registers it under a pair domain
  `<owner>.<parentModule>.<childModule>`; any other child self-registers under its owner.
  Two assemblers instancing one variant therefore never share a key.
- Routers join an instance to a group only when the instance's own `(owner, group)` matches the
  router's, so two projects may each name a group `top`.

## 6. Shared definitions

Two definitions are the same only when they are one row reached through `include:`. A matching
name in another project is a different definition. The framework supports two shapes and infers
neither.

- **Shared by reference.** One project owns the definitions, usually a definitions-only project
  such as `common`, and every consumer includes its files. There is one C++ module and one SV
  package; binds are direct. `examples/ip_test/common` and `examples/simple_ip/common` are this
  shape.
- **Project-local copies.** Each project declares its own copy under its own owner-qualified
  identity. In SystemC the copies are distinct types, and a cross-project bind gets a generated
  port thunker that repacks the payload. In RTL, packed payloads with the same layout connect
  directly as signals. `validatePorts` checks protocol and packed layout at each connected
  boundary; semantic drift between layout-identical copies is not detected. Fixture:
  `unittest/fixtures/param-cross-project`, compositions `adaptedProject.yaml` and
  `collisionProject.yaml`.

Moving from copies to a shared project is an authoring change: create the shared project,
repoint each consumer's `include:` at it, and delete the local copy. During the mix, local and
shared identities coexist and the thunkers stay until the last consumer moves.
`projectOverrides:` addresses a different problem, several physical copies of one shared project.

## 7. Parameterized boundaries

`specs/spec-parameter-inheritance.md` holds the parameter rules. For composition:

- **Shared declaration.** Projects that include one `ipParameters` declaration share one
  parameter identity, and a parameterized connection crosses the boundary directly
  (`examples/xprojParam/shared`, `cstShared`).
- **De-parameterized boundary.** The assembler declares literal-width boundary types and each
  leg is adapted by a thunker (`examples/xprojParam/uniq`; the `boundaryProject.yaml`
  composition of `unittest/fixtures/param-cross-project`).
- **`containerParam:` across projects.** A cross-project child takes a declared variant whose
  bindings are `containerParam:` (`examples/xprojParam/dpTop`).
- **Independent same-named declarations** in different projects are different parameters.
  Their interfaces meet through an adapter, and the composition is rejected when the packed
  widths at the bound values disagree. Two visible declarations of one name in one scope are
  rejected.
- **`inheritContainerParam:`** is same-project only and is rejected across a project boundary.
- **Known limits.** A block's Config context is one file (`blocks.configContext`), so a Config
  drawn from parameter declarations in two projects is not supported. An assembler's generated
  module opens every sub-project namespace with `using namespace` and names thunker payload
  types unqualified, so stage projects that export the same payload identifier fail to compile
  (`examples/xprojParam/deparam`, which passes `make db` and `make gen`). Distinct identifiers,
  as in `uniq`, avoid it.

## 8. Active-top reachability

Only the root project's `topInstance` counts. `projectCreate.reachableInstanceKeys` walks
containment from the `_topInstance` rows and persists `REACHABLEINSTANCES`. A child's
standalone harness, its `cpu` and its testbench connections are in the database but outside
this set.

| Consumer | Gate |
| :--- | :--- |
| Router decode tree and primary router | `config/postParseRegisterPorts.py` resolves routers over reachable instances only |
| Router view | `getBlockData` routes reachable instances only |
| Base address defines | `templates/systemc/includes.py` skips unreachable instances |
| Address space check | unreachable instances without `addressGroup` are skipped in `calcAddresses` |
| `svModuleFiles` | `createBuildManifest` compiles reachable blocks only |
| `rtl.f` packages and `+incdir+` | `COMPILECONTEXTS` |
| Registrar pairs, and the assembler directory that hosts each Config module | reachable instances only |

`calcAddresses` computes offsets for every block in the database. Reachability decides what is
placed, not what is computed.

`COMPILECONTEXTS` (`calcCompileContexts`) is the compile closure: the top context's include
chain, then the context of every reachable block, closed under include scope. It orders `rtl.f`.
A definitions-only project has no `TOPCONTEXT` and emits no `rtl.f`.

## 9. Firmware composition

- Generated firmware headers sit in the `fwInc` segment, whose build group is `sc`. The manifest
  lists every compile directory, foreign ones included, so a parent's firmware sees a child's
  `<includeName>IncludesFW.h` and the base address defines on the `-I` path.
- `fw/src` is user code, listed by `EXTRA_PRJ_SRC_DIRS` in the rundir `Makefile`.
- The `cpu` block in `examples/ip_test/common/cpu/yaml/cpu.yaml` is a generic APB master owned by
  `common`. It runs firmware through the BSP `regRead32`/`regWrite32` seam.
- The BSP in `common/fw/bsp` is not in the default source set. A project opts in with
  `EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp`, as every `ip_test` and `simple_ip` rundir does.

## 10. Build and migration order

- **Generate children first.** A parent compiles child files it does not regenerate, so they
  must exist. `examples/ip_test/Makefile` makes `gen` depend on each child's `gen` and chains
  `clean` the same way.
- **Regenerate owned, compile all.** The parent's manifest lists only owned files as regeneration
  targets, and lists owned and foreign files in its module, source and SV compile sets.
- **Migrate bottom-up.** `make migrate` acts on one project.
  `pysrc/migrateSubProjects.py::checkSubProjects` reports each direct child without the current
  `yamlFormat:` as `TODO_UNMIGRATED_SUBPROJECT` and blocks the parent's stamp. Run each child's
  `make migrate` from its own `rundir/` first: in `ip_test`, `common`, then `ip` and `ipBridge`,
  then `ip_test`.
- **Re-run stamped children.** After a builder update, run every child's `make migrate` again even
  when it is already stamped. Otherwise the parent imports module names the child's stale files
  no longer export.
- **Source composition.** Composed projects link object files. Generated non-templated blocks
  self-register through a retained static initializer, which a static archive drops unless it is
  linked with `-Wl,--whole-archive` (`common/systemc/instanceFactory.h`).

## 11. Diagnostics

| Condition | Where | Message names |
| :--- | :--- | :--- |
| Two paths provide one `projectName` | `readRaw` | both paths; says to add `projectOverrides` in an ancestor |
| Same-depth override conflict | `ProjectScanner._foldEffective` | both declarers, both targets, the depth |
| Override target missing, not a project file, or wrong `projectName` | `ProjectScanner._selectMasters` | declarer, target, name |
| Project file reached through `include:` | `readRaw` | the file and its `projectName` |
| File listed directly by two projects | `ProjectScanner._assignOwnership` | the file and both projects |
| Ownership tie | `ProjectScanner._assignOwnership` | the file and the tied providers |
| Reference cycle | `ProjectScanner._assignOwnership` | the cycle |
| Context absent from the ownership scan | `_deriveOwnershipFromScan` | the context |
| Unresolved block, type or interface | scope lookup during parse | the file, section, field and value, and a declaring file when one is loaded |
| Shared module, package or Config identity | `rejectSharedName` | the name and both owners |
| Instances without `topInstance` | `projectCreate` | the project |

## 12. Reference fixtures

| Path | Shows |
| :--- | :--- |
| `examples/ip_test` | Root `ip_test` with children `common` (definitions-only, owns `cpu`), `ip`, `ipBridge`; vendored symlinks and nested overrides in `bridge/`; owned-only gen with child-first ordering |
| `examples/simple_ip` | A small composition over `common` and `ip` without overrides |
| `examples/xprojParam` | Parameterized interfaces across projects: shared declaration, de-parameterized boundary, `containerParam:` chains |
| `unittest/fixtures/multi-copy` | Several physical copies of one shared project reconciled onto one master |
| `unittest/fixtures/cross-branch-override` | A master named only by an override in a sibling branch |
| `unittest/fixtures/conflict-override` | Same-depth override conflict |
| `unittest/fixtures/scan-ownership-tie` | Ownership tie and its resolution by direct listing |
| `unittest/fixtures/param-cross-project` | Shared, de-parameterized, adapted and colliding cross-project interfaces |

Tests: `unittest/test_project_scan.py`, `test_provider_override.py`, `test_nested_ownership.py`,
`test_param_cross_project_linkage.py`.
