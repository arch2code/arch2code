#!/usr/bin/env python3
"""Both ends of one connection resolving to the same port of the same block.

A connection end is keyed by `portId`, which `config/schema.yaml` composes from
`instanceType` + `portName`. When both ends of ONE connection are instances of
the same block type and both resolve to the same port name - which is what
`getPortChannelName` produces when `srcport:` and `dstport:` are both omitted,
since it falls back to the interface name for each end - the two ends collide on
that key. Merging them leaves the connection holding a single end and emits a
channel bound to itself, which is not valid in either emitted language, so the
key is refused at parse time instead.

Collision ACROSS connections is a different and intended thing (a block's
definition is the set of instance-defined connections, and two instances of one
block type on one port name contribute that same fact once), so the second cell
authors exactly that and requires it to build.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


BASE_YAML = """types:
  data_t: {width: 8, desc: "Data word"}

structures:
  data_st:
    data: {varType: data_t, desc: "Data word"}

interfaces:
  dataIf:
    interfaceType: rdy_vld
    desc: "Data interface"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  peer: {desc: "Block used at both ends"}
  sink: {desc: "Distinct consumer block"}

instances:
  uTop:   {container: top, instanceType: top}
  uPeerA: {container: top, instanceType: peer}
  uPeerB: {container: top, instanceType: peer}
  uSinkA: {container: top, instanceType: sink}
  uSinkB: {container: top, instanceType: sink}

connections:
__CONNECTIONS__
"""


def build_project(connections):
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='conn_end_collision_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(BASE_YAML.replace('__CONNECTIONS__', connections.rstrip()))

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='conn_end_collision_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(f"""projectName: conn_end_collision_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
""")
    return project_path, arch_path


def run_db(connections):
    project_path, arch_path = build_project(connections)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '-y', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=60, cwd=base_dir, env=env)
        return result
    finally:
        for path in (project_path, arch_path, db_path):
            if path and os.path.exists(path):
                os.unlink(path)


EXPECTED = [
    "names both ends on the same port of the same block",
    "'uPeerA'",
    "'uPeerB'",
    "block 'peer'",
    "port 'dataIf'",
    "distinct port names",
]


def test_same_block_same_port_both_ends_rejected():
    """Both ends are instances of `peer` and neither names a port, so both
    resolve to the interface name and the two ends share one portId."""
    print("both ends of one connection on the same block/port is rejected")
    result = run_db("  - {interface: dataIf, src: uPeerA, dst: uPeerB}")
    combined = result.stdout + '\n' + result.stderr
    if result.returncode == 0:
        print("  FAIL: db build succeeded on the colliding connection")
        return False
    if 'Traceback (most recent call last):' in combined:
        print("  FAIL: Python stack trace instead of a clean diagnostic")
        print("  " + "\n  ".join(combined.split('\n')[:20]))
        return False
    missing = [n for n in EXPECTED if n.lower() not in combined.lower()]
    if missing:
        print(f"  FAIL: diagnostic missing {missing}")
        print("  " + "\n  ".join(combined.split('\n')[:30]))
        return False
    print("  PASS")
    return True


def test_same_block_same_port_across_connections_is_accepted():
    """Two connections reusing one block type on one port name state the same
    fact about that block twice; merging them per file is intended."""
    print("the same block/port reused by two separate connections is accepted")
    result = run_db(
        "  - {interface: dataIf, src: uPeerA, dst: uSinkA}\n"
        "  - {interface: dataIf, src: uPeerB, dst: uSinkB}")
    if result.returncode != 0:
        print("  FAIL: db build rejected a cross-connection reuse it must accept")
        print("  " + "\n  ".join((result.stdout + result.stderr).split('\n')[:30]))
        return False
    print("  PASS")
    return True


def run_all_tests():
    ok = test_same_block_same_port_both_ends_rejected()
    ok = test_same_block_same_port_across_connections_is_accepted() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
