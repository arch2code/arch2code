# Plan #125 post-merge follow-ups — defects deferred out of the origin/main merge

- **Status:** PLANNED (2026-09-21). No code written beyond the interim guards
  named below, which landed inside the merge itself.
- **Branch:** `feature/125-a2c-20-followup-issues`, after the merge of
  `origin/main` (d7897c62: PRs #124/#131 sockets, #128 AXI user structs and
  optional payloads, #134 arbitration, #135 Pune fixes, #140 Verilator
  dependencies) into the #125 branch (d20563cc).
- **Source:** two independent reviews of the merge resolution. One review
  compared every file changed on both sides against the merge base; the other
  was a second-opinion review that raised twelve findings. Every item below was
  verified against the staged tree and both parents before it was recorded.
- **Rule for this plan:** none of these items is a merge-resolution defect. The
  two resolution defects the reviews found (a dropped `cpp_descriptor_config_name`
  helper and a duplicate `xif` recipe) were fixed inside the merge. The items
  here are either inherited verbatim from one parent or are gaps the merge made
  visible. They are fixed after the merge commit, each as its own commit, so the
  merge stays reviewable as resolution content.

---

## 1. Ordering and gates

| Order | Item | Why this position |
| :--- | :--- | :--- |
| 1 | §2 socket shell on a parameterizable block | Removes an interim db-time rejection; unblocks the socket feature for parameterized IP. |
| 2 | §3 connectionMap boundary validation | Turns a red unit suite green; small, self-contained. |
| 3 | §4 type payload unit coverage | Closes coverage gaps on generator paths the merge touched; no behaviour change. |
| 4 | §5 socket runtime and decode defects | Inherited from main; several need a design decision (wire format, USER support) and are best raised as issues against main first. |
| 5 | §6 cleanups | Zero-risk, fold into whichever commit touches the file. |

Gates that apply to every item: the unit suite
(`unittest/run_all_tests_parallel.sh`) and `make pipeline-test`, run
sequentially, never overlapped (the build-manifest writer suite regenerates
examples in place). A change under `templates/` or `pysrc/` only lands in a
consumer after `make clean` in that consumer.

---

## 2. Socket shell on a parameterizable block

### 2.1 Problem

Main's Python-socket feature emits a `<block>Socket` shell class
(`templates/systemc/classDeclSocket.py`, `templates/systemc/constructorSocket.py`)
that registers itself with the instance factory. For a block with its own
`params:` it does so with one explicit template instantiation per variant,
naming each variant's Config struct. That is the pre-#125 registration scheme.

On the #125 branch a parameterizable leaf carries no registration in its own
module unit. The per-assembler trampoline registrar
(`templates/systemc/blockRegistrar.py`, view `getRegistrarConfigView` at
`pysrc/processYaml.py:1769`) owns it, because the Config an instance binds is
the parent's choice (per-variant, container-sourced, foreign). The trampoline
registers the `_model` and `_verif` kinds only; nothing registers `_socket`.

The merge therefore left parameterized sockets in a state where the shell would
register under a Config the assembler never binds. An interim guard,
`validateSocketOnParameterizedBlock` (`pysrc/processYaml.py:4599`), rejects
`hasSkt: true` on any `isParameterizable` block at `make db`, with
`unittest/test_error_socket_parameterized.py` covering the rejected and the
accepted arm. No ISP project declares a socket shell, so nothing in the
workspace is affected by the guard.

### 2.2 Design

- Extend the registrar view with a `_socket` registration per (child, parent)
  pair when the child has `hasSkt: true`, mirroring the `_model` rows: same
  variant labels, same owner-qualified Config struct, same project scoping.
- Emit the registration from `blockRegistrar.py` alongside the model lambda,
  constructing `<block>Socket<Config>` instead of `<block><Config>`. The
  registrar translation unit must include the socket shell header for that
  block; add it to the registrar's dependency lines the same way the model
  header is added.
- Remove self-registration from `classDeclSocket.py` / `constructorSocket.py`
  for the `hasOwnParams` arm (keep it for the non-parameterizable arm, which
  the pipeline's `pySocket`, `axiSocketMaster` and `axiSocketSlave` examples
  exercise today). `_variant_config_names` in `constructorSocket.py` becomes
  unnecessary once the arm is removed.
- Container-sourced children (`inheritContainerParam`) are a family of C++
  types with no factory key of their own; the model registrar already skips
  them, and the socket registration follows the same rule.
- Delete the interim guard and its unit test, and replace the test with a
  positive one: a parameterizable block with `hasSkt: true` under a parent,
  asserting the registrar emits the `_socket` registration for each variant
  and that the shell's own translation unit emits none.

### 2.3 Acceptance

- The positive test above passes; `test_error_socket_parameterized.py` is gone.
- The three socket examples regenerate without diff.
- A scratch example (not committed) with a parameterized socket block builds
  and its Python side can resolve the `_socket` key for every variant.

---

## 3. connectionMap boundary validation (`unittest/test_validate_ports.py`)

### 3.1 Problem

The suite fails on pure origin/main and in the merge. Its first two tests
expect `make db` to reject (a) a `connectionMaps:` entry on an interior block
whose boundary port nothing above picks up, and (b) a connectionMap whose
computed port name differs from the name the parent's connection computes for
the same physical port. Both builds currently exit 0.

History: main commit b7cde3e2 added `_lookupInstanceFromMap`,
`_collectBoundaryPorts` and a `validatePorts` body that called them, plus the
tests. The parameterized-types branch had independently rewritten
`validatePorts` for the packed-form compatibility concern; when it merged into
main the newer body won and the two helpers became dead code. The #125 branch
never had them, so this merge dropped the dead helpers. Today's `validatePorts`
(`pysrc/processYaml.py:7251`) only inspects blocks that declare `ports:`.

### 3.2 Why the rule is correct (design view, not example count)

- A connectionMap surfaces a contained instance's interface at its block's
  boundary. The block's SystemC class and RTL module declare that port from the
  connectionMap's name (`templates/systemc/baseClassDecl.py`,
  `templates/systemVerilog/module_hdl_wrapper.py`). The parent's generated
  bind statement and RTL instantiation use the connection end's name
  (`pysrc/intf_gen_utils.py` `sc_connect_channel_type`,
  `templates/systemVerilog/moduleInterfacesInstances.py`).
- **Name mismatch** is therefore a hard defect: a C++ "no member named" error
  or an SV elaboration error on a port that does not exist, surfacing late in
  generated code.
- **Orphan on an interior block** is a defect. A `dst` orphan is an unbound
  `sc_port`, which the kernel rejects at elaboration, or an undriven RTL input.
  A `src` orphan is an output nothing reads (an interrupt nobody polls): no
  crash, an invisible correctness bug. A floating handshake stalls forever; an
  unrouted register bus leaves a block at reset defaults. There is no reason to
  write the connectionMap if the interface is meant to go nowhere.
- **Orphan on the project's top instance** is legitimate: those ports are the
  project's exported I/O contract, wired by the project or testbench that
  instantiates it. The testbench external pseudo-block's local-only channels
  (`_ext_cm_*` in `templates/systemc/testbench.py`) are this case. The instance
  row with `container == '_topInstance'` identifies it.

### 3.3 Design

Add `validateConnectionMapBoundaries(connections_flat, connection_maps_flat,
instances_flat)` and call it from `validatePorts` after `validateRtlHierarchy`:

- Index, per block, every boundary port name it acquires from a connection end
  or an outer connectionMap, with the interface key and direction.
- For each connectionMap whose block is not the top instance's block, require
  its computed port name to be in that block's index.
- On failure, `printError` naming the interface, the port, the block, the
  instance and the hazard in design terms (floating input with no driver for
  `dst`, output nothing above reads for `src`), then
  `exit(warningAndErrorReport())`. When a boundary connection of the same
  interface and direction exists under another name, append
  `add port: <name> to the connectionMap`. The existing test greps for
  `connectionmap`, `irq_if`, `boundary` and `port: irq_out`, so no test edit is
  needed.

### 3.4 Acceptance and gate

- All three tests in `test_validate_ports.py` pass.
- `make db` across every example project exits as it does today. The
  intentionally failing `xprojParam` probes fail for their own reasons and
  must not start failing on this check.
- Re-enrol the suite in both runners (an example reader in
  `run_all_tests_parallel.sh`, a numbered suite in `run_all_tests.sh`). The
  merge enrolled it, which turned the CI unit-test job red because the check
  is dead code; the enrolment was removed again on 2026-09-21 until this
  section lands.

---

## 4. Type payload unit coverage

Type payloads (`datatype: type` / `typeStruct` interface parameters, which
spell as a (name, width) pair) are covered at a variant for channel width,
HDL wrapper width, missing backing parameter on a connection, and kind
mismatch (`unittest/test_optional_intf_params.py`). The following variant
paths have no unit test, and the first three sit on code the merge touched:

- **connectionMap with a type payload** sized by a root parameter, where the
  child lacks the parameter. The connectionMaps loop of
  `_validateParameterizedConnectionEndpoints` (`pysrc/processYaml.py:6354`)
  did not recognise `types`-kind payloads until the merge review caught it;
  the fix has no test. Mirror `test_param_type_payload_missing_backing_param`
  with a `connectionMaps:` entry instead of a connection.
- **Thunker member spelling with a type payload.** Every thunker spelling
  assertion uses struct payloads. Assert both arms of
  `_qualified_payload_type_name` (`pysrc/intf_gen_utils.py`): a
  parameterizable type spells `<ctx>_ns::<type>, <owner>_<block><V>Config::<W>`;
  a fixed type whose width names a constant spells the resolved literal.
- **Direct-copy verdict for type payloads.** `unittest/test_payload_direct_copy.py`
  checks structure signatures only; add a `types` pair (equal and differing
  `typeStorage`) and an enum pair to the verdict test.
- **Container parameter inheritance with a type payload.** None of the eight
  inheritance suites binds one; add a type payload to
  `unittest/test_inherit_container_param.py`'s fixture.
- **Cross-project variant with a type payload** in
  `unittest/test_param_cross_project_linkage.py`.

Acceptance: each new test fails when its guard is reverted (verify by
temporarily reverting the connectionMaps `declKind` line for the first one).

---

## 5. Socket runtime and decode defects inherited from main

All code in this section is byte-identical to origin/main; the #125 branch
never touched it. Raise each as an issue against main's socket feature
(#124/#131) and fix on a branch from main, so the fix reaches both lines.
Items 5.1 to 5.3 need a design decision before code.

### 5.1 AXI wire format has no width or burst bound

`interfaces/axi_write/axi_write_port_socket.h:33-34` declares
`uint8_t data[SOCKET_AXI_BURST_BYTES]` (4096, `common/systemc/socketTransport.h:152`)
and `uint16_t strb[SOCKET_AXI_BURST_BYTES / 16]`. The copy loop at line 157
writes `beat_bytes * (awlen + 1)` bytes with no bound: a legal 256-bit,
256-beat burst writes 8192 bytes. Strobes are sixteen bits per beat, so data
above 128 bits truncates its strobe. **Decision:** either `static_assert` the
instantiation to `D::_byteWidth * 256 <= SOCKET_AXI_BURST_BYTES` and
`D::_byteWidth <= 16` with a message that names the wire struct and its Python
ctypes mirror, or widen the wire format. The read side has the same shape.

### 5.2 Socket overloads accept only absent USER payloads

`axi_read_port_socket.h:50,264` and `axi_write_port_socket.h:51,251` take
`std::monostate` for every USER slot. The catalog view sets `hasPortSocket`
from the interface definition alone (`pysrc/processYaml.py:1512`), so a design
that binds a USER payload on a socket-enabled AXI port fails at C++ compile
time. **Decision:** support USER payloads in the wire format, or reject the
combination at `make db` in the socket catalog view with a message naming the
port and the bound payload.

### 5.3 Write BFM dummy beat spelled with an absent WUSER

`interfaces/axi_write/axi_write_bfm.h:133` constructs
`axiWriteDataSt<DATA_T, STRB_T, std::monostate, ID, IDW>` and passes it to
`sendDataCycle`, which takes the exact envelope `axiWriteDataSt<D, S, WU, ID, IDW>`.
Any instantiation with a bound WU fails to compile. Spell the dummy with `WU`.
Not socket-specific, but it arrived with the same feature.

### 5.4 Lockstep acknowledgement wait has no exit predicate

`common/systemc/socketSync.cpp:273` `wait_for_ack` loops on delta cycles until
the acknowledgement arrives. If the peer disconnects while a wait is pending
the receive thread reports closure but the loop never observes it, and the
kernel spins forever. Add a connected-and-running predicate to the loop and
return (or raise the end-of-test vote) when it drops.

### 5.5 Lockstep state crosses threads unsynchronised

`socketSync.cpp:27,32,33,34` declare `g_python_ready`, `g_at_boundary`,
`g_lockstep_epoch_ns`, `g_lockstep_epoch_set` as plain globals. The receive
thread (`std::thread`, line 496) writes them (line 508) and SystemC threads
read them; that is a data race. The receive thread also reaches
`sc_time_stamp()` through `socketSyncScTimeNs()`, which is not safe off the
kernel thread. Make the flags `std::atomic` or guard them with the existing
mutexes, and have the receive thread hand the epoch capture to a kernel-side
process instead of reading kernel time itself.

### 5.6 APB socket decode excludes memory windows

`pysrc/processYaml.py:1380` `_blockRegisterWordDecode` skips
`regType == 'memory'` and returns `None` when no register offsets remain. The
code comment records this as intentional (memory windows are range-decoded in
RTL). Consequences: a valid memory access through the socket returns PSLVERR,
and a memory-only target has no map at all, which the socket treats as "accept
every address". **Decision:** persist complete register and memory ranges in
the decode view, or reject socket drive ports onto memory-only targets at db.

### 5.7 APB target selected by first connection match on block type

`pysrc/processYaml.py:1443` `_socketApbTargetBlockKey` scans all project
connections and returns the first whose source or destination instance has
this block type and port. Two instances of one block type wired to different
APB targets resolve to whichever connection sorts first. The per-instance
target must be persisted by `projectCreate` and supplied to the view keyed by
instance, not derived from block type.

### 5.8 `INSTANCES_WITH_REGAPB` read as optional

`pysrc/processYaml.py:1416` (and 2280) read the fact with `failOk=True` and
return `None` when absent, while `config/postParseRegisterPorts.py` always
persists it. Read it directly so a broken producer fails at the source.

---

## 6. Cleanups

- `pysrc/processYaml.py:3294,3299`: `(crossBind.get('thunker') or {}).get('payloads', []) or []`
  guards a state that cannot exist. A cross-interface end is only emitted when
  `buildThunkerView` returned a view, and every view carries `payloads`. Index
  directly. Identical on both parents and the merge base, so left out of the
  merge.
- `pysrc/intf_gen_utils.py`: the two literal `'Config'` spellings were replaced
  by `BLOCK_CONFIG_PARAM` in the merge; grep for any remaining literal in
  `templates/` when touching those files.
- `templates/systemc/testbench.py`: `_cm_synth_conn` sits between the import
  groups; move it below them when the file is next edited.
