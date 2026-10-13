#!/usr/bin/env python3
"""The generated sc_pack(), sc_unpack(), pack() and unpack() put every field
at the bit the RTL packed structs use.

The harness renders one context in both emission flavours, module (inline)
and model (declared in the header, defined out of line), and compiles them
into one binary against the SystemC kernel. For each struct shape it checks,
over random in-range values, that sc_pack() and pack() equal a layout built
field by field at the documented positions, that unpack() of that layout
gives the struct back, and that sc_unpack() and the sc_bv constructor do too.
pack() and unpack() run in out-of-line functions next to a 32-bit word loop,
the way a caller's own loop sees them. The binary is built at -O0 and at -O3,
because an access through a mistyped pointer only goes wrong once the
optimizer reorders it.

The shapes: a width-1 struct (packs to bool), narrow, 17-bit and exactly
64-bit plain structs with signed fields, a nested struct holding an array of
structs, a 100-bit member stored as word[], an array of structs and an array
of fields that cross a 64-bit word, two levels of nesting over 64 bits, a
narrow nested struct at bit 0 of a struct over 64 bits, a uint16_t nested
struct sharing word 0 with a field and another alone at bit 64, a uint64_t
nested struct at bit 64, arrays in uint16_t and uint32_t structs nested at
bit 0, at bit 1 and around a wide member, a datapath struct and a struct
nesting it, and parameterizable structs at several widths: scalar, array,
wide member, array of wide members, nested parameterizable structs, scalar
fields that cross bit 64 at some widths only (one copies isp_awb's
awb_rgb_pixel_mult_t), nested structs at bit 64 only at the default width, a
nested struct whose default fits in 32 bits, a member held as word[] at every
width, and arrays whose default length is one.

sc_pack() must assert, through Q_ASSERT, on a top field holding more bits than
its type, and no other check may trigger one.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.systemcGen import genSystemC
from templates.systemc import includes, structures

from _addrctl_helpers import build_database, cleanup, projectOpen
from _tmp_helpers import remove_tree

FIXTURE_DIR = os.path.join(test_dir, 'fixtures', 'sc-pack-word-path')
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')

CXX = 'clang++'
STD = '-std=c++23'
DEFINES = ['-DSC_CPLUSPLUS=201703L', '-DSC_INCLUDE_DYNAMIC_PROCESSES', '-DBOOST_STACKTRACE_LINK']
LIBS = ['-lsystemc', '-pthread']

# Per iteration: five checks for each of the 54 multi-bit shapes, four for the
# width-1 struct, six for the datapath pair and two tail asserts; 16
# iterations, then four width checks, in two flavours, per build. Pinned so a
# fixture edit that drops a case fails here rather than reducing the evidence
# silently.
EXPECTED_CHECKS = ((54 * 5 + 4 + 6 + 2) * 16 + 4) * 2
OPT_LEVELS = ('-O0', '-O3')

ARCH_YAML = """ipParameters:
    constants:
        P_W:  { value: 8,  maxValue: 40,  desc: "Parameterized field width" }
        A_N:  { value: 3,  maxValue: 6,   desc: "Parameterized array length" }
        PW_W: { value: 70, maxValue: 128, desc: "Parameterized wide field width" }
        Q_W:  { value: 64, maxValue: 64,  desc: "Parameterized width whose default fills a word" }
        M_W:  { value: 26, maxValue: 34,  desc: "isp_awb pixel-times-gain width" }
        N_A:  { value: 2,  maxValue: 12,  desc: "Parameterized array length of a nested struct" }
        N_ONE: { value: 1, maxValue: 4,   desc: "Parameterized array length, default one" }
        W2:   { value: 8,  maxValue: 100, desc: "Parameterized width, default narrow, maximum over 64" }
    types:
        pT:  { width: P_W, desc: "Parameterized field" }
        psT: { width: P_W, isSigned: true, desc: "Signed parameterized field" }
        pwT: { width: PW_W, desc: "Parameterized wide field" }
        qT:  { width: Q_W, desc: "Parameterized field, default 64" }
        mT:  { width: M_W, desc: "Parameterized pixel-times-gain field" }
        w2T: { width: W2, desc: "Parameterized field held as word[]" }

types:
    u1T:   { width: 1,   desc: "Bit" }
    u2T:   { width: 2,   desc: "Two" }
    u3T:   { width: 3,   desc: "Three" }
    u4T:   { width: 4,   desc: "Nibble" }
    u5T:   { width: 5,   desc: "Five" }
    u8T:   { width: 8,   desc: "Byte" }
    u12T:  { width: 12,  desc: "Twelve" }
    u24T:  { width: 24,  desc: "Twenty-four" }
    u32T:  { width: 32,  desc: "Thirty-two" }
    u40T:  { width: 40,  desc: "Forty" }
    u55T:  { width: 55,  desc: "Fifty-five" }
    u64T:  { width: 64,  desc: "Sixty-four" }
    u100T: { width: 100, desc: "Hundred" }
    s3T:   { width: 3,   isSigned: true, desc: "Signed three" }
    s5T:   { width: 5,   isSigned: true, desc: "Signed five" }
    s7T:   { width: 7,   isSigned: true, desc: "Signed seven" }
    s40T:  { width: 40,  isSigned: true, desc: "Signed forty" }

structures:
    oneSt:
        e: { varType: u1T, desc: "only bit" }
    tinySt:
        x: { varType: u3T, desc: "high" }
        y: { varType: s5T, desc: "low, signed" }
    smallSt:
        a: { varType: u4T, desc: "high" }
        s: { varType: s5T, desc: "signed" }
        b: { varType: u8T, desc: "low" }
    exact64St:
        hi: { varType: u24T, desc: "high" }
        lo: { varType: s40T, desc: "low, signed" }
    innerSt:
        x: { varType: u4T, desc: "high" }
        y: { varType: s3T, desc: "low, signed" }
    nestSt:
        top:   { varType: u3T, desc: "high" }
        inner: { subStruct: innerSt, arraySize: 3, desc: "array of structs" }
        tail:  { subStruct: smallSt, desc: "nested" }
    wideSt:
        hi: { varType: u4T, desc: "high" }
        w:  { varType: u100T, desc: "wide member" }
        lo: { varType: s7T, desc: "low, signed" }
    bigNestSt:
        inners: { subStruct: smallSt, arraySize: 5, desc: "array of structs over 64" }
        flag:   { varType: u1T, desc: "low" }
    arrSt:
        v: { varType: u12T, arraySize: 7, desc: "array crossing a word" }
        z: { varType: s5T, desc: "low, signed" }
    deepSt:
        n: { subStruct: nestSt, desc: "nested with arrays" }
        w: { subStruct: wideSt, desc: "nested over 64" }
    lowNestSt:
        w:    { varType: u100T, desc: "wide member" }
        tail: { subStruct: smallSt, desc: "narrow nested struct at bit 0" }
    log2NSt:
        b: { varType: u4T, desc: "high" }
        a: { varType: u5T, desc: "low" }
    aliasSt:
        hi:   { varType: u8T, desc: "alone in word 1" }
        addr: { varType: u55T, desc: "shares word 0 with n" }
        n:    { subStruct: log2NSt, desc: "uint16_t _packedSt at bit 0 of a uint64_t[2]" }
    nHighSt:
        n:  { subStruct: log2NSt, desc: "uint16_t _packedSt at bit 64" }
        lo: { varType: u64T, desc: "fills word 0" }
    wordHighSt:
        n:  { subStruct: exact64St, desc: "uint64_t _packedSt at bit 64" }
        lo: { varType: u64T, desc: "fills word 0" }
    pix4St:
        pixels: { varType: u8T, arraySize: 4, desc: "array in a uint32_t _packedSt" }
    pix2St:
        p: { varType: u8T, arraySize: 2, desc: "array in a uint16_t _packedSt" }
    csiSt:
        fv:   { varType: u1T, desc: "high" }
        lv:   { varType: u1T, desc: "middle" }
        data: { subStruct: pix4St, desc: "narrow array struct at bit 0" }
    csiUnSt:
        fv:   { varType: u1T, desc: "high" }
        data: { subStruct: pix4St, desc: "narrow array struct at bit 1" }
        lv:   { varType: u1T, desc: "low" }
    pixWideSt:
        a: { subStruct: pix2St, desc: "narrow array struct above a wide member" }
        w: { varType: u100T, desc: "wide member" }
        b: { subStruct: pix2St, desc: "narrow array struct at bit 0" }
    dpSt:
        tag:  { varType: u8T, desc: "high" }
        data: { varType: u32T, generator: datapath, desc: "datapath payload" }
        len:  { varType: u4T, desc: "low" }
    dpOuterSt:
        hdr:   { varType: u3T, desc: "high" }
        inner: { subStruct: dpSt, desc: "nested datapath struct" }
    pSt:
        pa: { varType: pT, desc: "param high" }
        pb: { varType: s5T, desc: "low, signed" }
    pArrSt:
        px: { varType: pT, arraySize: A_N, desc: "param array" }
        pz: { varType: u4T, desc: "low" }
    pWideSt:
        hi: { varType: u3T, desc: "high" }
        pw: { varType: pwT, desc: "param wide member" }
        ps: { varType: psT, desc: "signed param low" }
    pWArrSt:
        pw: { varType: pwT, arraySize: 2, desc: "array of param wide members" }
        z:  { varType: u2T, desc: "low" }
    pNestSt:
        inner: { subStruct: pSt, arraySize: A_N, desc: "array of param structs" }
        plain: { subStruct: smallSt, desc: "plain nested" }
        pw:    { subStruct: pWideSt, desc: "nested param wide" }
    pStrSt:
        a: { varType: u8T, desc: "high, crosses bit 64 at P_W 17 to 23" }
        p: { varType: psT, desc: "signed param, crosses bit 64 at P_W over 24" }
        b: { varType: u40T, desc: "low" }
    awbLikeSt:
        r: { varType: mT, desc: "isp_awb awb_rgb_pixel_mult_t, crosses bit 64 at M_W 26" }
        g: { varType: mT, desc: "green" }
        b: { varType: mT, desc: "blue" }
    pMisSt:
        n: { subStruct: exact64St, desc: "uint64_t _packedSt at bit 64 only at the default Q_W" }
        q: { varType: qT, desc: "param low" }
    pMisNSt:
        hi: { varType: u8T, desc: "high" }
        n:  { subStruct: log2NSt, desc: "uint16_t _packedSt at bit 64 only at the default Q_W" }
        q:  { varType: qT, desc: "param low" }
    pBigSt:
        a: { varType: u8T, arraySize: N_A, desc: "16 bits by default, 96 at most" }
    pHoldSt:
        b:  { subStruct: pBigSt, desc: "param nested struct, default 32 bits or fewer, maximum over 64" }
        lo: { varType: u3T, desc: "low" }
    pW2St:
        hi: { varType: u3T, desc: "high" }
        w:  { varType: w2T, desc: "word[] member at every width" }
        lo: { varType: u5T, desc: "low" }
    pOneArrSt:
        v: { varType: u8T, arraySize: N_ONE, desc: "param array, default one element" }
        z: { varType: u4T, desc: "low" }
    pOneSt:
        v: { varType: u8T, arraySize: N_ONE, desc: "only field, param array, default one element" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    ip:
        desc: "Parameterized block"
        params: [P_W, A_N, PW_W, Q_W, M_W, N_A, N_ONE, W2]

instances:
    uTop: { container: top, instanceType: top }
    uIp:  { container: top, instanceType: ip, variant: variant0 }

parameters:
    ip:
        variant0:
            P_W: 8
            A_N: 3
            PW_W: 70
            Q_W: 64
            M_W: 26
            N_A: 2
            N_ONE: 1
            W2: 8
"""

_SC_MAIN = r"""
int sc_main(int, char **)
{
    mod::runChecks("module");
    mdl::runChecks("model");
    printf("checks:%" PRIu64 " failures:%" PRIu64 "\n", checks, failures);
    return failures ? 1 : 0;
}
"""


def toolchain_env():
    env = {}
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE'):
        value = os.environ.get(var)
        if not value:
            raise RuntimeError(f"{var} is not set; the SystemC toolchain variables the "
                               f"arch2code makefiles require must be set to run this suite")
        env[var] = value
    return env


def _contextData(prj):
    """The context holding the structures, as `genSystemC` builds it."""
    for context in prj.yamlContext:
        if context.startswith('_'):
            continue
        data = prj.getContextData([context], genSystemC.dataTypeMappings)
        genSystemC.calcStructure(genSystemC, data, prj)
        if data['structures']:
            return data
    raise AssertionError("no context carries the fixture structures")


def _renderStructs(prj, data, mode, section, namespace=''):
    args = types.SimpleNamespace(mode=mode, section=section, template='structures',
                                 namespace=namespace)
    out = []
    for key, value in data['structures'].items():
        out.extend(structures.oneStruct(args, prj, data, key, value))
    return '\n'.join(out)


def render_source():
    """The harness translation unit: shared types, then the module flavour in
    namespace mod and the model flavour in namespace mdl, each followed by the
    checks."""
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        data = _contextData(prj)
        args = types.SimpleNamespace(mode='model', section='types', template='includes',
                                     namespace='')
        typesText = includes.render(args, prj, data)
        moduleText = _renderStructs(prj, data, 'module', 'header')
        modelHeader = _renderStructs(prj, data, 'model', 'header')
        modelCpp = _renderStructs(prj, data, 'model', 'cpp', namespace='mdl')
    finally:
        cleanup([project_path, db_path] + arch_paths)
    return '\n'.join([
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include <algorithm>',
        '#include <format>',
        '#include "bitTwiddling.h"',
        typesText,
        '#include "sc_pack_support.h"',
        'namespace mod {', moduleText, '#include "sc_pack_checks.inc"', '}',
        'namespace mdl {', modelHeader, '}',
        # A split definition's leading return type is looked up at namespace scope.
        'using namespace mdl;',
        modelCpp,
        'namespace mdl {', '#include "sc_pack_checks.inc"', '}',
        _SC_MAIN,
    ])


def build(build_dir, env, source, opt):
    src = os.path.join(build_dir, 'sc_pack_word_path.cpp')
    with open(src, 'w') as f:
        f.write(source)
    common = [STD, opt, '-Wall', '-Wno-unused-variable', '-Wno-unused-function', '-Wfatal-errors'] + DEFINES + [
        '-I' + env['BOOST_INCLUDE'], '-I' + env['SYSTEMC_INCLUDE'], '-I' + COMMON_SC, '-I' + FIXTURE_DIR]
    binary = os.path.join(build_dir, 'sc_pack_word_path' + opt)
    cmd = ([CXX] + common + [src, os.path.join(COMMON_SC, 'bitTwiddling.cpp'),
                             '-o', binary,
                             '-L' + env['SYSTEMC_LIBDIR']] + LIBS)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"build failed:\n{' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return binary


def test_sc_pack_matches_field_layout_and_pack():
    """Build and run the harness; every check in the module docstring must hold."""
    env = toolchain_env()
    assert shutil.which(CXX), f"{CXX} not found on PATH"
    source = render_source()
    build_dir = tempfile.mkdtemp(prefix='a2c_sc_pack_')
    try:
        results = []
        for opt in OPT_LEVELS:
            binary = build(build_dir, env, source, opt)
            results.append((opt, subprocess.run([binary], capture_output=True, text=True, timeout=300)))
    finally:
        remove_tree(build_dir)

    for opt, result in results:
        output = result.stdout + result.stderr
        assert result.returncode == 0, f"{opt} harness exited {result.returncode}:\n{output}"
        summary = [line for line in output.splitlines() if line.startswith('checks:')]
        assert len(summary) == 1, f"{opt}: expected one summary line, got {summary!r}:\n{output}"
        checks, fails = summary[0].split()
        assert fails == 'failures:0', f"{opt}:\n{output}"
        count = int(checks.split(':')[1])
        assert count == EXPECTED_CHECKS, f"{opt}: expected {EXPECTED_CHECKS} checks, got {count}:\n{output}"
        print(f"  {opt}: {count} layout and round-trip checks across 57 shapes "
              f"in two flavours, 0 failures")


DATAPATH64_YAML = """types:
    u8T:  { width: 8,  desc: "Byte" }
    u64T: { width: 64, desc: "Sixty-four" }

structures:
    dp64St:
        tag:  { varType: u8T, desc: "high" }
        data: { varType: u64T, generator: datapath, desc: "64-bit datapath payload" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true

instances:
    uTop: { container: top, instanceType: top }
"""


def test_datapath_field_of_64_bits_renders():
    """A struct with a datapath field of 64 bits renders in every emission
    flavour."""
    db_path, project_path, arch_paths = build_database(DATAPATH64_YAML)
    try:
        prj = projectOpen(db_path)
        data = _contextData(prj)
        for mode, section in (('module', 'header'), ('model', 'header'), ('model', 'cpp'), ('fw', 'header')):
            text = _renderStructs(prj, data, mode, section, namespace='ns' if section == 'cpp' else '')
            assert 'dp64St' in text, f"{mode} {section}: dp64St not rendered:\n{text}"
    finally:
        cleanup([project_path, db_path] + arch_paths)
    print("  dp64St renders in the module, model and fw flavours")


def run_all_tests():
    tests = [
        test_sc_pack_matches_field_layout_and_pack,
        test_datapath_field_of_64_bits_renders,
    ]
    print("=" * 70)
    print("SC_PACK WORD PATH TESTS")
    print("=" * 70)
    results = []
    for test_func in tests:
        print(f"\n{test_func.__name__}:")
        try:
            test_func()
            results.append((test_func.__name__, True))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "=" * 70 + "\nTEST SUMMARY\n" + "=" * 70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
