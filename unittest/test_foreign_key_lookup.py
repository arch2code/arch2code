#!/usr/bin/env python3
"""Direct coverage for the projectCreate foreign-key lookup primitives.

Exercises `lookupInScope` and `validateForeignKey` against a parsed
project: plain-FK hit/miss, combo-FK hit/miss, _a2csystem fallback,
`scope: global` duplicate diagnostic, and the requirement that a raw
name containing `/` is treated as a literal."""

import os
import sqlite3
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate

g.disableColors = True


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


def _build_project():
    """Build a minimal multi-file project that exercises every lookup
    branch we want to test."""
    types_yaml = """types:
  width16_t:
    desc: "16-bit width type defined in an included file"
    width: 16
"""
    types_path = _write_temp(types_yaml, '.yaml', 'fk_types_')
    # A duplicate object for the scope: global duplicate-diagnostic case. It is a
    # TYPE (not a block) on purpose: two same-named blocks in one project resolve
    # to one qualified SystemVerilog module name and are rejected by the
    # per-block module-name uniqueness gate at db-creation, so a duplicate-block
    # project no longer builds. A duplicate type carries no such gate, so the
    # project builds and _lookupInGlobal's duplicate path is still exercised.
    duplicate_type_yaml = """types:
  sharedType:
    desc: "Type defined in duplicate-A; same name lives in duplicate-B"
    width: 8
"""
    duplicate_a_path = _write_temp(
        duplicate_type_yaml, '.yaml', 'fk_dup_a_')
    duplicate_b_path = _write_temp(
        duplicate_type_yaml, '.yaml', 'fk_dup_b_')
    arch_yaml = f"""include:
  - {os.path.basename(types_path)}
  - {os.path.basename(duplicate_a_path)}
  - {os.path.basename(duplicate_b_path)}

ipParameters:
  constants:
    WIDTH:
      value: 13
      maxValue: 13
      desc: "Backing parameter constant for leafBlock.WIDTH"

blocks:
  leafBlock:
    desc: "Leaf with a parameter"
    params: [WIDTH]
  topBlock:
    desc: "Top block"

instances:
  uTop: {{ container: topBlock, instanceType: topBlock }}
  uLeaf: {{ container: topBlock, instanceType: leafBlock, variant: wide }}

parameters:
  leafBlock:
    wide:
      WIDTH: 13
"""
    arch_path = _write_temp(arch_yaml, '.yaml', 'fk_arch_')
    project_yaml = f"""projectName: fk_lookup_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(
        project_yaml, '_project.yaml', 'fk_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    paths = [
        project_path, arch_path, types_path,
        duplicate_a_path, duplicate_b_path, db_path,
    ]
    return project_path, db_path, paths, arch_path, types_path


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


def _run():
    print("Foreign-key lookup primitives")
    original_cwd = os.getcwd()
    (project_path, db_path, paths,
     arch_path, types_path) = _build_project()
    arch_context = os.path.basename(arch_path)
    types_context = os.path.basename(types_path)
    conn = None
    results = []
    try:
        creator = projectCreate(project_path, db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        g.db = conn
        g.cur = conn.cursor()

        def plain_fk_hit():
            # types are loaded from an included file; the lookup must
            # walk the arch file's include chain to reach types_path.
            row, qualification = creator.lookupInScope(
                'types', arch_context, 'width16_t')
            return row is not None \
                and row['type'] == 'width16_t' \
                and qualification == types_context

        def plain_fk_miss():
            row, qualification = creator.lookupInScope(
                'types', arch_context, 'no_such_type')
            return row is None and qualification is None

        def a2csystem_fallback():
            # apb is defined in $a2c/interfaces/apb/apb_if.yaml which
            # the standard project.yaml loads into the _a2csystem
            # context. The user file does not include it directly.
            row, qualification = creator.lookupInScope(
                'interface_defs', arch_context, 'apb')
            return row is not None \
                and row['interface_type'] == 'apb' \
                and qualification == '_a2csystem'

        def raw_name_with_slash():
            # A name containing '/' must be treated literally. Today's
            # store has no such literal, so the call must return
            # (None, None) without splitting and resolving the right
            # half as a qualification.
            row, qualification = creator.lookupInScope(
                'types', arch_context, 'width16_t/' + types_context)
            return row is None and qualification is None

        def global_duplicate_diagnostic():
            # sharedType is defined in both duplicate-A and duplicate-B
            # files, so a `scope: global` lookup must record an error
            # via printError while still returning the last match.
            before = g.errorCount
            row, qualification = creator.lookupInScope(
                'types', 'global', 'sharedType')
            after = g.errorCount
            return row is not None and after > before

        def _validator_for(section, field):
            return creator.schema.data['validator'][section + field]

        def combo_fk_hit():
            # parameters.variants.params.blockParam is a combo FK over
            # (block, param) validating against blocksparams.blockparam.
            # The arch yaml binds leafBlock.WIDTH to 13; the same
            # source row must resolve back to the matching blocksparams
            # entry.
            source_row = {'block': 'leafBlock', 'param': 'WIDTH'}
            validator = _validator_for('parametersvariantsparams', 'blockParam')
            row, qualification = creator.validateForeignKey(
                source_row, 'parametersvariantsparams', 'blockParam',
                arch_context)
            return row is not None \
                and validator['section'] == 'blocksparams' \
                and row['block'] == 'leafBlock' \
                and row['param'] == 'WIDTH' \
                and qualification == arch_context

        def combo_fk_miss():
            source_row = {'block': 'leafBlock', 'param': 'NOT_DECLARED'}
            row, qualification = creator.validateForeignKey(
                source_row, 'parametersvariantsparams', 'blockParam',
                arch_context)
            return row is None and qualification is None

        def plain_fk_validate():
            # validateForeignKey's plain branch routes through
            # lookupInScope. Use the structures.vars.varType validator
            # (plain FK against types.type).
            source_row = {'varType': 'width16_t'}
            row, qualification = creator.validateForeignKey(
                source_row, 'structuresvars', 'varType', arch_context)
            return row is not None \
                and row['type'] == 'width16_t' \
                and qualification == types_context

        results.append(_run_case("plain-FK hit", plain_fk_hit))
        results.append(_run_case("plain-FK miss", plain_fk_miss))
        results.append(_run_case("_a2csystem fallback", a2csystem_fallback))
        results.append(_run_case(
            "raw name with '/' is literal", raw_name_with_slash))
        results.append(_run_case(
            "global duplicate diagnostic", global_duplicate_diagnostic))
        results.append(_run_case("combo-FK hit", combo_fk_hit))
        results.append(_run_case("combo-FK miss", combo_fk_miss))
        results.append(_run_case(
            "validateForeignKey plain branch", plain_fk_validate))
        return all(results)
    except Exception as exc:
        print(f"FAIL: setup raised {exc}")
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
