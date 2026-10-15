#!/usr/bin/env python3
"""Interface timing intent: backpressure overrides and the channels they reach.

projectCreate rejects a backpressure: override the interface definition does
not allow. The block view resolves each channel's effectiveBackpressure from
the definition's timing and every port the channel joins, and the generated
constructors pass it to each channel and thunker whose definition lets a
design override it."""

import os
import shutil
import subprocess
import sys
import tempfile
import types


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from templates.systemc import baseClassDecl, constructor, testbench


# consumer declares its ports, so each can carry a backpressure: override.
# A: the dst port lowers a default stream. B: the dst port raises an interface
# that is lowered, and the producer's port still inherits false. C: no
# override. D: both declared ports raise a lowered interface. S: fixed timing.
# P: an ack protocol, which nothing may lower. E and T join two blocks that
# stay in a testbench External when uConsumer is the excluded DUT.
ARCH_YAML = """types:
  data_t: {width: 8, desc: "Data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  stream:
    interfaceType: rdy_vld
    desc: "Default stream"
    structures:
      - {structure: data_st, structureType: data_t}
  lowStream:
    interfaceType: rdy_vld
    desc: "Valid-only stream"
    backpressure: false
    structures:
      - {structure: data_st, structureType: data_t}
  stat:
    interfaceType: status
    desc: "Status"
    structures:
      - {structure: data_st, structureType: data_t}
  ctrl:
    interfaceType: push_ack
    desc: "Control"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer"}
  consumer:
    desc: "Consumer"
    ports:
      inA: {interface: stream, direction: dst, backpressure: false}
      inB: {interface: lowStream, direction: dst, backpressure: true}
      inC: {interface: stream, direction: dst}
      inS: {interface: stat, direction: dst}
      inP: {interface: ctrl, direction: dst}
  hiProducer:
    desc: "Producer that honors rdy"
    ports:
      out: {interface: lowStream, direction: src, backpressure: true}
  hiConsumer:
    desc: "Consumer that honors rdy"
    ports:
      in: {interface: lowStream, direction: dst, backpressure: true}
  sink: {desc: "Sink with inferred ports"}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}
  uHiProducer: {container: top, instanceType: hiProducer}
  uHiConsumer: {container: top, instanceType: hiConsumer}
  uSink: {container: top, instanceType: sink}

connections:
  - {interface: stream, src: uProducer, srcport: outA, dst: uConsumer, dstport: inA, interfaceName: chA}
  - {interface: lowStream, src: uProducer, srcport: outB, dst: uConsumer, dstport: inB, interfaceName: chB}
  - {interface: stream, src: uProducer, srcport: outC, dst: uConsumer, dstport: inC, interfaceName: chC}
  - {interface: stat, src: uProducer, srcport: outS, dst: uConsumer, dstport: inS, interfaceName: chS}
  - {interface: ctrl, src: uProducer, srcport: outP, dst: uConsumer, dstport: inP, interfaceName: chP}
  - {interface: lowStream, src: uHiProducer, srcport: out, dst: uHiConsumer, dstport: in, interfaceName: chD}
  - {interface: lowStream, src: uProducer, srcport: outE, dst: uSink, dstport: inE, interfaceName: chE}
  - {interface: stat, src: uProducer, srcport: outT, dst: uSink, dstport: inT, interfaceName: chT}
"""

# A project-local protocol whose default is no backpressure, for the rule that
# an override may never raise a value above the protocol default.
QUIET_DEF_YAML = """interface_defs:
  quiet:
    timing: elastic
    backpressure: { default: false, overridable: true }
    parameters:
      data_t: { datatype: struct }
    signals:
      vld: bool
      data: data_t
    modports:
      src:
        inputs: []
        outputs: ['vld', 'data']
      dst:
        inputs: ['vld', 'data']
        outputs: []
    sc_channel:
      type: 'quiet'
      multicycle_types: []

"""

# A cross-interface bind: the consumer's port is typed by childIf, so a thunker
# owns the channel to it. parentIf has backpressure off, so both the container
# channel and the thunker's channel take BACKPRESSURE_NONE.
THUNKER_ARCH_YAML = """types:
  data_t: {width: 8, desc: "Data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  parentIf:
    interfaceType: rdy_vld
    desc: "Parent interface"
    backpressure: false
    structures:
      - {structure: data_st, structureType: data_t}
  childIf:
    interfaceType: rdy_vld
    desc: "Child interface"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer"}
  consumer:
    desc: "Consumer"
    ports:
      inData: {interface: childIf, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
  - {interface: parentIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData, interfaceName: chX}
"""

# leaf turns backpressure off on its own port. inner and outer only map that
# port up, so the one channel carrying the traffic is chW in top, which joins
# outer's port. A cross-interface map in mapper puts a thunker on the leaf's
# channel inside mapper.
HIER_ARCH_YAML = """types:
  data_t: {width: 8, desc: "Data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  stream:
    interfaceType: rdy_vld
    desc: "Default stream"
    structures:
      - {structure: data_st, structureType: data_t}
  childIf:
    interfaceType: rdy_vld
    desc: "Child interface"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer"}
  outer: {desc: "Outer container"}
  inner: {desc: "Inner container"}
  mapper: {desc: "Container with a cross-interface map"}
  leaf:
    desc: "Leaf that never lowers rdy"
    ports:
      in: {interface: stream, direction: dst, backpressure: false}
  childLeaf:
    desc: "Leaf typed by childIf that never lowers rdy"
    ports:
      in: {interface: childIf, direction: dst, backpressure: false}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uOuter: {container: top, instanceType: outer}
  uInner: {container: outer, instanceType: inner}
  uLeaf: {container: inner, instanceType: leaf}
  uMapper: {container: top, instanceType: mapper}
  uChildLeaf: {container: mapper, instanceType: childLeaf}

connections:
  - {interface: stream, src: uProducer, srcport: outW, dst: uOuter, dstport: in, interfaceName: chW}
  - {interface: stream, src: uProducer, srcport: outX, dst: uMapper, dstport: in, interfaceName: chX}

connectionMaps:
  - {interface: stream, block: outer, port: in, direction: dst, instance: uInner, instancePort: in}
  - {interface: stream, block: inner, port: in, direction: dst, instance: uLeaf, instancePort: in}
  - {interface: stream, block: mapper, port: in, direction: dst, instance: uChildLeaf, instancePort: in}
"""

# The producer's port is typed by childIf, so a testbench External that
# excludes uConsumer adapts it with a thunker. Only the excluded consumer's
# port turns backpressure off.
DUT_PORT_ARCH_YAML = THUNKER_ARCH_YAML.replace(
    '    desc: "Parent interface"\n    backpressure: false\n',
    '    desc: "Parent interface"\n').replace(
    '  producer: {desc: "Producer"}\n',
    '  producer:\n    desc: "Producer"\n    ports:\n'
    '      outData: {interface: childIf, direction: src}\n').replace(
    'inData: {interface: childIf, direction: dst}',
    'inData: {interface: parentIf, direction: dst, backpressure: false}')

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def build(archText):
    """Run projectCreate on archText. Returns (result, dbPath, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix='timing_intent_')
    with open(os.path.join(tmpdir, 'arch.yaml'), 'w') as f:
        f.write(archText)
    projectPath = os.path.join(tmpdir, 'project.yaml')
    with open(projectPath, 'w') as f:
        f.write("projectName: timing_intent\nyamlFormat: 2\ntopInstance: uTop\n\n"
                "dirs:\n  root: .\n\nprojectFiles:\n  - arch.yaml\n")
    dbPath = os.path.join(tmpdir, 'timing_intent.db')
    env = dict(os.environ, NO_COLOR='1')
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', projectPath, '--db', dbPath],
        capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
    return result, dbPath, tmpdir


def blockData(proj, block):
    blockKey = next(key for key, row in proj.data['blocks'].items() if row['block'] == block)
    return proj.getBlockData(blockKey)


def initLines(proj, data):
    """The container constructor's initializer entries that build a channel or a thunker."""
    init = constructor.render(types.SimpleNamespace(section='init', mode='module'), proj, data)
    return [line.strip() for line in init.splitlines() if line.strip().startswith(',ch') or 'thunker_' in line]


def externalInitLines(proj, block, excluded):
    blockKey = next(key for key, row in proj.data['blocks'].items() if row['block'] == block)
    external = proj.getBlockData(blockKey, trimRegLeafInstance=True, excludeInstances={excluded})
    testbench.refactor_tbExternal(None, proj, external)
    init = testbench.ext_sec_init(types.SimpleNamespace(variant=None), proj, external)
    return external, [line.strip() for line in init.splitlines() if line.strip().startswith(',ch') or 'thunker_' in line]


def test_effective_backpressure_and_generated_arguments():
    print("\n[view] each channel's effectiveBackpressure follows timing and every endpoint")
    result, dbPath, tmpdir = build(ARCH_YAML)
    try:
        check(result.returncode == 0, f"the fixture builds a database\n{result.stdout}{result.stderr}")
        if result.returncode != 0:
            return
        proj = projectOpen(dbPath)
        top = blockData(proj, 'top')
        values = {row['interfaceName']: row['effectiveBackpressure']
                  for group in top['connectDouble'].values() for row in group.values()}
        expected = {'chA': False, 'chB': False, 'chC': True, 'chS': False, 'chP': True,
                    'chD': True, 'chE': False, 'chT': False}
        for channel, value in expected.items():
            check(values[channel] == value,
                  f"{channel} effectiveBackpressure is {value} (got {values[channel]})")

        consumer = blockData(proj, 'consumer')
        portValues = {name: row['effectiveBackpressure']
                      for group in consumer['ports'].values() for name, row in group.items()}
        expectedPorts = {'inA': False, 'inB': True, 'inC': True, 'inS': False, 'inP': True}
        for port, value in expectedPorts.items():
            check(portValues[port] == value,
                  f"consumer port {port} effectiveBackpressure is {value} (got {portValues[port]})")

        print("\n[generated] only an overridable protocol's channel takes the backpressure argument")
        lines = initLines(proj, top)
        check(lines == [',chA("consumer_chA", "producer", BACKPRESSURE_NONE)',
                        ',chB("consumer_chB", "producer", BACKPRESSURE_NONE)',
                        ',chC("consumer_chC", "producer", BACKPRESSURE_ALLOWED)',
                        ',chS("consumer_chS", "producer")',
                        ',chP("consumer_chP", "producer")',
                        ',chD("hiConsumer_chD", "hiProducer", BACKPRESSURE_ALLOWED)',
                        ',chE("sink_chE", "producer", BACKPRESSURE_NONE)',
                        ',chT("sink_chT", "producer")'],
              f"top builds rdy_vld channels with their value and status and push_ack without one (got {lines})")
        body = constructor.render(types.SimpleNamespace(section='body', mode='module'), proj, top)
        check('ignoreSetTimed' not in body and 'setTimed' not in body,
              "the constructor body says nothing about setTimed")

        print("\n[generated] a testbench External builds the peer channels it keeps the same way")
        _, lines = externalInitLines(proj, 'top', 'uConsumer')
        check(lines == [',chD("chD", "uHiProducer", BACKPRESSURE_ALLOWED)',
                        ',chE("chE", "uProducer", BACKPRESSURE_NONE)',
                        ',chT("chT", "uProducer")'],
              f"the External without uConsumer builds chD, chE and chT (got {lines})")

        print("\n[generated] <block>Channels passes each port's value")
        decl = baseClassDecl.render(types.SimpleNamespace(mode='module', noExternalComments=True),
                                    proj, consumer)
        channels = decl[decl.index('class consumerChannels'):]
        lines = [line.strip().lstrip(',') for line in channels.splitlines() if '+name).c_str()' in line]
        check(lines == ['inA(("inA"+name).c_str(), srcName, BACKPRESSURE_NONE)',
                        'inB(("inB"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)',
                        'inC(("inC"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)',
                        'inS(("inS"+name).c_str(), srcName)',
                        'inP(("inP"+name).c_str(), srcName)'],
              f"consumerChannels passes the value to inA, inB and inC only (got {lines})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_thunker_takes_connection_value():
    print("\n[generated] a peer thunker's owned channel takes its connection's value")
    result, dbPath, tmpdir = build(THUNKER_ARCH_YAML)
    try:
        check(result.returncode == 0, f"the fixture builds a database\n{result.stdout}{result.stderr}")
        if result.returncode != 0:
            return
        proj = projectOpen(dbPath)
        lines = initLines(proj, blockData(proj, 'top'))
        check(lines == [',chX("consumer_chX", "producer", BACKPRESSURE_NONE)',
                        ',thunker_chX_uConsumer("thunker_chX_uConsumer", chX, uConsumer->inData, name(), BACKPRESSURE_NONE)'],
              f"top builds chX and the thunker that owns the consumer's channel with BACKPRESSURE_NONE (got {lines})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_container_port_follows_child():
    print("\n[view] a container port counts the child port its connectionMap binds, at any depth")
    result, dbPath, tmpdir = build(HIER_ARCH_YAML)
    try:
        check(result.returncode == 0, f"the fixture builds a database\n{result.stdout}{result.stderr}")
        if result.returncode != 0:
            return
        proj = projectOpen(dbPath)
        top = blockData(proj, 'top')
        values = {row['interfaceName']: row['effectiveBackpressure']
                  for group in top['connectDouble'].values() for row in group.values()}
        check(values['chW'] is False,
              f"chW into outer takes the leaf's value from two levels down (got {values['chW']})")
        check(values['chX'] is False,
              f"chX into mapper takes its cross-interface child's value (got {values['chX']})")

        print("\n[generated] a connectionMap thunker's owned channel takes the map's value")
        lines = initLines(proj, blockData(proj, 'mapper'))
        check(lines == [',thunker_uChildLeaf("thunker_uChildLeaf", in, uChildLeaf->in, name(), BACKPRESSURE_NONE)'],
              f"mapper builds the thunker that owns the child's channel with BACKPRESSURE_NONE (got {lines})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_pruned_thunker_counts_dut_end():
    print("\n[generated] an External's DUT-boundary thunker counts the excluded DUT port")
    result, dbPath, tmpdir = build(DUT_PORT_ARCH_YAML)
    try:
        check(result.returncode == 0, f"the fixture builds a database\n{result.stdout}{result.stderr}")
        if result.returncode != 0:
            return
        proj = projectOpen(dbPath)
        external, lines = externalInitLines(proj, 'top', 'uConsumer')
        value = next(iter(external['prunedConnections'].values()))['effectiveBackpressure']
        check(value is False, f"the pruned chX row takes uConsumer's port value (got {value})")
        check(lines == [',thunker_chX_uProducer("thunker_chX_uProducer", inData, uProducer->outData, name(), BACKPRESSURE_NONE)'],
              f"the External builds its DUT-boundary thunker with BACKPRESSURE_NONE (got {lines})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def expect_rejected(title, archText, fragments):
    print(f"\n[reject] {title}")
    result, dbPath, tmpdir = build(archText)
    try:
        output = result.stdout + result.stderr
        check(result.returncode != 0, "projectCreate fails")
        for fragment in fragments:
            check(fragment in output, f"the error says {fragment!r}")
        if result.returncode == 0 or not all(fragment in output for fragment in fragments):
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_rejections():
    expect_rejected(
        "backpressure on a fixed-timing interface entry",
        ARCH_YAML.replace('    interfaceType: status\n',
                          '    interfaceType: status\n    backpressure: false\n'),
        ["interface 'stat' sets backpressure: false", "has timing: fixed"])
    expect_rejected(
        "backpressure on a port of a fixed-timing interface",
        ARCH_YAML.replace('inS: {interface: stat, direction: dst}',
                          'inS: {interface: stat, direction: dst, backpressure: false}'),
        ["block 'consumer' port 'inS' sets backpressure: false", "has timing: fixed"])
    expect_rejected(
        "backpressure on an interface entry whose protocol is not overridable",
        ARCH_YAML.replace('    interfaceType: push_ack\n',
                          '    interfaceType: push_ack\n    backpressure: false\n'),
        ["interface 'ctrl' sets backpressure: false", "overridable: false"])
    expect_rejected(
        "backpressure on a port whose protocol is not overridable",
        ARCH_YAML.replace('inP: {interface: ctrl, direction: dst}',
                          'inP: {interface: ctrl, direction: dst, backpressure: true}'),
        ["block 'consumer' port 'inP' sets backpressure: true", "overridable: false"])
    expect_rejected(
        "backpressure: true above a protocol default of false",
        QUIET_DEF_YAML + ARCH_YAML.replace(
            'interfaces:\n',
            'interfaces:\n  quietIf:\n    interfaceType: quiet\n    desc: "Quiet"\n'
            '    backpressure: true\n    structures:\n'
            '      - {structure: data_st, structureType: data_t}\n', 1),
        ["interface 'quietIf' sets backpressure: true", "defaults to backpressure: false"])
    expect_rejected(
        "a backpressure value that is not a bool",
        ARCH_YAML.replace('    backpressure: false\n', '    backpressure: maybe\n', 1),
        ["field backpressure", "not in the allowed values"])


def main():
    print("=" * 72)
    print("TESTING INTERFACE TIMING INTENT")
    print("=" * 72)
    test_effective_backpressure_and_generated_arguments()
    test_thunker_takes_connection_value()
    test_container_port_follows_child()
    test_pruned_thunker_counts_dut_end()
    test_rejections()
    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all interface timing intent checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
