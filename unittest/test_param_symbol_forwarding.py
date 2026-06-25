#!/usr/bin/env python3
"""Parent->child parameter symbol forwarding (diff-named and same-named).

Covers how a parameterized parent forwards parameter symbols to a
parameterized contained child instance:

(a) A binding whose value is a PARENT SYMBOL (a constant declared in the
    parent's IP-root file) is persisted on parametersvariants with that
    symbol in `value` and the qualified declaring-file key in `valueKey`;
    a literal binding keeps `value` numeric and `valueKey` empty.

(b) The projectOpen view `svInstanceParams` for the child instance forwards
    the symbol spelling for the symbol-bound, differently-named child param
    and the literal for the literal-bound param.

(c) Same-named control: when a child param's name matches a parent param
    name, the view forwards the parent symbol regardless of the child's own
    literal binding (the value flows down from the parent's instantiation).

(d) The binding-sizing validator REJECTS a symbol whose resolved value
    exceeds the child param's backing maxValue.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate, projectOpen


def _write_temp(content, suffix, prefix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=test_dir)
    os.close(fd)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


# Child IP root: own params LEAF_DATA_WIDTH (diff-named) and PWIDTH
# (same-named as a parent param). maxValue of LEAF_DATA_WIDTH bounds the
# symbol the parent forwards.
CHILD_YAML = """ipParameters:
  constants:
    LEAF_DATA_WIDTH: {value: 4, maxValue: 32, desc: "child diff-named width"}
    LEAF_MEM_DEPTH:  {value: 4, maxValue: 16, desc: "child literal depth"}
    PWIDTH:          {value: 4, maxValue: 32, desc: "child same-named width"}

blocks:
  childIp:
    desc: "Parameterized child IP"
    params: [LEAF_DATA_WIDTH, LEAF_MEM_DEPTH, PWIDTH]
"""


def _make_files(child_binding):
    """Assemble a temp project where parent `parentIp` (params PWIDTH,
    OUT_WIDTH) contains `uChild` = childIp. `child_binding` is the YAML
    `parameters:` block binding childIp's params for variant `v0`.
    """
    child_path = _write_temp(CHILD_YAML, '.yaml', 'symfwd_child_')
    parent_yaml = f"""ipParameters:
  constants:
    OUT_WIDTH: {{value: 8, maxValue: 16, desc: "parent diff-named symbol width"}}
    PWIDTH:    {{value: 8, maxValue: 16, desc: "parent same-named width"}}

blocks:
  parentIp:
    desc: "Parameterized parent IP"
    params: [OUT_WIDTH, PWIDTH]
"""
    parent_path = _write_temp(parent_yaml, '.yaml', 'symfwd_parent_')
    arch_yaml = f"""include:
  - {os.path.basename(child_path)}
  - {os.path.basename(parent_path)}

blocks:
  top:
    desc: "Top block"

instances:
  uTop:    {{ container: top, instanceType: top }}
  uParent: {{ container: top, instanceType: parentIp, variant: pv0 }}
  uChild:  {{ container: parentIp, instanceType: childIp, variant: v0 }}

parameters:
  parentIp:
    - {{ variant: pv0, param: OUT_WIDTH, value: 8 }}
    - {{ variant: pv0, param: PWIDTH, value: 8 }}
  childIp:
{child_binding}
"""
    arch_path = _write_temp(arch_yaml, '.yaml', 'symfwd_arch_')
    project_yaml = f"""projectName: param_symbol_forwarding_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(project_yaml, '_project.yaml', 'symfwd_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    return project_path, db_path, [child_path, parent_path, arch_path]


# Valid binding: LEAF_DATA_WIDTH bound to parent symbol OUT_WIDTH (diff-named),
# LEAF_MEM_DEPTH literal, PWIDTH bound to a child literal (same name as parent).
VALID_BINDING = """    - { variant: v0, param: LEAF_DATA_WIDTH, value: OUT_WIDTH }
    - { variant: v0, param: LEAF_MEM_DEPTH,  value: 4 }
    - { variant: v0, param: PWIDTH,          value: 4 }
"""

# Oversize binding: bind child PWIDTH (maxValue 32) is fine, but bind
# LEAF_MEM_DEPTH (child maxValue 16) to parent symbol OUT_WIDTH (value 8 here
# but max 16) — instead force the failure with a symbol whose resolved value
# exceeds the child's maxValue: bind LEAF_MEM_DEPTH (maxValue 16) to a parent
# const resolving to 8 is fine, so use a dedicated oversize symbol.
# We reuse OUT_WIDTH (resolves to 8) against a child param with maxValue 4.
OVERSIZE_CHILD_YAML = """ipParameters:
  constants:
    SMALL: {value: 2, maxValue: 4, desc: "child small param, maxValue 4"}

blocks:
  childIp:
    desc: "Parameterized child IP"
    params: [SMALL]
"""


def _oversize_files():
    child_path = _write_temp(OVERSIZE_CHILD_YAML, '.yaml', 'symfwd_oschild_')
    parent_yaml = """ipParameters:
  constants:
    OUT_WIDTH: {value: 8, maxValue: 16, desc: "parent symbol resolving to 8"}

blocks:
  parentIp:
    desc: "Parameterized parent IP"
    params: [OUT_WIDTH]
"""
    parent_path = _write_temp(parent_yaml, '.yaml', 'symfwd_osparent_')
    arch_yaml = f"""include:
  - {os.path.basename(child_path)}
  - {os.path.basename(parent_path)}

blocks:
  top:
    desc: "Top block"

instances:
  uTop:    {{ container: top, instanceType: top }}
  uParent: {{ container: top, instanceType: parentIp, variant: pv0 }}
  uChild:  {{ container: parentIp, instanceType: childIp, variant: v0 }}

parameters:
  parentIp:
    - {{ variant: pv0, param: OUT_WIDTH, value: 8 }}
  childIp:
    - {{ variant: v0, param: SMALL, value: OUT_WIDTH }}
"""
    arch_path = _write_temp(arch_yaml, '.yaml', 'symfwd_osarch_')
    project_yaml = f"""projectName: param_symbol_forwarding_oversize_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(project_yaml, '_project.yaml', 'symfwd_osproject_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    return project_path, db_path, [child_path, parent_path, arch_path]


def _run_valid():
    print("symbol forwarding: persisted binding + view spelling")
    original_cwd = os.getcwd()
    project_path, db_path, extra = _make_files(VALID_BINDING)
    paths = [project_path, db_path] + extra
    conn = None
    try:
        projectCreate(project_path, db_path)

        # (a) persisted binding: symbol kept in value, qualified valueKey.
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT blockKey FROM blocks WHERE block = ?", ('childIp',))
        child_block_key = c.fetchone()['blockKey']
        c.execute(
            "SELECT param, value, valueKey FROM parametersvariants "
            "WHERE blockKey = ? AND variant = ?", (child_block_key, 'v0'))
        rows = {r['param']: r for r in c.fetchall()}

        ldw = rows['LEAF_DATA_WIDTH']
        assert ldw['value'] == 'OUT_WIDTH', \
            f"(a) symbol binding value expected 'OUT_WIDTH', got {ldw['value']!r}"
        assert ldw['valueKey'].startswith('OUT_WIDTH/') and ldw['valueKey'].endswith('.yaml'), \
            f"(a) valueKey expected qualified to declaring file, got {ldw['valueKey']!r}"

        lmd = rows['LEAF_MEM_DEPTH']
        assert str(lmd['value']) == '4' and not (lmd['valueKey'] or ''), \
            f"(a) literal binding expected value 4 / empty valueKey, got {dict(lmd)}"
        conn.close()
        conn = None

        # (b)/(c) view svInstanceParams forwards spellings.
        prj = projectOpen(db_path)
        parent_block_key = [
            k for k, r in prj.data['blocks'].items()
            if isinstance(r, dict) and r.get('block') == 'parentIp'][0]
        view = prj.getBlockData(parent_block_key)
        child_inst = next(
            inst for inst in view['subBlockInstances'].values()
            if inst['instance'] == 'uChild')
        spelling = {p['param']: p['spelling'] for p in child_inst['svInstanceParams']}

        # (b) diff-named symbol-bound param forwards the symbol; literal stays.
        assert spelling['LEAF_DATA_WIDTH'] == 'OUT_WIDTH', \
            f"(b) LEAF_DATA_WIDTH expected 'OUT_WIDTH', got {spelling['LEAF_DATA_WIDTH']!r}"
        assert spelling['LEAF_MEM_DEPTH'] == '4', \
            f"(b) LEAF_MEM_DEPTH expected literal '4', got {spelling['LEAF_MEM_DEPTH']!r}"

        # (c) same-named control: child PWIDTH matches a parent param name, so
        # the view forwards the parent symbol PWIDTH even though the child's own
        # binding is the literal 4.
        assert spelling['PWIDTH'] == 'PWIDTH', \
            f"(c) same-named PWIDTH expected to forward parent symbol 'PWIDTH', got {spelling['PWIDTH']!r}"

        print("PASS: symbol forwarding (a,b,c)")
        return True
    finally:
        if conn is not None:
            conn.close()
        os.chdir(original_cwd)
        _cleanup(paths)


def _run_oversize():
    print("symbol forwarding: sizing validator rejects oversize symbol")
    # Run projectCreate in a clean subprocess: validation populates
    # process-global state, so an in-process second build would also trip
    # duplicate-key diagnostics from the first build's globals.
    project_path, db_path, extra = _oversize_files()
    paths = [project_path, db_path] + extra
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=120, cwd=base_dir, env=env)
        combined = result.stdout + result.stderr
        # OUT_WIDTH resolves to 8; child SMALL maxValue is 4 -> rejected.
        assert result.returncode != 0, \
            "(d) build should fail when a forwarded symbol exceeds child maxValue"
        assert "exceeding the backing ipParameters constant" in combined and \
               "maxValue 4" in combined, \
            f"(d) expected sizing-validator rejection message; got:\n{combined}"
        print("PASS: symbol forwarding (d) sizing rejection")
        return True
    finally:
        _cleanup(paths)


def run_all_tests():
    ok = _run_valid()
    ok = _run_oversize() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
