#!/usr/bin/env python3
"""fileGeneration.layout selector validation (projectCreate, T1.1).

The base config supplies `fileGeneration.layout: functional`, so every merged
project carries the selector. projectCreate.validateLayout() accepts only
'functional' or 'hierarchical' and hard-stops on anything else, before the
layout value is consumed downstream. This test exercises the reject branch and
both accepted values; the default (selector absent from the user file, inherited
from base) is the path every other fixture already takes.
"""

import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
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


def _run_with_layout(layout):
    """Build the valid arch, injecting a fileGeneration.layout selector into
    the generated project file. layout=None omits the section (inherits base
    default). Returns (completed process, paths-to-clean)."""
    project_path, arch_paths = make_project([('arch', ARCH_YAML)])
    if layout is not None:
        with open(project_path, 'a') as f:
            f.write(f"\nfileGeneration:\n    layout: {layout}\n")
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, db_path] + arch_paths
    try:
        return run_arch2code(project_path, db_path), paths
    except Exception:
        cleanup(paths)
        raise


def _check_invalid():
    print("layout: an unknown value is a hard stop")
    result, paths = _run_with_layout('bogus')
    try:
        output = result.stdout + result.stderr
        assert result.returncode != 0, \
            f"expected failure for invalid layout; got rc=0\n{output}"
        assert "fileGeneration.layout must be one of" in output, \
            f"expected the layout-validation message; got:\n{output}"
        print("PASS: invalid layout rejected")
        return True
    finally:
        cleanup(paths)


def _check_accepted(layout):
    print(f"layout: '{layout}' is accepted")
    result, paths = _run_with_layout(layout)
    try:
        output = result.stdout + result.stderr
        assert result.returncode == 0, \
            f"expected '{layout}' to build; got rc={result.returncode}\n{output}"
        assert "fileGeneration.layout must be one of" not in output, \
            f"'{layout}' must not trip layout validation; got:\n{output}"
        print(f"PASS: '{layout}' accepted")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    ok = (_check_invalid()
          and _check_accepted('functional')
          and _check_accepted('hierarchical'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
