#!/usr/bin/env python3
"""Tests for interface_def-driven cross-interface thunker views."""

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


BASE_YAML = """constants:
  WIDTH: {value: 8, desc: "Data width"}

types:
  data_t: {width: WIDTH, desc: "Data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
__INTERFACES__

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer block"}
  consumer:
    desc: "Consumer block"
    ports:
      inData: {interface: __CHILD_INTERFACE__, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
  - {interface: __PARENT_INTERFACE__, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}
"""


def create_test_files(arch_content):
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='thunker_view_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    project_content = f"""projectName: thunker_view_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='thunker_view_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)

    return project_path, arch_path


def build_database(arch_content, expect_success=True):
    project_path, arch_path = create_test_files(arch_content)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', project_path, '--db', db_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=base_dir,
            env=env,
        )
        if result.returncode != 0:
            if not expect_success:
                return db_path, project_path, arch_path, result
            raise RuntimeError(
                f"Failed to build database:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        if not expect_success:
            raise RuntimeError(
                f"Database build succeeded unexpectedly:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        return db_path, project_path, arch_path
    except Exception:
        for path in (project_path, arch_path, db_path):
            if path and os.path.exists(path):
                os.unlink(path)
        raise


def cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def get_top_block_data(db_path):
    proj = projectOpen(db_path)
    top_block = next(
        key for key, value in proj.data['blocks'].items()
        if value.get('block') == 'top')
    return proj.getBlockData(top_block)


def first_thunker(block_data):
    conn = next(iter(block_data['connectDouble']['connections'].values()))
    return conn['crossInterfaceEnds'][0]['thunker']


def render_interfaces(interface_type, parent_name, child_name):
    if interface_type == 'req_ack':
        structures = """    structures:
      - {structure: data_st, structureType: data_t}
      - {structure: data_st, structureType: rdata_t}"""
    elif interface_type in ('apb', 'axi_read'):
        structures = """    structures:
      - {structure: data_st, structureType: addr_t}
      - {structure: data_st, structureType: data_t}"""
    elif interface_type == 'notify_ack':
        structures = ""
    else:
        structures = """    structures:
      - {structure: data_st, structureType: data_t}"""

    return f"""  {parent_name}:
    interfaceType: {interface_type}
    desc: "Parent interface"
{structures}
  {child_name}:
    interfaceType: {interface_type}
    desc: "Child interface"
{structures}"""


def build_arch(interface_type, parent_name='parentIf', child_name='childIf'):
    return (
        BASE_YAML
        .replace('__INTERFACES__', render_interfaces(interface_type, parent_name, child_name))
        .replace('__PARENT_INTERFACE__', parent_name)
        .replace('__CHILD_INTERFACE__', child_name)
    )


def test_parameter_order(interface_type, expected_types):
    print(f"\nTesting parameter-derived thunker payload order for {interface_type}")
    db_path, project_path, arch_path = build_database(build_arch(interface_type))
    try:
        thunker = first_thunker(get_top_block_data(db_path))
        actual_types = [payload['structureType'] for payload in thunker['payloads']]
        if actual_types != expected_types:
            print(f"FAIL: expected {expected_types}, got {actual_types}")
            return False
        expected_channel = interface_type
        if thunker.get('channelType') != expected_channel:
            print(f"FAIL: expected channelType {expected_channel}, got {thunker.get('channelType')}")
            return False
        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


def test_no_struct_parameter_not_thunked():
    print("\nTesting no-struct protocol does not create a thunker")
    # Protocols with no struct parameters have no parameterized payload to
    # bridge. They should not take the thunker path at all; ordinary
    # same-protocol binding semantics decide whether the connection is valid.
    db_path, project_path, arch_path = build_database(
        build_arch('notify_ack', 'parentNotifyIf', 'childNotifyIf'))
    try:
        block_data = get_top_block_data(db_path)
        conn = next(iter(block_data['connectDouble']['connections'].values()))
        if conn.get('crossInterfaceEnds'):
            print("FAIL: no-struct protocol unexpectedly produced a thunker")
            print(conn['crossInterfaceEnds'])
            return False
        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


BINDS_DIRECTLY_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 16, desc: "Data width"}
  types:
    data_t: {width: WIDTH, desc: "Data type"}

structures:
  data_st:
    data: {varType: data_t, desc: "Data payload"}

interfaces:
  dataIf:
    interfaceType: rdy_vld
    desc: "Data stream"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block", hasRtl: false}
  producer:
    desc: "Producer block"
    params: [WIDTH]
    hasRtl: false
    ports:
      outData: {interface: dataIf, direction: src}
  consumer:
    desc: "Consumer block"
    params: [WIDTH]
    hasRtl: false
    ports:
      inData: {interface: dataIf, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer, variant: prodVar}
  uConsumer: {container: top, instanceType: consumer, variant: consVar}

connections:
  - {interface: dataIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}

parameters:
  producer:
    prodVar:
      WIDTH: 8
  consumer:
    consVar:
      WIDTH: 8
"""


def test_binds_directly_reflects_param_values():
    print("\nTesting bindsDirectly compares resolved root-parameter values")
    # producer and consumer each carry their own Config for the same
    # interface. Equal WIDTH values make the two Configs one payload type;
    # a value that no longer agrees stops the two sides binding directly.
    db_path, project_path, arch_path = build_database(BINDS_DIRECTLY_YAML)
    try:
        prj = projectOpen(db_path)
        interfaceRow = next(
            value for value in prj.data['interfaces'].values()
            if value['interface'] == 'dataIf')
        producerInst = next(
            value for value in prj.data['instances'].values()
            if value['instance'] == 'uProducer')
        consumerInst = next(
            value for value in prj.data['instances'].values()
            if value['instance'] == 'uConsumer')
        parentSelection = prj._resolveInstanceConfigFields(producerInst)
        childSelection = prj._resolveInstanceConfigFields(consumerInst)

        if not prj.bindsDirectly(interfaceRow, interfaceRow['interfaceKey'],
                                  parentSelection, childSelection):
            print("FAIL: equal-value ends should bind directly")
            return False

        disagreeing = dict(childSelection)
        disagreeing['descriptor'] = dict(childSelection['descriptor'])
        disagreeing['descriptor']['values'] = dict(childSelection['descriptor']['values'])
        disagreeing['descriptor']['values']['WIDTH'] = 16
        if prj.bindsDirectly(interfaceRow, interfaceRow['interfaceKey'],
                              parentSelection, disagreeing):
            print("FAIL: disagreeing values should not bind directly")
            return False

        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


CONNMAP_MISSING_PARAM_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 16, desc: "Data width"}
    OTHER_W: {value: 4, maxValue: 8, desc: "Unrelated width"}
  types:
    data_t: {width: WIDTH, desc: "Data type"}

structures:
  data_st: {data: {varType: data_t, desc: "Data payload"}}

interfaces:
  dataIf: {interfaceType: rdy_vld, desc: "Data stream", structures: [{structure: data_st, structureType: data_t}]}

blocks:
  top: {desc: "Top block", hasRtl: false}
  mid: {desc: "Boundary port undeclared, top-down inferred", params: [WIDTH], hasRtl: false}
  leaf: {desc: "Declares an unrelated param, still missing WIDTH", params: [OTHER_W], hasRtl: false}

instances:
  uTop: {container: top, instanceType: top}
  uMid: {container: top, instanceType: mid, variant: midVar}
  uLeaf: {container: mid, instanceType: leaf, variant: leafVar}

connectionMaps:
  - {interface: dataIf, block: mid, port: inData, direction: dst, instance: uLeaf, instancePort: inData}

parameters:
  mid: {midVar: {WIDTH: 8}}
  leaf: {leafVar: {OTHER_W: 4}}
"""


def test_connectionmap_child_missing_param_rejected():
    print("\nTesting connectionMap child whose block lacks a required parameter")
    # mid's own boundary Config needs WIDTH, but leaf declares no params: at
    # all, so it cannot supply the payload's backing parameter in its own
    # module scope.
    db_path, project_path, arch_path, result = build_database(
        CONNMAP_MISSING_PARAM_YAML, expect_success=False)
    try:
        if 'does not declare the required parameter' not in result.stdout:
            print(f"FAIL: expected the missing-parameter diagnostic, got:\n{result.stdout}")
            return False
        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


TYPE_PAYLOAD_INTERFACE_DEF = """interface_defs:
  ty_proto:
    parameters:
      p_ty: {datatype: type}
    signals:
      valid: bool
      ready: bool
      sig_ty: p_ty
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_ty']
      dst:
        inputs: ['valid', 'sig_ty']
        outputs: ['ready']
    sc_channel:
      type: 'ty_proto'
      multicycle_types: []

"""

TYPE_PAYLOAD_BODY = """interfaces:
  parentIf: {interfaceType: ty_proto, desc: "Parent interface", structures: [{structure: data_t, structureType: p_ty}]}
  childIf: {interfaceType: ty_proto, desc: "Child interface", structures: [{structure: data_t, structureType: p_ty}]}

blocks:
  top: {desc: "Top block", hasRtl: false}
  producer:
    desc: "Producer block"
    hasRtl: false
__PRODUCER_PARAMS__
    ports:
      outData: {interface: parentIf, direction: src}
  consumer:
    desc: "Consumer block"
    hasRtl: false
__CONSUMER_PARAMS__
    ports:
      inData: {interface: childIf, direction: dst}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer__PRODUCER_VARIANT__}
  uConsumer: {container: top, instanceType: consumer__CONSUMER_VARIANT__}

connections:
  - {interface: parentIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}
"""

PARAM_TYPE_PAYLOAD_YAML = TYPE_PAYLOAD_INTERFACE_DEF + """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 16, desc: "Data width"}
  types:
    data_t: {width: WIDTH, desc: "Data type"}

""" + (TYPE_PAYLOAD_BODY
       .replace('__PRODUCER_PARAMS__', '    params: [WIDTH]')
       .replace('__CONSUMER_PARAMS__', '    params: [WIDTH]')
       .replace('__PRODUCER_VARIANT__', ', variant: prodVar')
       .replace('__CONSUMER_VARIANT__', ', variant: consVar')) + """
parameters:
  producer:
    prodVar:
      WIDTH: 8
  consumer:
    consVar:
      WIDTH: 8
"""

FIXED_TYPE_PAYLOAD_YAML = TYPE_PAYLOAD_INTERFACE_DEF + """constants:
  WIDTH: {value: 8, desc: "Data width"}

types:
  data_t: {width: WIDTH, desc: "Data type"}

""" + (TYPE_PAYLOAD_BODY
       .replace('__PRODUCER_PARAMS__\n', '')
       .replace('__CONSUMER_PARAMS__\n', '')
       .replace('__PRODUCER_VARIANT__', '')
       .replace('__CONSUMER_VARIANT__', ''))


def _thunker_type_args(db_path):
    prj = projectOpen(db_path)
    top = get_top_block_data(db_path)
    thunker = first_thunker(top)
    ref = prj.datatypeRef('types', thunker['payloads'][0]['structureKey'])
    ns = intf_gen_utils.cpp_namespace_name(prj.contextModuleIdentity[ref['context']])
    decls = intf_gen_utils.sc_declare_thunkers(top, prj, '', top)
    if len(decls) != 1 or not decls[0].endswith(' thunker_outData_uConsumer;'):
        raise AssertionError(f"expected one thunker member for the bind, got {decls}")
    args = decls[0].split('<', 1)[1].rsplit('>', 1)[0]
    return prj, thunker, ns, [a.strip() for a in args.split(',')]


def test_type_payload_spelling_parameterizable():
    print("\nTesting thunker spelling of a parameterizable type payload")
    # A type payload is a (name, width) pair. A parameterizable type is an
    # alias template over the Config the bound side selects, its width a
    # member of that Config, and the type name carries its owner's namespace.
    db_path, project_path, arch_path = build_database(PARAM_TYPE_PAYLOAD_YAML)
    try:
        prj, thunker, ns, args = _thunker_type_args(db_path)
        configs = [intf_gen_utils.cpp_config_struct_name(p['configSelection'])
                   for p in thunker['payloads']]
        expected = [f'{ns}::data_t<{configs[0]}>', f'{configs[0]}::WIDTH',
                    f'{ns}::data_t<{configs[1]}>', f'{configs[1]}::WIDTH']
        if args[:4] != expected:
            print(f"FAIL: expected {expected}, got {args[:4]}")
            return False
        if not (configs[0].endswith('ProdVarConfig') and configs[1].endswith('ConsVarConfig')):
            print(f"FAIL: each side must spell the Config its own instance selects, got {configs}")
            return False
        if args[4:] != ['true' if pair['directCopy'] else 'false'
                        for pair in thunker['payloadPairs']]:
            print(f"FAIL: the verdict slot must follow the two pairs, got {args[4:]}")
            return False
        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


def test_type_payload_spelling_fixed_width_constant():
    print("\nTesting thunker spelling of a fixed type whose width names a constant")
    # The constant's bare name is ambiguous across the contexts a composed
    # container imports, so the width is spelled as its resolved literal.
    db_path, project_path, arch_path = build_database(FIXED_TYPE_PAYLOAD_YAML)
    try:
        prj, thunker, ns, args = _thunker_type_args(db_path)
        expected = [f'{ns}::data_t', '8', f'{ns}::data_t', '8']
        if args[:4] != expected:
            print(f"FAIL: expected {expected}, got {args[:4]}")
            return False
        print("PASS")
        return True
    finally:
        cleanup((db_path, project_path, arch_path))


def run_all_tests():
    tests = [
        lambda: test_parameter_order('rdy_vld', ['data_t', 'data_t']),
        lambda: test_parameter_order('req_ack', ['data_t', 'rdata_t', 'data_t', 'rdata_t']),
        lambda: test_parameter_order('push_ack', ['data_t', 'data_t']),
        lambda: test_parameter_order('apb', ['addr_t', 'data_t', 'addr_t', 'data_t']),
        test_no_struct_parameter_not_thunked,
        test_binds_directly_reflects_param_values,
        test_connectionmap_child_missing_param_rejected,
        test_type_payload_spelling_parameterizable,
        test_type_payload_spelling_fixed_width_constant,
    ]
    return 0 if all(test() for test in tests) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
