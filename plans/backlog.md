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

- `unittest/fixtures/clockgen-link-loss/shared.mk` does not set `A2C_ROOT`. It is not yet known whether the test harness supplies it.
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

### K16. External registers wider than 64 bits have no working RTL (resolved)

- `external_reg_if.write` is 2 bits wide, so the per-word strobe `{1<<n}` truncates for word 2 and above.
- `templates/systemVerilog/moduleRegs.py:87-93` means to reject such registers, but the flag name is misspelt (`unsup_` vs `unsupp_`), so it only prints an error and generation continues.
- Source: found on branch 155 during the D1 wide-register work.
- Resolved by decision D1b: an `ext` register may be no wider than the 32-bit register bus. `projectCreate` (`_post_registers` in `pysrc/processYaml.py`) rejects a wider one at `make db`, naming the register, block, file, width and limit, and the dead template check is removed. Test: `unittest/test_error_ext_register_width.py`.

### K17. Model external-register commands carry no word strobe (moot)

- After D1, the model's `hwRegisterIf` issues one `reg_write_cmd` per word. The command has no field naming the word written, while RTL engine code can use `write[n]`.
- Source: found on branch 155 during the D1 wide-register work.
- Moot after D1b: an `ext` register is one word, so there is one command and one strobe bit per write, and `hwRegisterIf` is back to one command per register write.

### K18. Two example runs fail, cause not yet confirmed

- `examples/ip_test` regression: `bridge_driver` fails at elaboration with `Unknown instance ip_top.uBridgeDriver`. That instance is declared only in the bridge project (`bridge/yaml/bridgeStdTop.yaml:60`), but `rundir/regr_ip_test.json:36` uses it under `ip_top`.
- `examples/simple_ip/ip` `run-vl`: `Attempted to create an instance ip of an unregistered block type ip_verif`.
- Neither failure has yet been checked against a tree from before branch 155.
- Source: found on branch 155 while checking the D2 decoder change.

### K19. The external register interface still has a 2-bit `write`

- After D1b, an `ext` register is one 32-bit word, but `external_reg_if.yaml` (`write: 'bit [1:0]'`), `external_reg_if.sv` and `external_reg_hdl_if` (`sc_bv<2>`) still size `write` for two words. The `ext` write arm in `moduleRegs.py` can now only drive bit 0.
- Narrowing `write` to 1 bit is an interface change, so it waits for a decision.
- Source: found on branch 155 during D1b.

### K20. The register bus `data_t` width is not checked

- Register decode works in 32-bit words: `moduleRegs.py` slices `pwdata[31:0]`, and `regBase::cpu_write` takes `uint32_t`. `interfaces/apb/apb_if.yaml` leaves `data_t` as a free struct parameter, and `projectCreate` does not check that an `addressBus` interface binds it to 32 bits.
- A narrower `data_t` gives an out-of-range `pwdata` part-select in the generated RTL for any register wider than it.
- Fix: reject at `make db` an `addressBus` interface whose `data_t` is not 32 bits.
- Source: found on branch 155 during the D1b review.

### K21. `rtl-registers.md` names the wrong external register ports

- `rules/skills/rtl-registers.md:33` lists `<regName>_wr` and `_wdata`. The real interface is `external_reg_if`, with `write`, `wdata` and `rdata`.
- Source: found on branch 155 during the D1b review. This predates it.

### K22. `test_file_prefix.py` cleanup fails on NFS

- `check_main_migrate_without_prefix` prints PASS, then `shutil.rmtree` fails on an NFS `.nfs*` placeholder file. The check returns `FileNotFoundError` instead of True and leaves a `unittest/file_prefix_main_*` directory behind. It happened on two separate runs.
- Possible fix: put the temp directory outside the NFS tree, or retry `rmtree` once. The cause of the open file handle is not yet known.
- Source: found on branch 155 during D6b.

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

### K30. Parameterized registers decode the nominal width, not the worst case

- `templates/systemVerilog/moduleRegs.py:43`, `:49` build segments from `get_struct_width` (the nominal `width`), while `calcAddresses` reserves `maxBitwidth`. The model registers the nominal `bytes` (`templates/systemc/constructor.py:335`). For `ipCfg` in `examples/simple_ip` the nominal width is 73 bits and the reserved width is 131 bits, so words 0x30C and 0x310 are reserved but decoded by neither side. For a variant wider than nominal, the extra bits have no flops. The comments at `moduleRegs.py:490-493` and `:651` ("worst-case word") are wrong.
- Possible fix: build segments from `maxBitwidth` and register `maxBytes` in the model.
- Source: found on branch 155 during the D2b scope review. No example uses a wider variant.
- Fixed on branch 155 by user decision on 2026-10-05, together with K34. `worstCaseBitwidth` and `rowFootprintBytes` in `pysrc/processYaml.py` compute the footprint once. The address map, the RTL handler (`worstBitwidth`) and the model (`maxBytes`) all read it. In the RTL and in the model, words of an `rw` or `ro` register above the bound variant's width read 0 and drop writes. Test: `unittest/test_regs_param_width_footprint.py`.

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

### K34. Parameterizable-width memories use a different row stride in the model and the RTL

- There are three strides, not two. The address map sizes rows from `maxBitwidth` (`processYaml.py:5842`). The RTL handler sizes them from the nominal `width` (`moduleRegs.py:72-75` via `intf_gen_utils.get_struct_width`), which matches the worst case in simple_ip only by rounding: 3 words and 4 words both give 16-byte rows. With a nominal width of 32 and a `maxBitwidth` of 128, the RTL would use 4-byte rows against a 16-byte map stride. The model registers and indexes rows at the variant's own width (`nextPowerOf2min4(_byteWidth)`, `common/systemc/hwMemory.h:77-101`, `addressMap.h:51-56`).
- Example: `examples/simple_ip` `uIp`, variant0. The model claims block offsets 0x00-0x3F at 4 bytes a row. The RTL claims 0x00-0xFF at 16 bytes a row. A read at 0x40 returns `BADD_C0DE` in the model and row 4 in the RTL. A write at 0x10 lands in model row 4 and RTL row 1.
- Possible fix: compute the row footprint once from the worst-case width. Have the RTL handler and the model's `hwMemory` both read it, at the stride the address map allocates. This is the memory counterpart of K30, which has the same nominal-width cause.
- Source: found on branch 155 during the D2c review.
- Fixed on branch 155 with option A, by user decision on 2026-10-05: one worst-case row stride for every variant. `rowBytes` comes from `rowFootprintBytes`. The RTL row width, the model's `hwMemory`/`hwMemoryPort` `ROW_BYTES` template argument and the `addMemory` size all read it. Bytes of a row above the variant's width read 0 and drop writes. A `static_assert` rejects a `ROW_BYTES` smaller than the default or not a power of two. Test: `unittest/test_regs_param_width_footprint.py`, which covers the flat leaf model and the reg-handler model. Not changed: the RTL writes a memory row when the variant's top word is written, and the model writes each word into the row at once.

### K35. A memory with a fixed address type wider than its depth indexes past its RAM

- `moduleRegs.py` slices the row index as `<addrSt>'(apb_addr[31:2])`, relative to address 0, not to the memory's base. When the address type is wider than the depth needs, base bits reach the index. `ipFixedMem` in `examples/simple_ip` (8-bit address, 16 rows, base 0x200) drives index 0x80 for row 0 (`ipRegs.sv:155`, `ip.sv:89`, `memory_dp.sv:61-63`).
- Verilator wraps the index, so the examples pass. A 4-state simulator follows the LRM and drops the write and reads X. Rows past the depth already read `BADD_C0DE` after D2c.
- Source: found on branch 155 during the D2c review.
- Fixed on branch 155 by user decision on 2026-10-05. The row index and the in-row word select now count from the memory's base (`(apb_addr - REG_X)`), as the model does. The word select had the same defect for a base not aligned to the row footprint, which an integer `alignment:` produces. Tests: `unittest/test_regs_rtl_mem_index.py`, `unittest/test_regs_rtl_mem_word_select.py`.

### K36. A router with no upstream feed crashes the decoder templates

- A router block with no authored register-bus connection or boundary connectionMap into it passes `make db`. Then `templates/systemVerilog/apbDecodeModule.py` and `templates/systemc/constructor.py` both raise UnboundLocalError, because each scans connection rows for the parent port. The view's `addressDecode['registerBusPort']` cannot replace that scan, because for a router it holds the interface name (`apbReg`), not the port name (`cpu_main` in examples/mixed).
- Only an authoring mistake reaches this, for example running `make gen` before wiring the CPU.
- A fix was drafted on branch 155 and not landed. It had three parts:
  - a `make db` rejection of a reachable router that has neither a register-bus connection into it nor a boundary connectionMap feeding it. It must run after `validatePorts` and the block-scope name check. If it runs at the end of `postParseRegisterPorts.postProcess`, it takes over the messages of five existing error tests: block-scope name collision, addrgroup vartype collision, nested decoder overflow, register interface type mismatch and register packed form;
  - a view field for the router's real feed port;
  - both templates read that field.
- Cost: about 18 `test_addrctl_*` fixtures and 8 other success-path fixtures and controls author feedless routers, and each needs a feed. A shared CPU block in `unittest/_addrctl_helpers.py` keeps that change mechanical.
- Source: found on branch 155 in the D2 router review. Deferred from branch 155 by user decision on 2026-10-05.

### K37. Unit tests leave temporary project directories in `unittest/`

- `test_inherit_vl_child.py`, `test_regs_handler_container_config.py` and the tests that create `inherit_order_*` and `param_scope_shared_*` leave one directory per run under `unittest/`. The tree holds about 30 of each, the oldest from 2026-09-29, before branch 155. Git does not report them.
- Possible fix: create them under the system temp dir, or remove them in a `finally`.
- Source: found on branch 155 during the final verification run.

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

### K41. A context whose only content is `ipParameters:` emits no package or `Includes.cppm`

- `smartInclude` keys on `includeSections` (`pysrc/processYaml.py:4092`: `types`, `structures`, `constants`). A context that declares only `ipParameters:` therefore gets no `_package.sv` and no `Includes.cppm`.
- Option A, adding `ipParameters` to `includeSections`, was tried on 2026-10-06 and reverted. The package and `Includes.cppm` it emitted were empty. `test_variant_binding_resolution.py` then failed with "'arch_package' is used by two distinct design units". In `examples/xprojParam`, dpMid and dpTop imported context files that do not exist, so each needed new files.
- Today `importPackages` (`pysrc/systemVerilogGeneratorHelper.py:22`) imports nothing for such a context, and `unittest/test_ipparam_only_context.py` checks that the design generates, lints and runs.
- Possible fix: needs a decision on what such a context's package would contain, since option A's files were empty.
- Source: found on branch 155 while testing an out-of-tree project. Left open by user decision on 2026-10-06.

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
