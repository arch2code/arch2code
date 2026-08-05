#!/usr/bin/env python3
"""yamlFormat sentinel gate (projectCreate).

A migrated project carries a single top-level `yamlFormat: 2` in its
project.yaml. projectCreate refuses to build a project that lacks the
sentinel, or that declares a value the generator does not expect, before
any address or eval processing runs. These are the two negative branches
the gate adds; the positive (sentinel present) path is exercised by every
other stamped fixture, and is asserted here too for completeness.
"""

import os
import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    make_project,
    render_leaf,
    render_router,
    run_arch2code,
    test_dir,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Leaf config register" }
"""
)


def _run_with_format(yaml_format):
    """Build the same valid arch with a chosen sentinel value (None omits
    the field). Returns the completed arch2code process for inspection."""
    project_path, arch_paths = make_project(
        [('arch', ARCH_YAML)], yaml_format=yaml_format)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        return run_arch2code(project_path, db_path), [project_path, db_path] + arch_paths
    except Exception:
        cleanup([project_path, db_path] + arch_paths)
        raise


def _check_absent():
    print("gate: absent sentinel is a hard stop naming `make migrate`")
    result, paths = _run_with_format(None)
    try:
        output = result.stdout + result.stderr
        assert result.returncode != 0, \
            f"expected failure when sentinel is absent; got rc=0\n{output}"
        assert "not migrated to yamlFormat" in output, \
            f"expected the un-migrated message; got:\n{output}"
        assert "make migrate" in output, \
            f"expected the remediation command; got:\n{output}"
        print("PASS: absent sentinel")
        return True
    finally:
        cleanup(paths)


def _check_wrong_value():
    print("gate: a mismatched sentinel reports the expected version")
    result, paths = _run_with_format(99)
    try:
        output = result.stdout + result.stderr
        assert result.returncode != 0, \
            f"expected failure when sentinel mismatches; got rc=0\n{output}"
        assert "expects yamlFormat: 2" in output, \
            f"expected the version-mismatch message; got:\n{output}"
        # The mismatch branch is distinct from the absent branch.
        assert "not migrated to yamlFormat" not in output, \
            f"mismatch must not print the absent-sentinel message; got:\n{output}"
        print("PASS: mismatched sentinel")
        return True
    finally:
        cleanup(paths)


def _check_present():
    print("gate: a correctly stamped project builds past the gate")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    cleanup([project_path, db_path] + arch_paths)
    print("PASS: present sentinel")
    return True


def run_all_tests():
    ok = _check_absent() and _check_wrong_value() and _check_present()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
