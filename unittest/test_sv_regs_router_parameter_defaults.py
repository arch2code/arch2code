#!/usr/bin/env python3
"""Generate and execute a parameterized register handler and router with their
declared parameter defaults and with explicit overrides."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


BASE = Path(__file__).resolve().parents[1]

ARCH = """ipParameters:
  constants:
    WIDTH: {value: 12, maxValue: 32, desc: "Register payload width"}
    OFFSET: {value: -3, maxValue: 16, valueType: int, desc: "Signed parameter"}
  types:
    cfgT: {width: WIDTH, maxBitwidth: 32, desc: "Register payload"}
constants:
  DWORD: {value: 32, desc: "APB word"}
types:
  apbAddrT: {width: DWORD, desc: "APB address"}
  apbDataT: {width: DWORD, desc: "APB data"}
structures:
  apbAddrSt:
    address: {varType: apbAddrT, generator: address}
  apbDataSt:
    data: {varType: apbDataT, generator: data}
  cfgSt:
    value: {varType: cfgT, generator: register, desc: "Register payload"}
interfaces:
  apbReg:
    desc: "Register bus"
    interfaceType: apb
    structures:
      - {structure: apbAddrSt, structureType: addr_t}
      - {structure: apbDataSt, structureType: data_t}
blocks:
  top: {desc: "Top", hasMdl: false, hasRtl: false}
  cpu:
    desc: "Register bus master"
    hasMdl: false
    hasRtl: false
    ports:
      cpu_main: {interface: apbReg, direction: src}
  decode:
    desc: "Parameterized router"
    hasMdl: false
    params: [WIDTH, OFFSET]
    addressBlock:
      addressGroup: top
      addressIncrement: 0x00100000
      maxAddressSpaces: 16
      varType: addr_id_top
      enumPrefix: ADDR_ID_TOP_
      upstreamPort: apbReg
      registerDecoderPort: apbReg
  leaf:
    desc: "Parameterized register owner"
    hasMdl: false
    params: [WIDTH, OFFSET]
instances:
  uTop: {container: top, instanceType: top}
  uCpu: {container: top, instanceType: cpu}
  uDecode: {container: top, instanceType: decode, variant: changed}
  uLeaf: {container: top, instanceType: leaf, addressGroup: top, variant: changed}
connections:
  - {interface: apbReg, src: uCpu, srcport: cpu_main, dst: uDecode, name: cpu_main}
parameters:
  decode:
    changed: {WIDTH: 20, OFFSET: -7}
  leaf:
    changed: {WIDTH: 20, OFFSET: -7}
registers:
  - {register: cfg, regType: rw, block: leaf, structure: cfgSt, desc: "Parameterized register"}
"""

PROJECT = """yamlFormat: 2
projectName: regsParamDefaults
topInstance: uTop
projectFiles:
  - arch.yaml
addressObjects:
  memories: {alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true}
  registers: {alignment: 8, sortDescending: true}
dirs:
  root: .
fileGeneration:
  fileCopyrightStatement: ""
"""

MAKEFILE = """PROJECTNAME = regsParamDefaults
TB_TOP_MODULE = top
HDL_TOP_MODULE = top
A2C_PRJ_YAML = $(REPO_ROOT)/project.yaml
include $(A2C_ROOT)/include/make/a2c-common.mk
.PHONY: clean
clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
"""

# The handler and router carry interface ports, which Verilator cannot take on a
# top module, so a harness instantiates each at its defaults and with overrides.
# The status_if payload widths make a handler whose storage ignores WIDTH fail
# elaboration.
HARNESS = """module harness;
import arch_package::*;
logic clk = 1'b0;
logic rst_n = 1'b0;
apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) upDef(), downDef(), upOvr(), downOvr();
status_if #(.data_t(logic [11:0])) cfgDef();
status_if #(.data_t(logic [19:0])) cfgOvr();
decode uDecodeDef (.cpu_main(upDef), .apbReg_uLeaf(downDef), .clk(clk), .rst_n(rst_n));
decode #(.WIDTH(20), .OFFSET(-7)) uDecodeOvr (.cpu_main(upOvr), .apbReg_uLeaf(downOvr), .clk(clk), .rst_n(rst_n));
leaf_regs uRegsDef (.apbReg(downDef), .cfg(cfgDef), .clk(clk), .rst_n(rst_n));
leaf_regs #(.WIDTH(20), .OFFSET(-7)) uRegsOvr (.apbReg(downOvr), .cfg(cfgOvr), .clk(clk), .rst_n(rst_n));
initial begin
    if ($bits(uDecodeDef.WIDTH) != 32 || $bits(uRegsDef.OFFSET) != 32 ||
        !(uRegsDef.OFFSET < 0) || !(uDecodeDef.OFFSET < 0) || $bits(uRegsDef.cfg_reg) != 12)
        $fatal(1, "Parameter type mismatch");
    if (uDecodeDef.WIDTH != 12 || uDecodeDef.OFFSET != -3 || uRegsDef.WIDTH != 12 || uRegsDef.OFFSET != -3)
        $fatal(1, "Backing defaults lost");
    if (uDecodeOvr.WIDTH != 20 || uDecodeOvr.OFFSET != -7 || uRegsOvr.WIDTH != 20 || uRegsOvr.OFFSET != -7 ||
        $bits(uRegsOvr.cfg_reg) != 20)
        $fatal(1, "Explicit overrides lost");
    $display("PASS: handler and router parameter defaults and overrides");
    $finish;
end
endmodule
"""


def run(command, work):
    result = subprocess.run(command, cwd=work, text=True, capture_output=True,
                            timeout=180, env={**os.environ, 'NO_COLOR': '1'})
    if result.returncode:
        raise RuntimeError(f"{' '.join(map(str, command))}\n{result.stdout}{result.stderr}")
    return result.stdout + result.stderr


def parameterLines(path):
    return [line.strip().rstrip(',') for line in path.read_text().splitlines()
            if line.strip().startswith('parameter ') and 'APB_READY_1WS' not in line]


def main():
    with tempfile.TemporaryDirectory(prefix='sv_regs_param_defaults_', dir=BASE / 'unittest') as temp:
        work = Path(temp)
        for name, text in [('arch.yaml', ARCH), ('project.yaml', PROJECT), ('Makefile', MAKEFILE)]:
            (work / name).write_text(text)
        make = ['make', '-j4', f'REPO_ROOT={work}', f'A2C_ROOT={BASE}']
        run(make + ['clean'], work)
        run(make + ['newmodule'], work)
        run(make + ['gen'], work)

        rtl = work / 'rtl'
        declarations = [
            "parameter int unsigned WIDTH = 32'h0000_000C",
            "parameter int OFFSET = -32'sh0000_0003",
        ]
        for name in ['leaf.sv', 'leaf_regs.sv', 'decode.sv']:
            lines = parameterLines(rtl / name)
            assert lines == declarations, f"{name} parameters {lines}, expected {declarations}"

        harness = work / 'harness.sv'
        harness.write_text(HARNESS)
        sources = [rtl / 'arch_package.sv', rtl / 'decode.sv', rtl / 'leaf_regs.sv', harness]
        run(['verilator', '--binary', '-j', '4', '--top-module', 'harness', '--Mdir', str(work / 'obj'),
             '-F', str(BASE / 'common' / 'systemVerilog' / 'a2c.f'), *map(str, sources)], work)
        output = run([str(work / 'obj' / 'Vharness')], work)
        assert 'PASS: handler and router parameter defaults and overrides' in output, output
        print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
