# Arch2Code

Arch2Code (A2C) generates hardware architecture documentation, SystemVerilog, and
SystemC from a single source of truth in YAML. This file is the glossary. It
says what each term means and which word to pick when several exist.

For generator pipeline, data model, and resolution rules, read
`GENERATOR_ARCHITECTURE.md`. For the schema contract, read
`config/SCHEMA_SPECIFICATION.md`.

## Language

### Keys and identity

**Row**:
One entry persisted from a YAML list section (`blocks:`, `instances:`,
`connections:`, etc.).

**Anchor**:
The YAML dict key that names a row in its section. The schema stores it as-is and
appends it to the row's storage key.

**Storage key**:
A row's hierarchical name inside one context. Built by concatenating ancestor
storage keys and the anchor. No separator between parts.

**Qualified key**:
`{storageKey}/{context}`. This is a row's identity. The context path may contain
`/`, so the qualified key may contain several slashes. Never split a qualified
key on `/` to recover components.

**Context**:
The YAML file where a row was authored. It is the suffix after `/` in the
qualified key. Scope walks this file's include chain.

**Scope**:
How a reference resolves. Walk the include chain of the referring row's context
file. That is the default. Global resolution drops include-chain isolation and
needs architect signoff.
_Avoid_: assuming references resolve globally

### Design entities

**Block**:
A design unit. Identity is the qualified key. In prose, `(block, context)` is
enough to tell two same-named blocks apart.
_Avoid_: module (the emitted SystemVerilog or C++ module, not the design unit),
component, unit

**Instance**:
An occurrence of a block inside a container block. Names the container, names
the block type, and selects a variant if needed.
_Avoid_: sub-block

**Container**:
The block that holds an instance. Every container is a block. Container describes
a relationship, not a separate block kind.

**Interface type**:
A reusable control protocol (`apb`, `rdy_vld`, `push_ack`, `axi`, `status`,
`memory`). Lives in the framework `interfaces/` tree. User projects do not
author these. In code and the database, the same thing is an **interface def**
(`interface_defs` table). Prose says interface type.
_Avoid_: "interface" for the protocol itself

**Interface**:
An interface type with concrete structures bound to it. Interface type is
`push_ack`. Interface is push_ack carrying `videoSt`.

**Connection**:
A point-to-point or multi-ended link on an interface (`connections:`). Only
between instances in the same container.
_Avoid_: a connection across a container boundary

**Connection map**:
Routes a container's boundary port to a child instance's port (`connectionMaps:`).
Use these for hierarchical routing. `connections:` wires siblings inside one
container.

**Constant**, **Type**:
Named scalars and enums (`constants:`, `types:`). A constant may be marked
parameterizable. A type defines width and encoding.

**Structure**:
An ordered set of fields (`structures:`). Structures own bit layout. Interface
compatibility follows packed form, not field names.
_Avoid_: struct, record, message

### Ports and the register bus

**Port**:
A datapath interface endpoint on a block boundary (`ports:`).

**Register port**:
A register-bus endpoint on a block boundary (`registerPorts:`). Declared
separately from datapath ports, validated separately. Only a reusable-IP
boundary or a nested router declares one. A top-down register-owning leaf gets
its ingress from the serving router.
_Avoid_: treating register ports as datapath ports

**Router**:
A block with `addressBlock:` set. Generates register decode for register-owning
sibling instances and nested routers in its container. Never decodes its own
container block.
_Avoid_: decoder (the generated artefact, not the declaring block)

**Leaf**:
A block with no user-authored child instances. It may still own registers or
memories.

**Address block**:
The `addressBlock:` declaration that makes a block a router.
_Avoid_: address map (the firmware address view, not the router block)

**Register**, **Memory**:
Addressable objects on a block, typed by a structure. Addresses are derived. You
do not author them.

### Parameterization

**Parameterizable constant**:
A named value marked eligible to become a design parameter. The mark makes it
eligible. It does not parameterize anything by itself.

**Reusable IP**:
A block and its project, built for other projects to instantiate. May expose
`ipParameters` in its root file and declare its own `registerPorts:` for
standalone or nested builds.

**ipParameters**:
Parameters a reusable IP exposes in its root file. Every exposed constant must
be consumed by at least one block param in the same file.

**Param**:
A block parameter in `params:`. Say "parameter" in prose when you are not naming
the YAML key.

**Variant**:
A named binding of every param a block declares. No default-fill. A variant that
skips a param is invalid.
_Avoid_: configuration, flavour, instance parameters

**Config**:
Generated artefact for one variant. Carries resolved values into SystemC and
SystemVerilog.
_Avoid_: swapping config and variant. You author a variant. Generation produces
a config.

### Projects and ownership

**Project**:
A build unit with its own `project.yaml`. Projects compose. One project can
reference another and instantiate its blocks.

**Project file**:
A YAML file under `projectFiles:`. Its closure defines ownership. Match full
canonical paths. Basename or prefix matching is wrong. Not the same as
`project.yaml` unless that file is in the list.

**Include**:
An `include:` entry. Grants name visibility along an include chain. Makes a block
or definition resolvable. Does not grant ownership.
_Avoid_: treating `include:` as ownership. Ownership is `projectFiles:`.

**Ownership**:
Which project generates a given artefact. Comes from `projectFiles:`. Resolving a
block name still needs an `include:` that reaches it.

### Generation

**Generated region**:
Text between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`. Templates own it
and rewrite it every run. Do not edit by hand.

**User region**:
Everything outside a generated region in an in-place file. The author owns it.
Regeneration preserves it.

**Scaffold**:
First creation of a file via `make newmodule`. Not the same as generation. The
file is created once. Generated regions refresh on later runs.

**File map**:
The `fileMap:` block on a block. Lists artefacts generation produces.

**Model**:
The SystemC behavioural implementation of a block.
_Avoid_: C++ (the language, not the artefact), behavioural model

**RTL**:
The SystemVerilog implementation of a block.

**Tandem**:
Run a block's model and RTL on the same stimulus and compare results.
_Avoid_: co-simulation (Verilator wrapping that enables tandem, not the
comparison)

## Relationships

- A project owns many blocks. A block belongs to one project.
- A project may reference another project.
- A container block holds many instances.
- An instance selects one variant of its block.
- A variant binds every param on its block and yields one config.
- An interface uses one interface type.
- Connections link instances in the same container. Connection maps cross a
  container boundary to a child instance.
- Ports and register ports are separate declarations on a block.
- A router serves sibling instances and nested routers in its container, not
  the container block itself.
- A row's identity is its qualified key.
