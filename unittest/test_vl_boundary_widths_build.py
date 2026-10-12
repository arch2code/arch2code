#!/usr/bin/env python3
"""Every HDL wrapper top's boundary pins agree in every emitter.

Four artifacts describe each pin of a Verilated wrapper top: the VCS port map
and the Xcelium foreign-module shell (both from `--vlBoundary`), the
SystemVerilog top (its port list and Verilator's own `V<top>.h`), and the
SystemC HDL bridge (compiled against the Verilated class by the Verilated
build). A disagreement mis-sizes or mis-types a simulator port. The pins
Verilator declares in `V<top>.h` are the ones the SystemC side binds, so each
top's header must list exactly the pins of its port map and Xcelium shell, with
the same direction and SystemC type.

Each top is compared against the full ordered pin list (pin, direction, width,
vector): interface pins in port then signal order, then the block's declared
clocks, then its resets. A vector pin is one typed by an eval hdlparam or a
bound parameterizable payload, or wider than one bit; it stays a vector at
width 1, so every simulator binds it as sc_bv<1>, which is what the
hand-written BFMs read. On the SystemVerilog top only a vector pin of width 1
carries `/*verilator sc_bv*/`; Verilator binds wider pins as sc_bv without it.

Fixture `fixtures/vl-boundary-widths` covers every top shape (no-param single
top, standalone per-variant tops, pair-registration tops of an inheriting child,
foreign owner-qualified tops of a reused leaf), every signal form (struct, type
and typeStruct payloads bound, unbound and parameterizable, optional parameters
left as gaps, type-named AXI and external_reg signals, eval hdlparams over fixed
and parameterizable structures), variants whose payloads are one byte and one
bit, two clock domains, an output clock and reset, and a top with no reset. The
expected pins are computed here from the fixture YAML and the protocol signal
tables below, independently of the generator.

The copy is built base-only, so it lives under builder/base (a project outside
it merges pro, whose tandem tee for axi_read takes no ID arguments). It is
gitignored and removed after the run; the run fails if it is left behind.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'vl-boundary-widths')
WORK_PREFIX = 'vl_boundary_widths_'
BUILD_JOBS = '8'

V0 = {'P_W': 5, 'P_N': 16}
V1 = {'P_W': 12, 'P_N': 40}
V2 = {'P_W': 1, 'P_N': 4}
# Every wrapper top the build must list, with the block it wraps and the
# parameter values it is built at.
TOPS = {
    'dutA_hdl_sv_wrapper': ('dutA', {}),
    'dutC2_hdl_sv_wrapper': ('dutC2', {}),
    'dutOut_hdl_sv_wrapper': ('dutOut', {}),
    'dutNoRst_hdl_sv_wrapper': ('dutNoRst', {}),
    'dutP_v0_hdl_sv_wrapper': ('dutP', V0),
    'dutP_v1_hdl_sv_wrapper': ('dutP', V1),
    'dutP_v2_hdl_sv_wrapper': ('dutP', V2),
    'dutQ_v0_hdl_sv_wrapper': ('dutQ', V0),
    'dutQ_v1_hdl_sv_wrapper': ('dutQ', V1),
    'dutQ_v2_hdl_sv_wrapper': ('dutQ', V2),
    'p5_wrapQ_c4_dutQ_v0_hdl_sv_wrapper': ('dutQ', V0),
    'p5_wrapQ_c4_dutQ_v1_hdl_sv_wrapper': ('dutQ', V1),
    'p5_wrapQ_c4_dutQ_v2_hdl_sv_wrapper': ('dutQ', V2),
    'vbwTop_fLeaf_vA_hdl_sv_wrapper': ('fLeaf', V0),
    'vbwTop_fLeaf_vB_hdl_sv_wrapper': ('fLeaf', V1),
    'vbwTop_fLeaf_vC_hdl_sv_wrapper': ('fLeaf', V2),
    'fLeaf_dflt_hdl_sv_wrapper': ('fLeaf', V0),
}
# Each block's ports in wrapper order, with the side the block takes; every
# port is named after its interface.
PORTS = {
    'dutA': [('axr_gap', 'dst'), ('axw_unb', 'src'), ('ext', 'src'), ('i3', 'dst'),
             ('i4', 'src'), ('axs', 'dst')],
    'dutC2': [('axs1', 'src')],
    'dutOut': [],
    'dutNoRst': [],
    'dutP': [('fr', 'dst'), ('fs', 'src'), ('fh', 'src'), ('ih2', 'dst'), ('ip', 'dst'),
             ('ip2', 'src'), ('axw_p', 'src')],
    'dutQ': [('fs', 'src'), ('fh', 'src'), ('ip', 'dst'), ('axw_p', 'src')],
    'fLeaf': [('fr', 'dst'), ('fs', 'src'), ('fh', 'src')],
}
# Per protocol, each signal in declaration order and what sizes it: an int is a
# fixed width, a name is a payload parameter, ('bytes', name) is the byte count
# of that parameter's payload. The AXI and external_reg integers are the widths
# of the types those signals name (interfaces/axi_read/axi_types.yaml and
# _extRegWriteT).
SIGNALS = {
    'axi_read': [('araddr', 'addr_t'), ('arid', 'id_t'), ('arlen', 8), ('arsize', 3),
                 ('arburst', 2), ('aruser', 'aruser_t'), ('arvalid', 1), ('arready', 1),
                 ('rdata', 'data_t'), ('rid', 'id_t'), ('rresp', 2), ('rlast', 1),
                 ('ruser', 'ruser_t'), ('rvalid', 1), ('rready', 1)],
    'axi_write': [('awaddr', 'addr_t'), ('awid', 'id_t'), ('awlen', 8), ('awsize', 3),
                  ('awburst', 2), ('awuser', 'awuser_t'), ('awvalid', 1), ('awready', 1),
                  ('wdata', 'data_t'), ('wid', 'id_t'), ('wstrb', 'strb_t'), ('wlast', 1),
                  ('wuser', 'wuser_t'), ('wvalid', 1), ('wready', 1), ('bresp', 2),
                  ('bid', 'id_t'), ('buser', 'buser_t'), ('bvalid', 1), ('bready', 1)],
    'axi4_stream': [('tvalid', 1), ('tready', 1), ('tdata', 'tdata_t'),
                    ('tstrb', ('bytes', 'tdata_t')), ('tkeep', ('bytes', 'tdata_t')),
                    ('tlast', 1), ('tid', 'tid_t'), ('tdest', 'tdest_t'), ('tuser', 'tuser_t')],
    'external_reg': [('wdata', 'data_t'), ('rdata', 'data_t'), ('write', 2)],
    'idt': [('vld', 1), ('s', 's_t'), ('ty', 'ty_t'), ('ts', 'ts_t'), ('o1', 'o1_t'),
            ('o2', 'o2_t'), ('o3', 'o3_t'), ('rdy', 1)],
    'idth': [('vld', 1), ('s', 's_t'), ('sb', ('bytes', 's_t')), ('ts', 'ts_t'),
             ('o2', 'o2_t'), ('rdy', 1)],
}
# Per protocol, the signals the dst side drives.
DST_DRIVEN = {
    'axi_read': {'arready', 'rid', 'rdata', 'rresp', 'rlast', 'ruser', 'rvalid'},
    'axi_write': {'awready', 'wready', 'bresp', 'bid', 'buser', 'bvalid'},
    'axi4_stream': {'tready'},
    'external_reg': {'rdata'},
    'idt': {'rdy'},
    'idth': {'rdy'},
}
# Width of an optional payload parameter left unbound.
UNBOUND = {'aruser_t': 1, 'ruser_t': 1, 'awuser_t': 1, 'wuser_t': 1, 'buser_t': 1,
           'id_t': 4, 'tuser_t': 1, 'o1_t': 2, 'o2_t': 3, 'o3_t': 5}

PORTMAP_TYPES = {True: ('bitvector', 'sc_bv'), False: ('bit', 'bool')}
XCELIUM_PIN = re.compile(r'sc_(in|out)<(bool|sc_bv<(\d+)>)> (\w+);')
# Every port member of the Verilated class, whatever its type, so a pin
# Verilator types other than bool or sc_bv still reaches the comparison.
VERILATED_PIN = re.compile(r'sc_core::sc_(in|out)<(.+?)>\s*&(\w+);')
SV_PORT = re.compile(r'^\s*(input|output)\b.*?(\w+)(\s*/\*verilator sc_bv\*/)?\s*,?\s*$')
DIRECTION = {'in': 'input', 'out': 'output'}


class Design:
    """Payload widths and pin lists of the fixture at given parameter values."""

    def __init__(self, work):
        sections = {'constants': {}, 'types': {}, 'structures': {}, 'interfaces': {},
                    'blocks': {}}
        self.params = set()
        for path in (os.path.join(work, 'leaf', 'yaml', 'vbwLeaf.yaml'),
                     os.path.join(work, 'top', 'yaml', 'vbwTop.yaml')):
            with open(path) as f:
                doc = yaml.safe_load(f)
            for section in sections:
                sections[section].update(doc.get(section) or {})
            ip = doc.get('ipParameters') or {}
            sections['constants'].update(ip.get('constants') or {})
            sections['types'].update(ip.get('types') or {})
            self.params |= set(ip.get('constants') or {})
        self.constants = {k: v['value'] for k, v in sections['constants'].items()}
        self.types = sections['types']
        self.structures = sections['structures']
        self.interfaces = sections['interfaces']
        self.blocks = sections['blocks']

    def width(self, name, values):
        env = dict(self.constants, **values)

        def value(token):
            return env[token] if isinstance(token, str) else token
        if name in self.types:
            row = self.types[name]
            signed = 1 if row.get('isSigned') else 0
            if 'widthLog2' in row:
                return value(row['widthLog2']).bit_length() + signed
            if 'widthLog2minus1' in row:
                return (value(row['widthLog2minus1']) - 1).bit_length() + signed
            return value(row['width'])
        return sum(self.width(field['varType'], values) * value(field.get('arraySize', 1))
                   for field in self.structures[name].values())

    def parameterizable(self, name):
        if name in self.types:
            row = self.types[name]
            return any(row.get(key) in self.params
                       for key in ('width', 'widthLog2', 'widthLog2minus1'))
        return any(self.parameterizable(field['varType']) or field.get('arraySize') in self.params
                   for field in self.structures[name].values())

    def clock_reset_pins(self, block):
        # An omitted clocks:/resets: is the implicit clk/rst_n; resets: {} is none.
        row = self.blocks[block]
        clocks = row['clocks'] if 'clocks' in row else {'clk': {}}
        resets = row['resets'] if 'resets' in row else {'rst_n': {}}
        return [(name, (attrs or {}).get('direction', 'input'), 1, False)
                for name, attrs in list(clocks.items()) + list(resets.items())]

    def expected_pins(self, block, values):
        """[(pin, direction, width, vector)] of a wrapper top, in boundary order."""
        pins = []
        for port, side in PORTS[block]:
            row = self.interfaces[port]
            protocol = row['interfaceType']
            bound = {s['structureType']: s['structure'] for s in row['structures']}
            for signal, sizing in SIGNALS[protocol]:
                if isinstance(sizing, int):
                    width, vector = sizing, sizing > 1
                elif isinstance(sizing, tuple):
                    width, vector = (self.width(bound[sizing[1]], values) + 7) // 8, True
                elif sizing in bound:
                    width = self.width(bound[sizing], values)
                    vector = self.parameterizable(bound[sizing]) or width > 1
                else:
                    width = UNBOUND[sizing]
                    vector = width > 1
                driven = 'dst' if signal in DST_DRIVEN[protocol] else 'src'
                direction = 'output' if driven == side else 'input'
                pins.append((f'{port}_{signal}', direction, width, vector))
        return pins + self.clock_reset_pins(block)


def a2c_env():
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return env


def make(work, target, subdir='top', extra=()):
    """Run one make target in the copy, overriding FIXTURE_ROOT and A2C_ROOT
    so the copy and the builder under test are used."""
    return subprocess.run(
        ['make', '-C', os.path.join(work, subdir), f'-j{BUILD_JOBS}',
         f'FIXTURE_ROOT={work}', f'A2C_ROOT={base_dir}', *extra, target],
        capture_output=True, text=True, timeout=3600, env=a2c_env())


def generate(work):
    """Scaffold and generate the copy, then write the per-top boundary files.
    Returns None on success, else a message."""
    for target in ('db', 'newmodule', 'gen'):
        result = make(work, target)
        if result.returncode != 0:
            return f"make {target} failed (rc={result.returncode})\n{result.stdout}\n{result.stderr}"
    # The boundary-file rule a2c-common.mk runs for VCS/Xcelium builds.
    result = make(work, os.path.join(work, 'top', '.gen', 'vl', '.boundary'))
    if result.returncode != 0:
        return f"boundary files failed (rc={result.returncode})\n{result.stdout}\n{result.stderr}"
    return None


def pin_type(vector, width):
    return f'sc_bv<{width}>' if vector else 'bool'


def compare(top, artifact, expected, actual):
    if actual == expected:
        return []
    lines = [f"{top} {artifact} differs from the expected pins:"]
    for index in range(max(len(expected), len(actual))):
        want = expected[index] if index < len(expected) else None
        got = actual[index] if index < len(actual) else None
        if want != got:
            lines.append(f"    [{index}] expected {want}, got {got}")
    return ['\n'.join(lines)]


def read_portmap(path):
    with open(path) as f:
        return [tuple(line.split()) for line in f if line.strip() and not line.startswith('#')]


def read_xcelium(path):
    with open(path) as f:
        return [(m.group(4), DIRECTION[m.group(1)], pin_type(m.group(2) != 'bool', m.group(3)))
                for m in XCELIUM_PIN.finditer(f.read())]


def read_sv_top(work, top):
    """(pin, direction, marked) of the SystemVerilog top module's ports, in order."""
    pattern = re.compile(rf'^module {top}\b')
    for path in glob.glob(os.path.join(work, '*', 'verif', '*.sv')):
        with open(path) as f:
            lines = f.read().splitlines()
        for index, line in enumerate(lines):
            if not pattern.match(line):
                continue
            ports = []
            for portLine in lines[index:]:
                if portLine.startswith(');'):
                    return ports
                m = SV_PORT.match(portLine)
                if m:
                    ports.append((m.group(2), m.group(1), bool(m.group(3))))
    return None


def check_boundary_files(work, design):
    """Port map, Xcelium shell and SystemVerilog top port list of every top."""
    problems = []
    vl = os.path.join(work, 'top', '.gen', 'vl')
    listed = {os.path.basename(p)[:-len('.portmap')] for p in glob.glob(os.path.join(vl, '*.portmap'))}
    if listed != set(TOPS):
        problems.append(f"boundary tops {sorted(listed)} differ from the expected {sorted(TOPS)}")
    for top, (block, values) in TOPS.items():
        expected = design.expected_pins(block, values)
        if top in listed:
            problems += compare(top, 'portmap',
                                [(pin, str(width), *PORTMAP_TYPES[vector])
                                 for pin, _, width, vector in expected],
                                read_portmap(os.path.join(vl, f'{top}.portmap')))
            problems += compare(top, 'Xcelium shell',
                                [(pin, direction, pin_type(vector, width))
                                 for pin, direction, width, vector in expected],
                                read_xcelium(os.path.join(vl, f'{top}_xcelium.h')))
        svTop = read_sv_top(work, top)
        if svTop is None:
            problems.append(f"{top}: no SystemVerilog module of that name")
            continue
        # Only a vector pin one bit wide carries the sc_bv marker.
        problems += compare(top, 'SystemVerilog top ports',
                            [(pin, direction, vector and width == 1)
                             for pin, direction, width, vector in expected],
                            svTop)
    return problems


def read_verilated(path):
    """(pin, direction, SystemC type) of every port of a Verilated class."""
    with open(path) as f:
        return [(m.group(3), DIRECTION[m.group(1)],
                 re.sub(r'\s+', '', m.group(2)).replace('sc_dt::', ''))
                for m in VERILATED_PIN.finditer(f.read())]


def check_verilated_build(work, design):
    """Verilate every top and compile the SystemC side, including the BFM
    conversions; then read each top's pins back from Verilator's own header
    and hold them to the expected pins, the port map and the Xcelium shell."""
    built = make(work, 'all', os.path.join('top', 'rundir'), extra=('VL_DUT=1',))
    problems = []
    if built.returncode != 0:
        errors = [line for line in (built.stdout + built.stderr).splitlines()
                  if 'error' in line.lower() and not line.startswith(('clang++', 'g++'))]
        problems.append(f"Verilated build failed (rc={built.returncode}):\n" + '\n'.join(errors[:20]))
    for top, (block, values) in TOPS.items():
        header = os.path.join(work, 'top', 'rundir', 'build', 'vl', 'obj_dir', top, f'V{top}.h')
        if not os.path.exists(header):
            problems.append(f"{top}: no Verilated header {header}")
            continue
        # Verilator groups its members by type, so the pins compare as sorted
        # lists: every pin present once, none extra. The SystemVerilog top
        # port list above holds the order.
        actual = sorted(read_verilated(header))
        expected = sorted((pin, direction, pin_type(vector, width))
                          for pin, direction, width, vector in design.expected_pins(block, values))
        problems += compare(top, 'Verilated header', expected, actual)
        vl = os.path.join(work, 'top', '.gen', 'vl')
        shell = sorted(read_xcelium(os.path.join(vl, f'{top}_xcelium.h')))
        problems += compare(top, 'Verilated header against the Xcelium shell', shell, actual)
        portmap = sorted((pin, pin_type(scType == 'sc_bv', width))
                         for pin, width, _, scType in read_portmap(os.path.join(vl, f'{top}.portmap')))
        problems += compare(top, 'Verilated header against the port map', portmap,
                            sorted((pin, scType) for pin, _, scType in actual))
    return problems


def run_all_tests():
    print("\n" + "=" * 70)
    print("VERILATED WRAPPER BOUNDARY PINS ACROSS EMITTERS")
    print("=" * 70)
    results = []
    work = tempfile.mkdtemp(prefix=WORK_PREFIX, dir=test_dir)
    try:
        shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
        failure = generate(work)
        if failure:
            print(f"  FAIL: {failure}")
            results.append(('generate', False))
        else:
            design = Design(work)
            for name, check in (('boundary files', check_boundary_files),
                                ('Verilated build', check_verilated_build)):
                print(f"\n{name}")
                problems = check(work, design)
                for problem in problems:
                    print(f"  FAIL: {problem}")
                if not problems:
                    print("  PASS")
                results.append((name, not problems))
    finally:
        remove_tree(work)
    print("\ntemporary copy removed")
    left = glob.glob(os.path.join(test_dir, f'{WORK_PREFIX}*'))
    if left:
        print(f"  FAIL: temporary copies left under {test_dir}: {left}")
    else:
        print("  PASS")
    results.append(('temporary copy removed', not left))

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
