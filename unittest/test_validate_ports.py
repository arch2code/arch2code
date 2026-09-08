#!/usr/bin/env python3
"""
Tests for validatePorts() connectionMap boundary port checking.
"""

import os
import sys
import tempfile
import subprocess

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def create_test_files(arch_content, project_extra=""):
    arch_fd, arch_path = tempfile.mkstemp(suffix='.yaml', prefix='arch_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    arch_basename = os.path.basename(arch_path)
    project_content = f"""yamlFormat: 2
projectName: validate_ports_test
topInstance: u_top

dirs:
  root: ..

projectFiles:
  - {arch_basename}
{project_extra}
"""
    project_fd, project_path = tempfile.mkstemp(suffix='_project.yaml', prefix='proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)

    return project_path, arch_path


def run_db_build(project_path, db_path, cwd=None):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    arch2code_path = os.path.join(base_dir, 'arch2code.py')
    cmd = [sys.executable, arch2code_path, '--yaml', project_path, '--db', db_path]
    if cwd is None:
        cwd = test_dir
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)


def test_orphan_connection_map():
    """connectionMap without a matching boundary connection should fail make db."""
    yaml = """types:
  bit_t:
    width: 1
    desc: single bit

structures:
  irq_st:
    level: {varType: bit_t, desc: irq level}

interfaces:
  irq_if:
    interfaceType: status
    desc: level-sensitive irq
    structures:
      - {structure: irq_st, structureType: data_t}

blocks:
  top_tb:
    desc: tb container
    hasTb: false
  child:
    desc: child block
    hasMdl: true
  top:
    desc: top block
    hasMdl: true
    hasTb: true

instances:
  top_tb:
    container: top_tb
    instanceType: top_tb
  u_top:
    container: top_tb
    instanceType: top
  u_child:
    container: top
    instanceType: child

connectionMaps:
  - {interface: irq_if, block: top, direction: src, instance: u_child}
"""
    project_path, arch_path = create_test_files(yaml)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        result = run_db_build(project_path, db_path)
        output = result.stderr + result.stdout
        if result.returncode == 0:
            print("FAIL: expected db build to fail for orphan connectionMap")
            return False
        if 'connectionmap' not in output.lower():
            print(f"FAIL: expected connectionMap in error output:\n{output}")
            return False
        if 'irq_if' not in output:
            print(f"FAIL: expected irq_if in error output:\n{output}")
            return False
        if 'boundary' not in output.lower():
            print(f"FAIL: expected boundary in error output:\n{output}")
            return False
        print("PASS: orphan connectionMap rejected")
        return True
    finally:
        for path in (project_path, arch_path, db_path):
            if os.path.exists(path):
                os.unlink(path)


def test_port_name_mismatch_hint():
    """connectionMap using interface name should hint when TB connection uses name: alias."""
    yaml = """types:
  bit_t:
    width: 1
    desc: single bit

structures:
  irq_st:
    level: {varType: bit_t, desc: irq level}

interfaces:
  irq_if:
    interfaceType: status
    desc: level-sensitive irq
    structures:
      - {structure: irq_st, structureType: data_t}

blocks:
  top_tb:
    desc: tb container
    hasTb: false
  sink:
    desc: irq sink
    hasMdl: true
  child:
    desc: child block
    hasMdl: true
  top:
    desc: top block
    hasMdl: true
    hasTb: true

instances:
  top_tb:
    container: top_tb
    instanceType: top_tb
  u_top:
    container: top_tb
    instanceType: top
  u_child:
    container: top
    instanceType: child
  u_sink:
    container: top_tb
    instanceType: sink

connections:
  - {interface: irq_if, src: u_top, dst: u_sink, name: irq_out}

connectionMaps:
  - {interface: irq_if, block: top, direction: src, instance: u_child}
"""
    project_path, arch_path = create_test_files(yaml)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        result = run_db_build(project_path, db_path)
        output = result.stderr + result.stdout
        if result.returncode == 0:
            print("FAIL: expected db build to fail for port name mismatch")
            return False
        if 'port: irq_out' not in output:
            print(f"FAIL: expected port hint in error output:\n{output}")
            return False
        print("PASS: port name mismatch hint emitted")
        return True
    finally:
        for path in (project_path, arch_path, db_path):
            if os.path.exists(path):
                os.unlink(path)


def test_nested_example_passes():
    """Valid nested example with aligned connectionMaps should pass make db."""
    nested_dir = os.path.join(base_dir, 'examples', 'nested', 'prj', 'yaml')
    project_path = os.path.join(nested_dir, 'nestedProject.yaml')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        result = run_db_build(project_path, db_path, cwd=nested_dir)
        output = result.stderr + result.stdout
        if result.returncode != 0:
            print(f"FAIL: nested example should pass make db:\n{output}")
            return False
        print("PASS: nested example db build succeeded")
        return True
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    tests = [
        test_orphan_connection_map,
        test_port_name_mismatch_hint,
        test_nested_example_passes,
    ]
    passed = sum(1 for t in tests if t())
    failed = len(tests) - passed
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
