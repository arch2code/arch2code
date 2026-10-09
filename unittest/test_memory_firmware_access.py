#!/usr/bin/env python3
"""Firmware access modes of regAccess memories.

regAccess is false, true (the same as rw), rw, ro or wo. These checks build a
routed leaf owning one parameterizable and one fixed-width portRportW memory
per mode and assert on the generated register handler: an ro memory's write
decodes its range and is dropped, with no write strobe and wr_en tied low; a
wo memory's read completes at once with zero, with no read pipeline. Each
handler is linted with verilator through its leaf. They also check the SystemC
constructors pass the mode, that true, 1 and rw generate identical files and
0 and false do, that an unknown mode is rejected, and they run a small SystemC program against
hwMemory and hwMemoryPort.

Fixtures are written outside the repository working tree.
"""

import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from pysrc.processYaml import projectOpen
from _tmp_helpers import remove_tree

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')
COMMON_SV = os.path.join(base_dir, 'common', 'systemVerilog')
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')
FLOPS_SV = os.path.join(COMMON_SV, 'flops.sv')
ASSERTS_SVH = os.path.join(COMMON_SV, 'asserts.svh')
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'memory', 'status')]
HARNESS = os.path.join(test_dir, 'fixtures', 'hw-memory-fw-access', 'hw_memory_fw_access.cpp')

PROJECT = """yamlFormat: 2
projectName: fwAccess
topInstance: uTop

projectFiles:
    - ../../yaml/shared.yaml
    - ../../yaml/top.yaml

dirs:
    root: ../..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""

# tbl is parameterizable (CFG_WIDTH, two 32-bit words at the variant's 40
# bits), tblFixed is fixed-width (cfgT, one word). With portRportW, ro puts
# the register handler on port A and wo on port B. leafB declares no
# registerPorts: and contains an instance, so its synthesised handler keeps a
# model of its own, which reaches tblB through a hwMemoryPort adapter.
DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        CFG_WIDTH: {{ value: 40, maxValue: 64, desc: "per-instance payload width" }}
    types:
        wideT:
            width: CFG_WIDTH
            maxBitwidth: 64
            desc: "parameterizable payload word"

constants:
    TBL_WORDS: {{ value: 8, desc: "memory wordlines" }}

types:
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    memAddrSt:
        address: {{ varType: memAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: wideT, generator: memory, desc: "parameterizable memory payload" }}
    fixedMemSt:
        data: {{ varType: cfgT, generator: memory, desc: "fixed-width memory payload" }}

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top, variant: wide }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top }}
    uLeafBSub:  {{ container: leafB, instanceType: leafBSub }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA configuration" }}

memories:
    - {{ memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, memoryType: {memoryType}, ports: [p], regAccess: {mode}, desc: "parameterizable table" }}
    - {{ memory: tblFixed, block: leafA, structure: fixedMemSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, memoryType: {memoryType}, ports: [p], regAccess: {mode}, desc: "fixed-width table" }}
    - {{ memory: tblB, block: leafB, structure: fixedMemSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, memoryType: {memoryType}, ports: [p], regAccess: {mode}, desc: "leafB table" }}

parameters:
    leafA:
        wide:
            CFG_WIDTH: 40
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top')
          + render_leaf('leafA', extra_block_lines='        params: [CFG_WIDTH]\n')
          + render_plain_block('leafB') + render_plain_block('leafBSub'))

HANDLER = 'rtl/leafA_regs.sv'
LEAF = 'rtl/leafA.sv'


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=300,
                          cwd=cwd, env=env)


def _build(mode, memoryType='portRportW'):
    """Write the fixture for one regAccess spelling and build its database.

    Returns (fixture_dir, db_path, completed_process).
    """
    fixture = tempfile.mkdtemp(prefix='fwaccess_')
    try:
        os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'yaml'))
        with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
            f.write(PROJECT)
        with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
            f.write(APB_PREAMBLE)
        with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
            f.write(DESIGN.format(blocks=BLOCKS, mode=mode, memoryType=memoryType))
        db = os.path.join(fixture, 'fwAccess.db')
        built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                           '--db', db, cwd=fixture)
        return fixture, db, built
    except BaseException:
        remove_tree(fixture)
        raise


def _generated_files(fixture):
    """Every scaffolded file that carries generated regions, relative to the
    fixture: SystemVerilog under rtl/, SystemC under model/ and base/."""
    files = []
    for sub, exts in (('rtl', ('.sv',)), ('model', ('.cppm', '.h', '.cpp')), ('base', ('.cppm', '.h', '.cpp'))):
        for root, _, names in os.walk(os.path.join(fixture, sub)):
            files += [os.path.relpath(os.path.join(root, n), fixture) for n in names if n.endswith(exts)]
    return sorted(files)


def _generate(mode, memoryType='portRportW'):
    """Build the fixture, scaffold it and regenerate every generated file.

    Returns (fixture_dir, {relative path: text}).
    """
    fixture, db, built = _build(mode, memoryType)
    if built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
    emitted = dict()
    for rel in _generated_files(fixture):
        lang = '--systemVerilog' if rel.endswith('.sv') else '--systemc'
        gen = _arch2code('--db', db, '-r', lang, '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return fixture, emitted


def _run_case(label, fn):
    try:
        fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"PASS: {label}")
    return True


def _expect(text, needle, what):
    if needle not in text:
        raise AssertionError(f"{what}: missing {needle!r}")


def _refute(text, needle, what):
    if needle in text:
        raise AssertionError(f"{what}: unexpected {needle!r}")


def check_ro_handler(emitted):
    """An ro memory's write case decodes its range and does nothing. The
    handler drives no write strobe or data, ties wr_en low and enables the
    memory from the read path only."""
    text = emitted[HANDLER]
    for memory in ('tbl', 'tblFixed'):
        for needle in (f'{memory}_update', f'{memory}_wr_enable', f'nxt_{memory}_data', f'{memory}_reg;'):
            _refute(text, needle, f"ro {memory}")
        _expect(text, f"assign {memory}.enable      = {memory}_rd_enable;", f"ro {memory}")
        _expect(text, f"assign {memory}.wr_en       = 1'b0;", f"ro {memory}")
        _expect(text, f"assign {memory}.write_data  = '0;", f"ro {memory}")
        _expect(text, f"{memory}_rd_capture", f"ro {memory} keeps its read pipeline")
    for const in ('REG_LEAFA_TBL', 'REG_LEAFA_TBLFIXED'):
        _expect(text, f"[{const}:{const} + {const}_SIZE - 32'd4]: ; // read-only to firmware: the write is dropped",
                "ro write case")
    _expect(text, "assign regs.pslverr = 1'b0;", "ro handler")


def check_wo_handler(emitted):
    """A wo memory's read case completes at once with zero. The handler has
    no read pipeline and enables the memory from the write path only."""
    text = emitted[HANDLER]
    for memory in ('tbl', 'tblFixed'):
        for needle in (f'{memory}_rd_enable', f'{memory}_rd_capture', f'{memory}_rword', f'{memory}.read_data'):
            _refute(text, needle, f"wo {memory}")
        _expect(text, f"assign {memory}.enable      = {memory}_wr_enable;", f"wo {memory}")
        _expect(text, f"assign {memory}.wr_en       = {memory}_wr_enable;", f"wo {memory}")
    for const in ('REG_LEAFA_TBL', 'REG_LEAFA_TBLFIXED'):
        arm = (f"[{const}:{const} + {const}_SIZE - 32'd4]: begin // write-only to firmware: reads return 0\n"
               f"                    nxt_rd_ready = 1'b1;\n"
               f"                    nxt_rd_data = '0;\n"
               f"                end")
        _expect(text, arm, "wo read case")
    _expect(text, "assign regs.pslverr = 1'b0;", "wo handler")


def check_register_port(emitted, regPort):
    """portRportW puts the handler's <memory>_reg on port A for ro and on
    port B for wo; the block's p port takes the other."""
    text = emitted[LEAF]
    blockPort = 'B' if regPort == 'A' else 'A'
    for memory in ('tbl', 'tblFixed'):
        for port, signal in ((regPort, f'{memory}_reg'), (blockPort, f'{memory}_p')):
            _expect(text, f".mem_port{port} ({signal})", f"leafA memory {memory}")


def check_model_constructors(emitted, enum):
    """The leaf models construct each hwMemory with the mode, and leafB's
    handler model constructs its hwMemoryPort adapter with the mode and the
    name it logs."""
    leafA = emitted['model/leafA.cppm']
    for memory in ('tbl', 'tblFixed'):
        _expect(leafA, f',{memory}(name(), "{memory}", mems, TBL_WORDS, HWMEMORYTYPE_NORMAL, {enum})',
                "leafA model")
    _expect(emitted['model/leafB.cppm'],
            f',tblB(name(), "tblB", mems, TBL_WORDS, HWMEMORYTYPE_NORMAL, {enum})', "leafB model")
    _expect(emitted['model/leafB_regs.cppm'],
            f',tblB_adapter(tblB, {enum}, std::string(this->name()) + ".tblB")', "leafB_regs model")


# The handler's interface ports carry no parameter override, so it is linted
# through the generated leaf, which binds them to real structs, under a
# wrapper supplying the APB interface.
_LINT_WRAPPER = """\
module leafA_lint_top
    import shared_package::*;
(
    input clk, rst_n
);
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();

    leafA #(.CFG_WIDTH(40)) dut (
        .regs(apbReg),
        .clk(clk), .rst_n(rst_n)
    );
endmodule
"""


def check_handler_lints_clean(fixture):
    """verilator --lint-only --no-timing of the handler through its leaf,
    default reset style, no -Wall."""
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = os.path.join(tmp, 'leafA_lint_top.sv')
        with open(wrapper, 'w') as f:
            f.write(_LINT_WRAPPER)
        cmd = (['verilator', '--lint-only', '--no-timing', '--top-module', 'leafA_lint_top',
                '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
               + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
               + [FLOPS_SV, ASSERTS_SVH]
               + [os.path.join(fixture, rel) for rel in
                  ('rtl/shared_package.sv', 'rtl/top_package.sv', HANDLER, LEAF)]
               + [wrapper])
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"lint failed:\n{result.stdout}{result.stderr}")


def _check_same_output(spelling, reference, stored):
    """regAccess: <spelling> is stored as `stored` and generates every file
    byte for byte as regAccess: <reference> does, on portRportW's
    read/write sibling."""
    fixture, emitted = _generate(spelling, 'portRportRW')
    try:
        refFixture, refEmitted = _generate(reference, 'portRportRW')
        try:
            if sorted(emitted) != sorted(refEmitted):
                raise AssertionError(f"{spelling} generates {sorted(emitted)}, {reference} {sorted(refEmitted)}")
            differ = [rel for rel in emitted
                      if not filecmp.cmp(os.path.join(fixture, rel), os.path.join(refFixture, rel), shallow=False)]
            if differ:
                raise AssertionError(f"{spelling} and {reference} generate different {differ}")
            prj = projectOpen(os.path.join(fixture, 'fwAccess.db'))
            got = {row['memory']: row['regAccess'] for row in prj.data['memories'].values()}
            if got != {'tbl': stored, 'tblFixed': stored, 'tblB': stored}:
                raise AssertionError(f"regAccess: {spelling} loads back as {got}, expected {stored!r} for every memory")
        finally:
            remove_tree(refFixture)
    finally:
        remove_tree(fixture)


def check_unknown_mode_rejected():
    fixture, db, built = _build('rx')
    try:
        output = built.stdout + built.stderr
        if built.returncode == 0:
            raise AssertionError(f"database build succeeded; expected a rejection:\n{output}")
        if 'Traceback' in output:
            raise AssertionError(f"rejection is a traceback, not a diagnostic:\n{output}")
        _expect(output, "field regAccess, rx is not in the allowed values", "diagnostic")
    finally:
        remove_tree(fixture)


# The model harness compiles hwMemory.h with the arch2code SystemC flags and
# links logging.cpp and randFactory.cpp, which hwMemory.h's includes need.
CXX = 'clang++'
CXX_FLAGS = ['-std=c++23', '-Wall', '-Wextra', '-Wpedantic', '-Wshadow', '-Wno-unused-variable',
             '-Wno-unused-parameter', '-Wfatal-errors', '-DSC_CPLUSPLUS=201703L',
             '-DSC_INCLUDE_DYNAMIC_PROCESSES', '-DBOOST_STACKTRACE_LINK']
HARNESS_SOURCES = (HARNESS, os.path.join(COMMON_SC, 'logging.cpp'), os.path.join(COMMON_SC, 'randFactory.cpp'))
# The four lines the harness's dropped accesses must log.
EXPECTED_LOG = (
    "top_roMem: firmware write to read-only memory at offset 0x4 dropped",
    "top_woMem: firmware read of write-only memory at offset 0x8 returns 0",
    "top.roPort: firmware write to read-only memory at offset 0x4 dropped",
    "top.woPort: firmware read of write-only memory at offset 0x8 returns 0",
)


def check_model_drops_and_logs():
    env = {var: os.environ.get(var) for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE')}
    missing = [var for var, value in env.items() if not value]
    if missing:
        raise AssertionError(f"{missing} not set; the SystemC toolchain variables the arch2code "
                             f"makefiles require must be set to run this check")
    includes = ['-I' + env['BOOST_INCLUDE'], '-I' + env['SYSTEMC_INCLUDE'], '-I' + COMMON_SC]
    includes += ['-I' + os.path.join(base_dir, 'interfaces', d)
                 for d in sorted(os.listdir(os.path.join(base_dir, 'interfaces')))
                 if os.path.isdir(os.path.join(base_dir, 'interfaces', d))]
    build_dir = tempfile.mkdtemp(prefix='a2c_hwmem_fw_')
    try:
        objects = []
        for src in HARNESS_SOURCES:
            obj = os.path.join(build_dir, os.path.basename(src).rsplit('.', 1)[0] + '.o')
            result = subprocess.run([CXX] + CXX_FLAGS + includes + ['-c', src, '-o', obj],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                raise AssertionError(f"compile {src} failed:\n{result.stdout}{result.stderr}")
            objects.append(obj)
        binary = os.path.join(build_dir, 'hw_memory_fw_access')
        result = subprocess.run([CXX, '-std=c++23', '-o', binary] + objects
                                + ['-L' + env['SYSTEMC_LIBDIR'], '-lsystemc', '-pthread'],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(f"link failed:\n{result.stdout}{result.stderr}")
        ran = subprocess.run([binary], capture_output=True, text=True, timeout=120)
    finally:
        remove_tree(build_dir)
    output = ran.stdout + ran.stderr
    if ran.returncode != 0 or 'checks:7 failures:0' not in output:
        raise AssertionError(f"harness exited {ran.returncode}, expected 'checks:7 failures:0':\n{output}")
    lines = output.splitlines()
    for expected in EXPECTED_LOG:
        if lines.count(expected) != 1:
            raise AssertionError(f"harness logs {expected!r} {lines.count(expected)} times, expected once:\n{output}")


def main():
    print("=" * 72)
    print("memory firmware access modes")
    print("=" * 72)
    ok = []
    for mode, handlerCheck, regPort, enum in (('ro', check_ro_handler, 'A', 'HWMEMORYFWACCESS_RO'),
                                              ('wo', check_wo_handler, 'B', 'HWMEMORYFWACCESS_WO')):
        fixture, emitted = _generate(mode)
        try:
            ok.append(_run_case(f"{mode}: the handler's fixed and parameterizable memories follow the mode",
                                lambda: handlerCheck(emitted)))
            ok.append(_run_case(f"{mode}: portRportW puts the register port on {regPort}",
                                lambda: check_register_port(emitted, regPort)))
            ok.append(_run_case(f"{mode}: the models construct hwMemory and hwMemoryPort with {enum}",
                                lambda: check_model_constructors(emitted, enum)))
            ok.append(_run_case(f"{mode}: the handler lints clean through its leaf",
                                lambda: check_handler_lints_clean(fixture)))
        finally:
            remove_tree(fixture)
    for spelling, reference, stored in (('true', 'rw', 'rw'), ('1', 'true', 'rw'), ('0', 'false', 0)):
        ok.append(_run_case(f"regAccess: {spelling} is stored as {stored!r} and generates the same files as {reference}",
                            lambda spelling=spelling, reference=reference, stored=stored:
                            _check_same_output(spelling, reference, stored)))
    ok.append(_run_case("an unknown regAccess value is rejected", check_unknown_mode_rejected))
    ok.append(_run_case("hwMemory and hwMemoryPort drop an ro write and read a wo memory as 0, logging each",
                        check_model_drops_and_logs))

    print()
    if all(ok):
        print("RESULT: all memory firmware access checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory firmware access checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
