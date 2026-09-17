# Review of build and HDL boundary changes

## Scope

Static review of the VCS/Xcelium build integration and generated HDL boundary
include/macro changes. Builds and tests were not run at the user's request.

## Findings

### High: transit structures can fail boundary generation

`pysrc/processYaml.py:3111` reads `structWidths[structKey]` for every
parameterizable structure exposed at a wrapper boundary. `calcVlTops()` fills
that map only from the block's `blockParameterizedDecls`.

A params-less block can transit a parameterized structure declared elsewhere.
That structure is present in the block view but absent from the top's
`structWidths`, so `--vlBoundary` raises `KeyError`. The transit test in
`unittest/test_transit_surface_classification.py` renders the registrar but does
not run boundary-pin generation.

Fix the `VLTOPS` width data so it covers every parameterized structure used by
the wrapper boundary, including transit structures. Add a test that calls
`getVlTopBoundaryPins()` for a params-less transit block.

### High: eval-derived pins use the nominal structure width

`pysrc/processYaml.py:3075-3077` evaluates HDL parameters such as AXI4-Stream
`tstrb_t` and `tkeep_t` against the structure row's stored `width`.
`getVlTopBoundaryPins()` has the selected top's resolved widths, but does not
pass them into `hdlParamWidths()`.

A non-default parameterized payload can therefore emit a VCS port map or
Xcelium shell with default-width strobe and keep pins. The assertions generated
by `templates/systemc/vlRegistrar.py` do not cover these pins because
eval-derived pins have no `structureKey`.

Evaluate HDL parameters against the selected top's resolved structure widths.
Cover an AXI4-Stream variant whose payload width differs from the default.

### Medium: flattened topology names are not unique

`include/make/a2c-systemc.mk:204` and `dutRun.py:34` replace every hierarchy
separator with `_`. Distinct valid paths can then select the same snapshot. For
example, `tb.u_a.u_b` and `tb.u_a_u_b` both become `tb_u_a_u_b`.

Use an injective filename encoding, or preserve dots because they are valid in
filenames. The makefile and dispatcher must use the same encoding.

### Medium: simulator command changes can reuse stale snapshots

The VCS stamps in `include/make/a2c-vcs.mk:44-81` do not record the complete
analysis and link commands. Changes to `VCS_OPTS`, `VCS_ELAB_OPTS`, linker
flags, include directories, or source-list options can leave the existing
snapshot newer than all named prerequisites.

`include/make/a2c-xrun.mk:50-54` records `XRUN_OPTS` and elaboration arguments,
but not `XRUN_LD_LIBS` or the rest of the generated xrun command.

Make command-affecting values prerequisites through content stamps. Include the
full normalized command inputs used by each analysis, elaboration, and link
stage.

### Low: Xcelium requires unused standalone SystemC settings

`include/make/a2c-systemc.mk:17-28` checks `SYSTEMC_INCLUDE`,
`SYSTEMC_LIBDIR`, and `LD_BOOST` before the Xcelium branch replaces the SystemC
include path and bypasses the normal linker command.

An Xcelium-only installation can have valid `XCELIUM_TOOLS` and
`XRUN_GCC_VERS` settings but fail while parsing the makefile. Move or
conditionalize checks that apply only to the standalone SystemC and VCS flows.

## Other observations

The reviewed simulator macro pairing and generated DUT-header selection did not
show another actionable defect. The working tree also contains a deleted
tracked SQLite journal file, `unittest/tmpy7kz9g0x.db-journal`; keep that
unrelated deletion out of this change unless it is intentional.
