#!/usr/bin/env python3
"""getVlTopBoundaryPins()/calcVlTops() width coverage for the VCS port map and
Xcelium shell generator.

Two gaps in VLTOPS[top].structWidths, both against the same mechanism:
calcVlTops() persists, per wrapper top, the evaluated width of every
parameterizable structure the create-time resolver can reach, and
getVlTopBoundaryPins() looks up a pin's width there.

1. A block that is never instantiated in this project (an exported/library
   leaf) is never flagged isParameterizable by calcBlockConfigInfo (nothing
   ever connects an instance of it, so the own-surface walk never runs), so
   deriveParameterizedDeclSets never puts its structures into
   blockParameterizedDecls. getBDDefinitionPorts still synthesises its
   declared ports directly from ports:, and one of them carries a
   structurally parameterizable payload (declared elsewhere, consumed here at
   its default value) that calcVlTops must still size.

2. An interface's eval-derived hdlparam (AXI4-Stream tstrb_t/tkeep_t, a byte
   count computed from tdata_t) must track the SELECTED TOP's resolved
   payload width, not the structure's nominal (default-value) width. At a
   1-byte top it stays a vector pin, so Verilator, VCS and Xcelium all bind it
   as sc_bv<1>, the type the hand-written BFM reads.

A third cell covers a signal whose signalType names a type (external_reg
`write`): its pin and SV wrapper port take the type's width rather than the
1-bit default, and the system file declaring that type emits no per-context
include or package.

A fourth cell covers clock and reset pins: they follow the block's declared
clocks then resets, with each one's direction, and a block declaring
`resets: {}` has no reset pin.

A fifth cell covers a payload typed by eval constants derived from a
parameter: at a non-default variant the VCS port map and Xcelium shell take
the width the variant's RTL computes, through a chain of eval constants.
"""

import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import build_database, cleanup, find_block  # noqa: E402
from pysrc.processYaml import projectOpen  # noqa: E402
import pysrc.intf_gen_utils as intf_gen_utils  # noqa: E402
import pysrc.vlBoundaryGen as vlBoundaryGen  # noqa: E402


TRANSIT_ARCH = """
ipParameters:
    constants:
        WIDTH: { value: 8, maxValue: 32, desc: "Payload width" }
    types:
        pixelT: { width: WIDTH, maxBitwidth: 32, desc: "Parameterizable payload" }

types:
    tagT: { width: 8, desc: "Sample tag" }

structures:
    xferSt:
        tag:  { varType: tagT,   desc: "Sample tag" }
        data: { varType: pixelT, desc: "Parameterizable payload" }

interfaces:
    xferIf:
        desc: "Parameterized push/ack channel"
        interfaceType: push_ack
        structures:
            - { structure: xferSt, structureType: data_t }

blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    leaf:
        desc: "Exported leaf IP: consumes the parameterizable interface at its default WIDTH, declares no params: itself, and is never instantiated"
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        clocks:
            clk: { period: 10 }
        ports:
            in:  { interface: xferIf, direction: dst }
            out: { interface: xferIf, direction: src }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""


def test_paramsless_transit_leaf_boundary_pins():
    """A params-less, uninstantiated transit leaf's wrapper boundary sizes its
    parameterizable payload pin instead of raising KeyError out of
    getVlTopBoundaryPins()."""
    print("params-less uninstantiated transit leaf: boundary pin width")
    db_path, project_path, arch_paths = build_database(
        TRANSIT_ARCH, top_instance='top_tb', project_name='vl_boundary_transit')
    try:
        prj = projectOpen(db_path)
        leafKey, leafRow = find_block(prj, 'leaf')
        ok = True
        if leafRow['isParameterizable']:
            print("FAIL: 'leaf' unexpectedly flagged isParameterizable; this "
                  "cell no longer covers the never-instantiated transit shape")
            ok = False
        vltops = prj.config.getConfig('VLTOPS')
        leafTop = next((t for t, v in vltops.items() if v['blockKey'] == leafKey), None)
        if leafTop is None:
            print("FAIL: no VLTOPS entry for 'leaf'")
            return False
        blockData = prj.getBlockData(leafKey)
        try:
            pins = prj.getVlTopBoundaryPins(blockData, leafTop)
        except KeyError as e:
            print(f"FAIL: getVlTopBoundaryPins() raised KeyError {e}")
            return False
        dataPin = next((p for p in pins if p['pin'] == 'in_data'), None)
        if dataPin is None:
            print(f"FAIL: no 'in_data' pin in {pins}")
            return False
        if dataPin['width'] != 16:  # tagT (8) + pixelT at its default WIDTH=8
            print(f"FAIL: 'in_data' width is {dataPin['width']}, expected 16 "
                  f"(8-bit tag + WIDTH=8 default payload)")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


AXI4_STREAM_ARCH = """
ipParameters:
    constants:
        WIDTH: { value: 8, maxValue: 64, desc: "Payload width, default 8 (1 byte)" }
    types:
        pixelT: { width: WIDTH, maxBitwidth: 64, desc: "Parameterizable payload" }

types:
    bitT: { width: 1, desc: "1-bit filler" }

structures:
    dataSt:
        data: { varType: pixelT, desc: "AXI4-Stream tdata payload" }
    bitSt:
        b: { varType: bitT, desc: "1-bit filler payload" }

interfaces:
    axi4str:
        interfaceType: axi4_stream
        desc: "Parameterizable AXI4-Stream interface"
        structures:
            - { structure: dataSt, structureType: tdata_t }
            - { structure: bitSt,  structureType: tid_t }
            - { structure: bitSt,  structureType: tdest_t }
            - { structure: bitSt,  structureType: tuser_t }

blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    leaf:
        desc: "Parameterized AXI4-Stream leaf"
        params: [WIDTH]
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        ports:
            out: { interface: axi4str, direction: src }
    chk:
        desc: "Parameterized AXI4-Stream peer checker"
        params: [WIDTH]
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
        ports:
            in: { interface: axi4str, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top, variant: wide }
    uChk:   { container: top_tb, instanceType: chk,  instGroup: top, variant: wide }
    uLeafN: { container: top_tb, instanceType: leaf, instGroup: top, variant: narrow }
    uChkN:  { container: top_tb, instanceType: chk,  instGroup: top, variant: narrow }

connections:
    - { interface: axi4str, src: uLeaf, srcport: out, dst: uChk, dstport: in }
    - { interface: axi4str, src: uLeafN, srcport: out, dst: uChkN, dstport: in, name: narrowLink }

parameters:
    leaf:
        wide:
            WIDTH: 32
        narrow:
            WIDTH: 8
    chk:
        wide:
            WIDTH: 32
        narrow:
            WIDTH: 8
"""


def test_axi4_stream_non_default_variant_strobe_width():
    """tstrb_t/tkeep_t must track each top's resolved tdata_t width (32 bits ->
    4 bytes at 'wide', 8 bits -> 1 byte at 'narrow'), and stay vector pins at
    1 byte."""
    print("AXI4-Stream per-variant tops: tstrb_t/tkeep_t width and vector")
    db_path, project_path, arch_paths = build_database(
        AXI4_STREAM_ARCH, top_instance='top_tb', project_name='vl_boundary_axi4s')
    try:
        prj = projectOpen(db_path)
        leafKey, _ = find_block(prj, 'leaf')
        blockData = prj.getBlockData(leafKey)
        ok = True
        for variant, tdataWidth, bytes_ in (('wide', 32, 4), ('narrow', 8, 1)):
            leafTop = blockData['svWrapper']['variantTops'][variant]
            pins = {p['pin']: p for p in prj.getVlTopBoundaryPins(blockData, leafTop)}
            tdata = pins['out_tdata']
            if (tdata['width'], tdata['vector']) != (tdataWidth, True):
                print(f"FAIL: {leafTop} 'out_tdata' is {tdata}, expected width "
                      f"{tdataWidth} (variant '{variant}') as a vector")
                ok = False
            for name in ('out_tstrb', 'out_tkeep'):
                if (pins[name]['width'], pins[name]['vector']) != (bytes_, True):
                    print(f"FAIL: {leafTop} '{name}' is {pins[name]}, expected "
                          f"width {bytes_} ({tdataWidth}-bit tdata) as a vector")
                    ok = False
            for name in ('out_tvalid', 'out_tready', 'out_tlast', 'out_tid'):
                if pins[name]['vector']:
                    print(f"FAIL: {leafTop} '{name}' is {pins[name]}, expected a "
                          f"scalar (bool signal or fixed 1-bit payload)")
                    ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


EXT_REG_ARCH = """
types:
    wordT: { width: 32, desc: "Register word" }

structures:
    wordSt:
        w: { varType: wordT, desc: "Register word" }

interfaces:
    extIf:
        desc: "External register interface"
        interfaceType: external_reg
        structures:
            - { structure: wordSt, structureType: data_t }

blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    leaf:
        desc: "Leaf with an external register port"
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        clocks:
            clk: { period: 10 }
        ports:
            ext: { interface: extIf, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""


def test_type_named_signal_width():
    """external_reg's `write` signal names the system type _extRegWriteT, so
    its pin and its SV wrapper port are 2 bits wide, not the 1-bit default.
    The system file that declares that type gets no per-context artifact."""
    print("external_reg type-named signal: boundary pin and SV port width")
    db_path, project_path, arch_paths = build_database(
        EXT_REG_ARCH, top_instance='top_tb', project_name='vl_boundary_extreg')
    try:
        prj = projectOpen(db_path)
        leafKey, _ = find_block(prj, 'leaf')
        vltops = prj.config.getConfig('VLTOPS')
        leafTop = next(t for t, v in vltops.items() if v['blockKey'] == leafKey)
        blockData = prj.getBlockData(leafKey)
        ok = True
        pins = prj.getVlTopBoundaryPins(blockData, leafTop)
        write = next(p for p in pins if p['pin'] == 'ext_write')
        if write['width'] != 2:
            print(f"FAIL: 'ext_write' width is {write['width']}, expected 2 "
                  f"(signalType _extRegWriteT declares width 2)")
            ok = False
        # The SV wrapper template blasts each port through this helper.
        svPorts = []
        for portType in blockData['ports']:
            for portData in blockData['ports'][portType].values():
                svPorts += intf_gen_utils.sv_gen_modport_signal_blast(portData, prj, blockData)['ports']
        if 'input bit [1:0] ext_write' not in svPorts:
            print(f"FAIL: SV wrapper ports {svPorts} lack 'input bit [1:0] ext_write' "
                  f"(signalType _extRegWriteT declares width 2)")
            ok = False
        systemContexts = set(prj.yamlContext['_a2csystem'])
        systemDirs = {os.path.dirname(os.path.abspath(os.path.join(base_dir, c))) for c in systemContexts}
        includeFiles = prj.config.getConfig('INCLUDEFILES')
        for fileType, entries in includeFiles.items():
            for context, entry in entries.items():
                if context in systemContexts or os.path.dirname(os.path.abspath(entry['fileName'])) in systemDirs:
                    print(f"FAIL: INCLUDEFILES[{fileType}] lists {entry['fileName']} for "
                          f"system context {context}; system files get no per-context artifact")
                    ok = False
        nodeDirs = set(prj.config.getConfig('CONTEXTNODEDIR')) & systemContexts
        if nodeDirs:
            print(f"FAIL: CONTEXTNODEDIR has system contexts {sorted(nodeDirs)}")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


CLOCK_ARCH = """
blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    gen:
        desc: "Leaf with a supplied clock, a produced clock and a produced reset"
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        clocks:
            clkIn:  { default: true, period: 10 }
            clkOut: { direction: output }
        resets:
            rstIn_n:  { clock: clkIn }
            rstOut_n: { clock: clkOut, direction: output }
    bare:
        desc: "Leaf with two clocks and no reset"
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        clocks:
            clkA: { default: true, period: 10 }
            clkB: { period: 20 }
        resets: {}

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""


def test_clock_reset_pins():
    """A top's clock and reset pins are its block's declared clocks then
    resets, in declaration order and with each one's direction."""
    print("clock and reset pins follow the block's declarations")
    db_path, project_path, arch_paths = build_database(
        CLOCK_ARCH, top_instance='top_tb', project_name='vl_boundary_clocks')
    try:
        prj = projectOpen(db_path)
        vltops = prj.config.getConfig('VLTOPS')
        expected = {
            'gen': [('clkIn', 'input'), ('clkOut', 'output'),
                    ('rstIn_n', 'input'), ('rstOut_n', 'output')],
            'bare': [('clkA', 'input'), ('clkB', 'input')],
        }
        ok = True
        for block, pinRows in expected.items():
            blockKey, _ = find_block(prj, block)
            top = next(t for t, v in vltops.items() if v['blockKey'] == blockKey)
            pins = prj.getVlTopBoundaryPins(prj.getBlockData(blockKey), top)
            actual = [(p['pin'], p['direction'], p['width'], p['vector']) for p in pins]
            want = [(pin, direction, 1, False) for pin, direction in pinRows]
            if actual != want:
                print(f"FAIL: {top} pins are {actual}, expected {want}")
                ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


EVAL_DERIVED_ARCH = """
ipParameters:
    constants:
        WIDTH: { value: 8, maxValue: 32, desc: "Base width" }

constants:
    DOUBLE_WIDTH: { eval: "$WIDTH * 2", desc: "Derived payload width" }
    TAG_WIDTH: { eval: "$DOUBLE_WIDTH / 4", desc: "Derived from a derived width" }

types:
    dataT: { width: DOUBLE_WIDTH, desc: "Derived width type" }
    tagT: { width: TAG_WIDTH, desc: "Twice-derived width type" }

structures:
    dataSt:
        value: { varType: dataT, desc: "Payload" }
        tag: { varType: tagT, desc: "Tag" }

interfaces:
    dataIf:
        interfaceType: push_ack
        desc: "Data"
        structures:
            - { structure: dataSt, structureType: data_t }

blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    leaf:
        desc: "Parameterized leaf"
        params: [WIDTH]
        hasMdl: true
        hasTb: false
        hasRtl: true
        hasVl: true
        clocks:
            clk: { period: 10 }
        ports:
            out: { interface: dataIf, direction: src }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }

parameters:
    leaf:
        wide: { WIDTH: 16 }
"""


def test_eval_derived_width_at_variant():
    """At variant 'wide' (WIDTH=16) the payload is DOUBLE_WIDTH=32 plus
    TAG_WIDTH=8 bits, as the RTL computes it, in the pin, the VCS port map and
    the Xcelium shell, not the default-valued 16 plus 4."""
    print("eval-derived payload width at a non-default variant")
    db_path, project_path, arch_paths = build_database(
        EVAL_DERIVED_ARCH, top_instance='top_tb', project_name='vl_boundary_eval')
    try:
        prj = projectOpen(db_path)
        leafKey, _ = find_block(prj, 'leaf')
        blockData = prj.getBlockData(leafKey)
        top = blockData['svWrapper']['variantTops']['wide']
        pins = prj.getVlTopBoundaryPins(blockData, top)
        ok = True
        portmapLine = 'out_data 40 bitvector sc_bv'
        if portmapLine not in vlBoundaryGen.portmap(top, pins).splitlines():
            print(f"FAIL: {top} port map lacks '{portmapLine}':\n"
                  f"{vlBoundaryGen.portmap(top, pins)}")
            ok = False
        shellLine = '    sc_out<sc_bv<40>> out_data;'
        if shellLine not in vlBoundaryGen.xceliumShell(top, pins).splitlines():
            print(f"FAIL: {top} Xcelium shell lacks '{shellLine.strip()}':\n"
                  f"{vlBoundaryGen.xceliumShell(top, pins)}")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    ok = test_paramsless_transit_leaf_boundary_pins()
    ok = test_axi4_stream_non_default_variant_strobe_width() and ok
    ok = test_type_named_signal_width() and ok
    ok = test_clock_reset_pins() and ok
    ok = test_eval_derived_width_at_variant() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
