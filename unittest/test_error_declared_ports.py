#!/usr/bin/env python3
"""
Test DB-time error handling for bottom-up block ports declarations.

These tests verify that invalid blocks.<block>.ports declarations fail during
database creation, before generator view assembly.
"""

import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def create_test_files(arch_content):
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='declared_ports_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    project_content = f"""projectName: declared_ports_error_test
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='declared_ports_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)

    return project_path, arch_path


def test_error_case(yaml_content, expected_patterns, test_name):
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"{'='*70}")

    project_path, arch_path = create_test_files(yaml_content)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)

    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '-y', project_path, '--db', db_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=base_dir,
            env=env,
        )

        full_output = result.stdout + '\n' + result.stderr
        if result.returncode == 0:
            print("  FAIL: Build succeeded when it should have failed")
            return False

        if 'Traceback (most recent call last):' in full_output:
            print("  FAIL: Got Python stack trace instead of clean error")
            print("  " + "\n  ".join(full_output.split('\n')[:20]))
            return False

        missing = [
            pattern for pattern in expected_patterns
            if pattern.lower() not in full_output.lower()
        ]
        if missing:
            print(f"  FAIL: Missing expected patterns: {missing}")
            print("  " + "\n  ".join(full_output.split('\n')[:40]))
            return False

        print("  PASS: Got expected DB-time error")
        return True

    finally:
        for path in (project_path, arch_path, db_path):
            if path and os.path.exists(path):
                os.unlink(path)


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
  dataIf:
    interfaceType: rdy_vld
    desc: "Primary data interface"
    structures:
      - {structure: data_st, structureType: data_t}
  altDataIf:
    interfaceType: rdy_vld
    desc: "Alternate compatible data interface"
    structures:
      - {structure: data_st, structureType: data_t}
  reqIf:
    interfaceType: req_ack
    desc: "Different protocol interface"
    structures:
      - {structure: data_st, structureType: data_t}
      - {structure: data_st, structureType: rdata_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer block"}
  consumer:
    desc: "Consumer block"
    ports:
__CONSUMER_PORTS__

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
__CONNECTIONS__
"""


def build_yaml(consumer_ports, connections):
    return (
        BASE_YAML
        .replace('__CONSUMER_PORTS__', consumer_ports.rstrip())
        .replace('__CONNECTIONS__', connections.rstrip())
    )


def test_declared_port_without_inferred_source():
    yaml = build_yaml(
        "      missingPort: {interface: dataIf, direction: dst}",
        "  - {interface: dataIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}",
    )
    return test_error_case(
        yaml,
        ["declares port 'missingPort'", "no connection", "produces port"],
        "Declared port has no inferred producer",
    )


def test_partial_declaration_missing_connection_port():
    yaml = build_yaml(
        "      inData: {interface: dataIf, direction: dst}",
        """  - {interface: dataIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}
  - {interface: dataIf, src: uProducer, srcport: outAux, dst: uConsumer, dstport: auxData}""",
    )
    return test_error_case(
        yaml,
        ["partial ports", "omits port 'auxData'", "implied by connections"],
        "Partial declaration omits connection-derived port",
    )


def test_declared_interface_wrong_protocol():
    yaml = build_yaml(
        "      inData: {interface: reqIf, direction: dst}",
        "  - {interface: dataIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}",
    )
    return test_error_case(
        yaml,
        ["declares interface 'reqIf'", "bound to interface 'dataIf'", "interfaceType"],
        "Declared port interface has wrong protocol",
    )


def test_declared_direction_mismatch():
    yaml = build_yaml(
        "      inData: {interface: dataIf, direction: src}",
        "  - {interface: dataIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}",
    )
    return test_error_case(
        yaml,
        ["declares direction 'src'", "bound with direction 'dst'"],
        "Declared port direction disagrees with inferred direction",
    )


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING ERROR HANDLING: Bottom-Up Declared Ports")
    print("="*70)

    tests = [
        test_declared_port_without_inferred_source,
        test_partial_declaration_missing_connection_port,
        test_declared_interface_wrong_protocol,
        test_declared_direction_mismatch,
    ]

    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
