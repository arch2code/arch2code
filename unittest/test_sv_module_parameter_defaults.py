#!/usr/bin/env python3
"""Generate and execute SV parameters with declared defaults and wide overrides."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


BASE = Path(__file__).resolve().parents[1]

DEFINITIONS = """ipParameters:
  constants:
    WIDTH: {value: 32, maxValue: 64, desc: "Unsigned width"}
    OFFSET: {value: -3, maxValue: 16, valueType: int, desc: "Signed offset"}
    LARGE: {value: 4294967296, maxValue: 1099511627776, desc: "Wide default"}
    GROW: {value: 1, maxValue: 1099511627776, desc: "Wide unsigned domain"}
    SIGNED_GROW: {value: -1, maxValue: 1099511627776, valueType: int, desc: "Wide signed domain"}
    SCALE: {value: 1.5, maxValue: 4, valueType: real, desc: "Real parameter"}
types:
  dummyT: {width: 8, desc: "Package context"}
constants:
  FIXED_SIGNED: {value: -3, valueType: int, desc: "Package formatting control"}
"""

ARCH = """include:
  - definitions.yaml
blocks:
  top: {desc: "Top", hasMdl: false}
  leaf:
    desc: "Parameter declaration test"
    hasMdl: false
    params: [WIDTH, OFFSET, LARGE, GROW, SIGNED_GROW, SCALE]
instances:
  uTop: {container: top, instanceType: top}
  uLeaf: {container: top, instanceType: leaf, variant: changed}
parameters:
  leaf:
    changed:
      WIDTH: 48
      OFFSET: -7
      LARGE: 8589934592
      GROW: 1099511627776
      SIGNED_GROW: -1099511627776
      SCALE: 2.5
"""

PROJECT = """yamlFormat: 2
projectName: paramDefaults
topInstance: uTop
projectFiles:
  - arch.yaml
dirs:
  root: .
fileGeneration:
  fileCopyrightStatement: ""
"""

MAKEFILE = """PROJECTNAME = paramDefaults
TB_TOP_MODULE = top
HDL_TOP_MODULE = top
A2C_PRJ_YAML = $(REPO_ROOT)/project.yaml
include $(A2C_ROOT)/include/make/a2c-common.mk
.PHONY: clean run
clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
run:
	$(REPO_ROOT)/obj_defaults/Vleaf
	$(REPO_ROOT)/obj_overrides/Vleaf
"""

CHECKS = """
initial begin
    if ($bits(WIDTH) != 32 || $bits(OFFSET) != 32 ||
        $bits(LARGE) != 64 || $bits(GROW) != 64 || $bits(SIGNED_GROW) != 64)
        $fatal(1, "Parameter width mismatch");
    if (!(type(WIDTH)'(-1) > type(WIDTH)'(0)) ||
        !(type(GROW)'(-1) > type(GROW)'(0)) ||
        !(type(OFFSET)'(-1) < type(OFFSET)'(0)) ||
        !(type(SIGNED_GROW)'(-1) < type(SIGNED_GROW)'(0)) || $typename(SCALE) != "real")
        $fatal(1, "Parameter type mismatch");
`ifdef CHECK_OVERRIDES
    if (WIDTH != 48 || OFFSET != -7 || LARGE != 64'd8589934592 ||
        GROW != 64'd1099511627776 || SIGNED_GROW != -64'sd1099511627776 || SCALE != 2.5)
        $fatal(1, "Explicit overrides lost");
`else
    if (WIDTH != 32 || OFFSET != -3 || LARGE != 64'd4294967296 ||
        GROW != 1 || SIGNED_GROW != -1 || SCALE != 1.5)
        $fatal(1, "Backing defaults lost");
`endif
    $display("PASS: SV parameter values, widths and signedness");
    $finish;
end

"""


def run(command, work):
    result = subprocess.run(command, cwd=work, text=True, capture_output=True,
                            timeout=180, env={**os.environ, 'NO_COLOR': '1'})
    if result.returncode:
        raise RuntimeError(f"{' '.join(map(str, command))}\n{result.stdout}{result.stderr}")
    return result.stdout + result.stderr


def main():
    with tempfile.TemporaryDirectory(prefix='sv_param_defaults_', dir=BASE / 'unittest') as temp:
        work = Path(temp)
        for name, text in [('definitions.yaml', DEFINITIONS), ('arch.yaml', ARCH),
                           ('project.yaml', PROJECT), ('Makefile', MAKEFILE)]:
            (work / name).write_text(text)
        make = ['make', '-j4', f'REPO_ROOT={work}', f'A2C_ROOT={BASE}']
        run(make + ['clean'], work)
        run(make + ['newmodule'], work)
        run(make + ['gen'], work)

        leaf = work / 'rtl' / 'leaf.sv'
        text = leaf.read_text()
        declarations = [
            "parameter int unsigned WIDTH = 32'h0000_0020",
            "parameter int OFFSET = -32'sh0000_0003",
            "parameter longint unsigned LARGE = 64'h0000_0001_0000_0000",
            "parameter longint unsigned GROW = 64'h0000_0000_0000_0001",
            "parameter longint SIGNED_GROW = -64'sh0000_0000_0000_0001",
            "parameter real SCALE = 1.5",
        ]
        for declaration in declarations:
            assert declaration in text, f"Missing {declaration}\n{text}"
        top = (work / 'rtl' / 'top.sv').read_text()
        for override in ['.WIDTH(48)', '.OFFSET(-7)', '.GROW(1099511627776)', '.SCALE(2.5)']:
            assert override in top, f"Missing instance override {override}\n{top}"
        package = work / 'rtl' / 'definitions_package.sv'
        assert "localparam int FIXED_SIGNED = -32'sh0000_0003;" in package.read_text()

        # The scaffold owns the generated declaration; checks live in its user body.
        marker = 'endmodule: leaf'
        assert marker in text
        leaf.write_text(text.replace(marker, CHECKS + marker))
        run(make + ['gen'], work)
        sources = [str(package), str(leaf)]
        for mode, flags in [
            ('defaults', []),
            ('overrides', ['+define+CHECK_OVERRIDES', '-GWIDTH=48', '-GOFFSET=-7',
                           "-GLARGE=64'd8589934592", "-GGROW=64'd1099511627776",
                           "-GSIGNED_GROW=64'shffffff0000000000", '-GSCALE=2.5']),
        ]:
            run(['verilator', '--binary', '-j', '4', '--top-module', 'leaf',
                 '--Mdir', str(work / f'obj_{mode}'), *flags, *sources], work)
        output = run(make + ['run'], work)
        assert output.count('PASS: SV parameter values, widths and signedness') == 2, output
        print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
