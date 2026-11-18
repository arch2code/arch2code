#!/usr/bin/env python3
"""An enum takes its SV width from width, widthLog2 or widthLog2minus1.

An enum with no width field takes the bit count of its largest value. An enum
that gives one of the three fields renders in the SV package the same way a
plain type does, so a widthLog2minus1 constant becomes `$clog2(C)` rather than
an empty `[-1:0]` range. make db rejects a given width that cannot hold the
largest enum value, naming the type, the width field, the bits it resolves to,
the largest value and the bits that value needs.
"""

import os
import sys
from types import SimpleNamespace

from _addrctl_helpers import build_database, cleanup
from _tmp_helpers import close_db

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from pysrc.systemVerilogGenerator import systemVerilogGenerator
from templates.systemVerilog import package


def _arch(width_line):
    """width_line is the enum's width field as YAML, or '' for none."""
    return f"""constants:
    FAC_NUM_BANKS: {{ value: 3, desc: "bank count" }}

types:
    fac_bank_e:
        desc: "bank select"
{width_line}        enum:
            - {{ enumName: FAC_BANK_PQSE, value: 0, desc: "PQSE bank" }}
            - {{ enumName: FAC_BANK_CMCU, value: 1, desc: "CMCU bank" }}
            - {{ enumName: FAC_BANK_PSS,  value: 2, desc: "PSS bank" }}

blocks:
    top:
        desc: "top"

instances:
    uTop: {{ container: top, instanceType: top }}
"""


def _render_package(db_path):
    prj = projectOpen(db_path)
    context = prj.data['blocks'][prj.getQualBlock('top')]['_context']
    data = prj.getContextData([context], systemVerilogGenerator.dataTypeMappings)
    # systemVerilogGenerator sets these two keys before it renders: the context
    # list and the user-supplied package imports, of which this fixture has none.
    data['context'] = [context]
    data['importPackages'] = None
    return package.render(SimpleNamespace(fileMapKey=None), prj, data)


def _renders(label, width_line, want):
    label = f"{label} renders typedef enum logic[{want}-1:0]"
    try:
        db_path, project_path, arch_paths = build_database(_arch(width_line))
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    try:
        rendered = _render_package(db_path)
        close_db()
        line = next((l for l in rendered.split('\n') if 'typedef enum' in l), None)
        if line is None or not line.startswith(f"typedef enum logic[{want}-1:0] {{"):
            print(f"FAIL: {label}: got {line!r}\n{rendered}")
            return False
        print(f"PASS: {label}")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _rejected(label, width_line, needles):
    label = f"{label} is rejected at make db"
    try:
        db_path, project_path, arch_paths, result = build_database(_arch(width_line), expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    try:
        combined = result.stdout + result.stderr
        missing = [n for n in ["type 'fac_bank_e'", os.path.basename(arch_paths[0])] + needles
                   if n not in combined]
        if missing:
            print(f"FAIL: {label}: diagnostic lacks {missing}\n{combined}")
            return False
        print(f"PASS: {label}")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    results = [
        _renders("no width", '', '2'),
        _renders("widthLog2minus1: FAC_NUM_BANKS", '        widthLog2minus1: FAC_NUM_BANKS\n',
                 '$clog2(FAC_NUM_BANKS)'),
        _renders("widthLog2: FAC_NUM_BANKS", '        widthLog2: FAC_NUM_BANKS\n',
                 '$clog2(FAC_NUM_BANKS+1)'),
        _renders("width: 4", '        width: 4\n', '4'),
        _rejected("width: 1", '        width: 1\n',
                  ["width resolves to a 1-bit width", "largest enum value 2 needs 2 bits"]),
        _rejected("widthLog2: 1", '        widthLog2: 1\n',
                  ["widthLog2 resolves to a 1-bit width", "largest enum value 2 needs 2 bits"]),
        _rejected("widthLog2minus1: 2", '        widthLog2minus1: 2\n',
                  ["widthLog2minus1 resolves to a 1-bit width", "largest enum value 2 needs 2 bits"]),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
