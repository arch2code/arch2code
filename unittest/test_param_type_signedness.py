#!/usr/bin/env python3
"""Signedness of the emitted C++ type alias for parameterizable types.

`includeTypes` (templates/systemc/includes.py) has two arms. The
non-parameterizable arm emits `platformDataType`, which already encodes
`isSigned`. The parameterizable arm emits its own container, because a
parameterizable type must be sized by `maxBitwidth` (the worst case across
variants) and not by `realwidth` (the width at default parameter values, which
is what `platformDataType` is derived from). That container must still honour
`isSigned`, otherwise a declared-signed field silently becomes unsigned in the
model while the SystemVerilog emitter keeps it signed.

Cases asserted against rendered text:
- signed parameterizable scalar   -> `using T = int64_t`
- unsigned parameterizable scalar -> `using T = uint64_t`
- signed non-parameterizable      -> unchanged `typedef int16_t T`
- signed parameterizable multi-word (maxBitwidth > 64) keeps `uint64_t word[N]`;
  that shape has no arithmetic operators, so signedness is not observable on it
  and it is deliberately left alone (it also receives no sign extension today).

signedParamT resolves to 8 bits at default parameters but can reach 40, so its
`platformDataType` is int8_t. The exact expected text therefore also pins the
container to the worst case rather than to the default-parameter width.
"""

import os
import sys
import tempfile
from types import SimpleNamespace

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectCreate, projectOpen
from pysrc.systemcGen import genSystemC
from templates.systemc.includes import includeTypes


ARCH = """ipParameters:
  constants:
    WIDTH: { value: 8, maxValue: 40, desc: "backing width, worst case wider than default" }
    WIDE_WIDTH: { value: 70, maxValue: 128, desc: "backing width past one 64 bit word" }
  types:
    signedParamT:
      width: WIDTH
      isSigned: true
      desc: "signed parameterizable scalar"
    unsignedParamT:
      width: WIDTH
      desc: "unsigned parameterizable scalar"
    signedWideParamT:
      width: WIDE_WIDTH
      isSigned: true
      desc: "signed parameterizable multi word"

types:
  signedFixedT:
    width: 12
    isSigned: true
    desc: "signed non parameterizable"

structures:
  paramSt:
    signedValue: { varType: signedParamT }
    unsignedValue: { varType: unsignedParamT }

blocks:
  consumer:
    desc: "block that backs the exposed params"
    params: [WIDTH, WIDE_WIDTH]
  top:
    desc: "top"

instances:
  uTop: { container: top, instanceType: top }
  uCons: { container: top, instanceType: consumer, variant: v0 }

parameters:
  consumer:
    v0:
      WIDTH: 8
      WIDE_WIDTH: 70
"""

PROJECT = """projectName: param_signedness_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {arch_basename}
"""


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


def _renderTypes(prj):
    """Render the `types` section of the SystemC includes template for the context
    that declares the fixture, exactly as the .cppm generator does."""
    context = prj.data['blocks'][prj.getQualBlock('consumer')]['_context']
    data = prj.getContextData([context], genSystemC.dataTypeMappings)
    return includeTypes(SimpleNamespace(mode='module'), prj, data)


def _aliasLine(rendered, typeName):
    for line in rendered.split('\n'):
        if f' {typeName} ' in line or f' {typeName};' in line:
            return line.strip()
    return None


def test_param_type_alias_signedness():
    print(f"\n{'='*70}\nTest: parameterizable type alias honours isSigned\n{'='*70}")
    arch_path = _write_temp(ARCH, '.yaml', 'arch_signedness_')
    project_path = _write_temp(
        PROJECT.format(arch_basename=os.path.basename(arch_path)),
        '_project.yaml', 'proj_signedness_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    try:
        projectCreate(project_path, db_path)
        rendered = _renderTypes(projectOpen(db_path))

        expected = {
            'signedParamT':
                'template<typename Config> using signedParamT = int64_t; '
                '// [max:40] signed parameterizable scalar',
            'unsignedParamT':
                'template<typename Config> using unsignedParamT = uint64_t; '
                '// [max:40] unsigned parameterizable scalar',
            'signedFixedT':
                'typedef int16_t signedFixedT; // [12] signed non parameterizable',
            'signedWideParamT':
                'template<typename Config> struct signedWideParamT { uint64_t word[ 2 ]; }; '
                '// [max:128] signed parameterizable multi word',
        }
        ok = True
        for typeName, want in expected.items():
            got = _aliasLine(rendered, typeName)
            if got != want:
                print(f"  FAIL: {typeName}\n    expected: {want}\n    got:      {got}")
                ok = False
            else:
                print(f"  ok: {got}")

        if not ok:
            print("\n  Rendered types section:")
            print('    ' + '\n    '.join(rendered.split('\n')))
            return False
        print("  PASS: parameterizable aliases honour isSigned")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)
        _cleanup([project_path, arch_path, db_path])


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: parameterizable C++ type alias signedness")
    print("="*70)
    tests = [
        test_param_type_alias_signedness,
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

    print("\n" + "="*70 + "\nTEST SUMMARY\n" + "="*70)
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
