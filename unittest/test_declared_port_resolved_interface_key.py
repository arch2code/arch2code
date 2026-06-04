#!/usr/bin/env python3
"""Declared-port cross-interface checks use the resolved interfaceKey."""

import os
import sys
import tempfile

from _addrctl_helpers import (
    cleanup,
    run_arch2code,
    test_dir,
    write_temp,
)


DESIRED_YAML = """constants:
  WIDTH: {value: 32, desc: "Desired child bus width"}

types:
  data_t: {width: WIDTH, desc: "Desired child data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  sharedIf:
    interfaceType: rdy_vld
    desc: "Child-visible interface with the correct packed form"
    structures:
      - {structure: data_st, structureType: data_t}
"""


POISON_YAML = """constants:
  WIDTH: {value: 16, desc: "Out-of-scope duplicate bus width"}

types:
  data_t: {width: WIDTH, desc: "Out-of-scope duplicate data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  sharedIf:
    interfaceType: rdy_vld
    desc: "Earlier duplicate that must not satisfy the child port"
    structures:
      - {structure: data_st, structureType: data_t}
"""


CHILD_YAML_TEMPLATE = """include:
  - __DESIRED_FILE__

blocks:
  consumer:
    desc: "Consumer whose port resolves sharedIf through its include scope"
    ports:
      inData: {interface: sharedIf, direction: dst}
"""


ARCH_YAML_TEMPLATE = """include:
  - __POISON_FILE__
  - __CHILD_FILE__

constants:
  WIDTH: {value: 32, desc: "Parent bus width"}

types:
  data_t: {width: WIDTH, desc: "Parent data type"}

variables:
  data: {type: data_t, desc: "Data"}

structures:
  data_st:
    data: {}

interfaces:
  parentIf:
    interfaceType: rdy_vld
    desc: "Parent interface compatible with the child-scoped sharedIf"
    structures:
      - {structure: data_st, structureType: data_t}

blocks:
  top: {desc: "Top block"}
  producer: {desc: "Producer block"}

instances:
  uTop: {container: top, instanceType: top}
  uProducer: {container: top, instanceType: producer}
  uConsumer: {container: top, instanceType: consumer}

connections:
  - {interface: parentIf, src: uProducer, srcport: outData, dst: uConsumer, dstport: inData}
"""


PROJECT_YAML_TEMPLATE = """projectName: declared_port_interface_key_test
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - __ARCH_FILE__
"""


def _run():
    print("Declared ports: cross-interface check uses resolved interfaceKey")
    desired_path = write_temp(DESIRED_YAML, '.yaml', 'decl_port_desired_')
    poison_path = write_temp(POISON_YAML, '.yaml', 'decl_port_poison_')
    child_yaml = CHILD_YAML_TEMPLATE.replace(
        '__DESIRED_FILE__', os.path.basename(desired_path))
    child_path = write_temp(child_yaml, '.yaml', 'decl_port_child_')
    arch_yaml = (
        ARCH_YAML_TEMPLATE
        .replace('__POISON_FILE__', os.path.basename(poison_path))
        .replace('__CHILD_FILE__', os.path.basename(child_path))
    )
    arch_path = write_temp(arch_yaml, '.yaml', 'decl_port_arch_')
    project_yaml = PROJECT_YAML_TEMPLATE.replace(
        '__ARCH_FILE__', os.path.basename(arch_path))
    project_path = write_temp(
        project_yaml, '_project.yaml', 'decl_port_proj_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, db_path, arch_path, child_path,
             desired_path, poison_path]
    try:
        result = run_arch2code(project_path, db_path)
        if result.returncode != 0:
            print(
                "FAIL: arch2code.py failed; the declared port should use "
                "the child file's resolved interfaceKey.\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
            return False
        print("PASS: declared port resolved interfaceKey")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
