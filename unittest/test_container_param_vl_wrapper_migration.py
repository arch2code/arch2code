#!/usr/bin/env python3
"""A block whose only variant is fully container-sourced, and shares its
container's own variant label, still gets a buildable verilated wrapper.

Copies `inherit-vl-child`, trims it to one leaf variant named `default`
(matching the container's `default`), scaffolds the wrapper while that
variant is still literal-valued, migrates it to `containerParam:` in place,
and regenerates without re-scaffolding. Asserts the regenerated `.sv` defines
exactly one module, the pair-qualified concrete top, and that the build
manifest records no bare `<block>_hdl_sv_wrapper` top for it. Db and
generation only; the product's own `make -j all VL_DUT=1` and run are the
end-to-end proof for this shape.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'inherit-vl-child')

# Everything from `instances:` to end of file, trimmed to one container
# instance (`uContDef`, variant `default`) and one leaf variant, ALSO named
# `default`: the `alt` container variant and the `solo` leaf variant are
# dropped, since either one keeps `vliLeaf`'s variant set non-empty and hides
# the defects under test.
TRIMMED_TAIL_TEMPLATE = """instances:
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
__LEAF_DEFAULT_VALUES__
    vliDrv:
        drvDef:
            VLI_WIDTH: VLI_WIDTH
    vliChk:
        chkDef:
            VLI_ALGO: VLI_ALGO
            VLI_WIDTH: VLI_WIDTH
"""

# Phase 1: the variant looks standalone, so `make newmodule` scaffolds its
# wrapper top the ordinary way (no `--mode=pair` stamp).
LITERAL_DEFAULT = """        default:
            VLI_ALGO: 1
            VLI_WIDTH: 8
"""

# Phase 2: the same variant, migrated in place to containerParam:, exactly as
# `yaml/debayer.yaml` migrated `preprocess`/`interpolate`. The already-
# scaffolded file is not re-created.
CONTAINERPARAM_DEFAULT = """        default:
            VLI_ALGO:  { containerParam: VLI_ALGO }
            VLI_WIDTH: { containerParam: VLI_WIDTH }
"""


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def write_tail(project, leaf_default_values):
    yamlPath = os.path.join(project, 'yaml', 'vliCont.yaml')
    with open(yamlPath) as f:
        text = f.read()
    head = text[:text.index('instances:')]
    tail = TRIMMED_TAIL_TEMPLATE.replace(
        '__LEAF_DEFAULT_VALUES__', leaf_default_values)
    with open(yamlPath, 'w') as f:
        f.write(head + tail)


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(target, project, e, extra=()):
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           '-j8']
    cmd.extend(extra)
    cmd.append(target)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)


def require_make(target, project, e, extra=()):
    result = make(target, project, e, extra=extra)
    if result.returncode != 0:
        raise RuntimeError(
            f"make {target} failed:\n{result.stdout}\n{result.stderr}")
    return result


WRAPPER_SV = 'vliLeaf_default_hdl_sv_wrapper.sv'
BARE_TOP = 'vliLeaf_hdl_sv_wrapper'


def _run():
    e = env()
    tmp = tempfile.mkdtemp(prefix='container_param_vl_wrapper_migration_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'vli')
        copy_fixture(project)

        # Phase 1: scaffold while the leaf's `default` still looks standalone.
        write_tail(project, LITERAL_DEFAULT)
        require_make('clean', project, e)
        require_make('db', project, e)
        require_make('newmodule', project, e)
        require_make('gen', project, e)
        wrapperPath = os.path.join(project, 'verif', WRAPPER_SV)
        if not os.path.exists(wrapperPath):
            print(f"FAIL: phase 1 did not scaffold {WRAPPER_SV}")
            return False
        with open(wrapperPath) as f:
            phase1 = f.read()
        if '--mode=pair' in phase1:
            print("FAIL: phase 1 wrapper scaffolded with --mode=pair; "
                  "this fixture no longer reproduces the migration")
            return False

        # Phase 2: migrate the leaf's `default` to containerParam: in place,
        # regenerate without re-scaffolding.
        write_tail(project, CONTAINERPARAM_DEFAULT)
        require_make('db', project, e)
        require_make('gen', project, e)

        buildMk = os.path.join(project, '.gen', 'build.mk')
        with open(buildMk) as f:
            manifest = f.read()
        topsLine = next(line for line in manifest.splitlines()
                        if line.startswith('A2C_VL_TOPS'))
        tops = topsLine.split(':=', 1)[1].split()

        ok = True
        if BARE_TOP in tops:
            print(f"FAIL: manifest still records the phantom bare top "
                  f"'{BARE_TOP}' ({topsLine})")
            ok = False

        pairTops = [t for t in tops if t.endswith('_default_hdl_sv_wrapper')
                   and 'vliLeaf' in t]
        if len(pairTops) != 1:
            print(f"FAIL: expected exactly one pair-qualified leaf top, "
                  f"found {pairTops} in {topsLine}")
            return False
        pairTop = pairTops[0]

        svVar = f'A2C_VL_SV_{pairTop}'
        svLine = next((line for line in manifest.splitlines()
                      if line.startswith(svVar)), None)
        if svLine is None:
            print(f"FAIL: manifest has no {svVar} entry")
            ok = False
        elif not svLine.split(':=', 1)[1].strip().endswith(WRAPPER_SV):
            print(f"FAIL: {svVar} does not point at {WRAPPER_SV}: {svLine}")
            ok = False

        with open(wrapperPath) as f:
            phase2 = f.read()
        modules = [line for line in phase2.splitlines()
                  if line.startswith('module ')]
        if modules != [f'module {pairTop}']:
            print(f"FAIL: {WRAPPER_SV} defines {modules}, expected exactly "
                  f"['module {pairTop}']")
            ok = False
        if f'endmodule : {pairTop}' not in phase2:
            print(f"FAIL: {WRAPPER_SV} has no matching endmodule for {pairTop}")
            ok = False

        if ok:
            print(f"PASS: the migrated leaf variant regenerates as the sole "
                  f"pair-qualified module '{pairTop}', sharing the container's "
                  f"physical file with no phantom bare top")
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
