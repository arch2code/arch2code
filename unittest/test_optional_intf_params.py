#!/usr/bin/env python3
"""Optional interface parameters: binding resolution and emitted spelling.

An interface parameter declared `optional: true` in interface_defs may be left
unbound by a declaring interface. `projectOpen.getIntfParamBindings()` still
returns one entry per struct parameter, in interface_defs declaration order, so
an unbound optional payload holds its own slot instead of letting a bound
payload shift left.

The language layers emit that list in the order it was declared, and apply the
emission rule:
  * a trailing run of unbound optional payloads is dropped, so an interface that
    binds nothing optional is spelled exactly as it was before the parameters
    existed (byte identity with the pre-feature generator);
  * an unbound optional payload that still precedes a bound one is a gap and is
    spelled with the C++ absence sentinel `std::monostate`;
  * SystemVerilog associates parameters by name, so it omits every unbound
    optional payload regardless of position.

Where a hand-written template splices another argument group into the payload
list - the Verilated bridge/hdlparam types in a BFM declaration, the whole child
(Down) group in a thunker declaration - the payloads are split at the boundary
between the required group and the optional tail. Optional parameters are
declared last (enforced across the shipped libraries by
test_interface_def_contracts.py), so that boundary is a prefix/suffix cut and
no declared parameter is reordered. The `tail_opt` fixture below exercises that
split with an interface of its own, bound and unbound.
"""

import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.intf_gen_utils as intf_gen_utils


# One fixture drives every check. `awNone` binds no optional payload,
# `awGap` binds only the last of axi_write's three (awuser_t, wuser_t,
# buser_t), so the first two are gaps. `awHead` binds only the first
# (awuser_t), leaving wuser_t and buser_t as a trailing unbound run for the
# payload list, but not for the BFM's bridge group, which still needs a bridge
# type per optional ahead of awuser_t's own payload slot. `streamPlain` /
# `streamUser` leave
# axi4_stream's tuser_t unbound / bound; tuser_t types the `tuser` signal, so
# the unbound case is the one that used to reach the boundary width helper with
# an empty structureKey. The last connection binds parent `awGap` to child
# `awNone`, which is a cross-interface bind whose only difference is an optional
# payload bound on one end and unbound on the other.
#
# `tail_opt` is a locally declared interface with the shape the split relies on:
# the required parameters p_a and p_b first, the optional p_opt last. Its
# optional payload types a signal, so it also contributes a Verilated bridge
# type, which is what makes the BFM's spliced argument group visible.
ARCH_YAML = """interface_defs:
  tail_opt:
    parameters:
      p_a: {datatype: struct}
      p_b: {datatype: struct}
      p_opt: {datatype: struct, optional: true}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
      sig_b: p_b
      sig_opt: p_opt
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a', 'sig_b', 'sig_opt']
      dst:
        inputs: ['valid', 'sig_a', 'sig_b', 'sig_opt']
        outputs: ['ready']
    sc_channel:
      type: 'tail_opt'
      multicycle_types: []

constants:
  ADDR_WIDTH: {value: 32, desc: "Address width"}
  DATA_WIDTH: {value: 32, desc: "Data width"}
  STRB_WIDTH: {value: 4, desc: "Write strobe width"}
  USER_WIDTH: {value: 8, desc: "User sideband width"}
  ID_WIDTH: {value: 4, desc: "Stream id width"}

types:
  addrT: {width: ADDR_WIDTH, desc: "Address"}
  dataT: {width: DATA_WIDTH, desc: "Data"}
  strbT: {width: STRB_WIDTH, desc: "Strobe"}
  userT: {width: USER_WIDTH, desc: "User sideband"}
  idT: {width: ID_WIDTH, desc: "Stream id"}

variables:
  addr: {type: addrT, desc: "Address"}
  data: {type: dataT, desc: "Data"}
  strb: {type: strbT, desc: "Strobe"}
  user: {type: userT, desc: "User sideband"}
  id: {type: idT, desc: "Stream id"}

structures:
  awAddrSt: {addr: {}}
  awDataSt: {data: {}}
  awStrbSt: {strb: {}}
  userSt: {user: {}}
  idSt: {id: {}}

interfaces:
  awNone:
    interfaceType: axi_write
    desc: "axi_write binding no optional payload"
    structures:
      - {structure: awAddrSt, structureType: addr_t}
      - {structure: awDataSt, structureType: data_t}
      - {structure: awStrbSt, structureType: strb_t}
  awGap:
    interfaceType: axi_write
    desc: "axi_write binding only the last optional payload"
    structures:
      - {structure: awAddrSt, structureType: addr_t}
      - {structure: awDataSt, structureType: data_t}
      - {structure: awStrbSt, structureType: strb_t}
      - {structure: userSt, structureType: buser_t}
  awHead:
    interfaceType: axi_write
    desc: "axi_write binding only the first optional payload"
    structures:
      - {structure: awAddrSt, structureType: addr_t}
      - {structure: awDataSt, structureType: data_t}
      - {structure: awStrbSt, structureType: strb_t}
      - {structure: userSt, structureType: awuser_t}
  streamPlain:
    interfaceType: axi4_stream
    desc: "axi4_stream leaving tuser unbound"
    structures:
      - {structure: awDataSt, structureType: tdata_t}
      - {structure: idSt, structureType: tid_t}
      - {structure: idSt, structureType: tdest_t}
  streamUser:
    interfaceType: axi4_stream
    desc: "axi4_stream binding tuser"
    structures:
      - {structure: awDataSt, structureType: tdata_t}
      - {structure: idSt, structureType: tid_t}
      - {structure: idSt, structureType: tdest_t}
      - {structure: userSt, structureType: tuser_t}
  tailBound:
    interfaceType: tail_opt
    desc: "tail_opt binding its optional tail"
    structures:
      - {structure: awAddrSt, structureType: p_a}
      - {structure: awDataSt, structureType: p_b}
      - {structure: userSt, structureType: p_opt}
  tailUnbound:
    interfaceType: tail_opt
    desc: "tail_opt leaving its optional tail unbound"
    structures:
      - {structure: awAddrSt, structureType: p_a}
      - {structure: awDataSt, structureType: p_b}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer block"}
  consumer:
    desc: "Consumer block"
    ports:
      inAwGap: {interface: awGap, direction: dst}
      inAwHead: {interface: awHead, direction: dst}
      inAwNone: {interface: awNone, direction: dst}
      inStreamPlain: {interface: streamPlain, direction: dst}
      inStreamUser: {interface: streamUser, direction: dst}
      inAwCross: {interface: awNone, direction: dst}
      inTailBound: {interface: tailBound, direction: dst}
      inTailUnbound: {interface: tailUnbound, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
  - {interface: awGap, src: uProducer, srcport: outAwGap, dst: uConsumer, dstport: inAwGap}
  - {interface: awHead, src: uProducer, srcport: outAwHead, dst: uConsumer, dstport: inAwHead}
  - {interface: awNone, src: uProducer, srcport: outAwNone, dst: uConsumer, dstport: inAwNone}
  - {interface: streamPlain, src: uProducer, srcport: outStreamPlain, dst: uConsumer, dstport: inStreamPlain}
  - {interface: streamUser, src: uProducer, srcport: outStreamUser, dst: uConsumer, dstport: inStreamUser}
  - {interface: awGap, src: uProducer, srcport: outAwCross, dst: uConsumer, dstport: inAwCross}
  - {interface: tailBound, src: uProducer, srcport: outTailBound, dst: uConsumer, dstport: inTailBound}
  - {interface: tailUnbound, src: uProducer, srcport: outTailUnbound, dst: uConsumer, dstport: inTailUnbound}
"""


PROJECT_YAML = """projectName: optional_intf_params_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {arch_name}
"""


FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def check_equal(actual, expected, message):
    check(actual == expected, f"{message}: expected {expected!r}, got {actual!r}")


def create_test_files():
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='optional_params_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(ARCH_YAML)

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='optional_params_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(PROJECT_YAML.format(arch_name=os.path.basename(arch_path)))

    return project_path, arch_path


def build_database():
    """Build the fixture database. Returns (db_path, project_path, arch_path)."""
    project_path, arch_path = create_test_files()
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to build database:\n"
                f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        return db_path, project_path, arch_path
    except Exception:
        cleanup((project_path, arch_path, db_path))
        raise


def cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def interface_row(proj, name):
    for row in proj.data['interfaces'].values():
        if row['interface'] == name:
            return row
    raise KeyError(name)


def bindings_for(proj, name):
    """The ordered payload bindings of the named interface.

    getIntfParamBindings is a pure function of the interface definition and the
    declared payload list, both of which a caller already holds.
    """
    row = interface_row(proj, name)
    return proj.getIntfParamBindings(
        proj.data['interface_defs'][row['interfaceTypeKey']], row['structures'])


def binding_tuples(bindings):
    return [(b['structureType'], b['structure'],
             bool(b['isOptional']), bool(b['isNull']))
            for b in bindings]


def template_args(decl):
    """The positional template arguments of an emitted declaration.

    An `sc_bv<N>` argument carries its own angle brackets, so mask them before
    splitting the argument list on commas.
    """
    args = decl.split('<', 1)[1].rsplit('>', 1)[0]
    return [a.strip() for a in args.replace('sc_bv<', 'sc_bv@').split(',')]


def cross_interface_end(top):
    """The single flagged cross-interface end of the fixture's connections."""
    ends = []
    for conns in top['connectDouble'].values():
        for conn in conns.values():
            ends.extend(conn.get('crossInterfaceEnds') or [])
    return ends[0] if len(ends) == 1 else None


def port_data(block_data, port_name):
    for port_group in block_data['ports'].values():
        if port_name in port_group:
            return port_group[port_name]
    raise KeyError(port_name)


def sc_mp(proj, block_data, port_name):
    return intf_gen_utils.sc_gen_modport_signal_blast(
        port_data(block_data, port_name), proj, block_data)


def sv_mp(proj, block_data, port_name):
    return intf_gen_utils.sv_gen_modport_signal_blast(
        port_data(block_data, port_name), proj, block_data)


def test_binding_list_shape(proj):
    """Resolution is full length: an unbound optional keeps its own slot."""
    print("\n[bindings] getIntfParamBindings returns every struct parameter")

    check_equal(
        binding_tuples(bindings_for(proj, 'awGap')),
        [('addr_t', 'awAddrSt', False, False),
         ('data_t', 'awDataSt', False, False),
         ('strb_t', 'awStrbSt', False, False),
         ('awuser_t', '', True, True),
         ('wuser_t', '', True, True),
         ('buser_t', 'userSt', True, False)],
        "awGap bindings keep the two unbound optionals ahead of the bound one")

    check_equal(
        binding_tuples(bindings_for(proj, 'awNone')),
        [('addr_t', 'awAddrSt', False, False),
         ('data_t', 'awDataSt', False, False),
         ('strb_t', 'awStrbSt', False, False),
         ('awuser_t', '', True, True),
         ('wuser_t', '', True, True),
         ('buser_t', '', True, True)],
        "awNone bindings still carry all three unbound optionals")

    check_equal(
        binding_tuples(bindings_for(proj, 'streamPlain')),
        [('tdata_t', 'awDataSt', False, False),
         ('tid_t', 'idSt', False, False),
         ('tdest_t', 'idSt', False, False),
         ('tuser_t', '', True, True)],
        "streamPlain bindings mark the unbound tuser_t isNull")

    # An unbound optional names no structure, so nothing downstream may index
    # prj.data['structures'] with its structureKey.
    unbound = [b for b in bindings_for(proj, 'awGap')
               if b['isNull']]
    check(all(b['structureKey'] == '' for b in unbound),
          "unbound optional bindings carry an empty structureKey")


def test_declaration_order_is_the_view_contract(proj):
    """The view returns one entry per declared parameter, in declared order."""
    print("\n[order] bindings come back in interface_defs declaration order")

    check_equal(
        binding_tuples(bindings_for(proj, 'tailBound')),
        [('p_a', 'awAddrSt', False, False),
         ('p_b', 'awDataSt', False, False),
         ('p_opt', 'userSt', True, False)],
        "tailBound bindings come back in declaration order p_a, p_b, p_opt")

    check_equal(
        binding_tuples(bindings_for(proj, 'tailUnbound')),
        [('p_a', 'awAddrSt', False, False),
         ('p_b', 'awDataSt', False, False),
         ('p_opt', '', True, True)],
        "tailUnbound keeps the unbound optional in its declared position")

    check_equal(
        [b['structureType']
         for b in bindings_for(proj, 'tailUnbound')
         if b['isNull']],
        ['p_opt'],
        "the unbound optional tail is the only isNull entry")


def test_optional_tail_split_by_consumers(proj, consumer):
    """The consumers split the payload list at the required/optional boundary.

    A channel or port emits the declared order unchanged. A BFM splices its
    whole Verilated bridge group at the boundary, which is the only reason the
    split exists; nothing is reordered on either side of it.
    """
    print("\n[split] the BFM splices its bridge group at the optional boundary")
    bound = sc_mp(proj, consumer, 'inTailBound')

    check_equal(bound['port_decl'],
                'tail_opt_in<awAddrSt, awDataSt, userSt> inTailBound;',
                "the port emits the declared payload order")
    check_equal(bound['channel_decl'],
                'tail_opt_channel<awAddrSt, awDataSt, userSt> inTailBound;',
                "the channel emits the declared payload order")
    check_equal(bound['hdl_if_decl'],
                'tail_opt_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<8>> inTailBound_hdl_if;',
                "the bridge types follow the same declared order")
    check_equal(bound['bfm_decl'],
                'tail_opt_dst_bfm<awAddrSt, awDataSt, sc_bv<32>, sc_bv<32>, '
                'sc_bv<8>, userSt> inTailBound_bfm;',
                "the BFM emits required payloads, the bridge group, then the "
                "optional tail")

    # The split is a prefix/suffix cut of the declared list: dropping the
    # spliced bridge group from the BFM leaves the channel's argument order.
    bfm_args = template_args(bound['bfm_decl'])
    check_equal([a for a in bfm_args if not a.startswith('sc_bv')],
                template_args(bound['channel_decl']),
                "the BFM payload arguments are the channel's, in the same order")

    # The unbound optional is a trailing unbound run of one, so it is dropped
    # rather than sentinel-filled, in the payloads and in the bridge group.
    unbound = sc_mp(proj, consumer, 'inTailUnbound')
    check_equal(unbound['port_decl'],
                'tail_opt_in<awAddrSt, awDataSt> inTailUnbound;',
                "an unbound optional tail is dropped from the port")
    check_equal(unbound['channel_decl'],
                'tail_opt_channel<awAddrSt, awDataSt> inTailUnbound;',
                "an unbound optional tail is dropped from the channel too")
    check_equal(unbound['bfm_decl'],
                'tail_opt_dst_bfm<awAddrSt, awDataSt, sc_bv<32>, sc_bv<32>> '
                'inTailUnbound_bfm;',
                "unbound p_opt contributes neither payload nor bridge type")
    check(intf_gen_utils.SC_NULL_PAYLOAD_TYPE not in unbound['port_decl'],
          "a trailing unbound optional needs no absence sentinel")

    # SystemVerilog associates by name, so it follows the same order and omits
    # the unbound optional entirely.
    check_equal(sv_mp(proj, consumer, 'inTailBound')['intf_decl'],
                'tail_opt_if #(.p_a(awAddrSt), .p_b(awDataSt), .p_opt(userSt)) '
                'inTailBound();',
                "named association follows declaration order")
    check_equal(sv_mp(proj, consumer, 'inTailUnbound')['intf_decl'],
                'tail_opt_if #(.p_a(awAddrSt), .p_b(awDataSt)) inTailUnbound();',
                "an unbound optional gets no named association")


def test_gap_filled_with_sentinel(proj, consumer):
    """An unbound optional before a bound one is spelled std::monostate.

    Each of axi_write's three optional payloads types an interface signal, so
    each also contributes a Verilated bridge type to the spliced group. A gap
    holds its slot in both groups: as the absence sentinel among the payloads,
    and as the one-bit placeholder among the bridge types.
    """
    print("\n[gap] unbound optional preceding a bound one fills its slot")
    sc = sc_mp(proj, consumer, 'inAwGap')

    check_equal(
        sc['port_decl'],
        'axi_write_in<awAddrSt, awDataSt, awStrbSt, std::monostate, '
        'std::monostate, userSt> inAwGap;',
        "awGap SystemC port fills awuser_t/wuser_t with the absence sentinel")
    check_equal(
        sc['channel_decl'],
        'axi_write_channel<awAddrSt, awDataSt, awStrbSt, std::monostate, '
        'std::monostate, userSt> inAwGap;',
        "awGap SystemC channel fills the same two slots")
    check_equal(
        sc['hdl_if_decl'],
        'axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>, bool, bool, '
        'sc_bv<8>> inAwGap_hdl_if;',
        "awGap bridge carries a placeholder bit per gap and buser_t's width")
    check_equal(
        sc['bfm_decl'],
        'axi_write_dst_bfm<awAddrSt, awDataSt, awStrbSt, sc_bv<32>, sc_bv<32>, '
        'sc_bv<4>, bool, bool, sc_bv<8>, std::monostate, std::monostate, '
        'userSt> inAwGap_bfm;',
        "awGap BFM fills the gaps after the Verilated bridge group")

    # Both AXI4 USER sidebands of a read interface reach the HDL boundary the
    # same way the stream's TUSER does.
    plain = sv_mp(proj, consumer, 'inAwNone')
    check('input bit inAwNone_awuser' in plain['ports'],
          "an unbound awuser_t blasts to a single-bit placeholder port")
    check('output bit inAwNone_buser' in plain['ports'],
          "an unbound buser_t blasts to a single-bit placeholder port on the "
          "response channel, which travels the other way")
    user = sv_mp(proj, consumer, 'inAwGap')
    check('output bit [7:0] inAwGap_buser' in user['ports'],
          "a bound buser_t blasts to its structure width")


def test_trailing_optional_omitted(proj, consumer):
    """A trailing run of unbound optionals is dropped, not sentinel-filled.

    These are the exact argument lists the generator produced before axi_write
    gained its three optional user payloads.
    """
    print("\n[trailing] unbound trailing optionals are omitted entirely")
    sc = sc_mp(proj, consumer, 'inAwNone')

    check_equal(sc['port_decl'],
                'axi_write_in<awAddrSt, awDataSt, awStrbSt> inAwNone;',
                "awNone SystemC port is spelled as it was pre-feature")
    check_equal(sc['channel_decl'],
                'axi_write_channel<awAddrSt, awDataSt, awStrbSt> inAwNone;',
                "awNone SystemC channel is spelled as it was pre-feature")
    check_equal(sc['bfm_decl'],
                'axi_write_dst_bfm<awAddrSt, awDataSt, awStrbSt, sc_bv<32>, '
                'sc_bv<32>, sc_bv<4>> inAwNone_bfm;',
                "awNone BFM is spelled as it was pre-feature")
    check(intf_gen_utils.SC_NULL_PAYLOAD_TYPE not in sc['port_decl'],
          "no absence sentinel appears when every unbound optional is trailing")

    stream = sc_mp(proj, consumer, 'inStreamPlain')
    check_equal(stream['port_decl'],
                'axi4_stream_in<awDataSt, idSt, idSt> inStreamPlain;',
                "streamPlain SystemC port omits the trailing tuser_t")
    check_equal(stream['hdl_if_decl'],
                'axi4_stream_hdl_if<sc_bv<32>, sc_bv<4>, sc_bv<4>, sc_bv<4>, '
                'sc_bv<4>> inStreamPlain_hdl_if;',
                "streamPlain bridge omits the trailing tuser_t bridge type")


def test_head_bound_keeps_bfm_bridge_group_whole(proj, consumer):
    """Binding only the FIRST optional payload still fills the whole bridge group.

    awHead binds awuser_t and leaves wuser_t/buser_t unbound, so the trimmed
    payload tail is just awuser_t: the SystemC port/channel are spelled exactly
    as awNone's trailing-trim rule would spell them, one payload longer. The
    BFM is different: trimming the bridge group the same way would leave it one
    argument short, which would shift awuser_t's own VL_ bridge slot onto
    wuser_t's, so the BFM must carry a bridge type for every optional, bound or
    not, ahead of the payload.
    """
    print("\n[head] binding only the first optional keeps the bridge group whole")
    sc = sc_mp(proj, consumer, 'inAwHead')

    check_equal(sc['port_decl'],
                'axi_write_in<awAddrSt, awDataSt, awStrbSt, userSt> inAwHead;',
                "awHead SystemC port keeps the trailing trim, one payload longer")
    check_equal(sc['channel_decl'],
                'axi_write_channel<awAddrSt, awDataSt, awStrbSt, userSt> '
                'inAwHead;',
                "awHead SystemC channel keeps the same trailing trim")
    check_equal(sc['bfm_decl'],
                'axi_write_dst_bfm<awAddrSt, awDataSt, awStrbSt, sc_bv<32>, '
                'sc_bv<32>, sc_bv<4>, sc_bv<8>, bool, bool, userSt> '
                'inAwHead_bfm;',
                "awHead BFM carries the complete bridge group before the "
                "payload, placeholders and all")


def test_unbound_optional_signal_blast(proj, consumer):
    """A signal typed by an unbound optional never reaches the width helper.

    axi4_stream's `tuser` signal is typed by the optional `tuser_t`. When that
    parameter is unbound the binding names no structure, so the boundary blast
    must spell the signal as the one-bit placeholder rather than looking a
    structure up by an empty structureKey.
    """
    print("\n[structureKey] signal typed by an unbound optional stays one bit")
    try:
        plain = sv_mp(proj, consumer, 'inStreamPlain')
    except KeyError as exc:
        # A structure lookup on the unbound payload's empty structureKey.
        check(False, "unbound tuser_t must not be looked up as a structure "
                     f"(KeyError {exc})")
        return
    user = sv_mp(proj, consumer, 'inStreamUser')

    check('input bit inStreamPlain_tuser' in plain['ports'],
          "unbound tuser_t blasts to a single-bit placeholder port")
    check('input bit [7:0] inStreamUser_tuser' in user['ports'],
          "bound tuser_t blasts to its structure width")

    # The SystemC bridge takes the same decision for the same signal.
    check_equal(sc_mp(proj, consumer, 'inStreamUser')['hdl_if_decl'],
                'axi4_stream_hdl_if<sc_bv<32>, sc_bv<4>, sc_bv<4>, sc_bv<4>, '
                'sc_bv<4>, sc_bv<8>> inStreamUser_hdl_if;',
                "bound tuser_t contributes its width to the Verilated bridge")


def test_optional_tail_after_hdlparam_group(proj, consumer):
    """The BFM splices the whole Verilated group at the optional boundary.

    axi4_stream declares two hdlparams (tstrb_t, tkeep_t) that contribute
    positional bridge arguments of their own, so the spliced group is wider than
    the payloads it is derived from and the boundary is unambiguous.
    """
    print("\n[split] optional payloads follow the hdlparam group in a BFM")
    sc = sc_mp(proj, consumer, 'inStreamUser')

    check_equal(
        sc['bfm_decl'],
        'axi4_stream_dst_bfm<awDataSt, idSt, idSt, sc_bv<32>, sc_bv<4>, '
        'sc_bv<4>, sc_bv<4>, sc_bv<4>, sc_bv<8>, userSt> inStreamUser_bfm;',
        "streamUser BFM emits userSt after both hdlparam bridge types")

    args = template_args(sc['bfm_decl'])
    check_equal(args[-1], 'userSt',
                "the optional payload is the last BFM template argument")
    check_equal(args[:3], ['awDataSt', 'idSt', 'idSt'],
                "the required payloads remain the leading BFM arguments")


def test_thunker_split_and_gap(proj, top):
    """A thunker emits up-required, down-required, up-optional, down-optional.

    The cross-interface bind pairs parent `awGap` with child `awNone`. The view
    hands each side its own full-length binding list in declaration order; the
    SystemC layer splits both at their optional boundary and splices them into
    the order the hand-written template declares, then drops only the trailing
    unbound run, so the parent's bound buser_t keeps its slot behind two
    sentinels while the child's three unbound optionals fall off the end.
    """
    print("\n[thunker] each side is split at its own optional boundary")
    flagged = cross_interface_end(top)
    if flagged is None:
        check(False, "exactly one cross-interface bind is flagged on the fixture")
        return

    # The view keeps both sides full length and in declared order; the emitted
    # spelling below is what proves the split and the interleave.
    payloads = [(p['side'], p['structureType'], p['isOptional'], p['isNull'])
                for p in flagged['thunker']['payloads']]
    check_equal(
        payloads,
        [('parent', 'addr_t', False, False), ('parent', 'data_t', False, False),
         ('parent', 'strb_t', False, False), ('parent', 'awuser_t', True, True),
         ('parent', 'wuser_t', True, True), ('parent', 'buser_t', True, False),
         ('child', 'addr_t', False, False), ('child', 'data_t', False, False),
         ('child', 'strb_t', False, False), ('child', 'awuser_t', True, True),
         ('child', 'wuser_t', True, True), ('child', 'buser_t', True, True)],
        "thunker view carries each side's full binding list in declared order")

    decls = intf_gen_utils.sc_declare_thunkers(top, proj, '', top)
    check_equal(
        decls,
        ['axi_write_port_thunker<awAddrSt, awDataSt, awStrbSt, awAddrSt, '
         'awDataSt, awStrbSt, std::monostate, std::monostate, userSt> '
         'thunker_outAwCross_uConsumer;'],
        "the emitted thunker is up-required, down-required, up-optional, with "
        "the child's trailing unbound run dropped")

    # The interleave is a prefix/suffix cut of each side's declared list: the
    # emitted arguments are the parent's required group, then the child's, then
    # the parent's optional group. Reading the groups back off the declaration
    # keeps this coupled to the spelling the C++ template requires.
    args = template_args(decls[0])
    check_equal(args[:3], ['awAddrSt', 'awDataSt', 'awStrbSt'],
                "the up-side required payloads lead the thunker arguments")
    check_equal(args[3:6], ['awAddrSt', 'awDataSt', 'awStrbSt'],
                "the down-side required payloads follow, before any optional")
    check_equal(args[6:], ['std::monostate', 'std::monostate', 'userSt'],
                "the up-side optional group follows both required groups, with "
                "its gaps sentinel-filled")


def test_sv_omits_unbound_by_name(proj, consumer):
    """SystemVerilog associates by name, so it omits every unbound optional."""
    print("\n[sv] unbound optionals produce no named parameter association")

    check_equal(
        sv_mp(proj, consumer, 'inAwGap')['intf_decl'],
        'axi_write_if #(.addr_t(awAddrSt), .data_t(awDataSt), '
        '.strb_t(awStrbSt), .buser_t(userSt)) inAwGap();',
        "awGap omits .awuser_t/.wuser_t even though buser_t follows them")
    check_equal(
        sv_mp(proj, consumer, 'inAwNone')['intf_decl'],
        'axi_write_if #(.addr_t(awAddrSt), .data_t(awDataSt), '
        '.strb_t(awStrbSt)) inAwNone();',
        "awNone omits all three optional associations")
    check_equal(
        sv_mp(proj, consumer, 'inStreamUser')['intf_decl'],
        'axi4_stream_if #(.tdata_t(awDataSt), .tid_t(idSt), .tdest_t(idSt), '
        '.tuser_t(userSt)) inStreamUser();',
        "a bound optional is associated by name")
    check(
        '.tuser_t(' not in sv_mp(proj, consumer, 'inStreamPlain')['intf_decl'],
        "an unbound optional produces no .tuser_t association")


def main():
    print("=" * 72)
    print("TESTING OPTIONAL INTERFACE PARAMETERS")
    print("=" * 72)
    try:
        db_path, project_path, arch_path = build_database()
    except RuntimeError as exc:
        print(f"  FAIL: fixture project must build: {exc}")
        return 1
    try:
        proj = projectOpen(db_path)
        consumer = proj.getBlockData(proj.getQualBlock('consumer'))
        top = proj.getBlockData(proj.getQualBlock('top'))

        test_binding_list_shape(proj)
        test_declaration_order_is_the_view_contract(proj)
        test_optional_tail_split_by_consumers(proj, consumer)
        test_gap_filled_with_sentinel(proj, consumer)
        test_trailing_optional_omitted(proj, consumer)
        test_head_bound_keeps_bfm_bridge_group_whole(proj, consumer)
        test_unbound_optional_signal_blast(proj, consumer)
        test_optional_tail_after_hdlparam_group(proj, consumer)
        test_thunker_split_and_gap(proj, top)
        test_sv_omits_unbound_by_name(proj, consumer)
    finally:
        cleanup((db_path, project_path, arch_path))

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all optional interface parameter checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
