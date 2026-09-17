# Plan: Running the C++20-module SystemC model under VCS and Xcelium on the Lattice RHEL farm

- **Status:** IN PROGRESS (2026-09-15). Compiler/ABI path proven for **both** VCS and Xcelium with Clang 18 (§3.5, §3.10).
  **Native RTL simulation proven in prototype for both VCS (§3.13) and Xcelium (§3.14), verif and tandem.** Remaining: make both
  flows automatic (generator + make, §5 items 1-4), regression wiring (§5 item 5), and the performance checks.
- **Branch context:** `feature/116-parameterized-types` (debayer), `builder` submodule on `feature/125-a2c-20-followup-issues`.
- **Goal (sharpened 2026-09-15):** run the **full debayer RTL regression** (`rundir/regr_debayer.json`: model, tandem and
  verif tests with the SystemVerilog RTL as the DUT) natively under **Synopsys VCS and Cadence Xcelium** on the farm host,
  without the container. Two sub-problems: (1) compile the C++20-module SystemC testbench/model on the host and link it
  with each simulator's SystemC kernel (the compiler/ABI problem, largely solved for VCS below); (2) replace the
  Verilator-generated DUT wrappers with a SystemC/HDL boundary native to each simulator so the RTL is elaborated by
  VCS/Xcelium (the DUT-boundary problem, under analysis). The Verilator flow inside the `a2c-dev` container with Clang
  is the known-good reference and is out of scope here.
- **Predecessor document:** `debayer/docs/vcs-build.md` (2026-07-07). This plan supersedes its compiler findings;
  its make-environment changes (`CPP_STD` knob, `a2cProEnv.mk`) are still in force and are reused unchanged.
- **Farm-specific storage for tools:** `/ldc/projects/qistor/users/atomlin/tools` (project space, 915 GB free).

---

## 0. Shareable status statement (2026-09-15, evening)

**Problem**

- The arch2code SystemC testbench and models now use C++20 named modules. No compiler on the Lattice farm could compile them:
  GCC 13.2 and GCC 14.2 fail on internal module-serialisation defects, and the site Clang 16 fails on global-module-fragment
  consistency errors. Until now the only working build was Verilator inside the development container.
- The VCS flow that existed pinned the DUT choice at compile time and had lost its RTL step, so a VCS build ran the SystemC
  model with no RTL at all. Xcelium had never been wired up.
- Requirement: run the complete debayer RTL regression natively under VCS and Xcelium on the farm, with no container, and with
  no added simulation-time overhead, since a full SoC will use the same flow.

**Solution and evidence**

- **Compiler:** a prebuilt Clang 18.1.8, using the VCS-matched GCC 13.2 standard library, compiles every module unit. It is
  installed in the shared project tools area (`/ldc/projects/qistor/tools/share/llvm-18.1.8`) and is the newest prebuilt Clang that runs
  on both farm releases: RHEL 9.6 and RHEL 8.10 (Clang 20.1.8, used in the container, needs glibc 2.34 and cannot start on RHEL 8.10; it
  was tested and passes both regressions on RHEL 9, so the flows are compiler-version agnostic). The GCC 13.2 library is mandatory:
  VCS's SystemC library requires its symbol versions, and Xcelium's bundled runtime accepts them but would reject GCC 14's. Both
  simulator flows are verified on an RHEL 8.10 node as well (every flow links the OS's shared Boost named by the setup script, and the VCS link
  keeps make's jobserver away from VCS's internal make).
- **VCS, automated:** `make USE_VCS=1 VL_DUT=1` builds the model once and links one short VCS snapshot per DUT topology
  (whole design, sub-block, tandem). VCS elaborates the generated HDL wrapper as the design and the SystemC testbench
  instantiates it through VCS's SystemVerilog-in-SystemC mechanism. Verif, tandem and sub-block tests pass on the real RTL.
  The full debayer regression runs under VCS through a small dispatcher that picks the snapshot from the test's own
  `--vlInst/--vlType/--vlTandem` arguments, so the regression definitions are unchanged. `make regr_vcs` passes 44 of 44 tests (build 3 min, run
  19 min at three jobs). The site holds three VCS runtime licences, so the session file runs three jobs; an earlier eight-job pass lost
  five tests to licence queuing, nothing functional.
- **Xcelium, automated:** `make USE_XCELIUM=1` does the same with `xrun`: one snapshot per topology (elaborated in parallel) and a
  run script with the same command line as the other flows, in its own `build_xrun` directory so both simulators' snapshots coexist.
  `make regr_xcelium` passes 44 of 44 tests (run 10 min at six jobs). One Xcelium-specific rule surfaced: the snapshot fixes the whole
  SystemC object set, so a model/model tandem test needs its own snapshot (three extra, shared with VCS through one topology list).
  Cadence's SystemC kernel is binary-only and needs no rebuild.
- **Generator:** arch2code now evaluates the DUT boundary pin widths at database creation and emits, per HDL top, the VCS port
  map and the Xcelium foreign-module shell under `.gen/vl`. Sub-project text stays stable when a parent adds a variant, the same
  way the registrars are handled. (Implementation complete, coordinator verification pending.)
- **Performance:** Verilator 5.038 also builds and runs on the farm host with the same Clang 18 recipe, so the three flows are
  measured on one machine, same tests, low verbosity, user CPU seconds:

  | Test (synthetic data) | Verilator | VCS | Xcelium |
  |---|---|---|---|
  | model only, no RTL | 8.7 | 12.2 | 10.6 |
  | debayer verif | 30.8 | 91.0 | 69.7 |
  | debayer verif tandem | 40.7 | 108.2 | 84.1 |
  | debayer.u_preprocess verif | 56.3 | 87.4 | 114.2 |

  Verilator compiles the RTL to C++ and leads the event-driven simulators as expected: on the whole design VCS is about 3x and
  Xcelium about 2.3x Verilator; on pure SystemC the VCS kernel is about 1.4x. DUT selection is construction-time only, so the flow
  itself adds no per-cycle overhead.

  Whole debayer regression (44 tests, same host, same day):

  | Flow | Result | Concurrent jobs | Limit on jobs | Wall time | Total CPU |
  |---|---|---|---|---|---|
  | Verilator | 44 / 44 pass | 6 | none (cores only) | 5 min 19 s | 23 min 53 s |
  | VCS | 44 / 44 pass | 3 | 3 VCSRuntime_Net licences at the site | 19 min 20 s (+ 2 min 54 s snapshot build) | 50 min 00 s |
  | Xcelium | 44 / 44 pass | 6 | `Xcelium_Single_Core`: 651 issued site-wide, about 20 to 30 free at the time (5280@lrd-virtlic-ha-01b) | 9 min 40 s (+ 3 min 49 s snapshot build, elaborations in parallel) | 43 min 21 s |

  With eight VCS jobs, five tests queued for a licence for the full 900 s timeout, so the VCS session file is fixed at three jobs.
- **Design decisions:** both simulators fix the SystemC topology in the snapshot, so "runtime DUT selection" is delivered as one
  snapshot per topology chosen at run time by the dispatcher. Generic controls live in the builder makefiles, Lattice farm specifics
  (Clang 18 path, tools prefix, Xcelium install, licence servers, OS Boost library) come from the farm setup scripts; the pro layer
  requires them without defaults, and defaults describing the container stay in base. SystemC 3.0.1 remains an acceptable
  later target for both simulators.

**Open items**

- Combined tree verified (VCS 93.9 s, Xcelium 70.1 s on the whole-design verif test). Rule: one VCS build or regression at a time
  per rundir, because concurrent VCS builds share the compile database.
- Deployment dependency (2026-09-17): the committed tree requires setup-scripts revision 3, staged under
  `/ldc/projects/qistor/users/atomlin/setup-proposed/` (README.txt there). The installed `/ldc/projects/qistor/setup/` is
  owned by another account and is not group-writable, so the install (copy the eight files) and the later removal of
  `libboost_program_options.a`, `libboost_system.a` and `libboost_stacktrace_basic.a` under `A2C_TOOLS_LOCAL/lib` are requests to
  that owner. Until then a farm build stops at `a2cProEnv: A2C_TOOLS_LOCAL is not set` unless the staged scripts are sourced directly.
- The plain (non-simulator) farm flow still selects `g++` (`USE_GCC := 1` in `a2cProEnv.mk`) and fails on GCC 13.2's
  `recursive lazy load` module defect; the recipe's `USE_GCC= CXX=<Clang 18 wrapper>` override is the workaround. Honour
  `A2C_CLANG` there too (already in the section 5 follow-ups).
- Xcelium elaborates the HDL wrappers a topology does not use as idle top-levels; harmless for debayer, a memory concern at
  SoC scale. Candidate fix: compile only the topology's wrapper from an instance-to-top mapping in the build manifest.
- SystemC 3.0.1 convergence; pro RTL library items (`rdyVldBurstFifo.sv`,
  `flops.sv` FPGA macros under Xcelium); refresh `docs/vcs-build.md`.
- Clean up `DUT_TOPOLOGIES` (owner request, 2026-09-17). The nine-entry hand-maintained list in `rundir/Makefile` duplicates
  the `--vlInst/--vlType/--vlTandem` combinations already present in the regression JSON and must be kept in step by hand;
  drift only surfaces as a `dutRun.py` "no snapshot" failure. Replace it with a derived list (from the regression file, or
  from the manifest's instance-to-top mapping, which the idle-top item above also needs) so the project Makefile carries no
  topology list.

---

## 1. Summary of findings so far

| # | Toolchain | Plain model build (`make`) | VCS flow (`make USE_VCS=1 all`) | Verdict |
|---|-----------|----------------------------|----------------------------------|---------|
| 1 | GCC 13.2.0 (VCS_GNU, default `g++`) | FAIL `recursive lazy load` on `debayer_tbIncludes.cppm`, deterministic (serial and parallel) | not applicable (VCS flow uses Clang) | unusable for module units, confirms `vcs-build.md` §5.D |
| 2 | Clang 16.0.0 (`/tools/dist/llvm-project`, the `A2C_CLANG` default) | not tried | FAIL: ODR/GMF errors in `--precompile` of every block module | regressed since 2026-07-07 (see §3.2) |
| 3 | GCC 14.2.1 (`/opt/rh/gcc-toolset-14`, new on the farm since July) | FAIL two ways (see §3.3) | not tried | unusable for module units |
| 4 | Clang 18.1.8 (LLVM prebuilt, installed §4) + GCC 13.2 libstdc++ | **PASS**, simulation runs, `No error` | **PASS**, VCS links, simulation runs under the VCS kernel, `No error` | **adopted** |

Key constraints that fall out of this:

- The C++ side must be compiled by Clang >= 17 (C++20 named modules; `-std=c++23`). No GCC on this farm can compile the
  generated module units. Clang 16 no longer can either for the current generator output.
- The standard library must be GCC 13.2's libstdc++ (VCS_GNU `gcc-13.2.0_64-shared`) because VCS's
  `libsystemc.so` (`systemc234-gcc13`) requires `GLIBCXX_3.4.32` and `GLIBCXX_3.4.30` symbols. Linking against the
  gcc-toolset-14 libstdc++ (system RHEL9 `libstdc++.so.6` plus nonshared archive) fails on those symbol versions.
- Boost: every farm flow links the OS shared `program_options` library named by `BOOST_LIBS` (setup script, per OS: RHEL 9 1.75,
  RHEL 8 1.66) with header-only stacktrace; the site headers (Boost 1.74) stay, the static site libraries are unused (3.40). The
  Clang-driven plain-flow link still needs `-fno-pie -no-pie`: the VCS_GNU g++ 13.2 defaults to non-PIC code and compiles the
  Verilator runtime and verilated library, so a PIE final link fails on those objects.

---

## 2. Environment facts (2026-09-15)

- Host: RHEL 9.6 (`5.14.0-570.62.1.el9_6`), glibc 2.34, NFS home. `LDC_RHEL_ENV=1`, `VCS_HOME=/tools/dist/synopsys/VCS/W-2024.09-SP2`.
- Python 3.10.13, PyYAML 6.0.3, Jinja2 3.1.6, GNU Make 4.3, Verilator 5.038. `make db` / `make gen` run cleanly.
- `gcc`/`g++` on PATH: VCS_GNU 13.2.0 (`/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared`).
- Other compilers: gcc-toolset-13 (13.2.1), gcc-toolset-14 (14.2.1) under `/opt/rh`; Clang 16 at
  `/tools/dist/llvm-project/build/bin/clang++`. `/tools/dist/llvm-project-old` is empty. No GCC 15, no dnf `gcc-toolset-15`.
- Container tooling: `podman` present, `docker` absent, no local `a2c-dev` image. Not used (user decision).
- Internet: GitHub and ftp.gnu.org reachable from the host (used to fetch the Clang 18 tarball).
- SystemC for VCS: `SYSTEMC_INCLUDE` overridden by `a2cProEnv.mk` to the patched
  `/ldc/projects/qistor/tools/local/include/vcs/systemc234`; `SYSTEMC_LIBDIR` is VCS's `systemc234-gcc13/lib-linux64`.
- VCS SystemC libraries per release (`$VCS_HOME/etc/systemc/accellera_install`): W-2024.09-SP2 (current `VCS_HOME`) has
  `systemc23{2,3,4}-gcc{6,7,9,12,13}` only; **X-2025.06-SP1-1, X-2025.06-SP2-5 and Y-2026.03-1 add `systemc301-gcc12` and
  `systemc301-gcc13`.** VCS_GNU X-2025.06 provides gcc 13.2.0 only (no 14). So SystemC 3.0.1 with the GCC 13 ABI is available
  for VCS by moving `VCS_HOME` to X-2025.06 or later, and for Xcelium via `-sc_301` (§3.8).
- Xcelium: PATH `xrun` is an LSF-submitting wrapper (`/lsc/ldp/release/latest/wrappers/xrun`). Installs:
  `/tools/dist/cadence/XCELIUM/XCELIUMMAIN26.03.002` (latest, bundled cdsgcc 9.3 and 12.4),
  `/tools/dist/cadence/XCELIUMML/XCELIUMML25.03.001`, `XCELIUMML24.09.007` (`latest` link).

---

## 3. Experiment log

### 3.1 Stale manifest after container build (fixed)

- Symptom: `make db` -> `No rule to make target '/work/ws/debayer/builder/interfaces/apb/apb_if.yaml'`.
- Cause: `.gen/build.mk` and `debayer.db` were produced inside the container where the repo is mounted at `/work`;
  the manifest stores absolute YAML paths.
- Fix: `make clean` from `rundir`, then `make db`, `make gen`. Both clean; `make gen` changed no tracked files.
- Side effect: `make clean` deletes `rundir/build/run` and `rundir/build/vl`. Note for anyone switching between
  container and host: always `make clean` when the mount path changes.

### 3.2 Clang 16 in the VCS flow (regressed)

- Command: `make USE_VCS=1 -j8 all` (selects `A2C_CLANG` default = Clang 16, `CPP_STD=c++2b`, `-nostdinc++ -isystem` to VCS_GNU gcc 13 headers).
- Result: every block module `--precompile` fails, e.g.
  `stl_pair.h:305:7: fatal error: 'std::pair<...trackerBase...>::pair' from module 'debayer_apb_decode.base.<global>' is not present in definition of 'std::pair<...>' provided earlier`
  and `bitTwiddling.h:13:20: fatal error: 'findNextPowerOf2Constexpr' has different definitions in different modules; definition in module 'debayer.<global>' first difference is function body`.
- Reading: Clang 16 GMF (global module fragment) merging defects. Clang 18 enables `-fskip-odr-check-in-gmf` by default
  (visible in its `-cc1` line) and compiles the same units cleanly. `vcs-build.md` §6 validated Clang 16 on 2026-07-07
  against older generator output; the builder `feature/125` changes (owner-qualified Config modules, struct equivalence)
  produce more/larger GMF-heavy units and expose the Clang 16 defects.

### 3.3 GCC 14.2.1 (gcc-toolset-14)

- Serial and parallel, clean build tree, all combinations of `-g`/`-g0`, `-O0`:
  - with `-fno-module-lazy` (the flag `a2c-systemc.mk` adds for GCC): compiling `debayer_tbIncludes.cppm` fails
    `debayer: error: failed to read compiled module cluster 2636: Bad file data` when importing `debayer`.
  - without it: writing the `debayer` CMI fails `internal compiler error: in write_location, at cp/module.cc:16280`.
- The three leaf units (`shared_typesIncludes`, `isp_typesIncludes`, `debayerIncludes` with `-fno-module-lazy`) compile; the
  defect is in GCC's serialization of the large `debayer` interface. Matches open GCC module bugs
  (PR 99426 "failed to read compiled module cluster: Bad file data", PR 104919, meta-bug PR 103524).
- Verdict: no GCC available here can be used. GCC 15 was not tested (not installed, not in dnf).

### 3.4 Clang 18.1.8 prebuilt, plain model flow (PASS)

- Source: `https://github.com/llvm/llvm-project/releases/download/llvmorg-18.1.8/clang+llvm-18.1.8-x86_64-linux-gnu-ubuntu-18.04.tar.xz`
  (1.0 GB, glibc >= 2.27 so it runs on RHEL9's 2.34; harmless `libtinfo.so.5: no version information` warning).
- Iteration 1: `--gcc-install-dir=/opt/rh/gcc-toolset-14/root/usr/lib/gcc/x86_64-redhat-linux/14`:
  all 71 TUs compile; link fails `relocation R_X86_64_32 against .rodata.str1.8 can not be used when making a PIE object`
  (static Boost). Adding `-fno-pie -no-pie` then fails
  `libsystemc.so: undefined reference to std::ios_base_library_init()@GLIBCXX_3.4.32` (toolset-14 links the RHEL9 system libstdc++).
- Iteration 2 (**working recipe**), from `rundir`:

  ```
  CL="/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8/bin/clang++ \
      --gcc-install-dir=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0 \
      -fno-pie -no-pie"
  make -j8 USE_GCC= CXX="$CL"
  ./build/run debayer --verbosity=medium
  ```

  `USE_GCC=` (empty, on the command line) overrides the `USE_GCC := 1` that `a2cProEnv.mk` forces for the non-VCS
  flow, selecting the Clang module rules (`--precompile`, `-fmodule-file=`). Build 52 s wall (-j8). Run: 9.0 s,
  two frames, `No error`, exit 0. The generated model binary is not the VCS one; both land at `rundir/build/run`.

### 3.5 Clang 18.1.8 in the VCS flow (PASS)

- Command, from `rundir` (`A2C_CLANG` is `?=` in `a2cProEnv.mk`, so the command line wins):

  ```
  make USE_VCS=1 -j8 all A2C_CLANG=/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8/bin/clang++
  ```

  73 s wall. All module units and TUs compile with `-std=c++2b -nostdinc++ -isystem <VCS_GNU gcc13 c++ headers> --gcc-toolchain=...`;
  `vcs +vcs+lic+wait -full64 -sysc=234 -race -kdb -debug_access ... sc_main -o build/run` links (VCS's g++ 13.2 does the link,
  `-Wl,-rpath,<gcc-13.2.0_64-shared>/lib64`). Clang objects are ABI-compatible with VCS's gcc13-built `libsystemc234-gcc13-64.a`.
- First run failed at time 0: `[Q_ASSERT] Attempted to create an instance debayer of an unregistered block type debayer_verif`.
  Cause: `rundir/Makefile` sets `VL_TYPE=verif` for `USE_VCS`, but `a2c-systemc.mk` only defines `VERILATOR` and links
  `libdebayervl_s_wrap.a` when `USE_VCS` is **unset**, and `debayerVlRegistrar.cpp` registers `debayer_verif` only `#ifdef VERILATOR`.
  Under VCS the `--vlType/--vlInst` runtime options are compiled out (`simController.cpp`, `#ifndef VCS`); the values are the
  compile-time `-DVL_TYPE/-DVL_INST` defines. This is exactly the open `VL_DUT` question of `vcs-build.md` §9.
- Rebuilt with `VL_TYPE=model` on the make command line (`make USE_VCS=1 VL_TYPE=model -j8 all A2C_CLANG=...`):
  run completes under the VCS SystemC kernel, `V C S   S i m u l a t i o n   R e p o r t`, CPU 10.6 s, `No error`, exit 0.
- Verdict: **compile with Clang 18, link and run with VCS works.** What remains for VCS is the DUT strategy (§5).

### 3.6 Xcelium reconnaissance (facts gathered, experiments delegated)

- `XCELIUMMAIN26.03.002/Linux/tools`: `cdsgcc/gcc/{9.3,12.4}` (Cadence builds of g++ 9.3.0 and 12.4.0, shipping
  `libstdc++.so.6.0.28` / `.31`). `xrun -helpall` still documents `-gcc_vers <9.3|6.3>`; also `-gnu`, `-Wcxx,<arg>`,
  `-Wld`, `-L<dir>`, `-l<lib>`, `-sc_main`, `-iusld`.
- SystemC library: `tools/systemc/lib/64bit/libsystemc_sh.so` (and `libsystemc_ar.a`), `SC_VERSION_ORIGINATOR "Cadence"`,
  `SYSTEMC_VERSION 20181013` (2.3.3 vintage). Maximum libstdc++ symbol version it needs: `GLIBCXX_3.4.30` (GCC 12).
  `tools/systemc/src` exists but appeared empty from this account; `tools/systemc/{files,gnu,lib/compat}` present (agent verifying).
- Clang 18 + GCC 13.2 libstdc++ compiles `shared_typesIncludes.cppm`, `isp_typesIncludes.cppm`, `debayerIncludes.cppm`
  (`--precompile`) and `logging.cpp` against **Xcelium's** SystemC headers (`-I tools/systemc/include`) with no errors.
  So the header side is fine; the open questions are link and runtime (libstdc++ 12 vs 13) and how xrun accepts prebuilt objects.
- Clang 18 against cdsgcc 12.4's libstdc++: `<format>` is absent (GCC 13 feature). The a2c make system has an fmt shim
  (`C_STD_VER != c++23` -> `-lfmt`; `/ldc/projects/qistor/tools/local/lib64/libfmt.a` exists) if a GCC-12 ABI target is required.
- Documentation is HTML: `Linux/doc/{xceliumSCUG,XceliumSC_Ref,xmscref,xmscsim,xmscqrg}`.

### 3.7 Native VCS compile/elaboration of the debayer RTL (PASS, agent experiment)

- Working command (scratch dir, absolute paths, no project files touched):

  ```
  vcs +vcs+lic+wait -full64 -sverilog -timescale=1ns/1ps \
    -F $REPO/builder/common/systemVerilog/a2c.f -F $REPO/rtl/rtl.f \
    $REPO/rtl/debayer.sv $REPO/rtl/debayer_regs.sv $REPO/rtl/interpolate.sv $REPO/rtl/preprocess.sv \
    +incdir+$REPO/verif $REPO/verif/debayer_default_hdl_sv_wrapper.sv \
    -top debayer_default_hdl_sv_wrapper -ignore initial_driver_checks -kdb -debug_access -l vcs_rtl.log
  ```

  rc 0, 0 errors, 1 warning (`TMBIN` at `rtl/debayer_regs.sv:108`, 32-bit literal into a 2-bit field, generated register
  code, template fix later). Compile 0.5 s, elab 0.17 s. `simv` smoke-runs. Adding `-sysc=234` is accepted
  (`Note-[SC-VCS-NO-SYSC] No SystemC models found`), so the co-simulation option is licensed and usable.
- File-list facts: `rtl/rtl.f` is relative to `rtl/` and lists only the four packages plus `+incdir+.`/`+libext+.sv`; the
  four module files come from the manifest variable `A2C_SV_FILES` in `.gen/build.mk` and must be passed explicitly (as the
  Verilator lint rule does). `builder/common/systemVerilog/a2c.f` provides the `-y` library dirs for every `*_if.sv` and
  `flops.sv`/`asserts.svh`; it must be passed with `-F` (paths relative to its own directory). Only `memory_dp` is pulled
  from the library search; no pro-layer RTL modules are instantiated.
- `debayer` cannot be a bare top: interface-typed ports (`apb_if`, `rdy_vld_if`) and six parameters without defaults.
  The generated `debayer_default_hdl_sv_wrapper` binds the parameters and flattens the interfaces, so it is the natural
  HDL top for VCS and Xcelium alike. `verif/debayer_hdl_sv_wrapper.svh:152` already contains an `` `ifdef VCS ``
  `$fsdbDumpvars` block, which needs `-kdb -debug_access`.
- Parameters bound by the default wrapper: `BITS_PER_PIXEL_COLOR=8`, `PIXELS_PER_CLOCK=4`, `HORIZONTAL_SIZE=3840`,
  `VERTICAL_SIZE=2160`, `DEBAYER_DIMENSION=5`, `DEBAYER_ALGORITHM=4`.
- Boundary signal set exposed by the wrapper (20 signals): `video_raw_stream_{vld,data[34:0],rdy}`,
  `video_rgb_stream_{vld,data[98:0],rdy}`, `cpu_apb_reg_{paddr[31:0],psel,penable,pwrite,pwdata[31:0],pready,prdata[31:0],pslverr}`,
  `clk`, `rst_n`. This is the pin-level contract a native VCS/Xcelium SystemC-side wrapper must drive/sample.

### 3.8 Xcelium 26.03 documentation and library review (agent research, read-only)

Extracted, tag-stripped doc pages are in the session scratch area (`xcelium-docs/<docset>/<page>.txt`). Facts:

- **Compilers.** Bundled `cdsgcc/gcc/{9.3,12.4}`; SystemC libraries per GCC under `tools/systemc/lib/64bit/gnu/{9.3,12.4}` and
  `tools/systemc_301/lib/64bit/gnu/{9.3,12.4}`. `xrun -gcc_vers` help text is stale (says 9.3 or 6.3). xmsc "does not compile
  SystemC source code into object form (rather it invokes a specified compiler)"; knobs are `-compiler <path>`, `-Wcxx,`,
  `-Wld,`, `-manual` (only user CFLAGS; default adds `-c -fPIC -Wall`). Requirement: `-D_GLIBCXX_USE_CXX11_ABI=1` (the shipped
  libraries use the cxx11 ABI). Platform page: "You must compile all of your C++ and SystemC code using a single compiler
  version. Do not mix object files produced by different compilers." **No page mentions Clang or third-party compilers.**
- **Prebuilt objects are accepted.** `xmsc_run *.cpp file1.o -genobj allobjects`; dynamic link of user objects with
  `libsystemc_sh.so libxmscCoSim_sh.so libxmscCoroutines_sh.so`; static relink of `xmelab_sc/xmsim_sc` from `libsystemc_ar.a`,
  `sc_fpi_xm.o`, `xmscpi.o`; `xmelab -loadsc model.so model_top` for SystemC-only. `xcelium_checklib.pl` flags a non-Cadence
  libstdc++ as an error ("You must use the libstdc++ library from Cadence install location only").
- **No rebuildable SystemC source.** `tools/systemc/src` and `tools/systemc_301/src` are empty directories; `files/install`
  holds only `.ins` files; kernel is binary-only (`libsystemc_sh.so`, `libsystemc_ar.a`, `sc_main.o`, `xmscpi.o`, `sc_fpi_xm.o`,
  `qt*.o`). Rebuilding Cadence's kernel with another compiler is not possible; "recompile SystemC" is therefore not a route
  for Xcelium (it is a route only for a simulator-independent library, which Xcelium co-simulation does not use).
- **SystemC versions.** Default `tools/systemc`: `SYSTEMC_2_3_4`, `IEEE_1666_SYSTEMC 201101L`, `SC_VERSION_ORIGINATOR "Cadence"`
  (2.3.4 features since Xcelium 23.09). Alternate `tools/systemc_301` (`-sc_301`): Accellera 3.0.1 based, C++17 baseline, RHEL8+,
  must not be mixed with 2.3.4. `sc_cmnhdr.h` sets `SC_CPLUSPLUS __cplusplus`; dynamic processes available. No documented
  `-std` ceiling; C++20/23 is not mentioned. Our probe (§3.6) shows Clang 18 `-std=c++23` compiles the a2c module units
  against the 2.3.4 headers.
- **libstdc++ runtime.** Cadence ships `tools/lib/64bit/libstdc++.so.6` (max `GLIBCXX_3.4.31`, GCC 13.1 era). `libsystemc_sh.so`
  (gnu/12.4) needs up to `GLIBCXX_3.4.30`. Objects built against GCC 13.2 headers may reference `GLIBCXX_3.4.32`
  (`std::ios_base_library_init`, seen in the VCS link) and would not resolve against Cadence's runtime unless a newer
  libstdc++ is loaded first (`xcelium_checklib.pl` warns) or the objects are restricted to <= 3.4.31 symbols. `-iusld`
  prepends `xmroot/tools/lib` to `LD_LIBRARY_PATH`; snapshots record `LD_LIBRARY_PATH` and error if it differs at `xmsim` time.
- **sc_main mode is supported** (`-sc_main`; SystemC-only design without HDL tops assumes sc_main). Constraints: statements before
  the first `sc_start` execute at `xmelab` time; xmelab exits sc_main by throwing `xmsc_elab_exception`, so a `catch(...)` in
  sc_main must add `catch(xmsc_elab_exception x) { throw; }` -- **relevant: a2c `builder/common/scmain/main.cpp` wraps the body
  in `try`/`catch`**. Objects are rooted under an `sc_main.` hierarchy prefix (a2c already sets `setHierarchyPrefix("sc_main")`
  for VCS). sc_main return value becomes the tool exit status; `argv[0]` is `xmsim`.

### 3.9 DUT-boundary analysis: how the RTL enters the SystemC testbench today (agent analysis, read-only)

Three generated layers per block (debayer, preprocess, interpolate), emitted by
`builder/base/templates/systemc/module_hdl_wrapper.py` (SC side), `builder/base/templates/fileGen/fileGen.py:292-430`
(SV side) and `builder/base/templates/systemc/vlRegistrar.py` (registration):

- `verif/<blk>_hdl_sv_wrapper.svh`: parameterized SV body with **pin-level ports**; instantiates the a2c SV interfaces,
  connects them to pins with `assign #0`, instantiates the real RTL top. VCS-only `$fsdbDumpvars` under `` `ifdef VCS ``.
  **Simulator-neutral, reusable unchanged.**
- `verif/<blk>_default_hdl_sv_wrapper.sv`: trampoline that pins parameters to a variant and instantiates the body;
  parent-qualified trampolines (e.g. `p7_debayer_c18_debayer_preprocess_default_hdl_sv_wrapper`) serve sub-block verif.
  These five tops are `A2C_VL_TOPS` in `.gen/build.mk`. **Reusable unchanged as the VCS/Xcelium HDL top(s).**
- `verif/<blk>_hdl_sc_wrapper.h`: `template <DUT_T, Config> class <blk>_hdl_sc_wrapper : sc_module, blockBase, <blk>Base<Config>`.
  Owns `sc_clock clk (1 ns, start 3 ns)` and `sc_signal<bool> rst_n` (released at 5 ns), one BFM per a2c port
  (`rdy_vld_dst_bfm`, `rdy_vld_src_bfm`, `apb_dst_bfm`, `status_dst_bfm`) and one `*_hdl_if` signal bundle
  (`sc_signal<bool> vld/rdy`, `sc_signal<sc_bv<W>> data`). Constructor: `dut_hdl = new DUT_T("dut_hdl")` then binds pins by
  name. Only Verilator-specific code: `#ifdef VERILATOR vl_trace(...)`. The template already has a dormant
  `#if !defined(VERILATOR) && defined(VCS)` branch (`module_hdl_wrapper.py:193-206, 219-226, 258-264`) that includes
  `<svModule>.h` and instantiates the VCS-generated class, but only for non-templated wrappers; all three wrappers here are
  Config-templated, so `DUT_T` comes from the registrar.
- `registrar/<blk>VlRegistrar.cpp`: whole TU `#ifdef VERILATOR`; includes `V<top>.h`; registers `"<blk>_verif"` producing
  `<blk>_hdl_sc_wrapper<V<top>, <Config>>`. **The only place the Verilator class name appears on the SystemC side.**
- Selection: `--vlInst X --vlType verif [--vlTandem]` -> `instanceFactory::registerInstance` (`simController.cpp:66-74`).
  Tandem creates a `verif` and a `model` child (`base/<blk>Tandem.cpp`). Under `-DVCS` these are compiled out
  (`simController.cpp:33-38`) and pinned by `-DVL_INST/-DVL_TYPE/-DVL_TANDEM` (`rundir/Makefile:19-24`, `main.cpp:66-75`).
- Build: `VL_DUT=1` -> `a2c-vl-wrap.mk` verilates each top with `verilator -sc -sv --pins-bv 2 --no-timing`, archives into
  `libdebayervl_s_wrap.a`; `a2c-systemc.mk:170-181` adds `-DVERILATOR`, include dirs and the lib, all under `#ifndef USE_VCS`.
  No `eval()`/manual clock stepping anywhere: Verilator `-sc` is already driven by `sc_clock`, so the design is already
  event-driven-simulator shaped. `main.cpp` Verilator-only code: `vl_tracer` (VCD), coverage.
- Regression launcher (`builder/base/regrLauncher/`): `build.command` runs once, `run.command` + nested `args+` per test,
  `labels+` filtering (`mdl`, `hdl`, `tandem`, `delay`, `unstable`), rules in `default.json`. **Nothing is simulator-aware.**
  All `hdl_tests` pass `--vlType/--vlInst/--vlTandem` at runtime, which the VCS build compiles out.

Reuse/replace summary: reuse `.svh` bodies, trampolines, `rtl.f`, `a2c.f`, BFMs, `_hdl_if` bundles, the `_verif/_tandem`
factory scheme, `<blk>Tandem`. Per simulator: only the `DUT_T` class and the TU that registers it, plus the build recipe.

Risks identified: (1) runtime option pinning under VCS (nine (inst,type,tandem) combinations would need nine snapshots);
(2) VCS port type mapping (`sc_bv<W>`/`bool` vs VCS default `sc_lv`/`sc_logic`, needs `-sc_portmap`); (3) only trampolines
can be tops, so the multi-top scheme stays; (4) `assign #0` + `sc_signal` delta behaviour differs from Verilator's cycle
model, watch `rdy_control_thread` (`rdy_vld_bfm.h:98-100`) and `apb_dst_bfm` `pready` sampling; (5) no DPI in project RTL;
`$fsdbDumpvars` needs Verdi PLI (VCS has it linked) and an Xcelium equivalent; (6) build cost of five tops per snapshot
versus the 120 s build timeout in `regr_debayer.json`; (7) `a2c-vl-wrap.mk:16` compiles the verilated lib with Verilator's
own `g++` (`-std=$(C_STD_VER)`), which is why the container was the only Verilator path on the farm.

### 3.10 Xcelium 26.03 links and runs Clang 18 objects (PASS, agent experiment)

- Direct binary `/tools/dist/cadence/XCELIUM/XCELIUMMAIN26.03.002/Linux/tools/bin/xrun` (26.03-s002) works on the RHEL9 host
  without the LSF wrapper. The wrapper's `xrun -K` returns immediately after submission, so it is unsuitable for scripted flows.
  `env.csh` in the install root is a Specman script and is not needed. Required environment: `LM_LICENSE_FILE` with the full
  site list (the wrapper injects it via LSF; the Xcelium feature is served by the `5280@` servers):
  `1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b:29000@ldc-hw-eda:1725@ldc-virtlic01:5280@lrd-virtlic-rh8-01:5280@lrd-virtlic-ha-01a:5280@lrd-virtlic-ha-01b:5056@lrd-virtlic-rh8-01`.
  No `LD_LIBRARY_PATH` needed.
- Working recipe (hello-world sc_main plus the project's `shared_typesIncludes.cppm` module unit), flags mirrored from what
  xmsc passes to its own g++:

  ```
  T=/tools/dist/cadence/XCELIUM/XCELIUMMAIN26.03.002/Linux/tools
  G13=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0
  CADFLAGS="-DNCSC -DCADENCE -DLNX86 -DXMSC -D_GLIBCXX_USE_CXX11_ABI=1 -I$T/systemc/include -I$T/systemc/include/cci \
            -I$T/systemc/include/factory -I$T/systemc/include/tlm2 -I$T/include -I$T/inca/include -fPIC"
  clang++ --gcc-install-dir=$G13 -std=c++23 -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES \
          -Wno-undefined-var-template -Wno-deprecated-declarations $CADFLAGS -c hello.cpp -o hello.o
  clang++ ... --precompile -x c++-module shared_typesIncludes.cppm -o shared_types.pcm
  clang++ ... -c shared_types.pcm -o shared_types.module.o
  xrun -64bit -sysc -sc_main -gcc_vers 12.4 hello.o shared_types.module.o -l run.log
  ```

  Prebuilt `.o` files on the xrun command line are accepted directly (no archive, no `-L/-l`). xmsc links them with cdsgcc 12.4
  g++ into `librun.so`, xmelab elaborates, xmsim runs: timed hello lines, `sc_stop`, exit 0. Each xrun stage 1-2 s.
- **ABI measurement.** Objects built against GCC 13.2 headers make `librun.so` require up to `GLIBCXX_3.4.31`. xmsim loads
  `tools/lib/64bit/libstdc++.so.6` (confirmed with `LD_DEBUG`), which provides `GLIBCXX_3.4.31`; cdsgcc 12.4's `libstdc++.so.6.0.31`
  does too; `libsystemc_sh.so` needs only 3.4.30. **GCC 13.2 headers are inside Xcelium's runtime envelope; no rebuild needed.**
  Constraint: stay on GCC 13.2 headers. GCC 14 headers (`GLIBCXX_3.4.32/33`) would not resolve. cdsgcc 12.4 headers are not
  an option (no `<format>`, project needs C++23).
- Expected noise: Clang `-Wundefined-var-template` on Cadence's `sc_signal.h` statics (suppress), "unused during compilation"
  for `-I` on the `.pcm` -> `.o` step.
- Verdict: **compile with Clang 18 + GCC 13.2 libstdc++, link and run with Xcelium works**, the same C++ objects recipe as for VCS
  apart from Cadence's defines/includes. What remains for Xcelium is the foreign-module DUT boundary (§5 item 4).

### 3.11 Phase 2 (started 2026-09-15): native RTL simulation under VCS

- User context: VCS previously ran and simulated, and the main problem was that VCS does not support run-time elaboration
  of the SystemC/HDL hierarchy; the compile-time switches (`-DVCS`, `-DTESTBENCH`, `-DVL_INST`, `-DVL_TYPE`, `-DVL_TANDEM`,
  `USE_VCS`) were introduced to pin the DUT selection at build time and may now be broken.
- Delegated: (a) prototype of the SV-in-SC DUT (vlogan `-sysc -sc_model` + portmap, hand-written registrar TU, VCS link, run);
  (b) read-only history search for the original run-time-elaboration problem and an audit of every VCS-conditional path.
- Results are appended below as they arrive.

### 3.12 History audit of the VCS switches and the "run-time elaboration" limitation (agent research, read-only)

**What the record says.** No commit message or document states the limitation; the 2025 commits are terse
(`base b562408` 2025-08-25 "#34 initial support vcs compilation alternative to verilator"; `base f238e32` 2025-08-27 "remove vcs
specific code from common makefile"; `debayer 7f17d42` 2025-08-26 "Initial commit for compilation/simulation with vcs";
`debayer 7dcbc35` 2025-08-27; `pro f73feaa` 2026-07-07 "#116 VCS compile"). The only mechanism-level comment is
`synchLock.h:105` about VCS prefixing `sc_main.` to instance names (already handled by `setHierarchyPrefix("sc_main")`).

**What the limitation reduces to.** It is not a SystemC-kernel limitation: VCS runs `sc_main` and constructs SystemC modules
dynamically (proven in §3.5). The constraint is on the SV side of the boundary: every `vlogan -sc_model <module>` shell class and
its VCS-elaborated HDL partition must be named at vlogan/vcs time, so the *set* of RTL DUTs in a snapshot is fixed at build time.
Verilator has the same property but arch2code hides it behind a C++ class (`V<top>`) selected by the runtime factory. The 2025
answer was to replace the runtime `--vlInst/--vlType/--vlTandem` options with `-D` macros: one snapshot per (inst, type, tandem)
triple. The alternative, compatible with the runtime factory, is to `-sc_model` **all five** `A2C_VL_TOPS` into one snapshot and
register all five; only the instantiated one is used. This is the approach phase 2 pursues (§3.11).

**The earlier VCS flow existed.** `debayer 7f17d42` added `verif/vl_wrap/Makefile` with, under `ifdef USE_VCS`:
`vlogan -full64 -sverilog -F a2c.f -F rtl/rtl.f <wrapper>.sv -sc_model <wrapper> +define+VL_DUT` per `HDL_SV_FILES` (no `-sysc`,
no `-sc_portmap`), target `vcswrap`, dispatched from base `all:` via `ifndef USE_VCS ... else vcswrap`. Removal: `base f238e32`
dropped the dispatch (layering); `base c42b535` (2026-07-22 "#116 remove vl_wrap") rewrote `module_hdl_wrapper.py` into the
`{%- if not is_template %}`-gated form that makes the VCS branch unreachable for templated wrappers; `debayer 8705c83`
(2026-07-26 "#116 working debayer") deleted `verif/vl_wrap/Makefile` and introduced the per-block `*VlRegistrar.cpp`. No portmap
or `syscan` ever existed in history. An orphan copy of the old recipe survives in
`builder/pro/examples/lmmiDemo/verif/vl_wrap/Makefile` (depends on the no-longer-defined `HDL_SV_FILES`).

**Stale or broken VCS-conditional paths today** (file:line):

1. `module_hdl_wrapper.py:201-206, 219-226, 252-258`: VCS branch only inside `{%- if not is_template %}`; all debayer wrappers
   are Config-templated, so unreachable. `DUT_T` comes from the registrar.
2. `vlRegistrar.py:44, 87`: whole TU `#ifdef VERILATOR`, no VCS branch; under `USE_VCS` the three registrar objects are empty TUs,
   so `debayer_verif` is never registered while `rundir/Makefile:24` pins `VL_TYPE=verif` (the §3.5 assertion).
3. `a2c-systemc.mk:305-309`: `all:` runs the Verilator sub-make whenever `VL_DUT` is set, with no `ifndef USE_VCS`; since
   `rundir/Makefile:22` sets `VL_DUT=1` under `USE_VCS`, **the VCS build verilates for nothing**.
4. `a2c-systemc.mk:142-152`: Verilator `obj_dir` and `$(VERILATOR_ROOT)/include` paths leak into every VCS compile (gated on `VL_DUT` only).
5. `rundir/Makefile:33`: `-I$(PROJECT_RUNDIR)/csrc/sysc/include` points at an empty directory (where `vlogan -sc_model` headers would land).
6. `builder/pro/examples/lmmiDemo/verif/vl_wrap/Makefile`: orphan of the 2025 recipe.
7. `simController.cpp:92-97`: `--vlInst/--vlType/--vlTandem/--vlTrace` compiled out under VCS; Boost would reject them as unknown,
   so the regression's 30+ `--vlType ... --vlInst ...` arguments cannot be passed to a VCS binary today.
8. `main.cpp:23-29`: `exit_handler` declared `int`, never returns a value (benign, `exit` is noreturn). `-DVCS` is defined only by
   `rundir/Makefile:32`; base never defines it.

**Factory mechanics relevant to VCS.** `_model`, `_tandem`, `_verif` are runtime string keys over a statically populated map
(`instanceFactory.cpp:13-16, 62-70`); `createInstance` deliberately refuses to fall back to `_model` for a non-model mode
(`:76-78`). Tandem constructs a `verif` and a `model` child through the same factory (`base/debayerTandem.cpp:37-38`). Nothing
here needs to change for VCS if all candidate DUT classes are linked in.

### 3.13 Native RTL simulation under VCS: prototype PASS (verif and tandem)

`R=$REPO`, `S=<scratch>/vcs-dut`, vlogan/vcs run from `$S/an`; Clang 18 as before.

1. C++ objects, from `rundir` (40 s): `make USE_VCS=1 -j8 all A2C_CLANG="$CLANG18 -gdwarf-4"` (tandem: add `VL_TANDEM=1`).
2. Analyze RTL + packages: `vlogan +vcs+lic+wait -full64 -sverilog -timescale=1ns/1ps -F $R/builder/common/systemVerilog/a2c.f -F $R/rtl/rtl.f
   $R/rtl/{debayer,debayer_regs,interpolate,preprocess}.sv +incdir+$R/verif`.
3. Analyze the library units the `-y` search would otherwise supply: `vlogan ... $B/interfaces/{apb/apb_if,rdy_vld/rdy_vld_if,memory/memory_if,status/status_if}.sv
   $B/common/systemVerilog/memory_dp.sv` (`B=$R/builder/base`).
4. SystemC shell of the HDL top, one file per call, explicit portmap:
   `vlogan ... -sc_model debayer_default_hdl_sv_wrapper -sc_portmap debayer_default_hdl_sv_wrapper.map +incdir+$R/verif $R/verif/debayer_default_hdl_sv_wrapper.sv`
   -> `csrc/sysc/include/debayer_default_hdl_sv_wrapper.h`, class with `sc_in<bool>`, `sc_in<sc_bv<35>>`, `sc_out<sc_bv<99>>`, `sc_bv<32>` ports named as the pins.
   **It binds to the existing `debayer_hdl_sc_wrapper<DUT_T,Config>` unchanged.**
5. Registrar TU: `registrar/debayerVlRegistrar.cpp` with the `#ifdef VERILATOR` removed, `#include "debayer_default_hdl_sv_wrapper.h"`
   and `debayer_default_hdl_sv_wrapper` as `DUT_T` in both `registerBlock("debayer_verif", ...)` lambdas; compiled with the make flow's exact
   clang++ line (32 `-fmodule-file=`), `-gdwarf-4`, `-I$S/an/csrc/sysc/include`.
6. Link: the make flow's `vcs +vcs+lic+wait -full64 -sysc=234 -race -kdb -debug_access -ignore initial_driver_checks -timescale=1ns/1ps ... <71 objects> sc_main -o simv`
   with the registrar object swapped. Nothing else added: VCS picks the sc_model from `csrc/sysc/modellist` in the cwd. 7-10 s.
7. `./simv debayer --verbosity=medium`.

Portmap (`name width hdl-type sc-type`, one per line): `video_raw_stream_vld 1 bit bool`, `video_raw_stream_data 35 bitvector sc_bv`,
`video_raw_stream_rdy 1 bit bool`, `video_rgb_stream_vld 1 bit bool`, `video_rgb_stream_data 99 bitvector sc_bv`, `video_rgb_stream_rdy 1 bit bool`,
`cpu_apb_reg_paddr 32 bitvector sc_bv`, `cpu_apb_reg_psel/penable/pwrite 1 bit bool`, `cpu_apb_reg_pwdata 32 bitvector sc_bv`,
`cpu_apb_reg_pready 1 bit bool`, `cpu_apb_reg_prdata 32 bitvector sc_bv`, `cpu_apb_reg_pslverr 1 bit bool`, `clk 1 bit bool`, `rst_n 1 bit bool`.

Workarounds required (all must be built into the flow):
1. **DWARF 4.** VCS W-2024.09's SystemC pre-elaboration (`simv_elab`, `snps::TapiImp::readDwarfInformation`) aborts on Clang 18's default
   DWARF 5 (`DwarfDebugInfoAttribute.cpp:344 Assertion 0 failed`, `Error-[SC-VCS-SYSC-ELAB]`). `-gdwarf-4` on every object fixes it.
2. `vlogan -sc_model` accepts exactly one source file (`Error-[SYSC_MVLOG]`); RTL analysis must be a separate vlogan call.
3. In the vlogan+vcs flow the `-y` dirs from `a2c.f` are not consulted at vcs elaboration (`Error-[SV-UIOT] Undefined interface or type apb_if`),
   vcs rejects parse-only options (`-y`, `+libext`, `+incdir`: `Error-[PRS_OPT]`), and `-F a2c.f` on vcs compiles `flops.sv`/`asserts.svh` out of
   context. Interface and library units must be analyzed explicitly with vlogan.
4. Trampoline port widths are parameter expressions; `-sc_model` cannot evaluate them (`Error-[SC-VDEF-14] No bit width specified`), so widths
   and types must come from the portmap (which is also what selects `bool`/`sc_bv` over `sc_logic`/`sc_lv`).
5. Stale `csrc/` from a failed link causes `Error-[NTMES] No TopModule/Entity supplied`; remove `csrc/` and `AN.DB` and redo steps 2-4.

Results (`-DVL_INST=debayer -DVL_TYPE=verif`, synthetic data): verif -> `INFO: debayer module instantiated`, `Completed frame: 1/2`,
`No error`, exit 0; sim time 4,149,237,000 ps, CPU 208 s, wall 3 m 30 s. Tandem (`VL_TANDEM=1`) -> `Tandem instance tb.debayer initialized`,
two frames, `No error`, exit 0; CPU 230 s, wall 3 m 51 s. Only warnings: `KDB-ELAB-FLV2O`, `KDB-OPTIONS` (Verdi elaboration; may matter for FSDB).
`--verbosity=medium` output (`window_handler` logging) dominates wall time.

Side effects: `rundir/build/debayer.build` and `rundir/build/run` now hold the `VL_TANDEM=1 -gdwarf-4` VCS build (git-ignored). No tracked file
modified. Scratch artifacts under `vcs-dut/` (portmap, registrar source, simv, simv_tandem, logs).

### 3.14 Native RTL simulation under Xcelium: prototype PASS (verif and tandem)

`R=$REPO`, `X=<scratch>/xcelium-dut`, `T=/tools/dist/cadence/XCELIUM/XCELIUMMAIN26.03.002/Linux/tools`, Clang 18.

1. C++ objects: the make flow's Clang lines with `-DVCS -DTESTBENCH -DVL_*`, the VCS/patched SystemC, Verilator and `csrc` includes
   removed, and `-DXCELIUM -DNCSC -DCADENCE -DLNX86 -DXMSC -D_GLIBCXX_USE_CXX11_ABI=1 -fPIC -Wno-undefined-var-template
   -Wno-deprecated-declarations -I$T/systemc/include -I$T/systemc/include/{cci,factory,tlm2} -I$T/include -I$T/inca/include` added.
   Module flow (`--precompile`/`-fmodule-file`) and `-std=c++2b -nostdinc++ -isystem <gcc13 c++ headers>` unchanged. 98 commands, 6 min serial.
2. `q_assert.cpp` compiled without `-DBOOST_STACKTRACE_LINK` (header-only stacktrace; the site static Boost is non-PIC).
3. `main.cpp` + `#ifdef XCELIUM catch (xmsc_elab_exception&) { throw; }` ahead of `catch (std::exception&)` in `try_sc_start`.
4. Registrar TU as in §3.13 but including the foreign-module shell header.
5. Foreign-module shell `debayer_default_hdl_sv_wrapper.h`: `class debayer_default_hdl_sv_wrapper : public xmsc_foreign_module` with
   name-initialised `sc_in<bool>` (`clk`, `rst_n`, `video_raw_stream_vld`, `video_rgb_stream_rdy`, `cpu_apb_reg_{psel,penable,pwrite}`),
   `sc_in<sc_bv<35>> video_raw_stream_data`, `sc_in<sc_bv<32>> cpu_apb_reg_{paddr,pwdata}`, `sc_out<bool>` (`video_raw_stream_rdy`,
   `video_rgb_stream_vld`, `cpu_apb_reg_{pready,pslverr}`), `sc_out<sc_bv<99>> video_rgb_stream_data`, `sc_out<sc_bv<32>> cpu_apb_reg_prdata`;
   `const char* hdl_name() const override { return "debayer_default_hdl_sv_wrapper"; }`. `bit`->`bool`, `bit [N-1:0]`->`sc_bv<N>` is Xcelium's
   default mapping: **no portmap file needed**; no parameters (trampoline pins them); `XMSC_MODULE_EXPORT` not needed in sc_main mode.
6. Run (fresh dir, `LM_LICENSE_FILE` exported as §3.10):

   ```
   xrun -64bit -sv -sysc -sc_main -gcc_vers 12.4 -timescale 1ns/1ps -clean -warn_multiple_driver \
     -F $R/builder/common/systemVerilog/a2c.f -F $R/rtl/rtl.f $R/rtl/{debayer,debayer_regs,interpolate,preprocess}.sv \
     +incdir+$R/verif $R/verif/debayer_default_hdl_sv_wrapper.sv <all .o> \
     -Wld,-L/ldc/projects/qistor/tools/local/lib64 -Wld,/usr/lib64/libboost_program_options.so.1.75.0 -Wld,/usr/lib64/libboost_system.so.1.75.0 \
     -Wld,-lopencv_core -Wld,-lopencv_imgproc -Wld,-lopencv_imgcodecs -Wld,-lstdc++fs -Wld,-ldl -Wld,-lrt -Wld,-lpthread \
     +systemc_args+debayer +systemc_args+--verbosity=low +systemc_args+--vlInst=debayer +systemc_args+--vlType=verif [+systemc_args+--vlTandem] -l xrun.log
   ```

   No `-top`: xmelab takes `worklib.sc_main:sc_module` and the packages as tops; the HDL wrapper is reached only through the foreign module.
   Re-simulate only: `xrun -R -64bit +systemc_args+...`. Xcelium honours `-F a2c.f`/`rtl.f` relative paths and the `-y` libraries directly
   (no explicit interface-unit analysis, unlike VCS).

Results: verif two frames, `No error`, exit 0; tandem `Tandem instance tb.debayer initialized`, two frames, `No error`. Same end time as VCS
(4,149,237 ns). **Simulation-only CPU (xrun -R, low verbosity): 69.6 s** (wall 1 m 11 s incl. 2-3 s start-up); full xrun 1 m 13 s; tandem
full 1 m 28 s. VCS prototype (§3.13) at medium verbosity: 208 s / 230 s, linked with `-race -kdb -debug_access`. Xcelium is about 3x less CPU;
the VCS debug/race options are the first suspect, not the boundary. **Action: re-measure VCS at low verbosity without `-race -kdb -debug_access`.**

Workarounds required (all must be in the automated flow):
1. Non-PIC site static Boost cannot enter xmsc's `librun.so` (1108 `R_X86_64_32` relocs). Used RHEL9 system `libboost_program_options.so.1.75.0`
   and `libboost_system.so.1.75.0` (headers 1.74, worked) and header-only stacktrace. Long-term: PIC Boost build or matching devel headers.
2. `-Wld,` splits on commas, so `-Wl,-rpath,...` cannot be passed; rely on `LD_LIBRARY_PATH` or `-Wld,-Xlinker -Wld,-rpath=...`.
3. `-top sc_main` is wrong in this mode (`*F,CUSCTOP: Multiple top instantiations of sc_module 'sc_main'`); give no `-top`.
4. `xmelab *E,MULAXX` (1956) from the FPGA-flow flop macros in `builder/common/systemVerilog/flops.sv:55-59` (`initial q = '0;` plus `always_ff`
   on the same variable); VCS/Verilator accept it. `-warn_multiple_driver` demotes to warnings; alternatives `+define+ASIC` or a macro rewrite.
5. `xmsc_elab_exception` rethrow in `try_sc_start` (sc_main runs twice: under xmelab to the first `sc_start`, then under xmsim).
6. `sc_main.` hierarchy prefix **not needed** (ran without `setHierarchyPrefix`); lock status dump was empty in this test, so a lock-heavy test
   should re-check.
7. `xmsim *W,SCK910: sc_start(0) will only execute one SystemC delta cycle` on a2c's enumeration `sc_start(SC_ZERO_TIME)`; harmless here.
8. Warnings only: `SPDUSD`, `LIBNOU`, `INTOVF` (`debayer_regs.sv:108`, same literal VCS flags).

Per-cycle boundary observations (not yet measured; use `xrun -R -xprof`/`-perfstat` before optimising): `clk` is an `sc_clock` crossing the
boundary twice per cycle (an HDL-side clock would halve boundary events); every pin is a separate `sc_signal` plus `assign #0` deltas; BFMs are
`SC_THREAD`s waking on every `clk.posedge_event()` regardless of traffic.

What the generator/make flow must emit for Xcelium (parallel to §3.13): `vlRegistrar.py` `#elif defined(XCELIUM)` branch; a generated
foreign-module shell header per trampoline from the same pin list/widths as the VCS portmap; `main.cpp` `xmsc_elab_exception` rethrow;
an `XCELIUM` make mode with the Cadence defines/includes, `-fPIC`, no `BOOST_STACKTRACE_LINK` (or a PIC stacktrace lib); PIC/shared Boost and
OpenCV via `-Wld,`; `a2c-xrun.mk` with the command above (no `-top`), `xrun -R +systemc_args+...` per regression test, direct `tools/bin/xrun`
with `LM_LICENSE_FILE`, `-clean` on rebuild. Follow-ups: `-sc_301`, `flops.sv` vs `MULAXX` and Boost (resolved in §3.15), FSDB/SHM tracing.

### 3.15 Xcelium blockers: `flops.sv` multiple driver and non-PIC Boost (agent research, read-only)

**`flops.sv` (`builder/base/common/systemVerilog/flops.sv`).** Two branches: `` `ifdef ASIC `` (synchronous reset via `` `RST ``, default
`~rstN`) and the default FPGA branch, in which five of six macros (`DFF`, `DFFR`, `DFFEN`, `DFFREN`, `SCFF`) pair `initial q = ...;` with an
`always_ff` on the same variable; only `DFFNR` is clean. IEEE 1800 forbids a second writer of an `always_ff` variable and Xcelium enforces it
(`*E,MULAXX`, 1956 sites: 292 in debayer `rtl/`, 46 in `builder/pro/common/systemVerilog`, 177 in base examples). Facts that constrain the fix:
- Nothing sets `ASIC`/`FPGA` anywhere (Verilator adds only `-DVL_DUT`); the FPGA branch is always taken. `rstN` does not exist in any RTL;
  the ports are `rst_n`, and `rst_n` is otherwise unused apart from gating APB select in `debayer_regs.sv:112-113`. The testbench holds reset
  5 ns. **In the FPGA flow the `initial` is the only initialisation a flop ever gets.**
- Macros are applied to pre-declared signals and part-selects (`debayer_regs.sv:108` `DFFREN(bayer_pattern_reg[1:0], ...)`), so declaration
  initialisers cannot replace the `initial`.
- Therefore: `` `ifndef XCELIUM `` around the `initial` leaves every flop X for the whole run (tandem diverges at once); `+define+ASIC` needs
  `+define+RST=!rst_n` too and changes time-0 semantics (X until 5 ns).
- **Recommendation:** primary, keep `xrun -warn_multiple_driver` (proven, zero effect on other tools, 1956 warnings of noise). For a clean log,
  add a helper macro in the FPGA branch (`` `A2C_FF `` = `always_ff`, or `always` under `` `ifdef XCELIUM ``) and use it in the five macros;
  plain `always @(posedge clk)` has identical simulation and synthesis semantics and no strict-driver check, and the `initial` stays, so
  time-0 values match VCS/Verilator. Drive it with an explicit `+define+XCELIUM` on the xrun line. Update
  `builder/base/rules/skills/rtl-core.md:134-136` (and the mirrored `.claude/skills/rtl-core/SKILL.md`) accordingly.

**Boost.** Site Boost is 1.74.0, static-only, non-PIC (`libboost_program_options.a` 2520 absolute relocations; `libboost_stacktrace_basic.a` 57;
`libboost_system.a` is a 1436-byte stub because Boost.System is header-only since 1.69). No PIC/shared Boost exists under
`/ldc/projects/qistor/tools` or `/tools/dist` (only vendor-private copies). System RHEL9 has runtime `boost-*-1.75.0-10.el9` shared libs
(`/usr/lib64/libboost_program_options.so.1.75.0`, `libboost_system.so.1.75.0`, no stacktrace, no `-devel`, no `.so` symlinks);
`boost-devel-1.75.0` is available in the AppStream repo and can be extracted user-side with `rpm2cpio`.
a2c's only stacktrace use is `q_assert.cpp:35` (`boost::stacktrace::stacktrace()`); with `-DBOOST_STACKTRACE_LINK` removed, the header-only
backend (`unwind_base_impls.hpp`) is exactly what `libboost_stacktrace_basic.a` packages: **byte-identical output, no feature loss** (`-ldl` already linked).
- **Recommendation (smallest change):** Xcelium mode compiles `-fPIC` without `BOOST_STACKTRACE_LINK` and links
  `-Wld,/usr/lib64/libboost_program_options.so.1.75.0 -Wld,-ldl` (drop `libboost_system`, drop stacktrace lib; `/usr/lib64` needs no rpath).
  Hardening: extract `boost-devel-1.75.0` into `/ldc/projects/qistor/users/atomlin/tools` and point `BOOST_INCLUDE` at it for the Xcelium mode so
  headers match the 1.75 `.so` (the prototype's 1.74-headers/1.75-lib pairing worked but is unsupported). VCS/plain flows unchanged
  (`-lboost_system` may be dropped there too). A private PIC Boost build is not recommended.

Design fact surfaced (out of scope, worth raising with the RTL owners): in the default FPGA flow the RTL has no functional reset; `rst_n`
only gates APB select, so power-on `initial` values are the reset model.

### 3.16 Automatic VCS native-DUT flow implemented (agent implementation, unstaged, coordinator-verified)

**Design correction forced by VCS.** VCS elaborates SystemC-on-top designs in two steps: it first runs the SystemC part alone (sc_main
up to the first `sc_start`) to discover which HDL models are instantiated, then builds `simv` around exactly that topology. VCS user guide
(`compilation_flow/elaboration_scheme.html`): "If your SystemC design topology depends on simv runtime arguments, then you MUST provide the
relevant arguments with `-syscelab`. The SystemC design topology during step 1 and the final execution of simv must be identical."
**This is the "run-time elaboration" limitation.** VCS also caches the discovered topology per output binary
(`csrc/sysc/<mangled-output-path>/instantiatedmodellist.syscelab`) and does not redo step 1 on relink, so relinking one binary with different
`-syscelab` args silently keeps the old topology (`Warning-[SC-ELAB-VHAN-I2] Cannot find Verilog input object` at run time).
Implemented compromise: `--vlInst/--vlType/--vlTandem` are runtime options again (command line identical to Verilator); the make flow passes
them to vcs via `-syscelab` (`VCS_ELAB_ARGS ?= $(VCS_TESTBENCH) --vlInst $(VL_INST) --vlType $(VL_TYPE) [--vlTandem]`); **one compile serves
every topology and only the 15-20 s link is per topology**; each topology is its own binary `build/run_<inst>_<type>[_tandem]`; the same
options are repeated on the simv command line. Uninstantiated `-sc_model` tops cost nothing at run time (measured below).

**Files changed** (nothing committed):
- base `templates/systemc/vlRegistrar.py`: guard `#if defined(VERILATOR) || defined(VCS_DUT)`; per-top include of `V<top>.h` or `<top>.h`;
  per-top `using <top>_dut_t = ...;` alias; top names from `verifRegistrations[].topModule`.
- base `pysrc/processYaml.py`: persisted `vcsDutClass`/`vcsDutHeader` beside `dutClass`/`dutHeader` in registrar pairs; `vcsDutHeader`/
  `variantVcsDutHeaders` in the svWrapper view. `pysrc/intf_gen_utils.py` `sc_concrete_dut` carries `vcsDutHeader`. `templates/systemc/module_hdl_wrapper.py`:
  non-templated preamble uses the view field and `VCS_DUT`.
- base `templates/systemVerilog/module_hdl_wrapper.py`: `$fsdbDumpvars` under `` `ifdef VCS_DEBUG `` (plain VCS builds otherwise fail `Error-[UST]`).
- base `common/systemc/simController.cpp`: `#ifndef VCS` removed. `common/scmain/main.cpp`: `XSTR(VL_*)/TESTBENCH` pinning removed; `exit_handler`
  `[[noreturn]]`; `VcsSetExitFunc` and `setHierarchyPrefix("sc_main")` kept.
- base `config/createBuildManifest.py`: emits `A2C_VL_PORTMAP_<top> := <wrapper stem>.portmap` and `A2C_VL_REGISTRAR_SRC` (fileType `blockVlRegistrar`).
- base `include/make/a2c-systemc.mk`: `VCS_RUNDIR ?= $(PROJECT_RUNDIR)`; under `USE_VCS`: `-DVCS` (+`-DVCS_DUT` with `VL_DUT`), `csrc/sysc/include` and
  `$(VCS_HOME)/include` on the include path, Verilator include dirs and sub-make excluded, `BIN = run_$(VCS_TOPOLOGY)` with `VL_DUT`, `BUILD_FLAVOR`
  `vcs-` prefix, includes `a2c-vcs.mk`.
- base `include/make/a2c-vcs.mk` (new): `VCS/VLOGAN/VCS_OPTS/VLOGAN_OPTS/VCS_ELAB_OPTS` (+`_USER_OPTS`); `VCS_LIB_SV_FILES` (interface `*_if.sv` plus
  `common/systemVerilog/*.sv` minus flops.sv, extensible via `EXTRA_VCS_LIB_SV_FILES`); RTL-analysis stamp; sequential `vlogan -sc_model <top> -sc_portmap`
  per `A2C_VL_TOPS` behind a stamp; registrar objects ordered after shell generation; `-syscelab` args stamp (topology change relinks only);
  vlogan-options stamp (`VCS_DEBUG` toggles re-analysis); `VCS_DEBUG=1` adds `-kdb -debug_access` and `+define+VCS_DEBUG`; csrc/stamp removal on link
  failure; `clean::` for AN.DB/csrc/daidir/vc_hdrs.h/logs. Default `VCS_ELAB_OPTS` has no `-race -kdb -debug_access`.
- pro `include/make/a2cProEnv.mk`: `A2C_CLANG ?= <Clang 18>`; `EXTRA_CXX_FLAGS += -gdwarf-4`.
- debayer `rundir/Makefile`: `USE_VCS` block deleted. Regenerated: `registrar/*VlRegistrar.cpp`, `verif/*_hdl_sv_wrapper.svh`. Hand-written test inputs
  `verif/{debayer,interpolate,preprocess}_default_hdl_sv_wrapper.portmap` (see blocker).

**Blocked: portmap generation.** Widths are mandatory (`Error-[SC-VDEF-14]` even with a global type map). Generation has no integer widths for
variant-bound structures: SV emits parameter expressions, SC emits `_bitWidth` constexpr, and the only Python evaluator
(`pysrc/valueResolver.py`, `ValueResolver(project, values=...)`, `_structureWidth`) runs only in `projectCreate` (needs `flatData`, `enums`, `qualEnums`,
not loaded by `projectOpen`). Registrations carry the parameter `values` at create time, but the boundary pin list is a `projectOpen` view (`getBDPorts`).
**Where it belongs:** persist per-registration evaluated boundary widths in `projectCreate` (where `registrarPairs` and the resolver live), then a
`.portmap` ext on the `vlSvWrap*` fileMap entries with a template (VCS accepts `#` and `//` comment lines, so GENERATED_CODE markers work). One portmap
per wrapper file suffices (VCS ignores entries for pins a model lacks). This is a data-contract change and needs owner sign-off. Interim: hand-written
files (widths taken from `verilator --xml-only`).

**Verification.** Agent: `make db`, `make gen` clean; `make USE_VCS=1 VL_DUT=1 -j8 all` 49 s wall, relink 15-20 s; `run_debayer_verif` `No error`;
`VL_TANDEM=1` -> `run_debayer_verif_tandem` `No error`, CPU 107.1 s; `VL_INST=debayer.u_preprocess` -> `run_debayer.u_preprocess_verif` `No error`,
CPU 86.2 s; non-VCS host flow builds (38 s) and runs (9.1 s); `py_compile` passes. **Coordinator re-run:** `make USE_VCS=1 VL_DUT=1 -j8 all` 48.6 s,
`./build/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif` -> `INFO: debayer module instantiated`, `No error`, exit 0, CPU 91.2 s.

**Performance (verif, synthetic, `--verbosity=low`, VCS CPU):** prototype one top + `-race -kdb -debug_access` 208.3 s; new flow five tops + same
options 210.8 s; **new flow five tops, default options 92.6 s**; `VCS_DEBUG=1` (`-kdb -debug_access`) 90.4 s. Uninstantiated tops cost nothing; the 2.3x
came from `-race`. Xcelium reference 69.6 s (§3.14).

**Review and fixes (same day).** Independent review found four items, all fixed and re-verified (`make USE_VCS=1 VL_DUT=1 -j8 all` 16 s incremental,
verif run `No error`, CPU 92.0 s): (1) link failure now removes `csrc`, `AN.DB` and both vlogan stamps so the analysis is redone; (2) VCS keys its
topology reuse on the per-binary `csrc/sysc/<mangled-output>/sysc_skeleton.v` (removing only `instantiatedmodellist.syscelab` is not enough), so the
link recipe removes those directories before every link and discovery re-runs in a few seconds; proven by relinking `run_debayer_verif` with
`VCS_ELAB_ARGS="debayer --vlInst debayer.u_preprocess --vlType verif"` and running the sub-block test to `No error`; (3) `builder/pro/include/make/a2cPro.mk`
adds `-F pro/common/systemVerilog/a2cPro.f` and the pro interface/common SV units to the vlogan library step; (4) comments trimmed. Review confirmed no
fallback lookups, no string-derived semantics, correct guards, correct make ordering, Verilator flow unchanged.
Pro RTL items surfaced for its owner: `builder/pro/common/systemVerilog/rdyVldBurstFifo.sv:36` `parameter dataSt = logic [31:0]` needs the `type`
keyword (vlogan `Error-[SE]`; filtered out of the library list for now); `a2cPro.f` lacks `+libext+.sv` (vlogan `Warning-[LIB-NO-EXT]`).

Follow-ups: `Warning-[RT_UO] Unsupported option '--vlInst' is ignored` per a2c option (harmless; `-suppress=RT_UO` candidate for `VCS_USER_OPTS`);
regression wiring must build one snapshot per topology and dispatch each test to `build/run_<topology>`; `rundir/vc_hdrs.h` is covered by `clean::`.

### 3.17 The port-map problem and the recommended solution (for owner decision)

**What VCS needs.** `vlogan -sc_model <top>` generates the SystemC shell class for an HDL module. For every port it must know the exact
bit width and the SystemC type to use. It reads widths from the module's port declarations and types from a port-map file. Two facts make
the generated trampolines unusable as-is: (a) the trampoline's port widths are *parameter expressions*, e.g.
`input bit [(1 + 1 + 1 + BITS_PER_PIXEL_COLOR*PIXELS_PER_CLOCK)-1:0] video_raw_stream_data` with `localparam BITS_PER_PIXEL_COLOR = 8`,
and `-sc_model` does not evaluate them (`Error-[SC-VDEF-14] No bit width specified`); (b) VCS's default SystemC types are `sc_logic`/`sc_lv`,
while the a2c SystemC wrapper binds `sc_signal<bool>` and `sc_signal<sc_bv<W>>`. The port map (`name width bit|bitvector bool|sc_bv`) fixes both,
and it must carry the *evaluated* integer width (35, 99, 32). Xcelium's foreign-module shell needs the same evaluated widths (`sc_in<sc_bv<35>>`),
so this is one requirement serving both simulators.

**Why arch2code cannot emit it today.** Widths of interface data structures depend on block parameters bound per variant. The generator
handles that in three different places, none of which yields an integer at generation time for the boundary pins:
- SystemVerilog side: `pysrc/intf_gen_utils.py::sv_struct_width_expression` renders a symbolic expression in terms of the block's parameters;
  the trampoline (`verif/<blk>_default_hdl_sv_wrapper.sv`) binds the parameter *values* as `localparam`s and leaves evaluation to the SV tool.
- SystemC side: `includes.py` emits `_bitWidth` as a `constexpr` in the generated structure types; the C++ compiler evaluates it.
- Python side: the only evaluator is `pysrc/valueResolver.py::ValueResolver(project, values=...)` (`_structureWidth`), and it runs only in
  `projectCreate` because it needs `flatData`, `enums` and `qualEnums`, which `projectOpen` does not load (by design: generators read persisted
  views, they do not re-derive project-wide facts).
The information exists in two halves on the wrong sides of the create/open boundary: the per-registration parameter values are in the
persisted `REGISTRARPAIRS`/active-config descriptors (`processYaml.py` ~3929-4097, `descriptor['values']`), created in `projectCreate`;
the boundary pin list (which interface ports become which pins, plus register ports) is a `projectOpen` view (`getBDPorts`, the `svWrapper`
view at ~1332-1368). Neither side alone can write the file.

**Recommended solution: evaluate and persist the boundary widths at database creation, then generate the port map and the Xcelium shell
from the persisted facts.**
1. In `projectCreate`, where the registrar pairs and their `values` are built and `ValueResolver` is available, compute for every verif
   registration (block, variant, parent-qualified pair) the boundary pin list with evaluated widths:
   `[{pin, width, direction}]`, using `ValueResolver(self, values=descriptor['values'])._structureWidth(...)` on each interface port's data
   structure (register/APB pins are fixed-width). Persist it beside the existing fields (`dutClass`, `vcsDutClass`, ...) in the registrar
   pair entry, e.g. `boundaryPins`. This follows the skill rules: project-wide truth derived from YAML and parameters lives in `projectCreate`,
   generators read persisted state.
2. Add `.portmap` (VCS) and an Xcelium shell header as additional `ext` entries of the existing `vlSvWrap*` fileMap entries (gated on `hasRtl`,
   like the trampolines), with two small templates that iterate `boundaryPins`: width 1 -> `bit bool`, else `bitvector sc_bv` (VCS);
   `sc_in/sc_out<bool|sc_bv<N>>` with `hdl_name()` (Xcelium). `make newmodule` scaffolds them, `make gen` maintains them, the build manifest
   already names `A2C_VL_PORTMAP_<top>`. VCS accepts `#`/`//` comment lines, so GENERATED_CODE markers work in the port map.
3. Consistency check for free: the persisted widths can be asserted against the C++ `_bitWidth` in the generated SC wrapper
   (`static_assert`), so a generator/evaluator disagreement fails at compile time rather than at the simulator boundary.

**Constraint added by the user (2026-09-15): sub-project text stability.** When a parent project instantiates a sub-project block with a
new variant, the sub-project's generated files must not change; the parent owns the variant-specific artifacts, as it does today with the
foreign registrar and the parent-qualified trampolines. The persisted boundary widths and the generated port map / Xcelium shell for a
parent-created variant must therefore be created in the parent project's database and emitted into parent-owned files, following the same
placement rule as the foreign registrar. The ownership mapping is being confirmed (agent research) before implementation.

**Ownership facts (agent research, `pysrc/processYaml.py`, `pysrc/artifactPaths.py`, `config/project.yaml`):**
- `REGISTRARPAIRS` (persisted at `processYaml.py:4182`) holds one entry per qualified (parent, child) pair with `ownerProject`, `pairVlStem`,
  `factoryProject` and, per verif registration, `topModule`, `dutClass`, `vcsDutClass`, `variant`, `values` (param -> value), `pairSpecific`
  (`:4150-4159`). `values` is also available in the read-only views; **the missing half is only the evaluator**, not the values.
- Registrar-mode rows (`blockVlRegistrar`, `configModule`, `vlSvWrapForeign`, `vlSvWrapPair`) are anchored at the *assembler* block's directory
  and owned by its project (`artifactPaths.py:144-179`); `resolveFileOwner` (`processYaml.py:755-799`) makes `--parent` files parent-owned;
  generators skip files owned by another project (`systemcGen.py:43-46`, `systemVerilogGenerator.py:51-54`); stale sweeps are owner-scoped.
  Block-mode variant rows exclude foreign and container-sourced labels (`variantSelection.py:9-11`). This is what keeps a child's tree stable.
- The SC wrapper `<child>_hdl_sc_wrapper.h` is a template on `DUT_T, Config` and never changes for a new variant; the parent's registrar instantiates it.
- **The parent's database can evaluate the child's widths.** `flatData` indexes every context parsed into the build, sub-projects included; the
  cross-project payload check at `processYaml.py:6765-6790` already resolves parent and child structures with two `ValueResolver`s in one database.
- **Obstacle:** in the single-project case the pair top (`p7_..._preprocess_default_hdl_sv_wrapper`) and the child's own variant top live in one
  physical file (`verif/preprocess_default_hdl_sv_wrapper.sv`, stamped `--block --variant`, child-owned), and the manifest maps both tops to one
  `.portmap` (`.gen/build.mk:24,26`). Pin names are identical, widths may legitimately differ, and a VCS port map is per `-sc_model` call. A port map
  attached as a fileMap `ext` would therefore be one file for two tops, and parent- or child-owned depending on the case. `recordVlTop` also
  hard-codes the `.portmap` suffix (`createBuildManifest.py:218`). The Xcelium shell has the same per-top nature plus a build-group question
  (`.h` under `vl_wrap` is not on any compile path today).

**Refined recommendation: persist the evaluated boundary pins per top at database creation, and emit the VCS port map and the Xcelium shell as
per-top *build-manifest outputs* under `.gen/`, not as fileMap source artifacts.**
1. `projectCreate`, at the point where each verif registration is built (`processYaml.py:4150-4159`, `values` and `ValueResolver` in scope): evaluate
   the boundary pins (`[{pin, width, direction}]`, interface data widths via `_structureWidth` with the registration's `values`; register/APB and
   `clk`/`rst_n` pins fixed) and persist them per top (`boundaryPins` on the registration; the same for block-mode standalone variant tops).
   Add a create-time check that two tops sharing a physical file agree on pin *names* (they do by construction) and record widths per top.
2. `config/createBuildManifest.py` (already a db-creation side effect that writes `.gen/build.mk`): additionally write `.gen/vl/<top>.portmap` and
   `.gen/vl/<top>_xcelium.h` from the persisted pins, one pair of files per `topModule`, and point `A2C_VL_PORTMAP_<top>` at the `.gen` path.
   These are pure derivations with no user-editable region, exactly like `build.mk`, so they need no fileMap entry, no `make newmodule`
   scaffolding, and no ownership rule: **whichever project runs `make db` gets the files for the tops its own manifest lists, in its own `.gen/`;
   a child's tree is untouched when a parent adds a variant.** `a2c-vcs.mk` consumes the manifest variable unchanged; `a2c-xrun.mk` adds
   `-I$(GEN_BUILD_DIR)/vl`; the registrar template includes `<top>_xcelium.h` (header name persisted like `vcsDutHeader`).
3. Consistency guard: the registrar TU can `static_assert` the persisted widths against the SC wrapper's `_bitWidth` for each top, so evaluator
   drift fails at compile time.
This keeps YAML as the single source of truth, reuses the existing evaluator and manifest mechanism, resolves the shared-file case (per-top files),
and satisfies the sub-project text-stability rule without touching the fileMap or the scaffolder. Cost: one derivation in `projectCreate`, one
persisted field, two small writers in `createBuildManifest.py`, one include path, one persisted header name.

**Decision (user, 2026-09-15): proceed with the refined approach above.** Implementation in progress (agent).

**Alternatives and why not.** Hand-written per project: works today (three files exist) but every project and every parameter change must be
maintained by hand for two simulators, and it contradicts YAML-as-single-source-of-truth. Build-time extraction from `verilator --xml-only`:
no generator change, but makes Verilator a dependency of the VCS and Xcelium flows and moves a design fact into the make system. Running
`ValueResolver` in `projectOpen`: would require loading `flatData`/enums in read-only mode, i.e. re-deriving project-wide facts in generators,
which the builder architecture rules forbid.

**Cost and risk.** Moderate: one `projectCreate` derivation reusing an existing evaluator, one persisted field, two short templates, two fileMap
`ext` entries; no schema (YAML) change, no change to user-authored YAML. Risk is in matching the pin naming/order that `getBDPorts` produces
for the SV wrapper; the `static_assert` in item 3 and a `make gen` diff against the three hand-written files are the checks.

---

### 3.18 VCS regression, first full pass: license pool limits parallelism (agent run, coordinator-analysed)

Run: `regr/regr_debayer_vcs.atomlin.2026-15-09-175440.1950718`, launcher `-j8`, 44 tests, dispatcher `builder/vcsRun.py` selecting `build/run_<topology>` from `--vlInst/--vlType/--vlTandem`.

- 39 of 44 tests passed (all `hdl_tests`, all model basic/delay tests).
- 5 tests timed out at 900 s: every `model_tests/tandem` test (three DUTs, both data sets). Their logs contain only `Licensed number of users already reached for VCS-BASE-RUNTIME/VCSRuntime_Net` and `Queuing for License` from the moment they started. Nothing functional failed; three of eight simultaneous simv processes obtained runtime licenses, so the pool is about three seats. Measured afterwards: `/lsc/ldp/bin/lmstat -c 1725@ldc-virtlic01 -f VCSRuntime_Net` reports 3 licences issued (the `lmstat` copies under `/tools/dist/synopsys/scl` do not run on this host).
- Under the VCS flow every binary, including `run_model`, is a VCS simv and needs a runtime seat. The launcher job count for VCS regressions must therefore match the seat count (`"jobs": 3` in `regr_debayer_vcs.json`) rather than the core count.
- Collision: during this run the boundary-pins agent rebuilt `build/run_debayer_verif` in the same rundir. Its elaboration-phase binary queued eight minutes for a license, then failed with `SC-VCS-SYSC-ELAB` and missing `csrc/sysc/*/*.tab` files; the make rule's failure cleanup then removed `csrc`, `AN.DB` and the snapshot. Root cause is shared `csrc`/`AN.DB` state plus license queuing, not the boundary-pins change. Rule going forward: one VCS build or regression at a time per rundir. The rerun at three jobs re-links the snapshot from the regenerated `.gen/vl/<top>.portmap` inputs.

Rerun at three jobs (session `regr/regr_debayer_vcs.atomlin.2026-15-09-181921.2109417`): **44 of 44 pass**, snapshot build 2 min 54 s
(seven links: `run_model` plus six verif snapshots, sequential because `csrc`/`AN.DB` are shared, objects compiled once), run 19 min 20 s;
longest test 5 min 07 s against the 900 s timeout. The snapshots were linked from the generated `.gen/vl/<top>.portmap` files.

Flow pieces (unstaged): `a2c-vcs.mk` `VCS_TOPOLOGIES` (`<inst>:verif[:tandem]`) and target `vcs_snapshots`; generic dispatcher
`builder/base/vcsRun.py` (`vcsRun.py <base binary> <sim args...>`: maps `--vlInst/--vlType/--vlTandem` to `<base>_<topology>`, `_model`
when no RTL instance is named, `execv` with unchanged arguments, exit 1 with a clear message when the snapshot is missing) plus a
`builder/vcsRun.py` symlink following the `regrLauncher.py` convention; `rundir/regr_debayer_vcs.json` (same tests and labels as
`regr_debayer.json`, `jobs: 3`, timeouts 900 s, rules `default.json` + new `vcs.json` for `Error-[code]` lines); `rundir/Makefile`
`VCS_TOPOLOGIES` for the three instances and target `regr_vcs`. A snapshot elaborated with only the testbench name runs every model-type
test (plain, model/model tandem, delay) with no topology warning, which is why one `run_model` serves all 20 model tests.
`-suppress=RT_UO` was dropped: first on the command line it suppresses nothing, last it trips the a2c option parser; each VCS log carries
eight harmless `Warning-[RT_UO]` lines instead.

Commands:
```
cd rundir
make -j8 USE_VCS=1 vcs_snapshots               # seven snapshots (VL_DUT implied)
make regr_vcs                                  # build + 44 tests, 3 jobs
../builder/dutRun.py build/run debayer --vlInst debayer.u_interpolate --vlType verif --vlTandem --verbosity=low
```

Per-test wall time of the three-job pass (launcher durations, `--verbosity=low`, host loaded by the concurrent Verilator baseline of 3.22);
each cell synthetic data; 1920x1080 data:

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 1:32; 0:18 | 2:44; 0:35 | 1:27; 0:21 |
| hdl delay | 3:46; 0:57 | 4:58; 1:14 | 3:01; 0:44 |
| hdl tandem | 1:48; 0:21 | 3:41; 0:52 | 1:39; 0:23 |
| hdl tandem_delay | 4:08; 1:04 | 5:07; 1:16 | 3:16; 0:48 |
| model delay | 0:16; 0:04 | 0:16; 0:05 | 0:16; 0:04 |
| model tandem | 0:25; 0:07 | 0:21; 0:06 | 0:22; 0:06 |
| model tandem_delay | 0:29; 0:08 | 0:24; 0:07 | 0:25; 0:07 |
| model basic (debayer) | 0:12; 0:04 | | |

Sum of the 24 RTL tests 47 min 05 s, of the 20 model tests 3 min 47 s; at three seats the RTL tests set the 19 min 20 s wall time.
JUnit: `test-reports/junit.xml`, `tests="44" failures="0" errors="0" time="3021.45"`.

Other measurements from the wiring work (same day):
- `vcs_snapshots` on warm objects (link phase only, seven snapshots): 2 min 17 s wall. First run's build step (compile plus seven links): 2 min 07 s
  because the objects were already current; the three-job rerun recompiled after `make db gen` had regenerated files: 2 min 33 s and 2 min 54 s.
- Single verif+model tandem run of the interpolate block through the dispatcher: 219.3 s CPU (the heaviest of the six RTL topologies).
- Intermediate rerun `regr/regr_debayer_vcs.atomlin.2026-15-09-181550.2052534`: 44 of 44 failed in 0.07 s each with
  `unrecognised option '-suppress=RT_UO'` from the a2c parser, which is what ruled the option out (its earlier "0 warnings" reading was that
  same immediate abort, not a suppression).
- Eight-job pass: 39 of 44, run 18 min 51 s, build 2 min 07 s; the five queued tests held their 900 s each, so the wall time hides the loss.

Decision applied (2026-09-15, owner request): `USE_VCS=1` and `USE_XCELIUM=1` imply `VL_DUT=1`. Implemented in `a2c-systemc.mk` before the
first `VL_DUT` gate (`ifneq ($(USE_VCS)$(USE_XCELIUM),)` / `VL_DUT ?= 1`); `VL_DUT=1` dropped from `regr_debayer_vcs.json`; a model-only
simulator binary takes an explicit empty `VL_DUT=`. Dry run confirmed: `make USE_VCS=1 all` targets `build/run_debayer_verif`,
`make USE_VCS=1 VL_DUT= all` targets `build/run`.

### 3.19 Automatic Xcelium native-DUT flow implemented (agent implementation, unstaged, coordinator verification pending)

`make USE_XCELIUM=1 VL_DUT=1 [VL_TANDEM=1] [VL_INST=<inst>] -j8 all` builds one Xcelium snapshot per DUT topology and a run script `build/run_<topology>`; the run command line is identical to the Verilator and VCS flows.

Design findings:
- Xcelium fixes the SystemC topology in the snapshot as VCS does. A snapshot elaborated with the model topology and re-simulated with `--vlInst debayer --vlType verif` fails `xmsim *F,SCOBNF: SystemC object 'clk' not found in 'sc_main.tb.debayer'`. Without elaboration-time `+systemc_args+` xmelab fails `SCK1026 ... did not call sc_start()`. So: one snapshot per topology (`xcelium_<topology>.d` via `-xmlibdirname`), elaboration arguments from `XRUN_ELAB_ARGS`, an options/args stamp forces a re-elaboration on change.
- `build/run_<topology>` is a generated shell script: every argument becomes `+systemc_args+<arg>`, then `exec xrun -R -xmlibdirname <snapshot> -64bit -nolog`. It exports the site `LM_LICENSE_FILE` captured at build time, otherwise a run outside the make environment fails `*F,VSPLIC`.
- xmelab makes every uninstantiated unit a top-level, so the wrappers a topology does not use are elaborated as idle tops with an undriven clock. `-top worklib.sc_main:sc_module` is fatal (`CUSCTOP`); putting the HDL in library `a2c_dut` via `-makelib` does not stop auto-top (kept, harmless). Open item: memory cost at SoC scale. Candidate fixes: compile only the topology's wrapper (needs an instance-to-top mapping in the manifest), or a Cadence option not yet found.
- `common/systemc/hwMemory.h` used `sc_core::sc_bind`; Cadence spells `sc_bind` as a macro. Replaced with a lambda (the form used elsewhere in a2c). The 3.14 prototype had silently skipped `synchLockPro.o`, which hid this.

Files (unstaged): base `include/make/a2c-xrun.mk` (new), `include/make/a2c-systemc.mk` (`USE_XCELIUM` block; `DUT_TOPOLOGY` generalises the per-topology `BIN`, `VCS_TOPOLOGY ?= $(DUT_TOPOLOGY)` alias), `templates/systemc/vlRegistrar.py` (`XCELIUM_DUT` branch from persisted `xceliumDutHeader`/`xceliumDutClass`), `pysrc/processYaml.py`, `common/scmain/main.cpp` (`xmsc_elab_exception` rethrow), `common/systemc/hwMemory.h`; pro `include/make/a2cProEnv.mk` (`USE_XCELIUM` block: `XCELIUM_ROOT`, direct `tools/bin/xrun`, `LM_LICENSE_FILE`, `XRUN_BOOST_LIBS` = system shared Boost 1.75; Clang 18 + GCC 13 header wiring shared by VCS and Xcelium), `a2cPro.mk` (`XRUN_USER_OPTS += -F a2cPro.f`). Xcelium shells `<top>_xcelium.h` come from the boundary-pins generator under `.gen/vl` (3.20).

Verification by the agent (rundir, `BIN_DIR=$PWD/build_xrun`, all `No error`, rc 0):

| Topology | Snapshot | Run CPU |
|---|---|---|
| debayer verif | 1 m 16 s (+36 s compile) | 69.7 s |
| debayer verif tandem | 1 m 28 s | 84.1 s |
| debayer.u_preprocess verif | 3 m 32 s (host busy) | 114.9 s |

The agent's VCS re-check collided with the regression's re-link of `build/run_debayer_verif` (same race as 3.18) and is pending a quiet tree. Leftovers in rundir: `build_xrun/`, `xcelium_*.d`, `xrun_*.log`, `xrun.history`.

### 3.20 Boundary pins persisted, per-top port map and Xcelium shell generated (agent implementation, unstaged)

Outcome of the 3.17 decision. One deviation from the plan: the build-manifest writer runs in `projectCreate`, which has no pin list
(pins are a `projectOpen` view built from `getBDPorts` plus `interface_defs`, including the view-synthesised register ports). Rather than
duplicate that view at create time, the split is:

- `projectCreate.calcVlTops` (called from `calcRegistrarPairs`) persists `VLTOPS = {topModule: {blockKey, structWidths: {structureKey: int}}}`
  for every manifest top (pair registrations, bare per-label tops, owner-qualified foreign tops, the single top of a params-less block).
  Widths come from `ValueResolver(values=<paramSourceKey: value>)._structureWidth` over the block's parameterised structures.
- `projectOpen` view helpers `getBDVlBoundaryPins` (in `getBlockData`) and `getVlTopBoundaryPins(ret, topModule)` compose the pin list
  `{pin, direction, structure, structureKey, width}` with the persisted width bound per top.
- A read-only pass `arch2code.py --vlBoundary` (`pysrc/vlBoundaryGen.py`, run by `make gen` via stamp `$(GEN_BUILD_DIR)/vl/.boundary`) writes
  `.gen/vl/<top>.portmap` (`pin width bit|bitvector bool|sc_bv`) and `.gen/vl/<top>_xcelium.h` (`xmsc_foreign_module` shell with
  name-initialised ports and `hdl_name()`), whole files, no user region.
- `createBuildManifest.py` points `A2C_VL_PORTMAP_<top>` at `.gen/vl/<top>.portmap` and emits `A2C_VL_GEN_INC`; `a2c-vcs.mk` makes the port
  maps depend on the boundary stamp, `a2c-xrun.mk` the registrar objects, `a2c-systemc.mk` adds `-I$(A2C_VL_GEN_INC)` under `USE_XCELIUM`.
- `vlRegistrar.py` emits `static_assert(<struct><Config>::_bitWidth == <persisted width>)` per payload pin of a templated wrapper, so a
  drift between the C++ structure and the persisted width fails the compile rather than the simulator elaboration.
- `intf_gen_utils.hdl_param_widths` factors the eval-DSL width lookup previously inline in both blast functions.
- debayer: the hand-written `verif/*.portmap` and `verif/*_xcelium.h` are deleted; `registrar/*VlRegistrar.cpp` regenerated (asserts:
  `video_bayer_t 35`, `video_rgb_t 99`, `bayer_preprocess_stream_t 323`).

Ownership: whichever project runs `make gen` writes its own manifest's tops into its own `.gen/vl`; a parent's new variant produces a new top in
the parent's `.gen` only. Verified on `examples/ip_test`: bridge `.gen/vl` holds 4 tops, ip holds 1, and a parent `make db gen` leaves the child
tree byte-identical. The assertion caught a real defect during development (bindings keyed by bare name resolved to defaults: 40 instead of 42
for the inherit fixture's `alt` top), fixed by keying on `paramSourceKey`.

Unit tests (with `VERILATOR_ROOT` exported and a `clang++` wrapper on PATH): `test_container_param_cross_project_vl`, `test_build_manifest`,
`test_stale_vl_wrap_cleanup`, `test_transit_container_vl_wrapper`, `test_stale_registrar_cleanup`, `test_container_param_vl_wrapper_migration`
pass. `test_inherit_vl_child` passes every boundary/width/build/run check and fails one text expectation on the registrar
(`vliLeaf_hdl_sc_wrapper<Vp13_..._hdl_sv_wrapper, ...>`) that the `<top>_dut_t` alias from the VCS-flow work (3.16) changed: expectation to be
updated. Running `test_build_manifest` regenerated the committed example outputs under `examples/*/{registrar,verif}` with all agents'
template changes; keep or revert with the rest of the change set.

Left to the coordinator: VCS build and run, Xcelium build and run, host model build on the combined tree (3.23).

Owner request (2026-09-15, applied): the boundary files are simulator artefacts and are written only under the make switches. In
`a2c-common.mk` the stamp joins `GEN_DEPS` only when `USE_VCS` or `USE_XCELIUM` is set (and the project has HDL tops); `a2c-vcs.mk` and
`a2c-xrun.mk` keep their own dependencies on the stamp. Dry runs: plain `make gen` and plain `make VL_DUT=1 all` invoke no `--vlBoundary`;
`make USE_VCS=1 gen` and `make USE_XCELIUM=1 gen` do. The persisted `VLTOPS` data and the registrar `static_assert` (a compile-time check
of the C++ structure width against the persisted width, valid under every flow) are unchanged.

### 3.21 Performance baseline: Verilator on the farm host (coordinator measurement)

Verilator 5.038 is installed at `/ldc/projects/qistor/tools/bin/verilator` (`VERILATOR_ROOT` already set in `a2cProEnv.mk`), so the
whole-design Verilator flow builds on the host with the plain-flow Clang 18 recipe (3.4) into a separate output directory:

```
CL="/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8/bin/clang++ --gcc-install-dir=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0 -fno-pie -no-pie"
make -j8 VL_DUT=1 USE_GCC= CXX="$CL" BIN_DIR=$PWD/build_vl all      # 52 s wall, 3 m 21 s CPU
```

The verilated library is compiled by the GCC 13.2 on PATH (same libstdc++ as the Clang objects). All runs `--verbosity=low`, `No error`, user CPU
seconds, host shared with the VCS regression (3 simv jobs) at the time:

| Test (synthetic data) | Verilator | VCS (3.13/3.18 logs) | Xcelium (3.19) |
|---|---|---|---|
| model only, no RTL | 8.7 | 12.2 | not measured |
| debayer verif | 30.8 | 91.0 | 69.7 |
| debayer verif tandem | 40.7 | 108.2 | 84.1 |
| debayer.u_preprocess verif | 56.3 | 87.4 | 114.9 (host busy) |

Reading: on pure SystemC the VCS kernel costs about 1.4x Verilator's build; with RTL in the loop VCS is about 3x and Xcelium about 2.3x
Verilator on the whole design. Verilator compiles the RTL to C++ and is expected to lead an event-driven simulator; the figures are the
reference for judging flow overhead, not a defect. A full 44-test pass against the Verilator build (`/usr/bin/time` wrapped, 6 jobs) is
running so every VCS regression test has a matching baseline; results follow in 3.22.

VCS per-test CPU seconds from the first regression pass (3.18), for reference (synthetic / 1920x1080):

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 91.0 / 17.4 | 165.2 / 35.5 | 87.4 / 20.4 |
| hdl delay | 227.8 / 56.5 | 292.0 / 72.6 | 179.4 / 43.8 |
| hdl tandem | 108.2 / 21.8 | 223.0 / 51.9 | 97.5 / 22.7 |
| hdl tandem_delay | 240.0 / 61.2 | 303.0 / 75.4 | 189.7 / 46.0 |
| model basic | 12.2 / 3.4 | | |
| model delay | 16.0 / 4.3 | 16.2 / 4.5 | 15.4 / 4.2 |
| model tandem_delay | 28.1 / 7.4 | 23.7 / 6.3 | 24.6 / 6.6 |

### 3.22 Full regression under Verilator on the host: 44 of 44 pass, per-test baseline (coordinator run)

Session `regr/regr_debayer_vlbase.atomlin.2026-15-09-183311.2188613` from the temporary session file `rundir/regr_debayer_vlbase.json`
(the VCS test tree, `default.json` rules only, `/usr/bin/time -f CPU_TIME_USER=%U build_vl/run debayer --verbosity=low`, 6 jobs, no build
step). Result: 44 passed, 0 failed, 5 min 19 s wall, 23 min 53 s total user CPU. The VCS pass at the same time was still running its
three jobs, so both sets were measured on a loaded host.

User CPU seconds, Verilator / VCS (VCS-to-Verilator ratio); each cell synthetic data; 1920x1080 data:

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 31.5 / 91.0 (2.9x); 8.1 / 17.4 (2.1x) | 102.7 / 165.2 (1.6x); 25.8 / 35.5 (1.4x) | 56.5 / 87.4 (1.5x); 14.3 / 20.4 (1.4x) |
| hdl delay | 72.2 / 227.8 (3.2x); 18.5 / 56.5 (3.1x) | 130.5 / 292.0 (2.2x); 33.3 / 72.6 (2.2x) | 80.3 / 179.4 (2.2x); 20.3 / 43.8 (2.2x) |
| hdl tandem | 41.1 / 108.2 (2.6x); 10.5 / 21.8 (2.1x) | 119.7 / 223.0 (1.9x); 30.0 / 51.9 (1.7x) | 61.5 / 97.5 (1.6x); 15.7 / 22.7 (1.4x) |
| hdl tandem_delay | 83.5 / 240.0 (2.9x); 21.6 / 61.2 (2.8x) | 137.8 / 303.0 (2.2x); 35.0 / 75.4 (2.2x) | 86.2 / 189.7 (2.2x); 22.0 / 46.0 (2.1x) |
| model delay | 10.0 / 16.0 (1.6x); 2.8 / 4.3 (1.6x) | 10.5 / 16.2 (1.5x); 2.9 / 4.5 (1.6x) | 10.1 / 15.4 (1.5x); 2.8 / 4.2 (1.5x) |
| model tandem | 17.1 / -; 4.5 / 6.4 (1.4x) | 15.8 / -; 4.1 / - | 14.1 / -; 3.8 / - |
| model tandem_delay | 18.4 / 28.1 (1.5x); 4.8 / 7.4 (1.5x) | 17.1 / 23.7 (1.4x); 4.5 / 6.3 (1.4x) | 15.4 / 24.6 (1.6x); 4.0 / 6.6 (1.6x) |
| model basic (debayer) | 8.9 / 12.2 (1.4x); 2.5 / 3.4 (1.4x) | | |

Reading:
- Pure SystemC (model tests): VCS's kernel and runtime cost a steady 1.4x to 1.6x over the plain SystemC 2.3.4 build.
- RTL in the loop: VCS costs 1.6x (interpolate) to 3.2x (debayer delay) Verilator; the smallest ratios are on the interpolate block, whose
  model-side work dominates, the largest on the whole design where the RTL dominates. This is Verilator's compiled-RTL advantage; the
  a2c flow adds nothing per cycle beyond the simulator's own SystemC/HDL boundary.
- Whole regression: 50 min 00 s CPU under VCS (three-job rerun, 3.18) versus 23 min 53 s under Verilator, 2.1x; wall time 19 min 20 s
  at three licence-bound jobs versus 5 min 19 s at six jobs, plus the 2 min 54 s VCS snapshot build.
- Xcelium per-test figures follow when its regression wiring lands (open item); the single runs in 3.21 put it between the two.
- Licence pools (`/lsc/ldp/bin/lmstat`, 2026-09-15 evening): `VCSRuntime_Net` 3 issued at `1725@ldc-virtlic01`; `Xcelium_Single_Core`
  651 issued, 617 in use at `5280@lrd-virtlic-ha-01b` (the `lrd-virtlic-rh8-01` server refuses status queries). Xcelium parallelism is
  therefore bounded by the free seats of a large shared pool, VCS by a hard three.

Leftovers: `rundir/regr_debayer_vlbase.json` (temporary session file, untracked), `rundir/build_vl/` (Verilator build), the vlbase session directory.

### 3.23 Combined tree verified by the coordinator (2026-09-15, 18:50 to 19:05)

All three agents finished; no other build or regression was running. From `rundir`, in sequence:

| Step | Result |
|---|---|
| `make db && make gen` | clean, nothing to regenerate; `.gen/vl` holds the 10 boundary files |
| `make USE_VCS=1 VL_DUT=1 -j8 all` | rc 0, 1 min 03 s wall (objects current, re-link plus elaboration) |
| `./build/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif` | `No error`, CPU 93.9 s |
| `make USE_XCELIUM=1 VL_DUT=1 -j8 all BIN_DIR=$PWD/build_xrun` | rc 0, about 1 min wall |
| `./build_xrun/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif` | `No error`, user CPU 70.1 s |

Both simulators consumed the generated `.gen/vl/<top>.portmap` and `<top>_xcelium.h`; the registrar `static_assert` widths compiled.
`unittest/test_inherit_vl_child.py` passes in full after its registrar expectation was updated to the `<top>_dut_t` alias (3.20).
`a2c-xrun.mk` header and library comments corrected to the per-topology snapshot design; a duplicated stamp dependency removed.

Next: Xcelium regression wiring (delegated, 3.24).

### 3.24 Xcelium regression wired; first pass 32 of 44, cause found and fixed (agent implementation, coordinator wiring)

Wiring (unstaged): `a2c-systemc.mk` names every simulator binary `run_<topology>` (`DUT_TOPOLOGY` is `model` when `VL_INST` is empty) and
holds the shared `DUT_TOPOLOGIES` list and `dut_topology_make` helper; `a2c-xrun.mk` snapshot dir `xcelium_$(DUT_TOPOLOGY).d` and target
`xrun_snapshots` (per-topology sub-makes run in parallel under the jobserver, each with its own `-xmlibdirname` and log; verified no
conflict); `a2c-vcs.mk` `VCS_TOPOLOGIES ?= $(DUT_TOPOLOGIES)`; `a2c-common.mk` `XRUN_BIN_DIR = $(PROJECT_RUNDIR)/build_xrun` and
`BIN_DIR = $(XRUN_BIN_DIR)` under `USE_XCELIUM`, `clean` covers it, so VCS (`build/`) and Xcelium (`build_xrun/`) snapshots coexist;
`rundir/regr_debayer_xcelium.json` (44 tests, 6 jobs, build `make -j8 USE_XCELIUM=1 xrun_snapshots`, run
`/usr/bin/time -f CPU_TIME_USER=%U ../builder/dutRun.py build_xrun/run debayer --verbosity=low`), `rundir/xcelium.json` (`*E,CODE` /
`*F,CODE` filters, verified on JUnit), `rundir/Makefile` `regr_xcelium`. Side effect: a model-only VCS build now produces `build/run_model`
rather than `build/run`, which is what the dispatcher expects.

First pass (session `regr/regr_debayer_xcelium.atomlin.2026-15-09-190640.2296094`): 32 passed, 12 failed; build 3 min 49 s (six
elaborations in parallel, 1 min 14 s to 3 min 24 s each), run 9 min 07 s, no licence errors at six jobs (17 free seats before the run).

Design finding: **Xcelium fixes the whole SystemC object set in the snapshot**, not only the HDL binding. The 12 failures are every
`model_tests/tandem` and `model_tests/tandem_delay` test, each dying in 0.2 s with `xmsim *F,SCOBNF: SystemC object 'verif' not found in
'sc_main.tb.<inst>'`: a model/model tandem constructs a second model instance under the DUT that the `run_model` snapshot (elaborated with
the bare testbench name) does not contain. VCS has no such constraint (one `run_model` served all 20 model tests, 3.18). Plain model,
model `--delay` and all 24 RTL tests are fine. Rule for Xcelium: every command-line option that changes the constructed SystemC hierarchy
needs its own snapshot.

Fix (coordinator, applied): the dispatcher maps `--vlType model --vlTandem --vlInst X` to `<base>_X_model_tandem` (plain model and model
delay stay on `model`); `DUT_TOPOLOGIES` in `rundir/Makefile` gains `<inst>:model:tandem` for the three instances. One shared list keeps
the dispatcher and both flows consistent; VCS gains three extra links (about a minute of build) with no run-time cost. The agent had already
verified the twelve tests pass on such snapshots (`build_xrun/run_<inst>_model_tandem`, 21 to 22 s each to build). Reruns: full Xcelium
regression and the two VCS model-tandem groups (results below).

Rerun results: VCS `vcs_snapshots` with the ten topologies 5 min 04 s (re-analysis after the incident below plus ten links);
`regrLauncher.py -j3 regr_debayer_vcs.json /model_tests/tandem` (the group argument is a run-path prefix and covers `tandem_delay` too):
12 of 12 pass in 1 min 14 s, so the VCS flow is unaffected by the shared mapping.
Xcelium `make regr_xcelium` (session `regr/regr_debayer_xcelium.atomlin.2026-15-09-192453.2336025`, snapshots already current so the
build step took 15 s): **44 of 44 pass**, run 9 min 40 s at six jobs, total user CPU 43 min 21 s, JUnit `tests="44" failures="0"`.
**Goal reached: the full debayer RTL regression runs under both VCS and Xcelium on the farm host.**

Incident: a `make -n USE_VCS=1 BIN_DIR=<scratch> vcs_snapshots` dry run by the agent executed the VCS link recipe, because it carried a `+`
prefix (kept from the old `export MAKEFLAGS=-j` habit); the link failed for lack of objects and its failure cleanup removed `rundir/AN.DB`
and `rundir/csrc`. The snapshots in `build/` stayed runnable; the next VCS build re-analyses. Fixed: the `+` is removed from the link
recipe (VCS's own csrc compile is under a second and needs no jobserver), so a dry run is now inert. The `+$(MAKE)` lines of the snapshot
targets are correct (a sub-make under `-n` is itself a dry run).

Xcelium per-test user CPU seconds from the first pass (model tandem rows from the agent's direct runs on the new snapshots); each cell
synthetic; 1920x1080:

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 70.7; 15.7 | 159.4; 38.6 | 114.2; 28.1 |
| hdl delay | 142.6; 36.1 | 235.4; 59.0 | 179.2; 45.0 |
| hdl tandem | 85.4; 19.7 | 199.4; 49.7 | 126.7; 30.8 |
| hdl tandem_delay | 162.2; 40.5 | 248.7; 62.5 | 193.1; 48.0 |
| model delay | 11.5; 3.3 | 11.9; 3.4 | 11.8; 3.4 |
| model tandem | 19.1; 5.1 | 17.7; 4.9 | 16.2; 4.5 |
| model tandem_delay | 20.2; 5.5 | 18.6; 5.1 | 17.5; 4.8 |
| model basic (debayer) | 10.6; 3.0 | | |

Totals: 24 RTL tests 39 min 51 s, 20 model tests 3 min 18 s, all 44 tests 43 min 09 s (Verilator 23 min 53 s, VCS 50 min 00 s). RTL tests
sit between the two (debayer default 70.7 versus 31.5 Verilator and 91.0 VCS); model tests cost about 1.2x plain SystemC.

Elaboration warnings: `MULAXXW` hits its 1000-per-run cap in every snapshot (`rtl/interpolate.sv`, the `flops.sv` item of 3.15);
`SPDUSD`/`LIBNOU` (unused incdirs and libraries from `a2c.f`); `INTOVF` at `debayer_regs.sv:108`; `MLIBEXT`. Run time: every test logs
`*W,SCK910: in a mixed SC-HDL design, sc_start(0) will only execute one SystemC delta cycle`.

Leftovers: `rundir/build_xrun/` (about 1 GB), ten `rundir/xcelium_*.d` (42 MB each), `rundir/xrun_*.log`, `xrun*.history`, `rundir/xcelium.d/hdl.var`.

### 3.25 Full unit test sweep on the combined tree: 130 of 130 (agent run)

`unittest/run_all_tests_parallel.sh` (the parallel drop-in for `make unittest`) with `VERILATOR_ROOT` exported and the Clang 18 wrapper on
`PATH` as `clang++`: 130 suites, 130 pass, runner exit 0, 10 min 06 s wall on 96 cores (load 55 to 70 during the fan-out).

- One drift from today's changes: `test_transit_surface_classification.py` built a mock `verifRegistrations` row without the keys the
  registrar template now reads (`topModule`, `vcsDutClass`, `vcsDutHeader`, `xceliumDutClass`, `xceliumDutHeader`; the real view supplies
  them). The mock gained the five keys; intent unchanged. `test_inherit_vl_child.py` had been updated earlier (3.23).
- Two suites (`test_error_declared_ports.py`, `test_error_rtl_hierarchy.py`) hit a fixed 10 s `subprocess` timeout on `projectCreate`
  under the 96-way fan-out on NFS; both pass on the runner's retry and standalone. Environment, not code.
- No failure traced to the generator, manifest, make files or C++ changes.
- Housekeeping observed (nothing deleted): about 280 empty `unittest/inherit_order_*` directories left by `test_inherit_vl_child.py`
  (NFS silly-rename defeats `rmtree`, dated 2026-08-23 onward, one added per run; not git-visible because empty); three empty
  `adaptprobe_*`/`adjudicate_*`/`chainprobe_*` directories from tests since removed; four ignored `addrctl_*` YAML files from interrupted
  runs; one `tmp*.db-journal` from the timed-out process.

Logs: scratchpad `unittest_sweep.log`, `suite_logs_firstpass/`, `rerun_*.log`. Examples half of the CI sweep (`make pipeline-test`) follows in 3.26.

### 3.26 Examples CI sweep (`make pipeline-test`) on the combined tree: 24 of 26, no failure from today's changes (agent run)

Environment as in 3.25. Two sweeps; the second is authoritative.

- Sweep 1 on the tree as found: 10 targets failed, all class "stale tree": 26 example projects still held databases and `.gen/build.mk`
  from a 2026-09-14 container build rooted at `/work/ws/debayer` (`Invalid config item VLTOPS not found`, source dirs pointing at
  `/work/...`). `push-test` runs `clean` first; the per-project `clean` targets were run instead (they remove only `.gen`, `rundir/build`,
  databases, `obj_dir`).
- Sweep 2 after the cleans: **24 of 26 pass** (nested, hello-world, mixed, in-and-out, lint-axi, lint-hier, apbDecode, axiDemo, axi4sDemo,
  hierVlDemo, ip-test, simple-ip, xproj-nested-router, xproj-param, xproj-matrix, xproj-reuse, xproj-matrix-probes, xproj-const,
  xproj-depth, xproj-twoctx, xproj-inherit, xproj-container-layout, xproj-inherit-layout, xproj-inferred-port, xproj-variant-unique, xif;
  the two below excepted). Targets exercising the new registrar output passed model and Verilated runs, including the six example
  registrars that carry the new `static_assert` width checks.
- `diagram-and-doc`: environment. The golden `examples/tests/golden/nestedSt.svg` was drawn by graphviz 2.43.0, the host has 2.44.0;
  labels identical, coordinates differ, deterministic across reruns. Every other golden matches. Options: regenerate the golden on the farm
  or pin graphviz.
- `pySocket`: environment with a pre-existing robustness gap. The Python client under `/ldc/projects/qistor/tools/bin/python3` (3.10.13)
  fails `ImportError: libffi.so.6` on `import ctypes`; the simulation then blocks in `accept()` with no host-side timeout (the SystemC
  watchdog cannot fire while the host thread blocks), so `run` hung 59 minutes until killed. `/usr/bin/python3` (3.9.21) imports fine.
- Examples git status: 83 modified tracked files (65 after the unit tests; the 18 new ones are pySocket and xprojParam/rtInh registrars and
  wrappers whose databases had been stale), all containing only today's template text (`VERILATOR || VCS_DUT || XCELIUM_DUT` guard,
  `<top>_dut_t` aliases, VCS header selection, `` `ifdef VCS_DEBUG``). No new untracked files under examples. No files edited by the agent.
- Observation (pre-existing design): the database rule depends only on YAML (`a2c-common.mk:156`), so a generator change never invalidates
  an existing database; a `make clean` (or a generator-version stamp) is needed after pulling generator changes.

Wall: sweep 1 683 s; sweep 2 3696 s of which about 59 min was the pySocket hang (all other targets done by about 27 min).
Logs: scratchpad `pipeline_test.log`, `pipeline_test2.log`, `clean_targeted.log`, `examples_status_{before,after1,after2}.txt`.

### 3.27 Review of the new compile switches across usage modes (agent review, read-only)

Scope: every new make switch and preprocessor macro against nine modes (plain model, Verilator DUT, VCS model-only, VCS per topology,
Xcelium model-only, Xcelium per topology, `gen`/`db` alone, `clean`, and the container Verilator build). Full text in the agent report
(scratchpad); findings, ranked:

Confirmed defects
1. **Non-templated SC wrapper has no Xcelium branch** (`templates/systemc/module_hdl_wrapper.py` preamble `#if defined(VCS_DUT)` / `#else
   V<top>.h`; class body still `#if !defined(VERILATOR) && defined(VCS)`). Under `XCELIUM_DUT` a params-less block's wrapper includes the
   Verilator header. debayer's blocks are all Config-templated so the regressions did not see it; `examples/simple` under Xcelium would.
   The view already carries `xceliumDutHeader`; fix: add it to `sc_concrete_dut`, `#elif defined(XCELIUM_DUT)` in the preamble, and
   `VCS_DUT || XCELIUM_DUT` selecting the SV-named shell in the body.
2. **`make clean USE_XCELIUM=1` leaves `rundir/build`**: `BIN_DIR` is reassigned to `build_xrun`, so the clean line removes `build_xrun`
   twice. Fix: name the default tree once and remove both fixed names.
3. **Nonsensical combinations not rejected**: `USE_VCS=1 USE_XCELIUM=1` defines both macro sets and gives `$(BIN_DIR)/$(BIN)` two recipes;
   `USE_GCC=1 USE_VCS=1` on the farm selects the GCC module rules for Clang. Fix: `$(error)` beside `VL_DUT ?= 1`, and in the pro Clang block.
4. **Change set incomplete for commit**: the four rundir JSON files and the `builder/vcsRun.py` symlink are untracked but referenced;
   `.gitignore` lacks `rundir/build_xrun/**`, `rundir/xcelium*.d/`, `rundir/xrun*.history`, `rundir/vc_hdrs.h`; a stray
   `unittest/tmp*.db-journal`.
5. **Stale `.d` prerequisites after a failed VCS link break the next Verilator build**: registrar `.d` files record `csrc/sysc/include/<top>.h`,
   the failure cleanup removes `csrc`, and the empty-recipe rule for those headers exists only under `USE_VCS`. Fix: `-MP` on the `-MMD`
   compiles (then the header-target rules in `a2c-vcs.mk` go).

Consistency points: `VCS_TESTBENCH`/`XRUN_TESTBENCH` and `VCS_ELAB_ARGS`/`XRUN_ELAB_ARGS` are identical (one `DUT_ELAB_ARGS` beside
`DUT_TOPOLOGY`); `VCS_TOPOLOGIES ?= $(DUT_TOPOLOGIES)` is the last VCS-spelled topology name; `vcsRun.py` serves both simulators but its name,
docstring and error text are VCS-specific; `hdl_param_widths` was added but the two inline copies remain, and the boundary-pin view imports
the template utility for a semantic width (inverts the view/utility dependency) and re-implements `get_intf_type`; `getBDVlBoundaryPins` runs
for every block in every `getBlockData` (gate on `hasVl`); `calcVlTops` calls the private `ValueResolver._structureWidth`; `+define+XCELIUM`
has no SV consumer; `XRUN_GCC_VERS ?= 12.4` is an install-specific choice living in base; simulator `clean::` lines run only under their
switch although the artefacts are in the shared rundir, `rundir/Makefile` duplicates part of that list and keeps `simv.daidir`, and
`run*.daidir` is globbed in the wrong directory; snapshot targets accept `VL_DUT=`; `DUT_TOPOLOGIES` assigned after the include (works
only because every consumer is recursively expanded); the Xcelium run script bakes `XRUN_R_OPTS` and `LM_LICENSE_FILE` without depending
on them; a few historical comments in `a2cProEnv.mk` and a plan reference in `a2c-xrun.mk`; `--vlTrace` accepted but inert under VCS and
Xcelium.

Checked and correct: mode (9) container build unchanged (flags, includes, link line, `BIN=run`, build dir, `GEN_DEPS`); ordering of
`VL_DUT ?= 1`, `BIN_DIR` override, `CXX` flow through pro; `VL_DUT=` behaviour; no `+` on non-make recipe lines; macro sets per mode
exclusive under the outer guard; the `<top>_dut_t` alias and `static_assert` compile identically in all DUT modes; `.f` handling without
duplicates; Python contract reads; ownership split of the boundary data; pro layer holds every farm path and compiler choice.

### 3.28 Review fixes applied and re-verified (agent implementation, 2026-09-16)

All five defects and every consistency item of 3.27 are applied; nothing skipped. `getBDVlBoundaryPins` was removed rather than gated
(its only consumer is `getVlTopBoundaryPins`, which now holds the pin walk).

Changes: non-templated SC wrapper `#if VCS_DUT / #elif XCELIUM_DUT / #else` with the SV-named shell under either simulator
(`sc_concrete_dut` carries `xceliumDutHeader`); `a2c-common.mk` `DEFAULT_BIN_DIR`/`XRUN_BIN_DIR` with `BIN_DIR` selecting, `clean::`
removing both trees and all simulator rundir artefacts unconditionally, `.daidir` globbed under `$(BIN_DIR)`; `$(error)` for
`USE_VCS`+`USE_XCELIUM` (base) and `USE_GCC` with a simulator switch (pro); `-MP` on the four `-MMD` rules and the header-target
workaround rules gone; `DUT_TESTBENCH`/`DUT_ELAB_ARGS` beside `DUT_TOPOLOGY`, `VCS_TOPOLOGIES` gone, snapshot targets error on `VL_DUT=`;
`XRUN_GCC_VERS` moved to pro and required by base; `+define+XCELIUM` dropped; the Xcelium run script depends on an `r_opts` stamp
(`XRUN_R_OPTS` + `LM_LICENSE_FILE`); the eval-DSL width evaluation lives in `projectOpen.hdlParamWidths` (template utilities call the
view, not the reverse), `getVlTopBoundaryPins` uses `get_intf_type`, `ValueResolver.structureWidth()` is public; dispatcher renamed
**`builder/base/dutRun.py`** (symlink `builder/dutRun.py`), simulator-neutral text stating the `DUT_TOPOLOGY` rule; `.gitignore` gains the
five rundir patterns; `rundir/Makefile` sets `DUT_TOPOLOGIES` before the include and drops the obsolete VCS clean lines; both session
files call `../builder/dutRun.py`; comments in `a2cProEnv.mk` and `a2c-xrun.mk` trimmed.

Checks (logs in scratchpad `fix/`):

| Check | Result |
|---|---|
| `make db && make gen` | clean, 3.7 s; only regenerated files in status |
| `USE_VCS=1 USE_XCELIUM=1`, `USE_GCC=1 USE_VCS=1` | both fail with the new errors |
| `make clean` plain / `USE_VCS=1` / `USE_XCELIUM=1` | each removes `build`, `build_xrun`, AN.DB, csrc, daidirs, `vc_hdrs.h`, logs, `xcelium*.d`, `xrun*` |
| plain Verilator dry run | 71 `-MP`, 103 `-DVERILATOR`, no `-DVCS`/`-DXCELIUM` |
| VCS ten snapshots | 3 min 30 s; `/hdl_tests/default/debayer` 2/2, `/model_tests/tandem` 12/12 |
| Xcelium ten snapshots | 4 min 38 s; `/hdl_tests/default` 6/6, `/model_tests` 20/20 |
| non-templated wrapper under Xcelium (`examples/simple`) | wrapper TU compiles via `simple_hdl_sv_wrapper_xcelium.h`, snapshot elaborates; the run hits the watchdog, and so does the same example under Verilator (pre-existing testbench issue, not the fix). `hierVlDemo`/`axi4sDemo` compile the wrapper TU but xmvlog rejects `wire int unsigned` (`SVNT2S`) in their RTL |
| template unit tests (8) then full suite | all rc 0; 130/130 in 2 min 38 s |
| `make clean && make -j4 -k pipeline-test` | 8 min 15 s; the same two environment failures as 3.26, nothing else |

Untracked files the owner must add: debayer `rundir/regr_debayer_vcs.json`, `rundir/regr_debayer_xcelium.json`, `rundir/vcs.json`,
`rundir/xcelium.json` (and `rundir/regr_debayer_vlbase.json` if the host Verilator baseline session is kept); builder `dutRun.py` symlink;
base `dutRun.py`, `include/make/a2c-vcs.mk`, `include/make/a2c-xrun.mk`, `pysrc/vlBoundaryGen.py`, the two `plans/*.md`.

New observations: the `simple` example testbench never reaches end of test in any DUT flow; `hierVlDemo.sv` and `axi4sDemo.sv` use
`wire int unsigned`, which Xcelium rejects.

### 3.29 Example RTL portability: `wire int unsigned` replaced (coordinator, 2026-09-16)

`examples/hierVlDemo/rtl/hierVlDemo.sv` and `examples/axi4sDemo/rtl/axi4sDemo.sv` declared two part-select bases as
`wire int unsigned x = <expr>;`. A net with a 2-state type is illegal (IEEE 1800 6.5); Verilator accepts it, Xcelium rejects it
(`xmvlog *E,SVNT2S`). Both now declare `int unsigned bit_base, byte_base;` driven by `assign` (user-owned RTL, outside generated regions).
Checks: `make lint` clean in both `rtl/` directories; base targets `make hierVlDemo axi4sDemo` (Verilator flow) pass with `No error`;
`make USE_XCELIUM=1 ... all` in both rundirs compiles the RTL and writes the snapshot (`build_xrun/run_<top>_verif`). Note for example
builds: the examples do not include the pro layer, so `XRUN_GCC_VERS=12.4`, `XCELIUM_TOOLS`, `XRUN`, `XRUN_BOOST_LIBS` and
`LM_LICENSE_FILE` must be given on the command line or in the environment.

Run on the Xcelium snapshots (`build_xrun/run_<top>_verif <top> --vlInst <top>`): both examples complete with `No error`, the
`axi4s_s_drv` receiving all four frames through the RTL and stopping at 20490 ns with the same final interface state as the Verilator
run (0.6 s wall under Xcelium, 0.09 s under Verilator). This also supplies the run check for the non-templated SC wrapper fix that 3.28 could
not reach on `simple`: a params-less block's wrapper works under `XCELIUM_DUT` end to end.

### 3.30 Clang 20.1.8 on the farm host (agent experiment, 2026-09-16, read-only, scratch install)

Question: the container uses Clang 20.1.8; can the farm use the same? Asset `LLVM-20.1.8-Linux-X64.tar.xz` (1.9 GB) from the
`llvmorg-20.1.8` release; the driver plus `lib/clang` extract to 334 MB.

- Runs on this host: highest symbol version required is `GLIBC_2.34`, exactly the host's glibc; no missing libraries; no `libtinfo`
  warning (Clang 18's build had one).
- Probe (`<format>`, `<version>`, `-std=c++23`) against the GCC 13.2 headers: clean.
- debayer plain model build with the 3.4 recipe (`BIN_DIR=build_clang20`): rc 0, 44.7 s; run `No error`. Every `-fmodule-file=` flag
  accepted unchanged; no module, PCM, BMI or DWARF diagnostics. Warning set identical in kind to Clang 18 (Boost deprecations, shadow,
  sign-compare).
- Verilator RTL build: rc 0, 59.1 s; whole-design verif `No error`, 30.4 s CPU (Clang 18: 30.8 s).
- Defaults identical to Clang 18: `__cplusplus` 201703L without `-std`, DWARF 5 with `-g`, `-std=c++2b` accepted. So the VCS-only
  `-gdwarf-4` stays necessary and sufficient; `CPP_STD = c++2b` needs no change.

Conclusion: no issue found; adopting Clang 20.1.8 on the farm needs only a persistent install (same trimmed layout as 4.) and the
`A2C_CLANG` path in `a2cProEnv.mk`. Not exercised: the VCS and Xcelium link steps with Clang 20 objects (same libstdc++, so no ABI change
is expected, but run the two regressions once after switching). Scratch copy at scratchpad `llvm20/`; `rundir/build_clang20` removed.

### 3.31 Clang 20 on RHEL 9 (both regressions pass) and RHEL 8.10 portability (agent runs, 2026-09-16)

Clang 20.1.8 installed at `/ldc/projects/qistor/users/atomlin/tools/llvm-20.1.8` (same trimmed layout as 4.), pro pointed at it, clean
rebuild: **VCS 44 of 44** (run 19 min 10 s at three jobs, session `regr/regr_debayer_vcs.atomlin.2026-16-09-153312.434058`) and
**Xcelium 44 of 44** (run 9 min 35 s at six jobs), objects confirmed Clang 20 from their `.comment` sections. So the flows are
compiler-version agnostic across Clang 18 and 20 on RHEL 9.

RHEL 8.10 check (node `ldc-farm06`, kernel 4.18.0-553, glibc 2.28; 101 of 501 farm hosts report `RHEL8.10`). LSF notes: no boolean
resource selects RHEL 8 and `select[ostype==RHEL8.10]` does not filter in this LIM configuration; `lshosts -o "hname ostype"` plus
`bsub -m <host>` is reliable; queue `interactive` refuses batch jobs, `short`/`long` work. `setup.bash` has no per-OS branch
(`LDC_RHEL_ENV=1` on both releases).

| Component | RHEL 8.10 |
|---|---|
| Clang 18.1.8 | works (probe compiles) |
| Clang 20.1.8 | cannot start: `GLIBC_2.29`, `2.32`, `2.33`, `2.34` not found |
| Verilator 5.038 | works (Perl wrapper; C++ via Clang 18) |
| OpenCV 4.12 `.so`, VCS `libsystemc.so` | within glibc 2.28 (highest `GLIBC_2.27` / `2.14`) |
| System Boost | only `libboost_program_options.so.1.66.0` (RHEL 9: 1.75.0) |
| Python 3.10.13 (site) | imports yaml, jinja2, ctypes |
| `xrun`, `vcs` binaries | run |
| Plain model + Verilator, Clang 18 | `No error` |
| VCS, Clang 18 | compile, vlogan, elaboration pass; VCS's internal link make fails `make[2]: *** read jobs pipe: Bad file descriptor` (GNU make 4.2.1 rejects inherited `--jobserver-auth` with closed descriptors; make 4.3 on RHEL 9 tolerates it) |
| Xcelium, Clang 18 | default 1.75 path: `ld: cannot find`; with `XRUN_BOOST_LIBS=.../so.1.66.0`: `No error` (1.74 headers against the 1.66 runtime worked for this program) |

Decision (owner, 2026-09-16): the farm compiler must work on both releases, so the pro layer returns to Clang 18.1.8 (the Clang 20 install
stays for the container-parity record). Changes in flight (3.32): `A2C_CLANG` back to Clang 18; `XRUN_BOOST_LIBS` chosen by
`/etc/os-release` `VERSION_ID` major in pro; the VCS link recipe clears `MAKEFLAGS`/`MFLAGS` for the `vcs` call so its internal make does
not inherit this make's jobserver. Logs: `rundir/rh8probe/` (NFS, untracked) and scratchpad `rh8/`, `clang20/`.

### 3.32 Farm setup scripts: proposed update for the tools owner (2026-09-16)

`/ldc/projects/qistor/setup` is owned by the tools owner account and read-only for users. Today it holds `setup.bash/.csh` (sources the
two below), `a2c_rhel_setup.bash/.csh` (site tools PATH, OpenCV `LD_LIBRARY_PATH`, `LDC_RHEL_ENV=1`), `vcs_systemc_gcc13.bash/.csh`
(VCS_HOME, Synopsys licence, VCS SystemC 2.3.4 gcc13, site Boost, VG_GNU gcc 13.2, Verdi) and an empty `xcelium.csh`. No per-OS branch.

Complete updated copies for the owner are staged in `/ldc/projects/qistor/users/atomlin/setup-proposed/` with a README:
`a2c_rhel_setup.*` export `A2C_CLANG=/ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++`; new `xcelium.bash/.csh` export
`XCELIUM_ROOT`, `XCELIUM_TOOLS`, `XRUN_GCC_VERS=12.4`, `LM_LICENSE_FILE`; `setup.*` source them. The pro makefiles keep the same values as
`?=` defaults, so the scripts are the site's single source and the makefiles still work without them (the agent in 3.31 is making
`XRUN_GCC_VERS` `?=` too). The Xcelium Boost `.so` stays a makefile choice from `/etc/os-release`, so the scripts are OS-independent.
Checked: `bash -n` clean; sourcing the drafts yields the expected values and `clang version 18.1.8`.

### 3.33 RHEL 8.10 and 9.6 both pass with the shared Clang 18 (agent implementation and verification, 2026-09-16)

Changes (unstaged): `a2cProEnv.mk` `A2C_CLANG ?= /ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++` (comment: newest prebuilt Clang
that runs on both farm releases), `XRUN_BOOST_LIBS ?=` chosen from `A2C_OS_MAJOR := $(shell . /etc/os-release && echo $${VERSION_ID%%.*})`
(8: `.so.1.66.0`, else `.so.1.75.0`), `XRUN_GCC_VERS ?= 12.4`; `a2c-vcs.mk` link recipe runs `MAKEFLAGS= MFLAGS= $(VCS) ...` so VCS's
internal make inherits no jobserver descriptors (`a2c-xrun.mk` spawns no make; unchanged).

| | RHEL 9.6 `lrd-farm-rh9-66` | RHEL 8.10 `ldc-farm06` (LSF job 4889895) |
|---|---|---|
| `make clean && make db && make gen` | clean | clean (gen 4 min 15 s on that node) |
| `make -j8 USE_VCS=1 all` + debayer verif run | 2 min 48 s; `No error`, 93.8 s CPU | 3 min 31 s; `No error` (run 3 min 57 s wall) |
| `make -j8 USE_XCELIUM=1 all` + debayer verif run | 3 min 03 s; `No error`; Boost `.so.1.75.0` | 4 min 25 s; `No error`; Boost `.so.1.66.0` selected automatically |
| Compiler in the build logs | shared llvm-18.1.8 | shared llvm-18.1.8 |
| VCS internal-make jobserver error | none | none |

New (cosmetic) warning in every VCS link: `gmake[2]: warning: jobserver unavailable: using -j1`, the expected effect of clearing the
jobserver for VCS's internal make (its compile is under a second). The staging copy `/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8`
was removed after this verification; the shared install is the only Clang 18. The Clang 20 test copy remains under
`/ldc/projects/qistor/users/atomlin/tools/llvm-20.1.8`. Logs: scratchpad `rh8fix/`, `rundir/rh8probe/` (untracked NFS directory, can be deleted).

### 3.34 Container verification of the change set (container agent, 2026-09-16; report `plans/handoff-container-verify-report.md`)

Environment: `a2c-dev:2.0` (Ubuntu 22.04.5), Clang 20.1.8, graphviz 2.43.0, tree at `/work/ws/debayer`, no simulator switches set.

| Check | Result |
|---|---|
| `make clean && make db && make gen` | clean; `git status` matches the change-set inventory exactly |
| boundary artefacts | `.gen/vl` absent; plain `make -n gen` has no `--vlBoundary`; `USE_VCS=1 USE_XCELIUM=1` rejected |
| plain model | `No error`; `-MP` present, no simulator macros |
| Verilator RTL: verif, tandem, u_preprocess | all `No error` (28 s, 37 s, 53 s); `static_assert` widths as expected |
| `make regr` (44 tests, 8 jobs) | **44 of 44**, 3 min 53 s |
| unit tests (parallel runner) | **130 of 130**, 2 min 46 s, no retries |
| `make pipeline-test` | **26 of 26**: `diagram-and-doc` passes (graphviz 2.43 matches the golden) and `pySocket` passes (its Python imports `ctypes`) |
| generated-text spot checks | three-way DUT selection in the SC wrapper and registrar as designed |

Deviation: the handoff's dry run `make -n USE_VCS=1 gen` stops at the parse-time `VCS_HOME` guard in `a2c-vcs.mk` (an `$(error)` fires
while make parses, before `-n` applies); with `VCS_HOME=/nonexistent` the dry run shows the boundary pass as expected and executes
nothing. Handoff text corrected. Observations: `unittest/tmpy7kz9g0x.db-journal` was a tracked stray file, now deleted (a ` D` in
status to be committed with the set); 85 modified example files (two more than the 83 counted after the unit tests; both are
regenerated outputs). The container's `make clean` rewrote `.gen/build.mk` with `/work` paths, so the farm tree needs
`make clean && make db && make gen` before its next build (done, 3.35).

Conclusion: the change set is neutral for the container Verilator flow and passes every CI check there; the farm and the container
now agree on all three suites.

### 3.35 Farm tree resynced after the container run (coordinator, 2026-09-16)

`make clean && make db && make gen` in `rundir` on the farm: rc 0; `.gen/build.mk` records `/home/atomlin/ws/debayer` paths again
(the container run had left `/work/ws/debayer`). Rule restated: after any build from the other environment, run `make clean` before
`make db` because the generated manifest and the dependency files hold absolute paths. Example modified-file count is 85 (both
environments agree).

### 3.36 Second review (build includes and boundary macros) reproduced, fixed and re-verified (agent run, 2026-09-16)

Review file: `plans/review-build-include-macro-changes.md` (static review by another agent). All five findings reproduced and fixed:

1. **Transit structures missing from `VLTOPS`** (high): a block never instantiated in the project (exported leaf, `hasVl`, no `params:`) is
   never marked parameterizable, so its structures were absent from `blockParameterizedDecls` and `getVlTopBoundaryPins` raised
   `KeyError`. `calcVlTops` now also resolves the parameterizable structures reached through the block's declared ports. Test
   `unittest/test_vl_boundary_pin_widths.py::test_paramsless_transit_leaf_boundary_pins`.
2. **Eval-derived pins at nominal width** (high): AXI4-Stream `tstrb`/`tkeep` for a `WIDTH=32` variant came out sized for the 8-bit
   default. `hdlParamWidths(intfDef, structParams, structWidths)` now evaluates against the top's resolved widths; `intfEvalDSL` takes a
   width. The two wrapper-template call sites keep nominal widths (`{}`), unchanged behaviour, outside this review's scope. Test
   `...::test_axi4_stream_non_default_variant_strobe_width`. Incidental: a block with no ports crashed the new walk (`axi4sDemo`);
   optional subtables are now read as optional. debayer widths (35, 99, 323) unchanged.
3. **Topology name collisions** (medium): dots are kept in `DUT_TOPOLOGY` and `dutRun.py` identically; names are now
   `run_debayer.u_preprocess_verif`, `xcelium_debayer.u_preprocess_verif.d` (earlier sections keep the historical spelling).
4. **Stale snapshots on option changes** (medium): the analysis stamp covers `VLOGAN_OPTS`, include dirs and source lists; the link stamp
   `VCS_OPTS`/`VCS_ELAB_OPTS`/`LD_FLAGS`; the xrun stamp also `XRUN_LD_LIBS` and the HDL compile command. Verified by `make -n` before and
   after an option change.
5. **Xcelium-only setups** (low): the `SYSTEMC_INCLUDE`/`SYSTEMC_LIBDIR`/`LD_BOOST` checks are skipped under `USE_XCELIUM`;
   `env -u ... make -n USE_XCELIUM=1 all` parses, the plain flow still errors.

Re-verification: `make clean && make db && make gen` clean; unit tests **131 of 131** (new suite included), 5 min 40 s; VCS
`vcs_snapshots` + `make regr_vcs` **44 of 44** (19 min 35 s); Xcelium `xrun_snapshots` + `make regr_xcelium` **44 of 44** (9 min 53 s);
`pipeline-test` 24 of 26 with the same two environment failures. Logs: scratchpad `review2/`. The deleted tracked
`unittest/tmpy7kz9g0x.db-journal` stays deleted; commit it separately as the reviewer suggested.

### 3.37 Farm setup scripts installed and verified (2026-09-17)

The tools owner installed the 3.32 proposal into `/ldc/projects/qistor/setup` (all eight files byte-identical to the staged copies, plus the
README). In a clean shell (`env -i`, only `HOME`/`USER`/`PATH=/usr/bin:/bin`), `source setup.bash` yields `A2C_CLANG` (shared Clang 18),
`XCELIUM_TOOLS`, `XRUN_GCC_VERS=12.4`, `LM_LICENSE_FILE` (nine servers), `LDC_RHEL_ENV=1`, `VCS_HOME`, `SNPSLMD_LICENSE_FILE`, and the
VCS_GNU gcc 13.2 on `PATH`; `clang version 18.1.8` and `xrun 26.03-s002` answer. Under that environment alone (no command-line
variables): `make -j8 USE_XCELIUM=1 all` + debayer verif run `No error` (69.8 s CPU); `make -j8 USE_VCS=1 all` + run `No error`
(93.4 s CPU); the VCS compile line uses the shared Clang path. The scripts are now the site's single source for the farm settings, with
the pro makefiles keeping the same values as `?=` defaults.

### 3.38 Pro makefile carries no farm defaults; setup scripts v2 proposed (agent implementation, 2026-09-17)

Owner rule: checked-in makefiles must not default to site paths, licence servers or tool versions; defaults describing the standard
container stay in base. `a2cProEnv.mk` now requires, with an `$(error)` naming the setup script: always (under `LDC_RHEL_ENV`)
`A2C_TOOLS_LOCAL` and `VERILATOR_ROOT`; under `USE_VCS`/`USE_XCELIUM` `A2C_CLANG`; under `USE_XCELIUM` `LM_LICENSE_FILE` and
`XRUN_BOOST_LIBS` (`XCELIUM_TOOLS` and `XRUN_GCC_VERS` already error in base). Derived, kept: `XRUN = $(XCELIUM_TOOLS)/bin/xrun`, the
OpenCV include/lib flags from `A2C_TOOLS_LOCAL`, `-lstdc++fs`, the gcc-on-PATH detection and Clang header wiring, `-gdwarf-4` under VCS,
the `USE_GCC` exclusivity error. The makefile no longer overrides `SYSTEMC_INCLUDE`; the setup script exports the patched-header path.
`grep -nE "/ldc|/tools/dist|virtlic|1725@|5280@|12\.4|1\.66|1\.75" pro/include/make/*.mk` matches only `$(error ...)` text.

Setup scripts v2 (staged in `/ldc/projects/qistor/users/atomlin/setup-proposed/`, README rewritten): `a2c_rhel_setup.*` add
`A2C_TOOLS_LOCAL=/ldc/projects/qistor/tools/local` and `VERILATOR_ROOT=/ldc/projects/qistor/tools/share/verilator`;
`vcs_systemc_gcc13.*` export `SYSTEMC_INCLUDE=$A2C_TOOLS_LOCAL/include/vcs/systemc234` (OpenCV-safe patched headers) instead of the stock
VCS path; `xcelium.*` choose `XRUN_BOOST_LIBS` from `/etc/os-release` `VERSION_ID` major (8: 1.66, else 1.75). **Until v2 is installed,
farm builds of this tree fail at the new `A2C_TOOLS_LOCAL`/`VERILATOR_ROOT`/`XRUN_BOOST_LIBS` errors when only the installed v1 scripts
are sourced.**

Verification with the v2 scripts sourced in a clean shell: missing-variable errors fire for each of the four required variables;
RHEL 9.6: VCS build 1 min 22 s, run `No error` 91.4 s CPU; Xcelium build 1 min 58 s, run `No error` 70.9 s; plain Verilator flow
`No error` 32 s. RHEL 8.10 (`ldc-farm06`, LSF job 4933225): VCS and Xcelium build and run `No error`, Boost `.so.1.66.0` chosen by the
script. Farm tree resynced afterwards. Logs: scratchpad `nodefaults/`, `rundir/rh8probe/nodefaults.*`.

### 3.39 Session restart note (2026-09-17, 14:54)

The Claude Code process restarted; the node-local scratch directory referenced as "scratchpad `<name>/`" in sections 3.13 to 3.38 was
wiped, so those logs are gone (the results recorded here stand; the NFS logs under `rundir/rh8probe/` and the regression session
directories under `rundir/regr/` remain). The Boost consolidation task (OS shared Boost for every farm flow, header-only stacktrace,
`A2C_BOOST_LIBS`, setup scripts revision 3) had not landed any edit before the restart and was restarted from scratch (3.40).

### 3.40 OS shared Boost for every farm flow; static site Boost unused (agent implementation plus coordinator follow-up, 2026-09-17)

Owner decision: link Boost from the OS shared library in every flow so the static Boost under `/ldc/projects/qistor/tools/local/lib`
can be dropped. Headers stay the site Boost 1.74.

Changes (unstaged): base `a2c-systemc.mk` uses header-only stacktrace everywhere (`-DBOOST_STACKTRACE_LINK`, `-lboost_stacktrace_basic`
and `-lboost_system` gone; `-ldl` stays), `BOOST_LIBS ?= -lboost_program_options -L$(LD_BOOST)` is the container default link input and
the `LD_BOOST` check fires only when that default is in use; `a2c-xrun.mk` builds `XRUN_LD_LIBS` from `BOOST_LIBS` (`XRUN_BOOST_LIBS`
gone). Pro requires `BOOST_LIBS` from the environment under `LDC_RHEL_ENV` (no `A2C_` alias: the setup scripts export base variable names,
as they do for `SYSTEMC_INCLUDE` and `VERILATOR_ROOT`), so non-pro builds such as the unit-test fixtures pick it up too. Setup scripts
revision 3: `a2c_rhel_setup.*` export `BOOST_LIBS` chosen per OS (RHEL 8 `-L/usr/lib64 -l:libboost_program_options.so.1.66.0`, else
`.so.1.75.0`); `vcs_systemc_gcc13.*` drop `LD_BOOST`; `xcelium.*` drop the Boost choice. Two tokens with the `-l:` exact-soname form are
needed because `vcs` parses a bare `.so` path on its command line as a Verilog source (`Error-[SE]`). Four unit tests
(`test_thunker_runtime`, `test_inherit_vl_child`, `test_regs_handler_container_config`, `test_container_param_cross_project_vl`)
honour `BOOST_LIBS` and require `LD_BOOST` only when it is absent; `test_thunker_runtime` mirrors the makefile link (header-only stacktrace).

`-fno-pie -no-pie` stays in the plain-flow recipe and the Clang wrapper, for a reason unrelated to Boost: the VCS_GNU gcc 13.2 toolchain
defaults to non-PIC code (`-fPIC`/`-fPIE` disabled), and Verilator's runtime and the verilated library are always compiled with it, so a
position-independent final link fails on those objects. Reproduced with a fully shared-Boost link.

Verification with `LD_BOOST` unset and the revision 3 scripts sourced in a clean shell: RHEL 9.6 plain + Verilator `No error`; VCS
`No error` 87.0 s CPU, `ldd` resolves `/lib64/libboost_program_options.so.1.75.0`; Xcelium `No error`, link `-Wld,-l:libboost_program_options.so.1.75.0`;
error path (`--vlInst nosuch`) exits 1 with the assertion and a backtrace as before; unit tests **131 of 131**; RHEL 8.10 (`ldc-farm06`,
LSF job 4955253) clean/db/gen, VCS, Xcelium and plain Verilator all `No error` resolving `.so.1.66.0`. Owner action after installing
revision 3: remove `libboost_program_options.a`, `libboost_system.a`, `libboost_stacktrace_basic.a` from `/ldc/projects/qistor/tools/local/lib`
(headers stay). Logs: scratchpad `boost/`, `rundir/rh8probe/boostprobe/`.

## 4. Installed artifacts

- `/ldc/projects/qistor/tools/share/llvm-18.1.8/` (258 MB, trimmed; final shared location since 2026-09-16 15:28, copied by the tools
  owner account, read-only for users; identical file list to the staging copy `/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8`,
  which is removed once the pro layer points at the shared path). Contents: `bin/clang-18` (+ `clang`, `clang++` symlinks),
  `lib/clang/18` (resource headers and runtimes). Verified: compiles `<format>` with `-std=c++23` against the VCS_GNU gcc 13.2
  headers. The full 7.1 GB extraction lives only in the session scratch area and can be discarded.

Install recipe (2026-09-15, run from a scratch directory; the full extraction is 7.1 GB, the trimmed install 258 MB):

```
curl -sSL -o llvm18.tar.xz https://github.com/llvm/llvm-project/releases/download/llvmorg-18.1.8/clang+llvm-18.1.8-x86_64-linux-gnu-ubuntu-18.04.tar.xz
tar -xJf llvm18.tar.xz
SRC=$PWD/clang+llvm-18.1.8-x86_64-linux-gnu-ubuntu-18.04
DST=/ldc/projects/qistor/tools/share/llvm-18.1.8   # final location (tools owner account); staged first under /ldc/projects/qistor/users/atomlin/tools
mkdir -p $DST/bin $DST/lib
cp -a $SRC/bin/clang-18 $SRC/bin/clang $SRC/bin/clang++ $DST/bin/
cp -a $SRC/lib/clang $DST/lib/                     # resource headers and runtimes (lib/clang/18)
$DST/bin/clang++ --version                          # clang version 18.1.8
$DST/bin/clang++ --gcc-install-dir=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0 \
    -std=c++23 -c probe.cpp -o /dev/null            # probe.cpp: #include <format> / <version>; must compile
```

Only the driver and its resource directory are needed: Clang is used with the GCC 13.2 headers and libraries (`--gcc-install-dir`), so
`lib/libclang*`, `lib/libLLVM*`, the other tools and the bundled libc++ were left out. The prebuilt binary needs glibc >= 2.27 (RHEL 9 has
2.34) and prints a harmless `libtinfo.so.5: no version information available` warning.
- No repository files were modified for the experiments. `debayer.db`, `.gen/`, `rundir/build/` are regenerated (all git-ignored).

---

## 5. Proposed work breakdown and open decisions

Ordered so that each step is independently testable. Items marked (pro) belong to `builder/pro`, (base) to `builder/base`,
(prj) to the debayer repo.

1. **Runtime DUT selection under VCS/Xcelium (base).** (See §3.12 for the history; the fix also has to cover stale items 3-5 there.) Remove the `#ifndef VCS` around `--vlInst/--vlType/--vlTandem/--vlTrace`
   in `common/systemc/simController.cpp:33` and stop pinning them via `-DVL_*` in `rundir/Makefile:19-24` (prj). One snapshot then
   serves all nine regression combinations. Keep `-DVCS`/`-DXCELIUM` for the simulator-specific glue only. Prerequisite for 5 and 6.
2. **Wire Clang 18 into the pro layer (pro).** `a2cProEnv.mk`: `A2C_CLANG ?=` -> `/ldc/projects/qistor/users/atomlin/tools/llvm-18.1.8/bin/clang++`
   (or a site-wide location once available); honour `A2C_CLANG` in the non-VCS host flow too (today `USE_GCC := 1`, `CXX = g++`),
   with `-fno-pie -no-pie` for the Clang-driven link. Decision: owner of `builder/pro`.
3. **VCS native DUT (base + pro).**
   a. `a2c-vcs.mk`: `vlogan -sverilog -sysc -sc_model <top> -sc_portmap <top>.portmap` for each of the five trampolines
      (`A2C_VL_TOPS`) over `a2c.f` + `rtl.f` + `A2C_SV_FILES` + `+incdir+verif`; then `vcs -sysc=234 ... sc_main <objs>` as today plus
      `-timescale=1ns/1ps -kdb -debug_access`. Emit the portmap (bit vectors -> `sc_bv<N>`, 1-bit -> `bool`) from the same port view the
      SC wrapper template uses; a2c already knows every pin name and evaluated width.
   b. `vlRegistrar.py`: add `#elif defined(VCS)` branch: `#include "<top>.h"` and register `<blk>_hdl_sc_wrapper<<top>, Config>`.
   c. `a2c-systemc.mk:170-181`: VCS branch adds `-I$(PROJECT_RUNDIR)/csrc/sysc/include` (already in `rundir/Makefile:29`) and no verilated lib.
   d. Smoke: `--vlInst debayer --vlType verif` synthetic-data test, then tandem, then sub-block trampolines.
4. **Xcelium native DUT (base + pro).**
   a. Compiler/ABI recipe: §3.10 (proven); full DUT prototype: §3.14 (proven, verif and tandem). Clang 18 + GCC 13.2 libstdc++ objects with Cadence defines/includes; `xrun -64bit -sysc -sc_main -gcc_vers 12.4 <objs>`;
      direct `tools/bin/xrun` with `LM_LICENSE_FILE` exported. Only the `.o` set changes per project; build an `a2c-xrun.mk` around it.
   b. Foreign-module DUT class: a2c-emitted `<top>_foreign.h` (`ncsc_foreign_module` subclass, `hdl_name()` = trampoline, `sc_in/sc_out`
      of `bool`/`sc_bv<N>`), registered under `#elif defined(XCELIUM)` in `vlRegistrar.py`. Emitting it ourselves avoids depending on
      Cadence's wrapper generator and mirrors 3a's portmap.
   c. `a2c-xrun.mk`: `xrun -sysc -sc_main -gnu -f a2c.f -f rtl/rtl.f <trampolines> <objects/archive> -top <trampolines> -timescale 1ns/1ps`,
      `-iusld` handling, `-Wld` for any extra libraries (Boost, OpenCV), `-DXCELIUM -D_GLIBCXX_USE_CXX11_ABI=1`.
   d. `main.cpp`: `catch (xmsc_elab_exception&) { throw; }` ahead of `catch(...)` under `XCELIUM` (§3.8); hierarchy prefix `sc_main` as for VCS.
   e. Smoke as in 3d. Note the LSF wrapper: use `$X/tools/bin/xrun` with `env.csh` variables exported, or accept LSF submission in the launcher.
5. **Regression (prj + base).** Session files `regr_debayer_vcs.json` and `regr_debayer_xrun.json` (or a `${SIM}` substitution) with
   simulator `build.command`s and realistic build timeouts; labels `vcs`/`xrun`; rules for `Error-[...]` (VCS) and `xmsim: *E` (Xcelium).
   `make regr_vcs` / `make regr_xrun` targets in `rundir/Makefile`.
   **Status 2026-09-15:** VCS half done and passing 44 of 44 (3.18: `vcs_snapshots`, `vcsRun.py`, `regr_debayer_vcs.json`, `vcs.json`,
   `regr_vcs`); no `vcs` label was added since the session file is simulator-specific. Xcelium half open.
6. **SystemC 3.0.1 convergence (optional, decided acceptable).** After the 2.3.4-based VCS RTL prototype works, evaluate
   `VCS_HOME=X-2025.06-SP2-5` (or Y-2026.03-1) with `-sysc=301` and `systemc301-gcc13`, and Xcelium `-sc_301`; check the
   patched-SystemC include (`/ldc/projects/qistor/tools/local/include/vcs/systemc234`, OpenCV int64 collision) has a 3.0.1
   equivalent or is no longer needed. Different toolchains/SystemC per simulator are acceptable.
7. **Housekeeping.** `docs/vcs-build.md` -> point to this plan; template fix for the `TMBIN` literal in generated `_regs.sv` (§3.7);
   review `assign #0` at the boundary under event-driven simulators (risk 4 in §3.9).

**Requirement (user, 2026-09-15): the final solution must not add simulation-time overhead.** debayer is a small design; a
complete SoC will use this flow. Consequences and checks:
- Runtime DUT selection is a construction-time factory lookup; it must add no per-cycle work. Uninstantiated `-sc_model` tops in
  the one-snapshot scheme must cost nothing at run time (verify with VCS `-simprofile` or CPU-time comparison of a one-top vs
  five-top snapshot on the same test).
- The SystemC/HDL boundary (BFMs, `sc_signal` bundles, `assign #0` in the `.svh`) is per-cycle. Measure verif CPU time at
  `--verbosity=low` for the same test under Verilator (container reference), VCS native and Xcelium native; investigate any
  boundary overhead (delta cycles at `#0`, `sc_bv` packing in the BFMs) before declaring done. Prototype datum (§3.13):
  verif two synthetic frames, `--verbosity=medium`, CPU 208 s under VCS versus 10.6 s for the model-only run; logging dominated wall time,
  so a low-verbosity re-measurement is needed before drawing conclusions.
- Prefer simulator-native tracing controls (FSDB/SHM plusargs) that are off by default; no always-on instrumentation.

**Decisions taken 2026-09-15 (user):**
- VCS flow home: generic controls and environment variables in the `builder`/`builder/base` makefiles (`a2c-vcs.mk` beside
  `a2c-vl-wrap.mk`); an additional pro makefile covers the Lattice farm environment (Clang 18 path, GCC 13 headers, `-gdwarf-4`,
  licences), or setup scripts under `/ldc/projects/qistor/setup`. `rundir/Makefile` loses its hand-written VCS recipe.
- DUT selection: **runtime, one snapshot.** All five `A2C_VL_TOPS` are `-sc_model`'d into one `simv`, all five registered; the
  `--vlInst/--vlType/--vlTandem` options are restored under VCS so `regr_debayer.json` runs unchanged.

Open decisions for the user/owners: (i) where Clang 18 lives long-term (user area vs `/ldc/projects/qistor/tools/local`, which is
read-only to this account); (ii) **decided 2026-09-15:** Xcelium may target SystemC 3.0.1 (`-sc_301`); SystemC had only been held at 2.3.4 for VCS compatibility. It is also acceptable for VCS and Xcelium to use different toolchains and SystemC libraries;
(iii) whether regression under VCS/Xcelium runs through LSF (the PATH `xrun` wrapper submits jobs) or on the local host.

## 6. Reproduction cheat-sheet

```
# one-time
source /ldc/projects/qistor/setup/setup.bash        # farm env: LDC_RHEL_ENV, VCS_HOME, VCS_GNU gcc 13.2 on PATH
CLANG18=/ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++
GCC13=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0

cd debayer/rundir
make clean && make db && make gen                    # required after switching container <-> host

# plain SystemC model (no simulator); add VL_DUT=1 for the Verilator RTL DUT (Verilator 5.038 is on the host)
make -j8 USE_GCC= CXX="$CLANG18 --gcc-install-dir=$GCC13 -fno-pie -no-pie" [VL_DUT=1]   # -no-pie: VCS_GNU g++ builds non-PIC Verilator objects; Boost comes from BOOST_LIBS (setup.bash)
./build/run debayer --verbosity=medium [--vlInst debayer --vlType verif [--vlTandem]]

# VCS flow (pro sets Clang 18; USE_VCS implies VL_DUT). One snapshot per DUT topology.
make -j8 USE_VCS=1 all                             # build/run_debayer_verif; VL_INST=debayer.u_preprocess / VL_TANDEM=1 select others
make -j8 USE_VCS=1 VL_DUT= all                     # model-only binary build/run
./build/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif
make -j8 USE_VCS=1 vcs_snapshots                   # build/run_model + one per DUT_TOPOLOGIES entry (<inst>:<type>[:tandem]), sequential links
../builder/dutRun.py build/run debayer --verbosity=low --vlInst debayer.u_preprocess --vlType verif --vlTandem
make regr_vcs                                      # regrLauncher.py --build regr_debayer_vcs.json, 3 jobs (3 licences); JUnit in regr/<session>/test-reports/

# Xcelium flow (pro sets the direct xrun binary and LM_LICENSE_FILE; USE_XCELIUM implies VL_DUT)
make -j8 USE_XCELIUM=1 all                         # snapshot xcelium_<topology>.d + run script build_xrun/run_<topology>
./build_xrun/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif
make -j8 USE_XCELIUM=1 xrun_snapshots              # build_xrun/run_model + one per DUT_TOPOLOGIES entry, elaborated in parallel
make regr_xcelium                                  # regrLauncher.py --build regr_debayer_xcelium.json, 6 jobs
```
