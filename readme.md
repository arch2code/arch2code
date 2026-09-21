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

## Recommended next step for AI agent users

`--newproject` does not install any agent configuration. Users working with an AI coding agent are recommended to run:

```
make agents-setup
```

This creates `AGENTS.md` from the template, symlinks `CLAUDE.md`, `GEMINI.md` and `ARCH2CODE_AI_RULES.md` at the repository root, and deploys the Arch2Code skill files into the agent skill directories, for example `.claude/skills/`. The target is available only after project creation, because it depends on the scaffolded makefiles.

## Build and run

```
make -C rundir run
```

When RTL was selected, the RTL may also be linted:

```
make -C rtl lint
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
|-- pu_out              = Directory holding output files for both .pu (plant uml files) files and resulting .svg (images) files
|
|-- gv_out              = Directory holding output files for both .gv (graphviz dot files) files and resulting .gv.svg (images) files
|
|-- templates           = Input templates for SystemC and SystemVerilog generated output
|
|-- examples            = directory with all the example projects
  |
  |-- mixed             = Mixed example
    |
    |-- arch            = directory with yaml files
    |
    |-- systemVerilog   = directory with systemVerilog files
    |
    |-- model           = directory with systemC file
  |
  |-- tests               = Contains pipeline golden results for sanity tests
```

# YAML input and project setup

see `mixed/readme.md`

## SystemVerilog Generated output
see `systemVerilog/readme.md`
