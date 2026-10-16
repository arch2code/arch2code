---
name: address-migration
description: Convert a legacy arch2code project from project-wide addressControl.yaml to per-block addressBlock: routers and the project.yaml address-policy sections. Covers what the make migrate address phase does, how to resolve TODO_ROUTER_RESOLUTION, TODO_INTERFACE_SCOPE and TODO_LEAF_REGISTER_PORTS, and the checks to make after conversion.
---
# Skill: legacy address-control migration

## Purpose

A legacy project points `project.yaml` at an `addressControl.yaml` holding
`AddressGroups:`, `InstanceGroups:` and `AddressObjects:`. arch2code declares
each router with a top-level `addressBlock:` on its block, and keeps
`instanceGroups:` and `addressObjects:` in `project.yaml`. `make db` refuses a
project whose `project.yaml` has no `yamlFormat: 2` and tells you to run
`make migrate`.

`make migrate` does the conversion. This skill covers what its address phase
does, the manual items it reports, and what to check afterwards. For the
migration as a whole, including the report format and exit codes, see
`migrate-project.md`. To design or change decode in a migrated project, see
`design-register-decode.md`.

## What the address phase does

For each `AddressGroups:` row:

- **No `decoderInstance:` and no instance names the group.** The row is dormant
  and is dropped.
- **`decoderInstance:` names an instance of a block in the project.** That block
  becomes the router. The phase writes an `addressBlock:` on it with
  `addressGroup:` set to the row name and `addressIncrement`,
  `maxAddressSpaces`, `varType` and `enumPrefix` copied verbatim.
  `RegisterBusInterface:` becomes both `upstreamPort:` and
  `registerDecoderPort:`. When `RegisterBusInterface:` is absent or `None`,
  the phase writes neither key, so both default to `apbReg`, and raises no
  `TODO_INTERFACE_SCOPE`. The phase does not copy `primaryDecode`,
  `varTypeContext` or `decoderInstance` into `addressBlock:`. The build infers
  the primary router from the hierarchy.
- **Anything else** is reported as `TODO_ROUTER_RESOLUTION` (Step 3).

It also:

- reports `TODO_INTERFACE_SCOPE` when a router's file does not see the
  `RegisterBusInterface:` interface through its `include:` chain (Step 2);
- reports `TODO_LEAF_REGISTER_PORTS` for each routed leaf (see "Migration
  diagnostics");
- rewrites `postProcess:` in `project.yaml`. It removes every entry that
  names a base script or the legacy `postParseRegister.py`, and deletes the
  block if nothing is left (Step 4);
- appends `instanceGroups:` and `addressObjects:` to `project.yaml`, copying
  the legacy row bodies;
- removes the `addressControl:` pointer and deletes `addressControl.yaml`
  once every `AddressGroups:` row is converted or dropped. Other manual items
  do not keep the file. While a router is unresolved, both stay and the report
  says `DELETE_DEFERRED`. Never delete the file by hand.

The project is stamped `yamlFormat: 2` only when no address item remains and
the other phases are clean.

| Report `KIND` | Meaning | Resolve in |
| --- | --- | --- |
| `TODO_ROUTER_RESOLUTION` | An `AddressGroups:` row's router cannot be resolved. | Step 3 |
| `TODO_INTERFACE_SCOPE` | A router's file does not see the register-bus interface. | Step 2 |
| `TODO_LEAF_REGISTER_PORTS` | A routed leaf needs a `registerPorts:` decision. | The `registerPorts:` note under Migration diagnostics |
| `ADVISORY_LEAF_REGISTER_PORTS` | The same decision, restated on every later run. Never blocks. | The `registerPorts:` note under Migration diagnostics |

## Step 1: capture a baseline, then run the converter

`make migrate` regenerates the tree, so capture the generated SystemC and
SystemVerilog output before the first run. Step 5 compares against it.

Then run `make migrate` from the project's `rundir/`. In a composed build, run
it once per sub-project, children first (`migrate-project.md`, "Composed
builds").

## Step 2: make the register-bus interface visible to every router

`TODO_INTERFACE_SCOPE` reads `Router block '<block>' (file <file>) has no
addressBus: true interface authored in its load-time scope.` The router's file
has to see the interface named by `upstreamPort:`, with its structures and
types.

Each YAML file sees only itself, the files it includes, and the files those
include. If a router's file does not see the interface, move the interface,
its structures and their types into an existing file every router file sees
by that rule, usually the deepest shared or router file. Do not create a new
YAML file for it, and do not give a router file an `include:` of the top
integration file, which inverts the include direction. See
`design-yaml-includes.md`.

`TODO_INTERFACE_SCOPE` is raised once per router, on the run that writes that
router's `addressBlock:`. It is not repeated, even while another router is
unresolved, so fix it before you re-run. A missed scope fix fails `make db`
later with `Router block '…' (file …) names upstreamPort '…', but no visible
interface has that name.`

## Step 3: resolve the router in the legacy row

`TODO_ROUTER_RESOLUTION` has three forms:

- `AddressGroups row '<group>' is referenced by an instance but names no
  decoderInstance, so its router block cannot be resolved …`
- `AddressGroups row '<group>' decoderInstance '<inst>' does not resolve to a
  router block …`
- `AddressGroups rows [<groups>] both resolve to router '<block>'; this group
  duplicates a prior addressBlock: …`

The first two messages say `author addressBlock: by hand` and the third says
`resolve by hand`. Do not follow that wording. Do not author `addressBlock:`.
Fix the legacy row in `addressControl.yaml` as below, then re-run
`make migrate`. The phase re-reads the legacy row on every run and keeps
reporting it until the row resolves, so a hand-written `addressBlock:` loops.

- **No `decoderInstance:`, or one that does not resolve.** Set
  `decoderInstance:` to the instance of the router block that serves the
  group. The instance and its block must be declared in the project's YAML.
  For a router instance `uApbDec`:

  ```yaml
  AddressGroups:
    top:
      addressIncrement: 0x01000000
      maxAddressSpaces: 16
      varType: addr_id_top
      enumPrefix: ADDR_ID_TOP_
      decoderInstance: uApbDec
  ```
- **Two rows on one router.** A router block serves one group. If one group
  is redundant, move its instances' `addressGroup:` to the other group and
  delete its row. Otherwise declare a second router block, instance it where
  that group's instances sit, and point the second row's `decoderInstance:` at
  it.

While a router is unresolved, each run appends `instanceGroups:` and
`addressObjects:` to `project.yaml` again. Before each re-run, delete the
copies the previous run appended at the end of `project.yaml`, or the file ends
up with duplicate keys.

## Step 4: check `project.yaml` after the conversion

Do these once the run that removes the `addressControl:` pointer has finished.
The phase does nothing after that run, so it cannot undo them.

- **`postProcess:`.** A project's `postProcess:` list replaces the base list;
  it does not add to it. The phase strips the base scripts from a block it
  keeps, so a kept block runs only the project's own scripts and register-port
  synthesis never runs. If `project.yaml` keeps a `postProcess:` block,
  list the base scripts first, in the order `builder/base/config/project.yaml`
  gives them, then the project's own:

  ```yaml
  postProcess:
    - $a2c/config/postParseRegisterPorts.py
    - $a2c/config/postParseChecks.py
    - $root/scripts/myCheck.py   # the project's own script
  ```

  If the block was deleted, the base list applies and nothing is needed.
- **`instanceGroups:` and `addressObjects:`.** Each appears at most once.
  `addressObjects:` must be present if the design has registers or `regAccess`
  memories (`manage-address-space.md`). Add it by hand if the legacy file had
  none.
- **The pointer and the legacy file are gone.** Search the tree for any other
  project that names `addressControl.yaml`.

## Step 5: regenerate and compare

`make migrate` ends with `make gen`. Build and run the project's normal targets
(`manage-build.md`), then compare the generated output with the Step 1
baseline. Byte-identical output is the goal. Review every difference.

## Migration diagnostics

### The `registerPorts:` note

`TODO_LEAF_REGISTER_PORTS` reads `Routed leaf block '<leaf>' (instance '<inst>',
served by router '<router>' for group '<group>') needs a registerPorts:
declaration authored by hand …`. It is raised on every run while the legacy
`AddressGroups:` table exists, and the run that deletes the table is the last
to raise it. Decide each leaf as follows:

- **A reusable IP**, whose `<block>Base` must be self-contained, declares one
  `registerPorts:` row naming the register-bus interface. The interface must
  be visible in the leaf's own file.
- **A block with a block-level `ports:` section** must declare `registerPorts:`
  too, or `make db` fails.
- **Any other top-down leaf** needs nothing. It infers its register bus from
  the serving router.

From the next run on, every routed leaf with no `registerPorts:` is listed as
`ADVISORY_LEAF_REGISTER_PORTS`. The advisory never blocks and never clears for a
top-down leaf. It stops only when the leaf declares `registerPorts:` or no
router serves it. Read it once per leaf.

### Build errors after conversion

The converter copies the legacy topology, and `make db` fails where that
topology breaks a decode rule. These come up most:

- **A routed leaf below a router-less container.** The converter leaves
  `addressGroup:` on the leaf. The router dispatches to the outermost
  passthrough container beside it, and only that container instance carries
  `addressGroup:` (`design-register-decode.md` §1). The build reports
  `Leaf instance '…' … is in container '…' which is not served by any router,
  …`, or `Instance '…' … is fed through router-less container '…' and must not
  carry addressGroup:`. Move `addressGroup:` from the leaf to the container
  instance that sits in the router's container, and remove it from every
  instance below. This works only when each container on the way holds no
  other register consumer and owns no registers. Otherwise add a router to
  that container.
- **`addressIncrement` or `maxAddressSpaces` not a power of two.** The value
  was copied verbatim and fails with `In …, addressBlock: of block '…'
  (addressGroup '…') sets maxAddressSpaces …, which is not a power of two. …`
  Fix it in the router's `addressBlock:`.
- **`upstreamPort` not visible.** `Router block '…' (file …) names upstreamPort
  '…', but no visible interface has that name.` Redo Step 2.

For every other decode error, see the diagnostics appendix of
`design-register-decode.md`.

A real-valued `eval:` such as `$DWORD / 2.0` is reported as an eval
`NEEDS_MANUAL` row, not an address item. `migrate-project.md` covers it.

## References

- `builder/base/migrateYaml.py` (`make migrate`) and
  `builder/base/pysrc/migrateAddressControl.py`, the address phase and the
  source of its messages.
- `builder/base/config/schema.yaml` for `blocks.addressBlock`,
  `instanceGroups` and `addressObjects`.
- `migrate-project.md` for the whole migration.
- `design-register-decode.md` for the decode rules and diagnostics.
- `manage-address-space.md` for `instanceGroups:` and `addressObjects:`.
- `design-yaml-includes.md` for include visibility.
