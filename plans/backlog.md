# Backlog

Known defects and feature requests that are not scheduled. Each entry says what is wrong, where, and where it came from. Remove an entry when it lands, and name the change that fixed it.

## Defects

### K1. SV package order is computed twice

- `pysrc/rtldotf.py` and `config/createBuildManifest.py` each derive the SV package order. The two lists can drift apart.
- Fix: compute one ordered list in `projectCreate` and have both consume it.
- Source: issue A43c, found on branch 155.

### K2. Lint and verilate recipes can exceed the shell argument limit

- The lint and verilate recipes pass the whole file list on one `sh -c` command line. A large design can pass 128 KiB and fail with "Argument list too long".
- Possible fix: write the list to a `.f` file and pass that.
- Source: issue A43d. This predates branch 155.

### K3. Derived and numbered names are not checked for collisions

- `make db` rejects a name used twice in one block (A28). It does not check names the generator derives: `<mem>_reg`, `u<Mem>`, `<mem>Mem`, `u<block>Regs`, or numbered channel names such as `o_0`.
- A user name that equals one of these still fails late, in the generator or the compiler.
- Source: issue A28b, found on branch 155.

### K4. Channel names are computed in more than one place

- `projectCreate` checks channel names in `clockTree.py`, and the generator computes them again in `getBDConnectionsFinal`. The two must agree by hand.
- Fix: compute each channel name once in `projectCreate`, store it in the connection row, and read it in both places.
- Source: issue A28c, found on branch 155.

### K5. `make compdb` and `make newmodule` rebuild the db for real

- Both run a `make -n -B compdb-capture` step to capture compile commands. The db rule still runs during that step, so a dry run rebuilds the db.
- Source: found on branch 155. This predates it.

### K6. `registerFeatures` does not support arrays

- `registerFeatures` in `templates/systemc/structures.py` does not handle a register struct with an array field.
- Source: found on branch 155.

### K7. Config-path unpack loses bits on word-crossing fields

- On the parameterised (`Config`) path, unpack drops bits of a field that crosses a word boundary. Seen in `mixSt_v<8>`.
- Source: found on branch 155 during the 64-bit width fix.

### K8. Dead `useConfig` branch in `fitsDirect`

- `templates/systemc/structures.py:1384`: the `useConfig` branch is never reached. Remove it, or add the case that reaches it.
- Source: found on branch 155.

### K9. `cpLayout` and `inhLayout` rundir Makefiles set `REPO_ROOT` wrongly

- Their `REPO_ROOT` lacks the suffix the other example rundirs use, so `make` from the rundir leaves `A2C_ROOT` empty. Today they can only be regenerated from the project root.
- Source: introduced by commit `ab3dc659` (#125). Found on branch 155.

### K10. `clockgen-link-loss` fixture has no `A2C_ROOT`

- `unittest/fixtures/clockgen-link-loss/include/make/shared.mk` uses `A2C_ROOT` (`:5-6`) and does not set it. It is not yet known whether the test harness supplies it.
- Source: found on branch 155.

### K11. Stale tracked outputs in two fixtures

- `unittest/fixtures/inherit-vl-child` and `unittest/fixtures/variant-two-integrators/ipLeaf` keep generated files that no longer match the generator.
- Source: found on branch 155.

### K12. `examples/inAndOut` has no `gen` target

- The example cannot be regenerated with `make gen`, so template changes do not reach it.
- Source: found on branch 155.

### K13. `make lint` re-runs db and gen, and block RTL directories have no lint target

- `make lint` depends on db and gen, so linting runs the generator first.
- A block's RTL directory has no lint target of its own.
- Source: issue A43, found on branch 155.

### K14. `nonByteAlignedSignedSt` descriptions contradict the packing

- In `examples/mixed`, the field descriptions of `nonByteAlignedSignedSt` give bit positions that disagree with the MSB-first packing.
- Source: found on branch 155.

### K15. A width can resolve to 0 for one variant

- A parameter binding can resolve a width to 0 for one variant, and `projectCreate` does not catch it. A check needs a marker saying which parameters are widths, and none exists. The `widthLog2` types accept 0 on purpose.
- Decision (branch 155, D10): leave it until a real design hits it.

### K18. Two example runs fail, cause not yet confirmed

- `examples/ip_test` regression: `bridge_driver` fails at elaboration with `Unknown instance ip_top.uBridgeDriver`. That instance is declared only in the bridge project (`bridge/yaml/bridgeStdTop.yaml:60`), but `rundir/regr_ip_test.json:36` uses it under `ip_top`.
- `examples/simple_ip/ip` `run-vl`: `Attempted to create an instance ip of an unregistered block type ip_verif`.
- The `simple_ip` failure has a known cause: `examples/simple_ip/ip/rundir/Makefile` invokes `run-vl-dut` without `VL_DUT=1`, so the aggregate `run-vl` rebuilds a non-verilated binary; the same tree passes with the flag supplied. The makefile is a project-owned scaffold-once file. The `ip_test` failure is not yet checked against a tree from before branch 155.
- Source: found on branch 155 while checking the D2 decoder change.

### K19. The external register interface still has a 2-bit `write`

- After D1b, an `ext` register is one 32-bit word, but `interfaces/external_reg/external_reg_if.yaml` (`write: _extRegWriteT`, a type of `width: 2`, `:2-4`, `:14`), `external_reg_if.sv` and `external_reg_hdl_if` (`sc_bv<2>`) still size `write` for two words. The `ext` write arm in `moduleRegs.py` can now only drive bit 0.
- Narrowing `write` to 1 bit is an interface change, so it waits for a decision.
- Source: found on branch 155 during D1b.

### K20. The register bus `data_t` width is not checked

- Register decode works in 32-bit words: `moduleRegs.py` slices `pwdata[31:0]`, and `regBase::cpu_write` takes `uint32_t`. `interfaces/apb/apb_if.yaml` leaves `data_t` as a free struct parameter, and `projectCreate` does not check that an `addressBus` interface binds it to 32 bits.
- A narrower `data_t` gives an out-of-range `pwdata` part-select in the generated RTL for any register wider than it.
- Fix: reject at `make db` an `addressBus` interface whose `data_t` is not 32 bits.
- Source: found on branch 155 during the D1b review.

### K23. A fatal error count can collide with migrate exit codes

- Fatal checks stop with `exit(warningAndErrorReport())` (for example `pysrc/processYaml.py:506`, `pysrc/artifactPaths.py:49`, `pysrc/genFileParam.py:56`), so the exit status is the error count. Under `migrateYaml.py`, a count of 1, 2 or 3 reads as `RC_TODO`, `RC_BLOCKED` or `RC_PHASE_FAILED`.
- Today the same checks also run in `newmodule`, `gen` or the final read-only sweep, so `make migrate` still fails. A check that ran only in a writing sweep would be misread.
- Possible fix: catch `SystemExit` with a non-zero code at the `migrateYaml.py` boundary and map it to one fixed code.
- Source: found on branch 155 during the migrate exit-status review.

### K24. Orphan sweep coverage gaps that predate D6b

- `vlWrapDirs` count as covering `.cpp` units in `_reportUnmanifestedSrcDirs` (`pysrc/migrateOrphans.py`). The model build feeds `A2C_VL_WRAP_DIRS` only to `-I` and the compile-database probe (`a2c-systemc.mk:160`, `:363`), so a hand-written `.cpp` in such a directory is not compiled and not reported. The case needs a contrived tree, such as a link `tb/wrap -> ../verif/vl_wrap`.
- `_CPP_UNIT_EXTS` leaves out `.h`, while the retired `find -L` scan also matched `*.h`. A header-only directory that dropped off the include path at the manifest switch is not reported. This scope was chosen earlier on purpose.
- Source: found on branch 155 during the D6b review.

### K25. `$(REPO_ROOT)//path` refs are not resolved as make resolves them

- The `extraVarRefs` regex (`pysrc/migrateCommon.py:354`) turns `EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)//fw/src` into the ref `/fw/src`. `os.path.join(rootDir, "/fw/src")` then discards the root, so the orphan sweep never sees the directory as wired, while make compiles it. `migrateLayout.py:818` shares the regex.
- Possible fix: `\$\(REPO_ROOT\)/+(?P<path>...)`, with a fixture that fails first.
- Source: found on branch 155 during the D6b review. This predates it.

### K26. `external_reg_dst_bfm` readback lags behind queued writes

- After the branch 155 queue fix, the BFM drives one queued command per two clocks and updates its mirror only after each one. A firmware read issued right after N back-to-back writes can return a value up to 2N clocks old. The generated RTL strobes `ext.write` within the APB write itself, so it has no lag.
- Closing the gap needs backpressure in the `external_reg` channel, which the fix kept unchanged.
- Source: found on branch 155 during the BFM queue review.

### K27. `hwRegisterIf` keeps pre-reset words after an RTL reset

- `hwRegisterIf::cpu_write` (`common/systemc/hwRegister.h`) merges the written word into its own `m_val` and sends the whole value. After a mid-run RTL reset, a low-word write to a wide rw register sends the high word firmware last wrote before the reset. The RTL child holds its reset value in that word.
- Source: found on branch 155 during the D1b review. This predates it.

### K28. `make lint` cannot run in place in `simple_ip` and `ip_test`

- Their rtl Makefiles, and those of the `ip`, `common` and `bridge` sub-projects, set `REPO_ROOT = $(shell git rev-parse --show-toplevel)`. Inside builder/base that is the builder root, so `include/make/shared.mk` is not found, `A2C_ROOT` stays empty, and make stops with `No rule to make target '/include/make/a2c-rtl.mk'`. `apbDecode` appends its own path to `REPO_ROOT` and works.
- The Makefiles were last changed in `e59ad943` (#116), so this predates branch 155. It is related to K9.
- Source: found on branch 155 during the final verification run.
- Same cause in more places, also before branch 155. These Makefiles have the same bare `REPO_ROOT` line, so `make clean` and `make run` stop on `/include/make/a2c-systemc.mk`:
  - the rundir Makefiles of `xprojParam/cpLayout` and `xprojParam/inhLayout`, added in `d06e20ff` (#125);
  - the rtl Makefiles of helloWorld, nested, xif, axiSocketMaster, axiSocketSlave and several `xprojParam` sub-projects.
- With `REPO_ROOT` corrected, lint in many of those rtl directories then stops in `a2c-rtl.mk:56`, "HDL_TOP_MODULE '<x>' has no Verilator wrapper in the build manifest", because the lint top has no `hasVl` wrapper. Lint at the `ip_test` top also cannot find `ip_top_package.sv`, because `top/rtl/rtl.f` lists it by a relative path. Decide per project whether lint is meant to run there.

### K29. `examples/mixed` read test depends on an earlier test, and may read uninitialised memory

- Run alone under the D4c prototype, `test_mem_hier_cpu_read` fails, because it reads what blockD's write test stored. The value read changed between runs, which suggests the model memory returns uninitialised data. Not yet confirmed.
- Source: found on branch 155 during the D4c prototype.

### K31. Unaligned register access differs between model and RTL

- `addressMap::contains` (`common/systemc/addressMap.h:104`) matches per byte, while the RTL arms match exact words. A read at REG+1 returns register bits in the model and `32'hBADD_C0DE` in the RTL. They also disagreed before branch 155 (RTL returned 0). APB masters normally align.
- Source: found on branch 155 during the D2b scope review.

### K32. A Config that sets its test list in its constructor ignores `--test`

- `common/scmain/main.cpp:115` builds the testbench, which runs the Config constructor, before `select_tests` at `:165`. A Config that calls `set_test_names` from its constructor therefore gets the full list, and `--test` has no effect, with no message. No in-tree Config does this. They all set the list later.
- Possible fix: `select_tests` re-filters a list that is already set, or `set_test_names` rejects a call before selection.
- Source: found on branch 155 during the D4c review (earlier `--test` pass).

### K33. `ADD_TEST` is a global macro

- `common/systemc/testController.h` defines `ADD_TEST` in every translation unit that includes it. A user project with its own `ADD_TEST` macro or identifier gets a redefinition. No in-tree code is affected.
- Source: found on branch 155 during the D4c review. The user chose the macro form in D4c.

### K36. A router with no upstream feed crashes the decoder templates

- A router block with no authored register-bus connection or boundary connectionMap into it passes `make db`. Then `templates/systemVerilog/apbDecodeModule.py` and `templates/systemc/constructor.py` both raise UnboundLocalError, because each scans connection rows for the parent port. The view's `addressDecode['registerBusPort']` cannot replace that scan, because for a router it holds the interface name (`apbReg`), not the port name (`cpu_main` in examples/mixed).
- Only an authoring mistake reaches this, for example running `make gen` before wiring the CPU.
- A fix was drafted on branch 155 and not landed. It had three parts:
  - a `make db` rejection of a reachable router that has neither a register-bus connection into it nor a boundary connectionMap feeding it. It must run after `validatePorts` and the block-scope name check. If it runs at the end of `postParseRegisterPorts.postProcess`, it takes over the messages of five existing error tests: block-scope name collision, addrgroup vartype collision, nested decoder overflow, register interface type mismatch and register packed form;
  - a view field for the router's real feed port;
  - both templates read that field.
- Cost: about 18 `test_addrctl_*` fixtures and 8 other success-path fixtures and controls author feedless routers, and each needs a feed. A shared CPU block in `unittest/_addrctl_helpers.py` keeps that change mechanical.
- Source: found on branch 155 in the D2 router review. Deferred from branch 155 by user decision on 2026-10-05.

### K38. Integer `alignment:` has no lower bound

- `calcAddresses` (`pysrc/processYaml.py` ~:5845, :5876, :5905) accepts any integer `alignment:` for registers and memories, and nothing validates the value. `rules/skills/manage-address-space.md:87-99` documents only `alignment: memsize` for memories.
- An integer below the row footprint places a memory off its row boundary. Branch 155 (K35) made the RTL handle that, so model and RTL agree.
- A value that is not a multiple of the 4-byte bus word looks broken. For example, `registers: { alignment: 1 }` with a 24-bit register gives a 3-byte object, so the next object can start at a non-word address that no word-addressed access reaches cleanly. This comes from reading the code. No fixture shows it yet.
- Possible fix: reject an `alignment:` that is not a multiple of 4 at `make db`, and document integer alignment for memories in the skill. Needs a decision on whether packed memory layouts stay supported.
- Source: found on branch 155 during the K35 review.

### K39. A parameterizable `ext` register produces RTL that does not compile

- `section_03b_regs` in `templates/systemVerilog/moduleRegs.py` takes the parameterizable branch for any parameterizable register. `section_01_regs` declares `<reg>_rword` only for `rw` and `ro`. An `ext` register with a parameterizable structure therefore reads an undeclared `<reg>_rword` and has no write arm.
- Failing input: a leaf with `DW: {value: 16, maxValue: 24}`, a type `dataT` with `maxBitwidth: 24`, and `{register: cfg, block: leafA, regType: ext, structure: wideRegSt}`. `make db` and `make gen` accept it. `verilator --lint-only` of `leafA_regs.sv` fails at DW 8, 16 and 24 with `Can't find definition of variable: 'cfg_rword'`. HEAD 079ab77e behaves the same.
- Possible fix: decide what a parameterizable `ext` register means, since its storage lives outside the handler. Then either emit the external read/write path for it or reject it at `make db`.
- Source: found on branch 155 during the K30/K34 review. It predates that pass.

### K40. A stale site marker is trusted under a parent make that is not arch2code

- `include/make/a2c-common.mk:68-77` treats `MAKELEVEL > 0` as meaning "my parent is an arch2code make that exported `A2C_SITE_EXTRA_LD_FLAGS`". When a make that does not include `a2c-common.mk` runs the project make (for example, the base `Makefile` running `pipeline-test`, a user's wrapper Makefile, or a CI make), a marker that leaked into the shell is trusted. It replaces the current `EXTRA_LD_FLAGS` without any message.
- Scenario: the shell holds `A2C_SITE_EXTRA_LD_FLAGS=-L/old/lib` and `EXTRA_LD_FLAGS=-L/new/lib`. `make -C builder/base pipeline-test` then links each example against `/old/lib`. This is unlikely, because the marker reaches a shell only by escaping a recipe's environment, for example a shell started from a recipe or a sourced environment dump.
- The comment at `:72` ("so a marker left in the user's shell is ignored") holds only when the arch2code make is the outermost make.
- Possible fix: a stronger handshake, for example a marker tied to the exporting make, or at least a corrected comment. Needs a decision.
- Source: found on branch 155 while reviewing the `test_make_site_env.py` harness fix. The test failed under `make unittest` because it inherited `MAKELEVEL`. The harness now drops `MAKELEVEL`, `MAKEFLAGS`, `MFLAGS` and `MAKEOVERRIDES`.

### K41. A type under `ipParameters:` in a file with no regular `types:`, `enums:`, `constants:` or `structures:` has no model declaration

- `includeValid` turns true only for a section in `includeSections`, which holds `types`, `structures` and `constants` (`pysrc/processYaml.py:4092`, `:8295-8296`). An `enums:` section also counts, because it maps to `types` (`config/schema.yaml:110-111`, `processYaml.py:8270`). `_process_ipParameters` (`:10023`) never sets it. A file with none of those sections therefore gets no `_package.sv` and no `Includes.cppm` (`contextFileEmitted`, `:7221-7223`), even when it also declares `blocks:` or `interfaces:`.
- A type declared under `ipParameters:` in such a file loses its model declaration. The `_v` template is emitted only into the declaring context's `Includes.cppm` (`getContextData`, `:1239-1240`; `templates/systemc/includes.py:140-160`). The RTL declares it module-local in each block that binds its parameter (`blockParameterizedDecls`), so the SV side is unaffected. A probe (scratchpad `g1r5/probe.py`) runs `projectCreate` on a copy of `examples/xprojParam/cstShared` whose defs file declares `cshPixelT` under `ipParameters: types:`. The defs context reports `valid= False`, neither file is emitted, `blockParameterizedDecls` still lists `cshPixelT` for `xpCstSharedSrc` and `xpCstSharedChk`, and `projectCreate` raises no error. The model compile failure is inferred, not observed.
- A file whose `ipParameters:` holds only constants works, as `examples/xprojParam/dpMid` shows.
- Option A, adding `ipParameters` to `includeSections`, was tried on 2026-10-06 and reverted. The package and `Includes.cppm` it emitted were empty. `test_variant_binding_resolution.py` then failed with "'arch_package' is used by two distinct design units". In `examples/xprojParam`, dpMid and dpTop imported context files that do not exist, so each needed new files.
- Today `importPackages` (`pysrc/systemVerilogGeneratorHelper.py:22`) imports nothing for such a context, and `unittest/test_ipparam_only_context.py` checks that the design generates, lints and runs.
- Possible fix: needs a decision on what such a context's package would contain, since option A's files were empty.
- Source: found on branch 155 while testing an out-of-tree project. Left open by user decision on 2026-10-06.

### K42. The address-control converter drops the base postProcess scripts from a kept override

- `postProcess` merges with `list_override` (`pysrc/processYaml.py:4113`). A project `postProcess:` list replaces the base list at `config/project.yaml:195-199`. It does not extend it.
- `_rewritePostProcess` (`pysrc/migrateAddressControl.py:539-614`) strips every entry whose basename matches a base script (`:592`) and keeps the rest. When a project-specific entry survives, the written list holds neither `postParseRegisterPorts.py` nor `postParseChecks.py`. Register-port distribution and the post-parse checks then stop running for that project. When nothing survives, the converter deletes the override and the base list applies, so only the kept case breaks.
- `unittest/test_migrate_address_control.py:263-269` asserts the broken result: `postParseChecks.py` must be gone and `customPass.py` must remain. `:446` asserts that the written list is exactly `["$proj/config/customPass.py"]`.
- Failing input: the dirty fixture in that test. After conversion, `project.yaml` holds `postProcess:` with the single entry `$proj/config/customPass.py`.
- Possible fix: needs a decision between (a) the converter writing the base scripts ahead of the project's entries, with the test asserting that, and (b) switching the merge to `list_append`. Under (b), an existing project that repeats the base scripts in its override would run them twice.
- Source: found on branch 155 during the skill review (2026-10-06).

### K43. Rerunning the address-control converter duplicates the policy sections

- `migrateAddressControlInProject` calls `_appendPolicySections` (`pysrc/migrateAddressControl.py:315-316`, defined at `:617`) whenever the legacy file has `InstanceGroups` or `AddressObjects` rows. It appends without checking whether `project.yaml` already has `instanceGroups:` or `addressObjects:`.
- The legacy file and its pointer survive a run while a router is unresolved. The converter is meant to be rerun after the router is authored by hand, and each rerun appends another copy of both sections.
- Failing input: the `_DIRTY_PROJECT`, `_DIRTY_TOP` and `_DIRTY_ADDR` fixtures from `unittest/test_migrate_address_control.py`, with `decoderInstance: uApbDec` removed from the `top` AddressGroups row so the router stays unresolved. Run 1 writes one `instanceGroups:` and one `addressObjects:`. Run 2, after an `addressBlock:` is added to `apbDecode` by hand, writes a second copy of each. Run 3, after the `addressControl:` pointer is removed by hand, reports clean and leaves both copies in place.
- Run 2 still reports `TODO_ROUTER_RESOLUTION` and keeps the pointer. The converter resolves a router only through the row's `decoderInstance` (`pysrc/migrateAddressControl.py:206-230`) and never sees a hand-authored `addressBlock:`. The `DELETE_DEFERRED` message (`:329-333`) promises removal once the router is authored, but for a row with no `decoderInstance` that never happens, so run 3 needs the pointer removed by hand.
- The result has duplicate top-level keys. `make db` loads `project.yaml` through `existsLoad` (`pysrc/processYaml.py:64-73`), and ruamel raises `DuplicateKeyError` on the second copy. Checked by loading a duplicate-key file through `existsLoad`; `make db` itself was not run.
- Possible fix: skip, or replace, a section that `project.yaml` already holds.
- Source: found on branch 155 during the skill review (2026-10-06).

### K44. `instanceGroups:` generates no ID enum, its `varType:` and `enumPrefix:` keys do nothing, and every instance gets ID 0

- Each `instanceGroups:` group declares a `varType` and an `enumPrefix`, the shape of an ID enumeration. The `instanceGroups:` section of `rules/skills/manage-address-space.md` says the `varType:` and `enumPrefix:` keys have no effect. `loadProjectAddressPolicy` (`pysrc/processYaml.py:7297`) loads the rows into `counterGroup['InstanceGroups']`. Their only reader is the `instGroup:` name check in `_auto_instanceGroup` (`:9463`). No template or generator reads them, so no enum type is emitted. Only `addressBlock:` groups get one, in `generateAddressEnums` (`:7182`).
- `_auto_instanceID` (`:9467-9478`) tests `self.counterGroup.get(section+'InstanceGroups')`, a key that nothing sets. It always takes the `default` branch, which resets that counter to 0 first, so every instance gets `instID` 0 and every block gets `blockID` 0. The same branch adds a `default` group that the project never declared.
- Evidence: `examples/apbDecode` declares `instanceGroups: top` and places six instances in it. `examples/apbDecode/apbDecode.db` holds `instID` 0 for all 8 instances and `blockID` 0 for all 8 blocks. `examples/ip_test/ip_test.db` shows the same for 23 instances and 17 blocks.
- `make db` accepts `varType:` and `enumPrefix:` on every group (`_PROJECT_ADDRESS_GROUP_FIELDS`, `pysrc/processYaml.py:7262`), and `arch2code.py --newproject` writes both into every new `project.yaml` (`pysrc/newProject.py:60-63`). Neither key changes any output.
- Needs a user decision. Document the section as having no generated output, generate the enum and fix the numbering, or retire the section. If the enum is not generated, decide whether to remove `varType:` and `enumPrefix:` from the accepted fields and from the `newProject.py` scaffold, or keep them.
- Source: found on branch 155 during the skill review (2026-10-06). `varType:`/`enumPrefix:` added from the history sweep (2026-10-07).

### K45. A `regType: memory` register raises a bare KeyError when `addressObjects:` has no `memories:` row

- `calcAddresses` loops over the rows that `addressObjects:` declares (`pysrc/processYaml.py:5823`). In the `registers` pass, it reads `self.addressObjects['memories']` for every `regType: memory` register (`:5852`, `:5854`, `:5909`, `:5911`). A project whose `addressObjects:` has a `registers:` row and no `memories:` row raises `KeyError: 'memories'` there, naming neither the register nor the file.
- `_validateProjectAddressRows` (`:7331`) rejects unknown fields. It does not require a `memories:` row.
- Plausible, not reproduced. These four reads are the only subscripts of `addressObjects['memories']` in the tree.
- Possible fix: a `make db` diagnostic that names the register and asks for an `addressObjects: memories:` row.
- Source: found on branch 155 during the skill review (2026-10-06).

### K46. Include visibility reaches two levels, apparently by accident

- `processYamls` builds each file's context at `pysrc/processYaml.py:8193-8200`. For each direct include `f`, it adds `f` and `yamlDependancies[f]`, and `yamlDependancies[f]` holds only `f`'s direct includes. `yamlContext[f]` was probably meant. It is already complete at that point, because `f` is processed first.
- A file therefore sees names from its includes and from their includes, and no further. A name three includes away fails with "add the defining file to the include: chain" (`:8769`).
- Evidence: in `examples/hierInclude`, `b/hierIncludeB.yaml` includes `hierInclude.yaml`, which includes `hierIncludeTop.yaml`, which includes `hierIncludeNestedTop.yaml`. `systemVerilog/b/hierIncludeB_package.sv:5-7` imports `hierInclude_package` and `hierIncludeTop_package`. It does not import `hierIncludeNestedTop_package`, which exists.
- Possible fix: needs a decision to keep two levels and document them, make visibility fully transitive, or limit it to direct includes. Either change alters the import lists in generated packages.
- Source: found on branch 155 during the skill review (2026-10-06).

### K47. A bare include filename resolves differently depending on read order

- `getFileList` (`pysrc/processYaml.py:5603-5607`) keeps a bare `include:` entry such as `shared_types.yaml` unresolved when `os.path.basename(f) == f and f in dep_set`. `dep_set` holds every include recorded so far. Otherwise it resolves the name against the including file's directory.
- Scenario: `sub/a.yaml` includes a bare `shared_types.yaml`. Read first, it resolves to `sub/shared_types.yaml`. Read after another file has recorded the root-level `shared_types.yaml`, it resolves to the root-level file. Read order follows declaration order, so reordering `projectFiles:` can change which file `sub/a.yaml` includes.
- `pysrc/projectScan.py:256-257` calls the same `getFileList` with the scanner's own dependency map, so the ownership scan repeats the rule. The comment at `:104-107` describes this.
- From reading the code. No fixture yet.
- Possible fix: needs a decision on whether a bare name may ever refer to a file outside the including file's directory.
- Source: found on branch 155 during the skill review (2026-10-06).

### K48. Pro `lockLocation` can grant one location to two requesters in the same cycle

- `builder/pro/common/systemVerilog/lockLocation.sv:62` compares `location[i]` with the registered `lock[j]`. A grant made earlier in the same pass writes `nLock[j]`, so a later requester for the same location does not see it.
- Scenario: from reset, `req=4'b0011`, `lockReq=4'b0011`, `location[0]=location[1]=5`. Requester 0 is granted and sets `nLock[0]=5`. Requester 1 compares 5 with `lock[0]`, which still holds its reset value, and is granted too.
- `memArb` is not exposed. It drives `req` from the one-hot grant of the `rrArb` read instance (`builder/pro/common/systemVerilog/memArb.sv:69-80`), at `:95-106`, so at most one bit is set per cycle.
- Read only, not simulated. Needs a failing fixture, such as a directed test of the scenario above, before a fix.
- Possible fix: compare with `nLock[j]`.
- Source: found on branch 155 during the skill review (2026-10-06).

### K49. Four Pro SystemVerilog modules do not compile

- All in `builder/pro/common/systemVerilog`:
  - `vldAckFifo.sv:39-40` and `rdyVldVldAckFifo.sv:40` use an interface `vld_ack_if` that no file in `builder/` defines.
  - `rdyVldBurstFifo.sv` is an unfinished stub. `:43` uses `rdyVldBurstIf`, also undefined. Lines 38-39 end with `;` inside the parameter list. Line 38 needs `,`, and line 39, the last parameter, needs none. `dataSt` and `hdrSt` at `:36-37` take a type but are declared without `type`. The file ends at the port list's `)` on `:45`, with no `;`, body or `endmodule`.
  - `dramMgr.sv:57` also uses `vld_ack_if`, and nothing instantiates it.
- No file in `builder/` instantiates any of the four, so no build or lint reaches them.
- Read only, not compiled.
- Possible fix: needs a decision to fix them, remove them, or leave them. `rdyVldBurstFifo` would have to be written, not repaired.
- Source: found on branch 155 during the skill review (2026-10-06).

### K50. Gate targets race under `make -j`

- `builder/base/Makefile:658`: `push-test: clean unittest pipeline-test` lists its steps as prerequisites. `make -j push-test` runs `clean`, the unit suite and the examples at once, and the unit suite regenerates examples in place. `builder/base/CLAUDE.md` says to run `push-test` without `-j`; nothing enforces it.
- `builder/Makefile:13-14` says "Recipe lines hold the order under -j", which invites `-j` on the workspace `push-test`. That holds for the three lines at `:16-18`. The last of them reaches `$(MAKE) -C $(PRO_REPO_ROOT) pipeline-test` (`:11`), and that sub-make inherits the jobserver.
- `builder/pro/Makefile:68`: `pipeline-test: unit-test lmmi-demo inh-tandem` then runs the pro unit tests next to the examples. The pro unit tests work in temporary directories, so the practical risk is low.
- Possible fix: sequence each gate with recipe lines, as `builder/Makefile:15-18` does.
- Source: found on branch 155 during the skill review (2026-10-06).

### K51. `make migrate --port-tb` and `--port` open the database outside `_runPhase`

- `migrateYaml.py:756` (`--port-tb`) and `:799` (`--port`) call `projectOpen(args.db)` directly. The sweep wraps the same call in `_runPhase` (`:633`) and returns `RC_BLOCKED` (2) when it fails (`:641-646`).
- An exception from `projectOpen` in these modes leaves `main()` as a bare traceback with no `TODO_PHASE_FAILED` item, and Python exits 1, the value of `RC_TODO`. `make migrate` treats exit 1 as pending hand work and carries on (`include/make/a2c-common.mk:216-218`, `:234-236`). After a failed `--port-tb` open it runs `make gen` on a `Config.cpp` that was never restructured, the abort that exit 2 exists to prevent (`:221-223`).
- Wrapping alone does not fix `--port`. That mode maps every caught phase failure to `RC_TODO` (`:810`), so a wrapped open still exits 1, and only the report improves.
- Plausible, not reproduced. `_runPhase` catches `Exception` only, so a fatal check that calls `exit()` inside `projectOpen` escapes it on every path. K23 covers that case.
- Possible fix: wrap both calls in `_runPhase`, and have `--port-tb` return `RC_BLOCKED` when the open fails, as the sweep does.
- Source: found on branch 155 during the skill review (2026-10-06).

### K52. regrLauncher raises KeyError for a missing required key

- regrLauncher reads required keys by subscript and never checks them. A missing key raises `KeyError` with a traceback, and the message names neither the key's path nor the JSON file:
  - `session.name`: `regrLauncher/__main__.py:55`, in `setup_session`.
  - a test's `labels`: `regrLauncher/queue.py:81` and `:101`, when filters are applied.
  - a test's `command`, `args`, `timeout` or `rules`: `regrLauncher/queue.py:41`, as each run is queued.
  - `session.lrp`: `regrLauncher/runner.py:175`, after each test finishes.
  - `build.command` and `build.timeout`, with `--build`: `regrLauncher/runner.py:107`.
- A `+` key with no parent value, such as `args+` where no ancestor sets `args`, fails the same way. `merge_parent_attributes` (`regrLauncher/__main__.py:23-31`) merges only when the parent has the key. Otherwise the key keeps its `+` suffix, and the lookup of `args` at `queue.py:41` fails.
- Reproduced with two session files. One without `session.name` stops with `KeyError: 'name'` at `__main__.py:55`. One whose test sets `args+` with no parent `args` stops with `KeyError: 'args'`, raised from the worker pool.
- Possible fix: check the merged dictionary after `propagate_attributes` (`__main__.py:181`) and report each missing key with its test path.
- Source: found on branch 155 during the skill review (2026-10-06).

### K53. A `_global` context can raise KeyError in `includeValid`

- Plausible, not reproduced. The anchor was not recorded when this was found during the option D smartInclude work; the site below is the most plausible one in the current tree.
- `postYamlExternalScript` passes a postProcess script's returned sections to `processSingleFile("_global", ...)` (`pysrc/processYaml.py:5451`). `_global` is in `specialContexts`, so `processSingleFile` creates no `includeValid` entry for it (`:8262-8265`). A returned section in `includeSections` (`types`, `structures` or `constants`) then sets `self.includeValid[yamlFile]["valid"]` (`:8296`) and would raise `KeyError: '_global'`.
- The base scripts do not reach it. `config/postParseRegisterPorts.py:1505` calls `processSingleFile` on the owner context instead. A project script that returns one of those sections would.
- Low severity.
- Possible fix: needs a decision on whether a postProcess script may return those sections at all, since `_global` has no package to emit them into.
- Source: found on branch 155 during the skill review (2026-10-06).

### K54. Stale comments and an unused schema field

- `templates/fileGen/scaffold.py:74-78`: the scaffolded Makefile says files listed in `EXTRA_SC_GEN_FILES` and `EXTRA_SV_GEN_FILES` "stamp for regeneration and compile with the scaffolded set". `include/make/a2c-common.mk:131` and `:139` add them only to the regeneration lists. The model build compiles every `.cpp` and scans every `.cppm` in the builder runtime directories (`A2C_SRC_DIRS`) and the manifest's source directories (`PRJ_SRC_DIRS`) (`include/make/a2c-systemc.mk:58`, `:62`, `:96-97`, `:111-114`). A listed file outside those directories compiles only if it is also listed in `EXTRA_CPP_SRC`, `EXTRA_O3_CPP_SRC` or `EXTRA_CPP_MODULE_SRC`. `EXTRA_SV_GEN_FILES` is also a prerequisite of the Verilator wrapper library (`include/make/a2c-vl-wrap.mk:40`, `:100`), which triggers a rebuild but adds nothing to the compile.
- `common/scmain/main.cpp:177-178` says the default verbosity is 2 (HIGH). The default is `VERBOSITY_MEDIUM` (`:58`). A `logPrint` with no level logs at `LOG_NORMAL` (`common/systemc/logging.h:275`, `:284`), which needs HIGH, so by default it prints nothing.
- `pysrc/newProject.py:78-80`: the firmware file-map comment says headers appear once the design declares registers or regAccess memories. The entry is `cond: {smartInclude: true}`, and `contextFileEmitted` (`pysrc/processYaml.py:7221-7223`) emits a smartInclude file for any context with `types`, `structures` or `constants` (`:4092`).
- `config/project.yaml:204-206` says legacy `addressControl.yaml` rows are still accepted and must match when both spellings are present. `loadProjectAddressPolicy` reads only `project.yaml` (`pysrc/processYaml.py:7306-7307`), and only the `make migrate` converter (`pysrc/migrateAddressControl.py`) reads `addressControl.yaml`.
- `examples/ip_test/ip/yaml/ip.yaml` misdescribes how `IP_NONCONST_DEPTH` sizes `ipNonConstMem`. The comment at `:201-203` says the worst case comes through the variants, with `maxValue` as a cap. The comment at `:229-231` says a `_resolveBlockParamMaxWordLines` helper takes the largest variant-bound value and that the parameter has no backing constant, and the `desc` at `:232` repeats "no backing constant". No such helper exists, and the variant bindings play no part. `IP_NONCONST_DEPTH` is an ipParameters constant (`:15`, `maxValue: 24`), and `calcAddresses` sizes the memory from that `maxValue` (`pysrc/processYaml.py:5857-5860`).
- `unittest/test_interface_def_contracts.py:46-49`: the Rule 5 docstring says a parameter declares `datatype: struct` or `datatype: type`. `config/schema.yaml:146-152` also allows `typeStruct`.
- `config/schema.yaml:184` declares `sc_channel.thunker: optional(false)`. No code reads it and no interface definition sets it. The `thunker` keys in `pysrc/intf_gen_utils.py` and `pysrc/processYaml.py:3493` belong to cross-binding rows, not to `sc_channel`.
- Possible fix: correct each comment. Removing `thunker:` changes the schema, so it follows `config/SCHEMA_SPECIFICATION.md` and needs a decision.
- Source: found on branch 155 during the skill review (2026-10-06).

### K55. The `valueType` errors for constants advise Python `//`, which `eval` rejects

- When a `uint` or `int` constant holds a float, the errors at `pysrc/processYaml.py:9031` and `:9038` (in `_constants`) and at `:1297` (in `projectOpen.getContextData`) tell the user "Use // for integer division".
- `eval` is SystemVerilog syntax (`pysrc/evalExpr.py`, module docstring). `/` truncates toward zero (`_truncDiv`, `:524`), and `//` fails to parse: `parse('7//2')` raises `EvalParseError: unexpected token '/'`. Real literals are rejected at parse time, and a `$symbol` that resolves to a float is rejected in `pysrc/valueResolver.py` (`_toInt`), so an `eval` expression cannot produce a float.
- A float reaches these checks only through a literal `value:`, such as `value: 1.5` on a `uint` constant. The message then blames `eval` and recommends syntax that the parser rejects.
- Possible fix: name the literal `value:` as the cause, and recommend `valueType: real` or an integer literal.
- Source: found on branch 155 during the skill review (2026-10-07).

### K56. `INTERFACE_AUTO_ALLOC` asserts on the tag it should allocate

- `interfaceLog` (`common/systemc/interfaceBase.h:75`) checks `tracker_->is_valid(tag)` and fails `Q_ASSERT_CTX` with "Invalid tracker interface data" (`:82`) before it reaches the `autoAlloc` branch (`:84`). `is_valid` returns `valid_[tag]` (`common/systemc/tracker.h:290-293`), which is false for a tag nobody has allocated.
- `tracker::autoAlloc` (`tracker.h:183-191`) allocates a tag that is not valid, and the connection `tracker:` field exists so the interface manages the tracker "instead of generate error" (`config/schema.yaml:545`). With `autoAlloc` set, the assert therefore fires before the allocation. A connection `tracker: alloc`, `allocReq` or `allocAck` sets it, and `setTandem` (`interfaceBase.h:125-132`) sets it on an interface already in an auto mode. `q_assert_body` records the failure and forces end of test (`common/systemc/q_assert.cpp:45-46`).
- No example or unit fixture sets a connection `tracker:` value, so nothing in the tree runs this path. From reading the code. Not reproduced.
- Possible fix: skip the validity check when `autoAlloc` is set, or move it after the allocation.
- Source: found on branch 155 during the skill review (2026-10-07).

### K57. The "Primary instance not found" branch in `main.cpp` is dead

- `common/scmain/main.cpp:335-337` calls `errorCode::fail("Primary instance not found")` and jumps to `exit_goto` when `instanceFactory::getInstance(vlInst)` returns null. `getInstance` (`common/systemc/instanceFactory.cpp:26-38`) asserts `Unknown instance <path> Check your command line option ...` (`:35`) before it returns null.
- That assert does not return. `main.cpp:335` runs during elaboration, before the first `sc_start` (`:345`). `q_assert_body` returns only once simulation has stopped or ended (`common/systemc/q_assert.cpp:60-62`). Otherwise it reaches `sc_assert(false)` (`:63`), a SystemC fatal report whose default action aborts the process, as the comment at `:58-59` says. A bad `--vlInst` therefore aborts inside `getInstance`, and `main.cpp:336-337` never runs.
- From reading the code. Not run.
- Possible fix: needs a decision on whether a bad `--vlInst` aborts or exits cleanly. Either delete the dead `errorCode::fail` and `goto`, or look the instance up without the assert and report through `exitMsg`, as the testbench path does (`:339-343`).
- Source: found on branch 155 during the skill review (2026-10-07).

### K58. `twoClkSlowTick.sv` imports `twoClk_package` by hand

- `examples/twoClk/rtl/twoClkSlowTick.sv:23` imports `twoClk_package` after `GENERATED_CODE_END`. The generated region imports only `twoClkIp_package` (`:8`).
- `pysrc/textfileHelper.py:39` declares `--importPackages` for `GENERATED_CODE_PARAM`, `pysrc/systemVerilogGenerator.py:54-55` passes it on, and `importPackages` in `pysrc/systemVerilogGeneratorHelper.py:33-36` adds those packages to the generated import list. No shipped file uses the option.
- `twoClkSlowTick` is declared in `twoClk.yaml` (`:107`), so `twoClk_package` is its own context's package. The generator imports the contexts the generated code uses: types on the block's ports, interface instances, registers, memories and parameterized declarations, constants that child-instance parameter bindings name, and the context of each parameterizable child (`getBDIncludes`, `pysrc/processYaml.py:3415-3534`; `_resolveSvInstanceParams`, `:2141-2171`, `:2249`). Nothing on this block's ports comes from `twoClk`, so the generated region omits the package, and the hand import supplies `TWO_CLK_TICK_DIV` (`twoClkSlowTick.sv:29`). The skills forbid a hand import and route such a package through `--importPackages`.
- Possible fix: move the import to `--importPackages twoClk_package` in the file's `GENERATED_CODE_PARAM`.
- Source: found on branch 155 during the skill review (2026-10-07).

### K59. regrLauncher drops every `--attr` value after the first

- `attrAction` (`regrLauncher/__main__.py:118`) parses only `values[0]` (`:123`). `--attr` takes `nargs='+'` (`:140`), so argparse hands the action every following word up to the next option. The action drops the rest without a warning. A `group` positional that follows `--attr` is dropped the same way.
- Reproduced by capturing the parsed arguments. `r.json --attr run.args+=X session.lrp=2` gives `attr = [('run', 'args', True, 'X')]`, and `session.lrp=2` is gone. `r.json --attr run.args+=X mygroup` gives the same `attr` and an empty `group`.
- Possible fix: needs a decision. Either apply every value, or take one value per `--attr` (drop `nargs='+'` and read `values` as a string) and repeat the option for each assignment.
- Source: found on branch 155 during the skill review (2026-10-07).

### K60. A structure-level `desc:` crashes `processSimple`

- A structure that carries its own `desc:` key next to its fields first gets a warning, `has unknown field desc` (`pysrc/processYaml.py:8453`). `processSimple` then hands the structure to `processSubTable` (`:8474`), which reads the `desc` string as a field row. The nested `processSimple` calls `.get` on that string (`:8581`) and raises `AttributeError: 'str' object has no attribute 'get'`.
- Reproduced by calling `processSimple('structures', ...)` on `foo_t: {desc: "x", a: {varType: byte_t}}`. `make db` itself was not run.
- Possible fix: reject a non-mapping field value with a message that names the structure and the key.
- Source: found on branch 155 during the skill review (2026-10-07).

### K61. In the hierarchical layout, an authored `blockDir:` or `dir:` resolves against the working directory

- `processSingleFile` makes the default node directory absolute (`pysrc/processYaml.py:8244`). A file-level `blockDir:` is used as written, with no `abspath` (`:8234-8235`), and so is a block's `dir:`, through `_auto_blockDir` (`:9802-9807`).
- `expandNewModulePath` (`pysrc/artifactPaths.py:35-52`) joins that directory with the segment and passes the result to `os.path.abspath`, so a relative value resolves against the working directory.
- `projectCreate` changes to the project file's directory (`:4226`), so `make db` resolves the value from there. No generator does the same, so where generated output lands depends on the directory the generator starts in.
- Plausible, from reading the code. Not run.
- Possible fix: needs a decision. Anchor the path at the project root, or reject `blockDir:` and `dir:` in the hierarchical layout.
- Source: found on branch 155 during the skill review (2026-10-07).

### K62. Pro `rrArb` rotates its priority on `next` instead of following the grant

- `builder/pro/common/systemVerilog/rrArb.sv:71-74` takes the next priority pointer from `gnt` only when `next` is low. When `next` is high, it rotates the old pointer by one position, wherever the grant went.
- Both callers raise `next` on every cycle they serve. `memArb` drives `wrNext` on every write it acks and `rdNext` on every read it serves, a refused locking read included (`memArb.sv:117-140`). `vldAckArb` raises `next` when `vld & ack` (`vldAckArb.sv:72-75`).
- Under back-to-back service the pointer therefore rotates every cycle on its own. A cycle model of `rrArb.sv` with `NUM_ARB=4` and `next` high every cycle gives these grant sequences:
  - `req=1100`: 2, 2, 2, 3, repeating. Requester 2 gets three grants for each one to requester 3.
  - `req=0011`: 0, 1, 0, 0, repeating, the same 3:1 split.
  - all four requesting: 0, 1, 2, 3, which is fair.
- From a model of the RTL. Not simulated.
- Possible fix: needs a decision. Either take the pointer from the grant when `next` is high, or document that the arbiters are only approximately fair.
- Source: found on branch 155 during the skill review (2026-10-07).

### K63. The migrate sweep does not report an include of a header the block port deleted

- `pysrc/migrateOrphans.py:622-626` builds `removedNames` from `delete`-disposition legacy entries only. A model block's legacy `<block>.h` has `port` disposition (`:153`), so it never enters that set.
- `make migrate` runs `--port` (`include/make/a2c-common.mk:237`), which deletes the ported pair (`pysrc/migrateBlockModulePort.py:713-714`), and then the read-only sweep (`a2c-common.mk:240`). The sweep reports a `port` file as `TODO_PORT` only while it exists (`migrateOrphans.py:597-598`). A hand-written `.cppm` or testbench `.cpp` that still includes the deleted header is therefore not reported, and the build fails on a missing header.
- `portBlockModules` rewrites includes only inside the pairs it converts. The testbench External port reports sibling includes of its own deleted header (`_reportExternalIncludeSites`, `migrateBlockModulePort.py:918`), and the block port has no counterpart.
- From reading the code. Not reproduced.
- Possible fix: after the port runs, add the deleted `port`-disposition headers to the names the user-include scan looks for.
- Source: found on branch 155 during the skill review (2026-10-07).

### K64. A `registerPorts:` row with no `reset:` is not checked against the router's bus reset

- With no `reset:`, the register handler uses its clock's selected reset (`pysrc/clockTree.py:2366`). `_checkRegisterPortsOnBus` (`:2504`) checks the clock binding on every instance, and the reset binding only when `reset:` is authored (`:2527`). Its docstring states the same.
- Scenario: a leaf whose `rst_n` binds to `rstB` sits under a router whose bus reset is `rstA`. `make db` accepts it, and the handler resets on `rstB`.
- From reading the code. Not run.
- Consequence in the generated RTL: while `rstB` is asserted and `rstA` is not, the router forwards a firmware access to the handler. The handler ANDs its read and write selects with its own reset (`templates/systemVerilog/moduleRegs.py:866-867`), so its `pready` (`:918`) stays 0 while `rstB` is asserted. The router has no timeout and returns the child's `pready` (`templates/systemVerilog/apbDecodeModule.py:151`, `:156`), so the access stalls until `rstB` releases.
- Possible fix: needs a decision. Check the selected reset against the bus reset the same way, or document that an unauthored `reset:` may differ from the bus reset.
- Source: found on branch 155 during the skill review (2026-10-07).

### K65. The `newmodule` comment says the compdb refresh fails on an unfilled scaffold

- `include/make/a2c-common.mk:295-296` says the compdb parse fails on `.cppm` scaffolds that `make gen` has not filled. `pysrc/gen_cpp_module_map.py:52-65` skips a `.cppm` with no `export module` declaration and prints a warning.
- From reading the code. Not run.
- Possible fix: correct the comment.
- Source: found on branch 155 during the skill review (2026-10-07).

### K66. A regression run never sees its per-run `RL_SEED` in its environment

- `regrLauncher/queue.py:37-40` sets `RL_SEED` and `RL_RUN_ID` with `setenv` in the parent process. The spawn `Pool` that runs the tests already exists (`regrLauncher/__main__.py:222`), and each worker builds the run environment from its own `os.environ` (`regrLauncher/runner.py:134`). The started process therefore never gets the per-run values. A `RL_SEED` exported in the shell does reach it, because each worker copies the environment when the pool starts.
- Only `${RL_SEED}` substitution in `run.command` and `run.args` works, because the parent performs it (`queue.py:41`, `regrLauncher/utils.py:18`).
- Reproduced with a spawn `Pool` probe. A generator that sets `os.environ['RL_SEED']` before each item, fed to `imap_unordered`, gives `None` for `RL_SEED` in every worker when the shell does not export it.
- Possible fix: pass the per-run environment to the runner explicitly.
- Source: found on branch 155 during the skill review (2026-10-07).

### K67. The `collectBlocksNeedingRegHandler` docstring says it returns leaf blocks only

- `config/postParseRegisterPorts.py:52-55` says the function returns "every leaf block" that owns registers or regAccess memories. The code at `:56-66` takes every block that owns a register or a regAccess memory and never checks for children.
- A container that owns registers gets a handler too. `synthesiseRegHandler` sets the handler's `hasMdl` from whether the block has children (`:82`, `:89`), so that case is expected. The comment at `:590` repeats the "leaf blocks" wording.
- The docstring may mean a leaf of a router, as `rules/skills/design-register-decode.md` uses the word. `CONTEXT.md` (`:107-109`) defines a leaf as a block with no user-authored child instances.
- From reading the code. No fixture needed, since output does not change.
- Possible fix: say "every block" in the docstring and in the `:590` comment.
- Source: found on branch 155 during the skill review (2026-10-07).

### K68. The migration scope check sees deeper includes than `make db` does

- `_interfaceInScope` (`pysrc/migrateAddressControl.py:442-447`) searches `_includeClosure` (`:427-439`), which follows the router file's `include:` chain to any depth.
- `make db` gives each file a context of the file, its direct includes and their direct includes (`pysrc/processYaml.py:8178`, `:8198`, `:8200`). `lookupInScope` searches only that context (`:10551`). The router check calls it (`config/postParseRegisterPorts.py:383`) and fails with "no visible interface has that name" (`:385-389`).
- An `addressBus` interface three include levels below the router file therefore passes the migration check, with no `TODO_INTERFACE_SCOPE` item (`migrateAddressControl.py:272-278`), and then fails `make db`.
- Reproduced with a Python probe that calls the real functions on a chain a.yaml, b.yaml, c.yaml, d.yaml, with the interface in d.yaml. `_interfaceInScope` returns `True`. `projectCreate.processYamls` builds a context of a, b and c for a.yaml, and `lookupInScope` returns `(None, None)`. Make and `arch2code.py` were not run.
- Possible fix: make `_includeClosure` match the visibility `make db` uses. That depends on the K46 decision. Today that visibility is two levels.
- Source: found on branch 155 during the skill review (2026-10-07).

### K69. The `migrateAddressControl` module docstring cites a missing skill step and calls the orchestrator future

- `pysrc/migrateAddressControl.py:27` points routed-leaf `registerPorts:` authoring at "skill Steps 4 / 6.2". `rules/skills/address-migration.md` has Steps 1 to 5 (`:66-165`), Step 4 is the `project.yaml` check (`:138`), and the `registerPorts:` guidance is the note under Migration diagnostics (`:173`). The TODO message (`migrateAddressControl.py:289-293`) and the constant comment (`:57`) already point at that note.
- `:33-34` says "the future orchestrator does not stamp it". The orchestrator exists. `migrateYaml.py::migrateProject` (`:220`) runs this module as Phase B (`:322-324`) and stamps `yamlFormat: 2` only when `stampEligible` holds (`:327`), which requires `addressReport.clean` (`:213`). `make migrate` calls it first (`include/make/a2c-common.mk:227`). The `clean` docstring (`migrateAddressControl.py:86-87`) already names it as current.
- From reading the code. No fixture needed, since output does not change.
- Possible fix: rewrite the docstring to say what the module converts and that `migrateYaml.py::migrateProject` calls it as Phase B of `make migrate`. Point the `registerPorts:` item at the Migration diagnostics note.
- Source: found on branch 155 during the skill review (2026-10-07).

### K70. Two `hwMemory` assert messages name the wrong function

- `common/systemc/hwMemory.h:143`, in `readRMW`, asserts `m_synch` with the message "writeRMW called on non-synch memory".
- `:157`, in `lock`, asserts `HWMEMORYTYPE_NORMAL` with the message "readRMW called on register memory - not allowed".
- A user who calls `readRMW` or `lock` gets a failure that names a function they did not call.
- From reading the code. Not run.
- Possible fix: name `readRMW` at `:143` and `lock` at `:157`.
- Source: found on branch 155 during the skill review (2026-10-07).

### K71. Dead state and a stale comment in `processYaml.py`

- `generatorTemplates` (`pysrc/processYaml.py:4079`) is assigned and never read.
- The comment at `:4208-4210` says the raw base and Pro inputs are kept so `configTemplates()` can merge template config files. `mergeProjectConfig` returns them into `self._a2cBaseProj` and `self._a2cProProj` (`:4211`), and nothing reads either attribute.
- `calcAddresses` persists `self.addressControl` as the `ADDRESS_CONFIG` blob (`:6035-6036`). Nothing reads it, and the `loadProjectAddressPolicy` docstring says so (`:7303-7304`).
- `processYamls` skips the `includeValid` entry for a YAML file that has an `addressControl` section (`:8264`). This branch looks dead behind the `yamlFormat` gate (`_gateYamlFormat`, `:7267`). Unconfirmed: it needs a fixture that reaches `:8264` with an `addressControl` section after the gate.
- From reading the code. Not run.
- Possible fix: delete the unused set, the two attributes and their comment, and the `ADDRESS_CONFIG` write with its docstring sentence. Delete the `:8264` branch only after a fixture shows it unreachable.
- Source: history sweep of the skills (2026-10-07).

### K72. `configTemplates()` is a second pre-migration detector, and its message narrates the change

- `configTemplates()` (`pysrc/processYaml.py:5399-5413`) rejects `cppConfig`, `svConfig` and `docConfig` in the user `project.yaml`. Its message begins "Template configuration has changed" and lists the keys as "no longer supported".
- The comment at `:4221-4222` calls `_gateYamlFormat` the sole detector of a pre-migration project. This check is a second one.
- `examples/pySocket/arch/yaml/project.yaml:21-23` carries the three keys commented out (see K73).
- From reading the code. Not run.
- Needs a user decision. Move the rewrite to `migrateYaml.py` and delete the check, or keep the check and reword the message to say what to do.
- Source: history sweep of the skills (2026-10-07).

### K73. Code comments and examples describe history

- `config/project.yaml:204-206` says legacy `addressControl.yaml` rows are still accepted. No loader reads that file, and `_gateYamlFormat` (`pysrc/processYaml.py:7267`) stops an unmigrated project before address processing. That gate's docstring (`:7272-7274`) also narrates history: it calls an unmigrated project "legacy" and says the addressControl loader and Python-syntax eval are "already removed".
- `templates/fileGen/scaffold.py:74-78`, the scaffolded `shared.mk` text, says the `EXTRA_*_GEN_FILES` hosts "compile with the scaffolded set". `include/make/a2c-systemc.mk:107` compiles from the manifest's module set, and `rules/skills/manage-build.md:46` says the lists do not add a host to the compile. The same `a2c-systemc.mk` comment also narrates history at `:105-106` ("replaces the prior ... lookups") and `:108` ("now owned-only").
- `examples/ip_test/bridge/yaml/ipBridge.yaml:109-110` names `postParseRegister.py`. The base script is `postParseRegisterPorts.py` (`config/project.yaml:198`).
- `examples/pySocket/arch/yaml/project.yaml:21-23` carries `docConfig`, `cppConfig` and `svConfig` commented out, with "uncomment to use custom templates". `make db` rejects all three (K72).
- `examples/apbDecode/rtl/blockA.sv:67-68` ends "as before".
- `common/systemVerilog/flops.sv:17-18` says the `ASIC` and `FPGA_INIT_FLOPS` aliases exist "for compatibility with existing defines".
- `interfaces/raw/raw_channel.h:20` and `:25` say raw is for "legacy/external IP" and is problematic "while still supported".
- `pysrc/evalExpr.py:6` cites a plan file in a code docstring, and at the wrong path (`builder/base/plan-eval-symbolic-emission.md`; the file is `plans/plan-eval-symbolic-emission.md`).
- From reading the code. No fixture needed, since output does not change, except the `scaffold.py` text that lands in new projects.
- Possible fix: state the current behaviour in each comment, or delete it. The `blockA.sv` edit is outside a generated region.
- Source: history sweep of the skills (2026-10-07).

### K74. The `TODO_ROUTER_RESOLUTION` and `DELETE_DEFERRED` messages tell the user to author `addressBlock:` by hand

- `pysrc/migrateAddressControl.py:220` and `:231` end the first two `TODO_ROUTER_RESOLUTION` messages with "author addressBlock: by hand". `:487-488` ends the third with "resolve by hand". `DELETE_DEFERRED` (`:330-333`) says the file is removed "once the router is authored".
- `rules/skills/address-migration.md` Step 3 says to fix the legacy `AddressGroups:` row instead, because the converter resolves a router only through `decoderInstance` and never sees a hand-written `addressBlock:`. K43 describes the loop the message leads to.
- From reading the code. Not run.
- Possible fix: have each message say to set `decoderInstance:` on the legacy row, or split the row, and re-run `make migrate`. Have `DELETE_DEFERRED` say the file goes once the row resolves.
- Source: history sweep of the skills (2026-10-07).

### K75. `blockBase_src` is reachable only through a fileMap entry no shipped config has

- `templates/fileGen/fileGen.py:156` defines `blockBase_src`, which scaffolds a file with `--template=baseConstructor` regions. `render` dispatches to it for the `blockBase_src` target (`:36-37`).
- The base `blockBase` fileMap entry has only a `cppm` extension (`config/project.yaml:128`). `builder/pro/config/project.yaml` does not override `blockBase`. A project reaches `blockBase_src` only by adding a `src` extension to `blockBase` in its own fileMap.
- No `project.yaml` under `builder/` overrides `blockBase`. A user project outside the tree could, so this is a probable dead path, not a confirmed one.
- Possible fix: confirm no project uses it, then delete `blockBase_src`, its dispatch case and the `baseConstructor` template mapping (`config/project.yaml:26`) if nothing else uses that template.
- Source: history sweep of the skills (2026-10-07).

### K76. Ruling needed: where a composed build anchors a declaring project's wrapper and Config files

- In `unittest/fixtures/variant-two-integrators`, `top/.gen/build.mk` names `ipLeaf/verif/xviMid_xviLeaf_v0_hdl_sv_wrapper.sv`, the `vMid` wrapper and `ipLeaf/registrar/xviMid_xviLeafVariantConfig.cppm`. `xviMid`'s own `make newmodule` scaffolds them under `mid/`. `make -C top/rundir all VL_DUT=1` exits 2 with "Cannot find file containing module".
- Cause: `calcConfigModules` walks only the reachable instances. `xviTop` lists `xviMidProject.yaml` in `projectFiles:` without instantiating `xviMid`, so the `(xviMid, xviLeaf)` lookup misses and falls back to the child's directory, `parentKeys.get((declaringProject, childKey), childKey)` (`pysrc/processYaml.py:6805`).
- Options: anchor over every instance whose container context the declaring project owns and delete the fallback (proposed), or keep today's behaviour. Open with it: should a composed manifest compile and verilate a declaring project's Config module and tops when nothing reachable uses them?
- Source: `plan-116-review-feedback.md:1622-1682` (measured 2026-09-14). Grade: ruling needed; the defect is confirmed.

### K77. Ruling needed: one stamp or two for child-variant wrappers

- `vlSvWrap` (block mode, child's directory, bare stamp) and `vlSvWrapPair` (registrar mode, assembler's directory, `--mode=pair`) both spell the stem `<child>_<variant>`. In a flat single-project layout they name one path, so `--overwrite` lets the registrar pass re-stamp a standalone variant's wrapper to `--mode=pair`, and its ordinary top disappears.
- Options: (A) one bare stamp, retire `vlSvWrapPair` and route the cross-project pair through `vlSvWrapForeign` (recommended); (B) owner-qualify `vlSvWrapPair` and drop the concrete arms from the bare renderer, with a migrate phase; (C) dedupe by path in `artifactRows` and refuse an `--overwrite` that changes the stamp mode.
- Blocked on K76, since (A) and (B) anchor through the same `parentKey`.
- Source: `plan-parameter-sharing.md:1725-1758`. Grade: ruling needed.

### K78. Ruling needed: which blocks the Verilated-top filter applies to

- `plan-file-granular-compile-set.md` §3.3 proposes recording as Verilated tops only the variants a reachable instance selects. It needs a policy: (a) filter foreign-owned blocks only (recommended, no IP standalone build changes), or (b) filter every block, which stops an IP Verilating labels its own harness never instantiates.
- Source: `plan-file-granular-compile-set.md` §3.3 (formerly `file-granular-compile-set-plan.md`; the plan is kept). Grade: ruling needed.

### K79. Ruling needed: how the tandem status-port tee compares

- The plan proposes a settled-change comparison, a hard failure, and a window keyed off `--delay`, plus an event-loss fix, written fixture-first. The architect holds it.
- Source: `builder/pro/plans/bug-status-port-tandem-compare.md` (moved from base `plans/`; the plan is kept). Grade: ruling needed.

### K80. Ruling needed: whether to split `processYaml.py`

- The plan was never executed. Its inventory counted 6,564 lines; the file now has about 11,000. The assessment recommends deleting the plan and redoing the inventory if the split is revived.
- Source: `plan-split-processyaml.md`. Grade: ruling needed.

### K81. Ruling needed: rename `ip_test`'s `ipStd` address group to `top`

- Two groups with one name would give the addressGroup qualification defect template and runtime coverage in the example corpus. It changes a shared fixture other tests read, so it waits for the user.
- Source: `plan-addressgroup-qualification.md` §8. Grade: ruling needed.

### K82. Ruling needed: default name of the router's register ports

- `addressBlock.upstreamPort` and `registerDecoderPort` default to `apbReg`, the legacy generated port name. The alternative derives the name from the router block (for example `<routerBlock>Reg`), so a renamed router does not keep the legacy name. Nobody ruled; the code uses `apbReg`.
- Source: `plan-address-control-refactor.md:1052-1058`. Grade: ruling needed.

### K83. Ruling needed: the deferred testbench terminator follow-ups

- W1: should a scaffolded External always vote? Doing so needs a "skip" outcome, because a configuration with no checker would otherwise report a pass.
- W3: a unit test that every example's terminator survives DUT replacement. About seven examples fail it today (`simple`, `axiDemo`, `helloWorld`, `mixed`, `nested`, `xif`, `bridgeStdTop`), so it needs a waiver mechanism.
- Whether to enforce that a voter must register.
- Source: `plan-tb-external-terminator.md` §4-6, deferred by the user on 2026-09-08. Grade: ruling needed.

### K84. Multi-word signed types get no sign extension

- `get_sign_extension_code` is called only from the single-word arms of `templates/systemc/structures.py` (`:826`, `:1026`, `:1275`). The multi-word arm at `:1005-1020` has no call, so a signed type with `maxBitwidth > 64` unpacks without sign extension. No type in the tree is that wide.
- Source: `bugs-116.md:329-338`. Grade: confirmed.

### K85. A reused router-containing ancestor leaves later occurrences unconnected

- `_findRouterParent` (`config/postParseRegisterPorts.py:156`) returns the first match, and the single-router rule counts instance declarations, not hierarchy occurrences. A second occurrence of an ancestor that contains a router gets no connection. Also present on `origin/main`.
- Source: `bugs-clock-reset-pr-review.md:63-65` (R6). Grade: confirmed.

### K86. Register-bus dispatch loses the qualified interface identity

- The router-to-leaf dispatch discards the router interface's file context and emits its simple name in the instance's file (`config/postParseRegisterPorts.py`). The register-bus view selects interfaces by simple name (`getBDAddressBus`, see K93). `_checkInferredInterfaceScope` (`:308`) does not cover this dispatch row. Also present on `origin/main`.
- Source: `bugs-clock-reset-pr-review.md:59-62` (R5). Grade: confirmed.

### K87. `checkInterfacePair` compares the bare `interfaceType`

- `checkInterfacePair` (`pysrc/processYaml.py:7946`) compares `interfaceType` (`:7982-7983`), not the qualified `interfaceTypeKey`, so two projects' same-named protocol definitions pass as one. `maxTransferSize` and `multiCycleMode` are never compared, though the plan classed both as strict.
- Source: `plan-interface-compatibility.md:348-360`. Grade: confirmed.

### K88. `validatePorts` runs after build artefacts are written

- `projectCreate` calls `runCreateArtifacts()` (`pysrc/processYaml.py:4559`) before `validatePorts()` (`:4561`), so an interface compatibility failure aborts after the artefacts are on disk. The check does not depend on them.
- Possible fix: run `validatePorts` first.
- Source: `plan-interface-compatibility.md:538`. Grade: confirmed.

### K89. `connectionMap` thunker members collide by name

- `_thunker_member_name` (`pysrc/intf_gen_utils.py:1203-1210`) names a `connectionMap` thunker `thunker_<instance>` with no map, port or interface part. Two maps into one child instance emit two C++ members with one name. The peer-to-peer arm adds the channel name.
- Source: `plan-interface-compatibility.md` §5.8 (:684). Grade: confirmed.

### K90. A hand-written `isParameterizable: true` on a plain constant is accepted

- `config/schema.yaml:76` accepts `isParameterizable:` on a constant. Nothing in `pysrc/processYaml.py` rejects it on a constant with no `eval` and no backing parameter.
- Source: `plan-param-constant-collision.md:1487`. Grade: confirmed.

### K91. `common/systemVerilog/a2c.f` works only from its own directory

- `plan-parameter-sharing.md:2660` records `make lint` as unusable tree-wide because Verilator 5.038 rejects `+incdir+` in `a2c.f`. That cause did not reproduce on 2026-10-09: Verilator 5.038 accepts the file when run from `common/systemVerilog`. Run from elsewhere, it fails with "Cannot find file containing module: 'flops.sv'", because the `-y` and `+incdir+` paths are relative to the working directory.
- K28 holds the other `make lint` failures. Whether `a2c-rtl.mk` reaches this one was not checked.
- Source: `plan-parameter-sharing.md:2660`. Grade: plausible; the plan's stated cause is wrong.

### K92. A child project's `instanceGroups:` and `addressObjects:` are ignored

- `loadProjectAddressPolicy` (`pysrc/processYaml.py:7526`) reads only the root `project.yaml`. A composed child's address policy is dropped with no message. Related to K44.
- Source: `plan-addressgroup-qualification.md` §7 (R7). Grade: confirmed.

### K93. `getBDAddressBus` matches the register-bus interface by global name

- `getBDAddressBus` (`pysrc/processYaml.py:3438`) scans `self.data['interfaces']` across every context for a matching `interface` name (`:3447`), so two composed projects that declare one register-bus interface name collide. The same line reads the contracted `interface` field with `.get`.
- Source: `plan-addressgroup-qualification.md` §7 (R6). Grade: confirmed.

### K94. Dead `blk_name` parameter in `module_hdl_wrapper.py`

- `dut_instantiation` (`templates/systemVerilog/module_hdl_wrapper.py:148`) takes `blk_name` and never reads it.
- Source: `plan-116-review-feedback.md:1432`. Grade: confirmed.

### K95. Follow-ups left by the clock and reset review

- `projectOpen.data` is a class-level mutable dict (`pysrc/processYaml.py:529`), shared by every instance.
- `_bindTopInstance` (`pysrc/clockTree.py:1937`) duplicates the ordinary bind path.
- clockTree diagnostics print the internal connection key for unnamed connections, while the container checks in processYaml print a readable label.
- The zero-primary-router branch (`config/postParseRegisterPorts.py:212-221`) is unreachable from YAML, since it needs a containment cycle. A user `postProcess:` script ordered first could still reach it.
- The model `cpu_read` of a memory issues a port read and returns bits beyond the row width (`common/systemc/hwMemory.h`); the RTL answers zero without a request.
- `examples/mixed/rtl/blockD.sv:21`: the `blockBTableSP` port is undriven.
- #152: testController stalls when a test is not registered. `examples/mixed/tb/mixed/mixedConfig.cpp:47-51` removes the blockD tests.
- Source: `bugs-clock-reset-pr-review.md:103-113`. Grade: confirmed.

### K96. Contracted-field `.get()` leftovers in the SystemC templates

- `templates/systemc/baseClassDecl.py:320` reads `intf_data.get('maxTransferSize', 0)`. The field is contracted and the schema default is the string `"0"`, so the fallback has the wrong type too.
- `templates/systemc/structures.py:238` keeps a `.get('enum', False)` fallback for the `generator: datapath` plus `subStruct:` shape. That shape needs a `projectCreate` rule. On it, the datapath pack/unpack path truncates the pointer, and `structures.py:139` raises `KeyError: ''`.
- Source: `plan-testbench-module-conversion.md:2654`; `plan-interface-compatibility.md` §9.3b and its open-items list. Grade: confirmed.

### K97. Templated `prt()` takes hex widths from YAML, not the active Config

- `printOneVar` (`templates/systemc/structures.py:231-236`) sizes the hex field from the YAML `bitwidth`. A 70-bit and an 8-bit variant of one templated structure print alike.
- Source: `plan-variant-config-unification.md:1293`. Grade: confirmed.

### K98. Pro `lmmi` arbitration work is stranded on the #134 branch

- Commit `fa00ba7` ("#134 lmmi interface") is on `origin/feature/134-add-arbitration-features-to-all-interfaces` in builder/pro, and is in neither the builder HEAD nor `origin/main`.
- The `axi_read`/`axi_write` src-modport binding of `setExternalEvent` (plan §2.2) was never built.
- Source: `plan-134-arbitration-all-interfaces.md` §2.2. Grade: confirmed.

### K99. Stale force-link comment and an obsolete TODO

- `templates/systemc/classDecl.py:111-114` says non-templated blocks carry an active force-link function in `<block>Base.h`. The mechanism is retired and the base is a `.cppm`.
- `templates/systemc/structures.py:143`: `# TODO: handle variable size parameters`. The wrapper path already handles parameterizable widths.
- Source: `design-parameterized-types.md:610`. Grade: confirmed.

### K100. The end-of-test check reads two atomics separately

- `evaluateEndOfTest` (`common/systemc/endOfTest.cppm:78`) tests `voteCast && endOfTestCounter >= voters`. Each is atomic (`:88`, `:92`), but SystemC and host threads both reach the check, so the pair is not read as one.
- Source: `bugs-116.md` (end-of-test fix, :66-90). Grade: plausible.

### K101. A `connectionMap` with a parameterizable parent interface gives the child the container's Config context

- `calcBlockConfigInfo` step 3 adds the map's interface as the mapped child's own surface, so the child's `configContext` becomes the container's file. The result is a wrong Config, not a diagnostic. The plan's fixture works around it.
- Source: `plan-interface-compatibility.md` §5.8. Grade: plausible.

### K102. Per-file `connectionsends` collapses ends, so endpoint validation skips them

- `connectionsends` rows are keyed by `portId`, which `config/schema.yaml` composes from `instanceType` and `portName`, and `_process_connections` stores them in a per-file dict. Two connections in one file that reuse a block type on the same port name collapse to one entry, so `_validateParameterizedConnectionEndpoints` never sees the lost end.
- Source: `plan-interface-compatibility.md:191`. Grade: plausible.

### K103. A bare-name `variantValueBindings` entry could reach another project's constant

- `variantValueBindings` inserts the bare parameter name into the resolver's `values` dict, so a binding could resolve a same-named constant from another project.
- Source: `plan-interface-compatibility.md:546`. Grade: plausible.

### K104. Four copies of the storage-bucket table, one diverged

- The C++ storage-bucket table exists in four places, and one copy already differs. One pinning test holds it today. The single-source route through `getContextData()` was not taken.
- Source: `plan-interface-compatibility.md` §9.2, :1441. Grade: plausible.

### K105. A `Reserved` field wider than 64 bits is emitted as a scalar

- `pysrc/systemcGen.py` picks the bucket's `unsignedType` and ignores its `arrayElementSize`, so a `Reserved` padding field wider than 64 bits gets a container that cannot hold it. No example has one.
- Source: `plan-interface-compatibility.md:1218`, :1440. Grade: plausible.

### K106. `raw_channel` uses one event for both handshake directions

- `raw_channel` drives both handshake directions off one `sc_event`, and `write()` waits on the event it notifies. When a consumer is already parked, the writer's own notification also releases the writer, and the next `write()` can overwrite a value nobody read.
- Source: `plan-interface-compatibility.md:334`. Grade: plausible.

### K107. The `status` and `external_reg` thunkers cannot pass `default_value` to their child channel

- Both protocols declare `set_initial_value: true` and their channel constructors take an initial value, but the thunker has no way to forward it.
- Source: `plan-interface-compatibility.md:336`. Grade: plausible.

### K108. `calcForeignConfigHeaders` can collide on a bare block name

- It keys headers on `(projectName, blockKey)` but builds the file name from the bare block name. Two blocks with one name, owned by two projects and given variants by one declaring project, produce two entries with one file name.
- Source: `plan-parameter-sharing.md:2662`. Grade: plausible.

### K109. `make gen` exits 0 when the db build failed

- With `.gen/` absent after a failed db build, `make gen` reports success.
- Source: `plan-parameter-sharing.md:2656`. Grade: plausible.

### K110. Four spellings of "this block has its own params"

- `hasOwnParams` on the view, `params_by_block` in `calcBlockConfigInfo`, `blockInfo['params']` in the templates, and the raw `blocksparams` rows. A naming cleanup, not a correctness item.
- Source: `plan-parameter-sharing.md:2658`. Grade: plausible.

### K111. Project-scope parse residuals

- `connections` and `ipParameters` dispatch to their own `_process_<section>` before the shape check, so a null `connections:` body raises `TypeError` and `ipParameters: <scalar>` raises `AttributeError`.
- A user field named `lc` (`clocks: { clkA: { lc: 5 } }`) raises `AttributeError` in `processSimple`.
- A project named `_global` would collide with `specialContexts`; the `projectName` checks screen only against `yamlAllFiles`.
- Source: `plan-project-scope.md` §13. Grade: plausible.

### K112. One parameter-sharing done criterion was never re-checked

- The done criterion at `plan-parameter-sharing.md:2677` is marked NOT MET for direct instantiation (`uLeafX`, a third project instantiating a block at a variant an intermediate project declared). Step 12b probably resolved it. Nobody re-ran it.
- Source: `plan-parameter-sharing.md:2677`. Grade: plausible.

### K113. Clock alias and reset cost are unverified on real flows

- Whether a `wire clk = <clock>` alias survives ASIC clock-tree synthesis and SDC. No ASIC flow or SDC generation exists here.
- The FPGA area cost of enabling reset.
- Source: `plan-multi-clock-reset.md` §11. Grade: plausible.

### K114. Missing test: bare register block decode overflow (E4.2)

- `unittest/test_error_reg_block_decode_overflow.py` was planned for a bare register block whose decoded span exceeds the parent's per-child window, and was never written.
- Source: `plan-address-control-refactor.md:1271`; `plan-address-control-test-coverage.md:410`. Grade: confirmed.

### K115. Missing test: `inheritContainerParam` across projects

- Precondition (e), container and child from different projects, is stated only in the `unittest/test_inherit_container_param.py:35-40` docstring. The cross-project negative fixture was deferred.
- Source: `plan-parameterizable-config-template.md:799`. Grade: confirmed.

### K116. Missing test: unqualified width reference with an invisible backing constant

- The step 1 coverage fixture: an unqualified width reference whose backing constant is not visible from the interface's declaring context.
- Source: `plan-parameter-sharing.md:20` (§6 step 1). Grade: confirmed.

### K117. Missing test: generator emission of the six newer thunker headers

- No fixture makes the generator emit the six protocol thunker headers added for interface compatibility.
- Source: `plan-interface-compatibility.md:243`. Grade: confirmed.

### K118. Missing test: address control with two physical copies of one project

- Two copies of one logical project map to one qualified address-group key. Believed correct and untested. `unittest/fixtures/multi-copy` has no address control.
- Source: `plan-addressgroup-qualification.md` §7 (R5). Grade: confirmed.

### K119. Missing measurements: SV wildcard imports and payload copy cost

- Generated SV wildcard-imports several project-qualified packages into one scope. The plan reasons it is benign and never measured it on Verilator.
- Pack/unpack cost against direct copy is unmeasured, and the field-wise assignment adapter alternative is undecided.
- Source: `plan-addressgroup-qualification.md` §7 (R4); `plan-interface-compatibility.md:996`. Grade: confirmed.

### K120. Missing test: `newProject` fixtures and a `new-project` pipeline target

- Source: `plan-new-project-onboarding.md` §8. Grade: confirmed.

### K121. Missing evaluation: Arm B of the `design-register-decode` skill

- The agent evaluation of `design-register-decode` as the sole guidance, over H1-H8, was never run.
- Source: `firmware_decode_skill_fix_plan.md:235`. Grade: confirmed.

### K122. Missing test: `isp_lut` LUT arithmetic is never compared against a reference

- In `/work/ws/isp`, every value-checking run uses `--lut_cfg 0` (bypass), and the two runs that enable the LUT assert nothing. Sign extension, `frac * slope`, the shift, accumulator truncation, offset and saturation are unverified. The fix belongs in that repository, not in the builder.
- Source: `bugs-116.md:394-493` (BUG 13). Grade: confirmed.

### K123. Same-basename headers shadow each other across composed projects

- On the flat `-I` path, two composed projects' headers with one basename shadow each other. The layout B6 child-owned residual headers would need a project-qualified subpath.
- Deferred, design-only.
- Source: `plan-ip-project-composition.md:939` (C2.5). Grade: deferred.

### K124. A Config cannot be composed from two projects' parameter namespaces

- A block's Config draws from one `configContext`.
- Deferred, design-only.
- Source: `plan-interface-compatibility.md` §5.4 (G5.4); `plan-parameter-sharing.md`. Grade: deferred.

### K125. `TODO_USER_INCLUDE` does not fire for a residual testbench header include

- A residual `#include "<blk>Testbench.h"` is no longer reported. The plan declined the gap and says widening the sweep's include scan, the fix K63 proposes for the block-port case, is wrong for the testbench case.
- Declined. Kept so it is not re-filed.
- Source: `plan-testbench-module-conversion.md:1199-1203`. Grade: deferred.

### K126. A unary operator over a parenthesized conditional loses its parentheses

- `evalExpr.unparse` (`pysrc/evalExpr.py:461-465`) and `emissionUtils._emitNode` (`pysrc/emissionUtils.py:53-57`) wrap a unary operand only when it is a `Bin`. A `Cond` operand comes out bare.
- Reproduced: `unparse(parse('-($A ? 1 : 2)'))` gives `-${A/ctx} ? 1 : 2`, which re-parses as `(-A) ? 1 : 2`. With `A = 0` the original evaluates to -2 and the re-parsed tree to 2. The value `make db` stores is right; `evalCanonical` and the SV and C++ emitted from it compute something else.
- Fix: wrap a `Cond` operand in both places.
- Source: found while writing `specs/spec-eval-expressions.md`. Grade: confirmed (reproduced).

### K127. `$clog2` is wrong for large arguments

- `arch2codeHelper.clog2` is `math.ceil(math.log2(x))` (`pysrc/arch2codeHelper.py:9-10`), and `evalExpr.evaluate` uses it for `$clog2`. The float log rounds `2**n + 1` down to `n` for every `n >= 49`.
- Reproduced: `evaluate(parse('$clog2(562949953421313)'))` (`2**49 + 1`) returns 49; the answer is 50, `(x - 1).bit_length()`.
- Source: found while writing `specs/spec-eval-expressions.md`. Grade: confirmed (reproduced).

### K128. A row with both `value:` and `eval:` silently drops the `eval:`

- `processSimple` takes the named field whenever it is present and never reads `eval` (`pysrc/processYaml.py:8861-8866`). The unknown-field check exempts `eval` (`:8681`), so nothing reports it.
- `ARCH2CODE_AI_RULES.md`, Constants rule 2, says "either `value` OR `eval`, not both". Nothing enforces it.
- Source: found while writing `specs/spec-eval-expressions.md`. Grade: confirmed by reading.

### K129. A derived `maxValue` is not an upper bound when the expression can shrink

- `_constants` derives a parameterizable constant's `maxValue` by evaluating its `eval` with every parameterizable referent at its own `maxValue` (`pysrc/processYaml.py:9097-9101`, `valueResolver.maxValue`). For `$A - $B` or `$A / $B` a variant with a smaller `B` gives a larger value than that.
- Only the default value is checked against the derived bound (`:9126-9128`). A per-variant value above it is not, so anything sized from `maxValue` can be too small.
- Source: found while writing `specs/spec-eval-expressions.md`. Grade: plausible; the derivation is confirmed by reading, no fixture exercises a shrinking expression.

### K130. Two parents of one child in different directories get two registrars with one module name

- `artifactPaths.artifactRows` emits a registrar row per `(assembler, child)` pair in `REGISTRARPAIRS`, anchored at the assembler's directory (`pysrc/artifactPaths.py:173-192`). The template names the module per owning project and child only, `<project>.<child>.registrar` (`templates/systemc/blockRegistrar.py:42`, `intf_gen_utils.cpp_child_registrar_module_name`).
- Two assemblers of one child in different node directories of one project would therefore get two files with the same content declaring the same module. Not tested.
- Source: found while writing `specs/spec-block-registration.md`. Grade: plausible.

### K131. The `-Wl,-u <anchor>` advice has no anchor to name

- `common/systemc/instanceFactory.h:12-23` tells a project packaging blocks into a static archive to use `-Wl,--whole-archive` or `-Wl,-u <anchor>`. Generated code offers no usable anchor: the retain-marked statics sit in anonymous namespaces, and `register_<Class>_variants()` is attached to its named module (`templates/systemc/constructor.py:461-468`), so it has no stable plain symbol.
- Fix: drop the `-Wl,-u` advice, or emit a documented extern anchor per block.
- Source: found while writing `specs/spec-block-registration.md`. Grade: confirmed by reading.

### K132. `intf_gen_utils.cpp_registrar_module_name` has no caller

- `pysrc/intf_gen_utils.py:568-573` spells the three-part `<project>.<parent>.<child>.registrar`. The registrar template uses `cpp_child_registrar_module_name` (`templates/systemc/blockRegistrar.py:42`), and nothing calls the three-part form.
- Fix: delete it.
- Source: found while writing `specs/spec-cpp-module-layout.md`. Grade: confirmed.

### K133. `A2C_VL_TOP_<block>` misses a DUT child whose top is not a block-mode row

- `createBuildManifest` fills `dutTops` from `mode: block` rows only (`config/createBuildManifest.py:343-344`). A direct child of the top that runs at a foreign label or a container-sourced variant has its top on a registrar-mode row, so it gets no `A2C_VL_TOP_<block>` entry and `make lint` cannot resolve it through `HDL_TOP_MODULE`.
- Source: found while writing `specs/spec-verilated-wrappers.md`. Grade: confirmed by reading; no fixture exercises it.

### K134. Two adjacent unary operators emit an increment or decrement

- `evalExpr.unparse` and `emissionUtils._emitNode` wrap a unary operand only when it is a `Bin` (`pysrc/evalExpr.py:461-465`, `pysrc/emissionUtils.py:52-56`). `- -$A` and `-(-$A)` store as `--${A/ctx}` and emit as `--Config::A`; `+ +$A` emits as `++Config::A`. The canonical re-parses to the same tree, but C++ reads the emitted text as a decrement or increment and fails to compile.
- Reproduced: `unparse(parse('- -$A', qualify=...))` returns `'--${A/ctx}'` and `emitExpr` with `lang=C` returns `'--Config::A'`.
- Fix: separate or parenthesize a unary operand that is itself a `Unary`.
- Source: found while reviewing `specs/spec-eval-expressions.md`. Grade: confirmed (reproduced).

### K135. An authored `${name/context}` bypasses include scope

- `_Parser._atom` accepts a `SYM_Q` token as written and never calls `qualify` (`pysrc/evalExpr.py:366-367`), and `ValueResolver` takes any key containing `/` as already qualified (`pysrc/valueResolver.py:134-136`). An author who writes the qualified form can reach a constant in a file the row does not include.
- Fix: reject the authored qualified form in user input, or check it against the row's include scope.
- Source: found while reviewing `specs/spec-eval-expressions.md`. Grade: plausible; no fixture writes the qualified form.

### K136. An `eval:` under `ipParameters:` over fixed constants becomes direct-parameterizable

- `_constants` sets `directParam` from `ipActive` whenever no referent is parameterizable, with no check that the row has no `eval` (`pysrc/processYaml.py:9108-9111`). The comment there says the direct path applies to a "literal value (no eval)". An `eval:` under `ipParameters:` whose referents are all fixed is therefore treated as a direct parameter and requires an authored `maxValue`.
- Fix: decide whether such a row is fixed or direct, and make the code and comment agree.
- Source: found while reviewing `specs/spec-eval-expressions.md`. Grade: plausible; the branch is confirmed by reading, no fixture exercises it.

### K137. A misspelled `projectOverrides:` key is silently ignored

- `_selectMasters` looks up overrides only for names some provider declares (`pysrc/projectScan.py:532-570`), and the master-discovery pass scans any existing target regardless of the key (`:189-196`). An override keyed by a name no file provides, such as a typo, selects nothing and draws no diagnostic.
- Fix: reject an override whose key names no provided `projectName`.
- Source: found while reviewing `specs/spec-project-composition.md`. Grade: plausible.

### K138. `blockRegistrarInitLines` has an unreachable `variants` branch

- The `if data['variants']` branch in `templates/systemc/constructor.py:441` runs only for a block without its own `params:`, and `make db` rejects a variant on such a block (`pysrc/processYaml.py:10508-10514`). The branch never runs.
- Fix: delete it and keep the single empty-variant registration.
- Source: found while reviewing `specs/spec-block-registration.md`. Grade: confirmed by reading.

### K139. Multi-word `regAccess` memory writes differ between RTL and model

- The RTL handler stages the lower words of a memory row and writes the whole row when firmware writes the row's highest word (`rules/skills/rtl-registers.md:87`; the write enable follows the top word's update, `templates/systemVerilog/moduleRegs.py:339`).
- The SystemC `hwMemoryPort::cpu_write` does a read-modify-write of the whole row on every 32-bit word (`common/systemc/hwMemory.h:258-275`), and `hwMemory::cpu_write` updates the row in place per word (`:81-92`). A tandem comparison or a model-side observer can therefore see a partly written row between the word writes.
- Source: found while updating `rules/skills/design-register-decode.md` during the plans cleanup. Grade: confirmed by reading.

### K140. The round-trip helper fills only `_byteWidth` of a Config struct's packed word

- `_roundTripHelperLines` (`templates/systemc/structures.py:1588`) emits `memset(&packed, pattern, T::_byteWidth)` on a `T::_packedSt`. For a parameterizable struct narrower than 64 bits the packed form is a whole `uint64_t`, so the bytes above `_byteWidth` stay uninitialised. `unpack()` masks each field, and `packed` is never compared after `b.pack(packed)`, so the check still holds, but the helper does not exercise what it claims for those structs.
- The same helper declares `uint64_t test` and fills it with the pattern; nothing reads it.
- Source: found on branch 155 while fixing the `pack()` memset width (the same `_byteWidth` sizing mismatch, which left garbage in `pRegSt_v<12>::pack()` and failed CI nondeterministically). Grade: confirmed by reading.

### K141. An aligned nested struct above bit 64 packs into the wrong word

- `fw_pack_oneNamedStruct` (`templates/systemc/structures.py:1436`) gives a sub-struct of 64 bits or fewer that starts on a word boundary the destination `_ret` with no word index. In a fixed-width parent wider than 64 bits, `typedef uint64_t _packedSt[2]`, a 32-bit sub-struct at bit 64 is emitted as `hi.pack(*(subSt::_packedSt*)&_ret);`, which overwrites the low bits of word 0 and leaves word 1 zero.
- No example declares this layout; every aligned nested pack in the examples sits at position 0, so the round-trip tests do not reach it. Found by rendering the function in memory with position 64 in a 128-bit parent; not compiled or run.
- Source: reviewer finding on the branch 155 `pack()` memset fix. Grade: plausible, confirmed by rendering only.

## Feature requests

These stay off branch 155 (decision D12).

### F1. APB error response and abort (A22, A12)

- The SystemC `apb_channel` has no error field and no abort. Only the pySocket APB path returns PSLVERR (base cc508e8f).
- Proposal: add an optional `slverr` to `complete()`, default false, and carry it through `apbBusDecode`. Model abort as a TB-side watchdog that completes with an error, not as channel cancellation.
- An empty decoder slot could raise PSLVERR once this lands (follow-up to A3).

### F2. Instance `count:` (A6)

- `count:` values other than 1 are now rejected at `make db`. Real support would turn N instances and their connections into one entry.
- It needs a naming rule (for example `u_csiSif_0`) and an indexed connection syntax.

### F3. FW cross-compile target (A27)

- The project that asked for it carries its own target. Move it into the framework only after a second project needs it.

### F4. Transaction logic for raw tandem (A32)

- Raw is not transactional: the RTL side is a wire sampled every clock, and the model side is a hand-off that blocks until read. A one-to-one tee therefore cannot pair the two streams. Raw tandem is not recommended.
- Idea: let a raw tee take an injected function (a lambda) that supplies the transaction logic, deciding which samples form a transaction to compare. The interface stays clocked.
- Decision (branch 155, D5): no change now.

### F5. Authored `namespace:` and import semantics, and an IP packaging manifest

- Deferred, design-only. Names are qualified by `projectName` today, and C++ modules and SV packages carry the scoping. No authored `namespace:` field exists.
- Source: `plan-ip-namespaces-and-parameterization.md`. Grade: deferred.

### F6. A `projectName`-qualified include

- Deferred, design-only. An explicit `projectName:` on an `include:` would let a project reach another project's file without a vendored copy. Symlinks stand in for it today.
- Source: `plan-projectoverride-file-ownership.md:113`, :636. Grade: deferred.

### F7. Whole-variant inheritance form (D7)

- Deferred, design-only. Not built and not specified. Only the per-parameter `containerParam:` form exists. Re-decide before any work.
- Source: `plan-parameter-sharing.md:226-229`. Grade: deferred.

### F8. One `projectOpen` view for wrapper ownership (Gap 4)

- Deferred, design-only. Hardening of the cross-level wrapper work.
- Source: `plan-cross-level-variant-wrappers.md:21`, :378. Grade: deferred.

### F9. Registration packaging and portability

- Deferred, design-only:
  - uniform registrar ownership of non-templated children (Q7);
  - selective export of the block class, considered and not adopted;
  - archive packaging (Q5) and MSVC or minimum gcc support for `[[gnu::used, gnu::retain]]` (Q6).
- Source: `plan-block-registration.md`; `research-block-registration-options.md`; `plan-registration-encapsulation-cleanup.md:589-597`. Grade: deferred.

### F10. File-ownership follow-ups

- Deferred, design-only:
  - a W4 clean-start recovery target that deletes everything purely generated and regenerates;
  - a validator assertion that the `base`, `registrar` and `fwInc` segments hold no user content;
  - whether one frozen legacy map covers every legacy format;
  - whether the pro overlay must be conditional.
- Source: `plan-file-ownership-classification.md`. Grade: deferred.

### F11. New-project onboarding questions

- Deferred, design-only. The six open questions: a richer demo, non-interactive flags, `--newproject` adding a sub-project, the RTL question, a firmware stub, and a make-shaped entry point.
- Source: `plan-new-project-onboarding.md` §9. Grade: deferred.

### F12. `make db` lint for a node named like the project root (ip_test D5)

- Deferred, design-only. The convention is documented; the lint that rejects a node name equal to the project-root basename was not built.
- Source: `plan-ip_test-dir-cleanup.md:33`, :263. Grade: deferred.

### F13. Deferred generator options

- Deferred, design-only:
  - fully numeric trampoline port widths (`plan-canonical-verilated-wrappers.md:569`);
  - non-module mode in `constructor.py` and `blockRegs.py`, left as it is (`plan-sv-naming-refactor.md:129`);
  - the `'model'` emission flavour that `structures.py` selects when `--mode` is absent (`plan-testbench-module-conversion.md:2374-2379`);
  - a third `kind` that separates `import` from `using namespace` at the producer (`plan-testbench-module-conversion.md:1847-1849`);
  - whether render-helper `assert`s become `printError` (`plan-testbench-module-conversion.md:2862`);
  - the address-control converter not deleting a legacy `addressControl.yaml` when only advisory TODOs remain (`plan-yaml-migration.md:311`);
  - a compile-time `reinterpret_cast` bind (T5) and type-erased channels (T6, T7) (`research-multi-config-bindings.md:736`, :760);
  - Verilating one top several times with parameter overrides (`plan-canonical-verilated-wrappers.md:156`).
- Source: the plan files named per item. Grade: deferred.

### F14. Testbench use cases with no decision

- Deferred, design-only:
  - one testbench across several compiled variants;
  - parameter sweeps and randomised parameters;
  - runtime controls in `testBenchConfigFactory`;
  - `make newmodule` scaffolding `--excludeInst` for `_tb` wrappers.
- Source: `research-variant-aware-testbench-use-cases.md`; `plan-step-11-variant-aware-testbenches.md`. Grade: deferred.

### F15. Rejected alternatives

- Deferred, design-only. Recorded so they are not proposed again:
  - a `useDefault: true` flag (`plan-parameterizable-config-template.md`);
  - a per-site merged Config struct, and renaming block params (Q3) (`plan-parameter-sharing.md:390`);
  - auto-rewriting Python `//` in `eval` (`plan-eval-symbolic-emission.md`);
  - a WARNING for 9A (`plan-116-review-feedback.md`);
  - detecting conflicting registrations. `emplace` first-wins is intentional (`plan-reusable-ip-registrar.md:952`).
- Source: the plan files named per item. Grade: deferred.
