#!/usr/bin/env python3
"""Run a containerParam Verilated child owned by another project.

The fixture is a private copy of xprojParam's depth family. The assembler owns
the container Configs and xpDpLeaf owns the child block. The copied leaf enables
hasVl, then the normal make workflow scaffolds and generates its wrapper.

Two runs select one scalar --vlInst each. The selected leaves sit under
different xpDpMid Configs, so their RTL stamps algorithms 5 and 6 respectively.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from pysrc import intf_gen_utils
from pysrc.processYaml import projectOpen


SOURCE_ROOT = os.path.join(base_dir, 'examples', 'xprojParam')
PROJECTS = ('dpLeaf', 'dpMid', 'dpTop')
BUILD_JOBS = '8'
SAMPLE_COUNT = 4
SELECTED = {
    'customer': ('tb.xpDpTop.uWrap.uMid.uLeafB', 'uChk', 5),
    'customer2': ('tb.xpDpTop.uWrap.uMid2.uLeafB', 'uChk2', 6),
}


def toolchain_env():
    env = os.environ.copy()
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE', 'LD_BOOST'):
        if not env.get(var):
            raise RuntimeError(f"{var} is not set")
    if shutil.which('verilator') is None:
        raise RuntimeError("verilator is not on PATH")
    env['NO_COLOR'] = '1'
    return env


def copy_fixture():
    work = tempfile.mkdtemp(prefix='container_param_xproj_vl_', dir=test_dir)
    for name in PROJECTS:
        src = os.path.join(SOURCE_ROOT, name)
        dst = os.path.join(work, name)
        shutil.copytree(
            src, dst,
            ignore=shutil.ignore_patterns(
                'build', '.gen', 'base', 'registrar', 'verif',
                '*.db', '*.db-*'))
        for relpath in ('Makefile', 'rundir/Makefile', 'rtl/Makefile',
                        'include/make/shared.mk'):
            path = os.path.join(dst, relpath)
            if not os.path.exists(path):
                continue
            with open(path) as f:
                text = f.read()
            lines = text.splitlines(keepends=True)
            matches = [i for i, line in enumerate(lines)
                       if line.startswith('REPO_ROOT = ')]
            if len(matches) != 1:
                raise AssertionError(
                    f"{relpath} in {name} does not have one REPO_ROOT assignment")
            lines[matches[0]] = f'REPO_ROOT = {dst}\n'
            with open(path, 'w') as f:
                f.write(''.join(lines))
    return work


def make(project, target, env, *, directory=None, extra=()):
    cmd = ['make', '-C', directory or project, f'-j{BUILD_JOBS}']
    cmd.extend(extra)
    cmd.append(target)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=env)


def require_make(project, target, env, *, directory=None, extra=()):
    result = make(project, target, env, directory=directory, extra=extra)
    if result.returncode != 0:
        raise AssertionError(
            f"make {target} failed in {directory or project}:\n"
            f"{result.stdout}\n{result.stderr}")
    return result


def enable_leaf_vl(leaf):
    yaml = os.path.join(leaf, 'yaml', 'xpDpLeaf.yaml')
    with open(yaml) as f:
        text = f.read()
    old = '        hasVl: false\n        hasTb: false\n'
    new = '        hasVl: true\n        hasTb: false\n'
    if text.count(old) != 1:
        raise AssertionError("xpDpLeaf hasVl anchor changed")
    with open(yaml, 'w') as f:
        f.write(text.replace(old, new, 1))


def make_parent_the_assembler(work):
    top = os.path.join(work, 'dpTop')
    mid_model = os.path.join(work, 'dpMid', 'model')
    for name in ('xpDpMidStdWrap.cppm', 'xpDpMidStdTop.cppm',
                 'xpDpMidSnk.cppm', 'xpDpMidDrv.cppm'):
        os.unlink(os.path.join(mid_model, name))
    project_yaml = os.path.join(top, 'prj', 'yaml', 'xpDpTopProject.yaml')
    with open(project_yaml) as f:
        text = f.read()
    old = '    - ../../../dpMid/prj/yaml/xpDpMidProject.yaml\n'
    new = '    - ../../../dpLeaf/prj/yaml/xpDpLeafProject.yaml\n'
    if text.count(old) != 1:
        raise AssertionError("xpDpTop project reference anchor changed")
    with open(project_yaml, 'w') as f:
        f.write(text.replace(old, new, 1))

    top_yaml = os.path.join(top, 'yaml', 'xpDpTop.yaml')
    with open(top_yaml) as f:
        text = f.read()
    removals = (
        '            out2: { interface: dpIf, direction: src }\n',
        '    uLeafX:     { container: xpDpWrap,   instanceType: xpDpLeaf,   instGroup: top, variant: leafX }\n',
        '    uChkX:      { container: xpDpWrap,   instanceType: xpDpChk,    instGroup: top, variant: leafX }\n',
        '    - { interface: dpIf, src: uSrc, srcport: out2, dst: uLeafX, dstport: in }\n',
        '    - { interface: dpIf, src: uLeafX, srcport: out, dst: uChkX, dstport: in }\n',
        # uLeafX's own declared variant of xpDpLeaf, unused once the instance
        # naming it is removed above.
        '    # uLeafX\'s variant, declared by this assembler. DP_ALGO comes straight from\n'
        '    # the wrapper\'s CUST_ALGO rather than through the nested mid chain.\n'
        '    xpDpLeaf:\n'
        '        leafX:\n'
        '            DP_ALGO: { containerParam: CUST_ALGO }\n'
        '            DP_WIDTH: DP_WIDTH\n',
    )
    for line in removals:
        if text.count(line) != 1:
            raise AssertionError(f"xpDpTop direct-leaf anchor changed: {line!r}")
        text = text.replace(line, '', 1)
    with open(top_yaml, 'w') as f:
        f.write(text)

    source = os.path.join(top, 'model', 'xpDpSrc.cppm')
    with open(source) as f:
        text = f.read()
    line = '        out2->push(sample);\n'
    if text.count(line) != 1:
        raise AssertionError("xpDpSrc direct-leaf drive anchor changed")
    with open(source, 'w') as f:
        f.write(text.replace(line, '', 1))

    makefile = os.path.join(top, 'Makefile')
    with open(makefile) as f:
        text = f.read()
    recursion = """
# The mid-level IP generates and cleans through its own targets, which in turn
# cover the leaf.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
\t$(MAKE) -C $(REPO_ROOT)/../dpMid gen

clean::
\t$(MAKE) -C $(REPO_ROOT)/../dpMid clean
"""
    if text.count(recursion) != 1:
        raise AssertionError("xpDpTop recursive make anchor changed")
    with open(makefile, 'w') as f:
        f.write(text.replace(recursion, '\n', 1))


def install_leaf_rtl(leaf):
    path = os.path.join(leaf, 'rtl', 'xpDpLeaf.sv')
    with open(path) as f:
        text = f.read()
    marker = '\nendmodule: xpDpLeaf\n'
    if text.count(marker) != 1:
        raise AssertionError("generated xpDpLeaf RTL end marker changed")
    body = """
    dpSt inSt;
    dpSt fwd;

    always_comb begin
        inSt = dpSt'(in.data);
        fwd = inSt;
        fwd.algo = dpAlgoT'(DP_ALGO);
    end

    assign out.push = in.push;
    assign out.data = fwd;
    assign in.ack = out.ack;
"""
    with open(path, 'w') as f:
        f.write(text.replace(marker, body + marker, 1))


def update_parent_rtl_label(work):
    path = os.path.join(work, 'dpMid', 'rtl', 'xpDpMid.sv')
    with open(path) as f:
        text = f.read()
    old = 'endmodule: xpDpMid\n'
    new = 'endmodule: xpDpTop_xpDpMid\n'
    if text.count(old) != 1:
        raise AssertionError("xpDpMid RTL end label anchor changed")
    with open(path, 'w') as f:
        f.write(text.replace(old, new, 1))


def generate(work, env):
    leaf = os.path.join(work, 'dpLeaf')
    top = os.path.join(work, 'dpTop')
    make_parent_the_assembler(work)
    require_make(leaf, 'clean', env)
    require_make(top, 'clean', env)
    enable_leaf_vl(leaf)

    require_make(leaf, 'db', env)
    require_make(leaf, 'newmodule', env)
    install_leaf_rtl(leaf)
    require_make(leaf, 'gen', env)

    require_make(top, 'db', env)
    require_make(top, 'newmodule', env)
    require_make(top, 'gen', env)
    update_parent_rtl_label(work)
    return top


def check_generated(top):
    prj = projectOpen(os.path.join(top, 'xpDpTop.db'))
    mid = prj.getQualBlock('xpDpMid')
    leaf = prj.getQualBlock('xpDpLeaf')
    mid_pair = prj.registrarPairs[(mid, leaf)]
    if mid_pair['factoryProject'] == 'xpDpLeaf':
        raise AssertionError("pair factory project collides with the child owner")

    view = prj.getRegistrarConfigView(leaf, mid)
    registrations = {entry['variant']: entry for entry in view['verifRegistrations']}
    for variant in SELECTED:
        if variant not in registrations:
            raise AssertionError(
                f"missing Verilated registration for parent Config {variant}: "
                f"{sorted(registrations)}")
    identities = {
        (entry['fileStub'], entry['topModule'], entry['dutClass'])
        for entry in registrations.values()}
    if len(identities) != len(registrations):
        raise AssertionError("pair-qualified Verilated registration identities collide")
    if any(entry['fileStub'] == 'xpDpLeaf_dflt'
           for entry in registrations.values()):
        raise AssertionError("pair-qualified top collides with the child-owned top")
    if any(entry['physicalFileStub'].startswith('p')
           for entry in registrations.values()):
        raise AssertionError(
            "pair-qualified top leaked into the physical wrapper scaffold name")

    foreign = prj.config.getConfig('FOREIGNCONFIGHEADERS')[('xpDpTop', leaf)]
    if foreign['variants'] != ['customer'] or foreign['vlVariants']:
        raise AssertionError(
            f"container-sourced foreign Config was treated as a concrete top: {foreign}")

    registrar = os.path.join(
        top, '..', 'dpMid', 'registrar',
        'xpDpLeafVlRegistrar.cpp')
    if not os.path.exists(registrar):
        raise AssertionError(f"missing parent-owned registrar {registrar}")
    with open(registrar) as f:
        registrar_text = f.read()
    for variant in SELECTED:
        registration = registrations[variant]
        for expected in (registration['dutClass'], mid_pair['factoryProject'],
                         f'"{variant}"',
                         intf_gen_utils.cpp_config_expression_name(
                             registration['config'])):
            if expected not in registrar_text:
                raise AssertionError(
                    f"registrar omits {expected!r} for {variant}\n{registrar_text}")

        wrapper = os.path.join(
            top, '..', 'dpMid', 'verif',
            f'{registration["physicalFileStub"]}_hdl_sv_wrapper.sv')
        with open(wrapper) as f:
            wrapper_text = f.read()
        expected_value = SELECTED[variant][2]
        if f'localparam DP_ALGO = {expected_value}' not in wrapper_text:
            raise AssertionError(
                f"{os.path.basename(wrapper)} does not elaborate DP_ALGO="
                f"{expected_value}\n{wrapper_text}")
    print("PASS: generated pair wrappers carry both parent Config values")
    print("PASS: factory, project and pair-qualified identities do not collide")


def run_selected(top, env):
    rundir = os.path.join(top, 'rundir')
    require_make(top, 'all', env, directory=rundir, extra=('VL_DUT=1',))
    binary = os.path.join(rundir, 'build', 'run')
    if not os.path.exists(binary):
        raise AssertionError(f"missing simulation binary {binary}")

    for variant, (instance, checker, algorithm) in SELECTED.items():
        result = subprocess.run(
            [binary, 'xpDpTop', '--vlInst', instance],
            capture_output=True, text=True, timeout=300, env=env)
        output = result.stdout + result.stderr
        if result.returncode != 0:
            raise AssertionError(
                f"{variant} run failed with rc={result.returncode}\n{output}")
        expected = f"{checker} checked {SAMPLE_COUNT} samples at algorithm {algorithm}"
        if expected not in output:
            raise AssertionError(f"{variant} run omitted {expected!r}\n{output}")
        if f"{instance} forwarding" in output:
            raise AssertionError(
                f"{variant} selected leaf still ran its SystemC model\n{output}")
        for marker in ('Q_ASSERT', 'Fatal'):
            if marker in output:
                raise AssertionError(f"{variant} run reported {marker}\n{output}")
        if 'No error' not in output:
            raise AssertionError(f"{variant} run did not report success\n{output}")
        print(f"PASS: {variant} selected {instance} as RTL at DP_ALGO={algorithm}")


def run_all_tests():
    env = toolchain_env()
    for name in os.listdir(test_dir):
        if name.startswith('container_param_xproj_vl_'):
            shutil.rmtree(os.path.join(test_dir, name), ignore_errors=True)
    work = copy_fixture()
    try:
        top = generate(work, env)
        check_generated(top)
        run_selected(top, env)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as exc:
        print(f"FAIL: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
