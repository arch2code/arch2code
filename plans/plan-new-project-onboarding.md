# Plan: New Project Onboarding (`newProject.py` rewrite)

**Status:** IMPLEMENTED (2026-08-11). All decisions resolved.
A clean empty repository now reaches a project that builds, links, lints and
starts simulation in one command, verified in both the base-only and pro
setups. See §11 for what was built and where reality differed from this plan.

**Scope:** Replace `pysrc/newProject.py` so that a user starting from a clean,
empty git repository reaches a project that builds and runs, in one command.
The rewrite must serve both the base-only and the pro setups, must ask whether
the project includes firmware, and must create the initial directories and
makefiles.

**Classification:** active. This plan owns the onboarding entry point only. It
does not own layout semantics (`plan-decomp-functional-layout.md`), the
registrar (`plan-reusable-ip-registrar.md`), or YAML format migration
(`plan-yaml-migration.md`); it consumes decisions already locked by those plans.

---

## 1. Current state

### 1.1 What exists today

- Entry point: `arch2code.py:93` calls `newProject(args)` when `--newproject`
  is supplied and neither `--yaml` nor `--db` is given.
- Implementation: `pysrc/newProject.py`, 278 lines, of which roughly 180 are
  two embedded string templates.
- Behaviour: asks for a project name, a YAML directory, a top block name, a
  demo-or-specify choice, a block list and a copyright string. It then creates
  a fixed set of directories and writes exactly one file,
  `<yamlDir>/project.yaml`.

### 1.2 Defect inventory

The following are confirmed by reading the file and the surrounding
configuration. Each is a reason the current program cannot deliver a working
project.

- **The demo path does nothing.** `createDemoProject()` is `pass`
  (`newProject.py:178-179`). A user answering `y` receives a project with no
  blocks at all, and therefore no directories, because `createDirs()` iterates
  over an empty block list.
- **The custom YAML directory is discarded.** The assignment
  `functionalDirectories["yaml"] = configDir` sits inside the branch that runs
  only when the user accepts the default (`newProject.py:139-141`). A user who
  supplies a custom directory has the project file written to the default
  location instead.
- **Mutable class attributes.** `name`, `projDir` and `blocks` are declared at
  class scope (`newProject.py:97-99`). `blocks` is a shared mutable list.
- **The emitted `fileMap` is unresolvable.** The template declares
  `includeFW ... basePath: fwInc` (`newProject.py:85`) while the `dirs:` block
  it emits (`newProject.py:48-55`) never defines `fwInc`. Firmware generation
  is therefore broken in every project the tool has ever produced.
- **Hard-coded post-process paths.** `postProcess:` is emitted as
  `../../builder/base/examples/common/postParseRegister.py`
  (`newProject.py:89-91`). This binds the generated project to one exact tree
  depth and to the `examples/` directory. The base configuration already
  supplies `postProcess:`, so the project should not restate it at all.
- **Massive duplication of base configuration.** The emitted project file
  restates `dirs:`, the full `fileMap` and its forty lines of explanatory
  comments. All of it is inherited from `config/project.yaml`. Compare
  `examples/hierVlDemo/prj/yaml/hierVlDemoProject.yaml`, whose entire `dirs:`
  section is two lines with the comment "only root is supplied; other segments
  + hierarchicalDirs inherit the base config".
- **No layout selector.** `fileGeneration.layout` is never written, so every
  scaffolded project silently inherits the legacy `functional` default. This
  contradicts decision Q-L7 in `plan-decomp-functional-layout.md`, dated
  2026-06-30, which states that brand-new projects must explicitly set
  `layout: hierarchical`.
- **No makefiles.** `rules/skills/setup-project.md:99` documents the
  consequence plainly: "`newProject` scaffolds `project.yaml` and the directory
  tree only; the build `Makefile` and its `include/make/shared.mk` are copied
  from an existing example". Manual copying from an example is the single
  largest onboarding obstacle.
- **The seed design YAML is invalid.** `topTestBenchTemplate` instances
  `u_top` with `instanceType: top`, but no block named `top` is declared in the
  template. The template is also never written to disk by any code path.
- **No git-level bootstrap.** Nothing creates a `.gitignore`, so the first
  `git add` after a build stages the database, `.gen/`, `build/` and `obj_dir/`.

### 1.3 The bootstrap cycle

This is the central structural problem, and it is why the rewrite cannot be a
tidy-up.

- `include/make/a2c-common.mk:199` makes `newmodule` depend on
  `$(A2C_SQLDB_FILE)`.
- `include/make/a2c-common.mk:135` makes `$(A2C_SQLDB_FILE)` depend on
  `$(A2C_PRJ_YAML)`, produced by running `arch2code.py` under `make`.
- The makefiles that `make` needs are themselves scaffolded by
  `newModule.scaffold_create()` (`pysrc/newModule.py:408`), which runs only
  under `make newmodule`.

A clean repository therefore cannot enter the flow: `make` is required to
produce the makefiles that `make` requires. The rewritten `newProject` must
break this cycle from outside `make`.

---

## 2. Target experience

The complete path from an empty repository, for the base setup:

```
git init myChip && cd myChip
git submodule add https://github.com/arch2code/arch2code.git builder
pip3 install -r builder/requirements.txt
./builder/arch2code.py --newproject
make -C rundir run
```

For the pro setup, only the submodule line differs, and recursion is required
because the pro repository carries `base` as its own submodule:

```
git submodule add <pro-repository-url> builder
git submodule update --init --recursive
```

The recursion is not optional in the pro case. The pro repository carries
`base` as its own submodule (`builder/.gitmodules` points at
`git@github.com:arch2code/arch2code.git`), so a non-recursive clone leaves
`builder/base` empty and `builder/arch2code.py`, which is a symlink into
`base/`, dangling.

**Documentation split.** `base/readme.md` is the open-source repository's
readme and documents the base setup only. It must carry no pro instructions and
no site-specific URLs. The pro bootstrap, including the actual repository URL,
lives in the pro repository's own readme (`builder/readme.md`), which is the
first thing a user cloning pro sees. This mirrors the rule already stated in
`pro/include/make/a2cProEnv.mk`: site-specific settings live in pro, and
`builder/base` stays free of them.

Everything after `--newproject` must be produced by the tool. The user answers
a short questionnaire and receives a project that passes `make db` and runs.

**Entry point.** `arch2code.py --newproject` is retained. The entry point is
not architecturally required to be this command, but it is adequate and
changing it would add churn for no functional gain. Two consequences follow
from it being the **first** command a user ever types, and both are treated as
requirements rather than as documentation tidy-up:

- It must appear in `readme.md`. It currently appears in no document at all
  (§4.9.1).
- It is exempt from the "never run `arch2code.py` directly" rule, because at
  time zero there is no makefile to use instead (§4.9.1 item 3).

If the entry point is ever reshaped, the natural target is a `make`-shaped one
for consistency with that rule. That is recorded as open question 6 rather than
adopted here.

---

## 3. Decisions carried in from other plans

These are already locked elsewhere and are treated here as inputs, not as open
questions.

- **Layout for new projects is `hierarchical`.** Decision Q-L7,
  `plan-decomp-functional-layout.md`, dated 2026-06-30. The project file must
  write `fileGeneration.layout: hierarchical` explicitly. `functional` remains
  the merged-config default so that existing projects do not regress.
- **The project file lives at `prj/yaml/<name>Project.yaml`** in hierarchical
  layout, with design YAML under `yaml/`. Confirmed by
  `examples/hierVlDemo` and `examples/simple_ip`.
- **Makefile scaffolding already exists and must be reused, not reimplemented.**
  `config/project.yaml` declares `fileGeneration.scaffold` with four entries
  (`topMakefile`, `sharedMk`, `rundirMk`, `rtlMk`), rendered by
  `templates/fileGen/scaffold.py` and driven by
  `newModule.scaffold_create()`. Files are written only if absent and are never
  rewritten, deliberately ignoring `--overwrite`.
- **The pro overlay requires no branching in scaffolded makefiles.**
  `scaffold.py:69` unconditionally emits
  `-include $(A2C_ROOT)/pro/include/make/a2cPro.mk`. The leading dash makes a
  missing pro tree a silent no-op at make time. The comment at
  `scaffold.py:9-13` states this design intent explicitly.
- **A project declares very little.** The minimum viable project file is
  `yamlFormat: 2`, `projectName`, `projectFiles`, `topInstance` and
  `dirs.root`. Everything else is inherited from `config/project.yaml` through
  the base to pro to user merge in `processYaml.mergeProjectConfig`.

---

## 4. Design

### 4.1 Setup detection: base versus pro

The rewrite must not introduce a new detection mechanism. Exactly one exists in
Python, at `pysrc/processYaml.py:181-211` (`mergeProjectConfig`):

- `a2cRoot` is initially the parent of `pysrc`, that is `builder/base` in a pro
  checkout and `builder` in a base-only checkout.
- If `os.path.exists(a2cRoot + "/../pro")` and the user project does **not**
  live under the base root, `a2cRoot` is promoted to the parent so that
  `pro/config/project.yaml` is merged.
- The `userIsUnderBase` guard exists so that base examples inside a pro
  checkout still build as base-only.

Consequences for the rewrite:

- `newProject` must call `mergeProjectConfig` with the **intended** project file
  path before writing anything. The function needs only the path, not an
  existing file, for the `userIsUnderBase` test, and it returns the merged
  configuration the tool needs in order to know the layout segment names.
- A user project created at the repository root is never under `builder/base`,
  so pro is merged automatically whenever `builder/pro` exists.
- The tool should **report** the detected setup to the user as an informational
  line, for example "Detected setup: pro (builder/pro present)". It must not
  ask the user which setup they have, and it must not write any pro-specific
  content into the project file. The only pro-visible additions are the
  `tandem` fileMap entry, two templates and the `lmmi` interface, all of which
  arrive through the merge with no project-file involvement.

### 4.2 Questionnaire

The questionnaire must be short. Every question must change an emitted
artifact; anything derivable is derived.

| Question | Default | Effect |
| --- | --- | --- |
| Project name | none, required | `projectName`, `PROJECTNAME`, database name, `prj/yaml/<name>Project.yaml`, `regr_<name>.json` |
| Does this project include firmware? | `n` | Adds the `includeFW` fileMap entry, creates `fw/` and `prj/fw/`, adds the two firmware lines to `rundir/Makefile`, emits a firmware entry stub |
| Does this project include RTL? | `y` | Sets `hasRtl`/`hasVl` on the seed DUT block, and governs whether `rtl/Makefile` is scaffolded |
| Copyright statement | empty string | `fileGeneration.fileCopyrightStatement` |

Derived without asking:

- **Layout** is always `hierarchical` for a new project (§3).
- **Directory locations** come from `hierarchicalDirs` in the merged
  configuration, never from a hard-coded table. The present
  `functionalDirectories` dictionary at `newProject.py:18` must be deleted; it
  is a duplicate of configuration that is already authoritative.
- **`TB_TOP_MODULE` and `HDL_TOP_MODULE`** are derived by the existing
  `newModule._deriveTopModules(prj)`, which already inspects the database for
  the testbench top and the single verilated DUT.
- **Block list.** The current tool asks for a list of container blocks. This
  should be dropped. A user who does not yet know their block hierarchy cannot
  answer it, and a user who does will edit the YAML anyway. The seed design
  (§4.4) supplies a working two-block hierarchy that the user renames or
  extends.

### 4.3 Emitted artifacts

For a project named `myChip`, firmware enabled, at repository root:

```
myChip/                            (the git repository root)
├── .gitignore                     new: generated artifacts
├── Makefile                       scaffold: topMakefile
├── include/make/shared.mk         scaffold: sharedMk (+ A2C_PRJ_YAML, see 4.6)
├── prj/
│   ├── yaml/myChipProject.yaml    newProject writes
│   └── fw/                        firmware entry point host (hierarchical)
├── yaml/myChip.yaml               newProject writes: the seed design
├── rundir/Makefile                scaffold: rundirMk
├── rtl/Makefile                   scaffold: rtlMk
├── model/  base/  rtl/  tb/       created on demand by newmodule
├── registrar/  verif/             created on demand by newmodule
└── fw/                            firmware headers, only when firmware enabled
```

The project file itself must be short. Target content, matching the
`hierVlDemo` precedent rather than the current bloated template:

```yaml
yamlFormat: 2

projectName: myChip

projectFiles:
  - ../../yaml/myChip.yaml

topInstance: myChip_tb

dirs: # only root is supplied; other segments + hierarchicalDirs inherit the base config
  root: ../..

fileGeneration:
  layout: hierarchical
  fileCopyrightStatement: "<user answer>"
  # firmware only:
  fileMap:
    includeFW: { name: "IncludesFW", ext: {hdr: "h", src: "cpp"}, cond: {smartInclude: true}, mode: context, basePath: fwInc, desc: "yaml based fw include file" }

instanceGroups:
  top:
    varType: inst_top
    enumPrefix: INST_TOP_

addressObjects:
  memories: { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
  registers: { alignment: 8, sortDescending: true }
```

Note that `fileGeneration.template` is inherited and need not be restated, and
that `postProcess:` must **not** be emitted.

### 4.4 Seed design YAML

The current `topTestBenchTemplate` is invalid (§1.2) and unused. Replace it
with a minimal but genuinely working two-block design, modelled on
`examples/simple/arch/yaml/simple.yaml`, which is the smallest example that
builds and runs:

- `<name>_tb` — the testbench container, `hasVl/hasRtl/hasMdl/hasTb` all false,
  self-referencing instance, `instGroup: top`.
- `<name>` — the DUT, `hasMdl: true`, `hasTb: true`, and `hasRtl`/`hasVl` set
  from the RTL answer.

No constants, types, structures, interfaces or connections are required for a
project that builds. The seed should include those sections as commented
headers only, so the file teaches the schema without carrying dead content.
This is a deliberate reduction from the current 85-line commented template,
which duplicates `config/SCHEMA_SPECIFICATION.md`.

### 4.5 Breaking the bootstrap cycle

`newProject` must perform, in process, the two steps that `make db` and
`make newmodule` would perform, because no makefile exists yet:

1. Write `prj/yaml/<name>Project.yaml` and `yaml/<name>.yaml`.
2. Call `processYaml.projectCreate` on the project file, writing the database
   to `<root>/<name>.db`. This path must match
   `A2C_SQLDB_FILE = $(REPO_ROOT)/$(PROJECTNAME).db`
   (`a2c-common.mk:65`) so that the subsequent `make` sees the database as
   up to date rather than rebuilding it.
3. Open the database and call `newModule`, which runs `scaffold_create()` for
   the four makefiles and scaffolds the block and context files for the seed
   design.
4. Write `.gitignore`.
5. Print the next commands.

This reuses every existing seam. It adds no second copy of the makefile text,
no second layout table and no second merge path. The alternative, having
`newProject` write makefile text of its own, would duplicate `scaffold.py` and
is rejected.

### 4.6 Gap: hierarchical layout requires `A2C_PRJ_YAML`

This is a genuine defect that the rewrite must fix, and it is not visible from
`newProject.py` alone.

- `a2c-common.mk:64` defaults `A2C_PRJ_YAML ?= $(REPO_ROOT)/arch/yaml/project.yaml`.
- `scaffold.py::sharedMk` never emits `A2C_PRJ_YAML`.
- Every hierarchical example sets it by hand, for example
  `examples/hierVlDemo/include/make/shared.mk`:
  `A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/hierVlDemoProject.yaml`.

Since new projects are hierarchical by decision Q-L7, a scaffolded project
would look for `arch/yaml/project.yaml`, not find it, and fail on the first
`make db`. `scaffold.py::sharedMk` must therefore emit `A2C_PRJ_YAML` whenever
the layout is not functional. The value is already available: the layout mode
and the project-file path are both known to `projectCreate` and persisted.

### 4.7 Firmware

Firmware is not a schema concept. There is no `hasFw` block flag and no
firmware key in `config/schema.yaml`. Firmware is enabled entirely by the
presence of the `includeFW` entry in the project `fileMap`, which is commented
out at `config/project.yaml:194` and re-declared per project.

Answering yes to the firmware question must therefore produce four distinct
effects:

1. **Project file** — add the `includeFW` fileMap entry, exactly as quoted in
   §4.3. Key-level `dict_shallow` merging (`MERGE_SPEC` in
   `processYaml.py:3468-3482`) means only this one entry is declared; the base
   entries are inherited.
2. **Directories** — create `fw/` for the generated `<context>IncludesFW.{h,cpp}`
   and `fw/src/` for hand-authored firmware sources.

   **Correction (2026-08-10, verified against the tree).** An earlier draft of
   this plan specified `prj/fw/`, taken from the comment at
   `migrateLayout.py:135-141`. That comment describes how the *migration* routes
   pre-existing user-owned firmware orphans; it is not the convention for a new
   project. Every hierarchical example on disk uses `fw/src` — `ip_test/fw/src`,
   `simple_ip/fw/src` — with generated headers flattened into `fw/`. `fw/src` is
   also the directory the scaffolded `rundir/Makefile` adds to
   `EXTRA_PRJ_SRC_DIRS`, so `prj/fw` would have left the emitted makefile
   pointing at a directory the tool never created.
3. **`rundir/Makefile`** — the scaffolded `rundirMk` currently emits only the
   `EXTRA_O3_CPP_SRC` filter. A firmware project additionally requires the two
   lines that every firmware example carries, quoted from
   `examples/ip_test/rundir/Makefile`:

   ```make
   EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)/fw/src
   EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp
   ```

   The board support package is deliberately **not** in the default source set
   and must be opted into per project.
4. **Firmware entry stub** — a minimal `fw*Main.{cpp,h}` under `prj/fw/`,
   modelled on `examples/ip_test/fw/src/fwIpMain.cpp`, that includes the
   generated FW header and calls `regRead32`/`regWrite32` from
   `common/fw/bsp/regRdWr.h`.

**Recommended plumbing for effect 3.** Per `CLAUDE.md`, durable project truth
belongs in `projectCreate` and is persisted in the database-backed config. The
clean seam is therefore: `projectCreate` derives `hasFirmware` as
`'includeFW' in fileMap` and persists it; `scaffold_create()` passes it into
the scaffold `data` dictionary alongside `projectName`, `tbTop` and `hdlTop`;
`scaffold.py::rundirMk` emits the two lines conditionally. This adds one
derived fact and one conditional, and avoids any string inspection of the
project file at scaffold time.

**Caution.** A firmware project that declares no registers and no
`regAccess: true` memories generates no firmware headers at all, because
`includeFW` carries `cond: {smartInclude: true}`. The seed design has no
registers. The tool should therefore state, when firmware is selected, that
firmware headers appear once registers or firmware-accessible memories are
declared, and should point the user at `rules/skills/design-register-decode.md`
and `rules/skills/manage-address-space.md`.

### 4.8 `.gitignore`

Copy the pattern set already proven in `examples/.gitignore`, which correctly
distinguishes generated **artifacts** from generated **source**. Generated
source under `model/ rtl/ tb/ base/ fw/ verif/ registrar/` is tracked
deliberately; the following are not:

```
**/obj_dir/
**/build/
**/.gen/
**/*.db
**/.*.db
**/*.a
**/*.o
**/*.d
**/*.scgen
**/*.svgen
**/regr/
**/compile_commands.json
**/.clangd
__pycache__
```

### 4.9 Agent discoverability

This is a first-class requirement, not a convenience. At the moment the user
runs the entry point, the repository contains `builder/` and nothing else. No
`AGENTS.md`, no `CLAUDE.md`, no `.claude/skills/`, no `ARCH2CODE_AI_RULES.md`
symlink. An agent assisting the user has no rules loaded and no skill routing
table. Everything it needs to know must be discoverable from the tree as it
stands.

There are two distinct windows, and they need different answers.

#### 4.9.1 Before creation: how the entry point is found

Verified state of the tree today, and it is worse than expected:

- **The entry point is documented nowhere.** `--newproject` appears in no
  document. It is absent from `readme.md`, `AGENTS.md`, `AGENTS.md.template`
  and `ARCH2CODE_AI_RULES.md`. The only reachable string is the argparse help
  in `arch2code.py`.
- **The one piece of guidance that exists is actively wrong.**
  `ARCH2CODE_AI_RULES.md:248` instructs: "Always create `project.yaml` as the
  first file in a new project." That tells an agent to hand-author the project
  file rather than run the tool, which is precisely the failure mode this plan
  exists to remove. It is the same class of error catalogued in
  `firmware_decode_skill_fix_plan.md` §1, where skills teaching an obsolete
  manual model were identified as "the root cause the agent could not recover
  from".
- **The rules forbid the bootstrap command.** `AGENTS.md.template` Critical
  Constraint 1 reads: "NEVER run `python arch2code.py` directly. ALWAYS use
  `make` targets". At time zero there are no make targets, because the
  makefiles do not exist yet. An agent that has loaded these rules is
  prohibited from running the only command that can create them.
- **The routing target is stale.** The skill routing table sends "Start/Config"
  to `setup-project.md`, whose step 4 still says the makefiles must be copied
  by hand from an example (§1.2).
- **There is no readme above base.** `builder/` (the pro repository root)
  carries no markdown at all, and `base/readme.md` is 49 lines with no
  installation or getting-started section.

Required changes, in priority order:

1. **`base/readme.md` leads with the bootstrap.** The clean-repository sequence
   in §2 becomes the first content after the project description. This is the
   primary discovery surface for a human and the fallback for an agent. It
   documents the **base setup only**; the pro bootstrap lives in the pro
   repository's own readme (see the documentation split in §2), so the open
   source repository carries no site-specific URLs.
2. **Correct `ARCH2CODE_AI_RULES.md:248`** to direct the reader to the entry
   point, rather than to hand-author `project.yaml`. The surrounding bullets
   about `$root`, `$a2c` and inherited `fileMap` defaults stay; only the "first
   file" instruction is wrong.
3. **Carve out the bootstrap in Critical Constraint 1** of
   `AGENTS.md.template`. The constraint is correct for every other invocation
   and must stand; it needs one stated exception for project creation, where
   no makefile exists yet by definition.
4. **Add a bootstrap section to `base/AGENTS.md`.** This file is scoped to work
   under `builder/base`, but it is the one agent-facing document physically
   present at time zero, so it should name the entry point and point at the
   readme.
5. **Rewrite `setup-project.md` step 4** so the "Start/Config" routing target
   describes the real flow.

#### 4.9.2 After creation: installing the rules

`make agents-setup` (`a2c-agents.mk:48-120`) creates `AGENTS.md` from
`AGENTS.md.template`, appends each layer's `AGENTS.append.md`, symlinks
`CLAUDE.md`, `GEMINI.md` and `ARCH2CODE_AI_RULES.md`, and deploys every skill
into `.claude/skills/<name>/SKILL.md` and the `.gemini/`, `.opencode/` and
`.agents/` equivalents. Because `a2cPro.mk` adds `pro/rules` to
`EXTRA_A2C_RULES_DIRS`, the pro routing table in `pro/AGENTS.append.md` is
picked up with no extra machinery.

**DECIDED (architect, 2026-08-10): `newProject` recommends, it does not run.**
The tool must not install agent configuration into the user's repository as a
side effect of project creation. It closes by printing `make agents-setup` as
the recommended next step, alongside the other next commands.

Consequences of that decision:

- No `--no-agents` flag is needed, because nothing is installed implicitly.
- The closing message is load-bearing and is part of the deliverable, not
  incidental output. It must name the command explicitly and state what it
  installs, since this is the user's only prompt to run it.
- Discoverability of the agent rules therefore rests entirely on the readme
  (§4.9.1) plus this printed recommendation. Both must carry it; neither alone
  is sufficient, because a user who scripts the tool never reads the readme and
  a user who reads only the readme may miss the closing output.
- The ordering constraint is unchanged and worth stating in the message: the
  target is reachable only after `shared.mk` exists, because `a2c-agents.mk` is
  included by `a2c-common.mk`, which hard-errors on unset `PROJECTNAME`,
  `TB_TOP_MODULE` and `HDL_TOP_MODULE`. Running it before project creation
  fails; running it after succeeds.

The target is already safe to run and to repeat: every file is created only if
absent, and `AGENTS.md` is checksummed into `.agents-setup.md5` so
`agents-clean` will not delete a modified copy.

**No separate project-creation skill.** A skill is only discoverable after
`agents-setup` has run, so it cannot serve the clean-repository case by
construction. The bootstrap content belongs in the readme, and the corrected
`setup-project.md` covers project configuration from that point on.

#### 4.9.3 Defect: `agents-setup` is broken in the base-only setup

`a2c-agents.mk:83` hard-codes the rules symlink target:

```make
ln -s builder/base/ARCH2CODE_AI_RULES.md $(REPO_ROOT)/ARCH2CODE_AI_RULES.md
```

In the base-only setup the user adds `arch2code.git` directly as `builder/`, so
the file is at `builder/ARCH2CODE_AI_RULES.md` and the symlink dangles. The
same file already computes `A2C_BASE_DIR` correctly at lines 16-27, resolving
to `$(A2C_ROOT)/base` under pro and `$(A2C_ROOT)` otherwise; this line simply
does not use it. The fix is to derive the link target from `A2C_BASE_DIR`,
expressed relative to `REPO_ROOT`. Without it, half of the setups this plan
must support get a broken rules pointer as the closing act of onboarding.

---

## 5. Code changes by file

| File | Change |
| --- | --- |
| `pysrc/newProject.py` | Full rewrite. Delete `functionalDirectories`, `projectTemplate`, `topTestBenchTemplate`, `createDemoProject`, `createUserProject`. New flow per §4.5. Templates move to `templates/fileGen/` rather than living as module-level strings. |
| `templates/fileGen/newProjectFiles.py` | New. Renders the project file and the seed design YAML, consistent with how every other emitted artifact is templated. |
| `templates/fileGen/scaffold.py` | `sharedMk` emits `A2C_PRJ_YAML` for non-functional layouts (§4.6). `rundirMk` conditionally emits the two firmware lines (§4.7). |
| `pysrc/newModule.py` | `scaffold_create()` passes `hasFirmware` and the project-file path into the scaffold `data` dictionary. |
| `pysrc/processYaml.py` | `projectCreate` derives and persists `hasFirmware`. No change to `mergeProjectConfig`. |
| `config/project.yaml` | No change expected. The `scaffold` section already declares the four files. |
| `rules/skills/setup-project.md` | Rewrite step 4. The claim at line 99 that makefiles must be hand-copied from an example becomes false once this plan lands (§4.9.1 item 5). |
| `readme.md` | **Primary deliverable, not a footnote.** Lead with the clean-repository bootstrap from §2. This is the only discovery surface present at time zero (§4.9.1 item 1). Base setup only; see the documentation split in §2. |
| `builder/readme.md` (pro repository) | **New file, and it is in the pro repository, not base.** Carries the pro bootstrap, the pro repository URL, the reason the recursive submodule update is mandatory, and an inventory of what the pro layer adds. It is the first thing a user cloning pro sees. |
| `ARCH2CODE_AI_RULES.md` | Correct line 248, which currently instructs agents to hand-author `project.yaml` as the first file of a new project (§4.9.1 item 2). |
| `AGENTS.md.template` | Carve the bootstrap out of Critical Constraint 1, which otherwise forbids the only command that can start a project (§4.9.1 item 3). |
| `AGENTS.md` | Add a bootstrap section naming the entry point; this is the one agent-facing file present at time zero (§4.9.1 item 4). |
| `include/make/a2c-agents.mk` | Derive the `ARCH2CODE_AI_RULES.md` symlink target from the existing `A2C_BASE_DIR` instead of the hard-coded `builder/base/`, which dangles in the base-only setup (§4.9.3). |

---

## 6. Phasing

Each phase must leave the tree green.

- **Phase 1 — scaffold correctness.** Fix `A2C_PRJ_YAML` emission in
  `scaffold.py` and add the firmware conditional plus its `hasFirmware`
  plumbing. Independently testable against `examples/hierVlDemo` by deleting
  its `include/make/shared.mk` and re-scaffolding.
- **Phase 2 — templated project artifacts.** Move the project file and seed
  design into `templates/fileGen/newProjectFiles.py` and produce byte-correct
  output, still driven by the old questionnaire.
- **Phase 3 — the new flow.** Rewrite the questionnaire and add the in-process
  `projectCreate` and `newModule` invocations that break the bootstrap cycle.
- **Phase 4 — repository hygiene.** `.gitignore`, the closing instructions and
  the `readme.md` and `setup-project.md` documentation updates.

---

## 7. Acceptance criteria

The following must hold in a genuinely empty repository, run for both setups.

- `git init` followed by the submodule step, `pip3 install -r`, and
  `./builder/arch2code.py --newproject` completes with no manual file editing.
- `make db` succeeds.
- `make -C rundir run` builds and runs the seed model.
- `make -C rtl lint` succeeds when RTL was selected.
- `git status --porcelain` is empty after a build, matching the gate already
  enforced by `bitbucket-pipelines.yml`.
- Re-running `--newproject` in a populated repository does not overwrite any
  user-owned file. The create-once guarantee in `scaffold_create()` covers the
  makefiles; the project file and seed design need the same guard.
- With firmware selected, `fw/` and `prj/fw/` exist, `rundir/Makefile` carries
  both firmware lines, and the firmware stub compiles.
- With firmware not selected, no `includeFW` entry, no `fw/` directory and no
  firmware lines in `rundir/Makefile` are produced.
- In a pro checkout, the merged configuration includes the `tandem` fileMap
  entry and the `lmmi` interface, with no pro-specific text in the project file.

Discoverability criteria, which must hold in **both** setups:

- The bootstrap sequence is reachable from `readme.md` without prior knowledge
  of the `--newproject` flag.
- `newProject` closes by recommending `make agents-setup`, naming the command
  explicitly and stating what it installs (§4.9.2).
- `newProject` itself creates no agent configuration: no `AGENTS.md`, no
  `CLAUDE.md`, no `.claude/` directory appears as a side effect of creation.
- Running `make agents-setup` afterwards then produces `AGENTS.md`,
  `CLAUDE.md`, `GEMINI.md`, `ARCH2CODE_AI_RULES.md` and
  `.claude/skills/setup-project/SKILL.md` at the repository root.
- **Every one of those symlinks resolves.** This is the check that catches the
  §4.9.3 defect, and it must be asserted in the base-only setup specifically,
  where the current hard-coded path dangles.
- No document instructs the reader to hand-author `project.yaml` or to copy a
  Makefile from an example.
- An agent given only the fresh tree and the task "create an arch2code project
  here" reaches the entry point rather than hand-authoring YAML. This mirrors
  the documentation-eval approach in `firmware_decode_skill_fix_plan.md` §8;
  note that plan's recorded contamination hazard, since this plan document
  itself names the answer and must be excluded from any such eval's context.

---

## 8. Testing

- Extend `unittest/` with a fixture that drives the questionnaire from a
  scripted answer sequence rather than interactive `input()`. The rewrite
  should route every prompt through one injectable reader so the flow is
  testable; this is the one abstraction this plan considers justified, and it
  has an immediate call site in the tests.
- Add base-only and pro variants, plus firmware-on and firmware-off variants,
  giving four combinations.
- Consider adding a `new-project` target to the `pipeline-test` list in
  `base/Makefile:230` so that onboarding cannot silently regress.

---

## 9. Open questions for the architect

These change the work and should be answered before Phase 3.

1. **Demo project.** Should `--newproject` retain any notion of a richer demo,
   or is the two-block seed sufficient? This plan assumes the seed is
   sufficient and that `examples/simple` serves the demo role.
2. **Non-interactive mode.** Should the tool accept the answers as
   command-line flags, for scripted or agent-driven creation? This is required
   for the testing approach in §8 and is cheap if designed in from the start,
   but it widens the CLI surface.
3. **Sub-project creation.** Hierarchical layout composes, and `ip_test` shows
   a multi-node project where each node carries its own `prj/yaml/` and
   makefiles. Should `--newproject` be able to add a node to an existing
   project, or is it strictly a root-level, run-once tool? This plan assumes
   the latter.
4. **RTL question.** Is asking about RTL warranted, or should the seed always
   declare `hasRtl: true` and `hasVl: true` and let the user remove them?
5. **Firmware stub.** Should the firmware entry stub be emitted at all given
   that it cannot do anything useful until registers exist, or should the tool
   create only the directories and print guidance?
6. **Entry point shape.** `arch2code.py --newproject` is retained (§2). Is a
   `make`-shaped entry point wanted later, for consistency with the "always use
   make" rule? Doing so needs a makefile that exists before the project does,
   which is a different bootstrap problem from §1.3 and is not solved here.
Resolved by the architect on 2026-08-10:

- **Whether `newProject` runs `make agents-setup`.** It does not. The tool
  prints it as a recommended next step (§4.9.2).
- **Whether a separate project-creation skill is added.** No. A skill is not
  discoverable until `agents-setup` has run, so the bootstrap content goes in
  the readme instead (§4.9.1, §4.9.2).
- **Entry point.** `arch2code.py --newproject` is retained (§2).

---

## 10. Out of scope

- Migrating existing projects to hierarchical layout. That is owned by
  `make migrate-hierarchical` and `pysrc/migrateLayout.py`.
- Any change to the schema, the merge specification, or the layout resolution
  in `processYaml.py` beyond persisting the one derived `hasFirmware` fact.
- The dormant `pro/templates/systemc/fwQueue.py`, which iterates a `fwQueues`
  table that does not exist in `config/schema.yaml` and is not registered in
  `pro/config/project.yaml`. It is unrelated to firmware header generation
  despite the name.

---

## 11. Implementation record (2026-08-10)

### 11.1 Deviations from this plan, and why

- **No `templates/fileGen/newProjectFiles.py`.** §5 proposed moving the project
  and seed-design templates into the `templates/` tree. That is not possible:
  everything under `templates/fileGen/` is rendered through `renderer`, which
  requires an open project database, and at project-creation time no database
  exists. The templates therefore remain module-level strings in
  `pysrc/newProject.py`. Putting them in `templates/` would have implied a
  renderer contract the file could not honour.
- **`fw/src`, not `prj/fw`.** Corrected in §4.7; the plan had followed a
  `migrateLayout` comment describing orphan migration rather than the
  convention every hierarchical example actually uses.
- **`hasFirmware` is not persisted in the database.** §4.7 proposed deriving and
  persisting it in `projectCreate`. Unnecessary: `scaffold_create()` already
  receives `fileGenerationConfig`, so the flag is read directly from the file
  map at the point of use. Persisting it would have added durable state with a
  single consumer, against the "simplest solution first" rule in `CLAUDE.md`.
  `PRJFILE` *is* persisted, because the project file path is genuinely not
  otherwise reachable from `projectOpen`.
- **`newProject` also runs `make gen`.** Not in the original plan; forced by
  §11.2 item 1.

### 11.2 Defects found during implementation and fixed

Each of these independently blocked "clean repository to running project", and
none was visible from `newProject.py` alone.

1. **The model build never depends on generation.** `GEN_DEPS` is consumed only
   by the `gen` target (`a2c-common.mk:197`) and by the verilator wrapper
   (`a2c-vl-wrap.mk:55`). `a2c-systemc.mk` does not reference it, so a build
   compiles whatever is on disk. Existing projects hide this because their
   generated regions are already filled in and committed; a brand-new project
   has empty scaffolds, and the first build fails on unbalanced braces.
   **Fixed in `newProject` by running `make gen` after scaffolding**, so the
   project is handed over fully generated. The underlying build-ordering gap is
   left alone deliberately: making the systemc build depend on `GEN_DEPS` would
   change build semantics for every existing project, which is a separate
   decision. It remains a trap for `make newmodule` followed directly by
   `make run`, and is recorded as open question 8.
2. **The `tbConfig` scaffold did not compile.** `templates/fileGen/fileGen.py`
   emitted a `final()` calling `endOfTestState::GetInstance()` without
   `import a2c.endOfTest;`. Every existing example has the import hand-added
   above the generated region, which is why no example caught it. Fixed in the
   template.
3. **`TB_TOP_MODULE` was derived wrongly.** `newModule._deriveTopModules()`
   returned the block instanced at `_topInstance`, that is the testbench
   *container*. The run binary selects a testbench by the name the Config file
   registers, which is the block carrying `hasTb`. The scaffolded value made
   the binary exit with "TestBench not found". Confirmed against
   `examples/simple`, whose committed `shared.mk` says `TB_TOP_MODULE = simple`
   while the container is `simple_tb`. Fixed to prefer the single `hasTb`
   block, falling back to the top block when ambiguous.
4. **`agents-setup` was broken in the base-only setup** (§4.9.3), now fixed and
   verified: the rules symlink resolves to `builder/ARCH2CODE_AI_RULES.md` in a
   standalone checkout and `builder/base/...` under pro.

### 11.3 RESOLVED: the seed testbench does not end — option C adopted

**DECIDED (architect, 2026-08-11): option C.** Implemented and verified. The
`tbExternal` scaffold in `templates/fileGen/fileGen.py` now carries the
end-of-test idiom as commented guidance in both the header and the source, so
every block scaffolded by `make newmodule` teaches it, not just new projects.

The commented pair is modelled on the only testbench-side precedent in the tree,
`examples/ip_test/ip/tb/ip/ipExternal.{h,cpp}`: an `endOfTest eot_{true}` member
that registers a voter, a `stimulusThread` declaration, its `SC_THREAD`
registration in the constructor's user region, and a body that ends with
`eot_.setEndOfTest(true)`. Voting is what wakes the generated `eotThread` and
calls `sc_stop()`.

Verified by uncommenting the guidance in a freshly created project: the build
succeeds and the run reports "No error", matching the pass output of
`hello-world` and `hierVlDemo`. The un-uncommented default still aborts on the
end-of-test assertion, which is the framework correctly reporting that no test
has been written yet.

Note for anyone extending this: `endOfTestState::setEndOfTest` is private to the
`endOfTest` friend class, so the voter object is the supported route.
`forceEndOfTest()` is public but bypasses `evaluateEndOfTest()`, and therefore
never notifies `eotEvent` — it would latch the state without stopping the
simulation.

#### Original statement of the problem, and the options considered

The generated project builds, links, lints and starts simulation, then aborts
on the framework's own end-of-test assertion:

```
Fatal: (F4) assertion failed: false   (q_assert.cpp:58)
```

This is correct framework behaviour, not a defect. The scaffolded `External`
class provides an `eotThread` that waits on the end-of-test event, but nothing
signals that event until the user writes a test. The seed design deliberately
contains no test.

The consequence is that a new user's first `make -C rundir run` ends in a core
dump. Three options, none adopted without a decision:

- **A.** Accept it, and have the closing message state plainly that the run will
  assert until a test is written. Honest, zero machinery, poor first impression.
- **B.** Have the seed signal end-of-test immediately, so the first run prints
  "No error". Requires `newProject` to write into the user region of a file
  `newModule` scaffolds, which no other code path does.
- **C.** Add a commented end-of-test example to the `tbExternal` scaffold, so
  every new block carries the idiom and the user uncomments one line. Changes a
  shared template for all projects, not just new ones.

### 11.4 Verification performed

- Pro setup, firmware and RTL enabled: creates, generates, builds, links, runs;
  `make -C rtl lint` clean under Verilator 5.038; the pro-only `Tandem`
  artifact compiles.
- Pro setup, model-only (no firmware, no RTL): same, with no `fw/` directory,
  no firmware lines in `rundir/Makefile` and no `includeFW` entry.
- Base-only standalone checkout: reports "Detected setup: base", emits no
  `Tandem` artifact, and `make agents-setup` produces four resolving links.
- `make db` immediately after creation reports "Nothing to be done", confirming
  the database name matches `A2C_SQLDB_FILE`.
- Regression: `make hello-world` and `make hierVlDemo` both report "No error".
- `git status --porcelain` in `base` shows only the intended source edits and
  this plan; no build artifacts escape the ignore set.

Not yet done: the `unittest/` fixtures in §8. The questionnaire takes an
injectable `reader` argument specifically so they can be written without
driving `input()`.
