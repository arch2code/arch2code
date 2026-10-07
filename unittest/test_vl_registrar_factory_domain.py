#!/usr/bin/env python3
"""`_verif` registrations carry the factory domain the container looks up.

A child without its own params is looked up under its owner only
(`createInstanceProjectName`), so its registrar view holds one entry per
variant, keyed on the owner. `twoClk` and the child-project block `twoClkIpSrc`
are such children in `examples/twoClk`.

A child with its own params is looked up under the pair-qualified domain, and
standalone sites still ask for the owner alias, so its view keeps both entries.
`blockF` is such a child in `examples/mixed`.

Reads the example YAML and writes each database to a temp path.
"""

import os
import sys
import tempfile

from _addrctl_helpers import base_dir, cleanup, projectOpen, run_arch2code


TWOCLK_PROJECT = os.path.join(
    base_dir, 'examples', 'twoClk', 'prj', 'yaml', 'project.yaml')
MIXED_PROJECT = os.path.join(
    base_dir, 'examples', 'mixed', 'arch', 'yaml', 'project.yaml')


def _build_db(project_path):
    db_path = tempfile.mktemp(suffix='.db', dir=os.path.dirname(__file__))
    result = run_arch2code(project_path, db_path, timeout=180)
    if result.returncode != 0:
        cleanup([db_path])
        raise RuntimeError(
            f"arch2code.py failed on {project_path}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return db_path


def _verif_view(prj, child, parent):
    childKey = prj.getQualBlock(child)
    return prj.getRegistrarConfigView(childKey, prj.getQualBlock(parent))


def test_paramsless_child_registers_once():
    db_path = _build_db(TWOCLK_PROJECT)
    try:
        prj = projectOpen(db_path)
        view = _verif_view(prj, 'twoClk', 'twoClk_tb')
        keys = [(entry['variant'], entry['factoryProject'])
                for entry in view['verifRegistrations']]
        assert keys == [('', 'twoClk')], \
            f"twoClk has no own params, so it registers once under its owner; got {keys}"
        # A child from another project registers under that project, not the assembler.
        view = _verif_view(prj, 'twoClkIpSrc', 'twoClk')
        keys = [(entry['variant'], entry['factoryProject'])
                for entry in view['verifRegistrations']]
        assert keys == [('', 'twoClkIp')], \
            f"twoClkIpSrc has no own params, so it registers once under its owner " \
            f"twoClkIp; got {keys}"
    finally:
        cleanup([db_path])


def test_param_child_keeps_owner_alias():
    db_path = _build_db(MIXED_PROJECT)
    try:
        prj = projectOpen(db_path)
        view = _verif_view(prj, 'blockF', 'blockB')
        pair = prj.registrarPairs[(prj.getQualBlock('blockB'), prj.getQualBlock('blockF'))]
        keys = [(entry['variant'], entry['factoryProject'])
                for entry in view['verifRegistrations']]
        expected = sorted((variant, domain)
                          for variant in ('variant0', 'variant1')
                          for domain in (pair['factoryProject'], 'mixed'))
        assert pair['factoryProject'] != 'mixed', \
            "blockF's pair domain should differ from its owner"
        assert keys == expected, \
            f"blockF has own params, so it registers under the pair domain and the " \
            f"owner alias; expected {expected}, got {keys}"
    finally:
        cleanup([db_path])


def run_all_tests():
    print("Verilated registrar factory domains")
    for test in (test_paramsless_child_registers_once,
                 test_param_child_keeps_owner_alias):
        test()
        print(f"PASS: {test.__name__}")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
