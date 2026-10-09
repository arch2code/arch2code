---
name: migrate-project
description: Migrate an existing arch2code project to the current authoring format using `make migrate` (eval Python→SV, addressControl→per-block, include header→cppm modules, module-header split, orphan sweep, block and testbench .cpp/.h→.cppm port, regenerate) and resolve every manual item the tool reports, including the hand port of a parameterized block. Use whenever a project fails the projectCreate yamlFormat gate, still has header-mode includes or legacy .h/.cpp block pairs, carries stale generated orphans, or the user asks to run or finish a project migration.
---
# Skill: project migration

`make migrate` makes every mechanical edit. This skill explains what it runs,
how to read its report, and how to finish the items it can only report.

## 1. Run the tool

```text
make migrate
```

Run it from the project's `rundir/`. It migrates the one project
`A2C_PRJ_YAML` names. It converges: a migrated, orphan-free project re-runs
clean, exits 0 and changes nothing.

The target runs eight steps:

1.  **`migrateYaml.py --write <project.yaml>`**, the text conversion. It never
    opens the database. It runs the text phases below and stamps
    `yamlFormat: 2` only when none leaves manual work.
2.  **`make db`** builds the database from the stamped YAML.
3.  **`migrateYaml.py --sweep --write --db <db>`**, the sweep. It reads the
    database and runs these phases in order:
    - **Filename-prefix move.** When the project sets `svFilePrefix`,
      `scFilePrefix` or `fwFilePrefix` where it had none, every owned file of
      that kind still at its unprefixed name moves, byte for byte, to its
      prefixed name. Changing one non-empty prefix to another is not migrated.
    - **Orphan delete.** In a fully generated segment (`base`, and `registrar`
      on the hierarchical layout) every source file that carries
      `GENERATED_CODE_BEGIN` and is not a current artifact is deleted, which
      catches renamed and alternate-extension orphans. In a mixed segment
      (`model`, `rtl`, `vl_wrap`, `tb`) only the known legacy generated files
      are deleted: `<context>Includes.{h,cpp}`, `<context>_package.sv` and
      `<block>_hdl_sv_wrapper.sv`. A file without the marker is reported, never
      deleted. Files with a non-source extension are ignored. Once the orphans
      are gone, a re-run deletes nothing.
    - **Reports.** Legacy user files (`TODO_PORT`), user includes of deleted
      headers (`TODO_USER_INCLUDE`), unmarked files (`TODO_UNGENERATED_FILE`),
      and C++ directories the build does not compile
      (`TODO_UNMANIFESTED_SRC_DIR`).
    - **Re-stamps.** Each surviving generated file's `GENERATED_CODE_PARAM` line
      is rewritten to the canonical `--project` / `--context` form, and each
      RTL block's user-owned `endmodule: <label>` is set to the block's SV
      module name. Without that label Verilator raises `%Error-ENDLABEL`. A
      referenced child project's files are never rewritten. Both re-stamps need
      the database, so `make gen` cannot do them.
    - **Stale SV names.** Hand-written SV that names a generated module or
      package by its old project-qualified name is reported
      (`TODO_STALE_SV_NAME`).
4.  **`make newmodule`** creates each missing scaffolded file, such as
    `<context>Includes.cppm`. It runs after the sweep, so orphans are gone
    first.
5.  **`migrateYaml.py --port-tb --write --db <db>`**, the testbench port. It
    splits each `<block>Config.cpp` `tbConfig` region into `prerequisites`,
    `class` and `registration`, merges each legacy `<block>External.{h,cpp}`
    into the scaffolded `<block>External.cppm` with its `GENERATED_CODE_PARAM`
    line, and carries each legacy `<block>Testbench` pair's DUT `--variant=`
    onto `<block>Testbench.cppm` before deleting the pair. It runs before `gen`
    because `gen` rejects the legacy `<block>Config.cpp` region
    (`ValueError: Unknown section ''`) and would scaffold the External with the
    wrong `--block`. Between this step and `gen`, `<block>Config.cpp` does not
    compile, so never run it on its own.
6.  **`make gen`** fills the generated regions.
7.  **`migrateYaml.py --port --write --db <db>`**, the block port (Section 6).
    It needs the filled `<block>.cppm`, so it runs after `gen`.
8.  **`migrateYaml.py --sweep --db <db>`** without `--write`, printed under
    `=== pending after all phases (read-only sweep) ===`. It lists what is
    still left.

### Exit status

- Steps 1 and 2 halt on any non-zero exit, so an unresolved text-phase item
  stops the run before the database is built.
- Exit 1 from steps 3, 5 or 7 is pending hand work and does not halt. Their
  edits stay applied and `gen` still runs. Step 3's exit 1 is not the verdict,
  because steps 5 and 7 port the pairs it counts.
- Exit 2 halts at once. Step 3 returns it when the prefix move is blocked
  (`TODO_FILE_PREFIX_BOTH_EXIST`, `TODO_FILE_PREFIX_CHAIN`) or when opening the
  database, the move, or its report raises, because `newmodule` would otherwise
  delete a file left at its unprefixed name, with its user code. Step 5 returns
  it when the `<block>Config.cpp` restructure is refused (any `TODO_TBCONFIG_*`)
  or raises, because `gen` cannot render that file. On such a run the External
  and testbench-top ports still report their items but write nothing.
- Exit 3 comes only from step 3, when a phase raises or the sweep raises
  outside any phase. Both report `TODO_PHASE_FAILED`. The target continues, but
  the recipe exits 1 at the end.
- Steps 5 and 7 open the database before any phase runs. If either prints a
  Python traceback with no `Phase failures` list, the open failed. It still
  exits 1, so treat it as a failure, not pending work. Fix the cause and re-run
  `make migrate`.
- On a run that reaches step 8, the recipe exits 1 when step 3 exited 3, when
  step 5 or 7 left an item, or when step 8 still reports one, and 0 otherwise.
  Make prints the code in its `Error N` line and itself exits 2 for any recipe
  failure, so a script must read `Error N`, not `$?`.

### Text phases (step 1)

- **Eval (Phase A).** Rewrites Python-syntax `eval` strings into the SV subset,
  for example `($X-1).bit_length()` to `$clog2($X)` and a C-style literal such
  as `0x10` to `'h10`. An eval already in the SV subset is left alone, so the
  phase is idempotent. Three forms are reported as `NEEDS_MANUAL` and left
  untouched. A real-valued eval such as `$DWORD / 2.0`: replace it with a
  literal `value:`. Floor division `//`, because it floors where SV `/`
  truncates: rewrite it by hand, for example the ceiling idiom `-(-a//b)` as
  `(a + b - 1) / b`. Power `**`: rewrite it without the operator, for example
  `1 << $N` for `2**$N`.
- **Address control (Phase B).** Converts `addressControl.yaml` to per-block
  `addressBlock:` routers and the `project.yaml` policy sections.
  `address-migration.md` covers it, including its traps.
- **Variant schema.** Rewrites `parameters:` entries from per-row lists
  (`- {variant: v, param: P, value: n}`) to the nested form (`v: {P: n}`),
  grouping rows by variant in first-seen order. It touches only `parameters:`
  sections and raises no manual items.
- **Includes.** Removes a legacy `fileGeneration.fileMap` `include` override
  (paired `.h`/`.cpp`) so the project inherits the `.cppm` module interface,
  and deletes the orphaned `<context>Includes.{h,cpp}`. Firmware
  `<context>IncludesFW.{h,cpp}` files stay header-mode. User code that
  includes a migrated header is reported as `TODO_USER_IMPORT` (Section 4).
- **Module header.** Splits each block-module `.cppm` header region into the
  current layout: a GMF-only `blockModuleHeader` region, the
  `// user #includes here` slot, a `moduleExport` region that owns
  `export module` and the imports, and the `// user imports here` slot, just
  before the class region. Only markers move. An `import` that lands in the
  `// user #includes here` slot sits before `export module` and is reported as
  `TODO_MODULE_IMPORT` (Section 4a).
- **langDomain.** Adds `langDomain: sv`, `sc` or `fw` to each entry of the
  project's own `fileGeneration.fileMap` that lacks it: `sv` when an `ext`
  value is `sv` or `svh`, `fw` for `basePath: fwInc`, `sc` otherwise. File
  names do not change. An entry it cannot edit safely is `TODO_LANGDOMAIN`.
  Add the key by hand with the same rule.
- **Composed-build check.** Reports each child project that is not yet
  stamped (`TODO_UNMIGRATED_SUBPROJECT`).

Each phase is idempotent. All except Phases A and B also run on a project
already stamped `yamlFormat: 2`. Because a stamped project exits step 1 with
0, the rest of the pipeline still finishes a partially migrated tree.

### Composed builds

A composed build is a top-level project whose `projectFiles:` lists child
`*Project.yaml` files. `examples/ip_test` is the reference. Each project has its
own `prj/yaml/<name>Project.yaml`, its own `include/make/shared.mk` setting
`A2C_PRJ_YAML`, and its own `rundir/`, so each needs its own `make migrate`
run from its own `rundir/`. The top-level run does not migrate the children.
It reports each unstamped direct child as `TODO_UNMIGRATED_SUBPROJECT` and
refuses to stamp.

Running only the top breaks three things:

1.  **The children are never stamped.** The `projectCreate` gate reads only the
    project file it is given. Composed, it sees the stamped top and passes, so
    the failure appears later, when someone builds the child on its own.
2.  **Part of each child's YAML is never converted.** The top's text phases walk
    its `projectFiles:` and the `include:` chains below them, but not a child's
    own `projectFiles:` list. In `ip_test`, only a run from `ip/rundir` reaches
    `ip/yaml/ipTop.yaml`. Nothing reports this.
3.  **Sections 3 and 7 are per project.** Each sub-project has its own
    `rundir/Makefile` and `shared.mk`, so its `EXTRA_*` wiring, per-project vl
    build tree and `layout:` choice are separate decisions the top-level run
    cannot see.

Migrate children first, in dependency order: in `ip_test`, `common`, then `ip`
and `ipBridge`, then `ip_test`. The top's text phases edit child YAML they
reach, so bottom-up keeps each edit in the run that stamps its owner. The check
reports direct children only, so bottom-up also walks a deep composition one
level at a time.

A stamped child draws no report, but it still needs its own `make migrate`
after a builder update. Otherwise the parent imports the child's current module
names (`<owner>_<context>`) while the child's stale files export different ones,
and the composed build fails with `module '<owner>_<ctx>' not found`, which no
`TODO_*` reports.

A file reached from several projects, through `projectOverrides:` or a vendored
symlink such as `ip_test/bridge/ip`, is fine. The second run over it changes
nothing.

## 2. Read the report

Applied edits are listed under `applied:`. Items the tool cannot finish are
listed under `manual TODO:` as:

```text
<file>:<line>  <KIND>  <message>
```

The filename-prefix move is the exception. It prints its items under
`=== filename-prefix move: <project> ===` as `TODO: <message>`, with no kind
name. Match them to `TODO_FILE_PREFIX_BOTH_EXIST` ("both … and … exist") or
`TODO_FILE_PREFIX_CHAIN` ("is the unprefixed name of … and also another
artifact's current name") by their text.

Resolve every item, then re-run `make migrate` until the report is clean.

A phase that raises does not stop the others. Its traceback goes to stderr and
it is listed under `Phase failures` as `TODO_PHASE_FAILED`, naming the phase
and its input. A failed text phase blocks the stamp. Section 1, "Exit status",
says which failures halt.

### Manual items

| `KIND` | From | Meaning | Resolve with |
| --- | --- | --- | --- |
| `TODO_ROUTER_RESOLUTION` | address phase | An `AddressGroups:` row's router cannot be resolved. | `address-migration.md`, Step 3 |
| `TODO_INTERFACE_SCOPE` | address phase | A router's file does not see the register-bus interface. Raised once, on the run that writes the router's `addressBlock:`. | `address-migration.md`, Step 2 |
| `TODO_LEAF_REGISTER_PORTS` | address phase | A routed leaf needs a `registerPorts:` decision. Raised on every run while the legacy table exists. The run that deletes the table raises it for the last time. | `address-migration.md`, the `registerPorts:` note |
| `TODO_UNMIGRATED_SUBPROJECT` | composed-build check | A child named in `projectFiles:` is not stamped. Blocks this project's stamp. | Run `make migrate` in the child's `rundir/`, which the message names, then re-run here (Section 1, "Composed builds"). |
| eval `NEEDS_MANUAL` | eval phase | A real-valued eval, floor division `//` or power `**` has no automatic SV-subset form. | Real-valued: replace the `eval:` with a literal `value:`. `//` and `**`: rewrite by hand (Section 1, "Eval (Phase A)"). |
| `TODO_LANGDOMAIN` | langDomain phase | A fileMap entry the phase cannot edit safely. | Add `langDomain:` by hand, using the rule in Section 1. |
| `TODO_USER_IMPORT` | includes phase | User code `#include`s a migrated context header. | Section 4 |
| `TODO_MODULE_IMPORT` | module-header phase | An `import` sits in the GMF zone before `export module`, where it is illegal. Never moved by the tool. | Section 4a |
| `TODO_PORT` | sweep | A legacy user file whose current artifact has another form or path. Never deleted by the sweep. | Block pairs clear in step 7 (Section 6), testbench External and Testbench pairs in step 5, on the same run, unless the porter reports its own item. Any other file, such as a `<block>_hdl_sc_wrapper.h` at a changed path: move its user code into the current file by hand and delete the legacy file. |
| `TODO_USER_INCLUDE` | sweep, testbench port | User code `#include`s a generated header that the generator does not emit. The testbench port also reports a `.cpp` that includes a legacy `<block>External.h`. | Section 4, or Section 4b for the External. |
| `TODO_UNGENERATED_FILE` | sweep, includes phase, layout migration | A file with no `GENERATED_CODE_BEGIN` marker that matches a delete target or sits in a fully generated segment. Never deleted. | It is user-owned (move or keep it) or a generated file that lost its marker (regenerate it). |
| `TODO_CURRENT_ARTIFACT` | sweep | A legacy file name that is also another artifact's current file, which a filename prefix can cause. Left in place. | Check that the file holds the current artifact's code. If it still holds the legacy one, replace it by hand. |
| `TODO_MISSING_BASEPATH` | sweep | A legacy fileMap `basePath` is absent from the current layout, so the entry is skipped. | Confirm the layout is expected. The item keeps the report non-clean until the stale entry no longer applies. |
| `TODO_UNSUPPORTED_LAYOUT` | sweep | A hierarchical-layout context still has a legacy header-mode file beside its current file, so that context is not swept. The sweep continues with the others. | Finish the format migration in functional layout before opting into hierarchical (Section 7). |
| `TODO_MISSING_PARAM_LINE` | sweep re-stamp | A generated file has a marker but no `GENERATED_CODE_PARAM` line to re-stamp. | Add the line the report quotes at the top of the file's generated preamble, then re-run. |
| `TODO_UNMANIFESTED_SRC_DIR` | sweep | A directory under `base`, `model`, `fw` or `tb` holds C++ the build manifest does not compile. | Section 3 |
| `TODO_STALE_SV_NAME` | sweep | User SV names a generated module or package by its old project-qualified name. The paragraph after this table says what it matches. | Rename the reference to the name the message gives, then re-run. |
| `TODO_FILE_PREFIX_BOTH_EXIST` | prefix move | A file exists at both its unprefixed and prefixed names. Neither moves. Halts. | Keep the copy holding your code at the prefixed name, delete the other, re-run. |
| `TODO_FILE_PREFIX_CHAIN` | prefix move | An unprefixed name is also another artifact's current name, so no file moves. Halts. | Put each artifact's code at its prefixed name by hand, then re-run. The message lists the chain. |
| `TODO_PORT_PARAM` | block port | The block declares its own `params:`, so its code must become a template on `Config` first. Legacy pair left. | Section 6, "Port a parameterized block by hand" |
| `TODO_PORT_HOSTILE_LIB` | block, testbench port | A user slot includes a library that breaks in a module purview, such as OpenCV. Legacy pair left. | Section 6, "A module-hostile library" |
| `TODO_PORT_SLOT0` | block, testbench port | The top of a legacy file, or the header after the class's `};`, holds a line the port will not place: a stray `import` or a declaration such as an `extern` global. One item per line. Legacy pair left. | Move an `import` to the `// user imports here` slot of the `.cppm`, first in the slot, and a declaration into the class or purview. Delete it from the legacy file, then re-run. |
| `TODO_PORT_UNPLACED` | block, testbench port | The port could not account for a code-bearing legacy line, usually a hand-edited slot boundary such as `};  // comment`. Nothing is written. | Restore the boundary to a bare `};` at column 0 and re-run, or port by hand. Never delete the reported code to clear it. |
| `TODO_PORT_NO_CPPM` | block, testbench port | A legacy pair exists but its `.cppm` was not scaffolded. | Run `make newmodule` (and `make gen` for a block), then re-run. |
| `TODO_PORT_TARGET_DAMAGED` | block, testbench port | The target `.cppm` lost its `GENERATED_CODE_PARAM` line or a region the port anchors on. | Delete the `.cppm`, re-scaffold it (`make newmodule`, then `make gen` for a block), and re-run. |
| `TODO_PORT_PARAM_SPLIT` | testbench port | The legacy `.h` and `.cpp` disagree on their `GENERATED_CODE_PARAM` tails (External) or `--variant=` (Testbench). | Make the two lines agree, then re-run. |
| `TODO_PORT_NO_PARAM_LINE` | testbench port | One legacy file has no `GENERATED_CODE_PARAM` line to carry. | Copy the line from the sibling file, then re-run. |
| `TODO_PORT_TAIL_UNPLACED` | testbench port | A legacy `<block>Testbench` PARAM line holds an argument beyond `--block=<dut>` and `--variant=<name>`, such as a retargeted `--block`, an `--excludeInst`, or `--variant v` spelled with a space. Nothing is stamped. | Put the argument on the `GENERATED_CODE_PARAM` line of `<block>Testbench.cppm` by hand, then delete the legacy pair. |
| `TODO_PORT_STALE_VARIANT` | testbench port | A legacy Testbench or External names a DUT `--variant=` that `gen` would reject: the block does not declare it, or the block has no own `params:`. An External retargeted at a `_tb` block is not checked. Nothing is stamped. | Block with own `params:`: choose the variant. Set it on `<block>Testbench.cppm` for the tb top, or on both legacy External files and re-run. The message lists the declared variants. Block without own `params:`: delete the legacy Testbench pair, or remove `--variant=` from both legacy External files and re-run. |
| `TODO_TBCONFIG_UNPLACED` | testbench port | A code-bearing line of `<block>Config.cpp` would not survive the restructure. Nothing is written. Halts. | Bring the file back to the fresh-scaffold shape by hand. Report it, because the restructure is deterministic. |
| `TODO_TBCONFIG_DIRECTIVE` | testbench port | The `<block>Config.cpp` preamble holds a preprocessor directive other than `#include`. The restructure would move it below the new `prerequisites` region and change its effect. Halts. | Place it by hand, below the `// user #includes and imports here` label if it must follow the framework includes, then re-run. |
| `TODO_TBCONFIG_NO_REGION` / `TODO_TBCONFIG_NO_PARAM` / `TODO_TBCONFIG_UNGENERATED` | testbench port | `<block>Config.cpp` has no `--template=tbConfig` region, no `GENERATED_CODE_PARAM` line above it, or no marker at all. Halts. | Restore the missing marker line from a fresh scaffold, then re-run. |
| `TODO_TBCONFIG_NO_REGISTRATION` | testbench port | `<block>Config.cpp` has no `<blk>Config::registerTestBenchConfig <blk>Config::registerTestBenchConfig_;` line, the anchor of the `registration` region the restructure adds. Without that region the testbench never registers, which fails at run time, not at build. Halts. | Add the `--section=registration` region markers after the class's closing `};`, copying a fresh scaffold, then re-run. |
| `TODO_PHASE_FAILED` | any step | A phase raised. Its report is missing and its edits may be partial. | Read the traceback, fix the cause, re-run. |

The sweep deletes only purely generated orphans. Every user-owned file it meets
is reported, not touched.

`TODO_STALE_SV_NAME` does not see a `bind` target, a name a macro builds, or a
reference in a one-line `` `define ``. If lint or synthesis names an unknown
module after a clean run, rename that reference the same way.

### Advisories

An advisory prints on every run and never blocks the stamp or the exit code. It
marks a question with more than one right answer. A crash inside an advisory
check is a phase failure and does block.

| `KIND` | From | Meaning | Act on it when |
| --- | --- | --- | --- |
| `ADVISORY_LEAF_REGISTER_PORTS` | address phase | A routed leaf declares no `registerPorts:`, so it infers its register bus. | The leaf is reusable IP and its `<block>Base` must be self-contained. A top-down leaf is correct as is, and the advisory keeps saying so. |

Read the advisories even on a clean run. After the migrating run, this is the
only place a leaf's top-down or reusable-IP answer is stated.

## 3. Wire user-owned files and source directories into the build

### Files with generated regions that no fileMap entry scaffolds

The build takes its generated files from the database-derived manifest
(`A2C_SC_GEN_FILES`, `A2C_SV_GEN_FILES`, written by
`config/createBuildManifest.py`). The manifest lists only files the fileMap
scaffolds. A file that carries `GENERATED_CODE_BEGIN` markers but that
`make newmodule` never creates drops out of both generation and compilation
until you wire it. Decide who owns each one:

* **arch2code owns the whole file.** Declare it under `fileGeneration.fileMap`
  with its current basename and segment, so the entry resolves to the existing
  path. `make newmodule` skips an existing file, so update its
  `GENERATED_CODE_PARAM` line to match the entry's mode before `make gen`. A
  project-wide address header is the common case (`manage-address-space.md`,
  Section 4). Remove any `EXTRA_SC_GEN_FILES` entry for a file once the
  manifest lists it.
* **The project owns the file and arch2code fills only its regions.** List it
  in `include/make/shared.mk`, above the `include … a2c-common.mk` line:
  C++ files (`.h`, `.cpp`, `.cppm`) on `EXTRA_SC_GEN_FILES`, SystemVerilog
  files (`.sv`, `.svh`) on `EXTRA_SV_GEN_FILES`.

```make
# Project-owned files whose generated regions arch2code updates.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/mixedEncoders.h
EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv
```

Listed files regenerate and compile with the scaffolded set. See
`manage-build.md` for the targets.

### Source directories (`TODO_UNMANIFESTED_SRC_DIR`)

The build compiles C++ only from `PRJ_SRC_DIRS`, which the manifest seeds with
the segment roots arch2code writes into (`A2C_SC_SRC_DIRS`). Each directory is
globbed one level deep, and the same list feeds the include path. A firmware
source directory, a shared helper directory, or a subdirectory of a segment
root is not on that list, so the build skips it without warning. The symptom
is usually a missing header or undefined symbol in an unrelated file.

The sweep reports each such directory. It scans `base`, `model`, `fw` and `tb`
at the project root, follows symlinked directories, and skips dot-directories
and the `build`, `obj_dir`, `rundir` and `builder` trees. It does not read
version control, so `.gitignore` has no effect. A subdirectory of a manifest
root is reported, because the glob does not recurse. A vendored tree outside
those four, such as `thirdparty/`, is not reported. In a hierarchical project
only the root node's segments are scanned.

Each item is a decision:

- **It belongs in the build.** Add it in the project's `rundir/Makefile`, as
  `examples/simple_ip` and `examples/ip_test` do. That also puts it on the
  include path:

  ```make
  EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)/fw/src
  ```

- **It does not.** Take vendored code, examples or dead directories out of the
  project tree.

Do not add every directory by reflex. A directory under a segment root is not
necessarily meant to build.

A directory reached by two paths, such as `fw/src` and a `model/shared` symlink
to it, is one item, named by the first path in sorted order with the others
listed. Wire only one path: two make a `.cpp` fail at link on duplicate symbols
and a `.cppm` fail at the module scan. To remove it instead, remove the
directory or every one of its paths. A link into a directory the manifest
already compiles is not reported.

The migrator never rewrites `EXTRA_*` lines. Section 7 says what to change after
a hierarchical layout move.

### A per-project vl build tree

The whole-design Verilator build runs in `rundir/build/vl`
(`A2C_VL_BUILD_DIR`, driven by `include/make/a2c-vl-build-entry.mk`). If the
project's `vl_wrap` segment holds its own vl build tree (a `Makefile`,
`obj_dir` and a built library), delete it. The build does not use it.

To find the `vl_wrap` segment, take the base `config/project.yaml` merged with
the project file's own `dirs:` and `fileGeneration:`, with the project's
entries winning. `dirs:` gives the functional placement and `hierarchicalDirs:`
the hierarchical one. Projects do
override these, as `examples/hierInclude` does for `rtl`.

A project that moved to hierarchical layout must check both placements. The
move relocates only source files, so a per-project vl build tree stays at the
functional location. The move also reduces the project file's `dirs:` to
`root:`, so the functional override that placed it is gone from the file
(Section 7).

## 4. Finish the includes (header to cppm) migration

When the includes phase applies edits, the project's context includes move
from paired headers to C++20 module interfaces. A `TODO_USER_IMPORT` blocks the
stamp, so step 1 halts and the `<context>Includes.cppm` files do not exist yet.
Fix the sites below, then re-run: step 1 stamps, `make newmodule` creates the
`.cppm` files and `make gen` fills them.

1.  **Fix each `TODO_USER_IMPORT` and `TODO_USER_INCLUDE` site.** A
    hand-written file that does `#include "<context>Includes.h"` must import
    the module instead. Copy the module name from the `export module` line of
    the generated `<context>Includes.cppm`, and the namespace from its
    `export namespace` line. Do not build them from the file name. The module
    is `<project>_<includeName>`, unless the name equals the project name or
    already starts with `<project>_`. `includeName` is the YAML file's stem
    unless the file sets `includeName:`. The namespace is the module name plus
    `_ns`. In `examples/ip_test`, project `ip_test` and context `ip_top`:

    ```cpp
    import ip_test_ip_top;
    using namespace ip_test_ip_top_ns;
    ```

    The scanner reports user-owned text: hand-written files and the gaps
    between generated regions. An include inside a generated region is not
    reported, because `make gen` rewrites it. The scanner matches only
    `#include "..."`, not `#include <...>`.

    Swapping the include is not always enough. The context types live in
    `<module>_ns`, so a `::foo_t` reference does not resolve, and a second
    `using namespace` can make a name ambiguous. The tool detects neither. The
    build flags them: qualify as `<module>_ns::foo_t`, or narrow the
    conflicting `using`.

2.  **Clear stale build state.** A header-mode build leaves `.d` dependency
    files naming the deleted headers, which break the next build with
    `No rule to make target ...Includes.h`. Run `make clean`, which removes
    the database, `.gen` and `rundir/build`, before rebuilding.

3.  **Verify.** Build and run the project's normal targets (`manage-build.md`).
    The includes phase reports `TODO_USER_IMPORT` only on the run that converts
    the includes. An `#include` left after that is reported by the sweep as
    `TODO_USER_INCLUDE` on every run, so a clean `make migrate` confirms none
    survived.

## 4a. Move a stray module import (`TODO_MODULE_IMPORT`)

The module-header phase puts the user code between the legacy header regions
into the `// user #includes here` slot, in the global module fragment (GMF),
before `export module`. A plain `#include` there is correct. An
`import` there is not: C++20 forbids an import before the module declaration
(clang: `imports must immediately follow the module declaration`).

Cut each reported `import <name>;` line from the `// user #includes here` slot
(between the `blockModuleHeader` region and the `moduleExport` region) and
paste it into the `// user imports here` slot (between the `moduleExport` region
and the class region). That slot is the module preamble. Put every `import`
first, then any `using namespace`. Never paste inside a generated region.
Re-run `make migrate` to confirm.

If the `// user imports here` slot holds an `import <ctx>;` and
`using namespace <ctx>_ns;` that the generated regions already emit, delete the
pair. The `moduleExport` region emits the import and the class region emits the
`using namespace`. A `using namespace` closes the module preamble, so any import
written after it in the slot is illegal. Keep only imports the generated regions
do not emit (Section 6, "Restore body-only context imports").

## 4b. A `.cpp` that defines External members

The testbench port moves `<block>External` into the module
`<block>.external` and deletes `<block>External.h`. A sibling `.cpp` that
included the header to define `<block>External` members out of line is
reported as `TODO_USER_INCLUDE`. An `import` does not fix it: a member of a
class attached to a module can only be defined in a unit of that module. Make
the file a module implementation unit:

```cpp
module;
#include "systemc.h"        // every #include goes here, before the module line
module myblk.external;      // the name from `export module` in myblkExternal.cppm
import myblk_tb;            // imports follow the module line
```

Keep the `.cpp` name. The build compiles every `.cpp` after all module
interfaces, so it needs no wiring. A `.cppm` holding `module <name>;` is not
compiled at all.

A name declared in a module unit is attached to that module and changes its
mangled symbol. A global or free function shared with a plain `.cpp`, such as a
test-selection string read by `<block>Config.cpp`, then fails to link against a
plain `extern` declaration. Wrap its definition in `extern "C++"` to keep it in
the global module:

```cpp
extern "C++" {
std::string myblkTestSelection;
}
```

The same applies to globals the port moved from the legacy `.cpp` tail into
`<block>External.cppm`.

## 5. Call the generated `createTbTop()` helper

`make gen` emits a protected member into the `--template=tbConfig
--section=class` region of each testbench's `<block>Config.cpp`:

```cpp
std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "<block>Testbench", "", "<project>"); }
```

The factory call for the testbench top, with its `projectName` key, belongs in
that generated helper and nowhere else. A testbench that builds the top by hand
in the user body of `createTestBench()` with the four-argument call below does
not compile, because the factory needs a project name:

```cpp
std::shared_ptr<blockBase> tb =
    instanceFactory::createInstance("", "tb", "<block>Testbench", "");
```

`make gen` never rewrites the user body and the tool reports nothing, so change
the call by hand:

```cpp
std::shared_ptr<blockBase> tb = createTbTop();
```

## 6. Block implementation port (step 7)

Every block with a model is one `<block>.cppm` module interface unit,
module `<project>_<block>.block` under the naming rule in Section 4. The class
is a `template<typename Config>` class only when the block declares its own
`params:`. The sweep reports each legacy `<block>.h`/`<block>.cpp` pair as
`TODO_PORT`, and step 7 handles it on the same run:

- **A synthesized register handler (`isRegHandler`) or a router
  (`addressBlock:`).** The pair holds no user code, so it is deleted and
  `make gen` recreates the `.cppm`.
- **A block without its own `params:`.** The port moves the four user slots
  (below) into the `.cppm` and deletes the pair. A user `#include
  "<sibling>.h"` of another block becomes `import <sibling module>;`. An
  include of a contained child's header is dropped, because the generated
  region already imports the child's `.base` module.
- **Anything else is declined** with `TODO_PORT_PARAM`, `TODO_PORT_HOSTILE_LIB`,
  `TODO_PORT_SLOT0`, `TODO_PORT_UNPLACED`, `TODO_PORT_NO_CPPM` or
  `TODO_PORT_TARGET_DAMAGED`, and the legacy pair stays untouched (Section 2).

The port rewrites `#include "<sibling>.h"` only inside the legacy pairs it
converts. It does not report any other file that includes a ported block's
`.h`, such as a hand-written `.cppm` or a testbench `.cpp`, and that file
fails the build with a missing header once the port deletes it. Replace the
include with the block's `import` by hand.

### Port a parameterized block by hand (`TODO_PORT_PARAM`)

`make migrate` does not parameterize a block and does not port one that is.
Do it in two passes, in this order.

**First, make the user code template-correct, in place in the legacy files.**
This needs understanding of the code, not text substitution:

- Prefix every out-of-line definition with `template<typename Config>` and
  rewrite `<block>::` to `<block><Config>::`.
- The generated class region already declares
  `using typename <block>Base<Config>::<T>;` for each parameterized type and
  structure of the base, and `using <block>Base<Config>::<name>;` for each
  block parameter, port and derived parameterizable constant (see
  `examples/ip_test/ip/model/ip.cppm`). Do
  not repeat them, because a second using-declaration of the same name is a
  compile error. Qualify any other dependent type as
  `typename <block>Base<Config>::<T>`.
- Reach inherited base members through `this->`, or a matching `using`
  declaration, where they become dependent names.
- Replace each `#include` of a dependency that is a module with an `import`. Copy the
  name from the dependency's generated `export module` line: a sibling block is
  `<project>_<sibling>.block`, a context is `<project>_<includeName>`.

If the code cannot be made template-correct, fix the parameterization first.

**Then move the four user slots into the `.cppm`.** The pipeline has already
scaffolded and filled `<block>.cppm`. The legacy files and the `.cppm` carry the
same markers, so each slot moves between the same two markers:

- **Class body** (from `<block>.h`): the members after the `--template=classDecl`
  `GENERATED_CODE_END` and before the class's `};`, to the same place in the
  `.cppm`.
- **Constructor init list** (from `<block>.cpp`): the user entries, such as
  `,m_myReg(...)`, between the `--template=constructor
  --section=init` `GENERATED_CODE_END` and the `--section=body`
  `GENERATED_CODE_BEGIN`.
- **Constructor body** (from `<block>.cpp`): the statements after the
  `--section=body` `GENERATED_CODE_END` and before the constructor's `};`,
  including every `SC_THREAD(...)` and `static_assert`.
- **Out-of-line definitions** (from `<block>.cpp`): everything after the
  constructor's `};` to the end of the file, to the tail of the `.cppm`.

The last two slots are one stretch of text split only by the constructor's
`};`. Move all of it. Never paste inside a generated region. Drop the legacy
boilerplate the module replaces: the `#ifndef` guard, `#include "systemc.h"`,
and the legacy `.cpp`'s `#include "<block>.h"`.

Then delete the legacy `<block>.h` and `<block>.cpp`, which the sweep never
deletes, run `make gen`, build, and re-run `make migrate` to confirm the item is
gone.

### Restore body-only context imports

The `moduleExport` region imports the block's `.base` module and every context
the block's generated code references through its registers, memories, ports
and connections. The class region opens with the matching
`using namespace <ctx>_ns;` lines. A context type or constant used only in the
hand-written body gives the generator nothing to key on, so you add that
import.

If the build reports `must be imported from module '<ctx>'` or
`use of undeclared identifier`, add `import <ctx>;` to the
`// user imports here` slot, between the `moduleExport` region and the class
region. That slot is always an open module preamble, so an import there is
legal. Put every `import` first. If you also need `using namespace <ctx>_ns;`
and the class region does not already emit it, place it after the imports.
Never paste into a generated region.

### A module-hostile library (`TODO_PORT_HOSTILE_LIB`)

Some libraries cannot be included in a module purview, notably ones that pull
SIMD-intrinsic or precompiled headers, such as OpenCV. Their headers attach to
the named module and clash with the global module:
`declaration of '<sym>' in the global module follows declaration in module
<block>.block`. Moving the include into the global module fragment does not
reliably fix it.

This is a design decision for the block, not a mechanical step. Keep the
library out of the module purview: confine its use to a plain, separately
compiled `.cpp` behind an opaque (pimpl) interface, so the block's code names
no library types.

## 7. Optional: migrate to hierarchical layout

The functional to hierarchical move is a separate, opt-in step. It is not part
of `make migrate` and not required by the `yamlFormat: 2` stamp. A project may
stay functional.

**Finish `make migrate` in functional layout first.** Add no `layout:` key
until `make migrate` is clean. A hierarchical context that still holds legacy
header-mode files is reported as `TODO_UNSUPPORTED_LAYOUT` and is not swept. A
cleanly hierarchical project sweeps without items, and the finish step below
needs one more `make migrate`.

Then opt in by adding `layout: hierarchical` under `fileGeneration:` in the
project file (the base default is `functional`), and run:

```text
make migrate-hierarchical
```

It wraps `migrateYaml.py --to-hierarchical --write <project.yaml>`. It only
relocates the tree: it builds no database, sweeps nothing and regenerates
nothing. Re-running it on a migrated project changes nothing. For a dry run
that prints the full move, delete and rewrite map and changes nothing, run
`migrateYaml.py --to-hierarchical <project.yaml>` without `--write`. There is no
make target for it.

Like `make migrate`, it acts on one project, so in a composed build each
sub-project opts in and runs it from its own `rundir/`. Every composed example
in the tree, such as `ip_test`, `simple_ip` and `twoClk`, declares
`hierarchical` in the top and in every child. Convert the whole composition rather than leaving it mixed.

### When it runs

- **Not opted in** (`layout: functional`, the default): nothing to do.
- **Already hierarchical** (the project file sits under `<prj>/<yaml>/`):
  nothing to do.
- **Opted in but still laid out functionally**: relocation runs. If the project
  is not yet `yamlFormat: 2`, it reports `TODO_NOT_FORMAT2` and moves nothing.

### Composed and nested-provider projects

A sub-project with its own project file and no other provider nested in its
tree converts cleanly. Run the dry run first and confirm it reports no escaping
moves and no manual items.

A project that nests providers in its tree, through vendored symlinks or
cross-project references, needs manual work, because relocation would try to
move files outside its own tree. Convert the independent children first, then
the parent:

1.  Re-point the parent's cross-project references at the children's new
    locations (`prj/yaml` and each node's `<node>/yaml`).
2.  Dry-run until it is clean, then apply. `--write` applies every safe move and
    reports each out-of-tree reference as `TODO_UNREWRITABLE_PATH`. It is not
    transactional and cannot roll back, so a destination clash can leave the
    tree half-moved.
3.  Fix each `TODO_UNREWRITABLE_PATH` reference whose relative depth changed.

In-tree nesting requires a hierarchical parent. A functional parent may compose
children only as external siblings. A child project file is referenced through
`projectFiles:`, never `include:`; `make db` rejects the latter.

A file belongs to the project that lists it directly in `projectFiles:`, and
otherwise to the project that reaches it at the greatest depth from the root.
Its directory plays no part, so relocation never changes ownership. See
`builder/base/specs/spec-project-composition.md` §4.

### What it moves

Every move preserves user content byte for byte.

- **Design YAML.** `arch/yaml/<decomp>/*.yaml` moves to `<decomp>/yaml/*.yaml`.
  A block with no decomposition subdirectory maps to the project-root node
  (`yaml/*.yaml`).
- **The project file** moves to `prj/yaml/<projectName>Project.yaml`. Its
  `dirs:` block is cut to `root:`, so the base `hierarchicalDirs:` governs
  placement. Functional overrides such as `verif/vl_wrap` or `fw/include`
  would misplace files under the hierarchical layout.
- **Project-scope files** (`fwIpMain`, `sc_main`, and the `vl_wrap` aggregator
  sources `vl_wrap.{cpp,h,sv}` and `vl_dummy.sv`) move to `prj/fw/` or
  `prj/verif/`. No build `Makefile` or `obj_dir` moves (Section 3).
- **Source.** A fully generated segment (`base`, `registrar`) is cleared of
  marker-carrying files, and `make migrate` recreates them in the new place. A
  file there without the marker is reported as `TODO_UNGENERATED_FILE` and left.
  In a mixed segment (`model`, `rtl`, `vl_wrap`, `tb`, `fwInc`) the known
  generated files (`Includes`, `_package`, the legacy `_hdl_sv_wrapper.sv`) are
  deleted the same way, and every other source file moves.
- **Relative references.** Relative `include:` and `projectFiles:` entries, and
  relative `#include` and `` `include `` paths in user regions, are re-rooted.
  Generated regions wait for `make gen`. `$macro` and absolute paths are left
  alone.
- **The build entry.** `include/` and `rundir/` stay at the project root. The
  tool re-points the `A2C_PRJ_YAML` line in `include/make/shared.mk` at the
  moved project file. It does not re-point `EXTRA_PRJ_SRC_DIRS`,
  `EXTRA_SC_GEN_FILES` or `EXTRA_SV_GEN_FILES` lines that name a segment that
  moves. It reports each as `TODO_UNREWRITABLE_PATH`, and you update it to the
  segment's new node-relative location. A sibling that only shares a top-level
  component with a moving segment, such as `fw/src` beside an `fwInc` segment
  at `fw/include`, is left alone. Which segments move depends on the merged
  `dirs:` and `hierarchicalDirs:`, so read the project file first.

### Read the report

The report prints the move, delete and rewrite map under `DRY-RUN` or `APPLIED`,
and manual items in the usual `<file>:<line>  <KIND>  <message>` form:

| `KIND` | Meaning | Resolve with |
| --- | --- | --- |
| `TODO_NOT_FORMAT2` | Opted in before the project is `yamlFormat: 2`. Nothing moved. | Run `make migrate`, then `make migrate-hierarchical`. |
| `TODO_UNGENERATED_FILE` | A file in a fully generated segment has no marker. Left in place. | Move it to its hierarchical location by hand, or add the marker if it should be generated. |
| `TODO_UNREWRITABLE_PATH` | A relative `include:` or `projectFiles:` reference that leaves the migrated tree, or an `EXTRA_*` line naming a segment that moves. Left unchanged. | Re-point it by hand after the move. |

### Finish the migration

```text
make clean      # drop the database, .gen and rundir/build built from the pre-move layout
make migrate    # re-stamp the moved files, then scaffold and regenerate
```

The final `make migrate` is required. Relocation leaves each moved file's
`GENERATED_CODE_PARAM` line unchanged, but a context's key comes from its YAML
location, which just changed. The moved firmware includes
(`<context>IncludesFW.{h,cpp}`, which stay header-mode and so move rather than
regenerate) then make `make gen` abort with:

```text
The context specified in GENERATED_CODE_PARAM: <ctx>.yaml is not a known context.
```

The re-stamp that fixes this runs only in the sweep, so only `make migrate`
reaches it. `make migrate` also runs `db`, the sweep, `newmodule` and `gen`, so
run it instead of those targets. Then build and run the normal targets, and
resolve any item the report lists.

## References

- `make migrate` and `migrateYaml.py`, which run every step.
- `make migrate-hierarchical` and `migrateYaml.py --to-hierarchical`
  (`pysrc/migrateLayout.py`), the opt-in layout move.
- Text phases: `pysrc/evalPyToSv.py`, `pysrc/migrateAddressControl.py`,
  `pysrc/migrateVariantSchema.py`, `pysrc/migrateIncludes.py`,
  `pysrc/migrateModuleHeader.py`.
- Sweep phases: `pysrc/migrateFilePrefix.py`, `pysrc/migrateOrphans.py`,
  `pysrc/migrateProjectParam.py`, `pysrc/migrateModuleEndlabel.py`,
  `pysrc/migrateStaleSvNames.py`.
- Ports: `pysrc/migrateBlockModulePort.py` (block port for `--port`, External
  and testbench-top ports for `--port-tb`) and `pysrc/migrateTbConfig.py`
  (`<block>Config.cpp` split for `--port-tb`).
- `config/createBuildManifest.py` and `include/make/a2c-common.mk`, the
  generated-file manifest and the `EXTRA_*` variables.
- `address-migration.md` for the address-control items.
- `manage-build.md` for `make` targets.
