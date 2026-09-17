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
   payload width, not the structure's nominal (default-value) width.
"""

import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import build_database, cleanup, find_block  # noqa: E402
from pysrc.processYaml import projectOpen  # noqa: E402


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

connections:
    - { interface: axi4str, src: uLeaf, srcport: out, dst: uChk, dstport: in }

parameters:
    leaf:
        wide:
            WIDTH: 32
    chk:
        wide:
            WIDTH: 32
"""


def test_axi4_stream_non_default_variant_strobe_width():
    """tstrb_t/tkeep_t must track the selected top's resolved tdata_t width
    (32 bits -> 4 bytes), not the structure's nominal default (8 bits -> 1
    byte)."""
    print("AXI4-Stream non-default variant: tstrb_t/tkeep_t width")
    db_path, project_path, arch_paths = build_database(
        AXI4_STREAM_ARCH, top_instance='top_tb', project_name='vl_boundary_axi4s')
    try:
        prj = projectOpen(db_path)
        leafKey, _ = find_block(prj, 'leaf')
        vltops = prj.config.getConfig('VLTOPS')
        leafTop = next(t for t, v in vltops.items() if v['blockKey'] == leafKey)
        blockData = prj.getBlockData(leafKey)
        pins = prj.getVlTopBoundaryPins(blockData, leafTop)
        tdata = next(p for p in pins if p['pin'] == 'out_tdata')
        tstrb = next(p for p in pins if p['pin'] == 'out_tstrb')
        tkeep = next(p for p in pins if p['pin'] == 'out_tkeep')
        ok = True
        if tdata['width'] != 32:
            print(f"FAIL: 'out_tdata' width is {tdata['width']}, expected 32 "
                  f"(variant 'wide' binds WIDTH=32)")
            ok = False
        for pin in (tstrb, tkeep):
            if pin['width'] != 4:
                print(f"FAIL: '{pin['pin']}' width is {pin['width']}, expected "
                      f"4 (32-bit tdata -> 4 bytes); the nominal WIDTH=8 "
                      f"default would wrongly give 1")
                ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    ok = test_paramsless_transit_leaf_boundary_pins()
    ok = test_axi4_stream_non_default_variant_strobe_width() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
