#!/usr/bin/env python3
"""`registerFeatures` (templates/systemc/structures.py) emits a register
struct's `_getValue`/`_setValue` accessors: one masked, shifted term per field,
each field where pack() puts it. The first YAML field is the MSB, so in
un0RegSt (the shape of apbDecode's `un0ARegSt`) fa/fb/fc sit at shifts 40, 8
and 0, and a parameterizable struct's shifts are spelled in its parameters.

The runtime case compiles these structs with -Werror=shift-count-overflow,
-Werror=shift-op-parentheses and -ftrivial-auto-var-init=pattern. The last
fills each uninitialised local with a byte pattern, so a pack() that leaves
part of its output unwritten fails on every run. The cases:
  - twoRegSt, fa=0xAA fb=0xBB: pack() == 0xAABB == _getValue(), and
    _setValue(pack()) gives back fa and fb;
  - outerRegSt, a nested register struct that is not the last field:
    _getValue() == pack(), and _setValue(pack()) gives back every field;
  - sRegSt, a 5-bit signed field holding -1: _getValue() == pack(), and
    _setValue(pack()) and unpack() both give back -1;
  - s8RegSt, a native signed byte holding -3: _getValue() == pack(), and
    _setValue(pack()) and unpack() both give back -3 and the other field;
  - s64RegSt, a signed 64-bit field: _setValue and unpack() of
    0x8000000000000005 keep it, and _getValue() returns it;
  - pRegSt_v<12>, a parameterizable struct at a non-default width:
    pack() == 0xAB123 == _getValue(), and _setValue(pack()) gives back both
    fields;
  - wideSt_v<64>, a Config width at its 64-bit maximum: _getValue(), pack()
    and unpack() keep 0x8123456789abcdef, and _setValue round-trips it;
  - swSt_v<64>, a signed Config width at 64: _setValue, pack() and unpack()
    of 0x8000000000000005 keep it.
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
from pysrc.intf_gen_utils import cpp_fw_namespace_name, wrap_fw_namespace
from templates.systemc import includes, structures

from _addrctl_helpers import build_database, cleanup, projectOpen


ARCH_YAML = """ipParameters:
    constants:
        P_W: { value: 8, maxValue: 16, desc: "Parameterized width" }
        W_W: { value: 32, maxValue: 64, desc: "Width reaching 64" }
        S_W: { value: 16, maxValue: 64, desc: "Signed width reaching 64" }
    types:
        pT: { width: P_W, desc: "Parameterized field" }
        wT: { width: W_W, desc: "Field up to 64 bits" }
        swT: { width: S_W, isSigned: true, desc: "Signed field up to 64 bits" }

types:
    u4T:  { width: 4,  desc: "Nibble" }
    u8T:  { width: 8,  desc: "Byte" }
    u32T: { width: 32, desc: "Word" }
    s5T:  { width: 5,  isSigned: true, desc: "Signed 5-bit" }
    s8T:  { width: 8,  isSigned: true, desc: "Signed byte" }
    s64T: { width: 64, isSigned: true, desc: "Signed 64-bit" }

structures:
    un0RegSt:
        fa: { varType: u8T,  generator: register, desc: "[47:40]" }
        fb: { varType: u32T, generator: register, desc: "[39:8]" }
        fc: { varType: u8T,  generator: register, desc: "[7:0]" }
    twoRegSt:
        fa: { varType: u8T, generator: register, desc: "[15:8]" }
        fb: { varType: u8T, generator: register, desc: "[7:0]" }
    innerRegSt:
        x: { varType: u4T, generator: register, desc: "[7:4]" }
        y: { varType: u4T, generator: register, desc: "[3:0]" }
    outerRegSt:
        hi:  { varType: u8T, generator: register, desc: "[23:16]" }
        mid: { subStruct: innerRegSt, desc: "[15:8]" }
        lo:  { varType: s8T, generator: register, desc: "[7:0]" }
    sRegSt:
        sa: { varType: s5T, generator: register, desc: "[12:8]" }
        sb: { varType: u8T, generator: register, desc: "[7:0]" }
    pRegSt:
        pa: { varType: u8T, generator: register, desc: "above pb" }
        pb: { varType: pT,  generator: register, desc: "[P_W-1:0]" }
    s8RegSt:
        sn: { varType: s8T, generator: register, desc: "[15:8]" }
        su: { varType: u8T, generator: register, desc: "[7:0]" }
    s64RegSt:
        sw: { varType: s64T, generator: register, desc: "[63:0]" }
    wideSt:
        ww: { varType: wT, generator: register, desc: "[W_W-1:0]" }
    swSt:
        sw: { varType: swT, generator: register, desc: "[S_W-1:0]" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    ip:
        desc: "Parameterized block"
        params: [P_W, W_W, S_W]

instances:
    uTop: { container: top, instanceType: top }
    uIp:  { container: top, instanceType: ip, variant: variant0 }

parameters:
    ip:
        variant0:
            P_W: 8
            W_W: 32
            S_W: 16
"""


def _header(name):
    print("\n" + "=" * 70)
    print(f"Test: {name}")
    print("=" * 70)


def _getStructData(prj, name='un0RegSt'):
    """(context data, structure key, structure view) for `name`, exactly as
    `genSystemC` builds it: per-context data plus the `calcStructure` pass that
    fills in `bitshift`/`bitwidth`/`isArray`/`register`."""
    for context in prj.yamlContext:
        if context.startswith('_'):
            continue
        data = prj.getContextData([context], genSystemC.dataTypeMappings)
        genSystemC.calcStructure(genSystemC, data, prj)
        for key, structData in data['structures'].items():
            if structData['structure'] == name:
                return data, key, structData
    raise AssertionError(f"{name} was not rendered into any context")


def _getValueTerm(name, width, shift):
    return f"(( {name} & ((1ULL<<{width})-1) ) << {shift})"


def _setValueLine(name, typeName, width, shift):
    return (f"{name} = ( {typeName} ) (( packedValue >> {shift} ) & "
            f"(( (uint64_t)1 << {width} ) - 1)) ;")


def test_getvalue_one_term_per_field():
    """Every field contributes a `_getValue` term, correctly masked-then-shifted."""
    _header("_getValue emits one correctly masked term per field")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        _, _, structData = _getStructData(prj)
        rendered = '\n'.join(structures.registerFeatures(structData, '    ', prj, False))

        expected = [
            _getValueTerm('fa', 8, 40),
            _getValueTerm('fb', 32, 8),
            _getValueTerm('fc', 8, 0),
        ]
        for term in expected:
            count = rendered.count(term)
            if count != 1:
                print(f"  FAIL: term {term!r} appears {count} times, expected 1")
                ok = False
            else:
                print(f"  ok: {term}")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print("  PASS: three fields, three correctly masked-and-shifted terms")
    return ok


def test_setvalue_one_line_per_field_at_pack_position():
    """`_setValue` unpacks each field from where pack() puts it, one line per
    field."""
    _header("_setValue unpacks each field from its pack() position")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        _, _, structData = _getStructData(prj)
        out = structures.registerFeatures(structData, '    ', prj, False)
        rendered = '\n'.join(out)

        expected = [
            _setValueLine('fa', 'u8T', 8, 40),
            _setValueLine('fb', 'u32T', 32, 8),
            _setValueLine('fc', 'u8T', 8, 0),
        ]
        setValueLines = [line for line in out if 'packedValue >>' in line]
        if len(setValueLines) != 3:
            print(f"  FAIL: expected 3 _setValue lines, got {len(setValueLines)}")
            ok = False
        for line in expected:
            if line not in rendered:
                print(f"  FAIL: missing expected _setValue line: {line!r}")
                ok = False
            else:
                print(f"  ok: {line}")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print("  PASS: one _setValue line per field, at its pack() position")
    return ok


_RUNTIME_MAIN = r"""
#include <cstdio>
static int fails = 0;
static void check(const char *what, bool ok) {
    std::printf("  %s: %s\n", ok ? "ok" : "FAIL", what);
    fails += !ok;
}
int main() {
    twoRegSt t;
    t.fa = 0xAA;
    t.fb = 0xBB;
    twoRegSt::_packedSt tp;
    t.pack(tp);
    twoRegSt tb;
    tb._setValue(tp);
    std::printf("  twoRegSt pack=%llx getValue=%llx\n",
                (unsigned long long)tp, (unsigned long long)t._getValue());
    check("twoRegSt pack() == 0xAABB", tp == 0xAABB);
    check("twoRegSt _getValue() == pack()", t._getValue() == tp);
    check("twoRegSt _setValue(pack()) round-trips", tb.fa == 0xAA && tb.fb == 0xBB);

    outerRegSt o;
    o.hi = 0x12;
    o.mid.x = 0x3;
    o.mid.y = 0x4;
    o.lo = 0x56;
    outerRegSt::_packedSt op;
    o.pack(op);
    outerRegSt ob;
    ob._setValue(op);
    std::printf("  outerRegSt pack=%llx getValue=%llx\n",
                (unsigned long long)op, (unsigned long long)o._getValue());
    check("outerRegSt _getValue() == pack()", o._getValue() == op);
    check("outerRegSt _setValue(pack()) round-trips",
          ob.hi == 0x12 && ob.mid.x == 0x3 && ob.mid.y == 0x4 && ob.lo == 0x56);

    sRegSt sg;
    sg.sa = -1;
    sg.sb = 0x22;
    sRegSt::_packedSt sp;
    sg.pack(sp);
    sRegSt sb;
    sb._setValue(sp);
    sRegSt su;
    su.unpack(sp);
    std::printf("  sRegSt pack=%llx _setValue sa=%d unpack sa=%d\n",
                (unsigned long long)sp, (int)sb.sa, (int)su.sa);
    check("sRegSt _getValue() == pack()", sg._getValue() == sp);
    check("sRegSt _setValue sign-extends sa like unpack()", sb.sa == -1 && su.sa == -1 && sb.sb == 0x22);

    pRegSt_v<12> pr;
    pr.pa = 0xAB;
    pr.pb = 0x123;
    pRegSt_v<12>::_packedSt pp;
    pr.pack(pp);
    pRegSt_v<12> pb;
    pb._setValue(pp);
    std::printf("  pRegSt_v<12> pack=%llx getValue=%llx\n",
                (unsigned long long)pp, (unsigned long long)pr._getValue());
    check("pRegSt_v<12> pack() == 0xAB123", pp == 0xAB123);
    check("pRegSt_v<12> _getValue() == pack()", pr._getValue() == pp);
    check("pRegSt_v<12> _setValue(pack()) round-trips", pb.pa == 0xAB && pb.pb == 0x123);

    s8RegSt n;
    n.sn = -3;
    n.su = 0x44;
    s8RegSt::_packedSt np;
    n.pack(np);
    s8RegSt nb;
    nb._setValue(np);
    s8RegSt nu;
    nu.unpack(np);
    std::printf("  s8RegSt pack=%llx _setValue sn=%d unpack sn=%d\n",
                (unsigned long long)np, (int)nb.sn, (int)nu.sn);
    check("s8RegSt _getValue() == pack()", n._getValue() == np);
    check("s8RegSt _setValue and unpack() give back sn=-3",
          nb.sn == -3 && nu.sn == -3 && nb.su == 0x44 && nu.su == 0x44);

    const uint64_t wide = 0x8000000000000005ULL;
    s64RegSt w64;
    w64._setValue(wide);
    s64RegSt u64;
    u64.unpack(wide);
    std::printf("  s64RegSt _setValue sw=%llx unpack sw=%llx\n",
                (unsigned long long)w64.sw, (unsigned long long)u64.sw);
    check("s64RegSt _setValue keeps 0x8000000000000005", (uint64_t)w64.sw == wide);
    check("s64RegSt unpack() keeps 0x8000000000000005", (uint64_t)u64.sw == wide);
    check("s64RegSt _getValue() round-trips", w64._getValue() == wide);

    const uint64_t full = 0x8123456789abcdefULL;
    wideSt_v<64> ws;
    ws.ww = full;
    wideSt_v<64> wb;
    wb._setValue(ws._getValue());
    std::printf("  wideSt_v<64> getValue=%llx _setValue ww=%llx\n",
                (unsigned long long)ws._getValue(), (unsigned long long)wb.ww);
    check("wideSt_v<64> _getValue() keeps every bit", ws._getValue() == full);
    check("wideSt_v<64> _setValue(_getValue()) round-trips", wb.ww == full);
    wideSt_v<64>::_packedSt wp;
    ws.pack(wp);
    wideSt_v<64> wu;
    wu.unpack(full);
    std::printf("  wideSt_v<64> pack=%llx unpack ww=%llx\n",
                (unsigned long long)wp, (unsigned long long)wu.ww);
    check("wideSt_v<64> pack() keeps every bit", wp == full);
    check("wideSt_v<64> unpack() keeps every bit", wu.ww == full);

    swSt_v<64> sws;
    sws._setValue(wide);
    swSt_v<64> swu;
    swu.unpack(wide);
    std::printf("  swSt_v<64> _setValue sw=%llx unpack sw=%llx\n",
                (unsigned long long)sws.sw, (unsigned long long)swu.sw);
    check("swSt_v<64> _setValue keeps 0x8000000000000005", (uint64_t)sws.sw == wide);
    check("swSt_v<64> unpack() keeps 0x8000000000000005", (uint64_t)swu.sw == wide);
    swSt_v<64>::_packedSt swp;
    sws.pack(swp);
    std::printf("  swSt_v<64> pack=%llx\n", (unsigned long long)swp);
    check("swSt_v<64> pack() keeps 0x8000000000000005", swp == wide);

    return fails ? 1 : 0;
}
"""

_RUNTIME_STRUCTS = ('twoRegSt', 'innerRegSt', 'outerRegSt', 'sRegSt', 'pRegSt',
                    's8RegSt', 's64RegSt', 'wideSt', 'swSt')


def test_accessors_agree_with_pack_at_runtime():
    """Every case listed in the module docstring, compiled and run. Each
    struct is the fw rendering, which has pack() and unpack() and no SystemC
    dependency; a register struct also gets the real registerFeatures output
    added to its body."""
    _header("_getValue/_setValue agree with pack() at runtime")
    if shutil.which('clang++') is None:
        raise RuntimeError("clang++ is not on PATH; it is the compiler this "
                           "test compiles the rendered structs with")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        data, _, _ = _getStructData(prj, 'twoRegSt')
        args = types.SimpleNamespace(mode='fw', section='types',
                                     template='includes', namespace='')
        typesText = includes.render(args, prj, data)
        args = types.SimpleNamespace(mode='fw', section='header',
                                     template='structures', namespace='')
        structs = []
        for key, value in data['structures'].items():
            if value['structure'] not in _RUNTIME_STRUCTS:
                continue
            lines = structures.oneStruct(args, prj, data, key, value)
            if value['register']:
                close = lines.index('\n};')
                lines[close:close] = structures.registerFeatures(
                    value, '    ', prj, value['isParameterizable'])
            structs.extend(lines)
        structs = wrap_fw_namespace(args, data, structs)
        namespace = cpp_fw_namespace_name(data['contextModuleIdentity'])
    finally:
        cleanup([project_path, db_path] + arch_paths)
    source = ('#include <cstdint>\n#include <cstring>\n#include "bitTwiddling.h"\n'
              + typesText + '\n' + '\n'.join(structs) + '\n'
              + f'using namespace {namespace};\n' + _RUNTIME_MAIN)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'accessors.cpp')
        with open(src, 'w') as f:
            f.write(source)
        exe = os.path.join(tmp, 'accessors')
        built = subprocess.run(
            ['clang++', '-std=c++20', '-Werror=shift-op-parentheses',
             '-Werror=shift-count-overflow', '-ftrivial-auto-var-init=pattern',
             f"-I{os.path.join(base_dir, 'common', 'systemc')}", src,
             os.path.join(base_dir, 'common', 'systemc', 'bitTwiddling.cpp'), '-o', exe],
            capture_output=True, text=True)
        if built.returncode != 0:
            print(f"  FAIL: rendered structs do not compile:\n{built.stderr}")
            return False
        ran = subprocess.run([exe], capture_output=True, text=True)
    print(ran.stdout.rstrip())
    if ran.returncode != 0:
        print("  FAIL: an accessor disagrees with pack()/unpack()")
        return False
    print("  PASS: every accessor agrees with pack() and unpack()")
    return True


def test_parameterizable_shifts_follow_config():
    """pRegSt {pa u8T, pb pT(P_W)}: pa sits above pb, so its shift is pb's
    width, spelled in the parameter, not the default width 8."""
    _header("parameterizable register shifts are spelled in the parameter")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        _, _, structData = _getStructData(prj, 'pRegSt')
        out = structures.registerFeatures(structData, '    ', prj, True)
    finally:
        cleanup([project_path, db_path] + arch_paths)
    paLines = [line.strip() for line in out if line.strip().startswith(('(( pa ', 'pa = '))]
    print("  " + "\n  ".join(paLines))
    bad = [line for line in paLines if 'P_W' not in line or '<< 8)' in line or '>> 8 )' in line]
    if len(paLines) != 2 or bad:
        print(f"  FAIL: pa's shift is not the expression in P_W: {bad or paLines}")
        return False
    print("  PASS: pa's _getValue and _setValue shift by pb's width in P_W")
    return True


def run_all_tests():
    print("=" * 70)
    print("TESTING: register _getValue/_setValue accessor emission")
    print("=" * 70)
    tests = [
        test_getvalue_one_term_per_field,
        test_setvalue_one_line_per_field_at_pack_position,
        test_parameterizable_shifts_follow_config,
        test_accessors_agree_with_pack_at_runtime,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
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
    sys.exit(run_all_tests())
