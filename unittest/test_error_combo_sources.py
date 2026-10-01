#!/usr/bin/env python3
"""Combo-source handling in `processSimple` (pysrc/processYaml.py).

Checks that an explicit-null combo source fails cleanly instead of
crashing, and that a required combo source left empty is still
validated rather than silently accepted.
"""

import sys

from _addrctl_helpers import build_database, cleanup


BASE_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }

structures:
    dataSt:
        data: { varType: dataT, desc: "payload word" }

interfaces:
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - { structure: dataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    prod:
        desc: "producer"
        hasMdl: true
    cons:
        desc: "consumer"
        hasMdl: true
    memBlock:
        desc: "block owning a memory"
        hasMdl: true

instances:
    uTop:  { container: top, instanceType: top }
    uProd: { container: top, instanceType: prod }
    uCons: { container: top, instanceType: cons }
    uMem:  { container: top, instanceType: memBlock }

memories:
    - { memory: tbl, block: memBlock, structure: dataSt, addressStruct: dataSt, wordLines: 4, ports: [p], desc: "test memory" }
"""


def _check(label, arch_yaml, required_substrings):
    print(label)
    db_path, project_path, arch_paths, result = build_database(
        arch_yaml, expect_success=False)
    try:
        combined = result.stdout + result.stderr
        if 'Traceback' in combined:
            print(f"FAIL: the build crashed instead of reporting a diagnostic.\n{combined}")
            return False
        missing = [needle for needle in required_substrings if needle not in combined]
        if missing:
            print(f"FAIL: diagnostic missing substrings {missing}.\n{combined}")
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_connection_name_null_is_missing_combo_source():
    """Feeds a connections row with `name: ~` (null combo source).
    Expects a "missing required combo source" diagnostic for connection."""
    arch_yaml = BASE_DESIGN + """
connections:
    - { interface: dataIf, name: ~, src: uProd, srcport: out, dst: uCons, dstport: in }
"""
    return _check(
        "connections row with name: ~ reports missing required combo source",
        arch_yaml,
        ["missing required combo source", "connection"])


def test_memory_connection_omitted_memory_is_missing_required_field():
    """Feeds a memoryConnections row that omits the required `memory:` field.
    The plain required-field check fires first and exits, so the combo
    loop only ever sees an explicit `~` for a required source."""
    arch_yaml = BASE_DESIGN + """
memoryConnections:
    - { block: memBlock, instance: uMem, port: p }
"""
    return _check(
        "memoryConnections row omitting memory: reports missing required field",
        arch_yaml,
        ["is missing required field memory"])


def test_memory_connection_empty_memory_fails_validation():
    """Feeds a memoryConnections row with `memory: ""` (empty required source).
    Expects the foreign-key validator to reject it as "not valid in context"."""
    arch_yaml = BASE_DESIGN + """
memoryConnections:
    - { memory: "", block: memBlock, instance: uMem, port: p }
"""
    return _check(
        "memoryConnections row with memory: \"\" is rejected by the foreign-key validator",
        arch_yaml,
        ["not valid in context"])


def run_all_tests():
    tests = [
        test_connection_name_null_is_missing_combo_source,
        test_memory_connection_omitted_memory_is_missing_required_field,
        test_memory_connection_empty_memory_fails_validation,
    ]
    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"EXCEPTION in {test_func.__name__}: {e}")
            results.append(False)
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
