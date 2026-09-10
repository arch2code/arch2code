#!/usr/bin/env python3
"""Parameter variant rows carry block-scoped parameter identity."""

import os
import sqlite3
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import Site, SiteBindingIndex, projectCreate


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


def _run():
    print("Parameter variants: duplicate bare param names use block identity")
    original_cwd = os.getcwd()
    target_yaml = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "targetBlock per-instance width (variant-bound block parameter)"}

blocks:
  targetBlock:
    desc: "Target block with WIDTH"
    params: [WIDTH]
"""
    other_yaml = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "otherBlock per-instance width (variant-bound block parameter)"}

blocks:
  otherBlock:
    desc: "Other visible block with WIDTH"
    params: [WIDTH]
"""
    target_path = _write_temp(target_yaml, '.yaml', 'param_ident_target_')
    other_path = _write_temp(other_yaml, '.yaml', 'param_ident_other_')
    arch_yaml = f"""include:
  - {os.path.basename(other_path)}
  - {os.path.basename(target_path)}

blocks:
  top:
    desc: "Top block"

instances:
  uTop: {{ container: top, instanceType: top }}
  uTarget: {{ container: top, instanceType: targetBlock, variant: wide }}
  uOther: {{ container: top, instanceType: otherBlock, variant: narrow }}

parameters:
  targetBlock:
    wide:
      WIDTH: 13
  otherBlock:
    narrow:
      WIDTH: 7
"""
    arch_path = _write_temp(arch_yaml, '.yaml', 'param_ident_arch_')
    project_yaml = f"""projectName: parameter_variant_identity_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(
        project_yaml, '_project.yaml', 'param_ident_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [project_path, arch_path, target_path, other_path, db_path]
    conn = None
    try:
        creator = projectCreate(project_path, db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        g.db = conn
        g.cur = conn.cursor()

        g.cur.execute(
            "SELECT blockKey FROM blocks WHERE block = ?", ('targetBlock',))
        target_block_key = g.cur.fetchone()['blockKey']
        g.cur.execute(
            "SELECT blockKey FROM blocks WHERE block = ?", ('otherBlock',))
        other_block_key = g.cur.fetchone()['blockKey']
        g.cur.execute(
            "SELECT blockparamKey, paramSourceKey FROM blocksparams "
            "WHERE blockKey = ? AND param = ?",
            (target_block_key, 'WIDTH'))
        target_row = g.cur.fetchone()
        target_param_key = target_row['blockparamKey']
        target_source_key = target_row['paramSourceKey']
        g.cur.execute(
            "SELECT blockparamKey, paramSourceKey FROM blocksparams "
            "WHERE blockKey = ? AND param = ?",
            (other_block_key, 'WIDTH'))
        other_row = g.cur.fetchone()
        other_param_key = other_row['blockparamKey']
        other_source_key = other_row['paramSourceKey']
        if target_source_key == other_source_key:
            print("FAIL: the two blocks' WIDTH params resolved to one backing constant")
            return False

        g.cur.execute(
            "SELECT param, blockParamKey, value FROM parametersvariantsparams "
            "WHERE blockKey = ? AND variant = ?",
            (target_block_key, 'wide'))
        variant_row = g.cur.fetchone()
        if variant_row['param'] != 'WIDTH':
            print(f"FAIL: expected bare param WIDTH, got {variant_row['param']}")
            return False
        if variant_row['blockParamKey'] != target_param_key:
            print(
                "FAIL: parametersvariants.blockParamKey should target "
                f"{target_param_key}, got {variant_row['blockParamKey']}")
            return False
        if variant_row['blockParamKey'] == other_param_key:
            print("FAIL: variant row resolved to the other block's WIDTH")
            return False

        # Bindings are seeded under the backing constant's own key, which is how
        # a payload width symbol reaches them. Two same-named params backed by
        # different constants must stay distinguishable.
        bindings = SiteBindingIndex(creator).bindingsAt(
            Site(target_block_key, 'wide', False), dict())
        if bindings.get(target_source_key) != 13:
            print(f"FAIL: binding {target_source_key} expected 13, "
                  f"got {bindings.get(target_source_key)}")
            return False
        if other_source_key in bindings:
            print("FAIL: variant bindings include the other block's WIDTH constant")
            return False
        print("PASS: parameter variant blockParamKey identity")
        return True
    except Exception as exc:
        print(f"FAIL: {exc}")
        return False
    finally:
        if conn is not None:
            conn.close()
        os.chdir(original_cwd)
        _cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
