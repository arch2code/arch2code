#!/usr/bin/env python3
"""A registrar file left behind when a pair child is renamed to a different
block is never removed by `gen` (which only rewrites generated regions of
files that already exist) or by `migrateOrphans` (which skips registrar-mode
entries by design). It lingers in the registrar directory and can shadow a
container-typed factory site.

Copies `inherit-vl-child`, trims it to one container instance and one leaf
variant (the same shape `test_container_param_vl_wrapper_migration.py`
scaffolds), then renames the leaf block `vliLeaf` -> `leaf` in place: the
container keeps assembling a leaf, but under a new childKey, so the old
`vliLeafRegistrar.cppm`/`vliLeafVlRegistrar.cpp` become stale.

Two scenarios:
  - `_run_newmodule_cleanup`: `make db newmodule gen` after the rename
    removes the stale files and scaffolds the new ones.
  - `_run_warning_path`: `make db gen` alone (no newmodule) leaves the stale
    files in place but warns about them and recommends `make newmodule`;
    running `make newmodule` then removes them, and a following `make gen`
    warns about nothing.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'inherit-vl-child')

# One container instance, one leaf variant: the minimal shape that gives
# vliCont a real registrar pair with vliLeaf.
TRIMMED_TAIL = """instances:
    vliTop_tb: { container: vliTop_tb, instanceType: vliTop_tb, instGroup: top }
    u_vliTop:  { container: vliTop_tb, instanceType: vliTop,    instGroup: top }
    uWrap:       { container: vliTop,    instanceType: vliWrap,   instGroup: top }
    uDrvDef:     { container: vliWrap,   instanceType: vliDrv,    instGroup: top, variant: drvDef }
    uContDef:    { container: vliWrap,   instanceType: vliCont,   instGroup: top, variant: default }
    uChkDef:     { container: vliWrap,   instanceType: vliChk,    instGroup: top, variant: chkDef }
    uLeafA:      { container: vliCont,   instanceType: vliLeaf,   instGroup: top, variant: default }
    uLeafB:      { container: vliCont,   instanceType: vliLeaf,   instGroup: top, variant: default }

connections:
    - { interface: vliIf, src: uLeafA,   srcport: out,     dst: uLeafB,   dstport: in,     name: contLink }
    - { interface: vliIf, src: uDrvDef,  srcport: out,     dst: uContDef, dstport: contIn }
    - { interface: vliIf, src: uContDef, srcport: contOut, dst: uChkDef,  dstport: in }

connectionMaps:
    - { interface: vliIf, block: vliCont, port: contIn,  direction: dst, instance: uLeafA, instancePort: in }
    - { interface: vliIf, block: vliCont, port: contOut, direction: src, instance: uLeafB, instancePort: out }

parameters:
    vliCont:
        default:
            VLI_ALGO: VLI_ALGO
            VLI_WIDTH: VLI_WIDTH
    vliLeaf:
        default:
            VLI_ALGO: 1
            VLI_WIDTH: 8
    vliDrv:
        drvDef:
            VLI_WIDTH: VLI_WIDTH
    vliChk:
        chkDef:
            VLI_ALGO: VLI_ALGO
            VLI_WIDTH: VLI_WIDTH
"""


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def write_tail(project):
    yamlPath = os.path.join(project, 'yaml', 'vliCont.yaml')
    with open(yamlPath) as f:
        text = f.read()
    head = text[:text.index('instances:')]
    with open(yamlPath, 'w') as f:
        f.write(head + TRIMMED_TAIL)


def rename_leaf_block(project, newName):
    # A block rename (not merely an instance label): the childKey `vliCont`
    # pairs with changes, so the registrar files the old childKey produced are
    # no longer part of the current contract.
    yamlPath = os.path.join(project, 'yaml', 'vliCont.yaml')
    with open(yamlPath) as f:
        text = f.read()
    with open(yamlPath, 'w') as f:
        f.write(text.replace('vliLeaf', newName))


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(targets, project, e):
    # make does not serialize independent phony targets under -j, so each
    # target here is its own invocation; the combined output and the last
    # invocation's returncode are returned (mirrors piping several `make`
    # calls into one log).
    text = ''
    returncode = 0
    for target in targets:
        cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
               '-j8', target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)
        text += result.stdout + result.stderr
        returncode = result.returncode
        if result.returncode != 0:
            break
    return text, returncode


def require_make(targets, project, e):
    text, returncode = make(targets, project, e)
    if returncode != 0:
        raise RuntimeError(f"make {' '.join(targets)} failed:\n{text}")
    return text


def _prepare_renamed_project(tmp):
    project = os.path.join(tmp, 'vli')
    copy_fixture(project)
    write_tail(project)
    e = env()

    baseline = require_make(['clean', 'db', 'newmodule', 'gen'], project, e)
    if 'stale registrar' in baseline.lower():
        raise RuntimeError(
            f"fresh scaffold already reports a stale registrar file:\n{baseline}")

    registrarDir = os.path.join(project, 'registrar')
    oldRegistrar = os.path.join(registrarDir, 'vliLeafRegistrar.cppm')
    oldRegistrarVl = os.path.join(registrarDir, 'vliLeafVlRegistrar.cpp')
    if not os.path.exists(oldRegistrar):
        raise RuntimeError(f"expected {oldRegistrar} to be scaffolded")
    if not os.path.exists(oldRegistrarVl):
        raise RuntimeError(f"expected {oldRegistrarVl} to be scaffolded")

    rename_leaf_block(project, 'leaf')
    newRegistrar = os.path.join(registrarDir, 'leafRegistrar.cppm')
    newRegistrarVl = os.path.join(registrarDir, 'leafVlRegistrar.cpp')
    return project, e, oldRegistrar, newRegistrar, oldRegistrarVl, newRegistrarVl


def _run_newmodule_cleanup():
    tmp = tempfile.mkdtemp(prefix='stale_registrar_newmodule_', dir=test_dir)
    try:
        project, e, oldRegistrar, newRegistrar, oldRegistrarVl, newRegistrarVl = \
            _prepare_renamed_project(tmp)

        require_make(['db', 'newmodule', 'gen'], project, e)

        if os.path.exists(oldRegistrar):
            print(f"FAIL: newmodule left the stale file {oldRegistrar} in place")
            return False
        if os.path.exists(oldRegistrarVl):
            print(f"FAIL: newmodule left the stale file {oldRegistrarVl} in place")
            return False
        if not os.path.exists(newRegistrar):
            print(f"FAIL: newmodule did not scaffold {newRegistrar}")
            return False
        if not os.path.exists(newRegistrarVl):
            print(f"FAIL: newmodule did not scaffold {newRegistrarVl}")
            return False

        print("PASS: newmodule removed the stale registrar files left behind by "
              "the pair child's rename and scaffolded the renamed ones")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_warning_path():
    tmp = tempfile.mkdtemp(prefix='stale_registrar_warning_', dir=test_dir)
    try:
        project, e, oldRegistrar, _, _, _ = _prepare_renamed_project(tmp)

        # gen alone (no newmodule) must warn about the stale file and leave it
        # in place; only newmodule deletes.
        combined = require_make(['db', 'gen'], project, e)
        if 'stale registrar file' not in combined or oldRegistrar not in combined:
            print(f"FAIL: gen output does not warn about {oldRegistrar}:\n{combined}")
            return False
        if 'make newmodule' not in combined:
            print(f"FAIL: gen output does not recommend 'make newmodule':\n{combined}")
            return False
        if not os.path.exists(oldRegistrar):
            print("FAIL: gen alone deleted the stale file; only newmodule should")
            return False

        require_make(['newmodule'], project, e)
        if os.path.exists(oldRegistrar):
            print(f"FAIL: newmodule did not remove {oldRegistrar}")
            return False

        combined = require_make(['gen'], project, e)
        if 'stale registrar' in combined.lower():
            print(f"FAIL: gen still warns after newmodule cleaned up:\n{combined}")
            return False

        print("PASS: gen warns about the stale registrar file and recommends "
              "newmodule; newmodule removes it and gen then warns of nothing")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    cleanup = _run_newmodule_cleanup()
    warning = _run_warning_path()
    return 0 if cleanup and warning else 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
