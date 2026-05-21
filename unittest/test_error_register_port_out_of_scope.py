#!/usr/bin/env python3
"""E1.5: Leaf registerPorts: row targets an interface defined outside the
leaf's load-time scope.

The leaf block lives in its own YAML file that does not include the
interfaces YAML. The arch YAML includes both files via `include:`, so
the global design eventually sees `apbReg`, but the leaf file's
load-time scope does not.

The schema's `_validate` step rejects the unresolved reference. The
diagnostic must name the leaf's defining YAML file (where the bad
row sits), the registerPorts row, the offending interface, and the
fact that the symbol could not be located in any other context.

The "no <section> row named '<value>' was found in any context
processed before this one" hint is produced by the generic
out-of-scope enrichment in `pysrc/processYaml.py::processSimple`.
That enrichment runs against `self.data` and so depends on file
processing order: in this fixture the arch yaml that defines
`apbReg` depends on the leaf yaml and is therefore processed
*after* it, so the symbol has not yet been registered when the leaf
fails validation. We accept the narrower "not found" message rather
than reach into unparsed raw yaml. The enrichment applies to every
`_validate: {section, field}` reference in the schema, not just to
registerPorts.
"""

import os
import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
    cleanup,
    render_router,
    run_arch2code,
    test_dir,
    write_temp,
)


LEAF_YAML = """blockDir: .

blocks:
    outOfScopeLeaf:
        desc: "Leaf referencing apbReg from outside its load-time scope"
        hasMdl: true
        registerPorts:
            regs: { interface: apbReg }
"""


ARCH_YAML_TEMPLATE = (
    APB_PREAMBLE
    + """
include:
    - __LEAF_FILE__

blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uLeaf:       { container: top, instanceType: outOfScopeLeaf, addressGroup: top }
"""
)


PROJECT_YAML_TEMPLATE = """projectName: e15_test
topInstance: uTop

dirs:
    root: ..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
    registers:
        alignment: 8
        sortDescending: true

projectFiles:
    - __ARCH_FILE__
"""


REQUIRED_SUBSTRINGS_TEMPLATE = [
    "key:regs",
    "field interface",
    "apbReg",
    "no interfaces row named",
    "any context processed before",
]


def _run():
    print("E1.5: registerPorts targets out-of-scope interface")
    leaf_path = write_temp(LEAF_YAML, '.yaml', 'addrctl_leaf_')
    arch_content = ARCH_YAML_TEMPLATE.replace('__LEAF_FILE__',
                                              os.path.basename(leaf_path))
    arch_path = write_temp(arch_content, '.yaml', 'addrctl_arch_')
    project_content = PROJECT_YAML_TEMPLATE.replace('__ARCH_FILE__',
                                                    os.path.basename(arch_path))
    project_path = write_temp(project_content, '_project.yaml',
                              'addrctl_proj_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)

    paths = [project_path, db_path, arch_path, leaf_path]
    try:
        result = run_arch2code(project_path, db_path)
        if result.returncode == 0:
            print("FAIL: arch2code.py succeeded; expected non-zero exit")
            return False
        combined = result.stdout + result.stderr
        # The diagnostic must mention the leaf yaml file where the bad
        # row is authored. The interface is authored in arch.yaml, but
        # arch.yaml is processed after leaf.yaml in dependency order, so
        # the enrichment cannot name it; we do not assert on the arch
        # filename for that reason.
        leaf_basename = os.path.basename(leaf_path)
        required = REQUIRED_SUBSTRINGS_TEMPLATE + [leaf_basename]
        for needle in required:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )
                return False
        print("PASS: E1.5")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
