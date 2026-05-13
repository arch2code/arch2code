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


def run_all_tests():
    tests = [
        lambda: test_parameter_order('rdy_vld', ['data_t', 'data_t']),
        lambda: test_parameter_order('req_ack', ['data_t', 'rdata_t', 'data_t', 'rdata_t']),
        lambda: test_parameter_order('push_ack', ['data_t', 'data_t']),
        lambda: test_parameter_order('apb', ['addr_t', 'data_t', 'addr_t', 'data_t']),
        test_no_struct_parameter_not_thunked,
    ]
    return 0 if all(test() for test in tests) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
