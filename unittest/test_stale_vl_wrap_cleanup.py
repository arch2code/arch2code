#!/usr/bin/env python3
"""A vl_wrap file left behind when a block or a declared variant is renamed is
never removed by `gen` (which only rewrites generated regions of files that
already exist) or by `migrateOrphans` (which does not walk the vl_wrap
segment). It lingers in verif/vl_wrap and can shadow a Verilator top a fresh
build would otherwise name identically.

Copies `inherit-vl-child`, trims it to one container instance and one leaf
variant (the same shape `test_stale_registrar_cleanup.py` scaffolds), then
exercises two renames in turn:
  - the leaf's declared variant label, so its per-variant
    `<block>_<variant>_hdl_sv_wrapper.sv` top becomes stale;
  - the leaf block itself, so all three of its vl_wrap files
    (`_hdl_sv_wrapper.sv`, `_hdl_sv_wrapper.svh`, `_hdl_sc_wrapper.h`) and its
    registrar files become stale.

For each rename: `make db gen` alone warns about the stale files and leaves
them in place; a following `make newmodule` removes them and a `make gen`
after that warns of nothing. A hand-authored file with no GENERATED_CODE
marker dropped into verif/vl_wrap survives every pass.

A stale vl_wrap file is removed only while its text outside the generated
regions is what the scaffold writes. In the block rename, the stale SC wrapper
header first carries user code in its end_ctor_init() body: newmodule keeps
and reports it while still removing the untouched stale files and the stale
registrar files. Once the header is restored to its scaffold text, newmodule
removes it.

Turning the leaf's `hasVl` off makes the same files stale without a rename:
`make newmodule` removes the vl_wrap files and the Verilator registrar, keeps
the model registrar, and the rundir build stops compiling the Verilator
registrar.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'inherit-vl-child')

# One container instance, one leaf variant, distinct labels for the container
# and the leaf so a rename of one cannot collide with a blind replace of the
# other.
TRIMMED_TAIL = """instances:
    vliTop_tb: { container: vliTop_tb, instanceType: vliTop_tb, instGroup: top }
    u_vliTop:  { container: vliTop_tb, instanceType: vliTop,    instGroup: top }
    uWrap:       { container: vliTop,    instanceType: vliWrap,   instGroup: top }
    uDrvDef:     { container: vliWrap,   instanceType: vliDrv,    instGroup: top, variant: drvDef }
    uContDef:    { container: vliWrap,   instanceType: vliCont,   instGroup: top, variant: contDef }
    uChkDef:     { container: vliWrap,   instanceType: vliChk,    instGroup: top, variant: chkDef }
    uLeafA:      { container: vliCont,   instanceType: vliLeaf,   instGroup: top, variant: leafVar }
    uLeafB:      { container: vliCont,   instanceType: vliLeaf,   instGroup: top, variant: leafVar }

connections:
    - { interface: vliIf, src: uLeafA,   srcport: out,     dst: uLeafB,   dstport: in,     name: contLink }
    - { interface: vliIf, src: uDrvDef,  srcport: out,     dst: uContDef, dstport: contIn }
    - { interface: vliIf, src: uContDef, srcport: contOut, dst: uChkDef,  dstport: in }

connectionMaps:
    - { interface: vliIf, block: vliCont, port: contIn,  direction: dst, instance: uLeafA, instancePort: in }
    - { interface: vliIf, block: vliCont, port: contOut, direction: src, instance: uLeafB, instancePort: out }

parameters:
    vliCont:
        contDef:
            VLI_ALGO: VLI_ALGO
            VLI_WIDTH: VLI_WIDTH
    vliLeaf:
        leafVar:
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


def rename_leaf_variant(project, newLabel):
    # A variant-label rename (not a block rename): the leaf's own declared
    # `leafVar` variant becomes a different label, so the old
    # `vliLeaf_leafVar_hdl_sv_wrapper.sv` top is no longer part of the
    # contract.
    yamlPath = os.path.join(project, 'yaml', 'vliCont.yaml')
    with open(yamlPath) as f:
        text = f.read()
    with open(yamlPath, 'w') as f:
        f.write(text.replace('leafVar', newLabel))


def rename_leaf_block(project, newName):
    # A block rename: every vl_wrap file named for the leaf (the per-variant
    # top, the shared wrapper body, and the SC wrapper header) becomes stale,
    # alongside its registrar files.
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


def _prepare_project(tmp, name):
    project = os.path.join(tmp, name)
    copy_fixture(project)
    write_tail(project)
    e = env()

    # The committed fixture's own verif/vl_wrap files are scaffolded for its
    # untrimmed variant set; trimming leaves a leftover the baseline scaffold
    # itself cleans up, so only file presence/absence is asserted here, not
    # the absence of the word "stale" in this combined log.
    require_make(['clean', 'db', 'newmodule', 'gen'], project, e)

    vlWrapDir = os.path.join(project, 'verif')
    dummy = os.path.join(vlWrapDir, 'vl_dummy.sv')
    with open(dummy, 'w') as f:
        f.write('// hand-authored, no GENERATED_CODE marker\nmodule vl_dummy; endmodule\n')

    expected = {
        'sv':  os.path.join(vlWrapDir, 'vliLeaf_leafVar_hdl_sv_wrapper.sv'),
        'svh': os.path.join(vlWrapDir, 'vliLeaf_hdl_sv_wrapper.svh'),
        'h':   os.path.join(vlWrapDir, 'vliLeaf_hdl_sc_wrapper.h'),
    }
    for kind, path in expected.items():
        if not os.path.exists(path):
            raise RuntimeError(f"expected baseline {kind} wrapper {path} to be scaffolded")
    return project, e, vlWrapDir, dummy, expected


def _run_variant_rename():
    tmp = tempfile.mkdtemp(prefix='stale_vl_wrap_variant_', dir=test_dir)
    try:
        project, e, vlWrapDir, dummy, expected = _prepare_project(tmp, 'vliVariant')
        oldTop = expected['sv']
        newTop = os.path.join(vlWrapDir, 'vliLeaf_leafVar2_hdl_sv_wrapper.sv')
        rename_leaf_variant(project, 'leafVar2')

        # gen alone (no newmodule) must warn about the stale top and leave it
        # in place.
        combined = require_make(['db', 'gen'], project, e)
        if 'stale vl_wrap file' not in combined or oldTop not in combined:
            print(f"FAIL: gen output does not warn about {oldTop}:\n{combined}")
            return False
        if 'make newmodule' not in combined:
            print(f"FAIL: gen output does not recommend 'make newmodule':\n{combined}")
            return False
        if not os.path.exists(oldTop):
            print("FAIL: gen alone deleted the stale top; only newmodule should")
            return False

        require_make(['newmodule'], project, e)
        if os.path.exists(oldTop):
            print(f"FAIL: newmodule did not remove {oldTop}")
            return False
        if not os.path.exists(newTop):
            print(f"FAIL: newmodule did not scaffold {newTop}")
            return False

        combined = require_make(['gen'], project, e)
        if 'stale vl_wrap' in combined.lower():
            print(f"FAIL: gen still warns after newmodule cleaned up:\n{combined}")
            return False

        if not os.path.exists(dummy):
            print(f"FAIL: hand-authored {dummy} did not survive the variant rename")
            return False

        print("PASS: a leaf variant rename leaves a stale vl_wrap top that gen "
              "warns about and newmodule replaces; the hand-authored file survives")
        return True
    finally:
        remove_tree(tmp)


def _run_block_rename():
    tmp = tempfile.mkdtemp(prefix='stale_vl_wrap_block_', dir=test_dir)
    try:
        project, e, vlWrapDir, dummy, expected = _prepare_project(tmp, 'vliBlock')
        oldFiles = list(expected.values())
        newFiles = [
            os.path.join(vlWrapDir, 'leaf_leafVar_hdl_sv_wrapper.sv'),
            os.path.join(vlWrapDir, 'leaf_hdl_sv_wrapper.svh'),
            os.path.join(vlWrapDir, 'leaf_hdl_sc_wrapper.h'),
        ]
        registrarDir = os.path.join(project, 'registrar')
        oldRegistrar = os.path.join(registrarDir, 'vliLeafRegistrar.cppm')
        if not os.path.exists(oldRegistrar):
            print(f"FAIL: expected baseline registrar file {oldRegistrar}")
            return False
        rename_leaf_block(project, 'leaf')

        combined = require_make(['db', 'gen'], project, e)
        for oldFile in oldFiles:
            if 'stale vl_wrap file' not in combined or oldFile not in combined:
                print(f"FAIL: gen output does not warn about {oldFile}:\n{combined}")
                return False
        if 'make newmodule' not in combined:
            print(f"FAIL: gen output does not recommend 'make newmodule':\n{combined}")
            return False
        for oldFile in oldFiles:
            if not os.path.exists(oldFile):
                print(f"FAIL: gen alone deleted {oldFile}; only newmodule should")
                return False

        # User code in the stale SC wrapper's end_ctor_init() body.
        scWrap = expected['h']
        with open(scWrap) as f:
            scaffoldText = f.read()
        hook = '        // Register synchLock,...\n'
        if hook not in scaffoldText:
            print(f"FAIL: {scWrap} does not carry the scaffold's end_ctor_init() body")
            return False
        with open(scWrap, 'w') as f:
            f.write(scaffoldText.replace(hook, hook + '        userSetup();\n'))

        combined = require_make(['newmodule'], project, e)
        if not os.path.exists(scWrap):
            print(f"FAIL: newmodule deleted {scWrap}, which holds user code")
            return False
        if 'kept stale vl_wrap file' not in combined or scWrap not in combined:
            print(f"FAIL: newmodule did not report keeping {scWrap}:\n{combined}")
            return False
        for oldFile in oldFiles:
            if oldFile != scWrap and os.path.exists(oldFile):
                print(f"FAIL: newmodule did not remove {oldFile}")
                return False
        if os.path.exists(oldRegistrar):
            print(f"FAIL: newmodule did not remove the stale registrar file {oldRegistrar}")
            return False

        with open(scWrap, 'w') as f:
            f.write(scaffoldText)
        require_make(['newmodule'], project, e)
        if os.path.exists(scWrap):
            print(f"FAIL: newmodule did not remove the untouched stale header {scWrap}")
            return False
        for newFile in newFiles:
            if not os.path.exists(newFile):
                print(f"FAIL: newmodule did not scaffold {newFile}")
                return False

        combined = require_make(['gen'], project, e)
        if 'stale vl_wrap' in combined.lower():
            print(f"FAIL: gen still warns after newmodule cleaned up:\n{combined}")
            return False

        if not os.path.exists(dummy):
            print(f"FAIL: hand-authored {dummy} did not survive the block rename")
            return False

        print("PASS: a leaf block rename leaves stale vl_wrap files that gen "
              "warns about and newmodule replaces, keeping a stale header that "
              "holds user code until it is restored; the stale registrar files "
              "and the hand-authored file are handled as before")
        return True
    finally:
        remove_tree(tmp)


def systemc_sources(project, e):
    # The rundir build compiles every registrar/*.cpp it finds, so CPP_SRC is
    # what a stale Verilator registrar would be compiled from.
    cmd = ['make', '-C', os.path.join(project, 'rundir'), '--no-print-directory',
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           '--eval', 'a2cPrintCppSrc: ; @echo CPP_SRC=$(CPP_SRC)', 'a2cPrintCppSrc']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)
    if result.returncode != 0:
        raise RuntimeError(f"CPP_SRC probe failed:\n{result.stdout}{result.stderr}")
    lines = [line for line in result.stdout.splitlines() if line.startswith('CPP_SRC=')]
    return lines[-1].split()


def _run_hasvl_flip():
    tmp = tempfile.mkdtemp(prefix='stale_vl_wrap_hasvl_', dir=test_dir)
    try:
        project, e, vlWrapDir, dummy, expected = _prepare_project(tmp, 'vliFlip')
        registrarDir = os.path.join(project, 'registrar')
        vlRegistrar = os.path.join(registrarDir, 'vliLeafVlRegistrar.cpp')
        modelRegistrar = os.path.join(registrarDir, 'vliLeafRegistrar.cppm')
        for path in (vlRegistrar, modelRegistrar):
            if not os.path.exists(path):
                print(f"FAIL: expected baseline registrar file {path}")
                return False
        if vlRegistrar not in systemc_sources(project, e):
            print(f"FAIL: the baseline build does not compile {vlRegistrar}, so the "
                  f"probe cannot show it dropping out")
            return False

        yamlPath = os.path.join(project, 'yaml', 'vliCont.yaml')
        with open(yamlPath) as f:
            text = f.read()
        if text.count('hasVl: true') != 1:
            print("FAIL: expected vliLeaf to be the fixture's only hasVl: true block")
            return False
        with open(yamlPath, 'w') as f:
            f.write(text.replace('hasVl: true', 'hasVl: false'))

        require_make(['db', 'newmodule', 'gen'], project, e)
        for path in list(expected.values()) + [vlRegistrar]:
            if os.path.exists(path):
                print(f"FAIL: newmodule left {path} after hasVl was turned off")
                return False
        if not os.path.exists(modelRegistrar):
            print(f"FAIL: newmodule removed the model registrar {modelRegistrar}, "
                  f"which hasVl does not govern")
            return False
        if vlRegistrar in systemc_sources(project, e):
            print(f"FAIL: the build still compiles {vlRegistrar}")
            return False
        if not os.path.exists(dummy):
            print(f"FAIL: hand-authored {dummy} did not survive the hasVl flip")
            return False

        print("PASS: turning hasVl off and running newmodule removes the leaf's "
              "vl_wrap files and Verilator registrar, the build no longer compiles "
              "the registrar, and the model registrar and hand-authored file stay")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    variant = _run_variant_rename()
    block = _run_block_rename()
    flip = _run_hasvl_flip()
    return 0 if variant and block and flip else 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
