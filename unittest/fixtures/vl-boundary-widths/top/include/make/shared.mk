# test_vl_boundary_widths_build.py builds a copy of this tree and overrides
# A2C_ROOT and FIXTURE_ROOT on the make command line, so both reach the
# sub-project makes; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
FIXTURE_ROOT = $(A2C_ROOT)/unittest/fixtures/vl-boundary-widths
REPO_ROOT = $(FIXTURE_ROOT)/top

PROJECTNAME = vbwTop
TB_TOP_MODULE = vbwTop
HDL_TOP_MODULE = dutA

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/vbwTopProject.yaml

# The idt/idth test protocols' companions: SystemC headers on the include path,
# SystemVerilog interfaces on each simulator's library search path. vlogan does
# not search -y, so VCS compiles the interfaces as library files.
EXTRA_A2C_SRC_DIRS = $(FIXTURE_ROOT)/interfaces/idt $(FIXTURE_ROOT)/interfaces/idth
VERILATOR_USER_OPTS = -F $(FIXTURE_ROOT)/interfaces/vbw.f
XRUN_USER_OPTS = -F $(FIXTURE_ROOT)/interfaces/vbw.f
EXTRA_VCS_LIB_SV_FILES = $(FIXTURE_ROOT)/interfaces/idt/idt_if.sv $(FIXTURE_ROOT)/interfaces/idth/idth_if.sv

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
