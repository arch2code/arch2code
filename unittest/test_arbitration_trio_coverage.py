#!/usr/bin/env python3
"""Declaration and compile-contract coverage for the multi-interface
arbitration trio.

`setExternalEvent(sc_event*)` / `isActive()` / `isNotActive()` is a channel
family's opt-in into the documented multi-interface arbitration pattern
(rules/skills/systemc-synchronization.md Section 1). A family that declares
one of the three without the other two silently breaks that pattern for
whichever caller reaches the missing piece: the pure-virtual declaration and
the concrete channel override must both be complete, never partial.

This suite discovers every `*_channel.h` under interfaces/ rather than
listing channel families by name, so a family authored tomorrow that opts
into the trio is checked without anyone updating this file. It also pins the
set of families that support the trio today, because the discovery-based
all-or-nothing check above cannot catch a family silently losing the trio
entirely (e.g. a future edit that removes both the pure-virtual declaration
and the concrete override together leaves nothing for that check to see).

Two kinds of check run here, and neither is a substitute for the other:

- The textual checks (test_trio_is_all_or_nothing,
  test_required_families_are_trio_complete) regex-match header text. They are
  fast and give a precise line-level message, but text matching alone cannot
  tell a well-formed override from a malformed one, an inaccessible member,
  or a template that fails to instantiate: `virtual bool isActive() override`
  matches the override regex whether or not it actually overrides anything.
- The compile checks (test_trio_compile_contract) generate one real C++
  translation unit per trio-complete family, explicitly instantiate that
  family's concrete channel template, and call setExternalEvent()/
  isActive()/isNotActive() through its *_in_if pointer. Explicit
  instantiation of a class with virtual member functions forces every
  virtual member -- not just the ones this file happens to call -- to
  compile, so a malformed signature or a template-instantiation failure in
  any of them fails the compile, not just a regex.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


# Families that support the full arbitration trio: a single SC_THREAD can
# service N ports of any of these via one shared sc_event, scanning
# isActive()/isNotActive() under a wait(event) loop. Every one of these must
# show up as trio-complete below; a family missing from this set has lost
# arbitration support entirely, which the discovery-based all-or-nothing
# check above cannot detect on its own since it only fires when a family
# declares part of the trio (e.g. raw/status/external_reg carry only
# setExternalEvent and never trip that check, but they also never claimed
# full trio support).
REQUIRED_FAMILIES = {
    'rdy_vld', 'axi_read', 'axi_write', 'axi4_stream', 'apb', 'memory',
}

PURE_VIRTUAL_RE = {
    'isActive': re.compile(r'virtual\s+bool\s+isActive\s*\(\s*\)\s*=\s*0\s*;'),
    'isNotActive': re.compile(r'virtual\s+bool\s+isNotActive\s*\(\s*\)\s*=\s*0\s*;'),
    'setExternalEvent': re.compile(
        r'virtual\s+void\s+setExternalEvent\s*\(\s*sc_event\s*\*\s*event\s*\)\s*=\s*0\s*;'),
}

OVERRIDE_RE = {
    'isActive': re.compile(r'\bisActive\s*\(\s*\)\s*override\b'),
    'isNotActive': re.compile(r'\bisNotActive\s*\(\s*\)\s*override\b'),
    'setExternalEvent': re.compile(
        r'setExternalEvent\s*\(\s*sc_event\s*\*\s*event\s*\)\s*override\b'),
}


def discover_channel_headers():
    """Map channel family name -> `*_channel.h` path, walking interfaces/.

    Discovery rather than a list: a channel family authored tomorrow is
    checked without this file being edited.
    """
    found = {}
    pattern = os.path.join(base_dir, 'interfaces', '*', '*_channel.h')
    for path in sorted(glob.glob(pattern)):
        family = os.path.basename(path)[:-len('_channel.h')]
        found[family] = path
    return found


def test_trio_is_all_or_nothing(headers):
    """A family that declares any one trio method must declare and
    implement all three; a partial family is a silent arbitration-pattern
    break for whichever caller reaches the missing piece."""
    trio_complete_families = set()
    for family, path in headers.items():
        with open(path, 'r') as f:
            text = f.read()

        declared = {name: bool(rx.search(text)) for name, rx in PURE_VIRTUAL_RE.items()}
        if not (declared['isActive'] or declared['isNotActive']):
            # Some families (external_reg, raw, status) declare only
            # setExternalEvent and never adopted isActive/isNotActive;
            # setExternalEvent alone is not treated as an opt-in below, since
            # it is also the marker of that separate, partial shape.
            continue

        implemented = {name: bool(rx.search(text)) for name, rx in OVERRIDE_RE.items()}

        for name in PURE_VIRTUAL_RE:
            check(declared[name],
                  f"{family}_channel.h declares '{name}' as pure virtual")
        for name in OVERRIDE_RE:
            check(implemented[name],
                  f"{family}_channel.h provides a concrete '{name}' override")

        if all(declared.values()) and all(implemented.values()):
            trio_complete_families.add(family)

    return trio_complete_families


def test_required_families_are_trio_complete(trio_complete_families):
    missing = REQUIRED_FAMILIES - trio_complete_families
    check(not missing,
          f"every family that must support the arbitration trio still does "
          f"(missing: {sorted(missing)})" if missing else
          "every family that must support the arbitration trio (rdy_vld, "
          "axi_read, axi_write, axi4_stream, apb, memory) still does")


# ---------------------------------------------------------------------------
# Compile-contract checks
# ---------------------------------------------------------------------------
#
# A trio-complete family's concrete channel template, and the number/shape of
# its payload type parameters, cannot be discovered generically: unlike the
# family name (from the filename) or the trio methods (from a fixed regex),
# the template argument list is a per-family fact of that channel's C++
# signature. FAMILY_COMPILE_SPECS is therefore a pinned map, one entry per
# trio-complete family, cribbed from real instantiations in the shipped
# examples (axiDemo for axi_read/axi_write/axi4_stream, helloWorld for
# rdy_vld, apbDecode for apb, mixed for memory) or, where no example
# instantiates the family, from its own channel header (notify_ack, pop_ack,
# push_ack, req_ack). A family that reaches trio-complete status without an
# entry here fails loudly below instead of silently skipping its compile
# check, so a new family cannot join the trio without also joining the real
# compile contract.
#
# dummyPayload<W> (defined inline in the generated translation unit) is a
# minimal stand-in for a generated payload struct (the same shape arch2code
# emits for e.g. axiAddrSt): a fixed-width value plus the handful of members
# every trio-complete channel calls on its template arguments somewhere in
# its body (getValueType, getStructValue, prt, and the pack()/_packedSt pair
# a couple of families use for a hash fallback), and _bitWidth as the
# compile-time constant every family reads to size its own structs.
FAMILY_COMPILE_SPECS = {
    'rdy_vld': {
        'channel': 'rdy_vld_channel<dummyPayload<32>>',
        'in_if': 'rdy_vld_in_if<dummyPayload<32>>',
    },
    'apb': {
        'channel': 'apb_channel<dummyPayload<32>, dummyPayload<32>>',
        'in_if': 'apb_in_if<dummyPayload<32>, dummyPayload<32>>',
    },
    'memory': {
        'channel': 'memory_channel<dummyPayload<32>, dummyPayload<32>>',
        'in_if': 'memory_in_if<dummyPayload<32>, dummyPayload<32>>',
    },
    'axi_read': {
        'channel': 'axi_read_channel<dummyPayload<32>, dummyPayload<32>>',
        'in_if': 'axi_read_in_if<dummyPayload<32>, dummyPayload<32>>',
    },
    'axi_write': {
        'channel': 'axi_write_channel<dummyPayload<32>, dummyPayload<32>, dummyPayload<4>>',
        'in_if': 'axi_write_in_if<dummyPayload<32>, dummyPayload<32>, dummyPayload<4>>',
    },
    'axi4_stream': {
        'channel': 'axi4_stream_channel<dummyPayload<32>, dummyPayload<8>, dummyPayload<8>>',
        'in_if': 'axi4_stream_in_if<dummyPayload<32>, dummyPayload<8>, dummyPayload<8>>',
    },
    'notify_ack': {
        # T is an unused "dummy template argument for consistency with other
        # interfaces" per the header's own comment, defaulted to bool.
        'channel': 'notify_ack_channel<>',
        'in_if': 'notify_ack_in_if<>',
    },
    'pop_ack': {
        'channel': 'pop_ack_channel<dummyPayload<32>>',
        'in_if': 'pop_ack_in_if<dummyPayload<32>>',
    },
    'push_ack': {
        'channel': 'push_ack_channel<dummyPayload<32>>',
        'in_if': 'push_ack_in_if<dummyPayload<32>>',
    },
    'req_ack': {
        'channel': 'req_ack_channel<dummyPayload<32>, dummyPayload<32>>',
        'in_if': 'req_ack_in_if<dummyPayload<32>, dummyPayload<32>>',
    },
}

TU_TEMPLATE = """\
// Compile contract for the '{family}' arbitration-trio channel family.
//
// Generated at test runtime by test_arbitration_trio_coverage.py: this is
// not hand-maintained source. Its only job is to make a real compiler prove
// what that test's textual regex checks cannot -- that {channel}
// actually compiles end to end, and that setExternalEvent()/isActive()/
// isNotActive() resolve through the {in_if} pointer with exactly the
// documented signatures (rules/skills/systemc-synchronization.md Section 1).
// A malformed override, an inaccessible signature, or a template
// instantiation failure fails this compile, not just a regex.
//
// Constructing {channel} (a concrete, non-abstract class) rather than
// explicitly instantiating the whole class template deliberately limits
// what this forces the compiler to check: a class's virtual member
// functions -- the trio among them -- are instantiated as part of
// instantiating the class itself, whether implicit or explicit, so
// constructing an instance already forces isActive()/isNotActive()/
// setExternalEvent() to compile. A non-virtual convenience member (an
// operator=, say) is only instantiated if this file actually calls it, so a
// defect confined to one of those -- unrelated to the trio this suite
// checks -- cannot fail this compile.
#include "systemc.h"
#include "{header}"

// A minimal stand-in for a generated payload struct (the same shape
// arch2code emits for e.g. axiAddrSt). See FAMILY_COMPILE_SPECS above for
// why this small a contract is sufficient.
template <unsigned W>
struct dummyPayload
{{
    static constexpr unsigned int _bitWidth = W;
    static constexpr unsigned int _byteWidth = (_bitWidth + 7) >> 3;
    static constexpr unsigned int _packedSize = (_byteWidth + 7) >> 3;
    typedef uint64_t _packedSt[_packedSize];
    uint64_t value = 0;
    dummyPayload() {{}}
    static const char* getValueType(void) {{ return ""; }}
    inline uint64_t getStructValue(void) const {{ return value; }}
    std::string prt(bool all = false) const {{ (void)all; return std::to_string(value); }}
    inline void pack(_packedSt &_ret) const {{ _ret[0] = value; }}
    inline void unpack(_packedSt &_src) {{ value = _src[0]; }}
}};

void trio_compile_check_{family}()
{{
    {channel} channel("trioCheck", "trioCheckBlock");
    {in_if} *ifacePtr = &channel;
    sc_event event;
    ifacePtr->setExternalEvent(&event);
    (void)ifacePtr->isActive();
    (void)ifacePtr->isNotActive();
}}
"""


def resolve_toolchain():
    """CXX / C++ standard exactly as include/make/a2c-common.mk computes
    them, by asking make to evaluate that file rather than re-encoding its
    ifndef USE_GCC switch here: if that file's logic changes, this keeps
    tracking it instead of silently drifting from what the real build does.
    """
    mk_path = os.path.join(base_dir, 'include', 'make', 'a2c-common.mk')
    tmpdir = tempfile.mkdtemp(prefix='trio_compile_toolchain_')
    try:
        printvars_path = os.path.join(tmpdir, 'printvars.mk')
        with open(printvars_path, 'w') as f:
            f.write("print-%:\n\t@echo '$*=$($*)'\n")
        try:
            result = subprocess.run(
                ['make', '-f', mk_path, '-f', printvars_path,
                 f'A2C_ROOT={base_dir}', f'REPO_ROOT={tmpdir}',
                 'PROJECTNAME=trioCompileCheck',
                 'TB_TOP_MODULE=trioCompileCheck',
                 'HDL_TOP_MODULE=trioCompileCheck',
                 'print-CXX', 'print-C_STD_VER'],
                capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            return None, f"could not run make against {mk_path}: {exc}"
        if result.returncode != 0:
            return None, (f"{mk_path} did not evaluate cleanly: "
                          f"{result.stderr.strip()}")
        values = {}
        for line in result.stdout.splitlines():
            key, sep, value = line.partition('=')
            if sep:
                values[key] = value
        if 'CXX' not in values or 'C_STD_VER' not in values:
            return None, f"{mk_path} did not report CXX/C_STD_VER"
        return (values['CXX'], values['C_STD_VER']), None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def include_dirs():
    """The -I set every project build assembles for A2C_SRC_DIRS in
    include/make/a2c-systemc.mk: common/systemc, common/scmain, and every
    interfaces/* family directory. pro/interfaces is out of scope for this
    base-only check (see FAMILY_COMPILE_SPECS: every trio-complete family
    checked here ships in base)."""
    dirs = [os.path.join(base_dir, 'common', 'systemc'),
            os.path.join(base_dir, 'common', 'scmain')]
    dirs += sorted(glob.glob(os.path.join(base_dir, 'interfaces', '*')))
    return [d for d in dirs if os.path.isdir(d)]


def env_include_flags():
    """BOOST_INCLUDE / SYSTEMC_INCLUDE exactly as include/make/a2c-systemc.mk
    requires them: that file's own ifndef checks abort the real build the
    same way if they are unset, so an unset var here means the compile check
    cannot run in this environment, not that the code is wrong.
    /usr/local/include is the fixed third entry that file's CPP_INCLUDES
    always adds alongside them.
    """
    missing = [v for v in ('SYSTEMC_INCLUDE', 'BOOST_INCLUDE')
               if not os.environ.get(v)]
    if missing:
        return None, missing
    return ([f"-I{os.environ['BOOST_INCLUDE']}",
             f"-I{os.environ['SYSTEMC_INCLUDE']}",
             "-I/usr/local/include"], None)


def compile_family(family, header_path, cxx, cxxstd, include_flags, workdir):
    spec = FAMILY_COMPILE_SPECS.get(family)
    if spec is None:
        return False, (
            f"family '{family}' is trio-complete but has no compile-check "
            f"template spec in FAMILY_COMPILE_SPECS (test_arbitration_trio_"
            f"coverage.py); a family joining the arbitration trio must add "
            f"one there so it gets a real compile, not just the textual "
            f"check above")

    src_path = os.path.join(workdir, f'trio_compile_{family}.cpp')
    with open(src_path, 'w') as f:
        f.write(TU_TEMPLATE.format(
            family=family, header=os.path.basename(header_path),
            channel=spec['channel'], in_if=spec['in_if']))

    cmd = [cxx, f'-std={cxxstd}', '-fsyntax-only',
           '-DSC_CPLUSPLUS=201703L', '-DSC_INCLUDE_DYNAMIC_PROCESSES',
           '-DBOOST_STACKTRACE_LINK'] + include_flags + [src_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"could not invoke {cxx} for '{family}': {exc}"
    if result.returncode != 0:
        return False, (
            f"{family}_channel.h fails a real compile of {spec['channel']} "
            f"calling setExternalEvent()/isActive()/isNotActive() through "
            f"{spec['in_if']}:\n{result.stderr}")
    return True, (f"{family}_channel.h compiles {spec['channel']} and the "
                  f"trio resolves through {spec['in_if']}")


def test_trio_compile_contract(trio_complete_families, headers):
    """Every discovered trio-complete family gets a real compile, not just a
    regex match. See the module docstring and the section header above."""
    print("\n[compile] every trio-complete family's channel actually "
          "compiles, and the trio resolves through its *_in_if pointer")
    toolchain, tc_err = resolve_toolchain()
    if toolchain is None:
        check(False, f"cannot resolve compiler/standard to run the compile "
                     f"check ({tc_err})")
        return
    cxx, cxxstd = toolchain

    include_flags, missing_env = env_include_flags()
    if include_flags is None:
        print(f"  SKIP: {', '.join(missing_env)} not set in this "
              f"environment, so the SystemC/Boost include path "
              f"include/make/a2c-systemc.mk requires cannot be resolved; "
              f"the compile portion of this check is skipped (the textual "
              f"checks above still ran). Set {', '.join(missing_env)} the "
              f"same way the example project builds do to enable it.")
        return
    include_flags = include_flags + [f'-I{d}' for d in include_dirs()]

    workdir = tempfile.mkdtemp(prefix='trio_compile_check_')
    try:
        for family in sorted(trio_complete_families):
            ok, message = compile_family(family, headers[family], cxx,
                                         cxxstd, include_flags, workdir)
            check(ok, message)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


MALFORMED_OVERRIDE_SRC = """\
// A minimal, SystemC-independent reproduction of the exact defect class
// this suite's compile checks exist to catch: a trio method's concrete
// override signature has drifted from its pure-virtual declaration.
class fake_event;

class trio_in_if {
public:
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent(fake_event *event) = 0;
};

class trio_channel : public trio_in_if {
public:
    bool isActive() override { return false; }
    bool isNotActive() override { return true; }
    // malformed: the parameter type no longer matches the base
    // declaration, so 'override' cannot bind to anything.
    void setExternalEvent(int event) override { (void)event; }
};

int main() {
    trio_channel c;
    trio_in_if *p = &c;
    fake_event *e = nullptr;
    p->setExternalEvent(e);
    return 0;
}
"""


def test_compile_harness_detects_malformed_override():
    """Proves the compile checks above are load-bearing: a malformed trio
    override is a real compile failure, something no regex match can tell
    apart from a well-formed one.

    This isolates the defect class the malformed-signature case names,
    independent of SystemC or the interfaces/ library, so it runs without
    any environment dependency and stays a permanent regression on its own.
    """
    print("\n[compile] a malformed trio override fails a real compile "
          "(compile-check harness self-test)")
    cxx = shutil.which('g++') or shutil.which('clang++')
    if cxx is None:
        check(False, "neither g++ nor clang++ is on PATH; cannot prove the "
                     "compile-check harness detects a malformed override")
        return
    workdir = tempfile.mkdtemp(prefix='trio_compile_harness_selftest_')
    try:
        src_path = os.path.join(workdir, 'malformed_override.cpp')
        with open(src_path, 'w') as f:
            f.write(MALFORMED_OVERRIDE_SRC)
        result = subprocess.run([cxx, '-std=c++17', '-fsyntax-only', src_path],
                                capture_output=True, text=True, timeout=60)
        check(result.returncode != 0,
              "a trio method whose concrete override signature no longer "
              "matches its pure-virtual declaration fails a real compile, "
              "which is what the compile check above relies on")
        check('override' in result.stderr,
              f"the compiler names 'override' as the problem, not a "
              f"generic error, so the failure is diagnosable "
              f"(stderr: {result.stderr.strip()[:400]})")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    print("=" * 72)
    print("TESTING ARBITRATION TRIO COVERAGE (DECLARATION + COMPILE)")
    print("=" * 72)
    headers = discover_channel_headers()
    check(len(headers) > 0, "discovered at least one *_channel.h under interfaces/")

    trio_complete_families = test_trio_is_all_or_nothing(headers)
    print(f"  trio-complete families: {sorted(trio_complete_families)}")
    test_required_families_are_trio_complete(trio_complete_families)

    test_trio_compile_contract(trio_complete_families, headers)
    test_compile_harness_detects_malformed_override()

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all arbitration trio declaration and compile checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
