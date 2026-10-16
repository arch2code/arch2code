# test_vl_boundary_widths_build.py builds a copy of this tree and overrides
# A2C_ROOT and FIXTURE_ROOT on the make command line, so both reach the
# sub-project makes; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
FIXTURE_ROOT = $(A2C_ROOT)/unittest/fixtures/vl-boundary-widths
REPO_ROOT = $(FIXTURE_ROOT)/leaf

PROJECTNAME = vbwLeaf
# Required by a2c-common.mk and unused: this project only builds db/gen.
TB_TOP_MODULE = fLeaf
HDL_TOP_MODULE = fLeaf

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/vbwLeafProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
