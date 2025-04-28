# Arch2Code

This tool (Arch2Code) is intended to simplify the generation of Hardware Architecture and generation of Arhictecture Documentation, System Verilog, and System C. Arch2Code is sometimes abbreviated A2C.

A **S**ingle **S**ource of **T**ruth, **SSoT**, is used to describe the architecture. Once the source SSoT is modified all outputs for the architecture can be generated. The SSoT is expressed in the yaml file format.

To get started using *Arch2Code*, see the [documentation](https://docs.arch2code.org/a2c-docs/latest/index.html).

[//]: # (This is a comment that will not render in the readme)
[//]: # "This is a comment that will not render in the readme"
[//]: # 'This is a comment that will not render in the readme'

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
