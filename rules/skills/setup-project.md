---
name: setup-project
description: Guide for initializing a new arch2code project, the directory layout (hierarchical or functional), and configuring the project file, including its testbench clocks and resets
---
# Skill: Set up a project

## Purpose
Create a project, understand where YAML and generated files go, and configure the project file.

## References
*   `ARCH2CODE_AI_RULES.md`, sections "Project File (`project.yaml`)" and "Project Configuration".
*   `builder/readme.md` for the bootstrap sequence.

## 1. Create the project

Start from an empty git repository with arch2code added as a submodule at `builder/`, then run `./builder/arch2code.py --newproject`. It asks for the project name, firmware, RTL and the copyright line, then:
*   writes the project file `prj/yaml/<name>Project.yaml`, the design file `yaml/<name>.yaml` and a `.gitignore`;
*   builds the database;
*   scaffolds `Makefile`, `include/make/shared.mk`, `rundir/Makefile`, `rtl/Makefile` and the seed blocks' implementation files;
*   runs `make gen` to fill the generated regions.

Edit the files it writes from then on. Do not copy makefiles from an example. `make newmodule` also creates any of the four makefiles that is missing, and never rewrites one that exists.

## 2. Directory layout

The project file's `fileGeneration.layout` picks the layout. `--newproject` writes `hierarchical`. A project file that sets no layout gets `functional`.

### Hierarchical

Generated files sit beside the YAML of each node. A node is the parent of the directory holding a YAML file, so a file at `<node>/yaml/<file>.yaml` generates into `<node>/model/`, `<node>/rtl/`, `<node>/base/`, `<node>/tb/`, `<node>/verif/`, `<node>/fw/` and `<node>/registrar/`. The project file sits in `prj/yaml/`, and `rundir/` and `include/` stay at the project root.

```text
<root>/
├── prj/yaml/my_chipProject.yaml    # project file
├── yaml/my_chip.yaml               # root node
├── model/ rtl/ base/ tb/ verif/ fw/ registrar/
├── isp/                            # subsystem node
│   ├── yaml/isp.yaml
│   └── model/ rtl/ base/ tb/ verif/ fw/ registrar/
├── include/make/shared.mk
├── rundir/Makefile
└── Makefile
```

Put each node's YAML directly in its `yaml/` directory. A file at `yaml/isp/isp.yaml` has node `yaml/`, so it would generate into `yaml/rtl/`. To add a subsystem, create `<subsystem>/yaml/<file>.yaml`.

### Functional

Each generated segment has one root under the project root, set by `dirs:` (`$root/model`, `$root/rtl`, `$root/base`, `$root/tb`, `$root/verif/vl_wrap`, `$root/fw/include`, `$root/registrar`). Inside each, files mirror the YAML file's directory relative to the project file. With the project file in `arch/yaml/`, a block in `arch/yaml/ip/ip.yaml` generates into `model/ip/`, `rtl/ip/`, `base/ip/` and `verif/vl_wrap/ip/`. Keep the project file at the top of the YAML tree.

### Both layouts

*   Context files (`*Includes.cppm`, `*_package.sv`) follow the same rule as blocks.
*   Testbench files nest one level further, under the block name: `tb/<block>/`.
*   `include:` and `projectFiles:` paths are relative to the file that holds them. See `design-yaml-includes.md`.
*   `make db` records the source and include directories in `.gen/build.mk`, so adding a directory needs no Makefile change.

### Placement overrides

The default placement is almost always right, so do not add an override to reproduce it. In the functional layout, a top-level `blockDir:` in a YAML file sets the directory for every block and context in that file, relative to each segment root. `blockDir: .` puts them directly under `model/`, `rtl/` and so on. A per-block `dir:` sets it for one block. In the hierarchical layout, do not set `blockDir:` or `dir:`. Move the YAML file into the node directory you want instead.

## 3. The project file

| Key | Rule |
| :--- | :--- |
| `yamlFormat: 2` | Required. `make db` rejects a project file without it and tells you to run `make migrate`. |
| `projectName` | The project's name. It prefixes the project's C++ module names. |
| `dirs:` | Only `root` is required, relative to the project file. Other segments come from the base config. |
| `projectFiles:` | The entry design files. See `design-yaml-includes.md`. |
| `topInstance` | Required when the project declares instances. A definitions-only project omits it. |
| `fileGeneration:` | `layout`, `fileCopyrightStatement`, and any `fileMap` entries the project adds. |
| `svFilePrefix`, `scFilePrefix`, `fwFilePrefix` | Optional filename prefixes. |
| `instanceGroups:`, `addressObjects:` | Address policy. See `manage-address-space.md`. |
| `clocks:`, `resets:` | The testbench. See below. |

Use the `$root` and `$a2c` macros in paths. List only the settings the project changes. Do not restate the base config's `dirs:`, `fileMap` or templates.

```yaml
yamlFormat: 2
projectName: my_chip

projectFiles:
  - ../../yaml/my_chip.yaml

topInstance: my_chip_tb

dirs:
  root: ../..

fileGeneration:
  layout: hierarchical
  fileCopyrightStatement: "Copyright My Company 2026"

instanceGroups:
  top:
    varType: inst_top
    enumPrefix: INST_TOP_

addressObjects:
  memories:
    alignment: memsize
    sizeRoundUpPowerOf2: true
    sortDescending: true
  registers:
    alignment: 8
    sortDescending: true
```

`--newproject` writes the `top` instance group. Keep it, because the seed design's instances set `instGroup: top` and `make db` rejects a group the project file does not declare.

### Firmware headers

A project that wants firmware headers adds `includeFW` under `fileGeneration.fileMap`. `--newproject` writes it when you ask for firmware. A project-wide address header needs a `regAddresses` entry with `mode: project`, whose `name:` is the file's literal basename. The base config has no active `regAddresses` entry, so a project gets the header only by declaring one. See `manage-address-space.md`.

## 4. Testbench clocks and resets

The project file's `clocks:` and `resets:` declare the testbench. They bind the input clocks and resets of the top block, the `topInstance`'s block. A block's own clocks and resets are declared on the block. See "Clocks and resets" in `design-architecture.md`.

A project that omits `clocks:` gets one testbench clock, `clk`, with `period` 1 ns. One that omits `resets:` gets one reset, `rst_n`, on the default clock.

*   `clocks.<name>`: `desc` (required), `default` (exactly one `true`, implied with one entry), `period` (positive integer, default `1`; an odd value in `ps` is rejected) and `timeUnit` (`ps`, `ns` or `us`, default `ns`).
*   `resets.<name>`: `desc` (required), `default` (exactly one `true`, implied with one entry), `clock` (default: the default clock) and `releaseCycles` (positive integer, default `3`, the reset's own clock edges before release).
*   The default reset belongs to the default clock. A clock and a reset may not share a name. Every reset is active-low.

Each top-block input is bound by the first rule that applies:
1.  The `topInstance` row's `clocks:`/`resets:` map, `<top-block port>: <testbench name>`.
2.  A testbench entry of the same name.
3.  `clk` falls back to the default testbench clock. `rst_n` falls back to the selected reset of the testbench clock its own clock is bound to.

`make db` rejects a top-block input that no rule binds, and a testbench entry that binds no top-block input. So every entry needs a matching input on the top block, either by name or by the map:

```yaml
# project file
clocks:
  clk:     { desc: "main clock", default: true, period: 1, timeUnit: ns }
  clkSlow: { desc: "slow clock", period: 3, timeUnit: ns }
resets:
  rst_n:     { desc: "main reset", default: true, clock: clk }
  rstSlow_n: { desc: "slow reset", clock: clkSlow, releaseCycles: 4 }

# design YAML: the top block declares both domains
blocks:
  my_chip_tb:
    desc: "Testbench container"
    clocks:
      clk:     { default: true }
      clkSlow: {}
    resets:
      rst_n:     { clock: clk }
      rstSlow_n: { clock: clkSlow }
```

When this project is a child of another, its `clocks:`/`resets:` do not bind its top block. The parent's instance map does.

## 5. Address policy and register decode

*   `instanceGroups:` and `addressObjects:` belong in the project file. See `manage-address-space.md`.
*   Register decode is declared per block: a router block carries `addressBlock:` and is generated, never hand-written. See `design-register-decode.md`.

## 6. Build files

*   `include/make/shared.mk` sets `PROJECTNAME`, `TB_TOP_MODULE`, `HDL_TOP_MODULE` and `A2C_PRJ_YAML`, then includes `a2c-common.mk`. `rundir/Makefile` includes `shared.mk` and then `a2c-systemc.mk`.
*   Clang is the recommended compiler. Set `USE_GCC` only where a simulator requires GCC. See `manage-build.md` for the compiler settings and for `EXTRA_SC_GEN_FILES` / `EXTRA_SV_GEN_FILES`.

## Validation
Run `make db` to check that the project file and design load.
