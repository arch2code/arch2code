# Arch2Code

This tool (Arch2Code) is intended to simplify the generation of Hardware Architecture and generation of Arhictecture Documentation, System Verilog, and System C. Arch2Code is sometimes abbreviated A2C.

A **S**ingle **S**ource of **T**ruth, **SSoT**, is used to describe the architecture. Once the source SSoT is modified all outputs for the architecture can be generated. The SSoT is expressed in the yaml file format.

To get started using *Arch2Code*, see the [documentation](https://docs.arch2code.org/a2c-docs/latest/index.html).

# Getting Started

A new project starts from a clean, empty git repository. Arch2Code is added as a git submodule at `builder/`, and `arch2code.py --newproject` creates the project.

```
git init myChip && cd myChip
git submodule add https://github.com/arch2code/arch2code.git builder
pip3 install -r builder/requirements.txt
./builder/arch2code.py --newproject
```

## What `--newproject` asks and produces

`--newproject` asks for the project name, whether the project includes firmware, whether the project includes RTL, and the copyright statement. It then writes the project file, the seed design YAML and a `.gitignore`, builds the database, and scaffolds `Makefile`, `include/make/shared.mk`, `rundir/Makefile` and `rtl/Makefile`. No manual file editing and no copying of makefiles from an example is required.

This is the one command that is run directly rather than through `make`, because at project-creation time no makefile exists yet. Every later operation uses `make` targets, such as `make db`, `make gen` and `make newmodule`.

## AI agents

If you use an AI coding agent, run:

```
make agents-setup
```

This installs the Arch2Code rules and skills for Claude Code, Gemini CLI, OpenCode and Cursor.

## Build and run

```
make -C rundir run
```

The first run passes. The scaffolded `tb/<name>/<name>External.cppm` holds a placeholder test, `test_replace_me`, which checks nothing, and an end-of-test voter that ends the run once the test completes. Until you replace the placeholder, each run prints `WARNING: test_replace_me is a placeholder with no checks; replace it with a real test in <name>External.cppm`. Write your tests as the comments in that file describe. Rename or remove `test_replace_me` in both files together: the function and its `ADD_TEST` line in the External, and its entry in the list in `tb/<name>/<name>Config.cpp`.

When RTL was selected, the RTL may also be linted:

```
make -C rtl lint
```

## A first design change

The seed design declares blocks and instances only. To check that a YAML edit regenerates and builds, add a constant and a type above `blocks:` in `yaml/<name>.yaml`:

```yaml
constants:
  DATA_WIDTH: {value: 32, desc: "Data bus width"}

types:
  data_t: {width: DATA_WIDTH, desc: "Data word"}
```

Then create and fill the new files:

```
make newmodule
make gen
```

`make gen` never creates a file, so `make newmodule` comes first. `make newmodule` creates `model/<name>Includes.cppm` and `rtl/<name>_package.sv`, plus `fw/<name>IncludesFW.h` and `fw/<name>IncludesFW.cpp` when firmware was selected. `make gen` then writes `DATA_WIDTH` and `data_t` into the `.cppm`, the `.sv` package and the firmware `.h`. Build the model without running it:

```
make -C rundir
```

When RTL was selected, lint the RTL as well:

```
make -C rtl lint
```

Then run it. The run passes and prints the placeholder warning:

```
make -C rundir run
```

# Directory Structure & key files in the root of the repository

```
arch2code.py            = The application
LICENSE                 = license file
|
|-- pysrc               = Directory for python sources
|
|-- pu_input            = Directory containing plant UML sequence diagram input flows
|
|-- pu_jar              = Directory containing plant UML jar file, used for .pu file processing and flows
|
|-- templates           = Input templates for SystemC and SystemVerilog generated output
|
|-- specs               = Normative specifications of generator features
|
|-- examples            = directory with all the example projects
  |
  |-- mixed             = Mixed example
    |
    |-- arch            = directory with yaml files
    |
    |-- rtl             = directory with systemVerilog files
    |
    |-- model           = directory with systemC file
  |
  |-- tests               = Contains pipeline golden results for sanity tests
```

`--flows` writes PlantUML output to `pu_out/`, and `--diagram` and `--drawStructure` write graphviz output to `gv_out/` by default, both in the directory `arch2code.py` runs from.

# YAML input and project setup

See `ARCH2CODE_AI_RULES.md` for the YAML sections and the project file, and `rules/skills/setup-project.md` for the directory layout.

## Simulators
`specs/SIMULATOR_INTEGRATION.md` covers building and running under VCS and Xcelium.
